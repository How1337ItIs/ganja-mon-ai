#!/usr/bin/env python3
"""Test if VB-Cable loopback is actually working"""
import sounddevice as sd
import numpy as np
import time
import threading

print("="*70)
print("VB-CABLE LOOPBACK TEST")
print("="*70)

# Find devices
devices = sd.query_devices()
cable_input_playback = None  # Where we play TO
cable_output_record = None   # Where we record FROM

for i, dev in enumerate(devices):
    if "CABLE INPUT" in dev['name'].upper() and dev['max_output_channels'] > 0:
        cable_input_playback = i
        print(f"[OK] CABLE Input (playback): device {i} - {dev['name']}")
    if "CABLE OUTPUT" in dev['name'].upper() and dev['max_input_channels'] > 0:
        if cable_output_record is None:  # Use first valid one
            cable_output_record = i
        print(f"[OK] CABLE Output (recording): device {i} - {dev['name']}")

if cable_input_playback is None or cable_output_record is None:
    print("[ERROR] VB-Cable not properly configured!")
    exit(1)

print(f"\n[TEST] Playing tone to device {cable_input_playback}...")
print(f"[TEST] Recording from device {cable_output_record}...")
print("\nIf loopback works, we should capture the tone!\n")

# Record what comes through CABLE Output
recording = []
def record_callback(indata, frames, time_info, status):
    recording.append(indata.copy())

# Start recording from CABLE Output
stream = sd.InputStream(
    device=cable_output_record,
    channels=1,
    samplerate=48000,
    callback=record_callback
)

stream.start()
time.sleep(0.5)  # Let it stabilize

# Play tone to CABLE Input
duration = 2
sample_rate = 48000
t = np.linspace(0, duration, int(sample_rate * duration))
tone = 0.5 * np.sin(2 * np.pi * 440 * t)

print("[*] Playing 2-second 440Hz tone...")
sd.play(tone, samplerate=sample_rate, device=cable_input_playback)
sd.wait()

time.sleep(0.5)
stream.stop()
stream.close()

# Analyze recording
if recording:
    recorded_audio = np.concatenate(recording)
    max_amplitude = np.max(np.abs(recorded_audio))

    print(f"\n[RESULT] Recorded {len(recorded_audio)} samples")
    print(f"[RESULT] Max amplitude: {max_amplitude:.4f}")

    if max_amplitude > 0.01:
        print("\n[SUCCESS] VB-CABLE LOOPBACK IS WORKING!")
        print(f"Signal detected with amplitude {max_amplitude:.4f}")
        print("\nThis means:")
        print("  ✅ Audio played to CABLE Input")
        print("  ✅ Looped through to CABLE Output")
        print("  ✅ OBS can capture it")
        print("  ✅ Twitter Spaces can use it")
    else:
        print("\n[FAILED] NO AUDIO DETECTED!")
        print("VB-Cable loopback is NOT working!")
        print("\nPossible fixes:")
        print("  1. Reinstall VB-Cable driver")
        print("  2. Restart Windows audio service")
        print("  3. Check VB-Cable Control Panel settings")
else:
    print("\n[ERROR] No recording captured!")

print("\n" + "="*70)
