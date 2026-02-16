# After Windows Restart - Quick Start Guide

## What We Fixed

1. ✅ Updated `rasta_live.py` to support 48kHz sample rate (was 16kHz)
2. ✅ Added `--input-device` parameter for explicit mic selection
3. ✅ Changed Deepgram to use 48kHz
4. ✅ Upgraded sounddevice 0.5.3 → 0.5.5
5. ✅ Updated CLAUDE.md with streaming policy (never stream without rasta voice)

## Commands to Run After Restart

### 1. Test AirPods Microphone
```bash
cd C:\Users\natha\sol-cannabis\rasta-voice
venv\Scripts\python.exe rasta_live.py --list-devices
```

Find your AirPods device number (should be device 1 or 10)

### 2. Test Audio Recording
```bash
venv\Scripts\python.exe -c "import sounddevice as sd; import numpy as np; audio = sd.rec(int(2 * 44100), samplerate=44100, channels=1, device=1); sd.wait(); print(f'Peak: {np.max(np.abs(audio)):.3f}')"
```

Should print a peak value > 0.01 (not crash with MME error)

### 3. Start Rasta Pipeline
```bash
venv\Scripts\python.exe rasta_live.py --input-device 1 --twitter-device 18 --monitor-device 19
```

**Device IDs:**
- `--input-device 1` = AirPods microphone (44.1kHz)
- `--twitter-device 18` = VB-Cable Input (for stream)
- `--monitor-device 19` = AirPods playback (hear yourself)

### 4. Configure OBS

From WSL/Claude Code:
```bash
cd /mnt/c/Users/natha/sol-cannabis
# I'll run the OBS configuration commands for you
```

### 5. Go Live

Once rasta voice is working:
- OBS will be configured automatically
- Desktop Audio will be set to VB-Cable Output
- Scene will have website + webcam
- I'll tweet the stream link

## If AirPods Still Don't Work

Try laptop internal mic:
```bash
venv\Scripts\python.exe rasta_live.py --input-device 11 --twitter-device 18 --monitor-device 19
```

Device 11 = Intel Smart Sound mic (built-in laptop)

## Tell Claude

Just say: **"restarted, test it"**

And I'll test everything and get you live!
