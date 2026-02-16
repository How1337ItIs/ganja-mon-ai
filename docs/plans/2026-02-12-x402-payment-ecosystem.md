# x402 Payment Ecosystem Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship all 5 x402 payment features (oracle endpoints, seeker bot, reputation farming, AP2 mandates, bidirectional commerce) to production on Chromebook before Feb 15 hackathon deadline.

**Architecture:** Thin wrappers on existing production code. The x402 verifier, payer, profit splitter, oracle data handlers, and reputation publisher are all built. We're adding ~1200 lines of endpoint wiring, a seeker client, and AP2 dataclasses. All new code lives in `src/x402_hackathon/`.

**Tech Stack:** FastAPI, Pydantic, existing `X402Verifier`/`X402Payer` from `src/a2a/x402.py`, `ProfitSplitter` from `src/payments/splitter.py`, multi-provider LLM from `src/a2a/skills.py`.

---

## Task 1: Scaffold the x402_hackathon Package

**Files:**
- Create: `src/x402_hackathon/__init__.py`
- Create: `src/x402_hackathon/oracle/__init__.py`
- Create: `src/x402_hackathon/seeker/__init__.py`
- Create: `src/x402_hackathon/ap2/__init__.py`
- Create: `src/x402_hackathon/reputation/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p src/x402_hackathon/oracle src/x402_hackathon/seeker src/x402_hackathon/ap2 src/x402_hackathon/reputation
```

**Step 2: Create __init__.py files**

```python
# src/x402_hackathon/__init__.py
"""x402 Payment Ecosystem — hackathon build for Moltiverse Feb 2026."""

# src/x402_hackathon/oracle/__init__.py
"""Oracle endpoints — paid intelligence via x402."""

# src/x402_hackathon/seeker/__init__.py
"""Alpha seeker — autonomous agent that buys intelligence."""

# src/x402_hackathon/ap2/__init__.py
"""AP2 Mandate Chain — structured autonomous commerce."""

# src/x402_hackathon/reputation/__init__.py
"""Reputation farming — payments as trust signals."""
```

**Step 3: Commit**

```bash
git add src/x402_hackathon/
git commit -m "feat: scaffold x402_hackathon package structure"
```

---

## Task 2: Oracle Pricing Config

**Files:**
- Create: `src/x402_hackathon/oracle/pricing.py`

**Step 1: Write the pricing config**

```python
"""
Oracle Pricing — 4-tier paid intelligence endpoints.

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


def get_pricing_json() -> dict:
    """Return all tiers as JSON-serializable dict for .well-known."""
    return {
        "version": "x402-oracle-v1",
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
    }
```

**Step 2: Commit**

```bash
git add src/x402_hackathon/oracle/pricing.py
git commit -m "feat: oracle pricing config — 4 tiers ($0.005-$0.15)"
```

---

## Task 3: Oracle Pydantic Response Models

**Files:**
- Create: `src/x402_hackathon/oracle/models.py`

**Step 1: Write the response models**

```python
"""
Oracle Response Models — Pydantic schemas for all 4 oracle tiers.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PlantHealth(BaseModel):
    score: int = Field(ge=0, le=100, description="Plant health 0-100")
    vpd_kpa: float = 0.0
    vpd_status: str = "unknown"
    grow_day: int = 0
    growth_stage: str = "vegetative"


class MarketDynamics(BaseModel):
    trading_pnl: float = 0.0
    mon_price_usd: float = 0.0


class SocialEnergy(BaseModel):
    score: int = Field(ge=0, le=100, default=50)
    posts_24h: int = 0


class SensorSnapshot(BaseModel):
    temperature_f: Optional[float] = None
    humidity_pct: Optional[float] = None
    vpd_kpa: Optional[float] = None
    co2_ppm: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GrowAlphaResponse(BaseModel):
    skill: str = "grow-alpha"
    signal: str  # BULLISH_GROW, NEUTRAL_GROW, CAUTIOUS_GROW
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
    narrative: str  # Rasta patois AI-generated narrative
    signal: str  # BULLISH/NEUTRAL/CAUTIOUS
    confidence: float = Field(ge=0.0, le=1.0)
    domains: Dict[str, Any] = {}  # All 5 domain scores
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
```

**Step 2: Commit**

```bash
git add src/x402_hackathon/oracle/models.py
git commit -m "feat: oracle Pydantic response models for 4 tiers"
```

---

## Task 4: Oracle Synthesis Engine

**Files:**
- Create: `src/x402_hackathon/oracle/synthesis.py`

**Context:** This is the brain of the premium oracle tier. It calls existing handlers (`handle_grow_alpha`, `handle_daily_vibes`, `handle_sensor_stream`) and then runs a Grok AI call to synthesize a narrative in Rasta patois.

**Step 1: Write the synthesis engine**

