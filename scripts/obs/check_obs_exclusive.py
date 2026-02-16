#!/usr/bin/env python3
"""Check if OBS is blocking VB-Cable with exclusive mode"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Checking Desktop Audio settings...")

settings = ws.call(obs_requests.GetInputSettings(inputName="Desktop Audio"))
current = settings.getInputSettings()

print(f"\nCurrent settings: {current}")
print("\n[*] Checking for exclusive mode...")

# Check if exclusive mode is enabled
if current.get('use_device_timing', False):
    print("[WARN] Device timing enabled - may cause exclusive lock!")

print("\n[FIX] Setting to NON-exclusive mode...")

# Update to allow sharing
ws.call(obs_requests.SetInputSettings(
    inputName="Desktop Audio",
    inputSettings={
        "device_id": current.get("device_id", "CABLE Output (VB-Audio Virtual Cable)"),
        "use_device_timing": False  # Don't lock the device
    },
    overlay=True
))

print("[OK] Desktop Audio set to SHARED mode!")
print("\nBoth OBS and Twitter Spaces should work now!")
print("\nRestart Twitter Spaces audio (disconnect/reconnect mic)")

ws.disconnect()
