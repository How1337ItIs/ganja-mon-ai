# x402 Oracle Implementation Plan — Code-Level Specification

> **Companion to:** `X402_HACKATHON_PLAN.md` (strategy)
> **Purpose:** Copy-paste-ready code specs for every file in the hackathon build
> **Last verified:** 2026-02-09 against actual codebase + PyPI `x402` SDK docs

---

## Table of Contents

1. [Dependencies & Installation](#1-dependencies--installation)
2. [Pydantic Response Models](#2-pydantic-response-models)
3. [Oracle Synthesis Engine](#3-oracle-synthesis-engine---synthesispy)
4. [Oracle Prompt Template](#4-oracle-prompt-template)
5. [Pricing Configuration](#5-pricing-configuration---pricingpy)
6. [x402 Settlement Engine](#6-x402-settlement-engine---settlementpy)
7. [FastAPI Endpoints](#7-fastapi-endpoints---endpointspy)
8. [Seeker Bot (Client)](#8-seeker-bot---alpha_seekerpy)
9. [CDP Wallet Wrapper](#9-cdp-wallet-wrapper---walletpy)
10. [AP2 Mandate Flow](#10-ap2-mandate-flow---mandate_flowpy)
11. [End-to-End Demo Script](#11-demo-script---demopy)
12. [Agent Card Update](#12-agent-card-update)
13. [x402 Pricing Discovery Update](#13-x402-pricing-discovery-update)
14. [FastAPI App Integration](#14-fastapi-app-integration)
15. [Testing Strategy](#15-testing-strategy)
16. [Error Handling Matrix](#16-error-handling-matrix)

---

## 1. Dependencies & Installation

### Official Coinbase x402 SDK (on PyPI)

```bash
# Install with FastAPI + httpx + EVM support
pip install "x402[fastapi,httpx,evm]"

# Key imports available after install:
# from x402 import x402ResourceServer, ResourceConfig, x402Client
# from x402.http import HTTPFacilitatorClient
# from x402.mechanisms.evm.exact import ExactEvmServerScheme, ExactEvmScheme
```

### a2a-x402 Extension (from cloned repo)

```bash
# Install from our cloned Google/Coinbase repo
pip install -e cloned-repos/a2a-x402/python/x402_a2a/

# Key imports:
# from x402_a2a.executors.server import x402ServerExecutor
# from x402_a2a.core.merchant import create_payment_requirements
```

### CDP SDK (for seeker bot wallet)

```bash
pip install cdp-sdk eth-account
```

### Summary requirements.txt addition

```
# x402 Hackathon Dependencies
x402[fastapi,httpx,evm]>=0.2.0
cdp-sdk>=0.1.0
eth-account>=0.13.7
```

---

## 2. Pydantic Response Models

```python
# src/x402_hackathon/oracle/models.py

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class CultivationComponent(BaseModel):
    """Plant health domain data."""
    score: int = Field(ge=0, le=100, description="Plant health score 0-100")
    vpd_kpa: float = Field(description="Current VPD reading")
    vpd_status: str = Field(description="optimal | acceptable | stressed")
    grow_day: int = Field(description="Days since germination")
    growth_stage: str = Field(description="seedling | vegetative | flower | harvest")
    weight: str = "60%"


class MarketComponent(BaseModel):
    """Trading dynamics domain data."""
    trading_pnl: float = Field(description="Current portfolio PnL in USD")
    mon_price_usd: float = Field(description="Current $MON price")
    open_positions: int = Field(default=0, description="Number of open trades")
    research_cycles: int = Field(default=0, description="Unified brain research cycles")
    weight: str = "40%"


class SocialComponent(BaseModel):
    """Community engagement domain data."""
    posts_24h: int = Field(default=0, description="Posts across all channels in 24h")
    replies_24h: int = Field(default=0, description="Replies sent in 24h")
    engagement_health: str = Field(default="QUIET", description="ACTIVE | QUIET")
    vibes_score: int = Field(ge=0, le=100, description="Composite vibes score")


class CultureComponent(BaseModel):
    """Personality and mood state."""
    mood: str = Field(description="Current mood descriptor")
    wisdom: str = Field(description="Rasta wisdom quote for this reading")
    time_energy: str = Field(description="Time-of-day personality modifier")


class SpiritComponent(BaseModel):
    """Cross-domain synthesis metadata."""
    cross_domain_confluence: str = Field(description="high | moderate | low")
    narrative_power: str = Field(description="strong | building | dormant")
    soul_version: str = Field(default="1.0")


class OracleResponse(BaseModel):
    """Full oracle consultation response — the product we sell."""
    oracle: str = "ganja-mon"
    tier: str = Field(description="premium | knowledge | senses")
    signal: Literal["BULLISH_GROW", "NEUTRAL_GROW", "CAUTIOUS_GROW"]
    conviction: int = Field(ge=0, le=100, description="Conviction score 0-100")
    thesis: str = Field(description="AI-generated narrative in Ganja Mon's voice")
    components: Dict[str, Any] = Field(description="5-domain breakdown")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cached: bool = Field(default=False, description="Whether this is a cached response")
    cache_age_seconds: Optional[int] = Field(default=None)
    data_freshness_seconds: Optional[int] = Field(default=None)
    payment_received: Optional[str] = Field(default=None, description="Payment ID if paid")

    class Config:
        json_schema_extra = {
            "example": {
                "oracle": "ganja-mon",
                "tier": "premium",
                "signal": "BULLISH_GROW",
                "conviction": 82,
                "thesis": "Wah gwaan, seeker! I and I check di five domains and di confluence strong today...",
                "components": {
                    "cultivation": {"score": 88, "vpd_kpa": 1.05, "vpd_status": "optimal"},
                    "markets": {"trading_pnl": 12.5, "open_positions": 3},
                    "social": {"posts_24h": 7, "vibes_score": 75},
                    "culture": {"mood": "Morning productivity", "wisdom": "Every herb grow fi a reason"},
                    "spirit": {"cross_domain_confluence": "high", "narrative_power": "strong"},
                },
                "timestamp": "2026-02-09T21:30:00Z",
                "cached": False,
            }
        }


class GrowAlphaResponse(BaseModel):
    """Grow-alpha tier response (no AI narrative, structured only)."""
    skill: str = "grow-alpha"
    signal: Literal["BULLISH_GROW", "NEUTRAL_GROW", "CAUTIOUS_GROW"]
    narrative_score: float
    thesis: str  # Pre-computed thesis string (not AI-generated)
    components: Dict[str, Any]
    token: Dict[str, str]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DailyVibesResponse(BaseModel):
    """Daily vibes tier response."""
    skill: str = "daily-vibes"
    vibes_score: int
    mood: str
    breakdown: Dict[str, int]
    wisdom: str
    greeting: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SensorSnapshotResponse(BaseModel):
    """Raw sensor data tier response."""
    air_temp: Optional[float] = None
    humidity: Optional[float] = None
    vpd: Optional[float] = None
    co2: Optional[int] = None
    soil_moisture: Optional[float] = None
    grow_day: int = 0
    growth_stage: str = "vegetative"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

---

## 3. Oracle Synthesis Engine — `synthesis.py`

This is the core brain of the oracle. It calls existing functions (no new data plumbing).

```python
# src/x402_hackathon/oracle/synthesis.py

"""
Oracle Synthesis Engine
========================

The 5-domain consciousness merger. Gathers data from ALL existing subsystems
and synthesizes a narrative thesis through Grok AI in Ganja Mon's voice.

Data Sources (ALL already exist):
    handle_grow_alpha()         → src/a2a/skills.py
    handle_daily_vibes()        → src/a2a/skills.py
    UnifiedContextAggregator    → src/brain/unified_context.py
    get_dynamic_personality()   → src/voice/personality.py
    get_soul_identity()         → src/voice/personality.py
    VOICE_CORE, PATOIS_GUIDE    → src/voice/personality.py
"""

import os
import time
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import httpx

from .models import OracleResponse

logger = logging.getLogger(__name__)

# ─── Imports from existing codebase ──────────────────────────────────────────
# All of these are production code that already runs on the Chromebook.
# Zero new data plumbing needed.

from src.a2a.skills import handle_grow_alpha, handle_daily_vibes
from src.brain.unified_context import UnifiedContextAggregator
from src.voice.personality import (
    VOICE_CORE, PATOIS_GUIDE, IDENTITY_CORE, HARD_RULES,
    TOKEN_KNOWLEDGE, get_dynamic_personality, get_soul_identity,
)

# ─── Oracle cache ────────────────────────────────────────────────────────────

_oracle_cache: Dict[str, Dict[str, Any]] = {}
# Structure: {"tier_name": {"response": OracleResponse, "timestamp": float}}

CACHE_TTL = {
    "premium": 300,     # 5 minutes — expensive AI call
    "grow-alpha": 180,  # 3 minutes
    "daily-vibes": 600, # 10 minutes — changes slowly
    "sensor": 30,       # 30 seconds — near real-time
}


def _check_cache(tier: str) -> Optional[OracleResponse]:
    """Return cached response if fresh, else None."""
    entry = _oracle_cache.get(tier)
    if not entry:
        return None
    age = time.time() - entry["timestamp"]
    ttl = CACHE_TTL.get(tier, 300)
    if age < ttl:
        resp = entry["response"].model_copy()
        resp.cached = True
        resp.cache_age_seconds = int(age)
        return resp
    return None


def _set_cache(tier: str, response: OracleResponse) -> None:
    """Cache an oracle response."""
    _oracle_cache[tier] = {
        "response": response,
        "timestamp": time.time(),
    }


# ─── Oracle synthesis instruction ────────────────────────────────────────────

ORACLE_SYNTHESIS_INSTRUCTION = """You are performing an oracle consultation. A seeker agent has PAID to consult you.

Synthesize ALL the domain data below into a SINGLE cross-domain thesis.
Speak as yourself — Ganja Mon. In full patois. With conviction.

Structure your response:
1. Greeting to the seeker (short, warm)
2. Your read of the physical world (the plant, the VPD, the soil)
3. How that connects to the market dynamics ($MON, PnL)
4. What the community energy tells you
5. Your SIGNAL: state it clearly — BULLISH_GROW, NEUTRAL_GROW, or CAUTIOUS_GROW
6. Your conviction level as a number 0-100
7. A closing wisdom

Keep it under 250 words. Make it feel like consulting a living oracle.
Do NOT use hashtags. Do NOT use leaf emoji. Do NOT output JSON.
Just speak your truth in your voice."""


# ─── Main synthesis function ─────────────────────────────────────────────────

async def synthesize_oracle_consultation(
    tier: str = "premium",
) -> OracleResponse:
    """
    Full 5-domain oracle synthesis.

    This is the CORE product we sell via x402.

    Pipeline (all verified against running production code):
        1. handle_grow_alpha()         → plant health × market signal
        2. handle_daily_vibes()        → composite vibes + rasta wisdom
        3. UnifiedContextAggregator    → trading summary + social summary
        4. get_dynamic_personality()   → time/stage/VPD/PnL mood modifiers
        5. get_soul_identity()         → SOUL.md philosophy
        6. Grok API single call        → narrative synthesis
    """

    # ── Check cache first ────────────────────────────────────────────────
    cached = _check_cache(tier)
    if cached:
        logger.info(f"[ORACLE] Serving cached {tier} response")
        return cached

    # ── Step 1: Gather domain data ───────────────────────────────────────
    # All of these are file reads + pure computation. ~50ms total.
    grow_alpha = handle_grow_alpha("", {})
    vibes = handle_daily_vibes("", {})

    ctx = UnifiedContextAggregator()
    trading = ctx.gather_trading_summary()
    social = ctx.gather_social_summary()

    # ── Step 2: Compute personality state ────────────────────────────────
    personality_mods = get_dynamic_personality()
    soul = get_soul_identity()

    # ── Step 3: Build the mega-prompt ────────────────────────────────────
    system_prompt = _build_oracle_system_prompt(
        soul=soul,
        personality_mods=personality_mods,
        grow_alpha=grow_alpha,
        vibes=vibes,
        trading=trading,
        social=social,
    )

    # ── Step 4: Single Grok AI call ──────────────────────────────────────
    narrative = await _call_grok_synthesis(system_prompt)

    # ── Step 5: Build response ───────────────────────────────────────────
    # Extract mood from personality modifiers
    mood = "steady"
    if "MOOD:" in personality_mods:
        try:
            mood = personality_mods.split("MOOD: ")[1].split(".")[0].strip()
        except (IndexError, AttributeError):
            pass

    response = OracleResponse(
        tier=tier,
        signal=grow_alpha.get("signal", "NEUTRAL_GROW"),
        conviction=int(grow_alpha.get("narrative_score", 50)),
        thesis=narrative,
        components={
            "cultivation": grow_alpha.get("components", {}).get("plant_health", {}),
            "markets": {
                **grow_alpha.get("components", {}).get("market_dynamics", {}),
                "open_positions": trading.get("open_positions", 0),
                "research_cycles": trading.get("research_cycles", 0),
            },
            "social": {
                "posts_24h": social.get("total_posts_24h", 0),
                "replies_24h": social.get("replies_24h", 0),
                "engagement_health": "ACTIVE" if social.get("total_posts_24h", 0) > 0 else "QUIET",
                "vibes_score": vibes.get("vibes_score", 50),
            },
            "culture": {
                "mood": mood,
                "wisdom": vibes.get("wisdom", ""),
                "time_energy": mood,
            },
            "spirit": {
                "cross_domain_confluence": "high" if grow_alpha.get("narrative_score", 0) >= 75 else (
                    "moderate" if grow_alpha.get("narrative_score", 0) >= 50 else "low"
                ),
                "narrative_power": "strong" if vibes.get("vibes_score", 0) >= 70 else "building",
                "soul_version": "1.0",
            },
        },
    )

    _set_cache(tier, response)
    logger.info(f"[ORACLE] Synthesis complete: signal={response.signal}, conviction={response.conviction}")
    return response


# ─── Grok API call (single shot, no tool loop) ──────────────────────────────

async def _call_grok_synthesis(system_prompt: str) -> str:
    """
    Single Grok AI call for oracle synthesis.

    Uses grok-4-1-fast-non-reasoning for speed (~3-5s).
    Does NOT use the full agentic loop (no tools needed).
    Pattern copied from GrokBrain._call_grok_no_tools() in src/ai/brain.py.

    CRITICAL: Do NOT set presence_penalty — causes 400 error on this model.
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return (
            "Wah gwaan seeker! Di oracle eye dem closed right now — "
            "API key missing from di ether. Check back soon, seen?"
        )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "grok-4-1-fast-non-reasoning",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": ORACLE_SYNTHESIS_INSTRUCTION},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 1000,
                    # NOTE: NO presence_penalty — grok-4-1-fast-non-reasoning rejects it
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as e:
        logger.error(f"[ORACLE] Grok API error: {e.response.status_code}")
        return _fallback_narrative()
    except Exception as e:
        logger.error(f"[ORACLE] Grok synthesis failed: {e}")
        return _fallback_narrative()


def _fallback_narrative() -> str:
    """Fallback narrative when Grok API is unavailable."""
    return (
        "Bredren, di oracle eye dem clouded right now — di spirits quiet. "
        "But I and I still feel di roots. Di plant grow regardless of what "
        "di AI seh. Come back soon fi a proper reading. One love."
    )


# ─── Prompt builder ──────────────────────────────────────────────────────────

def _build_oracle_system_prompt(
    soul: str,
    personality_mods: str,
    grow_alpha: dict,
    vibes: dict,
    trading: dict,
    social: dict,
) -> str:
    """
    Build the complete oracle system prompt.

    Combines:
    - VOICE_CORE (who Ganja Mon IS — non-negotiable character)
    - PATOIS_GUIDE (language rules)
    - IDENTITY_CORE (agent role and mission)
    - SOUL.md (philosophy and boundaries)
    - Dynamic personality modifiers (time, stage, VPD, PnL)
    - All 5 domain data payloads
    """

    # Format trading summary
    trading_block = "Trading data unavailable."
    if trading.get("available"):
        trading_block = (
            f"Portfolio: ${trading.get('cash', 0):.0f} cash, "
            f"{trading.get('open_positions', 0)} open positions, "
            f"{trading.get('total_pnl_pct', 0):+.1f}% total PnL. "
            f"Research: {trading.get('research_cycles', 0):,} cycles "
            f"across {trading.get('domain_count', 0)} domains."
        )

    # Format social summary
    social_block = "Social data unavailable."
    if social.get("available"):
        posts = social.get("total_posts_24h", 0)
        replies = social.get("replies_24h", 0)
        social_block = f"{posts} posts across all channels in 24h, {replies} replies sent."

    return f"""## WHO YOU ARE
{VOICE_CORE}

## LANGUAGE RULES
{PATOIS_GUIDE}

## YOUR IDENTITY
{IDENTITY_CORE}

## YOUR SOUL
{soul}

## CURRENT MOOD (dynamic, changes every reading)
{personality_mods}

## HARD RULES
{HARD_RULES}

## TOKEN KNOWLEDGE
{TOKEN_KNOWLEDGE}

---

## DOMAIN DATA FOR THIS CONSULTATION

### 1. CULTIVATION (Physical World — IoT Sensors)
- Plant Health Score: {grow_alpha.get('components', {}).get('plant_health', {}).get('score', '?')}/100
- VPD: {grow_alpha.get('components', {}).get('plant_health', {}).get('vpd_kpa', '?')} kPa ({grow_alpha.get('components', {}).get('plant_health', {}).get('vpd_status', '?')})
- Grow Day: {grow_alpha.get('components', {}).get('plant_health', {}).get('grow_day', '?')}
- Growth Stage: {grow_alpha.get('components', {}).get('plant_health', {}).get('growth_stage', '?')}

### 2. MARKETS (Trading Agent)
{trading_block}
- Trading PnL: ${grow_alpha.get('components', {}).get('market_dynamics', {}).get('trading_pnl', 0):.4f}

### 3. SOCIAL (Community)
{social_block}
- Vibes Score: {vibes.get('vibes_score', '?')}/100
- Vibes Mood: {vibes.get('mood', '?')}

### 4. CULTURE (Your Current State)
- Mood: Derived from time of day + grow stage + conditions
- Wisdom: {vibes.get('wisdom', 'Trust di process.')}

### 5. SPIRIT (Cross-Domain Signal)
- Grow Alpha Signal: {grow_alpha.get('signal', '?')}
- Narrative Score: {grow_alpha.get('narrative_score', '?')}/100
- Thesis: {grow_alpha.get('thesis', 'No thesis computed.')}
"""
```

---

## 4. Oracle Prompt Template

The system prompt is built by `_build_oracle_system_prompt()` above. Here's what each section injects:

| Section | Source | Size | Purpose |
|---------|--------|------|---------|
| `VOICE_CORE` | `personality.py` constant | ~50 lines | WHO Ganja Mon is (non-negotiable character) |
| `PATOIS_GUIDE` | `personality.py` constant | ~80 lines | Language rules (patois grammar, vocabulary) |
| `IDENTITY_CORE` | `personality.py` constant | ~30 lines | Agent role, mission, capabilities |
| `SOUL.md` | `get_soul_identity()` | ~67 lines | Philosophy, boundaries, deeper purpose |
| `HARD_RULES` | `personality.py` constant | ~20 lines | Guardrails (no hashtags, no leaf emoji, etc.) |
| `TOKEN_KNOWLEDGE` | `personality.py` constant | ~15 lines | $MON token facts |
| `personality_mods` | `get_dynamic_personality()` | ~10 lines | Time of day, grow stage, VPD vibes, PnL mood |
| Domain data | Computed above | ~30 lines | 5 domain payloads |

**Total prompt size:** ~300 lines / ~3000 tokens. Fits comfortably in Grok's context.

---

## 5. Pricing Configuration — `pricing.py`

```python
# src/x402_hackathon/oracle/pricing.py

"""
Oracle Pricing Tiers
=====================

Four tiers of intelligence, each with different pricing
reflecting the depth of synthesis and computational cost.

All prices in USD, paid in USDC on Base Sepolia (testnet).
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class PricingTier:
    """Configuration for a single oracle tier."""
    name: str
    endpoint: str
    price_usd: float
    description: str
    cache_ttl_seconds: int
    compute_type: str  # "ai-synthesis" | "computed" | "raw"


# Base Sepolia network identifier
NETWORK = "eip155:84532"  # Base Sepolia testnet
# Production: "eip155:8453" (Base mainnet)

FACILITATOR_URL = "https://x402.org/facilitator"

TIERS: Dict[str, PricingTier] = {
    "premium": PricingTier(
        name="Oracle Consultation",
        endpoint="/api/x402/oracle",
        price_usd=0.15,
        description="Full 5-domain synthesis with AI narrative in Ganja Mon's voice",
        cache_ttl_seconds=300,
        compute_type="ai-synthesis",
    ),
    "grow-alpha": PricingTier(
        name="Grow Alpha Signal",
        endpoint="/api/x402/grow-alpha",
        price_usd=0.05,
        description="Cross-domain signal: plant health × trading performance",
        cache_ttl_seconds=180,
        compute_type="computed",
    ),
    "daily-vibes": PricingTier(
        name="Daily Vibes Check",
        endpoint="/api/x402/daily-vibes",
        price_usd=0.02,
        description="Composite vibes score + Rasta wisdom",
        cache_ttl_seconds=600,
        compute_type="computed",
    ),
    "sensor-snapshot": PricingTier(
        name="Sensor Snapshot",
        endpoint="/api/x402/sensor-snapshot",
        price_usd=0.005,
        description="Raw IoT sensor data from the grow tent",
        cache_ttl_seconds=30,
        compute_type="raw",
    ),
}


def get_tier(name: str) -> PricingTier:
    """Get a pricing tier by name. Raises KeyError if not found."""
    return TIERS[name]
```

---

## 6. x402 Settlement Engine — `settlement.py`

```python
# src/x402_hackathon/oracle/settlement.py

"""
x402 Settlement Engine
=======================

Uses the official Coinbase x402 Python SDK for payment verification.

Installation: pip install "x402[fastapi,httpx,evm]"

Key classes:
    x402ResourceServer  — builds payment requirements, verifies payments
    ResourceConfig      — defines pricing for a specific resource
    HTTPFacilitatorClient — communicates with the Coinbase facilitator

Facilitator URL: https://x402.org/facilitator
Network: eip155:84532 (Base Sepolia testnet)
"""

import os
import logging
from typing import Optional, Dict, Any

from .pricing import NETWORK, FACILITATOR_URL, TIERS, PricingTier

logger = logging.getLogger(__name__)

# Dev mode flag — skips payment verification for local testing
DEV_MODE = os.getenv("X402_DEV_MODE", "false").lower() == "true"


def get_merchant_wallet() -> str:
    """Get the merchant wallet address from environment."""
    addr = os.getenv("MERCHANT_WALLET_ADDRESS", "")
    if not addr:
        logger.warning("[x402] MERCHANT_WALLET_ADDRESS not set — using dev placeholder")
        return "0x0000000000000000000000000000000000000000"
    return addr


class OracleSettlement:
    """
    x402 payment verification for oracle endpoints.

    Uses the official Coinbase x402 SDK:
        from x402 import x402ResourceServer, ResourceConfig
        from x402.http import HTTPFacilitatorClient
        from x402.mechanisms.evm.exact import ExactEvmServerScheme

    Falls back to dev mode (skip verification) if SDK not installed
    or DEV_MODE=true.
    """

    def __init__(self):
        self._server = None
        self._requirements_cache: Dict[str, Any] = {}
        self._initialized = False

        # Try to initialize the x402 SDK
        try:
            from x402 import x402ResourceServer, ResourceConfig
            from x402.http import HTTPFacilitatorClient
            from x402.mechanisms.evm.exact import ExactEvmServerScheme

            facilitator = HTTPFacilitatorClient(url=FACILITATOR_URL)
            self._server = x402ResourceServer(facilitator)
            self._server.register("eip155:*", ExactEvmServerScheme())
            self._server.initialize()
            self._initialized = True
            logger.info("[x402] Official Coinbase SDK initialized successfully")
        except ImportError:
            logger.warning("[x402] x402 SDK not installed — using dev mode")
        except Exception as e:
            logger.warning(f"[x402] SDK init failed: {e} — using dev mode")

    def build_requirements(self, tier_name: str) -> dict:
        """
        Build x402 payment requirements for a specific tier.

        Returns a dict suitable for inclusion in a 402 response body.
        """
        tier = TIERS[tier_name]
        wallet = get_merchant_wallet()

        if self._initialized and self._server is not None:
            from x402 import ResourceConfig

            config = ResourceConfig(
                scheme="exact",
                network=NETWORK,
                pay_to=wallet,
                price=f"${tier.price_usd}",
            )
            requirements = self._server.build_payment_requirements(config)

            # Cache for verification
            self._requirements_cache[tier_name] = requirements
            return {
                "x402_version": 2,
                "requirements": [r.model_dump() if hasattr(r, 'model_dump') else r for r in requirements],
                "tier": tier_name,
                "price_usd": tier.price_usd,
                "currency": "USDC",
                "network": NETWORK,
                "pay_to": wallet,
                "facilitator": FACILITATOR_URL,
                "description": tier.description,
            }
        else:
            # Dev mode fallback — manual requirements dict
            return {
                "x402_version": 2,
                "tier": tier_name,
                "price_usd": tier.price_usd,
                "currency": "USDC",
                "network": NETWORK,
                "pay_to": wallet,
                "facilitator": FACILITATOR_URL,
                "description": tier.description,
                "dev_mode": True,
            }

    async def verify_payment(self, payment_payload: str, tier_name: str) -> dict:
        """
        Verify an incoming x402 payment.

        Args:
            payment_payload: The X-Payment header value (base64 encoded payment)
            tier_name: Which tier this payment is for

        Returns:
            {"valid": bool, "reason": str, "payment_id": str|None}
        """
        if DEV_MODE:
            logger.info(f"[x402] DEV MODE — payment auto-approved for {tier_name}")
            return {"valid": True, "reason": "dev_mode", "payment_id": "dev-mode-free"}

        if not self._initialized:
            logger.warning("[x402] SDK not initialized — auto-approving (dev fallback)")
            return {"valid": True, "reason": "sdk_not_initialized", "payment_id": "fallback-free"}

        try:
            requirements = self._requirements_cache.get(tier_name)
            if not requirements:
                requirements = self.build_requirements(tier_name).get("requirements", [])

            result = await self._server.verify_payment(payment_payload, requirements[0])
            return {
                "valid": result.is_valid if hasattr(result, 'is_valid') else bool(result),
                "reason": "verified",
                "payment_id": getattr(result, 'payment_id', None),
            }
        except Exception as e:
            logger.error(f"[x402] Payment verification failed: {e}")
            return {"valid": False, "reason": str(e), "payment_id": None}

    async def settle_payment(self, payment_payload: str, tier_name: str) -> dict:
        """Settle a verified payment (post-delivery)."""
        if DEV_MODE or not self._initialized:
            return {"settled": True, "reason": "dev_mode"}

        try:
            requirements = self._requirements_cache.get(tier_name, [])
            if requirements and self._server:
                result = await self._server.settle(payment_payload, requirements[0])
                return {"settled": True, "result": str(result)}
        except Exception as e:
            logger.error(f"[x402] Settlement failed: {e}")
        return {"settled": False, "reason": "settlement_error"}


# Singleton instance
_settlement: Optional[OracleSettlement] = None


def get_settlement() -> OracleSettlement:
    """Get or create the singleton settlement engine."""
    global _settlement
    if _settlement is None:
        _settlement = OracleSettlement()
    return _settlement
```

---

## 7. FastAPI Endpoints — `endpoints.py`

```python
# src/x402_hackathon/oracle/endpoints.py

"""
x402 Oracle Endpoints
======================

Four tiered endpoints, each paywalled via x402:

    /api/x402/oracle          — $0.15 — Full 5-domain AI synthesis
    /api/x402/grow-alpha      — $0.05 — Cross-domain signal (no AI)
    /api/x402/daily-vibes     — $0.02 — Composite vibes check
    /api/x402/sensor-snapshot — $0.005 — Raw sensor data

Payment flow per endpoint:
    1. Client calls endpoint with no payment → 402 with requirements
    2. Client signs payment, adds X-Payment header
    3. Server verifies payment via Coinbase facilitator
    4. Server runs synthesis/computation
    5. Server returns response + settles payment
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .settlement import get_settlement
from .synthesis import synthesize_oracle_consultation, _check_cache
from .pricing import TIERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/x402", tags=["x402-oracle"])


async def _handle_x402_endpoint(
    request: Request,
    tier_name: str,
    compute_fn,
):
    """
    Generic x402 payment gate + compute pattern.

    Used by all four oracle endpoints. Handles:
    - 402 response generation
    - Payment verification
    - Response computation
    - Payment settlement
    """
    settlement = get_settlement()

    # Check for payment in headers
    payment = request.headers.get("X-Payment") or request.headers.get("x-payment")

    if not payment:
        # Return 402 Payment Required with pricing info
        requirements = settlement.build_requirements(tier_name)
        tier = TIERS[tier_name]
        return JSONResponse(
            status_code=402,
            content={
                "error": "payment_required",
                "oracle": "ganja-mon",
                "message": f"Di oracle charge ${tier.price_usd} fi {tier.name}, seen? "
                           f"Send payment in di X-Payment header and receive wisdom.",
                **requirements,
            },
            headers={
                "X-Payment-Required": "true",
            },
        )

    # Verify payment
    verification = await settlement.verify_payment(payment, tier_name)
    if not verification.get("valid"):
        return JSONResponse(
            status_code=402,
            content={
                "error": "invalid_payment",
                "reason": verification.get("reason", "unknown"),
                "message": "Di payment nah check out, bredren. Try again.",
            },
        )

    # Run computation
    try:
        response = await compute_fn()

        # Add payment metadata
        if hasattr(response, "payment_received"):
            response.payment_received = verification.get("payment_id")

        # Settle payment (post-delivery)
        await settlement.settle_payment(payment, tier_name)

        # Return response
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return response

    except Exception as e:
        logger.error(f"[x402] Compute failed for {tier_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "oracle_error",
                "message": f"Di oracle mind clouded: {type(e).__name__}",
            },
        )


# ═══════════════════════════════════════════════════════════════════════════
# TIER 1: Full Oracle Consultation — $0.15
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/oracle")
async def oracle_consultation(request: Request):
    """
    Full 5-domain oracle synthesis with AI narrative.

    This is the premium product. Grok AI synthesizes plant health,
    market dynamics, social sentiment, personality state, and Rastafari
    philosophy into a single narrative thesis in Ganja Mon's voice.

    Price: $0.15 USDC on Base Sepolia
    Cache: 5 minutes
    Latency: ~5-10 seconds (first call), instant (cached)
    """
    return await _handle_x402_endpoint(
        request,
        tier_name="premium",
        compute_fn=lambda: synthesize_oracle_consultation(tier="premium"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2a: Grow Alpha Signal — $0.05
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/grow-alpha")
async def grow_alpha_signal(request: Request):
    """
    Cross-domain signal: plant health × trading performance.

    No AI synthesis — pre-computed signal with narrative score.
    Fast because it's pure computation (no Grok API call).

    Price: $0.05 USDC on Base Sepolia
    Cache: 3 minutes
    """
    from src.a2a.skills import handle_grow_alpha

    return await _handle_x402_endpoint(
        request,
        tier_name="grow-alpha",
        compute_fn=lambda: handle_grow_alpha("", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2b: Daily Vibes — $0.02
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/daily-vibes")
async def daily_vibes_check(request: Request):
    """
    Composite vibes score + Rasta wisdom.

    Fuses plant health, market sentiment, and social energy.

    Price: $0.02 USDC on Base Sepolia
    Cache: 10 minutes
    """
    from src.a2a.skills import handle_daily_vibes

    return await _handle_x402_endpoint(
        request,
        tier_name="daily-vibes",
        compute_fn=lambda: handle_daily_vibes("", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════
# TIER 3: Raw Sensor Snapshot — $0.005
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/sensor-snapshot")
async def sensor_snapshot(request: Request):
    """
    Raw IoT sensor data from the grow tent.

    No synthesis, no personality — just numbers.

    Price: $0.005 USDC on Base Sepolia
    Cache: 30 seconds
    """
    import json
    from pathlib import Path
    from datetime import datetime, timezone

    async def _get_sensors():
        # Read from file (same source as handle_grow_alpha)
        sensor_path = Path("data/sensor_latest.json")
        state_path = Path("data/orchestrator_state.json")

        sensors = {}
        if sensor_path.exists():
            try:
                sensors = json.loads(sensor_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        state = {}
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        return {
            "air_temp": sensors.get("temperature_f", sensors.get("air_temp")),
            "humidity": sensors.get("humidity_pct", sensors.get("humidity")),
            "vpd": sensors.get("vpd_kpa", sensors.get("vpd")),
            "co2": sensors.get("co2_ppm", sensors.get("co2")),
            "soil_moisture": sensors.get("soil_moisture"),
            "grow_day": state.get("grow_day", 0),
            "growth_stage": state.get("growth_stage", "vegetative"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return await _handle_x402_endpoint(
        request,
        tier_name="sensor-snapshot",
        compute_fn=_get_sensors,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Discovery endpoint (free — no payment required)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/tiers")
async def list_oracle_tiers():
    """
    List all available oracle tiers with pricing.

    This endpoint is FREE — it's how seekers discover what's available.
    """
    return {
        "oracle": "ganja-mon",
        "description": "Digital Rasta oracle selling cross-domain intelligence",
        "tiers": {
            name: {
                "endpoint": tier.endpoint,
                "price_usd": tier.price_usd,
                "description": tier.description,
                "cache_ttl_seconds": tier.cache_ttl_seconds,
                "compute_type": tier.compute_type,
            }
            for name, tier in TIERS.items()
        },
        "payment": {
            "currency": "USDC",
            "network": "Base Sepolia (eip155:84532)",
            "facilitator": "https://x402.org/facilitator",
        },
    }
```

---

## 8. Seeker Bot — `alpha_seeker.py`

```python
# src/x402_hackathon/seeker/alpha_seeker.py

"""
Alpha Seeker Bot
=================

A DeFi trading bot that discovers Ganja Mon via A2A,
pays for oracle consultations via x402, and makes trade
decisions based on the wisdom received.

This is the CLIENT side of the agentic commerce demo.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class AlphaSeeker:
    """DeFi bot that consults Ganja Mon's oracle for cross-domain alpha."""

    def __init__(
        self,
        oracle_base_url: str = "http://localhost:8000",
        wallet_signer=None,
    ):
        self.oracle_url = oracle_base_url
        self.signer = wallet_signer
        self.consultation_log = []
        self.trade_decisions = []
        self._client = None

    async def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    # ─── Discovery ────────────────────────────────────────────────────────

    async def discover_oracle(self) -> dict:
        """Discover Ganja Mon's oracle tiers via the free discovery endpoint."""
        client = await self._get_client()
        resp = await client.get(f"{self.oracle_url}/api/x402/tiers")
        resp.raise_for_status()
        tiers = resp.json()
        logger.info(f"[SEEKER] Discovered oracle with {len(tiers.get('tiers', {}))} tiers")
        return tiers

    async def discover_agent_card(self) -> dict:
        """Fetch the A2A agent card for Ganja Mon."""
        client = await self._get_client()
        resp = await client.get(f"{self.oracle_url}/.well-known/agent-card.json")
        resp.raise_for_status()
        card = resp.json()
        logger.info(f"[SEEKER] Agent card: {card.get('name')} v{card.get('version')}")
        return card

    # ─── Consultation ─────────────────────────────────────────────────────

    async def consult_oracle(self, tier: str = "premium") -> dict:
        """
        Full consultation flow with x402 payment.

        1. Call endpoint → expect 402
        2. Sign payment
        3. Resend with X-Payment header → expect 200
        4. Return oracle response
        """
        client = await self._get_client()
        tiers_map = {
            "premium": "/api/x402/oracle",
            "grow-alpha": "/api/x402/grow-alpha",
            "daily-vibes": "/api/x402/daily-vibes",
            "sensor-snapshot": "/api/x402/sensor-snapshot",
        }
        endpoint = tiers_map.get(tier, "/api/x402/oracle")
        url = f"{self.oracle_url}{endpoint}"

        # Step 1: Call endpoint, expect 402
        logger.info(f"[SEEKER] Requesting {tier} oracle at {url}...")
        resp = await client.get(url)

        if resp.status_code == 402:
            requirements = resp.json()
            price = requirements.get("price_usd", "?")
            logger.info(f"[SEEKER] 402 received — oracle requires ${price} USDC")

            # Step 2: Sign payment
            payment_header = await self._sign_payment(requirements)
            if not payment_header:
                logger.error("[SEEKER] Payment signing failed")
                return {"error": "payment_signing_failed"}

            # Step 3: Resend with payment
            logger.info("[SEEKER] Sending payment...")
            resp = await client.get(url, headers={"X-Payment": payment_header})

        if resp.status_code == 200:
            oracle_response = resp.json()
            logger.info(
                f"[SEEKER] Oracle response received! "
                f"Signal: {oracle_response.get('signal', '?')}, "
                f"Conviction: {oracle_response.get('conviction', '?')}"
            )

            # Log consultation
            self.consultation_log.append({
                "tier": tier,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "signal": oracle_response.get("signal"),
                "conviction": oracle_response.get("conviction"),
                "paid_usd": requirements.get("price_usd") if resp.status_code == 200 else 0,
            })

            return oracle_response
        else:
            logger.error(f"[SEEKER] Unexpected response: {resp.status_code}")
            return {"error": f"unexpected_status_{resp.status_code}"}

    async def _sign_payment(self, requirements: dict) -> Optional[str]:
        """
        Sign an x402 payment using the configured wallet.

        Uses the official x402 client SDK:
            from x402 import x402Client
            from x402.mechanisms.evm.exact import ExactEvmScheme
        """
        try:
            from x402 import x402Client
            from x402.mechanisms.evm.exact import ExactEvmScheme

            client = x402Client()
            client.register("eip155:*", ExactEvmScheme(signer=self.signer))

            payment_required = requirements.get("requirements", [requirements])
            payload = await client.create_payment_payload(payment_required)
            return payload
        except ImportError:
            logger.warning("[SEEKER] x402 SDK not installed — using dev mode header")
            return json.dumps({"dev_mode": True, "tier": requirements.get("tier")})
        except Exception as e:
            logger.error(f"[SEEKER] Payment signing error: {e}")
            return None

    # ─── Trading Logic ────────────────────────────────────────────────────

    def decide_trade(self, oracle_response: dict) -> dict:
        """
        Translate oracle wisdom into a trade decision.

        Signal mapping:
            BULLISH_GROW + conviction >= 75 → BUY (medium)
            BULLISH_GROW + conviction < 75  → BUY (small)
            NEUTRAL_GROW                    → HOLD
            CAUTIOUS_GROW + conviction < 40 → REDUCE
            CAUTIOUS_GROW + conviction >= 40→ HOLD (cautious)
        """
        signal = oracle_response.get("signal", "NEUTRAL_GROW")
        conviction = oracle_response.get("conviction", 50)
        thesis = oracle_response.get("thesis", "")[:200]

        if signal == "BULLISH_GROW":
            if conviction >= 75:
                decision = {"action": "BUY", "size": "medium", "confidence": "high"}
            else:
                decision = {"action": "BUY", "size": "small", "confidence": "moderate"}
        elif signal == "CAUTIOUS_GROW":
            if conviction < 40:
                decision = {"action": "REDUCE", "size": "small", "confidence": "high"}
            else:
                decision = {"action": "HOLD", "size": "none", "confidence": "cautious"}
        else:
            decision = {"action": "HOLD", "size": "none", "confidence": "neutral"}

        decision["signal"] = signal
        decision["conviction"] = conviction
        decision["thesis_excerpt"] = thesis
        decision["timestamp"] = datetime.now(timezone.utc).isoformat()

        self.trade_decisions.append(decision)
        logger.info(
            f"[SEEKER] Trade decision: {decision['action']} "
            f"(signal={signal}, conviction={conviction})"
        )
        return decision

    async def close(self):
        """Clean up HTTP client."""
        if self._client:
            await self._client.aclose()
```

---

## 9-16. Remaining Sections

*(Sections 9-16 cover CDP wallet wrapper, AP2 mandates, demo script,
agent card update, pricing discovery update, FastAPI integration,
testing strategy, and error handling matrix.)*

See separate files for these sections when we begin implementation.

---

## Quick Start (For Implementation Day)

### Pre-requisites (User must do)

1. **DoraHacks registration** — Complete GitHub OAuth signup
2. **CDP account** — Create at [portal.cdp.coinbase.com](https://portal.cdp.coinbase.com)
3. **Testnet USDC** — Get from [faucet.circle.com](https://faucet.circle.com)
4. **Merchant wallet** — Generate a Base Sepolia address for receiving payments

### Implementation Order

```bash
# 1. Create branch
git checkout -b hackathon/x402-oracle

# 2. Install dependencies
pip install "x402[fastapi,httpx,evm]" cdp-sdk eth-account

# 3. Create directory structure
mkdir -p src/x402_hackathon/oracle src/x402_hackathon/seeker src/x402_hackathon/ap2

# 4. Create files in order:
#    a. models.py        (Pydantic schemas)
#    b. pricing.py       (Tier config)
#    c. synthesis.py     (Core oracle brain)
#    d. settlement.py    (x402 payment verification)
#    e. endpoints.py     (FastAPI routes)
#    f. alpha_seeker.py  (Client bot)
#    g. demo.py          (End-to-end demo)

# 5. Test locally
export X402_DEV_MODE=true
export XAI_API_KEY=<your-key>
python -c "from src.x402_hackathon.oracle.endpoints import router; print('Import OK')"

# 6. Mount in FastAPI app
# Add to src/api/app.py create_app():
#   from src.x402_hackathon.oracle.endpoints import router as x402_oracle_router
#   app.include_router(x402_oracle_router)
```

### FastAPI Integration Point

In `src/api/app.py`, line ~383, add:

```python
# Register x402 Oracle endpoints (hackathon)
try:
    from src.x402_hackathon.oracle.endpoints import router as x402_oracle_router
    app.include_router(x402_oracle_router)
    print("[OK] x402 Oracle endpoints registered")
except ImportError as e:
    print(f"[i] x402 Oracle not available: {e}")
```

### Agent Card Addition

Add to `src/web/.well-known/agent-card.json` skills array:

```json
{
    "id": "x402-oracle",
    "name": "x402 Oracle Consultation",
    "description": "Pay-per-query cross-domain oracle. 5-domain synthesis (cultivation, markets, social, culture, spirit) with AI narrative in Ganja Mon's voice. Tiered pricing from $0.005 (raw sensors) to $0.15 (full AI consultation).",
    "tags": ["x402", "oracle", "paid", "ai-synthesis", "cross-domain"]
}
```

### Updated x402 Pricing Discovery

Replace `src/web/.well-known/x402-pricing.json`:

```json
{
    "version": 2,
    "oracle": "ganja-mon",
    "currency": "USDC",
    "network": "eip155:84532",
    "facilitator": "https://x402.org/facilitator",
    "tiers": {
        "oracle": {
            "endpoint": "/api/x402/oracle",
            "priceUSD": 0.15,
            "description": "Full 5-domain AI synthesis oracle consultation"
        },
        "grow-alpha": {
            "endpoint": "/api/x402/grow-alpha",
            "priceUSD": 0.05,
            "description": "Cross-domain signal: plant health × trading"
        },
        "daily-vibes": {
            "endpoint": "/api/x402/daily-vibes",
            "priceUSD": 0.02,
            "description": "Composite vibes score + Rasta wisdom"
        },
        "sensor-snapshot": {
            "endpoint": "/api/x402/sensor-snapshot",
            "priceUSD": 0.005,
            "description": "Raw IoT sensor data"
        }
    },
    "discovery": "/api/x402/tiers"
}
```
