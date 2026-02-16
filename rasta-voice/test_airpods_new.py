import sounddevice as sd
import numpy as np

print("Testing AirPods device 1 with new PortAudio DLL...")
print("(Upgraded sounddevice 0.5.3 -> 0.5.5)")

try:
    audio = sd.rec(int(2 * 44100), samplerate=44100, channels=1, device=1, dtype='float32')
    sd.wait()
    peak = np.max(np.abs(audio))
    print(f"Peak level: {peak:.3f}")

    if peak > 0.001:
        print("\n*** SUCCESS - AIRPODS WORKING! ***")
    else:
        print("Mic accessible but no audio detected")

except Exception as e:
    print(f"ERROR: {e}")
