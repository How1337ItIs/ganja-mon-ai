#!/usr/bin/env python3
"""
Daily Grow Advancement & Archival
==================================

Runs daily at midnight to:
1. Advance grow day counter
2. Archive daily snapshot
3. Archive logs
4. (Optional) Preserve data on-chain

Cron: 0 0 * * * (midnight daily)
"""

import asyncio
import os
import sys
import httpx
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
ARCHIVE_DIR = PROJECT_ROOT / "archive"
PHOTOS_DIR = ARCHIVE_DIR / "photos"
LOGS_DIR = ARCHIVE_DIR / "logs"
DATA_DIR = ARCHIVE_DIR / "data"

# API
API_URL = os.environ.get("API_URL", "http://localhost:8000")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "k6azjF-VLXaaPjyEadEWsPzlIw22Ldaf9OIcqK5cD4E")


async def get_admin_token():
    """Get JWT token for admin access"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/auth/token",
            data={"username": "admin", "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"Auth failed: {response.status_code}")


async def advance_day(token: str):
    """Advance the grow day counter"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/grow/advance-day",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Advanced to Day {data['current_day']}")
            return data['current_day']
        else:
            print(f"✗ Day advance failed: {response.status_code}")
            return None


async def archive_daily_snapshot(day: int):
    """Capture and archive daily snapshot"""
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_path = PHOTOS_DIR / f"day_{day:03d}_{datetime.now().strftime('%Y%m%d')}.jpg"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/api/webcam/latest")
        if response.status_code == 200:
            with open(snapshot_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Archived snapshot: {snapshot_path.name}")
            return snapshot_path
        else:
            print(f"✗ Snapshot failed: {response.status_code}")
            return None


async def archive_sensor_data(day: int):
    """Archive sensor data for the day"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    data_path = DATA_DIR / f"day_{day:03d}_sensors.json"

    async with httpx.AsyncClient() as client:
        # Get last 24 hours of data
        response = await client.get(f"{API_URL}/api/sensors/history?hours=24")
        if response.status_code == 200:
            with open(data_path, 'w') as f:
                f.write(response.text)
            print(f"✓ Archived sensor data: {data_path.name}")
            return data_path
        else:
            print(f"✗ Data archive failed: {response.status_code}")
            return None


async def archive_ai_decisions(day: int):
    """Archive AI decisions"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    ai_path = DATA_DIR / f"day_{day:03d}_ai.json"

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/api/ai/latest")
        if response.status_code == 200:
            with open(ai_path, 'w') as f:
                f.write(response.text)
            print(f"✓ Archived AI decision: {ai_path.name}")
            return ai_path
        else:
            print(f"✗ AI archive failed: {response.status_code}")
            return None


async def preserve_onchain(day: int):
    """
    Preserve daily summary on Monad blockchain (optional).

    Stores IPFS hash on-chain for permanent record.
    Requires: web3, ipfs client
    """
    try:
        # TODO: Implement IPFS upload
        # TODO: Implement Monad contract interaction
        print(f"⏸ On-chain preservation not yet implemented (coming soon)")
        return None
    except Exception as e:
        print(f"✗ On-chain preservation failed: {e}")
        return None


async def main():
    """Run daily advancement and archival"""
    print(f"\n{'='*60}")
    print(f"Daily Advancement - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    try:
        # Get auth
        print("[*] Authenticating...")
        token = await get_admin_token()

        # Advance day
        print("[*] Advancing grow day...")
        new_day = await advance_day(token)

        if new_day:
            # Archive snapshot
            print(f"[*] Archiving Day {new_day - 1} data...")
            await archive_daily_snapshot(new_day - 1)
            await archive_sensor_data(new_day - 1)
            await archive_ai_decisions(new_day - 1)

            # On-chain preservation (optional)
            if os.environ.get("ENABLE_ONCHAIN", "false").lower() == "true":
                await preserve_onchain(new_day - 1)

        print(f"\n✓ Daily advancement complete!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ Daily advancement failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
