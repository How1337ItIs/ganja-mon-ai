#!/usr/bin/env python3
"""Run one daily GrowRing NFT mint pipeline cycle.

Designed for automation (OpenClaw cron / manual ops).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.onchain.daily_mint import DailyMintPipeline  # noqa: E402


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "growring-mint-runner"})
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "growring-mint-runner"})
    with urlopen(req, timeout=30) as resp:
        return resp.read()


def _c_to_f(c: float) -> float:
    return (c * 9.0 / 5.0) + 32.0


def _build_sensor_payload(sensors: dict, stage: dict) -> dict:
    air_temp = sensors.get("air_temp")
    temp_f = None
    if isinstance(air_temp, (int, float)):
        temp_f = _c_to_f(float(air_temp))

    payload = {
        "temperature": round(temp_f, 2) if temp_f is not None else 75.0,
        "humidity": float(sensors.get("humidity") or 60.0),
        "vpd": float(sensors.get("vpd") or 1.0),
        "soil_moisture": float(sensors.get("soil_moisture") or 0.0),
        "growth_stage": stage.get("current_stage") or "seedling",
    }
    return payload


async def _run(args: argparse.Namespace) -> int:
    api_base = args.api_base.rstrip("/")

    try:
        sensors = _fetch_json(f"{api_base}/api/sensors")
        stage = _fetch_json(f"{api_base}/api/grow/stage")
        image_bytes = _fetch_bytes(f"{api_base}/api/webcam/latest")
    except (HTTPError, URLError, TimeoutError) as e:
        print(json.dumps({"status": "error", "error": f"API fetch failed: {e}"}))
        return 1
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected API error: {e}"}))
        return 1

    data_dir = PROJECT_ROOT / "data" / "growring"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    image_path = raw_dir / f"daily_capture_{stamp}.jpg"
    image_path.write_bytes(image_bytes)

    sensor_payload = _build_sensor_payload(sensors, stage)

    pipeline = DailyMintPipeline(
        grow_start_date=args.grow_start_date,
        data_dir=data_dir,
    )

    try:
        result = await pipeline.run(
            webcam_image=image_path,
            sensor_data=sensor_payload,
            health_score=args.health_score,
            mood=args.mood,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Pipeline failure: {e}"}))
        return 1

    print(json.dumps(result, ensure_ascii=True))

    status = str(result.get("status", "")).lower()
    if status in {"minted", "dry_run", "skipped"}:
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one daily GrowRing mint cycle")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="Base URL for local HAL API")
    parser.add_argument("--grow-start-date", default="2026-02-01", help="ISO grow start date")
    parser.add_argument("--health-score", type=int, default=80, help="Health score override")
    parser.add_argument("--mood", default="irie", help="Mood string for narrative/art")
    parser.add_argument("--dry-run", action="store_true", help="Generate art/narrative but skip mint/list/promote")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
