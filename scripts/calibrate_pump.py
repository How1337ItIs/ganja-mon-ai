#!/usr/bin/env python3
"""
Water Pump Calibration
======================

Runs pump for exactly 10 seconds to measure flow rate.

Usage:
    1. Put pump hose in measuring cup
    2. Run: python scripts/calibrate_pump.py
    3. Measure water in cup
    4. Update PUMP_RATE_ML_PER_SEC in src/hardware/kasa.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hardware.kasa import KasaActuatorHub


async def calibrate():
    """Run pump for 10 seconds"""
    print("\n" + "="*60)
    print("WATER PUMP CALIBRATION")
    print("="*60)
    print("\nMake sure:")
    print("  1. Pump hose is in a measuring cup")
    print("  2. You're ready to measure the water")
    print("")
    input("Press ENTER when ready to start...")

    # Get pump IP from environment
    pump_ip = os.environ.get("KASA_WATER_PUMP_IP", "192.168.125.129")

    kasa = KasaActuatorHub({"water_pump": pump_ip})

    print(f"\n[*] Connecting to pump at {pump_ip}...")
    connected = await kasa.connect()

    if not connected:
        print("[!] Failed to connect to pump!")
        print(f"    Check IP: {pump_ip}")
        print("    Check plug is online")
        return

    print("[OK] Pump connected!")
    print("\n" + "="*60)
    print("STARTING PUMP FOR 10 SECONDS")
    print("="*60)
    print("")

    try:
        # Turn pump ON
        print("[*] Pump ON...")
        await kasa.set_device("water_pump", True)

        # Run for exactly 10 seconds
        for i in range(10, 0, -1):
            print(f"    {i} seconds remaining...")
            await asyncio.sleep(1)

        # Turn pump OFF
        await kasa.set_device("water_pump", False)
        print("[*] Pump OFF")

    except Exception as e:
        # Safety: ensure pump is off
        await kasa.set_device("water_pump", False)
        print(f"[!] Error: {e}")
        return

    print("\n" + "="*60)
    print("CALIBRATION COMPLETE")
    print("="*60)
    print("\nMeasure the water in your cup:")
    ml = input("How many ml? ")

    if ml:
        try:
            ml_float = float(ml)
            rate = ml_float / 10.0
            print(f"\n[RESULT]")
            print(f"  Water dispensed: {ml_float}ml in 10 seconds")
            print(f"  Flow rate: {rate:.1f} ml/second")
            print(f"\nUpdate src/hardware/kasa.py line 181:")
            print(f"  PUMP_RATE_ML_PER_SEC = {rate:.1f}")
            print("")
        except ValueError:
            print("[!] Invalid number")


if __name__ == "__main__":
    try:
        asyncio.run(calibrate())
    except KeyboardInterrupt:
        print("\n[!] Calibration cancelled")
