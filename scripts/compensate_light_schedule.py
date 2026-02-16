#!/usr/bin/env python3
"""
One-time light schedule compensation
Turns lights OFF at 3:30 AM (instead of midnight) to compensate for missed morning hours
"""
import asyncio
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from src.hardware.tapo import TapoActuatorHub


async def main():
    # Connect to grow light
    hub = TapoActuatorHub(
        device_ips={'grow_light': os.getenv('TAPO_GROW_LIGHT_IP', '192.168.125.208')},
        username=os.getenv('TAPO_USERNAME'),
        password=os.getenv('TAPO_PASSWORD')
    )
    await hub.connect()
    print(f"✅ Connected to grow light")

    # Calculate time to lights off (3:30 AM)
    now = datetime.now()
    lights_off_time = now.replace(hour=3, minute=30, second=0, microsecond=0)

    # If it's past 3:30 AM, target tomorrow
    if lights_off_time <= now:
        lights_off_time += timedelta(days=1)

    wait_seconds = (lights_off_time - now).total_seconds()

    print(f"📅 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌙 Lights will turn OFF at: {lights_off_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏳ Waiting {wait_seconds/3600:.1f} hours...")

    # Wait until lights off time
    await asyncio.sleep(wait_seconds)

    # Turn lights OFF
    print(f"🌙 Turning lights OFF (compensated schedule)")
    await hub.set_device('grow_light', False)
    print(f"✅ Lights OFF - plant will get 18 hours total today")
    print(f"📝 Normal 18/6 schedule resumes at 6:00 AM")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
