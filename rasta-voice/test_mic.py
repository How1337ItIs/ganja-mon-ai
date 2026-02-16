#!/usr/bin/env python3
"""Quick mic test - run this yourself"""
import sounddevice as sd
import numpy as np

print("Press ENTER when ready, then speak for 3 seconds")
input()
print("RECORDING...")

audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype=np.float32)
sd.wait()

peak = np.abs(audio).max()
print(f"Peak level: {peak:.4f}")

if peak > 0.02:
    print("MIC WORKING!")
elif peak > 0.005:
    print("Mic working but quiet")
else:
    print("No audio detected")
