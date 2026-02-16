"""
Compound Learning with Quality Gates
=====================================

Extracts candidate patterns from trade outcomes.
Applies 4-gate quality filter before promoting to active strategies.

Gates:
    1. Discovery Depth — Is this non-obvious? (reject truisms)
    2. Reusability — Applies across >1 market/token/timeframe?
    3. Trigger Clarity — Can the agent detect this automatically?
    4. Verification — Statistical evidence (min 5 samples, >55% win rate)

Pattern from: Legba/Loa framework compound-orchestrator.sh
"""

import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.learning.grimoire import get_grimoire

log = structlog.get_logger("compound_learning")

DB_PATH = Path("data/compound_learning.db")


@dataclass
class CandidatePattern:
    """A pattern candidate extracted from trade data."""
    name: str
    pattern_type: str          # "source_accuracy", "time_of_day", "regime", "confluence"
    conditions: Dict[str, Any] = field(default_factory=dict)
    sample_size: int = 0
    win_rate: float = 0.0
    avg_pnl: float = 0.0
    profit_factor: float = 0.0
    discovered_at: float = field(default_factory=time.time)

    # Gate results
    gate_discovery: bool = False
    gate_reusability: bool = False
    gate_trigger: bool = False
    gate_verification: bool = False

    @property
    def passes_all_gates(self) -> bool:
        return all([
            self.gate_discovery,
            self.gate_reusability,
            self.gate_trigger,
            self.gate_verification,
        ])

    @property
    def gates_passed(self) -> int:
        return sum([
            self.gate_discovery,
            self.gate_reusability,
            self.gate_trigger,
            self.gate_verification,
        ])


@dataclass
class PromotedPattern:
    """A pattern that passed all quality gates and is active."""
    name: str
    pattern_type: str
    conditions: Dict[str, Any]
    initial_weight: float = 0.5
    current_weight: float = 0.5
    times_triggered: int = 0
    times_profitable: int = 0
    total_pnl: float = 0.0
    promoted_at: float = field(default_factory=time.time)
    last_triggered: float = 0.0


