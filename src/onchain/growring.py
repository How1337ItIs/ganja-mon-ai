"""
GrowRing Minting — Monad On-Chain
===================================

Mints GrowRing ERC-721 NFTs on Monad via the GrowRing contract.
Uses web3.py for transaction construction and signing.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.core.config import get_settings

logger = logging.getLogger(__name__)

# ─── Constants ──────────────────────────────────────────────────────────

MILESTONE_TYPES = {
    "daily_journal": 0,
    "germination": 1,
    "transplant": 2,
    "veg_start": 3,
    "flower_start": 4,
    "first_pistils": 5,
    "flush": 6,
    "cure_start": 7,
    "harvest": 8,
    "topping": 9,
    "first_node": 10,
    "trichomes": 11,
    "anomaly": 12,
}

RARITY_NAMES = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Legendary"}

# ABI for GrowRing.mintDaily function
GROWRING_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenId", "type": "uint256"},
            {"indexed": False, "name": "milestoneType", "type": "uint8"},
            {"indexed": False, "name": "rarity", "type": "uint8"},
            {"indexed": False, "name": "dayNumber", "type": "uint16"},
            {"indexed": False, "name": "imageURI", "type": "string"},
        ],
        "name": "MilestoneMinted",
        "type": "event",
    },
    {
        "inputs": [
            {"name": "_type", "type": "uint8"},
            {"name": "_dayNumber", "type": "uint16"},
            {"name": "_imageURI", "type": "string"},
            {"name": "_rawImageURI", "type": "string"},
            {"name": "_artStyle", "type": "string"},
            {"name": "_narrative", "type": "string"},
            {"name": "_temperature", "type": "uint16"},
            {"name": "_humidity", "type": "uint16"},
            {"name": "_vpd", "type": "uint16"},
            {"name": "_healthScore", "type": "uint8"},
        ],
        "name": "mintDaily",
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "milestones",
        "outputs": [
            {"name": "milestoneType", "type": "uint8"},
            {"name": "rarity", "type": "uint8"},
            {"name": "dayNumber", "type": "uint16"},
            {"name": "temperature", "type": "uint16"},
            {"name": "humidity", "type": "uint16"},
            {"name": "vpd", "type": "uint16"},
            {"name": "healthScore", "type": "uint8"},
            {"name": "growCycleId", "type": "uint8"},
            {"name": "imageURI", "type": "string"},
            {"name": "rawImageURI", "type": "string"},
            {"name": "artStyle", "type": "string"},
            {"name": "narrative", "type": "string"},
            {"name": "timestamp", "type": "uint48"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "nextTokenId",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _get_web3():
    """Get a web3 instance connected to Monad."""
    try:
        from web3 import Web3
    except ImportError:
        raise RuntimeError("web3 not installed. Run: pip install web3")

    settings = get_settings()
    rpc = settings.monad_rpc
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to Monad RPC: {rpc}")
    return w3


def _get_account():
    """Get the agent's account from the private key."""
    from web3 import Account

    settings = get_settings()
    pk = settings.private_key or os.getenv("MONAD_PRIVATE_KEY", "")
    if not pk:
        raise ValueError("PRIVATE_KEY not set in .env")
    return Account.from_key(pk)


def _get_contract():
    """Get the GrowRing contract instance."""
    w3 = _get_web3()
    settings = get_settings()
    address = settings.growring_address or os.getenv("GROWRING_ADDRESS", "")
    if not address:
        raise ValueError("GROWRING_ADDRESS not set in .env")

    from web3 import Web3

    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=GROWRING_ABI)


