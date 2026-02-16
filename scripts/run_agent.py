#!/usr/bin/env python3
"""
Simple launcher for the Grok agent on Windows.
Handles the path setup needed for relative imports.
"""
import sys
import os
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add src to path BEFORE any imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now we can import and run
import asyncio

# Change brain/agent.py relative imports to work
# by running from within the brain package context
from brain.agent import GrokAndMonAgent

async def main():
    # Enable hardware mode to use webcam, Kasa plugs, etc.
    use_hardware = "--mock" not in sys.argv

    # Build Kasa IPs from environment
    kasa_ips = {}
    if os.environ.get("KASA_PLUG_1_IP"):
        kasa_ips["plug_1"] = os.environ.get("KASA_PLUG_1_IP")
    if os.environ.get("KASA_PLUG_2_IP"):
        kasa_ips["plug_2"] = os.environ.get("KASA_PLUG_2_IP")
    if os.environ.get("KASA_PLUG_3_IP"):
        kasa_ips["plug_3"] = os.environ.get("KASA_PLUG_3_IP")
    if os.environ.get("KASA_PLUG_4_IP"):
        kasa_ips["plug_4"] = os.environ.get("KASA_PLUG_4_IP")

    agent = GrokAndMonAgent(
        use_hardware=use_hardware,
        kasa_ips=kasa_ips if kasa_ips else None
    )
    if "--once" in sys.argv:
        await agent.run_decision_cycle()
    else:
        await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
