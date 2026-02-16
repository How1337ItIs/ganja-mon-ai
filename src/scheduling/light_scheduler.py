"""
Standalone Light Scheduler
==========================

Lightweight asyncio loop that controls the grow light based on the
current growth stage's photoperiod (read from the database).

This runs inside the FastAPI server process (lifespan) so it has direct
access to hardware connections.  It replaces the photoperiod scheduler
that previously lived in the orchestrator (which no longer runs in
"all" / OpenClaw mode).

Logic:
  Every 60 seconds:
    1. Read current growth stage + photoperiod from DB (e.g. "18/6")
    2. Compute whether the light should be ON or OFF right now
    3. If the actual Tapo plug state differs → correct it

This is intentionally simple and stateless — each tick re-derives
the expected state from the clock, avoiding any risk of stale internal
state leading to missed transitions (the exact bug this module fixes).
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Default schedule: lights on at 6 AM, 18/6 veg
DEFAULT_LIGHT_ON_HOUR = 6
DEFAULT_PHOTOPERIOD = "18/6"


def should_light_be_on(
    now: Optional[datetime] = None,
    light_on_hour: int = DEFAULT_LIGHT_ON_HOUR,
    photoperiod: str = DEFAULT_PHOTOPERIOD,
) -> bool:
    """
    Pure function: given the current time and photoperiod, return True if the
    light should be ON.

    Args:
        now: Current datetime (defaults to datetime.now())
        light_on_hour: Hour of day lights turn ON (0-23)
        photoperiod: String like "18/6", "12/12", "24/0", "20/4"

    Returns:
        True if lights should be on, False if dark period
    """
    if now is None:
        now = datetime.now()

    # Parse photoperiod
    try:
        parts = photoperiod.split("/")
        hours_on = int(parts[0])
        hours_off = int(parts[1]) if len(parts) > 1 else (24 - hours_on)
    except (ValueError, IndexError):
        hours_on = 18
        hours_off = 6

    # Special case: 24/0 means always on
    if hours_on >= 24:
        return True

    # Special case: 0/24 means always off (shouldn't happen but be safe)
    if hours_on <= 0:
        return False

    light_off_hour = (light_on_hour + hours_on) % 24

    current_minutes = now.hour * 60 + now.minute
    on_minutes = light_on_hour * 60
    off_minutes = light_off_hour * 60

    if on_minutes < off_minutes:
        # Normal: e.g. ON at 6:00, OFF at 0:00 → on_minutes=360, off_minutes=0
        # Wait, this case: 6*60=360, (6+18)%24=0 → 0*60=0
        # So actually 360 > 0, we'd go to else. Let me reconsider.
        # on=360, off=0 → on > off (overnight dark). else branch.
        # on=6:00(360), off=18:00(1080) → 360 < 1080 → this branch
        # Light is on between 360 and 1080
        return on_minutes <= current_minutes < off_minutes
    else:
        # Overnight dark period: e.g. ON at 6:00(360), OFF at 0:00(0)
        # Light is on from 360 onwards OR before 0
        # i.e. light is on if current >= on_minutes OR current < off_minutes
        return current_minutes >= on_minutes or current_minutes < off_minutes


async def light_scheduler_loop(
    app_state,
    check_interval: int = 60,
):
    """
    Async loop that enforces the photoperiod light schedule.

    Reads the current growth stage from DB every tick, computes whether
    the light should be on, and corrects the Tapo plug if needed.

    Args:
        app_state: FastAPI app.state (must have .tapo_hub and optionally .actuators)
        check_interval: Seconds between checks (default: 60)
    """
    # Initial delay to let hardware connect
    await asyncio.sleep(30)
    logger.info("[LIGHT-SCHED] Light scheduler started (60s check interval)")
    print("[OK] Light scheduler started (60s enforcement loop)")

    consecutive_failures = 0

    while True:
        try:
            # 1. Read current photoperiod from DB
            photoperiod = DEFAULT_PHOTOPERIOD
            try:
                from src.db.connection import get_db_session
                from src.db.repository import GrowRepository
                async with get_db_session() as session:
                    repo = GrowRepository(session)
                    stage_data = await repo.get_current_stage()
                    if stage_data:
                        photoperiod = stage_data.get("photoperiod", DEFAULT_PHOTOPERIOD)
            except Exception as e:
                logger.warning(f"[LIGHT-SCHED] DB read failed: {e}")

            # 2. Compute expected state
            now = datetime.now()
            expected_on = should_light_be_on(
                now=now,
                light_on_hour=DEFAULT_LIGHT_ON_HOUR,
                photoperiod=photoperiod,
            )

            # 3. Read actual state (Tapo preferred; Kasa fallback) and correct if needed
            tapo_hub = getattr(app_state, 'tapo_hub', None)
            kasa_hub = getattr(app_state, 'actuators', None)
            if tapo_hub is None and kasa_hub is None:
                # No controllable backend available.
                await asyncio.sleep(check_interval)
                continue

            try:
                if tapo_hub is not None:
                    tapo_state = await asyncio.wait_for(
                        tapo_hub.get_state(),
                        timeout=10.0,
                    )
                    actual_on = bool(getattr(tapo_state, "grow_light", False))
                else:
                    kasa_state = await asyncio.wait_for(
                        kasa_hub.get_state(),
                        timeout=10.0,
                    )
                    actual_on = bool(getattr(kasa_state, "grow_light", False))
            except Exception as e:
                consecutive_failures += 1
                if consecutive_failures <= 3 or consecutive_failures % 10 == 0:
                    logger.warning(f"[LIGHT-SCHED] Light state read failed ({consecutive_failures}x): {e}")

                # If we can't read state, try to reconnect
                if consecutive_failures >= 3 and tapo_hub is not None:
                    try:
                        reconnected = await tapo_hub._reconnect_device("grow_light")
                        if reconnected:
                            logger.info("[LIGHT-SCHED] Tapo grow_light reconnected")
                            consecutive_failures = 0
                    except Exception:
                        pass

                await asyncio.sleep(check_interval)
                continue

            consecutive_failures = 0

            # 4. Correct if mismatch
            if actual_on != expected_on:
                action = "ON" if expected_on else "OFF"
                logger.info(
                    f"[LIGHT-SCHED] Correcting light: {action} "
                    f"(was={'ON' if actual_on else 'OFF'}, "
                    f"schedule={photoperiod}, time={now.strftime('%H:%M')})"
                )
                print(
                    f"[LIGHT-SCHED] {now.strftime('%H:%M')} Correcting light → {action} "
                    f"(photoperiod={photoperiod})"
                )

                # Prefer Tapo if configured; otherwise use Kasa directly.
                if tapo_hub is not None:
                    success = await tapo_hub.set_device("grow_light", expected_on)
                    if not success:
                        logger.error(f"[LIGHT-SCHED] Failed to set light {action} via Tapo!")
                        print(f"[LIGHT-SCHED] FAILED to set light {action} via Tapo!")
                        if kasa_hub and hasattr(kasa_hub, 'set_device'):
                            try:
                                await kasa_hub.set_device("grow_light", expected_on)
                                logger.info(f"[LIGHT-SCHED] Kasa fallback succeeded: {action}")
                            except Exception as ke:
                                logger.error(f"[LIGHT-SCHED] Kasa fallback also failed: {ke}")
                else:
                    try:
                        await kasa_hub.set_device("grow_light", expected_on)
                    except Exception as ke:
                        logger.error(f"[LIGHT-SCHED] Failed to set light {action} via Kasa: {ke}")

        except asyncio.CancelledError:
            logger.info("[LIGHT-SCHED] Light scheduler cancelled")
            break
        except Exception as e:
            logger.error(f"[LIGHT-SCHED] Unexpected error: {e}")

        await asyncio.sleep(check_interval)