async def mint_growring(
    milestone_type: str,
    day_number: int,
    image_uri: str,
    raw_image_uri: str,
    art_style: str,
    narrative: str,
    temperature: float = 75.0,
    humidity: float = 60.0,
    vpd: float = 1.0,
    health_score: int = 80,
    **kwargs,
) -> dict:
    """Mint a daily GrowRing NFT on Monad.

    Args:
        milestone_type: String key (e.g., "daily_journal", "harvest")
        day_number: Day in the grow cycle (1-indexed)
        image_uri: IPFS URI for the AI-generated art
        raw_image_uri: IPFS URI for the raw webcam photo
        art_style: Style name (e.g., "neon_noir")
        narrative: Rasta-voiced journal entry
        temperature: Temperature in °F
        humidity: Humidity percentage
        vpd: VPD in kPa
        health_score: 0-100 health assessment

    Returns:
        Dict with token_id, tx_hash, rarity, etc.
    """
    w3 = _get_web3()
    account = _get_account()
    contract = _get_contract()

    type_id = MILESTONE_TYPES.get(milestone_type, 0)

    # Scale values for on-chain storage
    temp_scaled = int(temperature * 100)
    humidity_scaled = int(humidity * 100)
    vpd_scaled = int(vpd * 1000)

    # Build transaction
    func = contract.functions.mintDaily(
        type_id,
        day_number,
        image_uri,
        raw_image_uri,
        art_style,
        narrative,
        temp_scaled,
        humidity_scaled,
        vpd_scaled,
        health_score,
    )

    nonce = w3.eth.get_transaction_count(account.address)
    tx = func.build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "gas": 1_000_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }
    )

    # Sign and send
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    # Parse token ID from logs (MilestoneMinted event)
    token_id = _parse_token_id(receipt)

    # Determine rarity from milestone type
    rarity = _compute_rarity(type_id)

    result = {
        "token_id": token_id,
        "tx_hash": tx_hash.hex(),
        "rarity": rarity,
        "rarity_name": RARITY_NAMES.get(rarity, "Unknown"),
        "milestone_type": milestone_type,
        "day_number": day_number,
        "image_uri": image_uri,
        "raw_image_uri": raw_image_uri,
        "art_style": art_style,
        "gas_used": receipt.get("gasUsed", 0),
        "block_number": receipt.get("blockNumber", 0),
    }

    logger.info(
        f"🌿 GrowRing #{token_id} minted (Day {day_number}, {RARITY_NAMES[rarity]}) "
        f"tx={tx_hash.hex()[:16]}... gas={receipt.get('gasUsed', 0)}"
    )

    return result


def _parse_token_id(receipt) -> int:
    """Parse the token ID from the MilestoneMinted event in transaction receipt.

    IMPORTANT: The receipt contains multiple events (Transfer, MilestoneMinted).
    We must match on the MilestoneMinted event signature to avoid reading the
    Transfer event's `from` field (address(0) = 0) as the token ID.
    """
    # keccak256("MilestoneMinted(uint256,uint8,uint8,uint16,string)")
    MILESTONE_MINTED_SIG = "0x"  # Will match by topic count as fallback

    # MilestoneMinted has 2 topics: [event_sig, tokenId]
    # Transfer has 4 topics: [event_sig, from, to, tokenId]
    # We want MilestoneMinted (exactly 2 topics) or Transfer's topics[3]
    for log in receipt.get("logs", []):
        topics = log.get("topics", [])
        # MilestoneMinted: exactly 2 topics (sig + indexed tokenId)
        if len(topics) == 2:
            try:
                return int(topics[1].hex(), 16)
            except (ValueError, AttributeError):
                continue
        # ERC-721 Transfer(from, to, tokenId): 4 topics, tokenId is topics[3]
        if len(topics) == 4:
            try:
                return int(topics[3].hex(), 16)
            except (ValueError, AttributeError):
                continue
    # Fallback: read next token ID from contract
    logger.warning("Could not parse token ID from logs, reading from contract")
    contract = _get_contract()
    return contract.functions.nextTokenId().call() - 1


def _compute_rarity(type_id: int) -> int:
    """Mirror the on-chain rarity computation in Python."""
    if type_id == 8:  # Harvest
        return 3  # Legendary
    if type_id == 0:  # DailyJournal
        return 0  # Common
    if type_id in (1, 2, 3, 4, 5, 6, 7):  # Germination through CureStart
        return 2  # Rare
    return 1  # Uncommon


async def get_growring_data(token_id: int) -> dict:
    """Read GrowRing milestone data from the contract."""
    contract = _get_contract()
    data = contract.functions.milestones(token_id).call()
    return {
        "milestone_type": data[0],
        "rarity": data[1],
        "day_number": data[2],
        "temperature": data[3] / 100,
        "humidity": data[4] / 100,
        "vpd": data[5] / 1000,
        "health_score": data[6],
        "grow_cycle_id": data[7],
        "image_uri": data[8],
        "raw_image_uri": data[9],
        "art_style": data[10],
        "narrative": data[11],
        "timestamp": data[12],
    }
