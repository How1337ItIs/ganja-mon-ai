import sounddevice as sd
import numpy as np

# Test AirPods devices
for dev_id in [1, 10, 23]:
    try:
        d = sd.query_devices(dev_id)
        print(f"\nDevice {dev_id}: {d['name']}")
        print(f"  Sample rate: {d['default_samplerate']}")

        print(f"  Testing...")
        audio = sd.rec(int(1 * int(d['default_samplerate'])),
                      samplerate=int(d['default_samplerate']),
                      channels=1,
                      device=dev_id,
                      dtype='float32')
        sd.wait()
        print(f"  ✓ WORKS!")
        break
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
