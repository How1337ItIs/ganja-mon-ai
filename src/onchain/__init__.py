"""
On-Chain GrowRing Integration
==============================

Daily 1-of-1 NFT minting pipeline for the GrowRing system.

Modules:
    - ipfs: Pin images and metadata to IPFS via Pinata
    - art: Generate AI artwork via Nano Banana Pro 3
    - growring: Mint GrowRing NFTs on Monad
    - marketplace: Auto-list NFTs (Magic Eden + Dutch auction)
    - promote: Social media promotion engine
    - daily_mint: Daily mint orchestrator (the main loop)

Usage:
    from src.onchain.daily_mint import DailyMintPipeline

    pipeline = DailyMintPipeline()
    result = await pipeline.run()
"""

from .growring import mint_growring, get_growring_data, MILESTONE_TYPES, RARITY_NAMES
from .ipfs import pin_image, pin_metadata
from .art import generate_daily_art
from .marketplace import auto_list_after_mint
from .ganja_payments import GanjaPaymentProcessor, get_ganja_pricing, GANJA_ART_PRICING

__all__ = [
    "mint_growring",
    "get_growring_data",
    "pin_image",
    "pin_metadata",
    "generate_daily_art",
    "auto_list_after_mint",
    "MILESTONE_TYPES",
    "RARITY_NAMES",
    "GanjaPaymentProcessor",
    "get_ganja_pricing",
    "GANJA_ART_PRICING",
]
