#!/usr/bin/env python3
"""
Test Govee sensor integration.
Run with: python scripts/test_govee.py

Requires GOVEE_API_KEY in .env or environment.
Get your key from: https://developer.govee.com/
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")


async def main():
    api_key = os.environ.get("GOVEE_API_KEY")

    if not api_key:
        print("ERROR: GOVEE_API_KEY not set")
        print("\nTo get your API key:")
        print("1. Open Govee Home app")
        print("2. Go to Settings → About Us → Apply for API Key")
        print("3. Add to .env file: GOVEE_API_KEY=your-key-here")
        print("\nOr register at: https://developer.govee.com/")
        return

    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")

    try:
        from hardware.govee import GoveeSensorHub, discover_govee_sensors

        # Discover all sensors
        print("\n=== Discovering Govee Sensors ===")
        sensors = await discover_govee_sensors(api_key)

        if not sensors:
            print("No Govee temperature sensors found on your account.")
            print("Make sure your H5179 sensors are set up in the Govee Home app.")
            return

        print(f"Found {len(sensors)} sensor(s):\n")
        for s in sensors:
            print(f"  Device: {s.get('deviceName', 'Unknown')}")
            print(f"    ID: {s.get('device')}")
            print(f"    Model: {s.get('model')}")
            print(f"    Retrievable: {s.get('retrievable', 'N/A')}")
            print()

        # Read from first sensor
        print("=== Reading from Sensor ===")
        hub = GoveeSensorHub(api_key=api_key)
        if await hub.connect():
            reading = await hub.read_all()
            print(f"\nTemperature: {reading.air_temp:.1f}°C ({reading.air_temp * 9/5 + 32:.1f}°F)")
            print(f"Humidity: {reading.humidity:.1f}%")
            print(f"VPD: {reading.vpd:.2f} kPa")
            print(f"Timestamp: {reading.timestamp}")
            await hub.disconnect()
        else:
            print("Failed to connect to sensor")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Run: pip install httpx")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
