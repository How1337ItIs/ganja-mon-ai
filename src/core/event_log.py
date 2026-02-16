"""
Shared Event Log
================

A thin append-only JSONL log that any subsystem (grow, trading, social) can
write to. Provides a single "Mon's day" narrative that the unified context
aggregator and social engagement daemon can read.

Schema per line::

    {
        "ts": "2026-02-09T14:30:00",
        "source": "grow" | "trading" | "social" | "email" | "a2a",
        "category": "action" | "observation" | "milestone" | "decision" | "error",
        "summary": "Watered Mon 200ml — soil was at 22%",
        "data": {}  // optional structured payload
    }

Usage::

    from src.core.event_log import log_event, read_recent_events

    # Any subsystem can write
    log_event("grow", "action", "Watered Mon 200ml", {"amount_ml": 200})
    log_event("trading", "decision", "Opened long on ETH at $3200")

    # Unified context or social daemon can read
    events = read_recent_events(hours=24, sources=["grow", "trading"])
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

EVENT_LOG_PATH = Path(__file__).parent.parent.parent / "data" / "unified_event_log.jsonl"


def log_event(
    source: str,
    category: str,
    summary: str,
    data: Optional[dict] = None,
) -> bool:
    """Append one event to the shared log. Returns True on success."""
    entry = {
        "ts": datetime.now().isoformat(),
        "source": source,
        "category": category,
        "summary": summary,
    }
    if data:
        entry["data"] = data
    try:
        EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(EVENT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to write event log: {e}")
        return False


def read_recent_events(
    hours: int = 24,
    sources: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
    limit: int = 50,
) -> list[dict]:
    """Read recent events from the shared log.

    Args:
        hours: How far back to look (default 24h).
        sources: Filter by source (e.g. ["grow", "trading"]). None = all.
        categories: Filter by category. None = all.
        limit: Max events to return (most recent first).
    """
    if not EVENT_LOG_PATH.exists():
        return []

    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
    events: list[dict] = []

    try:
        with open(EVENT_LOG_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("ts", "") < cutoff:
                    continue
                if sources and entry.get("source") not in sources:
                    continue
                if categories and entry.get("category") not in categories:
                    continue
                events.append(entry)
    except Exception as e:
        logger.error(f"Failed to read event log: {e}")

    return events[-limit:]


def rotate_event_log(keep_hours: int = 72):
    """Remove events older than keep_hours. Called periodically."""
    if not EVENT_LOG_PATH.exists():
        return

    cutoff = (datetime.now() - timedelta(hours=keep_hours)).isoformat()
    kept: list[str] = []

    try:
        with open(EVENT_LOG_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("ts", "") >= cutoff:
                        kept.append(json.dumps(entry))
                except json.JSONDecodeError:
                    continue

        with open(EVENT_LOG_PATH, "w") as f:
            for entry_str in kept:
                f.write(entry_str + "\n")
    except Exception as e:
        logger.error(f"Failed to rotate event log: {e}")
