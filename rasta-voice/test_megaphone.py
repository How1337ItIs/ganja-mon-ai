#!/usr/bin/env python3
"""Play a longer, louder test tone to all headphone outputs."""
import sounddevice as sd
import numpy as np
import time

def generate_tone(freq=880, duration=3.0, sample_rate=48000, volume=0.5):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Alternating beep pattern
    beep = np.sin(2 * np.pi * freq * t)
    envelope = (np.sin(2 * np.pi * 2 * t) > 0).astype(np.float32)  # On/off pattern
    tone = volume * beep * envelope
    return tone.astype(np.float32)

print("\n" + "="*60)
print("LOUD TEST - Playing through ALL headphone outputs")
print("="*60)
print("\nMake sure:")
print("  1. Megaphone is ON")
print("  2. Megaphone volume is UP")
print("  3. 3.5mm cable connected to both devices")
print("\nPlaying now...\n")

# Try device 19 first (most likely the 3.5mm jack)
for device_id in [19, 6, 15]:
    try:
        info = sd.query_devices(device_id)
        sr = int(info['default_samplerate'])
        print(f"Playing Device {device_id}: {info['name'][:40]}...", end=" ", flush=True)
        
        tone = generate_tone(freq=880, duration=3.0, sample_rate=sr, volume=0.7)
        sd.play(tone, samplerate=sr, device=device_id)
        sd.wait()
        print("Done!")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error: {e}")

print("\n✅ Test complete - did you hear anything through the megaphone?")
