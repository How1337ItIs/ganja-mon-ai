#!/usr/bin/env python3
"""
Kasa Plug LED Blinker
Tries to blink the LED indicator on each plug in a pattern.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    from kasa import Discover

    plugs = {
        "Plug 1": os.environ.get("KASA_PLUG_1_IP", "192.168.125.181"),
        "Plug 2": os.environ.get("KASA_PLUG_2_IP", "192.168.125.129"),
        "Plug 3": os.environ.get("KASA_PLUG_3_IP", "192.168.125.203"),
        "Plug 4": os.environ.get("KASA_PLUG_4_IP", "192.168.125.133"),
    }

    print("\n" + "=" * 50)
    print("KASA PLUG LED BLINKER")
    print("=" * 50)

    for name, ip in plugs.items():
        print(f"\n[*] Checking {name} ({ip})...")

        try:
            device = await Discover.discover_single(ip)
            await device.update()

            print(f"    Model: {device.model}")
            print(f"    Alias: {device.alias}")
            print(f"    Is on: {device.is_on}")

            # Check for LED control
            if hasattr(device, 'led'):
                print(f"    LED state: {device.led}")

                # Blink pattern: number of blinks = plug number
                plug_num = int(name.split()[1])
                print(f"    Blinking LED {plug_num} times...")

                for i in range(plug_num):
                    await device.set_led(False)  # LED off
                    await asyncio.sleep(0.3)
                    await device.set_led(True)   # LED on
                    await asyncio.sleep(0.3)

                print(f"    Done! {name} blinked {plug_num} times")
            else:
                print("    No LED control available")

            # Show all features
            if hasattr(device, 'features'):
                print(f"    Features: {list(device.features.keys())}")

        except Exception as e:
            print(f"    ERROR: {e}")

        await asyncio.sleep(2)

    print("\n" + "=" * 50)
    print("Plug 1 = 1 blink, Plug 2 = 2 blinks, etc.")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
