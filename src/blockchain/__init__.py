"""
Blockchain Integration
======================

Monad L1 and LFJ Token Mill integration for $MON token.

Usage:
    from src.blockchain import NadFunClient, MonadClient

    # Get token metrics
    nadfun = NadFunClient(token_address="0x...")
    metrics = await nadfun.get_token_metrics()
    print(metrics.market_cap)

    # Get recent trades
    trades = await nadfun.get_recent_trades(limit=10)

    # Direct Monad RPC
    monad = MonadClient()
    balance = await monad.get_balance("0x...")
"""

from .monad import (
    NadFunClient,
    MonadClient,
    TokenMetrics,
    TradeEvent,
    FundingStatus,
    create_nadfun_client,
    create_monad_client,
)

__all__ = [
    "NadFunClient",
    "MonadClient",
    "TokenMetrics",
    "TradeEvent",
    "FundingStatus",
    "create_nadfun_client",
    "create_monad_client",
]