```python
"""
Oracle Synthesis Engine — 5-domain intelligence synthesis.

Calls existing A2A skill handlers for raw data, then synthesizes
a narrative via Grok AI (xAI -> Gemini -> OpenRouter fallback).

Domains:
    1. Cultivation (IoT sensors, VPD, grow day)
    2. Markets (trading PnL, $MON price)
    3. Social (engagement metrics)
    4. Culture (Rastafari voice/personality)
    5. Spirit (SOUL.md philosophical context)
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Response cache: {tier_name: (timestamp, response_dict)}
_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def _get_cached(tier: str, ttl: int) -> Optional[Dict[str, Any]]:
    """Return cached response if within TTL."""
    entry = _cache.get(tier)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    return None


def _set_cache(tier: str, data: Dict[str, Any]):
    _cache[tier] = (time.time(), data)


def synthesize_sensor_snapshot() -> Dict[str, Any]:
    """Tier 4: Raw sensor data ($0.005)."""
    from src.a2a.skills import _read_json

    cached = _get_cached("sensor-snapshot", 30)
    if cached:
        return cached

    sensors = _read_json("data/sensor_latest.json", {})
    if not sensors:
        sensors = _read_json("data/latest_sensors.json", {})
    if not sensors:
        sensors = _read_json("data/latest_reading.json", {})

    result = {
        "temperature_f": sensors.get("temperature_f", sensors.get("temperature")),
        "humidity_pct": sensors.get("humidity_pct", sensors.get("humidity")),
        "vpd_kpa": sensors.get("vpd_kpa", sensors.get("vpd")),
        "co2_ppm": sensors.get("co2_ppm", sensors.get("co2")),
        "soil_moisture_pct": sensors.get("soil_moisture_pct", sensors.get("soil_moisture")),
        "data_source": "Govee H5075 + Ecowitt GW1100",
    }
    _set_cache("sensor-snapshot", result)
    return result


def synthesize_daily_vibes() -> Dict[str, Any]:
    """Tier 3: Composite vibes score ($0.02)."""
    cached = _get_cached("daily-vibes", 600)
    if cached:
        return cached

    from src.a2a.skills import handle_daily_vibes
    result = handle_daily_vibes("", {})
    _set_cache("daily-vibes", result)
    return result


def synthesize_grow_alpha() -> Dict[str, Any]:
    """Tier 2: Cross-domain plant x market signal ($0.05)."""
    cached = _get_cached("grow-alpha", 180)
    if cached:
        return cached

    from src.a2a.skills import handle_grow_alpha
    result = handle_grow_alpha("", {})
    _set_cache("grow-alpha", result)
    return result


def synthesize_premium_oracle() -> Dict[str, Any]:
    """
    Tier 1: Full 5-domain AI synthesis ($0.15).

    Calls all lower tiers for data, loads SOUL.md and personality,
    then runs a single Grok AI call for narrative generation.
    """
    cached = _get_cached("premium", 300)
    if cached:
        return cached

    # Gather all domain data
    sensor_data = synthesize_sensor_snapshot()
    vibes_data = synthesize_daily_vibes()
    alpha_data = synthesize_grow_alpha()

    # Load soul/personality context
    soul_text = ""
    soul_path = Path("SOUL.md")
    if soul_path.exists():
        try:
            soul_text = soul_path.read_text(encoding="utf-8")[:500]
        except Exception:
            pass

    personality_context = ""
    try:
        from src.voice.personality import get_dynamic_personality
        personality_context = get_dynamic_personality()[:300]
    except Exception:
        personality_context = "Jamaican Rasta AI cultivator, jovial, wise, one love vibes"

    # Build synthesis prompt
    prompt = f"""You are GanjaMon, a Rasta AI oracle who sells wisdom at the intersection of agriculture and DeFi.

SOUL CONTEXT:
{soul_text[:300]}

PERSONALITY:
{personality_context}

LIVE DATA:
- Sensors: temp={sensor_data.get('temperature_f')}F, humidity={sensor_data.get('humidity_pct')}%, VPD={sensor_data.get('vpd_kpa')} kPa
- Vibes Score: {vibes_data.get('vibes_score', 50)}/100 ({vibes_data.get('mood', 'unknown')})
- Alpha Signal: {alpha_data.get('signal', 'NEUTRAL')} (score={alpha_data.get('narrative_score', 50)})
- Plant Health: {alpha_data.get('components', {}).get('plant_health', {}).get('score', 50)}/100
- Market PnL: {alpha_data.get('components', {}).get('market_dynamics', {}).get('trading_pnl', 0)}

Synthesize a 3-5 sentence oracle consultation in authentic Rasta patois. Include:
1. A greeting (use "I and I")
2. Plant status insight grounded in the sensor data
3. A cross-domain signal (how plant health relates to market vibes)
4. A wisdom closing

Keep it genuine, grounded in REAL data, and entertaining. No hashtags."""

    # Call Grok (or fallback LLM)
    from src.a2a.skills import _llm_complete
    narrative = _llm_complete(prompt, max_tokens=400, temperature=0.8)

    if not narrative:
        narrative = (
            f"Blessed day from di oracle! I and I see VPD at {sensor_data.get('vpd_kpa', '?')} kPa, "
            f"vibes running {vibes_data.get('vibes_score', 50)}/100. "
            f"Signal say {alpha_data.get('signal', 'NEUTRAL')}. Trust di process, mon."
        )

    confidence = min(1.0, (alpha_data.get("narrative_score", 50) / 100))

    result = {
        "narrative": narrative,
        "signal": alpha_data.get("signal", "NEUTRAL_GROW"),
        "confidence": round(confidence, 3),
        "domains": {
            "cultivation": sensor_data,
            "markets": alpha_data.get("components", {}).get("market_dynamics", {}),
            "social": {"vibes_score": vibes_data.get("vibes_score"), "mood": vibes_data.get("mood")},
            "culture": "rasta-patois-synthesis",
            "spirit": "SOUL.md grounded",
        },
        "wisdom": vibes_data.get("wisdom", "Every herb grow fi a reason."),
    }
    _set_cache("premium", result)
    return result
```

**Step 2: Commit**

```bash
git add src/x402_hackathon/oracle/synthesis.py
git commit -m "feat: oracle synthesis engine — 5-domain intelligence + Grok AI narrative"
```

---

## Task 5: Oracle FastAPI Endpoints

**Files:**
- Create: `src/x402_hackathon/oracle/endpoints.py`
- Modify: `src/api/app.py:548` (add router include after ops_router)

**Context:** 4 paid endpoints using existing `X402Verifier` for payment verification and `ProfitSplitter` for revenue recording. The `PAYMENT-SIGNATURE` header carries the payment proof.

**Step 1: Write the oracle endpoints**

