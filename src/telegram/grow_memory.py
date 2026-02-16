"""Shared memory bridge between plant brain and Telegram bot.

Reads the grow agent's episodic memory, decision history, and sensor
trends directly from data files - giving the Telegram bot full awareness
of cultivation decisions, not just current sensor snapshots.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data file paths (on Chromebook, or fallback to WSL dev)
MEMORY_PATHS = [
    Path("/home/natha/projects/sol-cannabis/data"),
    PROJECT_ROOT / "data",
]

# Cache to avoid constant disk reads
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 120  # seconds


def _find_data_dir() -> Path | None:
    for p in MEMORY_PATHS:
        if p.exists():
            return p
    return None


def _cached_read(filename: str) -> Any:
    """Read a JSON file with caching."""
    now = time.time()
    if filename in _cache:
        ts, data = _cache[filename]
        if now - ts < CACHE_TTL:
            return data

    data_dir = _find_data_dir()
    if not data_dir:
        return None

    filepath = data_dir / filename
    if not filepath.exists():
        return None

    try:
        with open(filepath) as f:
            data = json.load(f)
        _cache[filename] = (now, data)
        return data
    except Exception as e:
        logger.debug(f"Failed to read {filename}: {e}")
        return None


def get_episodic_memory_context(count: int = 5) -> str:
    """Get the grow brain's recent episodic memory entries.

    Returns formatted text showing recent decision cycles, actions taken,
    conditions observed, and what the AI planned to do next.
    """
    memory = _cached_read("episodic_memory.json")
    if not memory:
        return ""

    entries = memory.get("entries", [])
    if not entries:
        return ""

    # Take the most recent N entries
    recent = entries[-count:]
    parts = ["## Recent Grow Brain Decisions"]

    for entry in recent:
        ts = entry.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            time_str = dt.strftime("%b %d %I:%M %p")
        except (ValueError, TypeError):
            time_str = ts[:16] if ts else "unknown"

        day = entry.get("grow_day", "?")
        label = entry.get("time_label", "")
        conditions = entry.get("conditions", {})
        actions = entry.get("actions_taken", [])
        observations = entry.get("observations", [])
        next_actions = entry.get("next_actions", [])
        day_totals = entry.get("day_totals", {})

        parts.append(f"\n**Day {day} - {label}** ({time_str})")

        # Conditions
        temp = conditions.get("temp_f") or conditions.get("temp_c")
        humidity = conditions.get("humidity")
        vpd = conditions.get("vpd")
        co2 = conditions.get("co2")
        if temp or humidity:
            cond_str = []
            if temp:
                cond_str.append(f"{temp}°{'F' if conditions.get('temp_f') else 'C'}")
            if humidity:
                cond_str.append(f"{humidity}% RH")
            if vpd:
                cond_str.append(f"VPD {vpd}")
            if co2:
                cond_str.append(f"{co2}ppm CO2")
            parts.append(f"Conditions: {', '.join(cond_str)}")

        # Actions
        if actions:
            parts.append(f"Actions: {', '.join(actions)}")
        else:
            parts.append("Actions: None (stable)")

        # Day totals
        if day_totals:
            totals = []
            if "water_ml" in day_totals:
                totals.append(f"{day_totals['water_ml']}ml watered")
            if "co2_injections" in day_totals:
                totals.append(f"{day_totals['co2_injections']} CO2 injections")
            if totals:
                parts.append(f"Day totals: {', '.join(totals)}")

        # Key observations
        if observations:
            parts.append(f"Observed: {'; '.join(observations[:2])}")

    return "\n".join(parts)


def get_decision_history(count: int = 3) -> str:
    """Get Grok's recent AI decisions with commentary.

    Reads from the latest AI decision log to show what Grok thought
    and why it took specific actions.
    """
    decisions = _cached_read("ai_decisions.json")
    if not decisions:
        # Try the single latest decision
        latest = _cached_read("latest_decision.json")
        if latest:
            decisions = [latest]
        else:
            return ""

    if isinstance(decisions, dict):
        decisions = [decisions]

    recent = decisions[-count:] if isinstance(decisions, list) else []
    if not recent:
        return ""

    parts = ["## Grok's Recent Reasoning"]
    for dec in recent:
        commentary = dec.get("commentary", "")
        analysis = dec.get("analysis", {})
        health = analysis.get("overall_health", "?")
        concerns = analysis.get("concerns", [])
        actions = dec.get("actions", [])

        if commentary:
            parts.append(f"- \"{commentary[:200]}\"")
        if health != "?":
            parts.append(f"  Health assessment: {health}")
        if concerns:
            parts.append(f"  Concerns: {'; '.join(concerns[:3])}")
        if actions:
            action_names = [a.get("tool", a.get("action", "?")) for a in actions[:3]]
            parts.append(f"  Actions taken: {', '.join(action_names)}")

    return "\n".join(parts)


def get_sensor_trends() -> str:
    """Get sensor trend data for richer context.

    Reads sensor history to calculate trends (rising/falling temp,
    drying soil, etc.) that go beyond the current snapshot.
    """
    memory = _cached_read("episodic_memory.json")
    if not memory:
        return ""

    entries = memory.get("entries", [])
    if len(entries) < 3:
        return ""

    recent = entries[-10:]
    parts = []

    # Temperature trend
    temps = [e["conditions"].get("temp_c") or e["conditions"].get("temp_f")
             for e in recent if e.get("conditions")]
    temps = [t for t in temps if t is not None]
    if len(temps) >= 3:
        trend = temps[-1] - temps[0]
        direction = "rising" if trend > 0.5 else "falling" if trend < -0.5 else "stable"
        parts.append(f"Temp trend: {direction} ({trend:+.1f}° over {len(temps)} readings)")

    # Humidity trend
    hums = [e["conditions"].get("humidity") for e in recent if e.get("conditions")]
    hums = [h for h in hums if h is not None]
    if len(hums) >= 3:
        trend = hums[-1] - hums[0]
        direction = "rising" if trend > 2 else "falling" if trend < -2 else "stable"
        parts.append(f"Humidity trend: {direction} ({trend:+.1f}%)")

    # VPD trend
    vpds = [e["conditions"].get("vpd") for e in recent if e.get("conditions")]
    vpds = [v for v in vpds if v is not None]
    if len(vpds) >= 3:
        avg = sum(vpds) / len(vpds)
        parts.append(f"VPD avg: {avg:.2f} kPa (target 0.8-1.2 for veg)")

    return "\n".join(parts) if parts else ""


def get_historical_review() -> str:
    """Get the external review agent's findings about grow decisions."""
    review = _cached_read("historical_review.json")
    if not review:
        return ""

    parts = []
    if review.get("insights"):
        parts.append("Grow insights: " + "; ".join(review["insights"][:3]))
    if review.get("patterns"):
        parts.append("Patterns: " + "; ".join(review["patterns"][:3]))
    if review.get("recommendations"):
        parts.append("Recommendations: " + "; ".join(review["recommendations"][:3]))

    return "\n".join(parts) if parts else ""


def get_full_grow_context() -> str:
    """Assemble complete grow brain context for Telegram bot injection.

    Called during response generation when grow/plant topics are detected.
    """
    sections = []

    episodic = get_episodic_memory_context(count=3)
    if episodic:
        sections.append(episodic)

    decisions = get_decision_history(count=2)
    if decisions:
        sections.append(decisions)

    trends = get_sensor_trends()
    if trends:
        sections.append(f"## Sensor Trends\n{trends}")

    review = get_historical_review()
    if review:
        sections.append(f"## Grow Review\n{review}")

    return "\n\n".join(sections) if sections else ""
