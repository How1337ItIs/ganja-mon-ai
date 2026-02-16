#!/usr/bin/env python3
"""
Gentle daily watering controller.

Purpose:
- Re-enable stage-guided daily watering after overwatering recovery periods.
- Keep watering gentle: one capped daily event, with a minimum interval.
- Use live HAL data and stage parameters to make the decision.

This script is safe to run repeatedly; it is idempotent across a day/interval.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.request import urlopen

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
STATE_PATH = DATA_DIR / "gentle_watering_state.json"

# Ensure local package imports work when run as a script.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


STAGE_ALIASES = {
    "clone": "seedling",
    "seedling": "seedling",
    "early_veg": "vegetative",
    "veg": "vegetative",
    "vegetative": "vegetative",
    "transition": "transition",
    "preflower": "transition",
    "flower": "flowering",
    "flowering": "flowering",
    "late_flower": "late_flower",
}


@dataclass
class StageProfile:
    base_ml: int
    max_ml: int


STAGE_DOSE = {
    "seedling": StageProfile(base_ml=30, max_ml=45),
    "vegetative": StageProfile(base_ml=35, max_ml=50),
    "transition": StageProfile(base_ml=35, max_ml=50),
    "flowering": StageProfile(base_ml=30, max_ml=45),
    "late_flower": StageProfile(base_ml=25, max_ml=40),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _read_json_url(url: str, timeout: float = 6.0) -> Dict[str, Any]:
    with urlopen(url, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {"events": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"events": []}


def _save_state(state: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def _log_grokmon_db_event(
    *,
    ts_iso: str,
    stage: str,
    soil_before: float,
    planned_ml: int,
    success: bool,
    backend: str,
) -> None:
    """Record watering attempts into grokmon.db so 'last watering' is accurate.

    The gentle watering cron runs outside the LLM/decision loop, so without this
    the DB action log can look "stuck" even when the pump is actually running.
    """
    db_path = DATA_DIR / "grokmon.db"
    if not db_path.exists():
        return

    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()

        # Use latest session as the active session (simpler and robust).
        cur.execute("select id, current_day from grow_sessions order by id desc limit 1")
        row = cur.fetchone()
        if not row:
            return
        session_id, grow_day = int(row[0]), int(row[1])

        now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_text = (
            "AUTOPILOT (gentle_daily_watering)\n"
            f"- ts_utc: {ts_iso}\n"
            f"- stage: {stage}\n"
            f"- soil_before: {soil_before}\n"
            f"- planned_ml: {planned_ml}\n"
            f"- backend: {backend}\n"
            f"- success: {bool(success)}\n"
        )

        cur.execute(
            "insert into ai_decisions(session_id, timestamp, grow_day, output_text, model_used, tokens_used) "
            "values (?, ?, ?, ?, ?, ?)",
            (session_id, now_local, grow_day, output_text, "autopilot/gentle_daily_watering", 0),
        )
        decision_id = int(cur.lastrowid)

        params = json.dumps(
            {
                "amount_ml": int(planned_ml),
                "backend": backend,
                "script": "scripts/gentle_daily_watering.py",
            }
        )
        reason = (
            f"Dispensed {planned_ml}ml of water. Reason: gentle_daily_watering "
            f"(soil_before={soil_before}, stage={stage}, ts_utc={ts_iso}, backend={backend})"
        )

        cur.execute(
            "insert into action_logs("
            "decision_id, session_id, timestamp, action_type, parameters, reason, "
            "executed, execution_time, success, outcome_verified"
            ") values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                decision_id,
                session_id,
                now_local,
                "water",
                params,
                reason,
                1,
                now_local,
                1 if success else 0,
                0,
            ),
        )

        con.commit()
    except Exception:
        # Never break watering if the DB logger fails.
        try:
            con.rollback()
        except Exception:
            pass
    finally:
        try:
            con.close()
        except Exception:
            pass


def _normalize_stage(stage: str) -> str:
    key = (stage or "").strip().lower().replace(" ", "_")
    return STAGE_ALIASES.get(key, "vegetative")


def _calc_planned_ml(
    stage: str,
    current_soil: float,
    stage_soil_min: float,
) -> int:
    profile = STAGE_DOSE.get(stage, STAGE_DOSE["vegetative"])
    dryness = max(0.0, stage_soil_min - current_soil)
    # Add a small amount as soil gets drier, but keep it gentle.
    extra = min(15.0, dryness * 1.2)
    planned = int(round(profile.base_ml + extra))
    return max(15, min(profile.max_ml, planned))


async def _water_with_kasa(amount_ml: int) -> bool:
    from src.hardware.kasa import KasaActuatorHub

    ip = os.getenv("KASA_WATER_PUMP_IP", "").strip()
    if not ip:
        return False

    hub = KasaActuatorHub({"water_pump": ip})
    if not await hub.connect():
        return False
    try:
        return await hub.water(amount_ml)
    finally:
        await hub.disconnect()


async def _water_with_tapo(amount_ml: int) -> bool:
    from src.hardware.tapo import TapoActuatorHub

    if not os.getenv("TAPO_WATER_PUMP_IP", "").strip():
        return False
    # Constructor reads credentials/IPs from env by default.
    hub = TapoActuatorHub()
    if not await hub.connect():
        return False
    try:
        return await hub.water(amount_ml)
    finally:
        await hub.disconnect()


async def _dispatch_watering(amount_ml: int) -> tuple[bool, str]:
    try:
        if await _water_with_kasa(amount_ml):
            return True, "kasa"
    except Exception as exc:
        return False, f"kasa_error:{exc}"

    try:
        if await _water_with_tapo(amount_ml):
            return True, "tapo"
    except Exception as exc:
        return False, f"tapo_error:{exc}"

    return False, "no_pump_backend"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage-guided gentle daily watering")
    parser.add_argument("--apply", action="store_true", help="Actually run watering if needed")
    parser.add_argument(
        "--min-hours-between",
        type=float,
        default=20.0,
        help="Minimum hours between watering events (default: 20)",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "agents" / "ganjamon" / ".env", override=False)

    hal_base = os.getenv("HAL_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

    try:
        stage_data = _read_json_url(f"{hal_base}/api/grow/stage")
        sensors = _read_json_url(f"{hal_base}/api/sensors")
        rate_data = _read_json_url(f"{hal_base}/api/predictions/absorption-rate")
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": f"hal_unavailable:{exc}"}))
        return 2

    stage_raw = str(stage_data.get("current_stage", "vegetative"))
    stage = _normalize_stage(stage_raw)
    current_soil = float(sensors.get("soil_moisture") or 0.0)
    rate_ml_per_pct = float(rate_data.get("absorption_rate_ml_per_pct") or 20.0)

    # Pull stage-specific soil range from HAL parameters.
    try:
        params = _read_json_url(f"{hal_base}/api/grow/parameters/{stage}")
        soil_cfg = params.get("soil_moisture", {}) if isinstance(params, dict) else {}
        stage_soil_min = float(soil_cfg.get("min", 30.0))
    except Exception:
        stage_soil_min = 30.0

    state = _load_state()
    last_ts = _parse_iso(str(state.get("last_water_ts", ""))) if state.get("last_water_ts") else None
    now = _now()
    min_interval = timedelta(hours=max(1.0, args.min_hours_between))
    cooldown_active = bool(last_ts and (now - last_ts) < min_interval)
    watered_today = bool(last_ts and last_ts.date() == now.date())

    planned_ml = _calc_planned_ml(stage=stage, current_soil=current_soil, stage_soil_min=stage_soil_min)
    projected_delta_pct = planned_ml / max(1.0, rate_ml_per_pct)
    trigger_threshold = stage_soil_min + 1.0  # gentle top-up near the lower bound

    needs_water = current_soil <= trigger_threshold
    should_water = needs_water and (not cooldown_active) and (not watered_today)

    result: Dict[str, Any] = {
        "ok": True,
        "apply": bool(args.apply),
        "stage_raw": stage_raw,
        "stage": stage,
        "soil_moisture": current_soil,
        "stage_soil_min": stage_soil_min,
        "trigger_threshold": trigger_threshold,
        "planned_ml": planned_ml,
        "projected_delta_pct": round(projected_delta_pct, 2),
        "needs_water": needs_water,
        "cooldown_active": cooldown_active,
        "watered_today": watered_today,
        "should_water": should_water,
        "state_path": str(STATE_PATH),
    }

    if not should_water:
        print(json.dumps(result))
        return 0

    if not args.apply:
        result["dry_run"] = True
        print(json.dumps(result))
        return 0

    success, backend = asyncio.run(_dispatch_watering(planned_ml))
    event = {
        "ts": _to_iso(now),
        "stage": stage,
        "soil_before": current_soil,
        "planned_ml": planned_ml,
        "success": success,
        "backend": backend,
    }
    state.setdefault("events", []).append(event)
    state["events"] = state["events"][-200:]
    if success:
        state["last_water_ts"] = event["ts"]
        state["last_water_ml"] = planned_ml
        state["last_stage"] = stage
    _save_state(state)
    _log_grokmon_db_event(
        ts_iso=event["ts"],
        stage=stage,
        soil_before=current_soil,
        planned_ml=planned_ml,
        success=success,
        backend=backend,
    )

    result["applied"] = success
    result["backend"] = backend
    result["event"] = event
    print(json.dumps(result))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
