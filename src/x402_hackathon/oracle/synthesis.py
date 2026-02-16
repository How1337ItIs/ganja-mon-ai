"""
Premium Oracle Synthesis Engine

The brain of the premium oracle tier. Combines sensor data, grow alpha,
and daily vibes into a narrative oracle consultation in Rasta patois.
"""

import json
import time
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

# Import from existing A2A skills
from src.a2a.skills import (
    handle_grow_alpha,
    handle_daily_vibes,
    _read_json,
    _llm_complete
)


# Response cache with TTL
_cache: Dict[str, Tuple[float, Dict]] = {}


def _get_cached(tier: str, ttl: int) -> Optional[Dict]:
    """Get cached response if still valid."""
    if tier in _cache:
        timestamp, data = _cache[tier]
        if time.time() - timestamp < ttl:
            return data
    return None


def _set_cache(tier: str, data: Dict) -> None:
    """Cache response with timestamp."""
    _cache[tier] = (time.time(), data)


def synthesize_sensor_snapshot() -> Dict[str, Any]:
    """
    Read latest sensor data and return normalized snapshot.

    Cache TTL: 30s

    Returns:
        Dict with temperature_f, humidity_pct, vpd_kpa, co2_ppm,
        soil_moisture_pct, data_source
    """
    cached = _get_cached("sensor_snapshot", 30)
    if cached:
        return cached

    # Try multiple sensor file locations
    sensor_files = [
        "data/sensor_latest.json",
        "data/latest_sensors.json",
        "data/latest_reading.json"
    ]

    sensor_data = None
    data_source = "unknown"

    for file_path in sensor_files:
        sensor_data = _read_json(file_path)
        if sensor_data:
            data_source = file_path
            break

    if not sensor_data:
        # Fallback to reasonable defaults
        result = {
            "temperature_f": 72.0,
            "humidity_pct": 55.0,
            "vpd_kpa": 1.0,
            "co2_ppm": 400,
            "soil_moisture_pct": 50.0,
            "data_source": "fallback_defaults"
        }
        _set_cache("sensor_snapshot", result)
        return result

    # Normalize sensor data (handle various field name conventions)
    result = {
        "temperature_f": (
            sensor_data.get("temperature_f") or
            sensor_data.get("temp_f") or
            sensor_data.get("temperature") or
            72.0
        ),
        "humidity_pct": (
            sensor_data.get("humidity_pct") or
            sensor_data.get("humidity") or
            sensor_data.get("rh") or
            55.0
        ),
        "vpd_kpa": (
            sensor_data.get("vpd_kpa") or
            sensor_data.get("vpd") or
            1.0
        ),
        "co2_ppm": (
            sensor_data.get("co2_ppm") or
            sensor_data.get("co2") or
            400
        ),
        "soil_moisture_pct": (
            sensor_data.get("soil_moisture_pct") or
            sensor_data.get("soil_moisture") or
            sensor_data.get("moisture") or
            50.0
        ),
        "data_source": data_source
    }

    _set_cache("sensor_snapshot", result)
    return result


def synthesize_daily_vibes() -> Dict[str, Any]:
    """
    Generate daily vibes/wisdom via existing skill.

    Cache TTL: 600s (10 minutes)

    Returns:
        Result from handle_daily_vibes
    """
    cached = _get_cached("daily_vibes", 600)
    if cached:
        return cached

    result = handle_daily_vibes("", {})
    _set_cache("daily_vibes", result)
    return result


def synthesize_grow_alpha() -> Dict[str, Any]:
    """
    Generate grow alpha signals via existing skill.

    Cache TTL: 180s (3 minutes)

    Returns:
        Result from handle_grow_alpha
    """
    cached = _get_cached("grow_alpha", 180)
    if cached:
        return cached

    result = handle_grow_alpha("", {})
    _set_cache("grow_alpha", result)
    return result