```python
"""
Oracle Endpoints — 4 paid intelligence tiers via x402.

Flow per request:
    1. Check PAYMENT-SIGNATURE header
    2. Missing -> 402 with Accept-Payment pricing
    3. Present -> X402Verifier.verify_header()
    4. Invalid -> 402 with reason
    5. Valid -> run synthesis
    6. Record payment in profit splitter + a2a_stats
    7. Return oracle response
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .pricing import ORACLE_TIERS, get_pricing_json
from .synthesis import (
    synthesize_premium_oracle,
    synthesize_grow_alpha,
    synthesize_daily_vibes,
    synthesize_sensor_snapshot,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["x402-oracle"])

# Payment header name (our convention)
PAYMENT_HEADER = "PAYMENT-SIGNATURE"
# Dev mode bypasses payment verification
DEV_MODE = os.getenv("X402_DEV_MODE", "false").lower() == "true"


def _get_verifier_for_tier(tier_name: str):
    """Create a verifier configured for the tier's price."""
    from src.a2a.x402 import X402Verifier
    tier = ORACLE_TIERS[tier_name]
    return X402Verifier(
        price_usd=tier.price_usd,
        currency="USDC",
        chain=os.getenv("A2A_PAYMENT_CHAIN", "base"),
        pay_to=os.getenv("BASE_WALLET_ADDRESS", os.getenv("MONAD_WALLET_ADDRESS", "")),
        require_payment=not DEV_MODE,
    )


def _build_402_response(tier_name: str) -> JSONResponse:
    """Build a 402 Payment Required response for a tier."""
    tier = ORACLE_TIERS[tier_name]
    verifier = _get_verifier_for_tier(tier_name)
    requirements = verifier.get_requirements()
    requirements["tier"] = tier_name
    requirements["priceUSD"] = str(tier.price_usd)
    requirements["description"] = tier.description
    requirements["pricingUrl"] = "https://grokandmon.com/.well-known/x402-pricing.json"
    return JSONResponse(
        status_code=402,
        content={
            "error": "payment_required",
            **requirements,
        },
        headers={
            "Accept-Payment": json.dumps(requirements),
        },
    )


def _record_payment(tier_name: str, amount_usd: float):
    """Record payment in profit splitter and a2a_stats."""
    # Profit split (60/25/10/5)
    try:
        from src.payments.splitter import get_profit_splitter
        splitter = get_profit_splitter()
        batch = splitter.create_batch(amount=amount_usd, source=f"x402-oracle-{tier_name}")
        splitter.execute_batch(batch)
        logger.info(f"Profit split recorded: ${amount_usd} from oracle/{tier_name}")
    except Exception as e:
        logger.warning(f"Profit split failed: {e}")

    # Update a2a_stats.json for reputation publisher
    try:
        stats_path = Path("data/a2a_stats.json")
        stats = {}
        if stats_path.exists():
            stats = json.loads(stats_path.read_text())
        stats["total_received_usd"] = stats.get("total_received_usd", 0) + amount_usd
        stats["oracle_consultations"] = stats.get("oracle_consultations", 0) + 1
        stats[f"oracle_{tier_name}_count"] = stats.get(f"oracle_{tier_name}_count", 0) + 1
        stats["last_oracle_payment"] = datetime.now(timezone.utc).isoformat()
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(json.dumps(stats, indent=2))
    except Exception as e:
        logger.warning(f"Stats update failed: {e}")


def _verify_and_serve(request: Request, tier_name: str, synthesize_fn):
    """Common flow: verify payment -> synthesize -> record -> respond."""
    payment = request.headers.get(PAYMENT_HEADER)

    if DEV_MODE and not payment:
        # Dev mode: serve without payment
        data = synthesize_fn()
        data["_dev_mode"] = True
        return JSONResponse(content=data)

    if not payment:
        return _build_402_response(tier_name)

    # Verify payment
    verifier = _get_verifier_for_tier(tier_name)
    valid, reason = verifier.verify_header(payment)

    if not valid:
        return JSONResponse(
            status_code=402,
            content={
                "error": "invalid_payment",
                "reason": reason,
                "tier": tier_name,
            },
        )

    # Payment verified — synthesize response
    tier = ORACLE_TIERS[tier_name]
    data = synthesize_fn()
    data["payment_verified"] = True
    data["payment_usd"] = tier.price_usd
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Record payment for profit splitting + reputation
    _record_payment(tier_name, tier.price_usd)

    return JSONResponse(content=data)


# --- Endpoints ---

@router.get("/api/x402/oracle")
async def premium_oracle(request: Request):
    """Premium tier ($0.15) — full 5-domain AI synthesis in Rasta patois."""
    return _verify_and_serve(request, "premium", synthesize_premium_oracle)


@router.get("/api/x402/grow-alpha")
async def grow_alpha(request: Request):
    """Grow Alpha tier ($0.05) — cross-domain plant x market signal."""
    return _verify_and_serve(request, "grow-alpha", synthesize_grow_alpha)


@router.get("/api/x402/daily-vibes")
async def daily_vibes(request: Request):
    """Daily Vibes tier ($0.02) — composite vibes score."""
    return _verify_and_serve(request, "daily-vibes", synthesize_daily_vibes)


@router.get("/api/x402/sensor-snapshot")
async def sensor_snapshot(request: Request):
    """Sensor Snapshot tier ($0.005) — raw IoT data."""
    return _verify_and_serve(request, "sensor-snapshot", synthesize_sensor_snapshot)


@router.get("/api/x402/pricing")
async def oracle_pricing():
    """Return all oracle pricing tiers (public, no payment required)."""
    return JSONResponse(content=get_pricing_json())
```

**Step 2: Mount the router in the main API**

In `src/api/app.py`, after line 548 (`app.include_router(ops_router)`), add:

```python
    # Register x402 Oracle paid endpoints
    try:
        from src.x402_hackathon.oracle.endpoints import router as x402_oracle_router
        app.include_router(x402_oracle_router)
    except ImportError:
        pass  # x402_hackathon not deployed yet
```

**Step 3: Commit**

```bash
git add src/x402_hackathon/oracle/endpoints.py src/api/app.py
git commit -m "feat: 4 paid oracle endpoints with x402 verification + profit splitting"
```

---

## Task 6: Reputation Farming Module

**Files:**
- Create: `src/x402_hackathon/reputation/farming.py`
- Modify: `src/blockchain/reputation_publisher.py` (add oracle_consultations signal)

**Context:** Wire payments into ERC-8004 reputation signals. The `_record_payment` function in endpoints.py already updates `data/a2a_stats.json`. The reputation publisher already reads from that file. We add `oracle_consultations` as a new signal type.

**Step 1: Write the farming module**

