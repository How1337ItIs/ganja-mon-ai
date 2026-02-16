#!/usr/bin/env python3
"""Check which audio device OBS is using"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Checking OBS audio device settings...\n")

try:
    desktop = ws.call(obs_requests.GetInputSettings(inputName="Desktop Audio"))
    print(f"Desktop Audio device: {desktop.getInputSettings()}")

    mic = ws.call(obs_requests.GetInputSettings(inputName="Mic/Aux"))
    print(f"Mic/Aux device: {mic.getInputSettings()}")

    print("\n[*] Desktop Audio should be:")
    print("  device_id: CABLE Output (VB-Audio Virtual Cable)")
    print("\n[*] If it's wrong, updating now...")

    ws.call(obs_requests.SetInputSettings(
        inputName="Desktop Audio",
        inputSettings={
            "device_id": "CABLE Output (VB-Audio Virtual Cable)"
        },
        overlay=True
    ))

    print("[OK] Desktop Audio set to VB-Cable!")

except Exception as e:
    print(f"[ERROR] {e}")

ws.disconnect()
