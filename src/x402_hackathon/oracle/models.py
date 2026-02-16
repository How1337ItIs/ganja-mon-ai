"""
Oracle Response Models — Pydantic schemas for all 4 oracle tiers.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SensorSnapshot(BaseModel):
    temperature_f: Optional[float] = None
    humidity_pct: Optional[float] = None
    vpd_kpa: Optional[float] = None
    co2_ppm: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GrowAlphaResponse(BaseModel):
    skill: str = "grow-alpha"
    signal: str
    narrative_score: float
    thesis: str
    components: Dict[str, Any]
    token: Dict[str, str] = {
        "symbol": "$MON",
        "chain": "monad",
        "contract": "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b",
    }
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payment_usd: float = 0.05


class DailyVibesResponse(BaseModel):
    skill: str = "daily-vibes"
    vibes_score: int = Field(ge=0, le=100)
    mood: str
    breakdown: Dict[str, int]
    wisdom: str
    greeting: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payment_usd: float = 0.02


class OracleSynthesis(BaseModel):
    """Premium tier — full 5-domain AI synthesis."""
    skill: str = "oracle-synthesis"
    narrative: str
    signal: str
    confidence: float = Field(ge=0.0, le=1.0)
    domains: Dict[str, Any] = {}
    wisdom: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payment_usd: float = 0.15


class PaymentRequiredResponse(BaseModel):
    """402 Payment Required response body."""
    error: str = "payment_required"
    version: str = "x402-oracle-v1"
    tier: str
    price_usd: float
    currency: str = "USDC"
    network: str = "base"
    chain_id: int = 8453
    pay_to: str = ""
    description: str = ""
    pricing_url: str = "https://grokandmon.com/.well-known/x402-pricing.json"
