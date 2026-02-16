#!/usr/bin/env python3
"""Temporarily disable OBS Desktop Audio to free VB-Cable for Spaces"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Disabling OBS Desktop Audio to free VB-Cable...")

# Mute Desktop Audio in OBS
ws.call(obs_requests.SetInputMute(inputName="Desktop Audio", inputMuted=True))

print("[OK] OBS Desktop Audio MUTED")
print("\nNow VB-Cable is free for Twitter Spaces!")
print("\nTalk in Spaces - they should hear rasta now!")
print("\nOnce Spaces works, I'll configure OBS properly to share.")

ws.disconnect()
