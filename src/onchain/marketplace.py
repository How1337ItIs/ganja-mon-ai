"""
Marketplace Auto-Listing
=========================

After minting a GrowRing, automatically list it for sale:
- COMMON/UNCOMMON → Magic Eden fixed price listing
- RARE/LEGENDARY → Custom Dutch auction via GrowAuction.sol

Magic Eden auto-indexes any ERC-721 on Monad, so our NFTs
appear there automatically. For programmatic listings, we use
their API when available, or approve + list via our auction contract.
"""

import json
import logging
import os
from typing import Optional
from decimal import Decimal

from src.core.config import get_settings

logger = logging.getLogger(__name__)


# ─── Pricing Strategy ──────────────────────────────────────────────────

LISTING_STRATEGIES = {
    "Common": {
        "type": "fixed_price",
        "price_mon": 0.05,
        "marketplace": "magic_eden",
    },
    "Uncommon": {
        "type": "fixed_price",
        "price_mon": 0.2,
        "marketplace": "magic_eden",
    },
    "Rare": {
        "type": "dutch_auction",
        "start_price_mon": 1.0,
        "end_price_mon": 0.1,
        "duration_hours": 24,
    },
    "Legendary": {
        "type": "dutch_auction",
        "start_price_mon": 5.0,
        "end_price_mon": 0.5,
        "duration_hours": 48,
    },
}


# GrowAuction ABI (minimal — just createAuction)
AUCTION_ABI = [
    {
        "inputs": [
            {"name": "_tokenId", "type": "uint256"},
            {"name": "_startPrice", "type": "uint128"},
            {"name": "_endPrice", "type": "uint128"},
            {"name": "_duration", "type": "uint48"},
        ],
        "name": "createAuction",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "_tokenId", "type": "uint256"}],
        "name": "getCurrentPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getActiveAuctions",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# GrowRing approve ABI
APPROVE_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

RARITY_NAMES = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Legendary"}


async def auto_list_after_mint(
    token_id: int,
    rarity: int,
    milestone_type: str,
) -> dict:
    """Auto-list a freshly minted GrowRing based on rarity.

    Args:
        token_id: The minted token ID
        rarity: Rarity level (0=Common, 1=Uncommon, 2=Rare, 3=Legendary)
        milestone_type: The milestone type string

    Returns:
        Dict with listing details
    """
    rarity_name = RARITY_NAMES.get(rarity, "Common")
    strategy = LISTING_STRATEGIES[rarity_name]

    logger.info(
        f"📋 Auto-listing GrowRing #{token_id} ({rarity_name}) "
        f"via {strategy['type']}"
    )

    if strategy["type"] == "dutch_auction":
        return await _create_dutch_auction(token_id, strategy, rarity_name)
    else:
        return await _list_magic_eden(token_id, strategy, rarity_name)


async def _create_dutch_auction(
    token_id: int, strategy: dict, rarity_name: str
) -> dict:
    """Create a Dutch auction for a RARE or LEGENDARY GrowRing.

    1. Approve the GrowAuction contract to transfer the NFT
    2. Call createAuction on the contract
    """
    from web3 import Web3, Account

    settings = get_settings()
    auction_address = os.getenv("GROW_AUCTION_ADDRESS", "")
    growring_address = os.getenv("GROWRING_ADDRESS", "")

    if not auction_address or not growring_address:
        logger.warning("Auction/GrowRing addresses not set, listing skipped")
        return {
            "listing_type": "dutch_auction",
            "status": "skipped",
            "reason": "contract addresses not configured",
        }

    w3 = Web3(Web3.HTTPProvider(settings.monad_rpc))
    pk = os.getenv("MONAD_PRIVATE_KEY", os.getenv("PRIVATE_KEY", ""))
    if not pk:
        logger.warning("MONAD_PRIVATE_KEY not set, listing skipped")
        return {
            "listing_type": "dutch_auction",
            "status": "skipped",
            "reason": "private key not configured",
        }
    account = Account.from_key(pk)

    # Calculate prices in wei (1 MON = 1e18 wei)
    start_price_wei = int(Decimal(str(strategy["start_price_mon"])) * Decimal("1e18"))
    end_price_wei = int(Decimal(str(strategy["end_price_mon"])) * Decimal("1e18"))
    duration_seconds = strategy["duration_hours"] * 3600

    # Step 1: Approve auction contract
    growring_contract = w3.eth.contract(
        address=Web3.to_checksum_address(growring_address), abi=APPROVE_ABI
    )
    approve_tx = growring_contract.functions.approve(
        Web3.to_checksum_address(auction_address), token_id
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }
    )
    signed_approve = account.sign_transaction(approve_tx)
    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    w3.eth.wait_for_transaction_receipt(approve_hash, timeout=30)

    # Step 2: Create auction
    auction_contract = w3.eth.contract(
        address=Web3.to_checksum_address(auction_address), abi=AUCTION_ABI
    )
    auction_tx = auction_contract.functions.createAuction(
        token_id, start_price_wei, end_price_wei, duration_seconds
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }
    )
    signed_auction = account.sign_transaction(auction_tx)
    auction_hash = w3.eth.send_raw_transaction(signed_auction.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(auction_hash, timeout=30)

    result = {
        "listing_type": "dutch_auction",
        "status": "listed",
        "token_id": token_id,
        "rarity": rarity_name,
        "start_price_mon": strategy["start_price_mon"],
        "end_price_mon": strategy["end_price_mon"],
        "duration_hours": strategy["duration_hours"],
        "auction_tx": auction_hash.hex(),
        "auction_url": f"https://grokandmon.com/auction/{token_id}",
    }

    logger.info(
        f"🔨 Dutch auction created for GrowRing #{token_id}: "
        f"{strategy['start_price_mon']}→{strategy['end_price_mon']} MON over "
        f"{strategy['duration_hours']}h | tx={auction_hash.hex()[:16]}..."
    )

    return result


async def _list_magic_eden(
    token_id: int, strategy: dict, rarity_name: str
) -> dict:
    """List a GrowRing on Magic Eden at a fixed price.

    Magic Eden auto-indexes all ERC-721 tokens on Monad. For programmatic
    listings, we'd use their API (requires API key). For now, we note
    the listing intent — the NFT will appear on ME automatically, and
    we can create listings manually or via their SDK when available.
    """
    growring_address = os.getenv("GROWRING_ADDRESS", "")

    result = {
        "listing_type": "fixed_price",
        "status": "indexed",
        "marketplace": "magic_eden",
        "token_id": token_id,
        "rarity": rarity_name,
        "price_mon": strategy["price_mon"],
        "collection_url": f"https://magiceden.io/collections/monad/{growring_address}",
        "token_url": (
            f"https://magiceden.io/item-details/monad/{growring_address}/{token_id}"
        ),
        "note": (
            "NFT auto-indexed on Magic Eden. Programmatic listing requires "
            "ME API key (application pending)."
        ),
    }

    logger.info(
        f"🏪 GrowRing #{token_id} ({rarity_name}) available on Magic Eden "
        f"at {strategy['price_mon']} MON"
    )

    return result
