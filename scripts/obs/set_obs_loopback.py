#!/usr/bin/env python3
"""Set OBS to capture VB-Cable Input as LOOPBACK"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Trying different VB-Cable configurations...")

# Try all possible VB-Cable device names
vb_cable_names = [
    "CABLE Input (VB-Audio Virtual Cable)",
    "CABLE Output (VB-Audio Virtual Cable)",
    "VB-Audio Virtual Cable",
    "CABLE-A Output (VB-Audio Cable A)",
    "CABLE-A Input (VB-Audio Cable A)"
]

for device_name in vb_cable_names:
    try:
        print(f"\n[*] Trying: {device_name}")
        ws.call(obs_requests.SetInputSettings(
            inputName="Desktop Audio",
            inputSettings={"device_id": device_name},
            overlay=True
        ))
        print(f"[OK] Set to: {device_name}")
        print("\nTalk now and watch Desktop Audio meter in OBS!")
        print("If it moves, this is the right one!")
        break
    except Exception as e:
        print(f"[SKIP] Failed: {e}")

print("\n[*] Current setting:")
settings = ws.call(obs_requests.GetInputSettings(inputName="Desktop Audio"))
print(f"Desktop Audio: {settings.getInputSettings()}")

ws.disconnect()