```python
"""
Reputation Farming — payments as Sybil-resistant trust signals.

Every verified oracle payment automatically:
1. Updates a2a_stats.json (done by endpoints.py)
2. Gets picked up by reputation_publisher.py (existing cron)
3. Published as proofOfPayment to ERC-8004 ReputationRegistry

This module provides helpers and the stats tracking.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

STATS_PATH = Path("data/a2a_stats.json")


def get_oracle_stats() -> Dict[str, Any]:
    """Get current oracle payment stats."""
    if not STATS_PATH.exists():
        return {
            "total_received_usd": 0.0,
            "oracle_consultations": 0,
            "oracle_premium_count": 0,
            "oracle_grow-alpha_count": 0,
            "oracle_daily-vibes_count": 0,
            "oracle_sensor-snapshot_count": 0,
        }
    try:
        return json.loads(STATS_PATH.read_text())
    except Exception:
        return {}


def record_oracle_payment(tier_name: str, amount_usd: float, payer: str = ""):
    """
    Record an oracle payment for reputation farming.

    Called by oracle endpoints after successful payment verification.
    Updates a2a_stats.json which the reputation publisher reads on its
    4-hour cron cycle to publish proofOfPayment signals on-chain.
    """
    stats = get_oracle_stats()
    stats["total_received_usd"] = stats.get("total_received_usd", 0) + amount_usd
    stats["oracle_consultations"] = stats.get("oracle_consultations", 0) + 1
    stats[f"oracle_{tier_name}_count"] = stats.get(f"oracle_{tier_name}_count", 0) + 1
    stats["last_oracle_payment"] = datetime.now(timezone.utc).isoformat()
    if payer:
        stats["last_payer"] = payer

    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATS_PATH.write_text(json.dumps(stats, indent=2))
    logger.info(f"Reputation farming: recorded ${amount_usd} from {tier_name}")


def get_reputation_signals() -> Dict[str, Any]:
    """
    Return reputation-ready signals for the publisher.

    These get included in the next reputation_publisher cycle
    as part of the 10-signal batch published to Monad.
    """
    stats = get_oracle_stats()
    return {
        "x402_revenue_usd": stats.get("total_received_usd", 0),
        "oracle_consultations": stats.get("oracle_consultations", 0),
        "oracle_tiers_active": sum(
            1 for k in ["premium", "grow-alpha", "daily-vibes", "sensor-snapshot"]
            if stats.get(f"oracle_{k}_count", 0) > 0
        ),
    }
```

**Step 2: Add oracle_consultations signal to reputation publisher**

In `src/blockchain/reputation_publisher.py`, find the signal list (the `publish_cycle` or `build_signals` function) and add a new signal for oracle consultations. Read the file to find the exact location, then add:

```python
# In the signal-building section, add after x402_revenue signal:
oracle_stats_path = DATA_DIR / "a2a_stats.json"
oracle_consultations = 0
if oracle_stats_path.exists():
    try:
        odata = json.loads(oracle_stats_path.read_text())
        oracle_consultations = int(odata.get("oracle_consultations", 0))
    except Exception:
        pass
signals.append(("oracle_consultations", oracle_consultations, 0, "service", "oracle"))
```

**Step 3: Commit**

```bash
git add src/x402_hackathon/reputation/farming.py src/blockchain/reputation_publisher.py
git commit -m "feat: reputation farming — oracle payments as trust signals on ERC-8004"
```

---

## Task 7: AP2 Mandate Chain

**Files:**
- Create: `src/x402_hackathon/ap2/mandates.py`

**Context:** AP2 (Agent Payment Protocol v2) structures autonomous commerce into 4 phases. We implement this as Pydantic dataclasses + a flow executor that wraps our existing X402Payer. Reference: `cloned-repos/AP2/samples/python/`.

**Step 1: Write the mandate chain**

