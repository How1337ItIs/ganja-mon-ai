"""
AP2 Mandate Chain - structured autonomous commerce in 4 phases.

Implements the full mandate lifecycle:
1. INTENT - Agent expresses a need
2. CART - Select oracle/service and tier
3. PAYMENT - Sign x402 authorization
4. RECEIPT - Receive service, record outcome
"""

import json
import base64
import httpx
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

from src.a2a.x402 import get_x402_payer


# Data directory
MANDATES_PATH = Path("data/ap2_mandates.json")


class MandatePhase(str, Enum):
    """4-phase mandate lifecycle."""
    INTENT = "INTENT"
    CART = "CART"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"


class IntentMandate(BaseModel):
    """Phase 1: Seeker expresses a need."""
    id: str
    phase: MandatePhase = MandatePhase.INTENT
    seeker: str  # Agent name or address
    goal: str  # What the agent wants to accomplish
    budget_usd: float  # Maximum willing to spend
    preferences: dict = {}  # Additional parameters
    timestamp: str


class CartMandate(BaseModel):
    """Phase 2: Select service and pricing."""
    id: str
    phase: MandatePhase = MandatePhase.CART
    intent_id: str  # Links back to intent
    oracle_url: str  # Service endpoint
    tier: str  # Service tier (tier1, tier2, tier3)
    price_usd: float
    currency: str = "USDC"
    chain: str = "base"
    pay_to: str  # Recipient address
    timestamp: str


class PaymentMandate(BaseModel):
    """Phase 3: Signed payment authorization."""
    id: str
    phase: MandatePhase = MandatePhase.PAYMENT
    cart_id: str  # Links back to cart
    payment_header: str  # Base64-encoded x402 payment proof
    signed_at: str
    tx_hash: Optional[str] = None  # On-chain settlement (if applicable)
    timestamp: str


class PaymentReceipt(BaseModel):
    """Phase 4: Service delivery and outcome."""
    id: str
    phase: MandatePhase = MandatePhase.RECEIPT
    payment_id: str  # Links back to payment
    service_delivered: bool
    response_data: dict  # Oracle response payload
    trade_decision: Optional[str] = None  # For trading oracles
    satisfaction: Optional[float] = None  # 0-1 rating
    timestamp: str


class MandateChain(BaseModel):
    """Complete 4-phase mandate execution chain."""
    session_id: str
    intent: Optional[IntentMandate] = None
    cart: Optional[CartMandate] = None
    payment: Optional[PaymentMandate] = None
    receipt: Optional[PaymentReceipt] = None
    status: str = "in_progress"  # in_progress | completed | failed
    total_spent_usd: float = 0.0
    created_at: str


