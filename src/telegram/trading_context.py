"""Fetches live trading data from the GanjaMon trading agent.

This module bridges the Telegram bot with the full trading agent brain,
giving it awareness of market activity, positions, signals, and performance.
"""

import os
import json
import httpx
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# GanjaMon agent data paths (both Windows dev and Chromebook production)
AGENT_DATA_PATHS = [
    # Chromebook production
    Path("/home/natha/projects/sol-cannabis/agents/ganjamon/data"),
    # Windows dev (WSL)
    Path("/mnt/c/Users/natha/sol-cannabis/agents/ganjamon/data"),
]

# GanjaMon aggregator API (runs on Chromebook)
AGGREGATOR_BASE = os.environ.get("GANJAMON_AGGREGATOR_URL", "http://localhost:8001")


def _find_data_dir() -> Path | None:
    """Find the agent data directory."""
    for path in AGENT_DATA_PATHS:
        if path.exists():
            return path
    return None


def _load_json_file(filename: str) -> dict | None:
    """Load a JSON file from the agent data directory."""
    data_dir = _find_data_dir()
    if not data_dir:
        return None

    filepath = data_dir / filename
    if not filepath.exists():
        return None

    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {filename}: {e}")
        return None


async def get_paper_portfolio() -> dict:
    """Get current paper trading portfolio."""
    return _load_json_file("paper_portfolio.json") or {}


async def get_performance_report() -> dict:
    """Get latest performance report."""
    return _load_json_file("performance_report.json") or {}


async def get_active_signals() -> list[dict]:
    """Get recent active signals from the aggregator."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{AGGREGATOR_BASE}/signals")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("signals", [])[:10]  # Last 10 signals
    except Exception as e:
        logger.debug(f"Failed to get signals from aggregator: {e}")

    # Fall back to file-based signals
    signals_file = _find_data_dir()
    if signals_file:
        signals = _load_json_file("recent_signals.json")
        if signals:
            return signals[:10]
    return []


async def get_active_positions() -> list[dict]:
    """Get current open positions."""
    portfolio = await get_paper_portfolio()
    return portfolio.get("positions", [])


async def get_recent_trades() -> list[dict]:
    """Get recently closed trades."""
    portfolio = await get_paper_portfolio()
    closed = portfolio.get("closed_positions", [])
    # Return last 5 trades
    return closed[-5:] if closed else []


async def get_market_sentiment() -> dict:
    """Get overall market sentiment from signals."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{AGGREGATOR_BASE}/status")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.debug(f"Failed to get aggregator status: {e}")
    return {}


async def get_upgrade_requests() -> list[dict]:
    """Get pending upgrade requests (agent's self-improvement desires)."""
    requests = _load_json_file("upgrade_requests.json") or []
    # Filter to recent pending requests
    pending = [r for r in requests if r.get("status") == "requested"]
    return pending[:5]


async def build_trading_context() -> str:
    """Build a comprehensive trading context summary for the AI.

    This gives the Telegram bot full awareness of:
    - Current portfolio state
    - Recent performance
    - Active signals
    - Market conditions
    - Agent's self-improvement goals
    """
    parts = []

    # Portfolio status
    portfolio = await get_paper_portfolio()
    if portfolio:
        balance = portfolio.get("balance", 0)
        total_value = portfolio.get("total_value", balance)
        pnl = total_value - portfolio.get("starting_balance", 1000)
        pnl_pct = (pnl / portfolio.get("starting_balance", 1000)) * 100

        parts.append("## Current Portfolio (Paper Trading)")
        parts.append(f"- Balance: ${balance:,.2f}")
        parts.append(f"- Total Value: ${total_value:,.2f}")
        parts.append(f"- P&L: ${pnl:+,.2f} ({pnl_pct:+.1f}%)")

    # Open positions
    positions = await get_active_positions()
    if positions:
        parts.append(f"\n## Open Positions ({len(positions)} active)")
        for pos in positions[:5]:  # Show top 5
            symbol = pos.get("symbol", "?")
            entry = pos.get("entry_price", 0)
            current = pos.get("current_price", entry)
            pnl_pct = ((current - entry) / entry * 100) if entry else 0
            parts.append(f"- {symbol}: {pnl_pct:+.1f}% from ${entry:.6f}")

    # Recent trades
    recent = await get_recent_trades()
    if recent:
        wins = sum(1 for t in recent if t.get("pnl", 0) > 0)
        parts.append(f"\n## Recent Trades ({wins}/{len(recent)} wins)")
        for trade in recent[-3:]:  # Last 3
            symbol = trade.get("symbol", "?")
            pnl = trade.get("pnl", 0)
            pnl_pct = trade.get("pnl_percent", 0)
            result = "✅" if pnl > 0 else "❌"
            parts.append(f"- {result} {symbol}: {pnl_pct:+.1f}%")

    # Performance metrics
    perf = await get_performance_report()
    if perf:
        win_rate = perf.get("win_rate", 0)
        total_trades = perf.get("total_trades", 0)
        parts.append(f"\n## Performance")
        parts.append(f"- Win Rate: {win_rate:.1%}")
        parts.append(f"- Total Trades: {total_trades}")
        if best := perf.get("best_trade"):
            parts.append(f"- Best Trade: {best.get('symbol', '?')} +{best.get('pnl_percent', 0):.0f}%")

    # Active signals
    signals = await get_active_signals()
    if signals:
        parts.append(f"\n## Active Signals ({len(signals)} recent)")
        for sig in signals[:3]:
            source = sig.get("source", "?")
            token = sig.get("token_address", "?")[:8]
            confidence = sig.get("confidence", 0)
            parts.append(f"- {source}: {token}... (conf: {confidence:.0%})")

    # Agent's current focus (from upgrade requests)
    upgrades = await get_upgrade_requests()
    if upgrades:
        parts.append(f"\n## Agent Focus (Self-Improvement)")
        for up in upgrades[:2]:
            parts.append(f"- {up.get('title', '?')}")

    return "\n".join(parts) if parts else "Trading agent offline or no data available."


async def get_rasta_market_take() -> str:
    """Get a Rasta-styled one-liner about current market conditions.

    This is for proactive comments - a quick vibe check on the market.
    """
    portfolio = await get_paper_portfolio()
    perf = await get_performance_report()
    positions = await get_active_positions()

    # Build a vibe based on performance
    if portfolio:
        starting = portfolio.get("starting_balance", 1000)
        total = portfolio.get("total_value", starting)
        pnl_pct = ((total - starting) / starting) * 100

        if pnl_pct > 20:
            return "Di bag be FAT today, bredren! Jah provide di alpha!"
        elif pnl_pct > 5:
            return "Irie gains flowin' in like a steady riddim."
        elif pnl_pct > 0:
            return "Small gains still gains, mon. Patience like growing herb."
        elif pnl_pct > -10:
            return "Market a test I patience today. Stay irie."
        else:
            return "Babylon market tryin' fi shake I out. But I and I hold strong!"

    if positions:
        return f"Watching {len(positions)} positions like hawk over di garden."

    return "Market deh quiet... perfect time fi reason bout di next move."


# Integration with the voice identity from meta_upgrade.py
RASTA_VOICE_PHRASES = [
    "Irie gains, mon!",
    "One love, one $MON",
    "Blessed be the bag holders",
    "Jah provide the alpha",
    "Smoke herb, stack sats, stay irie",
    "The riddim of the market speaks to I",
    "Babylon charts can't hold us down",
]

def get_random_rasta_phrase() -> str:
    """Get a random Rasta phrase for variety."""
    import random
    return random.choice(RASTA_VOICE_PHRASES)
