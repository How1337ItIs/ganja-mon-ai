import sounddevice as sd
import numpy as np

print("Testing microphone device 21...")
try:
    audio = sd.rec(int(1 * 16000), samplerate=16000, channels=1, device=21, dtype='float32')
    sd.wait()
    print("SUCCESS - Device 21 works!")
except Exception as e:
    print(f"Device 21 FAILED: {e}")

print("\nTesting device 23 (Headset API 2)...")
try:
    audio = sd.rec(int(1 * 16000), samplerate=16000, channels=1, device=23, dtype='float32')
    sd.wait()
    print("SUCCESS - Device 23 works!")
except Exception as e:
    print(f"Device 23 FAILED: {e}")

print("\nTesting device 32 (Realtek Mic API 3)...")
try:
    audio = sd.rec(int(1 * 16000), samplerate=16000, channels=1, device=32, dtype='float32')
    sd.wait()
    print("SUCCESS - Device 32 works!")
except Exception as e:
    print(f"Device 32 FAILED: {e}")
