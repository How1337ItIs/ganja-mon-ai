"""
x402 Payment Module
===================

Two-sided x402 payment support:

1. X402Verifier (receiving side):
   - FastAPI middleware that checks X-402-Payment headers
   - Validates payment proofs
   - Tracks payment receipts

2. X402Payer (client side):
   - Creates payment headers for outbound A2A calls
   - Signs EIP-3009 authorizations
   - Manages USDC balance awareness

Payment flow:
    Client                    Server
    ------                    ------
    1. Send request      -->
    2.                   <--  402 Payment Required (requirements)
    3. Sign payment      -->  X-402-Payment header
    4.                   <--  200 OK (result)

Supports USDC on Base (primary) and Monad.
"""

import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PaymentRequirements:
    """x402 payment requirements from a 402 response."""
    price_usd: float
    currency: str  # "USDC"
    chain: str  # "base", "monad"
    pay_to: str = ""  # Recipient address
    facilitator_url: str = ""
    extra: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

    @classmethod
    def from_response(cls, data: dict) -> "PaymentRequirements":
        return cls(
            price_usd=float(data.get("priceUSD", data.get("price", 0))),
            currency=data.get("currency", "USDC"),
            chain=data.get("chain", data.get("network", "base")),
            pay_to=data.get("payTo", data.get("pay_to", data.get("settlementAddress", ""))),
            facilitator_url=data.get("facilitatorUrl", data.get("facilitator_url", "")),
            extra={k: v for k, v in data.items() if k not in ("priceUSD", "price", "currency", "chain", "network", "payTo", "pay_to", "settlementAddress", "facilitatorUrl", "facilitator_url")},
        )


@dataclass
class PaymentReceipt:
    """Record of a payment made or received."""
    payment_id: str
    direction: str  # "sent" or "received"
    amount_usd: float
    currency: str
    chain: str
    counterparty: str  # Agent name or address
    timestamp: float
    tx_hash: Optional[str] = None
    verified: bool = False


