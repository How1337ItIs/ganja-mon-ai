#!/usr/bin/env python3
"""Force OBS to use CABLE Output"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Setting Desktop Audio to CABLE Output...")

ws.call(obs_requests.SetInputSettings(
    inputName="Desktop Audio",
    inputSettings={
        "device_id": "CABLE Output (VB-Audio Virtual Cable)"
    },
    overlay=True
))

print("[OK] Set to CABLE Output!")
print("\nNow test:")
print("  1. Talk into mic")
print("  2. Rasta voice plays")
print("  3. Watch OBS Desktop Audio meter")
print("\nIf still doesn't move, the issue is:")
print("  Rasta is playing to device 18 (CABLE Input)")
print("  But OBS needs to hear what's OUTPUTTING from VB-Cable")
print("\nMay need to set Windows 'Listen to this device' on CABLE Input...")

ws.disconnect()
