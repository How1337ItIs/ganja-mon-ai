#!/usr/bin/env python3
"""Emergency light off script - turn off grow light via Tapo plug"""
import asyncio
import os
import sys
from pathlib import Path

# Load env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hardware.tapo import TapoActuatorHub

async def main():
    hub = TapoActuatorHub()
    ok = await hub.connect()
    print(f"Connected: {ok}")
    if ok:
        result = await hub.set_device("grow_light", False)
        print(f"Light OFF: {result}")
    else:
        print("FAILED to connect to Tapo!")

asyncio.run(main())
