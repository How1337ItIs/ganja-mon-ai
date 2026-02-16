#!/usr/bin/env python3
"""List ALL available audio devices on Windows"""
import sounddevice as sd

print("="*60)
print("AVAILABLE AUDIO DEVICES")
print("="*60)

devices = sd.query_devices()
for i, dev in enumerate(devices):
    marker = ""
    if "CABLE" in dev['name'].upper():
        marker = " <-- VB-CABLE"
    if dev['max_input_channels'] > 0:
        print(f"[INPUT {i:2d}] {dev['name']}{marker}")
    if dev['max_output_channels'] > 0:
        print(f"[OUTPUT {i:2d}] {dev['name']}{marker}")

print("="*60)
print("\nOBS Desktop Audio should use:")
print("  CABLE Output (playback/output device)")
print("\nRasta pipeline outputs to:")
print("  CABLE Input (recording/input device for the pipeline)")
print("  CABLE Output (what OBS captures)")
print("="*60)
