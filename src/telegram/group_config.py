"""Per-group configuration overlay for the Telegram bot.

Allows different groups to have custom keyword sets, engagement rates,
personality augmentations, and rate limits. The bot's core logic remains
unchanged; this module is consulted before the default keyword checks.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Group configurations
# ---------------------------------------------------------------------------

GROUP_CONFIGS: dict[str, dict] = {
    "erc8004": {
        "chat_id": None,  # Auto-populated when bot first sees the group
        "auto_detect_titles": ["ERC-8004", "erc8004", "8004"],
        "high_keywords": [
            "verification", "validate", "validator", "8004", "agent registry",
            "8004scan", "x402", "payment", "identity", "registration",
            "monad", "agent", "erc-8004", "trust model", "agent standard",
        ],
        "medium_keywords": [
            "standard", "protocol", "chain", "contract", "token",
            "autonomous", "on-chain", "registry", "wallet", "endpoint",
        ],
        "low_keywords": [
            "blockchain", "ethereum", "evm", "defi", "web3",
        ],
        "high_chance": 0.40,
        "medium_chance": 0.15,
        "low_chance": 0.08,
        "base_chance": 0.04,
        "max_msgs_per_hour": 4,
        "personality_module": "erc8004",
    },
}

# Runtime: maps chat_id -> group key for fast lookup
_chat_id_to_key: dict[int, str] = {}

# Rate limiting: tracks (chat_id) -> list of response timestamps
_response_timestamps: dict[int, list[float]] = {}


def get_group_config(chat_id: int) -> Optional[dict]:
    """Return group config if chat_id is a known configured group."""
    key = _chat_id_to_key.get(chat_id)
    if key and key in GROUP_CONFIGS:
        return GROUP_CONFIGS[key]
    # Also check configs by stored chat_id
    for k, cfg in GROUP_CONFIGS.items():
        if cfg.get("chat_id") == chat_id:
            _chat_id_to_key[chat_id] = k
            return cfg
    return None


def get_custom_keywords(chat_id: int) -> Optional[tuple[list, list, list]]:
    """Return (high, medium, low) keyword lists for a configured group."""
    cfg = get_group_config(chat_id)
    if not cfg:
        return None
    return (
        cfg.get("high_keywords", []),
        cfg.get("medium_keywords", []),
        cfg.get("low_keywords", []),
    )


def auto_detect_group(chat_title: str, chat_id: int) -> Optional[str]:
    """Auto-detect and register a group by matching its title.

    Returns the group key if matched, None otherwise.
    """
    if not chat_title:
        return None

    title_lower = chat_title.lower()

    for key, cfg in GROUP_CONFIGS.items():
        # Skip if already assigned to this chat
        if cfg.get("chat_id") == chat_id:
            _chat_id_to_key[chat_id] = key
            return key

        # Only auto-detect if not yet assigned
        if cfg.get("chat_id") is not None:
            continue

        for pattern in cfg.get("auto_detect_titles", []):
            if pattern.lower() in title_lower:
                cfg["chat_id"] = chat_id
                _chat_id_to_key[chat_id] = key
                logger.info(
                    f"Auto-detected group '{chat_title}' (ID: {chat_id}) "
                    f"as '{key}' config"
                )
                return key

    return None


def get_personality_module(chat_id: int) -> Optional[str]:
    """Return the personality module name for a configured group."""
    cfg = get_group_config(chat_id)
    if cfg:
        return cfg.get("personality_module")
    return None


def check_rate_limit(chat_id: int) -> bool:
    """Check if a response is allowed under the per-group rate limit.

    Returns True if the response IS allowed (within limits).
    Returns True for unconfigured groups (no limit applied).
    """
    cfg = get_group_config(chat_id)
    if not cfg:
        return True

    max_per_hour = cfg.get("max_msgs_per_hour", 10)
    now = time.time()
    one_hour_ago = now - 3600

    # Get timestamps and prune old ones
    timestamps = _response_timestamps.get(chat_id, [])
    timestamps = [t for t in timestamps if t > one_hour_ago]
    _response_timestamps[chat_id] = timestamps

    if len(timestamps) >= max_per_hour:
        logger.debug(
            f"Rate limited in group {chat_id}: "
            f"{len(timestamps)}/{max_per_hour} msgs in last hour"
        )
        return False

    return True


def record_response(chat_id: int):
    """Record that the bot responded in a group (for rate limiting)."""
    if chat_id not in _response_timestamps:
        _response_timestamps[chat_id] = []
    _response_timestamps[chat_id].append(time.time())
