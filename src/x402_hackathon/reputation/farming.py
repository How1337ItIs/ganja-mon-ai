"""
Reputation farming - payments as Sybil-resistant trust signals for ERC-8004.

Tracks x402 micropayment revenue as proof of oracle value.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


STATS_PATH = Path("data/a2a_stats.json")


def get_oracle_stats() -> dict:
    """
    Reads and returns oracle payment stats.

    Returns dict with:
    - total_received_usd: float
    - oracle_consultations: int
    - oracle_tier1_count: int
    - oracle_tier2_count: int
    - oracle_tier3_count: int
    - last_oracle_payment: Optional[str] (ISO timestamp)
    - last_payer: Optional[str]
    """
    if not STATS_PATH.exists():
        return {
            "total_received_usd": 0.0,
            "oracle_consultations": 0,
            "oracle_tier1_count": 0,
            "oracle_tier2_count": 0,
            "oracle_tier3_count": 0,
            "last_oracle_payment": None,
            "last_payer": None,
        }

    try:
        with open(STATS_PATH, "r") as f:
            data = json.load(f)

        # Ensure all expected keys exist
        defaults = {
            "total_received_usd": 0.0,
            "oracle_consultations": 0,
            "oracle_tier1_count": 0,
            "oracle_tier2_count": 0,
            "oracle_tier3_count": 0,
            "last_oracle_payment": None,
            "last_payer": None,
        }
        defaults.update(data)
        return defaults
    except (json.JSONDecodeError, IOError):
        return get_oracle_stats()  # Return defaults on error


def record_oracle_payment(tier_name: str, amount_usd: float, payer: str = "") -> None:
    """
    Records an oracle payment event.

    Args:
        tier_name: Tier identifier (tier1, tier2, tier3)
        amount_usd: Payment amount in USD
        payer: Optional payer identifier (address, agent name, etc.)
    """
    stats = get_oracle_stats()

    # Update totals
    stats["total_received_usd"] += amount_usd
    stats["oracle_consultations"] += 1

    # Update tier-specific counter
    tier_key = f"oracle_{tier_name}_count"
    if tier_key in stats:
        stats[tier_key] += 1
    else:
        # New tier - initialize counter
        stats[tier_key] = 1

    # Update timestamps
    stats["last_oracle_payment"] = datetime.now().isoformat()
    if payer:
        stats["last_payer"] = payer

    # Ensure parent directory exists
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save updated stats
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)


def get_reputation_signals() -> dict:
    """
    Returns reputation signals for ERC-8004 trust scoring.

    Returns dict with:
    - x402_revenue_usd: Total micropayment revenue
    - oracle_consultations: Total number of paid consultations
    - oracle_tiers_active: Number of tiers with >0 consultations
    """
    stats = get_oracle_stats()

    # Count active tiers
    tier_keys = [k for k in stats.keys() if k.startswith("oracle_tier") and k.endswith("_count")]
    active_tiers = sum(1 for k in tier_keys if stats.get(k, 0) > 0)

    return {
        "x402_revenue_usd": stats["total_received_usd"],
        "oracle_consultations": stats["oracle_consultations"],
        "oracle_tiers_active": active_tiers,
    }
