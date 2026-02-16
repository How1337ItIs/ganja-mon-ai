import sounddevice as sd
import numpy as np

print("Testing DEFAULT microphone (None)...")
try:
    print("Recording 2 seconds - SPEAK NOW...")
    audio = sd.rec(int(2 * 16000), samplerate=16000, channels=1, device=None, dtype='float32')
    sd.wait()
    peak = np.max(np.abs(audio))
    print(f"SUCCESS! Peak level: {peak:.3f}")
    if peak > 0.01:
        print("MIC IS WORKING!")
    else:
        print("Mic works but no audio detected")
except Exception as e:
    print(f"DEFAULT MIC FAILED: {e}")
