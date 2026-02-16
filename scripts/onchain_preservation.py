#!/usr/bin/env python3
"""
On-Chain Data Preservation
===========================

Preserves grow data on Monad blockchain via IPFS.

Process:
1. Package daily data (sensors, AI, photo)
2. Upload to IPFS (get hash)
3. Store IPFS hash on Monad contract
4. Verify on-chain

This lets you say: "Our entire grow is permanently preserved on Monad blockchain"
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# Will implement when ready to deploy $MON contract
# Requirements:
# - IPFS node (ipfs.io or Pinata)
# - Monad contract deployed
# - Contract ABI
# - Wallet private key

class GrowDataPreserver:
    """Preserve grow data on-chain"""

    def __init__(self):
        self.ipfs_gateway = os.environ.get("IPFS_GATEWAY", "https://ipfs.io")
        self.monad_rpc = os.environ.get("MONAD_RPC_URL", "https://rpc.monad.xyz")
        self.contract_address = os.environ.get("GROW_CONTRACT_ADDRESS")
        self.private_key = os.environ.get("WALLET_PRIVATE_KEY")

    async def package_daily_data(self, day: int) -> dict:
        """Package all data for a day"""
        archive_dir = Path(__file__).parent.parent / "archive"

        data_package = {
            "day": day,
            "timestamp": datetime.now().isoformat(),
            "plant": "Mon",
            "strain": "Purple Milk",
            "photo": None,
            "sensors": None,
            "ai_decision": None,
        }

        # Load photo
        photo_path = archive_dir / "photos" / f"day_{day:03d}_*.jpg"
        photos = list(archive_dir.glob(f"photos/day_{day:03d}_*.jpg"))
        if photos:
            # Convert to base64 for IPFS
            import base64
            with open(photos[0], 'rb') as f:
                data_package["photo"] = base64.b64encode(f.read()).decode()

        # Load sensor data
        sensor_path = archive_dir / "data" / f"day_{day:03d}_sensors.json"
        if sensor_path.exists():
            with open(sensor_path) as f:
                data_package["sensors"] = json.load(f)

        # Load AI decision
        ai_path = archive_dir / "data" / f"day_{day:03d}_ai.json"
        if ai_path.exists():
            with open(ai_path) as f:
                data_package["ai_decision"] = json.load(f)

        return data_package

    async def upload_to_ipfs(self, data: dict) -> str:
        """Upload data package to IPFS, return hash"""
        # TODO: Implement IPFS upload via:
        # - Local IPFS node (ipfs add)
        # - Pinata API (pinata.cloud)
        # - NFT.storage (free, permanent)

        print("⏸ IPFS upload not yet implemented")
        return "QmPLACEHOLDER123456789"  # Placeholder hash

    async def store_on_monad(self, day: int, ipfs_hash: str):
        """Store IPFS hash on Monad contract"""
        # TODO: Implement web3 interaction:
        # - Connect to Monad RPC
        # - Call contract.storeGrowData(day, ipfs_hash)
        # - Wait for confirmation
        # - Return tx hash

        print("⏸ Monad contract interaction not yet implemented")
        return "0xPLACEHOLDER_TX_HASH"

    async def preserve_day(self, day: int):
        """Complete preservation flow"""
        print(f"\n[*] Preserving Day {day} on-chain...")

        # Package data
        data = await self.package_daily_data(day)
        print(f"  ✓ Packaged {len(str(data))} bytes")

        # Upload to IPFS
        ipfs_hash = await self.upload_to_ipfs(data)
        print(f"  ✓ IPFS: {ipfs_hash}")

        # Store on Monad
        tx_hash = await self.store_on_monad(day, ipfs_hash)
        print(f"  ✓ Monad TX: {tx_hash}")

        print(f"[✓] Day {day} preserved permanently!\n")
        return {"ipfs_hash": ipfs_hash, "tx_hash": tx_hash}


async def main():
    """Preserve latest completed day"""
    preserver = GrowDataPreserver()

    # Get current day, preserve previous
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{os.environ.get('API_URL', 'http://localhost:8000')}/api/grow/stage")
        current_day = response.json().get("current_day", 1)

    if current_day > 1:
        await preserver.preserve_day(current_day - 1)
    else:
        print("Still on Day 1, nothing to preserve yet")


if __name__ == "__main__":
    asyncio.run(main())