class MandateExecutor:
    """
    Executes and tracks AP2 mandate chains.

    Manages the full lifecycle from intent to receipt.
    """

    def __init__(self):
        """Initialize executor and load history."""
        self.history = self._load_history()

    def create_intent(
        self,
        seeker: str,
        goal: str,
        budget_usd: float,
        **preferences
    ) -> IntentMandate:
        """
        Create Phase 1: Intent mandate.

        Args:
            seeker: Agent identifier
            goal: What the agent wants to accomplish
            budget_usd: Maximum budget
            **preferences: Additional parameters

        Returns:
            IntentMandate instance
        """
        import uuid

        intent = IntentMandate(
            id=f"int_{uuid.uuid4().hex[:8]}",
            seeker=seeker,
            goal=goal,
            budget_usd=budget_usd,
            preferences=preferences,
            timestamp=datetime.now().isoformat(),
        )
        return intent

    def create_cart(
        self,
        intent: IntentMandate,
        oracle_url: str,
        tier: str,
        price_usd: float,
        pay_to: str,
    ) -> CartMandate:
        """
        Create Phase 2: Cart mandate.

        Args:
            intent: Intent mandate from phase 1
            oracle_url: Service endpoint
            tier: Service tier
            price_usd: Price for this tier
            pay_to: Payment recipient address

        Returns:
            CartMandate instance
        """
        import uuid

        # Validate budget
        if price_usd > intent.budget_usd:
            raise ValueError(f"Price ${price_usd} exceeds budget ${intent.budget_usd}")

        cart = CartMandate(
            id=f"cart_{uuid.uuid4().hex[:8]}",
            intent_id=intent.id,
            oracle_url=oracle_url,
            tier=tier,
            price_usd=price_usd,
            pay_to=pay_to,
            timestamp=datetime.now().isoformat(),
        )
        return cart

    async def create_payment(self, cart: CartMandate) -> Optional[PaymentMandate]:
        """
        Create Phase 3: Payment mandate.

        Signs an x402 payment authorization using EIP-3009.

        Args:
            cart: Cart mandate from phase 2

        Returns:
            PaymentMandate instance or None if signing fails
        """
        import uuid

        payer = get_x402_payer()
        if not payer:
            return None

        # Convert USD to USDC (6 decimals)
        amount_usdc = int(cart.price_usd * 1_000_000)

        # Build payment metadata
        payment_meta = {
            "network": "eip155:8453",  # Base
            "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
            "amount": amount_usdc,
            "payTo": cart.pay_to,
            "maxTimeoutSeconds": 300,
            "extra": {
                "name": "USD Coin",
                "version": "2",
                "resource": cart.oracle_url,
            },
        }

        # Sign payment (EIP-3009 authorization)
        try:
            payment_proof = await payer.pay_402(
                resource=cart.oracle_url,
                accepted={
                    "network": payment_meta["network"],
                    "asset": payment_meta["asset"],
                    "amount": str(amount_usdc),
                    "payTo": cart.pay_to,
                },
            )

            if not payment_proof:
                return None

            # Encode payment proof as base64
            payment_header = base64.b64encode(
                json.dumps(payment_proof).encode()
            ).decode()

            payment = PaymentMandate(
                id=f"pay_{uuid.uuid4().hex[:8]}",
                cart_id=cart.id,
                payment_header=payment_header,
                signed_at=datetime.now().isoformat(),
                timestamp=datetime.now().isoformat(),
            )
            return payment

        except Exception as e:
            print(f"Payment signing failed: {e}")
            return None

    def create_receipt(
        self,
        payment: PaymentMandate,
        response_data: dict,
        trade_decision: Optional[str] = None,
        satisfaction: Optional[float] = None,
    ) -> PaymentReceipt:
        """
        Create Phase 4: Receipt mandate.

        Args:
            payment: Payment mandate from phase 3
            response_data: Oracle response payload
            trade_decision: Optional trade decision
            satisfaction: Optional satisfaction rating (0-1)

        Returns:
            PaymentReceipt instance
        """
        import uuid

        receipt = PaymentReceipt(
            id=f"rcpt_{uuid.uuid4().hex[:8]}",
            payment_id=payment.id,
            service_delivered=True,
            response_data=response_data,
            trade_decision=trade_decision,
            satisfaction=satisfaction,
            timestamp=datetime.now().isoformat(),
        )
        return receipt

    async def execute_full_chain(
        self,
        seeker: str,
        goal: str,
        oracle_url: str,
        tier: str,
        price_usd: float,
        budget_usd: float,
        pay_to: str,
        **preferences,
    ) -> MandateChain:
        """
        Execute full 4-phase mandate chain.

        Args:
            seeker: Agent identifier
            goal: What the agent wants
            oracle_url: Service endpoint
            tier: Service tier
            price_usd: Price
            budget_usd: Maximum budget
            pay_to: Payment recipient
            **preferences: Additional intent parameters

        Returns:
            Complete MandateChain
        """
        import uuid

        session_id = f"chain_{uuid.uuid4().hex[:8]}"
        chain = MandateChain(
            session_id=session_id,
            created_at=datetime.now().isoformat(),
        )

        try:
            # Phase 1: Intent
            intent = self.create_intent(seeker, goal, budget_usd, **preferences)
            chain.intent = intent

            # Phase 2: Cart
            cart = self.create_cart(intent, oracle_url, tier, price_usd, pay_to)
            chain.cart = cart

            # Phase 3: Payment
            payment = await self.create_payment(cart)
            if not payment:
                chain.status = "failed"
                self._save_chain(chain)
                return chain

            chain.payment = payment

            # Call oracle with payment proof
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Decode payment header
                payment_data = json.loads(
                    base64.b64decode(payment.payment_header).decode()
                )

                response = await client.post(
                    oracle_url,
                    headers={
                        "PAYMENT-SIGNATURE": payment.payment_header,
                        "Content-Type": "application/json",
                    },
                    json={
                        "tier": tier,
                        "goal": goal,
                        "payment": payment_data,
                    },
                )

                response.raise_for_status()
                oracle_response = response.json()

            # Phase 4: Receipt
            receipt = self.create_receipt(
                payment,
                response_data=oracle_response,
                trade_decision=oracle_response.get("decision"),
                satisfaction=oracle_response.get("confidence"),
            )
            chain.receipt = receipt

            # Complete
            chain.status = "completed"
            chain.total_spent_usd = price_usd

        except Exception as e:
            print(f"Mandate chain execution failed: {e}")
            chain.status = "failed"

        # Save to history
        self._save_chain(chain)
        return chain

    def get_history(self) -> list[dict]:
        """
        Get mandate chain history.

        Returns:
            List of mandate chain dicts
        """
        return self.history

    def _save_chain(self, chain: MandateChain) -> None:
        """
        Persist mandate chain to history.

        Args:
            chain: MandateChain to save
        """
        # Add to history (keep last 100)
        self.history.append(chain.model_dump())
        self.history = self.history[-100:]

        # Ensure directory exists
        MANDATES_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Save to disk
        with open(MANDATES_PATH, "w") as f:
            json.dump(self.history, f, indent=2)

    def _load_history(self) -> list[dict]:
        """
        Load mandate chain history from disk.

        Returns:
            List of mandate chain dicts
        """
        if not MANDATES_PATH.exists():
            return []

        try:
            with open(MANDATES_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
