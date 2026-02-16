"""
Human Approval Gate
===================

Intercepts high-value payment batches for human approval via Telegram.

Two modes:
    1. **Auto-approve** -- batches under ``auto_approve_limit`` (default $50)
       are approved immediately with a Telegram notification.
    2. **Manual approve** -- batches at or above the limit require the admin
       to reply ``/approve <batch_id>`` or ``/deny <batch_id>`` within the
       timeout window (default 5 min).  If no response arrives the batch is
       auto-denied.

The gate works with ``Batch`` objects from the ``ProfitSplitter``.

Pattern from: LetsPing / cordia-openclaw-skill
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

log = structlog.get_logger("approval_gate")

PENDING_FILE = Path("data/pending_approvals.json")
HISTORY_FILE = Path("data/approval_history.json")


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"
    AUTO_DENIED = "auto_denied"


class RiskLevel(str, Enum):
    LOW = "low"           # No approval needed
    MEDIUM = "medium"     # Notification only
    HIGH = "high"         # Requires explicit approval
    CRITICAL = "critical" # Requires "YES" reply + 5min timeout


@dataclass
class ApprovalRequest:
    """A request waiting for human approval."""
    id: str
    action_type: str          # "batch", "trade", "strategy_change", "withdrawal"
    description: str
    risk_level: str
    amount_usd: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    timeout_seconds: float = 300.0  # 5 min default
    status: str = "pending"
    responded_at: float = 0.0
    response_message: str = ""

    @property
    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.timeout_seconds

    @property
    def is_resolved(self) -> bool:
        return self.status != "pending"


# Default risk thresholds
DEFAULT_THRESHOLDS = {
    "trade_notify": 500.0,       # Notify for trades > $500
    "trade_approve": 5000.0,     # Require approval > $5000
    "strategy_change": 0.20,     # 20% weight change
    "withdrawal": 100.0,         # Any withdrawal > $100
    "auto_approve_limit": 50.0,  # Auto-approve payment batches under this
}


class ApprovalGate:
    """
    Gates high-value payment batches and other risky actions through
    human approval via Telegram.

    Batch flow:
        1. ``request_approval(batch)`` -- assess the batch amount.
        2. If ``batch.total_usd < auto_approve_limit`` -- auto-approve,
           send a Telegram *notification* (no reply needed).
        3. Otherwise -- send a Telegram message requesting approval and
           block until the admin responds or the timeout expires.
        4. ``handle_response(batch_id, approved)`` -- called by the
           Telegram bot command handler when the admin replies.
    """

    def __init__(
        self,
        auto_approve_limit: float = 50.0,
        thresholds: Optional[Dict[str, float]] = None,
        notify_callback: Optional[Callable] = None,
        timeout_seconds: float = 300.0,
    ):
        self.auto_approve_limit = auto_approve_limit
        self.timeout_seconds = timeout_seconds
        self.thresholds = thresholds or dict(DEFAULT_THRESHOLDS)
        self.thresholds["auto_approve_limit"] = self.auto_approve_limit
        self._notify_callback = notify_callback  # async Telegram send fn
        self._pending: Dict[str, ApprovalRequest] = {}
        self._history: List[Dict[str, Any]] = []
        self._load_pending()
        self._load_history()

    # ------------------------------------------------------------------
    # Batch-oriented API (requested interface)
    # ------------------------------------------------------------------

    async def request_approval(self, batch: Any) -> ApprovalRequest:
        """
        Request approval for a payment batch from the splitter.

        Args:
            batch: A ``Batch`` dataclass (from ``ProfitSplitter.create_batch``).
                   Must have ``.id``, ``.total_usd``, ``.allocations``, ``.source``.

        Returns:
            An ``ApprovalRequest`` with its final ``status`` set.
        """
        amount = getattr(batch, "total_usd", 0.0)
        batch_id = getattr(batch, "id", f"batch_{int(time.time())}")
        source = getattr(batch, "source", "")
        allocations = getattr(batch, "allocations", {})

        # Build a human-readable description
        alloc_lines = ", ".join(
            f"{k}: ${v:,.2f}" for k, v in allocations.items()
        )
        description = (
            f"Payment batch ${amount:,.2f}"
            + (f" from {source}" if source else "")
            + f" [{alloc_lines}]"
        )

        request = ApprovalRequest(
            id=batch_id,
            action_type="batch",
            description=description,
            risk_level=RiskLevel.LOW.value if amount < self.auto_approve_limit else RiskLevel.HIGH.value,
            amount_usd=amount,
            details={"allocations": allocations, "source": source},
            timeout_seconds=self.timeout_seconds,
        )

        # -- Auto-approve small batches --
        if amount < self.auto_approve_limit:
            request.status = ApprovalStatus.AUTO_APPROVED.value
            request.responded_at = time.time()
            self._record_history(request)

            # Fire-and-forget notification (no reply needed)
            await self._send_notification(request, needs_reply=False)

            log.info(
                "batch_auto_approved",
                batch_id=batch_id,
                amount=amount,
            )
            return request

        # -- Require manual approval --
        self._pending[request.id] = request
        self._save_pending()

        await self._send_notification(request, needs_reply=True)

        log.info(
            "batch_approval_requested",
            batch_id=batch_id,
            amount=amount,
            timeout=self.timeout_seconds,
        )

        # Block until resolved or expired
        while not request.is_resolved and not request.is_expired:
            await asyncio.sleep(5)

        if request.is_expired and not request.is_resolved:
            request.status = ApprovalStatus.AUTO_DENIED.value
            request.responded_at = time.time()
            log.warning("batch_approval_expired", batch_id=batch_id)

        # Clean up
        self._pending.pop(request.id, None)
        self._record_history(request)
        self._save_pending()

        return request

    def handle_response(self, batch_id: str, approved: bool, message: str = "") -> bool:
        """
        Process an admin's approval/denial for a pending batch.

        Called by the Telegram bot when the admin sends:
            ``/approve <batch_id>`` or ``/deny <batch_id>``

        Args:
            batch_id: The batch ID to respond to.
            approved: True to approve, False to deny.
            message: Optional free-text from the admin.

        Returns:
            True if the response was recorded, False if no matching
            pending request was found.
        """
        request = self._pending.get(batch_id)
        if not request:
            log.warning("handle_response_not_found", batch_id=batch_id)
            return False

        request.status = (
            ApprovalStatus.APPROVED.value if approved
            else ApprovalStatus.DENIED.value
        )
        request.responded_at = time.time()
        request.response_message = message

        log.info(
            "batch_approval_response",
            batch_id=batch_id,
            approved=approved,
            message=message,
        )
        return True

    # ------------------------------------------------------------------
    # Generic action API (kept for non-batch actions)
    # ------------------------------------------------------------------

    def assess_risk(self, action_type: str, amount_usd: float = 0, **kwargs) -> RiskLevel:
        """Assess the risk level of an action."""
        if action_type == "batch":
            if amount_usd < self.auto_approve_limit:
                return RiskLevel.LOW
            return RiskLevel.HIGH

        if action_type == "trade":
            if amount_usd >= self.thresholds.get("trade_approve", 5000):
                return RiskLevel.CRITICAL
            elif amount_usd >= self.thresholds.get("trade_notify", 500):
                return RiskLevel.HIGH
            return RiskLevel.LOW

        elif action_type == "strategy_change":
            change_pct = kwargs.get("change_pct", 0)
            if abs(change_pct) >= self.thresholds.get("strategy_change", 0.20):
                return RiskLevel.HIGH
            return RiskLevel.LOW

        elif action_type == "withdrawal":
            if amount_usd >= self.thresholds.get("withdrawal", 100):
                return RiskLevel.CRITICAL
            return RiskLevel.MEDIUM

        elif action_type == "new_strategy":
            return RiskLevel.HIGH

        return RiskLevel.LOW

    async def request_action_approval(
        self,
        action_type: str,
        description: str,
        amount_usd: float = 0,
        timeout_seconds: float = 300.0,
        **details,
    ) -> ApprovalRequest:
        """
        Request approval for a generic (non-batch) action.

        For LOW risk: auto-approves immediately.
        For MEDIUM: notifies and auto-approves.
        For HIGH/CRITICAL: waits for human response (or timeout).
        """
        risk = self.assess_risk(action_type, amount_usd, **details)

        request = ApprovalRequest(
            id=f"{action_type}_{int(time.time())}_{id(details) % 10000}",
            action_type=action_type,
            description=description,
            risk_level=risk.value,
            amount_usd=amount_usd,
            details=details,
            timeout_seconds=timeout_seconds,
        )

        if risk == RiskLevel.LOW:
            request.status = ApprovalStatus.APPROVED.value
            request.responded_at = time.time()
            self._record_history(request)
            return request

        if risk == RiskLevel.MEDIUM:
            await self._send_notification(request, needs_reply=False)
            request.status = ApprovalStatus.APPROVED.value
            request.responded_at = time.time()
            self._record_history(request)
            return request

        # HIGH or CRITICAL
        self._pending[request.id] = request
        self._save_pending()
        await self._send_notification(request, needs_reply=True)

        log.info(
            "action_approval_requested",
            id=request.id,
            action=action_type,
            risk=risk.value,
            amount=amount_usd,
            timeout=timeout_seconds,
        )

        while not request.is_resolved and not request.is_expired:
            await asyncio.sleep(5)

        if request.is_expired and not request.is_resolved:
            request.status = ApprovalStatus.AUTO_DENIED.value
            request.responded_at = time.time()
            log.warning("action_approval_expired", id=request.id, action=action_type)

        self._pending.pop(request.id, None)
        self._record_history(request)
        self._save_pending()

        return request

    # Backward compat alias
    respond = handle_response

    # ------------------------------------------------------------------
    # Telegram notification
    # ------------------------------------------------------------------

    async def _send_notification(self, request: ApprovalRequest, needs_reply: bool = True) -> None:
        """Send a notification to the admin via Telegram."""
        if not self._notify_callback:
            log.debug("no_notify_callback", request_id=request.id)
            return

        try:
            if needs_reply:
                msg = (
                    f"APPROVAL NEEDED [{request.risk_level.upper()}]\n"
                    f"Action: {request.action_type}\n"
                    f"Amount: ${request.amount_usd:,.2f}\n"
                    f"Description: {request.description}\n"
                    f"ID: {request.id}\n"
                    f"Timeout: {request.timeout_seconds / 60:.0f} min\n\n"
                    f"Reply /approve {request.id} or /deny {request.id}"
                )
            else:
                msg = (
                    f"AUTO-APPROVED [{request.risk_level.upper()}]\n"
                    f"Action: {request.action_type}\n"
                    f"Amount: ${request.amount_usd:,.2f}\n"
                    f"Description: {request.description}\n"
                    f"ID: {request.id}"
                )

            result = self._notify_callback(msg)
            # Support both sync and async callbacks
            if asyncio.iscoroutine(result):
                await result

        except Exception as e:
            log.error("notify_error", error=str(e), request_id=request.id)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending approval requests, expiring stale ones."""
        for req in list(self._pending.values()):
            if req.is_expired:
                req.status = ApprovalStatus.AUTO_DENIED.value
                req.responded_at = time.time()
                self._record_history(req)
        self._pending = {k: v for k, v in self._pending.items() if not v.is_expired}
        self._save_pending()
        return list(self._pending.values())

    def get_status(self) -> Dict[str, Any]:
        approved = sum(
            1 for r in self._history
            if r.get("status") in ("approved", "auto_approved")
        )
        denied = sum(
            1 for r in self._history
            if r.get("status") in ("denied", "auto_denied")
        )
        return {
            "auto_approve_limit": self.auto_approve_limit,
            "timeout_seconds": self.timeout_seconds,
            "pending": len(self._pending),
            "total_requests": len(self._history),
            "approved": approved,
            "denied": denied,
            "thresholds": self.thresholds,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _record_history(self, request: ApprovalRequest) -> None:
        """Append a resolved request to the history ledger."""
        entry = {
            "id": request.id,
            "action_type": request.action_type,
            "description": request.description,
            "risk_level": request.risk_level,
            "amount_usd": request.amount_usd,
            "status": request.status,
            "created_at": request.created_at,
            "responded_at": request.responded_at,
            "response_message": request.response_message,
        }
        self._history.append(entry)
        self._save_history()

    def _save_pending(self) -> None:
        PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            k: {
                "id": v.id,
                "action_type": v.action_type,
                "description": v.description,
                "risk_level": v.risk_level,
                "amount_usd": v.amount_usd,
                "created_at": v.created_at,
                "timeout_seconds": v.timeout_seconds,
                "status": v.status,
            }
            for k, v in self._pending.items()
        }
        PENDING_FILE.write_text(json.dumps(data, indent=2))

    def _save_history(self) -> None:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Keep last 500 entries
        trimmed = self._history[-500:]
        HISTORY_FILE.write_text(json.dumps(trimmed, indent=2))

    def _load_pending(self) -> None:
        if PENDING_FILE.exists():
            try:
                data = json.loads(PENDING_FILE.read_text())
                for k, v in data.items():
                    req = ApprovalRequest(**v)
                    if not req.is_expired:
                        self._pending[k] = req
            except (json.JSONDecodeError, TypeError):
                pass

    def _load_history(self) -> None:
        if HISTORY_FILE.exists():
            try:
                self._history = json.loads(HISTORY_FILE.read_text())
            except (json.JSONDecodeError, TypeError):
                self._history = []


# Singleton
_instance: Optional[ApprovalGate] = None


def get_approval_gate() -> ApprovalGate:
    global _instance
    if _instance is None:
        _instance = ApprovalGate()
    return _instance
