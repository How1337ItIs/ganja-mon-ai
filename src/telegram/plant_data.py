"""Fetches live plant data from the local FastAPI server."""

import httpx
import logging

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


async def get_sensor_data() -> dict:
    """Get current sensor readings."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{API_BASE}/api/sensors/live")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Failed to get sensor data: {e}")
    return {}


async def get_grow_stage() -> dict:
    """Get current growth stage info."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{API_BASE}/api/grow/stage")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Failed to get grow stage: {e}")
    return {}


async def get_latest_ai_decision() -> dict:
    """Get Grok's latest AI decision/commentary."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{API_BASE}/api/ai/latest")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Failed to get AI decision: {e}")
    return {}


async def get_webcam_image() -> bytes | None:
    """Get latest webcam image as bytes."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{API_BASE}/api/webcam/latest")
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        logger.warning(f"Failed to get webcam image: {e}")
    return None


async def get_plant_summary() -> str:
    """Build a human-readable plant status summary for AI context."""
    from datetime import datetime

    sensors = await get_sensor_data()
    stage = await get_grow_stage()

    if not sensors:
        return "Plant sensors unavailable right now."

    parts = []

    # Current time (CRITICAL: Grok has no time awareness without this)
    now = datetime.now()
    parts.append(f"Current time: {now.strftime('%I:%M %p')} PST ({now.strftime('%A, %B %d, %Y')})")

    # Growth stage + dark period truth
    if stage:
        parts.append(f"Growth stage: {stage.get('stage', '?')} (Day {stage.get('day', '?')})")
        parts.append(f"Strain: {stage.get('strain', 'GDP Runtz')}")
        photoperiod = stage.get('photoperiod', '18/6')
        is_dark = stage.get('is_dark_period', False)
        parts.append(f"Photoperiod: {photoperiod} (lights on {'NO - DARK PERIOD' if is_dark else 'YES'})")

    # Environment
    temp_c = sensors.get("temperature")
    humidity = sensors.get("humidity")
    co2 = sensors.get("co2")
    vpd = sensors.get("vpd")
    soil = sensors.get("soil_moisture")

    if temp_c is not None:
        temp_f = temp_c * 9 / 5 + 32
        parts.append(f"Temperature: {temp_c:.1f}C / {temp_f:.1f}F")
    if humidity is not None:
        parts.append(f"Humidity: {humidity:.0f}%")
    if co2 is not None:
        parts.append(f"CO2: {co2} ppm")
    if vpd is not None:
        parts.append(f"VPD: {vpd:.2f} kPa")
    if soil is not None:
        parts.append(f"Soil moisture: {soil}%")

    return "\n".join(parts) if parts else "No sensor data available."
