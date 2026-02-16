#!/usr/bin/env python3
"""Test Govee API and list all devices"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

async def main():
    api_key = os.environ.get("GOVEE_API_KEY")

    if not api_key:
        print("ERROR: GOVEE_API_KEY not set")
        return

    print(f"Using API key: {api_key[:8]}...")
    print("\nQuerying Govee API...")

    import httpx

    async with httpx.AsyncClient(
        headers={"Govee-API-Key": api_key},
        timeout=30.0,
    ) as client:
        response = await client.get("https://developer-api.govee.com/v1/devices")

        print(f"\nHTTP Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nRaw API Response:\n{data}\n")

            devices = data.get("data", {}).get("devices", [])
            print(f"Found {len(devices)} device(s):\n")

            for d in devices:
                print(f"  Name: {d.get('deviceName', 'N/A')}")
                print(f"  Model: {d.get('model', 'N/A')}")
                print(f"  Device ID: {d.get('device', 'N/A')}")
                print(f"  Controllable: {d.get('controllable', 'N/A')}")
                print(f"  Retrievable: {d.get('retrievable', 'N/A')}")
                print(f"  Commands: {d.get('supportCmds', [])}")
                print()
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(main())
