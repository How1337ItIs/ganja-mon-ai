"""
Grimoire API Router
===================

HAL API endpoints for the grimoire learning system.
These endpoints allow OpenClaw skills to read from and write to domain grimoires.

Endpoints:
    GET  /api/learning/grimoire/list     - List entries for a domain
    GET  /api/learning/grimoire/context  - Get formatted context for AI prompts
    GET  /api/learning/grimoire/stats    - Get stats for all grimoire domains
    POST /api/learning/grimoire/add      - Add an entry to a grimoire domain
    POST /api/learning/grimoire/reinforce - Reinforce an existing entry
    POST /api/learning/grimoire/weaken   - Weaken an existing entry
"""

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning/grimoire", tags=["grimoire"])


# --- Request/Response Models ---

class GrimoireAddRequest(BaseModel):
    """Request to add an entry to a grimoire domain."""
    domain: str = Field(..., description="Grimoire domain: cultivation, trading, social, market_regimes")
    key: Optional[str] = Field(None, description="Unique key. Auto-generated from content if not provided.")
    entry: str = Field(..., description="The learning/insight content")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    source: str = Field("openclaw", description="Where this learning came from")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    ttl_seconds: float = Field(0, description="Time-to-live in seconds. 0 = never expires")


class GrimoireReinforceRequest(BaseModel):
    """Request to reinforce or weaken an entry."""
    domain: str
    key: str
    boost: float = Field(0.05, description="Amount to adjust confidence (positive for reinforce)")


class GrimoireEntryResponse(BaseModel):
    """A single grimoire entry."""
    key: str
    content: str
    confidence: float
    evidence_count: int
    source: str
    tags: List[str]
    created_at: float
    updated_at: float


# --- Endpoints ---

@router.get("/list")
async def list_grimoire_entries(
    domain: str = Query(..., description="Domain to list: cultivation, trading, social, market_regimes"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(50, ge=1, le=200),
):
    """List entries in a grimoire domain, optionally filtered by tags and confidence."""
    from src.learning.grimoire import get_grimoire

    VALID_DOMAINS = ["cultivation", "trading", "social", "market_regimes"]
    if domain not in VALID_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {VALID_DOMAINS}")

    g = get_grimoire(domain)
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    entries = g.search(tags=tag_list, min_confidence=min_confidence)[:limit]

    return {
        "domain": domain,
        "count": len(entries),
        "entries": [
            {
                "key": e.key,
                "content": e.content,
                "confidence": e.confidence,
                "evidence_count": e.evidence_count,
                "source": e.source,
                "tags": e.tags,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            }
            for e in entries
        ],
    }


@router.get("/context")
async def get_grimoire_context(
    min_confidence: float = Query(0.4, ge=0.0, le=1.0),
    limit_per_domain: int = Query(10, ge=1, le=50),
):
    """Get formatted context from all grimoires for AI prompt injection."""
    from src.learning.grimoire import get_all_grimoire_context

    context = get_all_grimoire_context(
        min_confidence=min_confidence,
        limit_per_domain=limit_per_domain,
    )
    return {"context": context}


@router.get("/stats")
async def get_grimoire_stats():
    """Get statistics for all grimoire domains."""
    from src.learning.grimoire import get_grimoire

    domains = ["cultivation", "trading", "social", "market_regimes"]
    stats = {}
    for domain in domains:
        g = get_grimoire(domain)
        stats[domain] = g.get_stats()

    return {"domains": stats}


@router.post("/add")
async def add_grimoire_entry(req: GrimoireAddRequest):
    """Add a learning entry to a grimoire domain."""
    from src.learning.grimoire import get_grimoire

    VALID_DOMAINS = ["cultivation", "trading", "social", "market_regimes"]
    if req.domain not in VALID_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Invalid domain. Must be one of: {VALID_DOMAINS}")

    g = get_grimoire(req.domain)

    # Auto-generate key if not provided
    key = req.key
    if not key:
        # Create a key from the first 60 chars of content + timestamp
        slug = req.entry[:60].lower().replace(" ", "_").replace("/", "_")
        key = f"{slug}_{int(time.time())}"

    entry = g.add(
        key=key,
        content=req.entry,
        confidence=req.confidence,
        source=req.source,
        tags=req.tags,
        ttl_seconds=req.ttl_seconds,
    )
    g.save()

    logger.info(f"Grimoire entry added: {req.domain}/{key} (confidence={req.confidence})")

    return {
        "status": "added",
        "domain": req.domain,
        "key": entry.key,
        "confidence": entry.confidence,
        "evidence_count": entry.evidence_count,
    }


@router.post("/reinforce")
async def reinforce_grimoire_entry(req: GrimoireReinforceRequest):
    """Reinforce a grimoire entry (evidence supports it)."""
    from src.learning.grimoire import get_grimoire

    g = get_grimoire(req.domain)
    entry = g.reinforce(req.key, boost=req.boost)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry '{req.key}' not found in {req.domain}")

    g.save()
    return {
        "status": "reinforced",
        "domain": req.domain,
        "key": req.key,
        "new_confidence": entry.confidence,
        "evidence_count": entry.evidence_count,
    }


@router.post("/weaken")
async def weaken_grimoire_entry(req: GrimoireReinforceRequest):
    """Weaken a grimoire entry (evidence contradicts it)."""
    from src.learning.grimoire import get_grimoire

    g = get_grimoire(req.domain)
    entry = g.weaken(req.key, penalty=req.boost)
    if entry is None:
        # Entry was deleted because confidence hit 0
        g.save()
        return {
            "status": "deleted",
            "domain": req.domain,
            "key": req.key,
            "reason": "confidence dropped to 0",
        }

    g.save()
    return {
        "status": "weakened",
        "domain": req.domain,
        "key": req.key,
        "new_confidence": entry.confidence,
    }
