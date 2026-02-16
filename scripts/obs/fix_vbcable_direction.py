#!/usr/bin/env python3
"""Fix OBS to capture VB-Cable OUTPUT not INPUT"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Fixing VB-Cable direction (OUTPUT not INPUT)...")

try:
    # Desktop Audio should be "CABLE Output" (what rasta plays TO)
    ws.call(obs_requests.SetInputSettings(
        inputName="Desktop Audio",
        inputSettings={
            "device_id": "CABLE Output (VB-Audio Virtual Cable)"  # OUTPUT side
        },
        overlay=True
    ))

    print("[OK] Desktop Audio set to 'CABLE Output' (correct!)")
    print("\nRasta plays audio TO VB-Cable")
    print("OBS captures FROM VB-Cable Output")
    print("\nNow OBS Desktop Audio should move when rasta talks!")

except Exception as e:
    print(f"[ERROR] {e}")

ws.disconnect()
