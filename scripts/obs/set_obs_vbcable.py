#!/usr/bin/env python3
"""Configure OBS to use VB-Cable audio instead of mic"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Configuring OBS audio for VB-Cable (Rasta voice)...")

try:
    # Get current audio settings
    settings = ws.call(obs_requests.GetInputSettings(inputName="Desktop Audio"))
    print(f"[*] Current desktop audio: {settings.getInputSettings()}")

    # Set to VB-Cable
    ws.call(obs_requests.SetInputSettings(
        inputName="Desktop Audio",
        inputSettings={
            "device_id": "CABLE Output (VB-Audio Virtual Cable)"
        },
        overlay=True
    ))

    print("[OK] Desktop Audio set to VB-Cable!")
    print("\nOBS will now capture Rasta voice from VB-Cable!")
    print("When you talk -> Rasta voice -> VB-Cable -> OBS -> Stream")

except Exception as e:
    print(f"[ERROR] {e}")
    print("\nManual fix:")
    print("1. OBS -> Settings -> Audio")
    print("2. Desktop Audio: CABLE Output (VB-Audio Virtual Cable)")
    print("3. Mic/Auxiliary: (Disable)")
    print("4. Apply")

ws.disconnect()
