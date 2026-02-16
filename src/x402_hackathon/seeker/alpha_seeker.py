"""
Autonomous seeker that buys intelligence from x402-compatible oracles.

The AlphaSeeker discovers oracle pricing, purchases consultations using x402 micropayments,
and makes trade decisions based on the intelligence received.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx

from src.a2a.x402 import get_x402_payer
from src.x402_hackathon.ap2.mandates import MandateExecutor
from src.x402_hackathon.oracle.pricing import ORACLE_TIERS

DEFAULT_ORACLE_URL = "https://grokandmon.com/api/x402/oracle"
CONSULTATION_LOG = Path("data/seeker_consultations.json")


class AlphaSeeker:
    """Autonomous intelligence buyer using x402 micropayments."""

    def __init__(
        self,
        oracle_url: str = DEFAULT_ORACLE_URL,
        budget_usd: float = 1.0,
        use_ap2: bool = True
    ):
        """
        Initialize the alpha seeker.

        Args:
            oracle_url: Base URL of the oracle service
            budget_usd: Maximum budget in USD
            use_ap2: Use AP2 mandate chain (True) or direct payment (False)
        """
        self.oracle_url = oracle_url.rstrip("/")
        self.budget_usd = budget_usd
        self.use_ap2 = use_ap2
        self.total_spent = 0.0
        self.consultations: List[Dict[str, Any]] = []

        # Ensure consultation log directory exists
        CONSULTATION_LOG.parent.mkdir(parents=True, exist_ok=True)

        # Load existing consultations
        if CONSULTATION_LOG.exists():
            try:
                with open(CONSULTATION_LOG, "r") as f:
                    self.consultations = json.load(f)
            except Exception:
                self.consultations = []

    async def discover_oracle(self, url: str) -> Dict[str, Any]:
        """
        Discover oracle endpoint - check if it returns data or requires payment.

        Args:
            url: Full URL of the oracle endpoint

        Returns:
            Dict with 'status', 'data' (if 200), or 'pricing' (if 402)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(url)

                if resp.status_code == 200:
                    return {
                        "status": "free",
                        "data": resp.json()
                    }
                elif resp.status_code == 402:
                    # Parse pricing from Accept-Payment header
                    pricing_info = {}
                    if "Accept-Payment" in resp.headers:
                        accept_payment = resp.headers["Accept-Payment"]
                        # Example: "USDC 0.001 eip155:8453:0xUSDC_ADDRESS"
                        parts = accept_payment.split()
                        if len(parts) >= 2:
                            pricing_info = {
                                "currency": parts[0],
                                "amount": float(parts[1]),
                                "address": parts[2] if len(parts) > 2 else None
                            }

                    return {
                        "status": "payment_required",
                        "pricing": pricing_info,
                        "message": resp.json().get("message", "Payment required")
                    }
                else:
                    return {
                        "status": "error",
                        "code": resp.status_code,
                        "message": resp.text
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }

    async def buy_consultation(self, tier_url: str) -> Dict[str, Any]:
        """
        Purchase a consultation from the oracle.

        Args:
            tier_url: Full URL of the tier endpoint (e.g., /oracle/sensor-snapshot)

        Returns:
            Oracle response data or error
        """
        if self.use_ap2:
            return await self._buy_via_ap2(tier_url)
        else:
            return await self._buy_direct(tier_url)

    async def _buy_direct(self, target: str) -> Dict[str, Any]:
        """
        Direct x402 payment flow without AP2.

        Args:
            target: Full URL of the oracle endpoint

        Returns:
            Oracle response data
        """
        # Step 1: Discover pricing
        discovery = await self.discover_oracle(target)

        if discovery["status"] == "free":
            return discovery["data"]

        if discovery["status"] != "payment_required":
            return {"error": f"Discovery failed: {discovery.get('message', 'Unknown error')}"}

        pricing = discovery["pricing"]
        price_usd = pricing.get("amount", 0.0)

        # Step 2: Budget check
        if self.total_spent + price_usd > self.budget_usd:
            return {"error": f"Insufficient budget (${self.budget_usd - self.total_spent:.4f} remaining)"}

        # Step 3: Get payer and build payment
        payer = get_x402_payer()
        if not payer:
            return {"error": "No x402 payer configured"}

        # Step 4: Make payment
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Initial request to get 402 and pricing
                resp = await client.get(target)
                if resp.status_code != 402:
                    if resp.status_code == 200:
                        return resp.json()
                    return {"error": f"Unexpected status: {resp.status_code}"}

                # Build Accept-Payment header from pricing
                accept_payment = f"{pricing['currency']} {pricing['amount']}"
                if pricing.get("address"):
                    accept_payment += f" {pricing['address']}"

                # Generate payment signature
                payment_header = payer.pay_402(
                    resource=target,
                    accepted=accept_payment,
                    payload=b""
                )

                # Retry with payment
                headers = {"PAYMENT-SIGNATURE": payment_header}
                paid_resp = await client.get(target, headers=headers)

                if paid_resp.status_code == 200:
                    data = paid_resp.json()
                    self._log_consultation(target, price_usd, data, ap2_session=None)
                    self.total_spent += price_usd
                    return data
                else:
                    return {"error": f"Payment failed: {paid_resp.status_code} - {paid_resp.text}"}

        except Exception as e:
            return {"error": f"Purchase failed: {str(e)}"}

    async def _buy_via_ap2(self, target: str) -> Dict[str, Any]:
        """
        Purchase using AP2 mandate chain.

        Args:
            target: Full URL of the oracle endpoint

        Returns:
            Oracle response data
        """
        # Extract tier name from URL
        tier_name = target.split("/")[-1]

        # Get price from ORACLE_TIERS
        tier_config = ORACLE_TIERS.get(tier_name)
        if not tier_config:
            return {"error": f"Unknown tier: {tier_name}"}

        price_usd = tier_config.price_usd

        # Budget check
        if self.total_spent + price_usd > self.budget_usd:
            return {"error": f"Insufficient budget (${self.budget_usd - self.total_spent:.4f} remaining)"}

        # Execute mandate chain
        try:
            pay_to = os.environ.get(
                "BASE_WALLET_ADDRESS",
                os.environ.get("MONAD_WALLET_ADDRESS", ""),
            )
            executor = MandateExecutor()
            chain = await executor.execute_full_chain(
                seeker="GanjaMon-AlphaSeeker",
                goal=f"Buy {tier_name} oracle intelligence",
                oracle_url=target,
                tier=tier_name,
                price_usd=price_usd,
                budget_usd=self.budget_usd,
                pay_to=pay_to,
            )

            if chain.status == "completed" and chain.receipt:
                data = chain.receipt.response_data
                ap2_session = chain.session_id
                self._log_consultation(target, price_usd, data, ap2_session)
                self.total_spent += price_usd
                return data
            elif chain.status == "failed" and not pay_to:
                # No payer configured — fall back to direct GET (dev mode)
                return await self._buy_direct(target)
            else:
                return {"error": f"AP2 chain failed (status={chain.status})"}

        except Exception as e:
            return {"error": f"AP2 purchase failed: {str(e)}"}

    def decide_trade(self, oracle_data: Dict[str, Any]) -> str:
        """
        Make a trade decision based on oracle intelligence.

        Args:
            oracle_data: Data returned from oracle consultation

        Returns:
            Trade decision: "BUY_MON", "HOLD", or "MONITOR"
        """
        if "error" in oracle_data:
            return "MONITOR"

        # Extract signal strength
        signal = oracle_data.get("signal", "NEUTRAL")
        narrative_score = oracle_data.get("narrative_score", 0.5)

        # Decision logic
        if signal == "STRONG_BUY" and narrative_score >= 0.7:
            return "BUY_MON"
        elif signal in ["BUY", "STRONG_BUY"] and narrative_score >= 0.6:
            return "BUY_MON"
        elif signal in ["SELL", "STRONG_SELL"] or narrative_score < 0.3:
            return "MONITOR"
        else:
            return "HOLD"

    def get_stats(self) -> Dict[str, Any]:
        """Get seeker statistics."""
        return {
            "total_spent": self.total_spent,
            "budget_remaining": self.budget_usd - self.total_spent,
            "consultations_count": len(self.consultations),
            "budget_usd": self.budget_usd
        }

    def _log_consultation(
        self,
        url: str,
        price: float,
        data: Dict[str, Any],
        ap2_session: Optional[str]
    ) -> None:
        """
        Log a consultation to persistent storage.

        Args:
            url: Oracle endpoint URL
            price: Price paid in USD
            data: Oracle response data
            ap2_session: AP2 session ID if used
        """
        consultation = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": url,
            "price_usd": price,
            "tier": url.split("/")[-1],
            "signal": data.get("signal"),
            "narrative_score": data.get("narrative_score"),
            "ap2_session": ap2_session,
            "method": "ap2" if ap2_session else "direct"
        }

        self.consultations.append(consultation)

        # Keep only last 200 consultations
        if len(self.consultations) > 200:
            self.consultations = self.consultations[-200:]

        # Save to file
        try:
            with open(CONSULTATION_LOG, "w") as f:
                json.dump(self.consultations, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save consultation log: {e}")


async def main():
    """Demo that buys all 4 tiers and makes trade decisions."""
    print("🔍 Alpha Seeker Demo\n")

    # Get oracle base URL from environment
    oracle_base = os.getenv("ORACLE_URL", "https://grokandmon.com")

    # Initialize seeker with $1 budget
    seeker = AlphaSeeker(
        oracle_url=f"{oracle_base}/api/x402/oracle",
        budget_usd=1.0,
        use_ap2=True  # Use AP2 mandate chain
    )

    # Define tiers in order
    tiers = [
        "sensor-snapshot",
        "daily-vibes",
        "grow-alpha",
        "premium"
    ]

    print(f"Budget: ${seeker.budget_usd:.2f}\n")

    # Buy each tier
    for tier in tiers:
        tier_url = f"{seeker.oracle_url}/{tier}"
        print(f"📊 Purchasing: {tier}")
        print(f"   URL: {tier_url}")

        data = await seeker.buy_consultation(tier_url)

        if "error" in data:
            print(f"   ❌ Error: {data['error']}\n")
            continue

        # Make trade decision
        decision = seeker.decide_trade(data)

        print(f"   ✅ Signal: {data.get('signal', 'N/A')}")
        print(f"   📈 Narrative Score: {data.get('narrative_score', 0):.2f}")
        print(f"   🎯 Decision: {decision}\n")

    # Print final stats
    stats = seeker.get_stats()
    print("\n💰 Final Stats:")
    print(f"   Total Spent: ${stats['total_spent']:.4f}")
    print(f"   Remaining: ${stats['budget_remaining']:.4f}")
    print(f"   Consultations: {stats['consultations_count']}")


if __name__ == "__main__":
    asyncio.run(main())
