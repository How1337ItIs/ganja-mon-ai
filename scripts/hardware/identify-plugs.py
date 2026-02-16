#!/usr/bin/env python3
"""
Kasa Plug Identifier
Cycles through each plug one at a time so you can see which device it controls.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    from kasa import Discover, SmartPlug

    plugs = {
        "Plug 1": os.environ.get("KASA_PLUG_1_IP", "192.168.125.181"),
        "Plug 2": os.environ.get("KASA_PLUG_2_IP", "192.168.125.129"),
        "Plug 3": os.environ.get("KASA_PLUG_3_IP", "192.168.125.203"),
        "Plug 4": os.environ.get("KASA_PLUG_4_IP", "192.168.125.133"),
    }

    # Add plug 5 if configured
    plug5 = os.environ.get("KASA_PLUG_5_IP")
    if plug5:
        plugs["Plug 5"] = plug5

    print("\n" + "=" * 50)
    print("KASA PLUG IDENTIFIER")
    print("=" * 50)
    print("\nThis will turn each plug ON for 5 seconds.")
    print("Watch your devices to identify which is which!\n")

    # First turn all OFF
    print("[*] Turning all plugs OFF first...\n")
    for name, ip in plugs.items():
        try:
            plug = SmartPlug(ip)
            await plug.update()
            await plug.turn_off()
            print(f"    {name} ({ip}): OFF")
        except Exception as e:
            print(f"    {name} ({ip}): ERROR - {e}")

    await asyncio.sleep(2)

    # Cycle through each plug
    for name, ip in plugs.items():
        print(f"\n{'='*50}")
        print(f">>> {name} ({ip}) - TURNING ON NOW <<<")
        print(f"{'='*50}")
        print("    Watch for which device turns on!")

        try:
            plug = SmartPlug(ip)
            await plug.update()
            await plug.turn_on()

            # Countdown
            for i in range(5, 0, -1):
                print(f"    {i}...", end=" ", flush=True)
                await asyncio.sleep(1)
            print()

            await plug.turn_off()
            print(f"    {name}: OFF\n")

        except Exception as e:
            print(f"    ERROR: {e}\n")

        await asyncio.sleep(1)

    print("\n" + "=" * 50)
    print("IDENTIFICATION COMPLETE")
    print("=" * 50)
    print("\nNote which plug controls which device:")
    print("  Plug 1 -> grow_light")
    print("  Plug 2 -> exhaust_fan")
    print("  Plug 3 -> circulation_fan")
    print("  Plug 4 -> water_pump (CAREFUL!)")
    print("  Plug 5 -> co2_solenoid")
    print("\nUpdate the mapping in .env if needed.\n")

if __name__ == "__main__":
    asyncio.run(main())
