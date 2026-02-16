"""
Grimoire Memory System
======================

Structured persistent knowledge files organized by domain.
Pattern from Legba/Loa framework — long-term learnings that survive restarts.

Domains:
    - trading/   — Winning patterns, losing patterns, regime-specific strategies
    - cultivation/ — Cannabis grow knowledge, VPD sweet spots, light schedules
    - social/    — Engagement learnings, community patterns, personality tuning
    - market_regimes/ — Regime-specific strategy configs (bull/bear/crab)

Each grimoire is a JSON file with structured sections, updated by learning loops,
read by decision makers. Provides institutional knowledge.
"""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

log = structlog.get_logger("grimoire")

GRIMOIRE_DIR = Path("data/grimoires")


@dataclass
class GrimoireEntry:
    """A single learning entry in a grimoire."""
    key: str                     # Unique identifier
    content: str                 # The learning/insight
    confidence: float = 0.5      # 0.0-1.0
    evidence_count: int = 1      # How many observations support this
    source: str = ""             # Where this came from
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float = 0.0      # 0 = never expires


@dataclass
class Grimoire:
    """A domain-specific knowledge store."""
    domain: str
    entries: Dict[str, GrimoireEntry] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def path(self) -> Path:
        return GRIMOIRE_DIR / self.domain / "knowledge.json"

    def add(
        self,
        key: str,
        content: str,
        confidence: float = 0.5,
        source: str = "",
        tags: Optional[List[str]] = None,
        ttl_seconds: float = 0,
    ) -> GrimoireEntry:
        """Add or update a knowledge entry."""
        now = time.time()

        if key in self.entries:
            entry = self.entries[key]
            entry.content = content
            entry.confidence = min(confidence, 1.0)
            entry.evidence_count += 1
            entry.updated_at = now
            if source:
                entry.source = source
            if tags:
                entry.tags = list(set(entry.tags + tags))
            log.debug("grimoire_updated", domain=self.domain, key=key)
        else:
            entry = GrimoireEntry(
                key=key,
                content=content,
                confidence=min(confidence, 1.0),
                source=source,
                tags=tags or [],
                created_at=now,
                updated_at=now,
                expires_at=now + ttl_seconds if ttl_seconds > 0 else 0,
            )
            self.entries[key] = entry
            log.debug("grimoire_added", domain=self.domain, key=key)

        return entry

    def get(self, key: str) -> Optional[GrimoireEntry]:
        """Get a knowledge entry by key."""
        entry = self.entries.get(key)
        if entry and entry.expires_at > 0 and time.time() > entry.expires_at:
            del self.entries[key]
            return None
        return entry

    def search(self, tags: Optional[List[str]] = None, min_confidence: float = 0.0) -> List[GrimoireEntry]:
        """Search entries by tags and/or minimum confidence."""
        now = time.time()
        results = []
        for entry in self.entries.values():
            if entry.expires_at > 0 and now > entry.expires_at:
                continue
            if entry.confidence < min_confidence:
                continue
            if tags and not any(t in entry.tags for t in tags):
                continue
            results.append(entry)
        return sorted(results, key=lambda e: e.confidence, reverse=True)

    def prune_expired(self) -> int:
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, e in self.entries.items() if e.expires_at > 0 and now > e.expires_at]
        for k in expired:
            del self.entries[k]
        return len(expired)

    def reinforce(self, key: str, boost: float = 0.05) -> Optional[GrimoireEntry]:
        """Reinforce an entry (evidence supports it)."""
        entry = self.entries.get(key)
        if entry:
            entry.confidence = min(entry.confidence + boost, 1.0)
            entry.evidence_count += 1
            entry.updated_at = time.time()
        return entry

    def weaken(self, key: str, penalty: float = 0.1) -> Optional[GrimoireEntry]:
        """Weaken an entry (evidence contradicts it)."""
        entry = self.entries.get(key)
        if entry:
            entry.confidence = max(entry.confidence - penalty, 0.0)
            entry.updated_at = time.time()
            if entry.confidence <= 0.0:
                del self.entries[key]
                return None
        return entry

    def save(self) -> None:
        """Persist grimoire to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "domain": self.domain,
            "metadata": self.metadata,
            "entries": {k: asdict(v) for k, v in self.entries.items()},
        }
        self.path.write_text(json.dumps(data, indent=2))

    def load(self) -> None:
        """Load grimoire from disk."""
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
            self.metadata = data.get("metadata", {})
            for k, v in data.get("entries", {}).items():
                self.entries[k] = GrimoireEntry(**v)
        except (json.JSONDecodeError, TypeError) as e:
            log.warning("grimoire_load_error", domain=self.domain, error=str(e))

    def format_context(self, limit: int = 20, min_confidence: float = 0.3) -> str:
        """Format grimoire for injection into AI prompts."""
        entries = self.search(min_confidence=min_confidence)[:limit]
        if not entries:
            return ""

        lines = [f"## {self.domain.title()} Knowledge ({len(entries)} entries)"]
        for e in entries:
            conf = f"[{e.confidence:.0%}]"
            lines.append(f"- {conf} {e.content}")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "entries": len(self.entries),
            "avg_confidence": (
                sum(e.confidence for e in self.entries.values()) / len(self.entries)
                if self.entries else 0
            ),
            "high_confidence": len([e for e in self.entries.values() if e.confidence >= 0.7]),
        }


# --- Singleton grimoire registry ---

_grimoires: Dict[str, Grimoire] = {}


def get_grimoire(domain: str) -> Grimoire:
    """Get or create a grimoire for a domain."""
    if domain not in _grimoires:
        g = Grimoire(domain=domain)
        g.load()
        _grimoires[domain] = g
    return _grimoires[domain]


def save_all_grimoires() -> None:
    """Persist all grimoires to disk."""
    for g in _grimoires.values():
        g.prune_expired()
        g.save()
    log.info("grimoires_saved", count=len(_grimoires))


def get_all_grimoire_context(min_confidence: float = 0.4, limit_per_domain: int = 10) -> str:
    """Get formatted context from all grimoires for AI prompt injection."""
    parts = []
    for domain in ["trading", "cultivation", "social", "market_regimes"]:
        g = get_grimoire(domain)
        ctx = g.format_context(limit=limit_per_domain, min_confidence=min_confidence)
        if ctx:
            parts.append(ctx)
    return "\n\n".join(parts)
