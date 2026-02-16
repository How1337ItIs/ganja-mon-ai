"""
USDC Profit Splitter
====================

Automates the 60/25/10/5 profit allocation split:
    60% -- Compound (trading capital)
    25% -- Buy $MON (primary mission)
    10% -- Buy $GANJA (own token support, after launch)
     5% -- Burn (deflationary pressure)

Tracks all splits in a ledger for transparency and auditing.
Emits events for each allocation.

From: identity.py mon_mission.py profit allocation + openclaw USDC payment splitter
"""

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.core.events import get_event_bus, MetricsEvent

log = structlog.get_logger("splitter")

LEDGER_PATH = Path("data/payment_ledger.json")

# Allocation percentages (from identity.py)
DEFAULT_ALLOCATION = {
    "compound": 0.60,      # Grow trading capital
    "buyback_mon": 0.25,   # Buy $MON (NEVER sell)
    "buyback_ganja": 0.10, # Buy $GANJA (after launch)
    "burn": 0.05,          # Deflationary burn
}

# Token addresses
MON_MONAD = "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
MON_BASE = "0xE390612D7997B538971457cfF29aB4286cE97BE2"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


@dataclass
class SplitRecord:
    """Record of a profit split."""
    timestamp: float = field(default_factory=time.time)
    total_profit_usd: float = 0.0
    source_trade: str = ""      # Trade that generated profit
    allocations: Dict[str, float] = field(default_factory=dict)
    executed: bool = False       # True if on-chain txs were sent
    tx_hashes: Dict[str, str] = field(default_factory=dict)


