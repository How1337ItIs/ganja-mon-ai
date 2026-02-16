#!/usr/bin/env python3
"""
Tapo P115 Connection Test
=========================

Tests connection to your Tapo smart plug.
Run: python test_tapo.py

Make sure to set TAPO_PASSWORD in .env first!
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_tapo():
    try:
        from tapo import ApiClient
    except ImportError:
        print("ERROR: tapo package not installed")
        print("Run: pip install tapo")
        return False

    username = os.getenv("TAPO_USERNAME")
    password = os.getenv("TAPO_PASSWORD")
    ip = os.getenv("TAPO_GROW_LIGHT_IP")

    print(f"Testing Tapo P115 connection...")
    print(f"  Username: {username}")
    print(f"  IP: {ip}")
    print(f"  Password: {'*' * len(password) if password else 'NOT SET!'}")
    print()

    if not password or password == "YOUR_TAPO_PASSWORD_HERE":
        print("ERROR: Please set your Tapo password in .env file!")
        print("Edit: /mnt/c/Users/natha/sol-cannabis/.env")
        print("Change: TAPO_PASSWORD=YOUR_TAPO_PASSWORD_HERE")
        print("To:     TAPO_PASSWORD=your-actual-password")
        return False

    try:
        print("Connecting to Tapo API...")
        client = ApiClient(username, password)

        print(f"Connecting to device at {ip}...")
        device = await client.p110(ip)  # P115 uses same API as P110

        print("Getting device info...")
        info = await device.get_device_info()

        print()
        print("=" * 50)
        print("SUCCESS! Connected to Tapo P115")
        print("=" * 50)
        print(f"  Device: {info.model}")
        print(f"  Nickname: {info.nickname}")
        print(f"  Status: {'ON' if info.device_on else 'OFF'}")
        print(f"  Signal: {info.signal_level}%")
        print()

        # Get energy usage (P115 feature!)
        print("Getting energy usage...")
        energy = await device.get_energy_usage()
        print(f"  Current Power: {energy.current_power / 1000:.1f}W")
        print(f"  Today's Usage: {energy.today_energy}Wh")
        print(f"  Today's Runtime: {energy.today_runtime} minutes")
        print()

        # Test toggle
        print("Testing toggle (will turn ON then OFF)...")

        if not info.device_on:
            print("  Turning ON...")
            await device.on()
            await asyncio.sleep(2)
            print("  Turning OFF...")
            await device.off()
        else:
            print("  Turning OFF...")
            await device.off()
            await asyncio.sleep(2)
            print("  Turning ON...")
            await device.on()

        print()
        print("All tests passed! Your Tapo P115 is ready for Grok & Mon.")
        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"ERROR: {type(e).__name__}")
        print("=" * 50)
        print(f"  {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check that the IP address is correct")
        print("  2. Make sure the plug is on the same network")
        print("  3. Verify 'Third-Party Compatibility' is ON in Tapo app")
        print("  4. Check username/password are correct")
        print("  5. Try toggling 'Third-Party Compatibility' off and on")
        return False


if __name__ == "__main__":
    asyncio.run(test_tapo())
