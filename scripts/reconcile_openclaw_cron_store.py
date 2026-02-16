#!/usr/bin/env python3
"""
Reconcile OpenClaw cron store directly (no `openclaw cron add/rm`).

Why:
- The OpenClaw CLI can hang, and a failure mid-run can leave a partially
  applied schedule (jobs removed but not re-added).
- The authoritative store is the file configured in
  `openclaw-workspace/config/openclaw.json` under `cron.store`
  (typically `openclaw-workspace/cron/cron.json`).

This script:
- Loads the configured cron store
- Rewrites it to a canonical set of jobs by name
- Preserves job `id` and `state` when possible to avoid losing run history
- Writes atomically to prevent truncation on crash/power loss
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


_default_project_root = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", str(_default_project_root))).resolve()
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", str(PROJECT_ROOT / "openclaw-workspace"))).resolve()
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", str(WORKSPACE_ROOT / "config" / "openclaw.json"))).resolve()


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _atomic_write(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _resolve_cron_store() -> Path:
    cfg = _load_json(CONFIG_PATH, {})
    rel = ((cfg.get("cron") or {}).get("store")) or "cron/cron.json"
    return (WORKSPACE_ROOT / rel).resolve()


@dataclass(frozen=True)
class JobSpec:
    expr: str
    message: str
    model: str
    timeout_seconds: int
    tz: str = "America/Los_Angeles"
    agent_id: str = "ganjamon"
    session_target: str = "isolated"


def canonical_specs() -> Dict[str, JobSpec]:
    # Cheap text-first defaults. Can be overridden per-machine via env vars.
    # Note: GLM-5 is text-only; use a vision-capable model for image workflows.
    fast_model = os.getenv("FAST_MODEL", "openrouter/moonshotai/kimi-k2.5")
    # Use a reasoning-capable model for less frequent "deep thinking" jobs.
    smart_model = os.getenv("SMART_MODEL", "openrouter/moonshotai/kimi-k2-thinking")

    # Use longer timeouts by default. Most failures we saw were timeouts at 180s.
    return {
        "Grow Decision Cycle": JobSpec(
            # Stagger off minute 0 to avoid thundering-herd spikes on the Chromebook.
            expr="7 */2 * * *",
            model=fast_model,
            timeout_seconds=600,
            message=(
                "Plant ops check. Use exec to fetch /api/sensors and /api/grow/stage, compare against safe targets. "
                "Then run gentle watering automation from the repo root (soil moisture is a supplemental signal; "
                "do not block the automation solely on a single probe reading):\n\n"
                "cd /home/natha/projects/sol-cannabis && /home/natha/projects/sol-cannabis/venv/bin/python "
                "scripts/gentle_daily_watering.py --apply\n\n"
                "If any environment action is needed, use the correct grow tools and log what changed. "
                "Keep it short and action-oriented."
            ),
        ),
        "Cross-Platform Social": JobSpec(
            # Keep this clear of Auto-Review to avoid skipped social cycles
            # when OpenClaw intentionally skips missed overlapping runs.
            expr="37 */4 * * *",
            model=fast_model,
            timeout_seconds=600,
            message=(
                "Social cycle. Use ganjamon-social workflow with varied content, then post across Twitter, Farcaster, "
                "and Telegram with no hashtags. Log URLs and outcomes."
            ),
        ),
        "Reputation Publishing": JobSpec(
            expr="47 1,5,9,13,17,21 * * *",
            model=fast_model,
            timeout_seconds=600,
            message=(
                "Reputation publish cycle. Check data quality and publish reputation/trust updates only when signals "
                "are high quality. Log tx/results."
            ),
        ),
        "Auto-Review": JobSpec(
            expr="13 0,6,12,18 * * *",
            # Keep this on a fast model so it does not starve nearby cycles.
            model=fast_model,
            timeout_seconds=420,
            message=(
                "Run operational review over last cycles (grow, trading, social, reliability), identify regressions, "
                "and emit concrete self-improvement actions."
            ),
        ),
        "Research and Intelligence": JobSpec(
            expr="21 8,20 * * *",
            model=fast_model,
            timeout_seconds=600,
            message="Research sweep using alpha/research skills, synthesize findings, and store actionable outputs.",
        ),
        "Daily Comprehensive Update": JobSpec(
            expr="5 9 * * *",
            model=fast_model,
            timeout_seconds=600,
            message="Daily report with plant health, system status, trading/social snapshots, and priority goals.",
        ),
        "Daily NFT Creation": JobSpec(
            expr="30 11 * * *",
            model=fast_model,
            timeout_seconds=600,
            message=(
                "Daily NFT pipeline. Use exec to run python3 scripts/run_daily_nft_mint.py and capture "
                "success/failure plus token/listing outputs."
            ),
        ),
        "Skill Library Check": JobSpec(
            # Keep this off the daytime load window; it can trigger expensive checks.
            expr="41 3 * * *",
            model=fast_model,
            timeout_seconds=240,
            message=(
                "Skill audit. Run a lightweight skills inventory and identify only top missing/high-value skills "
                "to improve operations. Keep runtime short."
            ),
        ),
        "Self-Improvement Reflection": JobSpec(
            expr="43 21 * * *",
            model=smart_model,
            timeout_seconds=600,
            message=(
                "Reflection loop. Review failures, stale components, and blocked goals; propose or apply safe fixes "
                "and log why."
            ),
        ),
        "Weekly Deep Analysis": JobSpec(
            expr="19 6 * * 1",
            model=smart_model,
            timeout_seconds=900,
            message="Weekly deep review and upgrade planning across grow quality, profitability, social, and resilience.",
        ),
    }


def _ensure_job(existing: Optional[Dict[str, Any]], name: str, spec: JobSpec) -> Dict[str, Any]:
    now_ms = _now_ms()
    job = dict(existing or {})
    prev_schedule = job.get("schedule") if isinstance(job, dict) else {}
    prev_expr = (prev_schedule or {}).get("expr")
    prev_tz = (prev_schedule or {}).get("tz")
    prev_kind = (prev_schedule or {}).get("kind")
    schedule_changed = (
        prev_kind != "cron"
        or prev_expr != spec.expr
        or prev_tz != spec.tz
    )
    job.setdefault("id", str(uuid.uuid4()))
    job.setdefault("createdAtMs", now_ms)
    job["updatedAtMs"] = now_ms
    job["agentId"] = spec.agent_id
    job["name"] = name
    job["enabled"] = True
    job.setdefault("wakeMode", "now")
    job["sessionTarget"] = spec.session_target

    job["schedule"] = {
        "kind": "cron",
        "expr": spec.expr,
        "tz": spec.tz,
    }

    payload = job.get("payload") or {}
    payload.update(
        {
            "kind": "agentTurn",
            "message": spec.message,
            "model": spec.model,
            "timeoutSeconds": int(spec.timeout_seconds),
        }
    )
    payload.pop("thinking", None)  # keep cron runs efficient by default
    job["payload"] = payload

    # Delivery acks can block cron lanes if channel/session routing stalls.
    # Keep autonomous jobs non-delivering by default for gateway stability.
    job["delivery"] = {"mode": "none"}
    # Preserve run history but clear sticky error counters so a prior bad model/timeout
    # doesn't leave the job in a "perma-red" state after reconciliation.
    state = job.get("state") or {}
    if isinstance(state, dict):
        # Running markers can stick around across restarts. Never preserve these.
        state.pop("runningAtMs", None)
        if schedule_changed:
            # If the schedule changed, force the gateway to recalculate nextRunAtMs
            # instead of preserving a stale timestamp from the previous cron expr.
            state.pop("nextRunAtMs", None)
        state.pop("lastError", None)
        state.pop("lastStatus", None)
        state["consecutiveErrors"] = 0
    job["state"] = state if isinstance(state, dict) else {}
    return job


def reconcile() -> Dict[str, Any]:
    store = _resolve_cron_store()
    obj = _load_json(store, {"version": 1, "jobs": []})
    jobs: List[Dict[str, Any]] = list(obj.get("jobs") or [])
    by_name = {j.get("name"): j for j in jobs if isinstance(j, dict) and j.get("name")}

    specs = canonical_specs()
    new_jobs = []
    for name, spec in specs.items():
        new_jobs.append(_ensure_job(by_name.get(name), name, spec))

    out = {"version": int(obj.get("version") or 1), "jobs": new_jobs}
    _atomic_write(store, out)
    return {"ok": True, "store": str(store), "jobs_total": len(new_jobs), "models": {n: s.model for n, s in specs.items()}}


def main() -> int:
    result = reconcile()
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
