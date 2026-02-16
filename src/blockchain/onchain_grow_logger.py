"""
On-Chain Grow Action Logger
============================

Logs plant care actions to the Monad blockchain for immutable verification.
Each grow action (watering, lighting, etc.) gets hashed and recorded on-chain.

This provides cryptographic proof of all AI cultivation decisions.

Integration:
- Hooks into existing DeviceAuditLog from transparency.py
- Sends minimal transactions with action hash in data field
- Batches actions to reduce gas costs (configurable)
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

# Monad configuration
MONAD_RPC_URL = os.getenv("MONAD_RPC_URL", "https://rpc.monad.xyz")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", os.getenv("MONAD_PRIVATE_KEY", ""))
ENABLE_ONCHAIN_LOGGING = os.getenv("ENABLE_ONCHAIN_LOGGING", "true").lower() == "true"

# Batch configuration
BATCH_SIZE = int(os.getenv("ONCHAIN_BATCH_SIZE", "10"))  # Actions per tx
BATCH_TIMEOUT_SECONDS = int(os.getenv("ONCHAIN_BATCH_TIMEOUT", "300"))  # 5 min

# Log file for tracking on-chain submissions
ONCHAIN_LOG_PATH = Path("data/onchain_grow_log.jsonl")


@dataclass
class GrowActionRecord:
    """A grow action to be logged on-chain"""
    timestamp: str
    action_type: str  # watering, lighting, exhaust, heating, humidity, stage_change
    device: str
    old_state: str
    new_state: str
    triggered_by: str
    reason: str

    def to_hash(self) -> str:
        """Generate deterministic hash of this action"""
        data = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)


class OnchainGrowLogger:
    """
    Logs grow actions to Monad blockchain.

    Actions are batched for efficiency:
    - Collect actions until batch size or timeout
    - Hash all actions together (Merkle-style)
    - Submit single tx with root hash
    - Keep local record of all action hashes
    """

    def __init__(self):
        self.enabled = ENABLE_ONCHAIN_LOGGING and bool(PRIVATE_KEY)
        self.pending_actions: List[GrowActionRecord] = []
        self.last_batch_time = datetime.now()

        if self.enabled:
            try:
                self.w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL))
                self.account = Account.from_key(PRIVATE_KEY)
                self.address = self.account.address
                logger.info(f"On-chain grow logger initialized: {self.address}")
            except Exception as e:
                logger.error(f"Failed to initialize on-chain logger: {e}")
                self.enabled = False
        else:
            logger.info("On-chain grow logging disabled (no private key or disabled)")
            self.w3 = None
            self.account = None
            self.address = None

        # Ensure log directory exists
        ONCHAIN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def record_action(
        self,
        action_type: str,
        device: str,
        old_state: str,
        new_state: str,
        triggered_by: str = "grok_decision",
        reason: str = ""
    ) -> Optional[str]:
        """
        Record a grow action for on-chain logging.

        Returns the action hash.
        """
        action = GrowActionRecord(
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            device=device,
            old_state=old_state,
            new_state=new_state,
            triggered_by=triggered_by,
            reason=reason
        )

        action_hash = action.to_hash()

        # Log locally
        self._log_local(action, action_hash)

        # Add to pending batch
        if self.enabled:
            self.pending_actions.append(action)

            # Check if we should submit batch
            should_submit = (
                len(self.pending_actions) >= BATCH_SIZE or
                (datetime.now() - self.last_batch_time).seconds >= BATCH_TIMEOUT_SECONDS
            )

            if should_submit:
                asyncio.create_task(self._submit_batch())

        return action_hash

    def _log_local(self, action: GrowActionRecord, action_hash: str):
        """Log action to local file"""
        entry = {
            **action.to_dict(),
            "action_hash": action_hash,
            "onchain_status": "pending" if self.enabled else "disabled"
        }

        with open(ONCHAIN_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def _submit_batch(self):
        """Submit pending actions as a batch to Monad"""
        if not self.enabled or not self.pending_actions:
            return

        try:
            # Create batch root hash
            action_hashes = [a.to_hash() for a in self.pending_actions]
            batch_data = json.dumps({
                "type": "grokmon_grow_batch",
                "count": len(action_hashes),
                "hashes": action_hashes,
                "timestamp": datetime.now().isoformat()
            }, sort_keys=True)
            batch_root = hashlib.sha256(batch_data.encode()).hexdigest()

            # Create and send transaction
            tx_hash = await self._send_onchain_log(batch_root, len(action_hashes))

            if tx_hash:
                logger.info(
                    f"[ONCHAIN] Logged {len(action_hashes)} grow actions | "
                    f"Root: {batch_root[:16]}... | TX: {tx_hash}"
                )

                # Update local log with tx hash
                self._update_local_log(action_hashes, tx_hash, batch_root)

            # Clear pending
            self.pending_actions = []
            self.last_batch_time = datetime.now()

        except Exception as e:
            logger.error(f"Failed to submit on-chain batch: {e}")

    async def _send_onchain_log(self, batch_root: str, action_count: int) -> Optional[str]:
        """Send a transaction to Monad with the batch root hash"""
        if not self.w3 or not self.account:
            return None

        try:
            # Prepare data payload
            data_payload = f"GROKMON_GROW:{batch_root}:{action_count}"
            data_hex = "0x" + data_payload.encode().hex()

            # Get nonce and gas price
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = self.w3.eth.gas_price

            # Build transaction (minimal value, just data)
            tx = {
                "nonce": nonce,
                "to": self.address,  # Send to self (data-only tx)
                "value": 0,
                "gas": 30000,  # Minimal gas for data tx
                "gasPrice": int(gas_price * 1.1),  # 10% buffer
                "data": data_hex,
                "chainId": 143  # Monad chain ID
            }

            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            return tx_hash.hex()

        except Exception as e:
            logger.error(f"On-chain tx failed: {e}")
            return None

    def _update_local_log(self, action_hashes: List[str], tx_hash: str, batch_root: str):
        """Update local log entries with on-chain tx info"""
        # Read existing entries
        if not ONCHAIN_LOG_PATH.exists():
            return

        entries = []
        with open(ONCHAIN_LOG_PATH, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("action_hash") in action_hashes:
                        entry["onchain_status"] = "confirmed"
                        entry["tx_hash"] = tx_hash
                        entry["batch_root"] = batch_root
                    entries.append(entry)
                except:
                    pass

        # Write back
        with open(ONCHAIN_LOG_PATH, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    async def force_submit(self):
        """Force submit any pending actions immediately"""
        if self.pending_actions:
            await self._submit_batch()

    def get_recent_logs(self, count: int = 20) -> List[dict]:
        """Get recent on-chain log entries"""
        if not ONCHAIN_LOG_PATH.exists():
            return []

        entries = []
        with open(ONCHAIN_LOG_PATH, "r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except:
                    pass

        return entries[-count:]


# Global instance
_logger_instance: Optional[OnchainGrowLogger] = None


def get_onchain_logger() -> OnchainGrowLogger:
    """Get or create the global on-chain logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = OnchainGrowLogger()
    return _logger_instance


def log_grow_action(
    action_type: str,
    device: str,
    old_state: str,
    new_state: str,
    triggered_by: str = "grok_decision",
    reason: str = ""
) -> Optional[str]:
    """
    Convenience function to log a grow action on-chain.

    Returns the action hash.

    Example:
        log_grow_action(
            action_type="watering",
            device="water_pump",
            old_state="off",
            new_state="on:250ml",
            triggered_by="grok_decision",
            reason="Soil moisture at 35%, below 40% threshold"
        )
    """
    return get_onchain_logger().record_action(
        action_type=action_type,
        device=device,
        old_state=old_state,
        new_state=new_state,
        triggered_by=triggered_by,
        reason=reason
    )


# Action type constants for consistency
class GrowActionTypes:
    WATERING = "watering"
    LIGHTING = "lighting"
    EXHAUST = "exhaust"
    INTAKE = "intake"
    HEATING = "heating"
    HUMIDITY = "humidity"
    STAGE_CHANGE = "stage_change"
    OBSERVATION = "observation"
    SENSOR_READ = "sensor_read"
