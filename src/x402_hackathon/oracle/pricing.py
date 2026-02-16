"""
Oracle Pricing — Intelligence + Art Studio endpoints.

Each tier has a USD price, cache TTL, and endpoint path.
Prices are in USDC on Base chain.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class OracleTier:
    name: str
    price_usd: float
    cache_ttl_seconds: int
    endpoint: str
    description: str


ORACLE_TIERS: Dict[str, OracleTier] = {
    "premium": OracleTier(
        name="premium",
        price_usd=0.15,
        cache_ttl_seconds=300,
        endpoint="/api/x402/oracle",
        description="Full 5-domain AI synthesis in Rasta patois (Grok AI)",
    ),
    "grow-alpha": OracleTier(
        name="grow-alpha",
        price_usd=0.05,
        cache_ttl_seconds=180,
        endpoint="/api/x402/grow-alpha",
        description="Cross-domain plant health x market signal",
    ),
    "daily-vibes": OracleTier(
        name="daily-vibes",
        price_usd=0.02,
        cache_ttl_seconds=600,
        endpoint="/api/x402/daily-vibes",
        description="Composite vibes score (plant + market + social)",
    ),
    "sensor-snapshot": OracleTier(
        name="sensor-snapshot",
        price_usd=0.005,
        cache_ttl_seconds=30,
        endpoint="/api/x402/sensor-snapshot",
        description="Raw IoT sensor data (temp, humidity, VPD, CO2)",
    ),
}


def get_tier(name: str) -> OracleTier:
    """Get a pricing tier by name. Raises KeyError if not found."""
    return ORACLE_TIERS[name]


ART_TIERS = {
    "commission": {
        "price_usd": 0.25,
        "endpoint": "/api/x402/art/commission",
        "method": "POST",
        "description": "Custom art from your prompt/image — GanjaMon's unique vision",
        "accepts": {"prompt": "str", "image_b64": "str (optional)", "style": "str (optional)"},
    },
    "pfp": {
        "price_usd": 0.10,
        "endpoint": "/api/x402/art/pfp",
        "method": "POST",
        "description": "Unique profile picture for agents — iconic and instantly recognizable",
        "accepts": {"prompt": "str (agent name/description)", "style": "str (optional)"},
    },
    "meme": {
        "price_usd": 0.05,
        "endpoint": "/api/x402/art/meme",
        "method": "POST",
        "description": "Rasta meme from context/trends — actually funny",
        "accepts": {"prompt": "str (topic/context)", "style": "str (optional)"},
    },
    "ganjafy": {
        "price_usd": 0.03,
        "endpoint": "/api/x402/art/ganjafy",
        "method": "POST",
        "description": "Transform any image into Rasta/cannabis style",
        "accepts": {"image_b64": "str (required)", "prompt": "str (optional)"},
    },
    "banner": {
        "price_usd": 0.08,
        "endpoint": "/api/x402/art/banner",
        "method": "POST",
        "description": "DexScreener/social banner — professional with personality",
        "accepts": {"prompt": "str (token/project info)", "style": "str (optional)"},
    },
}


def get_pricing_json() -> dict:
    """Return all tiers as JSON-serializable dict for .well-known."""
    return {
        "version": "x402-oracle-v2",
        "agent": "GanjaMon",
        "agent_id": 4,
        "chain": "base",
        "currency": "USDC",
        "tiers": {
            name: {
                "price_usd": tier.price_usd,
                "endpoint": tier.endpoint,
                "description": tier.description,
                "cache_ttl_seconds": tier.cache_ttl_seconds,
            }
            for name, tier in ORACLE_TIERS.items()
        },
        "art_studio": ART_TIERS,
    }