class CompoundLearning:
    """
    Extracts, validates, and promotes trading patterns.

    Lifecycle:
    1. Extract candidate patterns from trade history
    2. Apply 4-gate quality filter
    3. Promote passing patterns (initial weight 0.5)
    4. Track promoted pattern performance
    5. Decay underperforming patterns
    """

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None
        self._candidates: List[CandidatePattern] = []
        self._promoted: Dict[str, PromotedPattern] = {}

    def _ensure_db(self) -> sqlite3.Connection:
        if self._db is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(str(DB_PATH))
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    name TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    conditions TEXT,
                    sample_size INTEGER,
                    win_rate REAL,
                    avg_pnl REAL,
                    profit_factor REAL,
                    gates_passed INTEGER,
                    discovered_at REAL,
                    status TEXT DEFAULT 'candidate'
                )
            """)
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS promoted (
                    name TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    conditions TEXT,
                    current_weight REAL DEFAULT 0.5,
                    times_triggered INTEGER DEFAULT 0,
                    times_profitable INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    promoted_at REAL,
                    last_triggered REAL DEFAULT 0.0
                )
            """)
            self._db.commit()

            # Load promoted patterns
            for row in self._db.execute("SELECT * FROM promoted"):
                pp = PromotedPattern(
                    name=row[0],
                    pattern_type=row[1],
                    conditions=json.loads(row[2]),
                    current_weight=row[3],
                    times_triggered=row[4],
                    times_profitable=row[5],
                    total_pnl=row[6],
                    promoted_at=row[7],
                    last_triggered=row[8],
                )
                self._promoted[pp.name] = pp

        return self._db

    def extract_candidates(self, trade_history: List[Dict]) -> List[CandidatePattern]:
        """
        Extract candidate patterns from trade history.

        Each trade dict should have: source, token, chain, direction, pnl_percent,
        entry_time, meta, confidence.
        """
        if len(trade_history) < 5:
            return []

        candidates = []

        # Pattern 1: Source accuracy patterns
        source_stats: Dict[str, Dict] = {}
        for trade in trade_history:
            src = trade.get("source", "unknown")
            if src not in source_stats:
                source_stats[src] = {"wins": 0, "losses": 0, "total_pnl": 0.0}
            if trade.get("pnl_percent", 0) > 0:
                source_stats[src]["wins"] += 1
            else:
                source_stats[src]["losses"] += 1
            source_stats[src]["total_pnl"] += trade.get("pnl_percent", 0)

        for src, stats in source_stats.items():
            total = stats["wins"] + stats["losses"]
            if total < 5:
                continue
            win_rate = stats["wins"] / total
            avg_pnl = stats["total_pnl"] / total

            candidates.append(CandidatePattern(
                name=f"source_accuracy:{src}",
                pattern_type="source_accuracy",
                conditions={"source": src},
                sample_size=total,
                win_rate=win_rate,
                avg_pnl=avg_pnl,
                profit_factor=stats["wins"] / max(stats["losses"], 1),
            ))

        # Pattern 2: Chain performance
        chain_stats: Dict[str, Dict] = {}
        for trade in trade_history:
            chain = trade.get("chain", "unknown")
            if chain not in chain_stats:
                chain_stats[chain] = {"wins": 0, "losses": 0, "total_pnl": 0.0}
            if trade.get("pnl_percent", 0) > 0:
                chain_stats[chain]["wins"] += 1
            else:
                chain_stats[chain]["losses"] += 1
            chain_stats[chain]["total_pnl"] += trade.get("pnl_percent", 0)

        for chain, stats in chain_stats.items():
            total = stats["wins"] + stats["losses"]
            if total < 5:
                continue
            candidates.append(CandidatePattern(
                name=f"chain_performance:{chain}",
                pattern_type="chain",
                conditions={"chain": chain},
                sample_size=total,
                win_rate=stats["wins"] / total,
                avg_pnl=stats["total_pnl"] / total,
                profit_factor=stats["wins"] / max(stats["losses"], 1),
            ))

        # Pattern 3: Confidence threshold effectiveness
        confidence_buckets = {"low": [], "mid": [], "high": []}
        for trade in trade_history:
            conf = trade.get("confidence", 0.5)
            pnl = trade.get("pnl_percent", 0)
            if conf < 0.4:
                confidence_buckets["low"].append(pnl)
            elif conf < 0.7:
                confidence_buckets["mid"].append(pnl)
            else:
                confidence_buckets["high"].append(pnl)

        for bucket, pnls in confidence_buckets.items():
            if len(pnls) < 5:
                continue
            wins = sum(1 for p in pnls if p > 0)
            candidates.append(CandidatePattern(
                name=f"confidence_bucket:{bucket}",
                pattern_type="confidence",
                conditions={"confidence_bucket": bucket},
                sample_size=len(pnls),
                win_rate=wins / len(pnls),
                avg_pnl=sum(pnls) / len(pnls),
                profit_factor=wins / max(len(pnls) - wins, 1),
            ))

        self._candidates = candidates
        return candidates

    def apply_quality_gates(self, candidates: Optional[List[CandidatePattern]] = None) -> List[CandidatePattern]:
        """Apply 4-gate quality filter to candidates."""
        if candidates is None:
            candidates = self._candidates

        for c in candidates:
            # Gate 1: Discovery Depth — is this non-obvious?
            c.gate_discovery = self._gate_discovery(c)

            # Gate 2: Reusability — applies broadly?
            c.gate_reusability = self._gate_reusability(c)

            # Gate 3: Trigger Clarity — can we detect automatically?
            c.gate_trigger = self._gate_trigger(c)

            # Gate 4: Verification — statistical evidence?
            c.gate_verification = self._gate_verification(c)

        passing = [c for c in candidates if c.passes_all_gates]
        log.info(
            "quality_gates_applied",
            total=len(candidates),
            passing=len(passing),
            details={c.name: c.gates_passed for c in candidates},
        )
        return passing

    def _gate_discovery(self, c: CandidatePattern) -> bool:
        """Is this insight non-obvious?"""
        # Reject truisms (>80% win rate with low sample is likely noise)
        if c.sample_size < 10 and c.win_rate > 0.80:
            return False
        # Reject if PnL is close to zero (not actionable)
        if abs(c.avg_pnl) < 1.0:
            return False
        return True

    def _gate_reusability(self, c: CandidatePattern) -> bool:
        """Does this apply across more than one context?"""
        # Source accuracy is inherently reusable (applies to all tokens from that source)
        if c.pattern_type == "source_accuracy":
            return True
        # Chain patterns reusable across tokens on that chain
        if c.pattern_type == "chain":
            return True
        # Confidence patterns reusable universally
        if c.pattern_type == "confidence":
            return True
        # If we have enough samples, it's probably reusable
        return c.sample_size >= 10

    def _gate_trigger(self, c: CandidatePattern) -> bool:
        """Can we detect this pattern automatically?"""
        # All our pattern types have clear triggers
        # Source → check signal source
        # Chain → check chain
        # Confidence → check confidence score
        return len(c.conditions) > 0

    def _gate_verification(self, c: CandidatePattern) -> bool:
        """Is there statistical evidence?"""
        return (
            c.sample_size >= 5
            and c.win_rate >= 0.55
            and c.profit_factor >= 1.2
        )

    def promote_patterns(self, passing: List[CandidatePattern]) -> int:
        """Promote passing patterns to active status."""
        db = self._ensure_db()
        promoted_count = 0

        for c in passing:
            if c.name in self._promoted:
                # Already promoted — reinforce
                pp = self._promoted[c.name]
                pp.current_weight = min(pp.current_weight + 0.05, 1.5)
                continue

            pp = PromotedPattern(
                name=c.name,
                pattern_type=c.pattern_type,
                conditions=c.conditions,
                initial_weight=0.5,
                current_weight=0.5,
            )
            self._promoted[c.name] = pp
            promoted_count += 1

            # Persist
            db.execute(
                "INSERT OR REPLACE INTO promoted VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pp.name, pp.pattern_type, json.dumps(pp.conditions),
                 pp.current_weight, pp.times_triggered, pp.times_profitable,
                 pp.total_pnl, pp.promoted_at, pp.last_triggered),
            )

            # Also store in grimoire
            grimoire = get_grimoire("trading")
            grimoire.add(
                key=f"pattern:{c.name}",
                content=f"Pattern '{c.name}': {c.win_rate:.0%} win rate over {c.sample_size} trades, avg PnL {c.avg_pnl:.1f}%",
                confidence=min(c.win_rate, 0.9),
                source="compound_learning",
                tags=["pattern", c.pattern_type],
            )

        db.commit()

        if promoted_count > 0:
            log.info("patterns_promoted", count=promoted_count)

        return promoted_count

    def record_pattern_outcome(self, pattern_name: str, pnl: float) -> None:
        """Record outcome when a promoted pattern triggers."""
        pp = self._promoted.get(pattern_name)
        if not pp:
            return

        pp.times_triggered += 1
        pp.total_pnl += pnl
        pp.last_triggered = time.time()

        if pnl > 0:
            pp.times_profitable += 1
            pp.current_weight = min(pp.current_weight + 0.03, 1.5)
        else:
            pp.current_weight = max(pp.current_weight - 0.05, 0.1)

        # Persist
        db = self._ensure_db()
        db.execute(
            "UPDATE promoted SET current_weight=?, times_triggered=?, times_profitable=?, total_pnl=?, last_triggered=? WHERE name=?",
            (pp.current_weight, pp.times_triggered, pp.times_profitable, pp.total_pnl, pp.last_triggered, pp.name),
        )
        db.commit()

    def decay_promoted(self, decay_rate: float = 0.98) -> None:
        """Decay all promoted pattern weights toward neutral."""
        db = self._ensure_db()
        for pp in self._promoted.values():
            pp.current_weight *= decay_rate
            pp.current_weight = max(pp.current_weight, 0.1)
        db.executemany(
            "UPDATE promoted SET current_weight=? WHERE name=?",
            [(pp.current_weight, pp.name) for pp in self._promoted.values()],
        )
        db.commit()

    def get_active_patterns(self, min_weight: float = 0.3) -> Dict[str, PromotedPattern]:
        """Get currently active promoted patterns."""
        self._ensure_db()
        return {
            name: pp for name, pp in self._promoted.items()
            if pp.current_weight >= min_weight
        }

    def get_pattern_weight(self, pattern_name: str) -> float:
        """Get weight of a specific promoted pattern."""
        pp = self._promoted.get(pattern_name)
        return pp.current_weight if pp else 0.0

    def get_status(self) -> Dict[str, Any]:
        self._ensure_db()
        return {
            "candidates": len(self._candidates),
            "promoted": len(self._promoted),
            "active": len([p for p in self._promoted.values() if p.current_weight >= 0.3]),
            "top_patterns": sorted(
                [
                    {"name": p.name, "weight": round(p.current_weight, 2), "win_rate": round(p.times_profitable / max(p.times_triggered, 1), 2)}
                    for p in self._promoted.values()
                ],
                key=lambda x: x["weight"],
                reverse=True,
            )[:5],
        }


# Singleton
_instance: Optional[CompoundLearning] = None


def get_compound_learning() -> CompoundLearning:
    global _instance
    if _instance is None:
        _instance = CompoundLearning()
    return _instance
