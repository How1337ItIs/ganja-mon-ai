"""
X402 Oracle Paid Endpoints
===========================

4 paid FastAPI routes using X402Verifier for payment verification.

Tiers:
- /api/x402/oracle — Premium oracle ($0.15, 5min cache)
- /api/x402/grow-alpha — Grow alpha signals ($0.05, 3min cache)
- /api/x402/daily-vibes — Daily vibes/wisdom ($0.02, 10min cache)
- /api/x402/sensor-snapshot — Raw sensor data ($0.005, 30s cache)
- /api/x402/pricing — Free pricing info (no payment)
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.a2a.x402 import X402Verifier
from src.payments.splitter import get_profit_splitter

from .pricing import ORACLE_TIERS, get_pricing_json
from .synthesis import (
    synthesize_premium_oracle,
    synthesize_grow_alpha,
    synthesize_daily_vibes,
    synthesize_sensor_snapshot,
)

# Payment header name (CRITICAL: this is the correct header name)
PAYMENT_HEADER = "PAYMENT-SIGNATURE"

# Dev mode bypasses payment verification
DEV_MODE = os.getenv("X402_DEV_MODE", "false").lower() == "true"

# Stats tracking
STATS_PATH = Path("data/a2a_stats.json")

router = APIRouter(tags=["x402-oracle"])


# ============================================================================
# Helper Functions
# ============================================================================


def _get_verifier_for_tier(tier_name: str) -> X402Verifier:
    """
    Creates an X402Verifier instance with the tier's price.

    Args:
        tier_name: Tier name (premium, grow-alpha, daily-vibes, sensor-snapshot)

    Returns:
        Configured X402Verifier instance
    """
    tier = ORACLE_TIERS[tier_name]
    return X402Verifier(
        price_usd=tier.price_usd,
        currency="USDC",
        chain=os.getenv("A2A_PAYMENT_CHAIN", "base"),
        pay_to=os.getenv("BASE_WALLET_ADDRESS", os.getenv("MONAD_WALLET_ADDRESS", "")),
        require_payment=not DEV_MODE,
    )


def _build_402_response(tier_name: str) -> JSONResponse:
    """
    Returns 402 Payment Required response with Accept-Payment header.

    Args:
        tier_name: Tier name

    Returns:
        JSONResponse with 402 status and payment requirements
    """
    tier = ORACLE_TIERS[tier_name]
    verifier = _get_verifier_for_tier(tier_name)
    requirements = verifier.get_requirements()

    # Add tier info and pricing URL
    requirements["tier"] = tier_name
    requirements["description"] = tier.description
    requirements["pricingUrl"] = "https://grokandmon.com/.well-known/x402-pricing.json"

    return JSONResponse(
        status_code=402,
        content={
            "error": "Payment required",
            "tier": tier_name,
            "price_usd": tier.price_usd,
            "message": f"This endpoint requires ${tier.price_usd} USDC payment on Base",
        },
        headers={
            "Accept-Payment": json.dumps(requirements),
        },
    )


def _record_payment(tier_name: str, amount_usd: float, payer: str = "") -> None:
    """
    Records an oracle payment in two places:

    1. ProfitSplitter — Creates and executes a batch for 60/25/10/5 allocation
    2. A2A Stats — Updates oracle consultation counters and payment tracking

    Args:
        tier_name: Tier name (premium, grow-alpha, daily-vibes, sensor-snapshot)
        amount_usd: Payment amount in USD
        payer: Optional payer identifier
    """
    # 1. ProfitSplitter batch
    try:
        splitter = get_profit_splitter()
        batch = splitter.create_batch(amount_usd, f"x402-oracle-{tier_name}")
        splitter.execute_batch(batch)
    except Exception as e:
        # Don't fail the request if splitter fails
        print(f"Warning: ProfitSplitter failed for {tier_name}: {e}")

    # 2. A2A Stats
    try:
        # Load existing stats
        if STATS_PATH.exists():
            with open(STATS_PATH, "r") as f:
                stats = json.load(f)
        else:
            stats = {
                "total_received_usd": 0.0,
                "oracle_consultations": 0,
                "oracle_premium_count": 0,
                "oracle_grow-alpha_count": 0,
                "oracle_daily-vibes_count": 0,
                "oracle_sensor-snapshot_count": 0,
                "last_oracle_payment": None,
                "last_payer": None,
            }

        # Update totals
        stats["total_received_usd"] += amount_usd
        stats["oracle_consultations"] += 1

        # Update tier-specific counter
        tier_key = f"oracle_{tier_name}_count"
        stats[tier_key] = stats.get(tier_key, 0) + 1

        # Update last payment info
        stats["last_oracle_payment"] = time.time()
        if payer:
            stats["last_payer"] = payer

        # Save back
        STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATS_PATH, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        # Don't fail the request if stats update fails
        print(f"Warning: A2A stats update failed for {tier_name}: {e}")


def _verify_and_serve(request: Request, tier_name: str, synthesize_fn):
    """
    Common payment verification and synthesis flow.

    Args:
        request: FastAPI Request object
        tier_name: Tier name
        synthesize_fn: Function to call to generate oracle response (no args)

    Returns:
        JSONResponse with oracle data (200) or payment required (402)
    """
    # Get payment header
    payment = request.headers.get(PAYMENT_HEADER) or request.headers.get("X-402-Payment")

    # DEV MODE: no payment required
    if DEV_MODE and not payment:
        result = synthesize_fn()
        result["_dev_mode"] = True
        return JSONResponse(content=result)

    # No payment → 402
    if not payment:
        return _build_402_response(tier_name)

    # Verify payment
    verifier = _get_verifier_for_tier(tier_name)
    valid, reason = verifier.verify_header(payment)

    if not valid:
        # Invalid payment → 402 with reason
        response = _build_402_response(tier_name)
        response_data = json.loads(response.body)
        response_data["error"] = f"Payment verification failed: {reason}"
        return JSONResponse(
            status_code=402,
            content=response_data,
            headers=response.headers,
        )

    # Valid payment → synthesize and serve
    result = synthesize_fn()

    # Add payment metadata
    tier = ORACLE_TIERS[tier_name]
    result["payment_verified"] = True
    result["payment_usd"] = tier.price_usd
    result["timestamp"] = time.time()

    # Record payment
    _record_payment(tier_name, tier.price_usd, payer="unknown")

    return JSONResponse(content=result)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/api/x402/oracle")
async def oracle_premium(request: Request):
    """
    Premium Oracle — Full 5-domain AI synthesis in Rasta patois.

    Price: $0.15 USDC on Base
    Cache: 5 minutes
    """
    return _verify_and_serve(request, "premium", synthesize_premium_oracle)


@router.get("/api/x402/grow-alpha")
async def oracle_grow_alpha(request: Request):
    """
    Grow Alpha — Cross-domain plant health × market signal.

    Price: $0.05 USDC on Base
    Cache: 3 minutes
    """
    return _verify_and_serve(request, "grow-alpha", synthesize_grow_alpha)


@router.get("/api/x402/daily-vibes")
async def oracle_daily_vibes(request: Request):
    """
    Daily Vibes — Composite vibes score (plant + market + social).

    Price: $0.02 USDC on Base
    Cache: 10 minutes
    """
    return _verify_and_serve(request, "daily-vibes", synthesize_daily_vibes)


@router.get("/api/x402/sensor-snapshot")
async def oracle_sensor_snapshot(request: Request):
    """
    Sensor Snapshot — Raw IoT sensor data (temp, humidity, VPD, CO2).

    Price: $0.005 USDC on Base
    Cache: 30 seconds
    """
    return _verify_and_serve(request, "sensor-snapshot", synthesize_sensor_snapshot)


@router.get("/api/x402/pricing")
async def oracle_pricing():
    """
    Pricing Info — Free endpoint, returns tier pricing and metadata.

    No payment required.
    """
    pricing = get_pricing_json()

    # Merge art studio pricing
    try:
        from .art_studio import get_art_pricing, get_gallery_stats
        pricing["art_studio"] = get_art_pricing()
        pricing["gallery_stats"] = get_gallery_stats()
    except Exception:
        pass

    return JSONResponse(content=pricing)


# ============================================================================
# Art Studio Endpoints
# ============================================================================


@router.post("/api/x402/art/commission")
async def art_commission(request: Request):
    """
    Art Commission — Custom art from prompt/image.

    Price: $0.25 USDC on Base
    Send JSON body: {"prompt": "...", "image_b64": "...(optional)", "style": "..."}
    """
    return await _art_endpoint(request, "commission", 0.25)


@router.post("/api/x402/art/pfp")
async def art_pfp(request: Request):
    """
    PFP Generator — Unique profile picture for agents.

    Price: $0.10 USDC on Base
    Send JSON body: {"prompt": "agent name/description", "style": "..."}
    """
    return await _art_endpoint(request, "pfp", 0.10)


@router.post("/api/x402/art/meme")
async def art_meme(request: Request):
    """
    Meme Generator — Rasta meme from context/trends.

    Price: $0.05 USDC on Base
    Send JSON body: {"prompt": "topic/context", "style": "..."}
    """
    return await _art_endpoint(request, "meme", 0.05)


@router.post("/api/x402/art/ganjafy")
async def art_ganjafy(request: Request):
    """
    Ganjafy — Transform image into Rasta style.

    Price: $0.03 USDC on Base
    Send JSON body: {"image_b64": "...(required)", "prompt": "..."}
    """
    return await _art_endpoint(request, "ganjafy", 0.03)


@router.post("/api/x402/art/banner")
async def art_banner(request: Request):
    """
    Banner Generator — DexScreener/social media banners.

    Price: $0.08 USDC on Base
    Send JSON body: {"prompt": "token/project info", "style": "..."}
    """
    return await _art_endpoint(request, "banner", 0.08)


@router.get("/api/x402/art/gallery")
async def art_gallery():
    """
    Art Gallery — Browse GanjaMon's art collection.

    No payment required.
    """
    try:
        from .art_studio import get_gallery, get_gallery_stats
        return JSONResponse(content={
            "gallery": get_gallery()[-20:],  # Last 20 pieces
            "stats": get_gallery_stats(),
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


async def _art_endpoint(request: Request, mode: str, price_usd: float):
    """
    Common art endpoint handler with payment verification.

    Accepts POST with JSON body containing prompt, image_b64, and style.
    """
    from .art_studio import create_art, ART_MODES

    # Check payment
    payment = request.headers.get(PAYMENT_HEADER) or request.headers.get("X-402-Payment")

    if DEV_MODE and not payment:
        # Dev mode — process without payment
        body = await _parse_art_body(request)
        result = await create_art(
            mode=mode,
            prompt=body.get("prompt", ""),
            source_image_b64=body.get("image_b64"),
            style_hints={"style": body.get("style", "")},
        )
        if "error" in result:
            return JSONResponse(content=result, status_code=500)
        result["_dev_mode"] = True
        # Don't return the full image in JSON — too large
        result.pop("image_b64", None)
        return JSONResponse(content=result)

    if not payment:
        # Return 402 with art-specific pricing
        verifier = X402Verifier(
            price_usd=price_usd,
            currency="USDC",
            chain=os.getenv("A2A_PAYMENT_CHAIN", "base"),
            pay_to=os.getenv("BASE_WALLET_ADDRESS", os.getenv("MONAD_WALLET_ADDRESS", "")),
            require_payment=True,
        )
        requirements = verifier.get_requirements()
        requirements["mode"] = mode
        requirements["description"] = ART_MODES[mode]["description"]

        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment required",
                "mode": mode,
                "price_usd": price_usd,
                "message": f"Art commission ({mode}) requires ${price_usd} USDC on Base",
                "accepts": "POST with JSON body: {prompt, image_b64?, style?}",
            },
            headers={"Accept-Payment": json.dumps(requirements)},
        )

    # Verify payment
    verifier = X402Verifier(
        price_usd=price_usd,
        currency="USDC",
        chain=os.getenv("A2A_PAYMENT_CHAIN", "base"),
        pay_to=os.getenv("BASE_WALLET_ADDRESS", os.getenv("MONAD_WALLET_ADDRESS", "")),
        require_payment=not DEV_MODE,
    )
    valid, reason = verifier.verify_header(payment)

    if not valid:
        return JSONResponse(
            status_code=402,
            content={"error": f"Payment verification failed: {reason}"},
        )

    # Process art request
    body = await _parse_art_body(request)
    result = await create_art(
        mode=mode,
        prompt=body.get("prompt", ""),
        source_image_b64=body.get("image_b64"),
        style_hints={"style": body.get("style", "")},
    )

    if "error" in result:
        return JSONResponse(content=result, status_code=500)

    # Record payment
    _record_payment(f"art-{mode}", price_usd, payer="unknown")

    # Announce on socials (fire-and-forget, copy image before popping)
    try:
        from .art_studio import post_art_to_socials
        social_result = dict(result)  # shallow copy so pop doesn't race
        asyncio.create_task(post_art_to_socials(
            social_result, mode=mode,
            prompt=body.get("prompt", ""),
            commissioned_by="an x402 agent",
        ))
    except Exception:
        pass

    result["payment_verified"] = True
    result["payment_usd"] = price_usd
    # Don't return full image in JSON
    result.pop("image_b64", None)
    return JSONResponse(content=result)


async def _parse_art_body(request: Request) -> dict:
    """Parse art request body, handling both JSON and empty bodies."""
    try:
        return await request.json()
    except Exception:
        return {}
