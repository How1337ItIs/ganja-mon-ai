#!/usr/bin/env python3
"""Unmute ALL audio in OBS"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

print("[*] Unmuting ALL OBS audio sources...")

# Unmute Desktop Audio
ws.call(obs_requests.SetInputMute(inputName="Desktop Audio", inputMuted=False))
ws.call(obs_requests.SetInputVolume(inputName="Desktop Audio", inputVolumeDb=0.0))
print("[OK] Desktop Audio: UNMUTED, Volume: 0dB")

# Unmute Mic/Aux
ws.call(obs_requests.SetInputMute(inputName="Mic/Aux", inputMuted=False))
ws.call(obs_requests.SetInputVolume(inputName="Mic/Aux", inputVolumeDb=0.0))
print("[OK] Mic/Aux: UNMUTED, Volume: 0dB")

print("\n[SUCCESS] All audio unmuted in OBS!")
print("Check OBS Audio Mixer - meters should show activity!")

ws.disconnect()
