#!/usr/bin/env python3
"""Comprehensive audio test - find the issue"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from obswebsocket import obsws, requests as obs_requests
import sounddevice as sd
import numpy as np
import time

print("="*70)
print("COMPREHENSIVE AUDIO TEST")
print("="*70)

# Test 1: Check VB-Cable exists
print("\n[TEST 1] VB-Cable Device Detection")
print("-"*70)
devices = sd.query_devices()
cable_input = None
cable_output = None

for i, dev in enumerate(devices):
    if "CABLE INPUT" in dev['name'].upper() and dev['max_output_channels'] > 0:
        cable_input = i
        print(f"[OK] Found CABLE Input (output): device {i}")
    if "CABLE OUTPUT" in dev['name'].upper():
        cable_output = i
        print(f"[OK] Found CABLE Output: device {i}")

if cable_input is None:
    print("[ERROR] VB-Cable Input (output device) not found!")
if cable_output is None:
    print("[ERROR] VB-Cable Output not found!")

# Test 2: Play test tone to VB-Cable
print("\n[TEST 2] Playing test tone to VB-Cable...")
print("-"*70)

if cable_input is not None:
    try:
        # Generate 1 second 440Hz tone
        duration = 1
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        tone = 0.3 * np.sin(2 * np.pi * 440 * t)

        print(f"[*] Playing 440Hz tone to device {cable_input} (CABLE Input)...")
        sd.play(tone, samplerate=sample_rate, device=cable_input)
        sd.wait()
        print("[OK] Tone played to VB-Cable!")
        print("    Did you hear it in headphones? (if Listen enabled)")
    except Exception as e:
        print(f"[ERROR] Failed to play: {e}")

# Test 3: Check OBS configuration
print("\n[TEST 3] OBS Configuration")
print("-"*70)

ws = obsws("localhost", 4455, "h2LDVnmFYDUpSVel")
ws.connect()

desktop_settings = ws.call(obs_requests.GetInputSettings(inputName="Desktop Audio"))
current_device = desktop_settings.getInputSettings().get("device_id", "")

print(f"[*] OBS Desktop Audio device: {current_device}")

if "CABLE" not in current_device.upper():
    print("[WARN] OBS not using VB-Cable!")
else:
    print("[OK] OBS is configured for VB-Cable")

# Test 4: Check if Desktop Audio is muted in OBS
mute_status = ws.call(obs_requests.GetInputMute(inputName="Desktop Audio"))
if mute_status.getInputMuted():
    print("[ERROR] Desktop Audio is MUTED in OBS!")
    print("[FIX] Unmuting now...")
    ws.call(obs_requests.SetInputMute(inputName="Desktop Audio", inputMuted=False))
    print("[OK] Desktop Audio unmuted!")
else:
    print("[OK] Desktop Audio is unmuted")

# Test 5: Check volume level
volume = ws.call(obs_requests.GetInputVolume(inputName="Desktop Audio"))
vol_db = volume.getInputVolumeDb()
print(f"[*] Desktop Audio volume: {vol_db:.1f} dB")

if vol_db < -20:
    print("[WARN] Volume is very low!")
    print("[FIX] Setting to 0dB...")
    ws.call(obs_requests.SetInputVolume(inputName="Desktop Audio", inputVolumeDb=0.0))
    print("[OK] Volume set to 0dB")
else:
    print("[OK] Volume is adequate")

ws.disconnect()

# Final recommendations
print("\n" + "="*70)
print("DIAGNOSIS & RECOMMENDATIONS")
print("="*70)

print("\nFor TWITTER SPACES to work:")
print("  1. Use Desktop X or Browser X (not phone)")
print("  2. Microphone setting in Spaces: 'CABLE Output'")
print("  3. Make sure rasta pipeline is running")
print("  4. Talk - they should hear rasta")

print("\nFor OBS to work:")
print("  1. Desktop Audio device: CABLE Output")
print("  2. Desktop Audio: Unmuted")
print("  3. Volume: 0dB or higher")
print("  4. Talk - meter should move")

print("\nIf NEITHER works:")
print("  - Check Windows Sound: CABLE Input -> Listen tab -> ENABLED")
print("  - Restart VB-Cable driver")
print("  - Restart rasta pipeline")

print("\n" + "="*70)