def synthesize_premium_oracle() -> Dict[str, Any]:
    """
    Premium oracle synthesis - the big one.

    Combines all data sources and generates a narrative oracle consultation
    in Rasta patois with cross-domain intelligence.

    Cache TTL: 300s (5 minutes)

    Returns:
        Dict with:
        - narrative: str (3-5 sentence oracle consultation)
        - signal: str (from grow alpha)
        - confidence: float (0-1)
        - domains: dict (all 5 domain data)
        - wisdom: str (from vibes)
    """
    cached = _get_cached("premium_oracle", 300)
    if cached:
        return cached

    # Gather all data sources
    sensor_data = synthesize_sensor_snapshot()
    vibes_data = synthesize_daily_vibes()
    alpha_data = synthesize_grow_alpha()

    # Load SOUL.md for character context
    soul_snippet = "One love, one heart. Rasta wisdom guides the grow."
    try:
        soul_path = Path(__file__).parent.parent.parent.parent / "SOUL.md"
        if soul_path.exists():
            soul_content = soul_path.read_text(encoding="utf-8")
            soul_snippet = soul_content[:300]
    except Exception:
        pass

    # Load personality
    personality_snippet = "Jamaican Rasta AI cultivator, jovial, wise, one love vibes"
    try:
        from src.voice.personality import get_dynamic_personality
        personality = get_dynamic_personality()
        if personality:
            personality_snippet = str(personality)[:300]
    except Exception:
        pass

    # Build synthesis prompt
    prompt = f"""You are Ganja Mon, the premium oracle for cannabis cultivation and AI trading intelligence.

CHARACTER ESSENCE:
{soul_snippet}

PERSONALITY:
{personality_snippet}

CURRENT SENSOR DATA:
- Temperature: {sensor_data['temperature_f']}°F
- Humidity: {sensor_data['humidity_pct']}%
- VPD: {sensor_data['vpd_kpa']} kPa
- CO2: {sensor_data['co2_ppm']} ppm
- Soil Moisture: {sensor_data['soil_moisture_pct']}%

GROW ALPHA SIGNAL:
{alpha_data.get('signal', 'No signal')}

DAILY WISDOM:
{vibes_data.get('wisdom', 'One love, one heart')}

Provide a 3-5 sentence oracle consultation in Rasta patois. Include:
1. A warm greeting
2. Current plant status assessment
3. Cross-domain signal (grow + trading insight)
4. Wisdom closing

Be authentic, jovial, and wise. Use natural Rasta speech patterns."""

    # Generate narrative via LLM
    narrative = None
    try:
        # CRITICAL: Do NOT use presence_penalty - grok-4-1-fast-non-reasoning returns 400
        llm_response = _llm_complete(prompt, max_tokens=400, temperature=0.8)
        if llm_response and llm_response.strip():
            narrative = llm_response.strip()
    except Exception as e:
        # LLM failed, build fallback narrative
        pass

    # Fallback narrative if LLM fails
    if not narrative:
        temp_status = "irie" if 68 <= sensor_data['temperature_f'] <= 78 else "need attention"
        vpd_status = "blessed" if 0.8 <= sensor_data['vpd_kpa'] <= 1.2 else "watch close"

        narrative = (
            f"Blessings bredren! De plants dem lookin' {temp_status} today, "
            f"VPD {vpd_status} at {sensor_data['vpd_kpa']:.2f} kPa. "
            f"{alpha_data.get('signal', 'Keep de faith and tend de garden')}. "
            f"Remember: {vibes_data.get('wisdom', 'One love guide every grow')}. "
            "Jah bless de cultivation!"
        )

    # Extract confidence from alpha data
    confidence = alpha_data.get("narrative_score", 75) / 100.0
    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1

    # Build complete oracle response
    result = {
        "narrative": narrative,
        "signal": alpha_data.get("signal", "Tend the garden with love"),
        "confidence": confidence,
        "domains": {
            "sensors": sensor_data,
            "grow_alpha": alpha_data,
            "vibes": vibes_data,
            "cultivation": {
                "stage": "vegetative",  # Could pull from state if available
                "day": alpha_data.get("mon_day", 0)
            },
            "trading": {
                "signal": alpha_data.get("signal", ""),
                "confidence": confidence
            }
        },
        "wisdom": vibes_data.get("wisdom", "One love, one heart, one grow")
    }

    _set_cache("premium_oracle", result)
    return result