```python
"""
AP2 Mandate Chain — structured autonomous commerce.

4-phase flow:
    IntentMandate  -> "I want $MON trading alpha, budget $1/day"
    CartMandate    -> "Oracle endpoint selected, $0.15 USDC"
    PaymentMandate -> "USDC payment signed via EIP-3009"
    PaymentReceipt -> "Oracle wisdom delivered, trade logged"

Each mandate is a Pydantic model logged to data/ap2_mandates.json
for audit and demo purposes.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MANDATES_PATH = Path("data/ap2_mandates.json")


class MandatePhase(str, Enum):
    INTENT = "intent"
    CART = "cart"
    PAYMENT = "payment"
    RECEIPT = "receipt"


class IntentMandate(BaseModel):
    """Phase 1: What the seeker wants."""
    id: str = Field(default_factory=lambda: f"intent_{uuid.uuid4().hex[:8]}")
    phase: MandatePhase = MandatePhase.INTENT
    seeker: str  # Agent name or address
    goal: str  # "I want $MON trading alpha"
    budget_usd: float  # Max spend for this session
    preferences: Dict[str, Any] = {}  # e.g. {"tier": "premium", "chain": "base"}
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CartMandate(BaseModel):
    """Phase 2: Selected service + pricing."""
    id: str = Field(default_factory=lambda: f"cart_{uuid.uuid4().hex[:8]}")
    phase: MandatePhase = MandatePhase.CART
    intent_id: str  # Links to IntentMandate
    oracle_url: str  # Full endpoint URL
    tier: str  # "premium", "grow-alpha", etc.
    price_usd: float
    currency: str = "USDC"
    chain: str = "base"
    pay_to: str = ""  # Merchant wallet address
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PaymentMandate(BaseModel):
    """Phase 3: Signed payment authorization."""
    id: str = Field(default_factory=lambda: f"pay_{uuid.uuid4().hex[:8]}")
    phase: MandatePhase = MandatePhase.PAYMENT
    cart_id: str  # Links to CartMandate
    payment_header: str = ""  # Base64-encoded x402 payment proof
    signed_at: str = ""
    tx_hash: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PaymentReceipt(BaseModel):
    """Phase 4: Service delivered + proof."""
    id: str = Field(default_factory=lambda: f"rcpt_{uuid.uuid4().hex[:8]}")
    phase: MandatePhase = MandatePhase.RECEIPT
    payment_id: str  # Links to PaymentMandate
    service_delivered: bool = False
    response_data: Dict[str, Any] = {}  # Oracle response
    trade_decision: Optional[str] = None  # What the seeker did with the data
    satisfaction: Optional[float] = None  # 0-1 rating
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MandateChain(BaseModel):
    """Full chain of mandates for one commerce session."""
    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    intent: Optional[IntentMandate] = None
    cart: Optional[CartMandate] = None
    payment: Optional[PaymentMandate] = None
    receipt: Optional[PaymentReceipt] = None
    status: str = "in_progress"  # in_progress, completed, failed
    total_spent_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MandateExecutor:
    """
    Execute an AP2 mandate chain using our x402 payer.

    Usage:
        executor = MandateExecutor()
        chain = await executor.execute_full_chain(
            seeker="AlphaBot",
            goal="Get $MON trading alpha",
            oracle_url="https://grokandmon.com/api/x402/oracle",
            tier="premium",
            budget_usd=1.0,
        )
    """

    def __init__(self):
        self._chains: List[MandateChain] = []
        self._load_history()

    def create_intent(self, seeker: str, goal: str, budget_usd: float, **kwargs) -> IntentMandate:
        """Phase 1: Declare intent."""
        return IntentMandate(seeker=seeker, goal=goal, budget_usd=budget_usd, preferences=kwargs)

    def create_cart(self, intent: IntentMandate, oracle_url: str, tier: str,
                    price_usd: float, pay_to: str = "") -> CartMandate:
        """Phase 2: Select service."""
        return CartMandate(
            intent_id=intent.id, oracle_url=oracle_url,
            tier=tier, price_usd=price_usd, pay_to=pay_to,
        )

    async def create_payment(self, cart: CartMandate) -> Optional[PaymentMandate]:
        """Phase 3: Sign payment using x402 payer."""
        from src.a2a.x402 import get_x402_payer
        payer = get_x402_payer()
        if not payer:
            logger.warning("AP2: No x402 payer available")
            return None

        # Build a mock 402 header for the payer to process
        import base64
        payment_required = base64.b64encode(json.dumps({
            "x402Version": 2,
            "accepts": [{
                "network": "eip155:8453",
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "amount": int(cart.price_usd * 1_000_000),
                "payTo": cart.pay_to,
                "maxTimeoutSeconds": 300,
                "extra": {"name": "USD Coin", "version": "2"},
            }],
            "resource": {"url": cart.oracle_url},
        }).encode()).decode()

        payment_header = await payer.pay_402(payment_required)
        if not payment_header:
            logger.warning("AP2: Payment signing failed")
            return None

        return PaymentMandate(
            cart_id=cart.id,
            payment_header=payment_header,
            signed_at=datetime.now(timezone.utc).isoformat(),
        )

    def create_receipt(self, payment: PaymentMandate, response_data: Dict[str, Any],
                       trade_decision: str = "", satisfaction: float = 1.0) -> PaymentReceipt:
        """Phase 4: Record delivery."""
        return PaymentReceipt(
            payment_id=payment.id,
            service_delivered=bool(response_data),
            response_data=response_data,
            trade_decision=trade_decision,
            satisfaction=satisfaction,
        )

    async def execute_full_chain(
        self, seeker: str, goal: str, oracle_url: str,
        tier: str, price_usd: float, budget_usd: float = 1.0,
        pay_to: str = "",
    ) -> MandateChain:
        """Execute all 4 phases of the AP2 mandate chain."""
        chain = MandateChain()

        # Phase 1: Intent
        chain.intent = self.create_intent(seeker, goal, budget_usd, tier=tier)
        logger.info(f"AP2 Intent: {seeker} wants '{goal}' (budget ${budget_usd})")

        # Phase 2: Cart
        chain.cart = self.create_cart(chain.intent, oracle_url, tier, price_usd, pay_to)
        logger.info(f"AP2 Cart: {tier} @ ${price_usd} from {oracle_url}")

        # Phase 3: Payment
        chain.payment = await self.create_payment(chain.cart)
        if not chain.payment:
            chain.status = "failed"
            self._save_chain(chain)
            return chain

        logger.info(f"AP2 Payment: signed ${price_usd} authorization")

        # Phase 4: Call oracle with payment
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    oracle_url,
                    headers={
                        "PAYMENT-SIGNATURE": chain.payment.payment_header,
                    },
                )
                if resp.status_code == 200:
                    response_data = resp.json()
                    chain.receipt = self.create_receipt(
                        chain.payment, response_data,
                        trade_decision="logged_for_analysis",
                        satisfaction=1.0,
                    )
                    chain.status = "completed"
                    chain.total_spent_usd = price_usd
                    logger.info(f"AP2 Receipt: oracle delivered, chain complete")
                else:
                    chain.receipt = self.create_receipt(
                        chain.payment, {"error": resp.text, "status": resp.status_code},
                        satisfaction=0.0,
                    )
                    chain.status = "failed"
                    logger.warning(f"AP2: Oracle returned {resp.status_code}")
        except Exception as e:
            chain.status = "failed"
            logger.error(f"AP2: Oracle call failed: {e}")

        self._save_chain(chain)
        return chain

    def get_history(self) -> List[Dict[str, Any]]:
        """Return all mandate chains."""
        return [c.model_dump() for c in self._chains]

    def _save_chain(self, chain: MandateChain):
        self._chains.append(chain)
        MANDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANDATES_PATH.write_text(json.dumps(
            [c.model_dump() for c in self._chains[-100:]],
            indent=2, default=str,
        ))

    def _load_history(self):
        if MANDATES_PATH.exists():
            try:
                data = json.loads(MANDATES_PATH.read_text())
                self._chains = [MandateChain(**c) for c in data]
            except Exception:
                self._chains = []
```

**Step 2: Commit**

```bash
git add src/x402_hackathon/ap2/mandates.py
git commit -m "feat: AP2 mandate chain — Intent->Cart->Payment->Receipt flow"
```

---

## Task 8: Alpha Seeker Bot

**Files:**
- Create: `src/x402_hackathon/seeker/alpha_seeker.py`

**Context:** Standalone client that discovers oracle, pays for intelligence, consumes it, and decides a trade action. Uses existing `X402Payer` and AP2 mandates.

**Step 1: Write the seeker bot**

