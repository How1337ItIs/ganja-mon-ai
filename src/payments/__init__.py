"""
Payment & Monetization Layer
============================

Automated profit allocation, human approval gates, signal monetization.
"""

from src.payments.splitter import (
    ProfitSplitter,
    Batch,
    SplitRecord,
    get_profit_splitter,
    DEFAULT_ALLOCATION,
    LEDGER_PATH,
)
from src.payments.approval_gate import (
    ApprovalGate,
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
    get_approval_gate,
)

__all__ = [
    "ProfitSplitter",
    "Batch",
    "SplitRecord",
    "get_profit_splitter",
    "DEFAULT_ALLOCATION",
    "LEDGER_PATH",
    "ApprovalGate",
    "ApprovalRequest",
    "ApprovalStatus",
    "RiskLevel",
    "get_approval_gate",
]