@dataclass
class Batch:
    """A payment batch ready for approval and execution."""
    id: str = field(default_factory=lambda: f"batch_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    total_usd: float = 0.0
    source: str = ""
    allocations: Dict[str, float] = field(default_factory=dict)
    status: str = "pending"   # pending | approved | executed | denied
    executed_at: float = 0.0
    approval_id: str = ""     # link to ApprovalGate request if applicable


class ProfitSplitter:
    """
    Splits trading profits according to the agent's values.

    Two main workflows:

    1. Streaming: call ``split(profit_usd, source)`` after each profitable
       trade.  Amounts accumulate in pending buckets until they cross the
       batch threshold, then ``get_ready_batches()`` surfaces them.

    2. One-shot: call ``create_batch(amount)`` to build a Batch object with
       the 60/25/10/5 split, then ``execute_batch(batch)`` to record it to
       the payment ledger.  No actual blockchain transactions are fired --
       that is the trading agent's responsibility.
    """

    def __init__(
        self,
        allocation: Optional[Dict[str, float]] = None,
        min_split_usd: float = 1.0,       # Minimum profit to split
        batch_threshold: float = 100.0,    # USD threshold before batch ready
    ):
        self.allocation = allocation or dict(DEFAULT_ALLOCATION)
        self.min_split_usd = min_split_usd
        self.batch_threshold = batch_threshold
        self._ledger: List[SplitRecord] = []
        self._batches: List[Dict[str, Any]] = []
        self._pending_batches: Dict[str, float] = {
            "compound": 0.0,
            "buyback_mon": 0.0,
            "buyback_ganja": 0.0,
            "burn": 0.0,
        }
        self._load_ledger()

    # ------------------------------------------------------------------
    # Batch API (requested interface)
    # ------------------------------------------------------------------

    def create_batch(self, amount: float, source: str = "") -> Batch:
        """
        Calculate the 60/25/10/5 split for *amount* USD and return a Batch.

        The batch is NOT automatically executed or persisted -- call
        ``execute_batch()`` to commit it to the ledger.

        Args:
            amount: Total profit in USD to split.
            source: Free-text description of what generated this profit.

        Returns:
            A ``Batch`` dataclass with allocations filled in.
        """
        allocations: Dict[str, float] = {}
        for bucket, pct in self.allocation.items():
            allocations[bucket] = round(amount * pct, 4)

        batch = Batch(
            total_usd=amount,
            source=source,
            allocations=allocations,
            status="pending",
        )

        log.info(
            "batch_created",
            batch_id=batch.id,
            total=amount,
            compound=allocations.get("compound", 0),
            mon_buyback=allocations.get("buyback_mon", 0),
            ganja_buyback=allocations.get("buyback_ganja", 0),
            burn=allocations.get("burn", 0),
            source=source,
        )
        return batch

    def execute_batch(self, batch: Batch) -> Batch:
        """
        Record a batch as executed in the payment ledger.

        This does NOT perform on-chain transactions -- it logs the batch to
        ``data/payment_ledger.json`` so the trading agent (or a human) can
        act on it.  The batch status is set to ``executed`` and the
        ``executed_at`` timestamp is filled in.

        Also accumulates the allocations into the streaming pending buckets
        and appends a ``SplitRecord`` to the internal ledger for consistency.

        Args:
            batch: A Batch previously returned by ``create_batch``.

        Returns:
            The same Batch with ``status`` and ``executed_at`` updated.
        """
        batch.status = "executed"
        batch.executed_at = time.time()

        # Mirror into the streaming ledger for get_total_allocated() etc.
        record = SplitRecord(
            timestamp=batch.timestamp,
            total_profit_usd=batch.total_usd,
            source_trade=batch.source,
            allocations=batch.allocations,
            executed=True,
        )
        self._ledger.append(record)

        # Also accumulate into pending buckets so downstream can track
        for bucket, amt in batch.allocations.items():
            self._pending_batches[bucket] = self._pending_batches.get(bucket, 0) + amt

        # Persist batch to the ledger file
        self._batches.append(asdict(batch))
        self._save_ledger()

        # Emit a metrics event so the rest of the system knows
        try:
            bus = get_event_bus()
            bus.emit_nowait(MetricsEvent(
                source="splitter",
                component="profit_splitter",
                metrics={
                    "batch_id": batch.id,
                    "total_usd": batch.total_usd,
                    "allocations": batch.allocations,
                },
            ))
        except Exception:
            pass  # event bus may not be running

        log.info(
            "batch_executed",
            batch_id=batch.id,
            total=batch.total_usd,
            allocations=batch.allocations,
        )
        return batch

    # ------------------------------------------------------------------
    # Streaming split API (original interface, kept intact)
    # ------------------------------------------------------------------

    def split(self, profit_usd: float, source_trade: str = "") -> Optional[SplitRecord]:
        """
        Compute profit split for a trade.

        Args:
            profit_usd: Profit amount in USD
            source_trade: Description of the trade that generated profit

        Returns:
            SplitRecord if split was computed, None if below minimum
        """
        if profit_usd < self.min_split_usd:
            return None

        allocations = {}
        for bucket, pct in self.allocation.items():
            amount = round(profit_usd * pct, 4)
            allocations[bucket] = amount
            self._pending_batches[bucket] = self._pending_batches.get(bucket, 0) + amount

        record = SplitRecord(
            total_profit_usd=profit_usd,
            source_trade=source_trade,
            allocations=allocations,
        )
        self._ledger.append(record)
        self._save_ledger()

        log.info(
            "profit_split",
            profit=profit_usd,
            compound=allocations.get("compound", 0),
            mon_buyback=allocations.get("buyback_mon", 0),
            ganja_buyback=allocations.get("buyback_ganja", 0),
            burn=allocations.get("burn", 0),
            source=source_trade,
        )

        return record

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def get_pending_batches(self) -> Dict[str, float]:
        """Get accumulated amounts waiting for execution."""
        return dict(self._pending_batches)

    def get_ready_batches(self) -> Dict[str, float]:
        """Get batches that have reached the execution threshold."""
        return {
            k: v for k, v in self._pending_batches.items()
            if v >= self.batch_threshold
        }

    def mark_executed(self, bucket: str, tx_hash: str = "") -> None:
        """Mark a bucket as executed (on-chain tx sent), resetting its pending amount."""
        amount = self._pending_batches.get(bucket, 0)
        if amount > 0:
            self._pending_batches[bucket] = 0
            log.info("bucket_executed", bucket=bucket, amount=amount, tx=tx_hash[:12] if tx_hash else "")
            self._save_ledger()

    def get_total_allocated(self) -> Dict[str, float]:
        """Get total amounts allocated historically."""
        totals: Dict[str, float] = {"compound": 0, "buyback_mon": 0, "buyback_ganja": 0, "burn": 0}
        for record in self._ledger:
            for bucket, amount in record.allocations.items():
                totals[bucket] = totals.get(bucket, 0) + amount
        return totals

    def get_batch_history(self) -> List[Dict[str, Any]]:
        """Return the full list of batches that have been created/executed."""
        return list(self._batches)

    def get_status(self) -> Dict[str, Any]:
        totals = self.get_total_allocated()
        return {
            "allocation": self.allocation,
            "batch_threshold": self.batch_threshold,
            "total_splits": len(self._ledger),
            "total_batches": len(self._batches),
            "total_profit_usd": sum(r.total_profit_usd for r in self._ledger),
            "total_allocated": totals,
            "pending_batches": self._pending_batches,
            "ready_for_execution": self.get_ready_batches(),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_ledger(self) -> None:
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ledger": [
                {
                    "timestamp": r.timestamp,
                    "total_profit_usd": r.total_profit_usd,
                    "source_trade": r.source_trade,
                    "allocations": r.allocations,
                    "executed": r.executed,
                }
                for r in self._ledger[-200:]  # Keep last 200
            ],
            "batches": self._batches[-200:],  # Keep last 200
            "pending_batches": self._pending_batches,
        }
        LEDGER_PATH.write_text(json.dumps(data, indent=2))

    def _load_ledger(self) -> None:
        if LEDGER_PATH.exists():
            try:
                data = json.loads(LEDGER_PATH.read_text())
                self._pending_batches = data.get("pending_batches", self._pending_batches)
                self._batches = data.get("batches", [])
                for entry in data.get("ledger", []):
                    self._ledger.append(SplitRecord(
                        timestamp=entry.get("timestamp", 0),
                        total_profit_usd=entry.get("total_profit_usd", 0),
                        source_trade=entry.get("source_trade", ""),
                        allocations=entry.get("allocations", {}),
                        executed=entry.get("executed", False),
                    ))
            except (json.JSONDecodeError, KeyError):
                pass


# Singleton
_instance: Optional[ProfitSplitter] = None


def get_profit_splitter() -> ProfitSplitter:
    global _instance
    if _instance is None:
        _instance = ProfitSplitter()
    return _instance
