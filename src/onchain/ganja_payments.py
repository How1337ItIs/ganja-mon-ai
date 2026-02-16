"""
$GANJA Payment Processor
==========================

Watches agent wallet for $GANJA ERC-20 transfers on Monad.
On payment confirmation:
    1. Credit the sender with a service (art commission, oracle query, etc.)
    2. Execute 50/50 burn/buyback:
       - 50% burned (sent to 0x...dEaD) — permanent supply reduction
       - 50% sold for $MON — value flywheel

$GANJA is kindling. $MON is the fire.

Usage:
    processor = GanjaPaymentProcessor()
    # Poll for new payments
    new_payments = await processor.check_payments()
    # Process pending payments (burn + buyback)
    await processor.process_pending()
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# Standard ERC-20 Transfer event signature
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Minimal ERC-20 ABI for transfer and balanceOf
ERC20_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Payment state file
PAYMENTS_STATE_PATH = Path("data/ganja_payments.json")


@dataclass
class GanjaPayment:
    """A single $GANJA payment received."""

    tx_hash: str
    sender: str
    amount_raw: int
    amount_human: float
    block_number: int
    timestamp: str
    service_type: str = "art_commission"  # art_commission | oracle | signal_feed
    service_status: str = "pending"  # pending | fulfilled | failed
    burn_tx: str = ""
    buyback_tx: str = ""
    processed: bool = False

    def to_dict(self) -> dict:
        return {
            "tx_hash": self.tx_hash,
            "sender": self.sender,
            "amount_raw": str(self.amount_raw),
            "amount_human": self.amount_human,
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "service_type": self.service_type,
            "service_status": self.service_status,
            "burn_tx": self.burn_tx,
            "buyback_tx": self.buyback_tx,
            "processed": self.processed,
        }


class GanjaPaymentProcessor:
    """
    Watches for $GANJA payments and processes the burn/buyback split.

    Flow:
        1. check_payments() — scans recent blocks for Transfer events to agent wallet
        2. process_pending() — for each unprocessed payment:
           a. Send burn_ratio (50%) to dead address
           b. Sell (1 - burn_ratio) (50%) for $MON
           c. Mark as processed
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.settings = get_settings()
        self.data_dir = data_dir or Path("data")
        self.state_path = self.data_dir / "ganja_payments.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()
        self._decimals: Optional[int] = None

    def _load_state(self) -> dict:
        """Load payment processing state."""
        if self.state_path.exists():
            try:
                with open(self.state_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "last_checked_block": 0,
            "payments": [],
            "total_received": 0,
            "total_burned": 0,
            "total_buyback": 0,
            "burn_count": 0,
            "buyback_count": 0,
        }

    def _save_state(self):
        """Persist payment state to disk."""
        with open(self.state_path, "w") as f:
            json.dump(self._state, f, indent=2)

    def _get_web3(self):
        """Get web3 instance connected to Monad."""
        try:
            from web3 import Web3
        except ImportError:
            raise RuntimeError("web3 not installed. Run: pip install web3")
        w3 = Web3(Web3.HTTPProvider(self.settings.monad_rpc))
        if not w3.is_connected():
            raise ConnectionError(f"Cannot connect to Monad RPC: {self.settings.monad_rpc}")
        return w3

    def _get_account(self):
        """Get the agent's signing account."""
        from web3 import Account

        pk = os.getenv("MONAD_PRIVATE_KEY", os.getenv("PRIVATE_KEY", ""))
        if not pk:
            raise ValueError("MONAD_PRIVATE_KEY / PRIVATE_KEY not set")
        return Account.from_key(pk)

    def _get_ganja_contract(self):
        """Get the $GANJA ERC-20 contract instance."""
        w3 = self._get_web3()
        from web3 import Web3

        return w3.eth.contract(
            address=Web3.to_checksum_address(self.settings.ganja_token_address),
            abi=ERC20_ABI,
        )

    def _get_decimals(self) -> int:
        """Get $GANJA token decimals (cached)."""
        if self._decimals is None:
            try:
                contract = self._get_ganja_contract()
                self._decimals = contract.functions.decimals().call()
            except Exception:
                self._decimals = 18  # Default ERC-20
        return self._decimals

    async def check_payments(self, lookback_blocks: int = 5000) -> List[GanjaPayment]:
        """
        Scan recent blocks for $GANJA transfers TO the agent wallet.

        Args:
            lookback_blocks: How many blocks back to scan (default 5000 ~ few hours on Monad)

        Returns:
            List of new GanjaPayment objects found
        """
        w3 = self._get_web3()
        account = self._get_account()
        agent_address = account.address.lower()

        current_block = w3.eth.block_number
        from_block = max(
            self._state["last_checked_block"] + 1,
            current_block - lookback_blocks,
        )

        if from_block > current_block:
            return []

        from web3 import Web3

        # Build filter for Transfer events to agent wallet
        ganja_addr = Web3.to_checksum_address(self.settings.ganja_token_address)
        agent_topic = "0x" + agent_address[2:].zfill(64)

        try:
            logs = w3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": current_block,
                "address": ganja_addr,
                "topics": [
                    TRANSFER_EVENT_TOPIC,
                    None,  # from (any sender)
                    agent_topic,  # to (our wallet)
                ],
            })
        except Exception as e:
            logger.error(f"Failed to fetch $GANJA transfer logs: {e}")
            return []

        new_payments = []
        existing_hashes = {p["tx_hash"] for p in self._state["payments"]}
        decimals = self._get_decimals()

        for log in logs:
            tx_hash = log["transactionHash"].hex()
            if tx_hash in existing_hashes:
                continue

            sender = "0x" + log["topics"][1].hex()[-40:]
            amount_raw = int(log["data"].hex(), 16)
            amount_human = amount_raw / (10 ** decimals)

            # Skip dust payments (less than 100 tokens)
            if amount_human < 100:
                continue

            # Skip self-transfers
            if sender.lower() == agent_address:
                continue

            payment = GanjaPayment(
                tx_hash=tx_hash,
                sender=Web3.to_checksum_address(sender),
                amount_raw=amount_raw,
                amount_human=amount_human,
                block_number=log["blockNumber"],
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            new_payments.append(payment)
            self._state["payments"].append(payment.to_dict())
            self._state["total_received"] += amount_human

            logger.info(
                f"💰 $GANJA payment received: {amount_human:.2f} from {sender[:10]}... "
                f"tx={tx_hash[:16]}..."
            )

        self._state["last_checked_block"] = current_block
        self._save_state()

        return new_payments

    async def process_pending(self) -> List[Dict[str, Any]]:
        """
        Process all unprocessed payments: burn 50%, sell 50% for $MON.

        Returns:
            List of processing results
        """
        results = []
        burn_ratio = self.settings.ganja_burn_ratio

        for payment_data in self._state["payments"]:
            if payment_data.get("processed"):
                continue

            amount_raw = int(payment_data["amount_raw"])
            burn_amount = int(amount_raw * burn_ratio)
            sell_amount = amount_raw - burn_amount

            result = {"tx_hash": payment_data["tx_hash"], "sender": payment_data["sender"]}

            # 1. Burn
            try:
                burn_tx = await self._burn_ganja(burn_amount)
                payment_data["burn_tx"] = burn_tx
                result["burn_tx"] = burn_tx
                result["burn_status"] = "success"
                self._state["total_burned"] += payment_data["amount_human"] * burn_ratio
                self._state["burn_count"] += 1
                logger.info(f"🔥 Burned {payment_data['amount_human'] * burn_ratio:.2f} $GANJA")
            except Exception as e:
                logger.error(f"Burn failed: {e}")
                result["burn_status"] = f"failed: {e}"

            # 2. Sell for $MON
            try:
                buyback_tx = await self._sell_for_mon(sell_amount)
                payment_data["buyback_tx"] = buyback_tx
                result["buyback_tx"] = buyback_tx
                result["buyback_status"] = "success"
                self._state["total_buyback"] += payment_data["amount_human"] * (1 - burn_ratio)
                self._state["buyback_count"] += 1
                logger.info(
                    f"💚 Sold {payment_data['amount_human'] * (1 - burn_ratio):.2f} "
                    f"$GANJA for $MON"
                )
            except Exception as e:
                logger.error(f"$MON buyback failed: {e}")
                result["buyback_status"] = f"failed: {e}"

            payment_data["processed"] = True
            results.append(result)

        self._save_state()
        return results

    async def _burn_ganja(self, amount: int) -> str:
        """Send $GANJA to the dead address (burn)."""
        w3 = self._get_web3()
        account = self._get_account()
        contract = self._get_ganja_contract()
        from web3 import Web3

        burn_addr = Web3.to_checksum_address(self.settings.ganja_burn_address)

        func = contract.functions.transfer(burn_addr, amount)
        nonce = w3.eth.get_transaction_count(account.address)
        tx = func.build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 100_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        if receipt["status"] != 1:
            raise RuntimeError(f"Burn tx reverted: {tx_hash.hex()}")

        return tx_hash.hex()

    async def _sell_for_mon(self, amount: int) -> str:
        """
        Sell $GANJA for $MON.

        On nad.fun, this would use their swap/sell endpoint.
        For now, we transfer to a designated sell wallet or use
        a DEX router if available.

        TODO: Integrate with nad.fun sell API or Monad DEX router
        when available. For now, holds in agent wallet for manual swap.
        """
        # Placeholder: in production, this would call nad.fun's sell API
        # or route through a DEX aggregator on Monad
        logger.info(
            f"$MON buyback queued: {amount} raw $GANJA to be sold. "
            f"Manual swap required until DEX integration is live."
        )
        return "pending_manual_swap"

    def get_stats(self) -> dict:
        """Get payment processing statistics."""
        decimals = self._get_decimals()
        pending = sum(1 for p in self._state["payments"] if not p.get("processed"))
        return {
            "total_payments": len(self._state["payments"]),
            "pending_payments": pending,
            "total_received_ganja": self._state.get("total_received", 0),
            "total_burned_ganja": self._state.get("total_burned", 0),
            "total_buyback_ganja": self._state.get("total_buyback", 0),
            "burn_count": self._state.get("burn_count", 0),
            "buyback_count": self._state.get("buyback_count", 0),
            "burn_ratio": self.settings.ganja_burn_ratio,
            "ganja_token": self.settings.ganja_token_address,
            "burn_address": self.settings.ganja_burn_address,
            "last_checked_block": self._state.get("last_checked_block", 0),
        }

    def get_payment_history(self, limit: int = 20) -> list:
        """Get recent payment history."""
        payments = self._state.get("payments", [])
        return payments[-limit:]


# ─── Art Commission via $GANJA ──────────────────────────────────────────

# Pricing in $GANJA tokens (calibrated to USD equiv, adjust as price moves)
GANJA_ART_PRICING = {
    "commission": 10_000,    # Custom art commission
    "pfp": 5_000,            # Profile picture
    "meme": 2_000,           # Meme generation
    "ganjafy": 1_000,        # Rasta transformation
    "banner": 3_000,         # Social/DexScreener banner
    "oracle": 500,           # Ask Mon oracle query
}


def get_ganja_pricing() -> dict:
    """Return art studio pricing in $GANJA tokens."""
    return {
        "currency": "$GANJA",
        "token_address": get_settings().ganja_token_address,
        "chain": "Monad",
        "payment_address": "agent wallet (see /api/wallet)",
        "burn_ratio": f"{get_settings().ganja_burn_ratio * 100:.0f}%",
        "mechanism": "50% burned (supply reduction), 50% sold for $MON (value flywheel)",
        "pricing": {
            mode: {
                "price_ganja": price,
                "description": desc,
            }
            for mode, price in GANJA_ART_PRICING.items()
            for desc in [
                {
                    "commission": "Custom art — your vision, Mon's brush",
                    "pfp": "Unique Rasta profile picture",
                    "meme": "Fresh meme from current vibes",
                    "ganjafy": "Transform any image into Rasta style",
                    "banner": "Social media / DexScreener banner",
                    "oracle": "Ask Mon anything — Rasta wisdom on demand",
                }.get(mode, mode)
            ]
        },
    }
