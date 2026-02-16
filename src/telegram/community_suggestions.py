"""Two-way trading integration - community can suggest trades.

Lets Telegram community members suggest trading ideas that get
queued for the trading agent to evaluate. Suggestions are stored
in a JSON file that the trading agent reads.
"""

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Suggestion queue paths (Chromebook prod, then WSL dev)
SUGGESTION_PATHS = [
    Path("/home/natha/projects/sol-cannabis/data/community_suggestions.json"),
    Path("/mnt/c/Users/natha/sol-cannabis/data/community_suggestions.json"),
]

MAX_SUGGESTIONS = 100  # Keep at most 100 suggestions


def _get_suggestion_path() -> Path:
    """Get the first existing suggestions file path, or create one."""
    for p in SUGGESTION_PATHS:
        if p.exists():
            return p
    # Default to first path
    path = SUGGESTION_PATHS[0]
    os.makedirs(path.parent, exist_ok=True)
    return path


def _load_suggestions() -> list[dict]:
    """Load the suggestion queue."""
    path = _get_suggestion_path()
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"Failed to load suggestions: {e}")
    return []


def _save_suggestions(suggestions: list[dict]):
    """Save the suggestion queue."""
    path = _get_suggestion_path()
    try:
        os.makedirs(path.parent, exist_ok=True)
        # Trim to max
        trimmed = suggestions[-MAX_SUGGESTIONS:]
        with open(path, "w") as f:
            json.dump(trimmed, f, indent=2)
    except Exception as e:
        logger.debug(f"Failed to save suggestions: {e}")


def add_suggestion(
    user_id: int,
    username: str,
    suggestion: str,
    suggestion_type: str = "general",
    token: str | None = None,
    chain: str | None = None,
) -> dict:
    """Add a community trading suggestion.

    Args:
        user_id: Telegram user ID
        username: Display name
        suggestion: The raw suggestion text
        suggestion_type: "buy", "sell", "research", "general"
        token: Token address/name if specified
        chain: Chain if specified

    Returns:
        The created suggestion dict
    """
    suggestions = _load_suggestions()

    entry = {
        "id": len(suggestions) + 1,
        "user_id": user_id,
        "username": username,
        "suggestion": suggestion[:500],
        "type": suggestion_type,
        "token": token,
        "chain": chain,
        "timestamp": time.time(),
        "status": "pending",  # pending, evaluated, acted_on, dismissed
        "agent_response": None,
    }

    suggestions.append(entry)
    _save_suggestions(suggestions)
    logger.info(f"Community suggestion from {username}: {suggestion[:80]}")
    return entry


def get_pending_suggestions(limit: int = 10) -> list[dict]:
    """Get pending suggestions for the agent to evaluate."""
    suggestions = _load_suggestions()
    pending = [s for s in suggestions if s.get("status") == "pending"]
    return pending[-limit:]


def get_recent_suggestions(limit: int = 5) -> str:
    """Format recent suggestions for display."""
    suggestions = _load_suggestions()
    recent = suggestions[-limit:] if suggestions else []

    if not recent:
        return "No community suggestions yet."

    parts = [f"**Community Suggestions** ({len(suggestions)} total)\n"]
    for s in recent:
        status = s.get("status", "pending")
        icon = {"pending": "⏳", "evaluated": "🔍", "acted_on": "✅", "dismissed": "❌"}.get(status, "?")
        username = s.get("username", "someone")
        text = s.get("suggestion", "")[:80]
        parts.append(f"{icon} **{username}**: {text}")
        if s.get("agent_response"):
            parts.append(f"   Agent: {s['agent_response'][:100]}")

    return "\n".join(parts)


def detect_trade_suggestion(text: str) -> dict | None:
    """Detect if a message contains a trade suggestion.

    Returns parsed suggestion info or None if not a suggestion.
    """
    text_lower = text.lower()

    # Common suggestion patterns
    buy_signals = ["you should buy", "ape into", "look at", "check out",
                   "bullish on", "buy some", "load up on", "accumulate",
                   "degen into", "long ", "snipe "]
    sell_signals = ["you should sell", "dump ", "take profit", "short ",
                    "bearish on", "exit "]
    research_signals = ["research ", "look into", "investigate", "what about",
                        "have you seen", "thoughts on"]

    suggestion_type = None
    for sig in buy_signals:
        if sig in text_lower:
            suggestion_type = "buy"
            break
    if not suggestion_type:
        for sig in sell_signals:
            if sig in text_lower:
                suggestion_type = "sell"
                break
    if not suggestion_type:
        for sig in research_signals:
            if sig in text_lower:
                suggestion_type = "research"
                break

    if not suggestion_type:
        return None

    # Try to extract token name/address
    token = None
    # Check for hex addresses
    import re
    addr_match = re.search(r'0x[a-fA-F0-9]{8,40}', text)
    if addr_match:
        token = addr_match.group(0)
    else:
        # Check for $TOKEN pattern
        ticker_match = re.search(r'\$([A-Za-z]{2,10})', text)
        if ticker_match:
            token = f"${ticker_match.group(1).upper()}"

    # Try to detect chain
    chain = None
    chain_map = {
        "monad": "monad", "base": "base", "eth": "ethereum",
        "sol": "solana", "arb": "arbitrum", "bnb": "bsc",
    }
    for keyword, chain_name in chain_map.items():
        if keyword in text_lower:
            chain = chain_name
            break

    return {
        "type": suggestion_type,
        "token": token,
        "chain": chain,
    }
