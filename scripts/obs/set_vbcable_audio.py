#!/usr/bin/env python3
"""Set OBS to use VB-Cable for rasta voice"""
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

try:
    print("[*] Getting audio devices...")

    # Get input list
    devices = ws.call(obs_requests.GetInputList())

    print("\n[*] Setting audio to VB-Cable...")

    # Set desktop audio to VB-Cable Output
    ws.call(obs_requests.SetInputSettings(
        inputName="Desktop Audio",
        inputSettings={
            "device_id": "VB-Cable"  # VB-Cable virtual audio device
        }
    ))

    print("[OK] OBS will now capture VB-Cable output (Rasta voice)!")
    print("\nMake sure:")
    print("  1. VB-Cable is installed")
    print("  2. Rasta voice pipeline outputs to VB-Cable")
    print("  3. Start: python rasta-voice/rasta_live.py")

except Exception as e:
    print(f"[ERROR] {e}")
    print("\nManual fix:")
    print("  OBS Settings -> Audio")
    print("  Desktop Audio: VB-Cable Output")
    print("  Mic/Aux: (None) or VB-Cable Input")

ws.disconnect()