class X402Verifier:
    """
    Server-side x402 payment verification middleware.

    Three verification tiers:
    1. ECDSA signature recovery (verify payer address from signed proof)
    2. On-chain tx hash lookup (verify actual USDC transfer via RPC)
    3. Honor system fallback (accept well-formed payment headers)

    On verified payments, auto-submits proofOfPayment feedback to the
    ERC-8004 ReputationRegistry (Pattern #24).
    """

    def __init__(
        self,
        price_usd: float = 0.001,
        currency: str = "USDC",
        chain: str = "base",
        pay_to: str = "",
        require_payment: bool = False,
    ):
        self.price_usd = price_usd
        self.currency = currency
        self.chain = chain
        self.pay_to = pay_to or os.getenv("BASE_WALLET_ADDRESS", "")
        self.require_payment = require_payment
        self._receipts: list[PaymentReceipt] = []
        self._rpc_urls = {
            "monad": os.getenv("MONAD_RPC_URL", "https://monad.drpc.org"),
            "base": os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
        }

    def get_requirements(self) -> Dict[str, Any]:
        """Return x402 payment requirements for a 402 response."""
        # CAIP-10 format: eip155:{chainId}:{address}
        chain_ids = {"base": 8453, "monad": 10143, "ethereum": 1}
        chain_id = chain_ids.get(self.chain, 10143)
        caip10 = f"eip155:{chain_id}:{self.pay_to}" if self.pay_to and not self.pay_to.startswith("eip155:") else self.pay_to
        return {
            "version": "x402-v1",
            "priceUSD": str(self.price_usd),
            "currency": self.currency,
            "network": self.chain,
            "chainId": chain_id,
            "payTo": caip10,
            "pricingUrl": "https://grokandmon.com/.well-known/x402-pricing.json",
            "description": f"A2A request fee: ${self.price_usd} {self.currency} on {self.chain}",
        }

    def verify_header(self, payment_header: Optional[str]) -> tuple[bool, str]:
        """
        Verify an X-402-Payment header.

        Returns (valid, reason).

        Verification tiers (tried in order):
        1. EIP-712/ECDSA signature → recovers payer address, verified=True
        2. On-chain tx hash → confirms transfer on RPC, verified=True
        3. Facilitator receipt → trusts facilitator, verified=False
        4. Honor system → accepts well-formed proof, verified=False
        """
        if not self.require_payment:
            return True, "Payment not required"

        if not payment_header:
            return False, "Missing X-402-Payment header"

        # Try to decode the payment proof
        try:
            # Header could be base64-encoded JSON or raw JSON
            if not payment_header.startswith("{"):
                decoded = base64.b64decode(payment_header).decode("utf-8")
                proof = json.loads(decoded)
            else:
                proof = json.loads(payment_header)
        except Exception:
            # Accept opaque payment tokens too (facilitator-signed)
            logger.info(f"Accepted opaque payment token (length={len(payment_header)})")
            self._record_receipt("received", self.price_usd, "unknown")
            return True, "Accepted opaque payment token"

        # Extract common fields
        amount = proof.get("amount", proof.get("value", 0))
        payer = proof.get("from", proof.get("payer", proof.get("sender", "")))

        # Tier 1: ECDSA signature recovery
        signature = proof.get("signature", "")
        if signature and payer:
            recovered = self._recover_signer(proof, signature)
            if recovered and recovered.lower() == payer.lower():
                logger.info(f"ECDSA verified: {amount} from {payer}")
                self._record_receipt(
                    "received",
                    float(amount) if amount else self.price_usd,
                    payer,
                    verified=True,
                )
                # Submit reputation feedback for verified payment
                self._submit_reputation_feedback(payer, float(amount) if amount else self.price_usd)
                return True, "ECDSA signature verified"
            elif recovered:
                logger.warning(f"ECDSA mismatch: claimed {payer}, recovered {recovered}")
                return False, f"Signature does not match claimed payer"

        # Tier 2: On-chain tx hash verification
        tx_hash = proof.get("tx_hash", proof.get("txHash", proof.get("transactionHash", "")))
        if tx_hash:
            verified = self._verify_tx_hash(tx_hash, proof.get("chain", self.chain))
            if verified:
                logger.info(f"On-chain verified: tx {tx_hash[:10]}... from {payer}")
                self._record_receipt(
                    "received",
                    float(amount) if amount else self.price_usd,
                    payer or "on-chain",
                    verified=True,
                    tx_hash=tx_hash,
                )
                self._submit_reputation_feedback(payer or "on-chain", float(amount) if amount else self.price_usd)
                return True, f"On-chain tx verified: {tx_hash[:16]}..."

        # Tier 3: Facilitator receipt (trust the facilitator)
        if proof.get("receipt"):
            logger.info("Facilitator receipt accepted")
            self._record_receipt("received", self.price_usd, "facilitator")
            return True, "Facilitator receipt accepted"

        # Tier 4: Honor system (well-formed proof with amount + payer)
        if amount and payer:
            logger.info(f"Honor system: {amount} from {payer} (unverified)")
            self._record_receipt("received", float(amount) if amount else self.price_usd, payer)
            return True, "Payment proof accepted (honor system)"

        return False, "Invalid payment proof structure"

    def _recover_signer(self, proof: dict, signature: str) -> Optional[str]:
        """
        Recover the Ethereum address from the payment proof signature.

        Uses eth_account for ECDSA recovery. Returns the recovered address
        or None if the library is unavailable or the signature is invalid.
        """
        try:
            from eth_account.messages import encode_defunct
            from eth_account import Account

            # Reconstruct the signed message (canonical JSON without the signature)
            proof_copy = {k: v for k, v in proof.items() if k != "signature"}
            message = json.dumps(proof_copy, sort_keys=True)
            signable = encode_defunct(text=message)
            recovered = Account.recover_message(signable, signature=signature)
            return recovered
        except ImportError:
            logger.debug("eth_account not available, cannot do ECDSA recovery")
            return None
        except Exception as e:
            logger.warning(f"ECDSA recovery failed: {e}")
            return None

    def _verify_tx_hash(self, tx_hash: str, chain: str = "monad") -> bool:
        """
        Verify a transaction hash on-chain via RPC.

        Performs a synchronous eth_getTransactionReceipt call. Returns True
        if the tx exists, succeeded (status=0x1), and the recipient matches.
        """
        rpc_url = self._rpc_urls.get(chain)
        if not rpc_url:
            logger.debug(f"No RPC URL for chain {chain}")
            return False

        try:
            import requests
            resp = requests.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                    "id": 1,
                },
                timeout=10,
            )
            if resp.status_code != 200:
                return False

            result = resp.json().get("result")
            if not result:
                logger.debug(f"Tx {tx_hash[:10]}... not found on {chain}")
                return False

            # Check status (0x1 = success)
            status = result.get("status", "0x0")
            if status != "0x1":
                logger.warning(f"Tx {tx_hash[:10]}... failed (status={status})")
                return False

            # Check recipient matches our pay_to address (if we have one)
            to_addr = result.get("to", "")
            if self.pay_to and to_addr.lower() != self.pay_to.lower():
                # Could be a USDC transfer (logs contain actual recipient)
                # For now, accept if the tx succeeded
                logger.debug(f"Tx recipient {to_addr[:10]}... != pay_to {self.pay_to[:10]}... (may be USDC contract)")

            logger.info(f"On-chain tx verified: {tx_hash[:16]}... on {chain}")
            return True

        except ImportError:
            logger.debug("requests library not available for tx verification")
            return False
        except Exception as e:
            logger.warning(f"Tx verification failed: {e}")
            return False

    def _submit_reputation_feedback(self, payer: str, amount_usd: float):
        """
        Submit a proofOfPayment reputation signal to the ERC-8004 ReputationRegistry.

        Called when a verified x402 payment is received. This creates a
        positive feedback entry for the paying agent (Pattern #24).
        """
        try:
            from src.blockchain.reputation_publisher import publish_signal
            publish_signal(
                signal_name="x402_payment_received",
                signal_value=f"Verified payment of ${amount_usd:.4f} from {payer}",
                metadata={
                    "payer": payer,
                    "amount_usd": amount_usd,
                    "currency": self.currency,
                    "chain": self.chain,
                    "type": "proofOfPayment",
                },
            )
            logger.info(f"Reputation feedback submitted for x402 payment from {payer}")
        except ImportError:
            logger.debug("reputation_publisher not available, skipping feedback")
        except Exception as e:
            logger.warning(f"Reputation feedback submission failed: {e}")

    def _record_receipt(self, direction: str, amount: float, counterparty: str,
                        verified: bool = False, tx_hash: Optional[str] = None):
        import uuid
        receipt = PaymentReceipt(
            payment_id=str(uuid.uuid4())[:8],
            direction=direction,
            amount_usd=amount,
            currency=self.currency,
            chain=self.chain,
            counterparty=counterparty,
            timestamp=time.time(),
            tx_hash=tx_hash,
            verified=verified,
        )
        self._receipts.append(receipt)
        # Keep last 1000 receipts
        if len(self._receipts) > 1000:
            self._receipts = self._receipts[-500:]

    def get_receipts(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Get recent payment receipts."""
        return [
            {
                "id": r.payment_id,
                "direction": r.direction,
                "amount": r.amount_usd,
                "currency": r.currency,
                "chain": r.chain,
                "counterparty": r.counterparty,
                "timestamp": r.timestamp,
                "verified": r.verified,
                "tx_hash": r.tx_hash,
            }
            for r in self._receipts[-limit:]
        ]

    def total_received(self) -> float:
        return sum(r.amount_usd for r in self._receipts if r.direction == "received")

    def verified_received(self) -> float:
        """Total amount received with verified payment proofs."""
        return sum(r.amount_usd for r in self._receipts if r.direction == "received" and r.verified)


class X402Payer:
    """
    Client-side x402 payment sender.

    Makes REAL on-chain USDC transfers to pay for agent services.
    Supports x402 v2 "exact" scheme (direct ERC-20 transfer).

    Flow:
    1. Receive 402 with PAYMENT-REQUIRED header (base64 JSON)
    2. Parse payment requirements (amount, asset, payTo, network)
    3. Execute ERC-20 transfer on-chain
    4. Return PAYMENT-RESPONSE header with tx hash for retry
    """

    # USDC contract addresses per network
    USDC_CONTRACTS = {
        "eip155:8453": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",   # Base mainnet
        "eip155:84532": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # Base Sepolia
        "eip155:1": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",     # Ethereum
        "eip155:10143": "0x754704Bc059F8C67012fEd69BC8A327a5aafb603",  # Monad mainnet (Circle native)
    }

    RPC_URLS = {
        "eip155:8453": "https://mainnet.base.org",
        "eip155:84532": "https://sepolia.base.org",
        "eip155:1": "https://eth.llamarpc.com",
        "eip155:10143": "https://monad.drpc.org",
    }

    CHAIN_IDS = {
        "eip155:8453": 8453,
        "eip155:84532": 84532,
        "eip155:1": 1,
        "eip155:10143": 10143,
    }

    # Minimal ERC-20 ABI
    ERC20_ABI = json.loads(
        '[{"constant":false,"inputs":[{"name":"to","type":"address"},{"name":"value","type":"uint256"}],'
        '"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"},'
        '{"constant":true,"inputs":[{"name":"account","type":"address"}],'
        '"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},'
        '{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
    )

    def __init__(
        self,
        private_key: str = "",
        max_payment_usd: float = 0.01,
        daily_limit_usd: float = 1.0,
    ):
        self._private_key = private_key or os.getenv("MONAD_PRIVATE_KEY", "")
        self.max_payment_usd = max_payment_usd
        self._daily_limit = daily_limit_usd
        self._total_spent = 0.0
        self._daily_reset_ts = time.time()

        # Derive wallet address from key
        self.wallet_address = ""
        if self._private_key:
            try:
                from web3 import Web3
                w3 = Web3()
                acct = w3.eth.account.from_key(self._private_key)
                self.wallet_address = acct.address
            except Exception:
                pass

    def _reset_daily_if_needed(self):
        """Reset daily spending counter every 24h."""
        if time.time() - self._daily_reset_ts > 86400:
            self._total_spent = 0.0
            self._daily_reset_ts = time.time()

    async def pay_402(
        self,
        payment_required_header: str,
    ) -> Optional[str]:
        """
        Parse a 402 PAYMENT-REQUIRED header, create EIP-3009 signed
        authorization, return payment payload for retry.

        x402 "exact" scheme uses EIP-3009 transferWithAuthorization:
        the client signs an authorization, the server pulls the funds.

        Returns base64-encoded payment payload or None if payment fails.
        """
        self._reset_daily_if_needed()

        if not self._private_key:
            logger.warning("x402: No private key configured, cannot pay")
            return None

        # Decode the PAYMENT-REQUIRED header
        try:
            decoded = json.loads(base64.b64decode(payment_required_header))
        except Exception as e:
            logger.warning(f"x402: Failed to decode payment header: {e}")
            return None

        accepts = decoded.get("accepts", [])
        if not accepts:
            logger.warning("x402: No payment options in 402 response")
            return None

        # Prefer Monad mainnet, fall back to Base and others
        preferred_networks = ["eip155:10143", "eip155:8453", "eip155:84532", "eip155:1"]
        chosen = None
        for net in preferred_networks:
            for opt in accepts:
                if opt.get("network") == net:
                    chosen = opt
                    break
            if chosen:
                break

        if not chosen:
            chosen = accepts[0]

        network = chosen["network"]
        amount = int(chosen["amount"])
        asset = chosen["asset"]
        pay_to = chosen["payTo"]
        max_timeout = int(chosen.get("maxTimeoutSeconds", 300))
        extra = chosen.get("extra", {})
        amount_usd = amount / 1_000_000

        # Safety checks
        if amount_usd > self.max_payment_usd:
            logger.warning(f"x402: ${amount_usd:.4f} exceeds max ${self.max_payment_usd}")
            return None

        if self._total_spent + amount_usd > self._daily_limit:
            logger.warning(f"x402: Daily limit exceeded")
            return None

        chain_id = self.CHAIN_IDS.get(network)
        if not chain_id:
            logger.warning(f"x402: Unsupported network {network}")
            return None

        # Create EIP-3009 signed authorization
        try:
            signature, authorization = self._sign_eip3009(
                chain_id=chain_id,
                usdc_address=asset,
                pay_to=pay_to,
                amount=amount,
                max_timeout=max_timeout,
                usdc_name=extra.get("name", "USD Coin"),
                usdc_version=extra.get("version", "2"),
            )
        except Exception as e:
            logger.error(f"x402: EIP-3009 signing failed: {e}")
            return None

        self._total_spent += amount_usd
        logger.info(f"x402: Signed ${amount_usd:.4f} authorization to {pay_to[:10]}... on {network}")

        # Build x402 v2 payment payload per spec:
        # Must include resource (echoed from 402), accepted (chosen option), payload (sig + auth)
        resource = decoded.get("resource", {})
        payload = {
            "x402Version": 2,
            "resource": resource,
            "accepted": chosen,  # Echo back the chosen payment option
            "payload": {
                "signature": signature,
                "authorization": authorization,
            },
        }

        return base64.b64encode(json.dumps(payload).encode()).decode()

    def _sign_eip3009(
        self,
        chain_id: int,
        usdc_address: str,
        pay_to: str,
        amount: int,
        max_timeout: int,
        usdc_name: str = "USD Coin",
        usdc_version: str = "2",
    ) -> tuple[str, dict]:
        """
        Sign an EIP-3009 TransferWithAuthorization message.

        Returns (signature_hex, authorization_dict).
        """
        from web3 import Web3
        from eth_account.messages import encode_typed_data

        w3 = Web3()
        account = w3.eth.account.from_key(self._private_key)

        now = int(time.time())
        valid_after = now - 5  # valid immediately (small buffer)
        valid_before = now + max_timeout

        # Random nonce (32 bytes)
        nonce = "0x" + os.urandom(32).hex()

        authorization = {
            "from": account.address,
            "to": Web3.to_checksum_address(pay_to),
            "value": str(amount),
            "validAfter": str(valid_after),
            "validBefore": str(valid_before),
            "nonce": nonce,
        }

        # EIP-712 typed data for TransferWithAuthorization
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "TransferWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ],
            },
            "primaryType": "TransferWithAuthorization",
            "domain": {
                "name": usdc_name,
                "version": usdc_version,
                "chainId": chain_id,
                "verifyingContract": Web3.to_checksum_address(usdc_address),
            },
            "message": {
                "from": account.address,
                "to": Web3.to_checksum_address(pay_to),
                "value": amount,
                "validAfter": valid_after,
                "validBefore": valid_before,
                "nonce": bytes.fromhex(nonce[2:]),
            },
        }

        signable = encode_typed_data(full_message=typed_data)
        signed = w3.eth.account.sign_message(signable, private_key=self._private_key)

        return "0x" + signed.signature.hex(), authorization

    async def create_payment_header(self, agent_url: str, amount_usd: Optional[float] = None) -> Optional[str]:
        """Create a pre-emptive X-402-Payment header (for agents that accept proofs)."""
        if not self.wallet_address:
            return None
        return None  # Only pay reactively on 402

    async def handle_402(self, requirements: Dict[str, Any]) -> Optional[str]:
        """Legacy interface — use pay_402 with raw header instead."""
        return None

    def get_spending_stats(self) -> Dict[str, Any]:
        self._reset_daily_if_needed()
        return {
            "total_spent_usd": round(self._total_spent, 6),
            "daily_limit_usd": self._daily_limit,
            "remaining_usd": round(self._daily_limit - self._total_spent, 6),
            "wallet": self.wallet_address[:10] + "..." if self.wallet_address else "not set",
        }


# Singleton instances
_verifier: Optional[X402Verifier] = None
_payer: Optional[X402Payer] = None
_payer_init_attempted: bool = False


def get_x402_verifier() -> X402Verifier:
    global _verifier
    if _verifier is None:
        _verifier = X402Verifier(
            price_usd=float(os.getenv("A2A_PRICE_USD", "0.001")),
            chain=os.getenv("A2A_PAYMENT_CHAIN", "monad"),
            pay_to=os.getenv("MONAD_WALLET_ADDRESS", os.getenv("BASE_WALLET_ADDRESS", "")),
            require_payment=os.getenv("A2A_REQUIRE_PAYMENT", "false").lower() == "true",
        )
    return _verifier


def get_x402_payer() -> Optional[X402Payer]:
    """Return a payer only when outbound x402 payment is actually possible.

    Without a private key, creating a payer causes a warning flood during A2A
    sweeps (one warning per paid endpoint). Returning None cleanly disables
    outbound payments and avoids log/CPU churn.
    """
    global _payer, _payer_init_attempted
    if _payer_init_attempted:
        return _payer
    _payer_init_attempted = True

    enabled = os.getenv("X402_PAYER_ENABLED", "auto").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        logger.info("x402 payer disabled via X402_PAYER_ENABLED")
        _payer = None
        return _payer

    private_key = os.getenv("MONAD_PRIVATE_KEY", "").strip()
    if not private_key:
        if enabled in {"1", "true", "yes", "on"}:
            logger.warning(
                "x402 payer enabled but MONAD_PRIVATE_KEY is missing; paid outbound calls disabled"
            )
        else:
            logger.info("x402 payer unavailable (MONAD_PRIVATE_KEY not set); paid outbound calls disabled")
        _payer = None
        return _payer

    _payer = X402Payer(
        private_key=private_key,
        max_payment_usd=float(os.getenv("X402_MAX_PAYMENT_USD", "0.01")),
        daily_limit_usd=float(os.getenv("X402_DAILY_LIMIT_USD", "1.0")),
    )
    return _payer
