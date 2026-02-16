"""
Anti-Robot Engagement Patterns
===============================

Makes automated posting look human. Jittered timestamps, variable lengths,
organic emoji usage, time-based modulation.

Pattern from: dragon-userbot/ + elizaos/ best practices.

Rules:
    - Jittered timestamps (±5min random variance)
    - Variable post length (1 sentence to 100 words)
    - Natural typos/corrections occasionally
    - Ask questions ("fam what do you think?")
    - Time-based modulation: peak hours 150% freq, night 40%
    - No templated emoji patterns
"""

import random
import time
from datetime import datetime
from typing import Optional

import structlog

log = structlog.get_logger("anti_robot")

# Peak hours (UTC) — crypto is global but US hours are highest engagement
PEAK_HOURS = set(range(13, 22))      # 1PM-10PM UTC (8AM-5PM EST)
MODERATE_HOURS = set(range(9, 13))    # 9AM-1PM UTC
QUIET_HOURS = set(range(0, 9))       # Late night UTC

# Frequency multipliers
FREQ_PEAK = 1.5
FREQ_MODERATE = 1.0
FREQ_QUIET = 0.4

# Engagement closers (make posts feel human)
CLOSERS_CASUAL = [
    "",  # No closer most of the time
    "",
    "",
    "ya know?",
    "fam what do you think?",
    "just sayin",
    "lmk",
    "thoughts?",
    "real talk",
    "irie",
    "one love",
    "seen?",
]

CLOSERS_ALPHA = [
    "",
    "not financial advice tho",
    "DYOR always",
    "NFA obviously",
    "watching this one close",
    "keep your eyes peeled",
]


def get_frequency_multiplier(hour: Optional[int] = None) -> float:
    """Get posting frequency multiplier for current hour."""
    if hour is None:
        hour = datetime.utcnow().hour

    if hour in PEAK_HOURS:
        return FREQ_PEAK
    elif hour in MODERATE_HOURS:
        return FREQ_MODERATE
    elif hour in QUIET_HOURS:
        return FREQ_QUIET
    return FREQ_MODERATE


def jitter_delay(base_seconds: float, variance_pct: float = 0.3) -> float:
    """Add random jitter to a delay. Returns jittered seconds."""
    jitter = base_seconds * variance_pct
    return base_seconds + random.uniform(-jitter, jitter)


def should_post_now(
    base_interval_minutes: float,
    last_post_time: float,
    platform: str = "",
) -> bool:
    """Decide if we should post now, accounting for time-of-day and jitter."""
    freq = get_frequency_multiplier()
    adjusted_interval = base_interval_minutes / freq

    # Add jitter (±30% of interval)
    jittered = jitter_delay(adjusted_interval * 60, variance_pct=0.3)

    elapsed = time.time() - last_post_time
    return elapsed >= jittered


def humanize_length(target_length: int) -> int:
    """Vary content length naturally (±20%)."""
    variance = int(target_length * 0.2)
    return max(20, target_length + random.randint(-variance, variance))


def add_organic_closer(text: str, post_type: str = "general") -> str:
    """Maybe add a natural conversation closer."""
    if random.random() > 0.3:  # 70% of the time, no closer
        return text

    closers = CLOSERS_ALPHA if post_type in ("trade_call", "alpha_insight") else CLOSERS_CASUAL
    closer = random.choice(closers)
    if not closer:
        return text

    # Add with natural punctuation
    if text.endswith((".", "!", "?")):
        return f"{text} {closer}"
    else:
        return f"{text}. {closer.capitalize() if random.random() > 0.5 else closer}"


def simulate_typing_delay(content_length: int) -> float:
    """Simulate human typing time (for platforms that track it)."""
    # ~40 WPM = ~200 chars/min = ~3.3 chars/sec
    base_time = content_length / 3.3
    # Add thinking pauses
    pauses = random.randint(0, 3) * random.uniform(0.5, 2.0)
    return base_time + pauses


def vary_emoji_usage(text: str) -> str:
    """Add organic emoji usage (not templated patterns)."""
    # Only 20% of posts get emoji
    if random.random() > 0.2:
        return text

    # Contextual emoji (not templated)
    contextual = {
        "profit": ["💰", "📈", "🔥"],
        "loss": ["📉", "😤"],
        "plant": ["🌱", "💧"],
        "chill": ["😎", "✌️", "🙏"],
        "alpha": ["👀", "🔍", "💎"],
    }

    # Pick one category at random
    category = random.choice(list(contextual.keys()))
    emoji = random.choice(contextual[category])

    # Place at end (most natural)
    return f"{text} {emoji}"


def get_post_schedule(
    platform: str,
    posts_per_day: int = 8,
) -> list:
    """Generate a humanized posting schedule for the day."""
    schedule = []
    interval = 24 * 60 / posts_per_day  # minutes between posts

    current_minute = random.randint(0, 59)  # Random start

    for i in range(posts_per_day):
        hour = int(current_minute / 60) % 24

        # Skip very quiet hours (reduce to 40%)
        freq = get_frequency_multiplier(hour)
        if freq < 0.5 and random.random() > 0.4:
            current_minute += interval
            continue

        # Add heavy jitter (±45 min)
        jittered_minute = current_minute + random.uniform(-45, 45)
        jittered_hour = int(jittered_minute / 60) % 24
        jittered_min = int(jittered_minute % 60)

        schedule.append({
            "hour": jittered_hour,
            "minute": jittered_min,
            "platform": platform,
        })

        current_minute += interval

    return sorted(schedule, key=lambda x: x["hour"] * 60 + x["minute"])
