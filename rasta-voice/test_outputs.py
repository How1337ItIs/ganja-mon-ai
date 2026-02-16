#!/usr/bin/env python3
"""Test different audio output devices to find the headphone jack."""
import sounddevice as sd
import numpy as np
import time

# Generate a test tone
def generate_tone(freq=440, duration=1.0, sample_rate=48000):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = 0.3 * np.sin(2 * np.pi * freq * t)
    return tone.astype(np.float32)

# List of likely headphone jack devices to test
test_devices = [
    (6, "Headphones (Realtek(R) Audio) @ 44100Hz"),
    (15, "Headphones (Realtek(R) Audio) @ 44100Hz"),
    (19, "Headphones (Realtek(R) Audio) @ 48000Hz"),
    (29, "Headphones 1 (Realtek HD Audio 2nd output) @ 48000Hz"),
    (30, "Headphones 2 (Realtek HD Audio 2nd output) @ 44100Hz"),
    (33, "Headphones () @ 44100Hz"),
]

print("\n" + "="*60)
print("AUDIO OUTPUT TEST - Find your 3.5mm headphone jack")
print("="*60)
print("\nI'll play a beep through different outputs.")
print("Listen to your megaphone and tell me which one works!\n")

for device_id, name in test_devices:
    try:
        print(f"Testing Device [{device_id}]: {name}")
        print("  Playing tone... ", end="", flush=True)
        
        # Try to get device's sample rate
        try:
            info = sd.query_devices(device_id)
            sr = int(info['default_samplerate'])
        except:
            sr = 48000
        
        tone = generate_tone(freq=880, duration=1.5, sample_rate=sr)
        sd.play(tone, samplerate=sr, device=device_id)
        sd.wait()
        print("Done!")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*60)
print("Which device played through your megaphone?")
print("="*60)