```python
"""
Alpha Seeker — autonomous agent that buys intelligence.

Demonstrates the CLIENT side of x402 commerce:
1. Discover oracle (via hardcoded URL or 8004scan API)
2. Call oracle endpoint -> receive 402 with pricing
3. Parse Accept-Payment requirements
4. Sign USDC payment via X402Payer (EIP-3009)
5. Resend request with PAYMENT-SIGNATURE header
6. Receive oracle wisdom
7. Log consultation + decide trade action
8. Report outcome to reputation

Can be run standalone:
    python -m src.x402_hackathon.seeker.alpha_seeker
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Default oracle endpoint
DEFAULT_ORACLE_URL = "https://grokandmon.com/api/x402/oracle"
CONSULTATION_LOG = Path("data/seeker_consultations.json")


class AlphaSeeker:
    """
    Autonomous seeker that buys intelligence from x402-compatible oracles.
    """

    def __init__(
        self,
        oracle_url: str = DEFAULT_ORACLE_URL,
        budget_usd: float = 1.0,
        use_ap2: bool = True,
    ):
        self.oracle_url = oracle_url
        self.budget_usd = budget_usd
        self.use_ap2 = use_ap2
        self._total_spent = 0.0
        self._consultations: List[Dict[str, Any]] = []

    async def discover_oracle(self, url: str = "") -> Dict[str, Any]:
        """
        Discover oracle pricing by calling the endpoint without payment.
        Returns the 402 response with pricing requirements.
        """
        target = url or self.oracle_url
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(target)

            if resp.status_code == 402:
                data = resp.json()
                logger.info(f"Discovered oracle: ${data.get('priceUSD', '?')} {data.get('currency', 'USDC')}")
                return {
                    "url": target,
                    "status": 402,
                    "pricing": data,
                    "accept_payment": resp.headers.get("Accept-Payment", ""),
                }
            elif resp.status_code == 200:
                # Dev mode or free endpoint
                return {"url": target, "status": 200, "data": resp.json()}
            else:
                return {"url": target, "status": resp.status_code, "error": resp.text}

    async def buy_consultation(self, tier_url: str = "") -> Optional[Dict[str, Any]]:
        """
        Full purchase flow: discover -> pay -> consume.

        Returns the oracle response if successful.
        """
        target = tier_url or self.oracle_url

        if self.use_ap2:
            return await self._buy_via_ap2(target)
        return await self._buy_direct(target)

    async def _buy_direct(self, target: str) -> Optional[Dict[str, Any]]:
        """Direct x402 purchase without AP2 mandate chain."""
        # Step 1: Discover pricing
        discovery = await self.discover_oracle(target)
        if discovery["status"] == 200:
            # Free — just return data
            return discovery.get("data")

        if discovery["status"] != 402:
            logger.warning(f"Unexpected status {discovery['status']} from {target}")
            return None

        # Step 2: Sign payment
        from src.a2a.x402 import get_x402_payer
        payer = get_x402_payer()
        if not payer:
            logger.warning("No x402 payer available — cannot buy")
            return None

        accept_payment = discovery.get("accept_payment", "")
        if not accept_payment:
            # Build from response body
            import base64
            pricing = discovery["pricing"]
            accept_payment = base64.b64encode(json.dumps({
                "x402Version": 2,
                "accepts": [{
                    "network": f"eip155:{pricing.get('chainId', 8453)}",
                    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                    "amount": int(float(pricing.get("priceUSD", 0)) * 1_000_000),
                    "payTo": pricing.get("payTo", ""),
                    "maxTimeoutSeconds": 300,
                    "extra": {"name": "USD Coin", "version": "2"},
                }],
                "resource": {"url": target},
            }).encode()).decode()

        payment_header = await payer.pay_402(accept_payment)
        if not payment_header:
            logger.warning("Payment signing failed")
            return None

        price_usd = float(discovery["pricing"].get("priceUSD", 0))

        # Budget check
        if self._total_spent + price_usd > self.budget_usd:
            logger.warning(f"Budget exceeded: spent ${self._total_spent}, budget ${self.budget_usd}")
            return None

        # Step 3: Resend with payment
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                target,
                headers={"PAYMENT-SIGNATURE": payment_header},
            )

            if resp.status_code == 200:
                data = resp.json()
                self._total_spent += price_usd
                self._log_consultation(target, price_usd, data)
                logger.info(f"Consultation purchased: ${price_usd} from {target}")
                return data
            else:
                logger.warning(f"Payment rejected: {resp.status_code} {resp.text[:200]}")
                return None

    async def _buy_via_ap2(self, target: str) -> Optional[Dict[str, Any]]:
        """Purchase via AP2 mandate chain for full auditability."""
        from src.x402_hackathon.ap2.mandates import MandateExecutor

        executor = MandateExecutor()

        # Parse tier from URL
        tier = "premium"
        if "grow-alpha" in target:
            tier = "grow-alpha"
        elif "daily-vibes" in target:
            tier = "daily-vibes"
        elif "sensor-snapshot" in target:
            tier = "sensor-snapshot"

        from src.x402_hackathon.oracle.pricing import ORACLE_TIERS
        price_usd = ORACLE_TIERS[tier].price_usd

        # Budget check
        if self._total_spent + price_usd > self.budget_usd:
            logger.warning(f"Budget exceeded")
            return None

        chain = await executor.execute_full_chain(
            seeker="AlphaSeeker",
            goal=f"Buy {tier} intelligence for trading alpha",
            oracle_url=target,
            tier=tier,
            price_usd=price_usd,
            budget_usd=self.budget_usd,
            pay_to=os.getenv("BASE_WALLET_ADDRESS", ""),
        )

        if chain.status == "completed" and chain.receipt:
            self._total_spent += price_usd
            data = chain.receipt.response_data
            self._log_consultation(target, price_usd, data, ap2_session=chain.session_id)
            return data

        logger.warning(f"AP2 chain failed: {chain.status}")
        return None

    def decide_trade(self, oracle_data: Dict[str, Any]) -> str:
        """
        Interpret oracle response and decide trade action.

        Returns a trade decision string.
        """
        signal = oracle_data.get("signal", "NEUTRAL_GROW")
        narrative_score = oracle_data.get("narrative_score", oracle_data.get("confidence", 0.5))
        if isinstance(narrative_score, (int, float)) and narrative_score > 100:
            narrative_score = narrative_score / 100

        if "BULLISH" in signal and narrative_score > 0.7:
            return "BUY_MON — Oracle bullish with high confidence"
        elif "CAUTIOUS" in signal:
            return "HOLD — Oracle cautious, wait for better signal"
        else:
            return "MONITOR — Neutral signal, no action"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_spent_usd": round(self._total_spent, 6),
            "budget_remaining_usd": round(self.budget_usd - self._total_spent, 6),
            "consultations": len(self._consultations),
            "oracle_url": self.oracle_url,
        }

    def _log_consultation(self, url: str, price: float, data: Dict[str, Any], ap2_session: str = ""):
        entry = {
            "url": url,
            "price_usd": price,
            "signal": data.get("signal", ""),
            "trade_decision": self.decide_trade(data),
            "ap2_session": ap2_session,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._consultations.append(entry)
        # Persist
        try:
            CONSULTATION_LOG.parent.mkdir(parents=True, exist_ok=True)
            all_entries = []
            if CONSULTATION_LOG.exists():
                all_entries = json.loads(CONSULTATION_LOG.read_text())
            all_entries.append(entry)
            CONSULTATION_LOG.write_text(json.dumps(all_entries[-200:], indent=2))
        except Exception as e:
            logger.warning(f"Failed to save consultation log: {e}")


async def main():
    """Demo: run the seeker against our own oracle."""
    logging.basicConfig(level=logging.INFO)

    oracle_base = os.getenv("ORACLE_URL", "https://grokandmon.com")
    seeker = AlphaSeeker(
        oracle_url=f"{oracle_base}/api/x402/oracle",
        budget_usd=0.50,
        use_ap2=True,
    )

    print("=== Alpha Seeker Demo ===")
    print(f"Oracle: {seeker.oracle_url}")
    print(f"Budget: ${seeker.budget_usd}")
    print()

    # Try all 4 tiers
    tiers = [
        ("sensor-snapshot", f"{oracle_base}/api/x402/sensor-snapshot"),
        ("daily-vibes", f"{oracle_base}/api/x402/daily-vibes"),
        ("grow-alpha", f"{oracle_base}/api/x402/grow-alpha"),
        ("premium", f"{oracle_base}/api/x402/oracle"),
    ]

    for tier_name, url in tiers:
        print(f"\n--- Buying {tier_name} ---")
        data = await seeker.buy_consultation(url)
        if data:
            decision = seeker.decide_trade(data)
            print(f"  Signal: {data.get('signal', data.get('mood', 'N/A'))}")
            print(f"  Decision: {decision}")
        else:
            print(f"  Failed (budget or payment issue)")

    print(f"\n--- Seeker Stats ---")
    stats = seeker.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Commit**

```bash
git add src/x402_hackathon/seeker/alpha_seeker.py
git commit -m "feat: alpha seeker bot — autonomous oracle consumer with AP2 mandate chain"
```

---

## Task 9: Full Commerce Loop Demo Script

**Files:**
- Create: `src/x402_hackathon/seeker/demo.py`

**Context:** A single script that demonstrates the full bidirectional commerce loop: oracle serves paid data, seeker buys it, profit gets split, reputation gets farmed, AP2 mandates are logged.

**Step 1: Write the demo script**

```python
"""
Full Commerce Loop Demo
========================

Demonstrates ALL 5 x402 payment features in one run:
1. Oracle endpoints serve paid intelligence
2. Seeker bot discovers, pays, and consumes
3. Profit splitter allocates 60/25/10/5
4. Reputation farming records to ERC-8004
5. AP2 mandate chain logs full audit trail

Run:
    python -m src.x402_hackathon.seeker.demo

For local testing (no real payment):
    X402_DEV_MODE=true python -m src.x402_hackathon.seeker.demo --local
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("x402-demo")


async def run_demo(local: bool = False):
    """Run the full commerce loop."""
    base_url = "http://localhost:8000" if local else "https://grokandmon.com"

    print()
    print("=" * 60)
    print("  GanjaMon x402 Payment Ecosystem — Full Commerce Loop")
    print("=" * 60)
    print(f"  Oracle: {base_url}")
    print(f"  Mode: {'LOCAL (dev)' if local else 'PRODUCTION'}")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # --- Feature 1: Oracle Pricing Discovery ---
    print("\n[1/5] Oracle Pricing Discovery")
    print("-" * 40)

    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{base_url}/api/x402/pricing")
        if resp.status_code == 200:
            pricing = resp.json()
            for tier_name, tier_info in pricing.get("tiers", {}).items():
                print(f"  {tier_name}: ${tier_info['price_usd']} — {tier_info['description']}")
        else:
            print(f"  Pricing endpoint returned {resp.status_code}")

    # --- Feature 2: Seeker Bot Purchase ---
    print("\n[2/5] Alpha Seeker — Buying Intelligence")
    print("-" * 40)

    from src.x402_hackathon.seeker.alpha_seeker import AlphaSeeker
    seeker = AlphaSeeker(
        oracle_url=f"{base_url}/api/x402/oracle",
        budget_usd=0.50,
        use_ap2=True,
    )

    # Buy sensor snapshot (cheapest)
    print("\n  Tier: sensor-snapshot ($0.005)")
    data = await seeker.buy_consultation(f"{base_url}/api/x402/sensor-snapshot")
    if data:
        print(f"  Result: temp={data.get('temperature_f')}F, vpd={data.get('vpd_kpa')} kPa")
    else:
        print("  (Skipped — no payer configured or dev mode)")

    # Buy daily vibes
    print("\n  Tier: daily-vibes ($0.02)")
    data = await seeker.buy_consultation(f"{base_url}/api/x402/daily-vibes")
    if data:
        print(f"  Vibes: {data.get('vibes_score', '?')}/100 — {data.get('mood', '?')}")
        decision = seeker.decide_trade(data)
        print(f"  Trade Decision: {decision}")

    # --- Feature 3: AP2 Mandate Chain ---
    print("\n[3/5] AP2 Mandate Chain")
    print("-" * 40)

    mandates_path = Path("data/ap2_mandates.json")
    if mandates_path.exists():
        chains = json.loads(mandates_path.read_text())
        latest = chains[-1] if chains else None
        if latest:
            print(f"  Session: {latest.get('session_id', '?')}")
            print(f"  Status: {latest.get('status', '?')}")
            print(f"  Spent: ${latest.get('total_spent_usd', 0):.4f}")
            if latest.get("intent"):
                print(f"  Intent: {latest['intent'].get('goal', '?')}")
            if latest.get("cart"):
                print(f"  Cart: {latest['cart'].get('tier', '?')} @ ${latest['cart'].get('price_usd', 0)}")
            if latest.get("receipt"):
                print(f"  Delivered: {latest['receipt'].get('service_delivered', False)}")
    else:
        print("  (No AP2 mandates yet — run with payer enabled)")

    # --- Feature 4: Profit Split ---
    print("\n[4/5] Profit Allocation (60/25/10/5)")
    print("-" * 40)

    from src.payments.splitter import get_profit_splitter
    splitter = get_profit_splitter()
    status = splitter.get_status()
    print(f"  Total splits: {status['total_splits']}")
    print(f"  Total profit: ${status['total_profit_usd']:.4f}")
    for bucket, amount in status.get("total_allocated", {}).items():
        print(f"    {bucket}: ${amount:.4f}")

    # --- Feature 5: Reputation Farming ---
    print("\n[5/5] ERC-8004 Reputation Farming")
    print("-" * 40)

    from src.x402_hackathon.reputation.farming import get_oracle_stats, get_reputation_signals
    stats = get_oracle_stats()
    signals = get_reputation_signals()
    print(f"  Oracle consultations: {stats.get('oracle_consultations', 0)}")
    print(f"  Total x402 revenue: ${stats.get('total_received_usd', 0):.4f}")
    print(f"  Reputation signals: {signals}")
    print(f"  Agent: #4 on Monad (8004scan.io)")
    print(f"  Next publish: reputation_publisher cron (every 4h)")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("  Commerce Loop Complete")
    print(f"  Seeker spent: ${seeker.get_stats()['total_spent_usd']:.4f}")
    print(f"  Budget remaining: ${seeker.get_stats()['budget_remaining_usd']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    local = "--local" in sys.argv
    asyncio.run(run_demo(local=local))
```

**Step 2: Commit**

```bash
git add src/x402_hackathon/seeker/demo.py
git commit -m "feat: full commerce loop demo — all 5 x402 features in one script"
```

---

## Task 10: Update .well-known Files and Agent Card

**Files:**
- Modify: `pages-deploy/.well-known/agent-card.json` (or create x402-pricing.json)
- Check: `src/web/.well-known/` directory

**Step 1: Create x402-pricing.json**

Find the `.well-known` directory and add the pricing file. The `get_pricing_json()` function from `pricing.py` defines the schema. Write the static JSON version:

```json
{
  "version": "x402-oracle-v1",
  "agent": "GanjaMon",
  "agent_id": 4,
  "chain": "base",
  "currency": "USDC",
  "tiers": {
    "premium": {
      "price_usd": 0.15,
      "endpoint": "/api/x402/oracle",
      "description": "Full 5-domain AI synthesis in Rasta patois (Grok AI)",
      "cache_ttl_seconds": 300
    },
    "grow-alpha": {
      "price_usd": 0.05,
      "endpoint": "/api/x402/grow-alpha",
      "description": "Cross-domain plant health x market signal",
      "cache_ttl_seconds": 180
    },
    "daily-vibes": {
      "price_usd": 0.02,
      "endpoint": "/api/x402/daily-vibes",
      "description": "Composite vibes score (plant + market + social)",
      "cache_ttl_seconds": 600
    },
    "sensor-snapshot": {
      "price_usd": 0.005,
      "endpoint": "/api/x402/sensor-snapshot",
      "description": "Raw IoT sensor data (temp, humidity, VPD, CO2)",
      "cache_ttl_seconds": 30
    }
  }
}
```

**Step 2: Update agent-card.json**

Add the oracle skill to the agent card's skills list. Read the existing agent-card.json first, then add:

```json
{
  "id": "x402-oracle",
  "name": "x402 Digital Oracle",
  "description": "Paid intelligence service: 5-domain synthesis (cultivation + markets + social + culture + spirit). 4 price tiers from $0.005 to $0.15 USDC.",
  "tags": ["x402", "oracle", "paid", "commerce"]
}
```

**Step 3: Commit**

```bash
git add pages-deploy/.well-known/ src/web/.well-known/
git commit -m "feat: .well-known/x402-pricing.json + agent card oracle skill"
```

---

## Task 11: Local Integration Test

**Step 1: Set dev mode and run the API locally**

```bash
cd /mnt/c/Users/natha/sol-cannabis
export X402_DEV_MODE=true
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &
sleep 5
```

**Step 2: Test all 4 oracle endpoints**

```bash
# Pricing (free)
curl -s http://localhost:8000/api/x402/pricing | python3 -m json.tool

# Sensor snapshot (dev mode = free)
curl -s http://localhost:8000/api/x402/sensor-snapshot | python3 -m json.tool

# Daily vibes
curl -s http://localhost:8000/api/x402/daily-vibes | python3 -m json.tool

# Grow alpha
curl -s http://localhost:8000/api/x402/grow-alpha | python3 -m json.tool

# Premium oracle
curl -s http://localhost:8000/api/x402/oracle | python3 -m json.tool

# Test 402 response (without dev mode)
X402_DEV_MODE=false curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/x402/oracle
# Expected: 402
```

**Step 3: Run demo script**

```bash
X402_DEV_MODE=true python3 -m src.x402_hackathon.seeker.demo --local
```

**Step 4: Fix any errors, then commit**

```bash
git add -A
git commit -m "fix: integration test fixes for x402 oracle endpoints"
```

---

## Task 12: Deploy to Chromebook

**Step 1: Deploy the new code**

```bash
cd /mnt/c/Users/natha/sol-cannabis
bash deploy.sh --restart
```

**Step 2: Verify endpoints are live**

```bash
# Health check
curl -s https://grokandmon.com/api/admin/ping

# Oracle pricing
curl -s https://grokandmon.com/api/x402/pricing | python3 -m json.tool

# 402 response (no payment)
curl -s -w "\n%{http_code}\n" https://grokandmon.com/api/x402/oracle
```

**Step 3: Commit deploy confirmation**

```bash
git add -A
git commit -m "deploy: x402 oracle endpoints live on grokandmon.com"
```

---

## Execution Notes

- **Total new files:** 10 Python files across 4 subpackages + 1 JSON config
- **Total new lines:** ~1200
- **Existing code modified:** `src/api/app.py` (3 lines), `src/blockchain/reputation_publisher.py` (~8 lines)
- **No new dependencies** — everything uses existing packages
- **Dev mode:** `X402_DEV_MODE=true` bypasses payment verification for local testing
- **Gotcha:** `grok-4-1-fast-non-reasoning` does NOT support `presence_penalty` — omit it
- **Gotcha:** Glob tool times out on project root — use specific paths
- **Gotcha:** Two separate APIs exist (port 8000 main, port 8080 trading) — oracle goes on main
