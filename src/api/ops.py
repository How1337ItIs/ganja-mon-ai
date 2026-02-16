"""
Operations Log API Router
===========================

HAL API endpoints for the operations log (ops_log.jsonl).
Lets the agent distinguish intentional restarts from crashes,
and serves as the hackathon timeline.

Endpoints:
    GET  /api/ops/log           - Read recent ops log entries
    GET  /api/ops/restarts      - Get recent restart events (with reason)
    GET  /api/ops/timeline      - Hackathon timeline view (all events, grouped by day)
    POST /api/ops/log           - Append a new ops log entry
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ops", tags=["operations"])

PROJECT_ROOT = Path(__file__).parent.parent.parent
OPS_LOG = PROJECT_ROOT / "data" / "ops_log.jsonl"


class OpsLogEntry(BaseModel):
    event: str  # deploy, service_restart, config_change, incident, fix, milestone
    actor: str  # antigravity, codex, claude, gemini, user, system, openclaw
    detail: str  # human-readable description
    category: str = "general"  # upgrade, maintenance, fix, incident, milestone, meta
    files: Optional[list[str]] = None  # affected files


def _read_log(limit: int = 100) -> list[dict]:
    """Read the ops log, most recent first."""
    if not OPS_LOG.exists():
        return []
    entries = []
    for line in OPS_LOG.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    entries.reverse()  # most recent first
    return entries[:limit]


@router.get("/log")
async def get_ops_log(
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None, description="Filter: upgrade, maintenance, fix, incident, milestone"),
    actor: Optional[str] = Query(None, description="Filter by actor: antigravity, codex, claude, gemini, user"),
):
    """Read recent ops log entries."""
    entries = _read_log(limit=500)
    if category:
        entries = [e for e in entries if e.get("category") == category]
    if actor:
        entries = [e for e in entries if e.get("actor") == actor]
    return {"entries": entries[:limit], "count": len(entries[:limit])}


@router.get("/restarts")
async def get_recent_restarts(
    limit: int = Query(10, ge=1, le=50),
):
    """Get recent service restart events with reasons.
    
    The agent should call this on startup to understand WHY it was restarted.
    If the most recent restart is 'maintenance' or 'upgrade', no alarm needed.
    If no recent restart is logged, it was likely a crash or OOM kill.
    """
    entries = _read_log(limit=500)
    restarts = [
        e for e in entries
        if e.get("event") in ("service_restart", "incident")
    ]
    
    # Add a hint for the agent
    if restarts:
        latest = restarts[0]
        if latest.get("category") in ("maintenance", "upgrade"):
            hint = "Most recent restart was intentional (maintenance/upgrade). No action needed."
        elif latest.get("category") == "incident":
            hint = "Most recent restart was due to an INCIDENT. Check detail for root cause."
        else:
            hint = "Check detail field for restart context."
    else:
        hint = "No restart events logged. This might be a crash/OOM. Check journalctl."
    
    return {
        "hint": hint,
        "restarts": restarts[:limit],
        "count": len(restarts[:limit]),
    }


@router.get("/timeline")
async def get_hackathon_timeline():
    """Full hackathon timeline, grouped by day, for presentation."""
    entries = _read_log(limit=1000)
    entries.reverse()  # chronological for timeline
    
    days = {}
    for entry in entries:
        ts = entry.get("ts", "")
        day = ts[:10] if len(ts) >= 10 else "unknown"
        days.setdefault(day, []).append(entry)
    
    return {
        "title": "Grok & Mon — Development Timeline",
        "total_events": len(entries),
        "days": days,
    }


@router.post("/log")
async def append_ops_log(entry: OpsLogEntry):
    """Append a new entry to the ops log."""
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": entry.event,
        "actor": entry.actor,
        "detail": entry.detail,
        "category": entry.category,
    }
    if entry.files:
        record["files"] = entry.files
    
    OPS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(OPS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    
    logger.info(f"[OPS] {entry.event} by {entry.actor}: {entry.detail}")
    return {"status": "logged", "record": record}
