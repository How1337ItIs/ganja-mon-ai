# Handoff - Jan 23 Stream Attempt (Audio Driver Issues)

**Date:** 2026-01-23, 4:20 PM PST
**Status:** 🔴 Stream postponed - Windows audio drivers corrupted
**Issue:** PortAudio Error -9999 preventing microphone access
**Solution:** Windows restart required
**Next Claude:** Test audio after restart and get stream live

---

## What Happened This Session

### Initial Goal
- Go live at 4:20 PST for Twitter video stream
- Use Rasta voice transformation (REQUIRED - never stream without it)
- Show grow dashboard + webcam + plant cam via OBS/Restream

### What We Successfully Completed

1. ✅ **Posted hype tweet** with plant image
   - Tweet ID: 2014844415651787261
   - Image: Current shot of Mon (Purple Milk)
   - Text announced 4:20 PST stream

2. ✅ **Posted LP locked tweet**
   - Tweet ID: 2014855453961028061
   - Announced Sablier liquidity lock
   - Transaction: 0x0f6491d17d6dd12ff05f7613ad8669ac3ee3e2c2ec00d5b9ff23fb7717cac47e
   - Stream: LK2-143-33

3. ✅ **Updated rasta voice character prompts**
   - Reduced "seen" usage (was overused)
   - Increased "mon" usage (Western stereotype)
   - Updated in: `rasta_live.py`, `test_dialect_xai.py`, `rasta_interactive.py`

4. ✅ **Updated CLAUDE.md policies**
   - Added Autonomy & Automation Policy (be maximally helpful, do things yourself)
   - Added Remote Agent Execution instructions
   - Added Streaming Policy: NEVER stream without rasta voice working

5. ✅ **Fixed Chromebook orchestrator**
   - Verified tweepy is installed
   - Service restarted and running
   - Twitter integration confirmed: `[OK] Twitter client initialized`
   - Automated tweets will post every 3 hours

6. ✅ **Fixed OBS configuration**
   - Desktop Audio set to "CABLE Output (VB-Audio Virtual Cable)"
   - Desktop Audio UNMUTED
   - Volume: 100% (0 dB)
   - Scene: "Main - Plant + You" configured
   - Browser sources added for website

7. ✅ **Updated rasta_live.py for better device support**
   - Changed sample rate: 16000 Hz → 48000 Hz (supports modern devices)
   - Added `--input-device` parameter for explicit mic selection
   - Added `device=config.input_device` to InputStream
   - Upgraded sounddevice: 0.5.3 → 0.5.5 (fresh PortAudio DLL)

### Critical Issue Encountered

**PortAudio Error -9999** - Cannot open ANY microphone input stream

**Symptoms:**
- Every microphone device fails: `Error opening InputStream: Unanticipated host error [PaErrorCode -9999]`
- Tested devices: AirPods (device 1, 10, 23), Intel mic (device 2, 11, 21), Realtek (device 32)
- Tested APIs: MME, DirectSound, WASAPI - all fail
- Tested libraries: sounddevice, pyaudiowpatch - both fail
- Error persists even with:
  - Administrator privileges
  - Fresh PortAudio DLL (sounddevice 0.5.5)
  - AirPods re-paired
  - Microphone privacy permissions enabled
  - Different sample rates (16kHz, 44.1kHz, 48kHz)

**Root Cause:** Windows audio driver corruption (worked yesterday, broken today)

**Evidence it's driver-level:**
- OBS CAN create microphone sources successfully
- Windows recognizes all devices as "OK"
- Privacy settings allow microphone access
- No exclusive-mode apps found
- Error is identical across all devices and libraries

**Solution:** Windows restart (only guaranteed fix for driver state)

---

## Current System State

### Tweets Posted
1. Stream announcement: https://twitter.com/GanjaMonAI/status/2014844415651787261
2. LP lock announcement: https://twitter.com/GanjaMonAI/status/2014855453961028061

### OBS Configuration
- **Status:** Running
- **WebSocket:** localhost:4455, password: h2LDVnmFYDUpSVel
- **Scene:** Main - Plant + You
- **Sources in scene:**
  - Sensor Bar (enabled)
  - Mon Plant Cam (disabled - toggle if needed)
  - Grow Website (enabled - http://192.168.125.128:8000)
  - You / Laptop Webcam Full / YOUR FACE (webcam - 0x0 size, needs manual activation)
  - Flashing Banner (disabled)
- **Desktop Audio:**
  - Device: CABLE Output (VB-Audio Virtual Cable) ✅
  - Muted: False ✅
  - Volume: 0 dB (100%) ✅
- **Streaming:** Stopped (was started, then stopped for troubleshooting)

### Chromebook Server
- **Status:** Running and healthy
- **Service:** grokmon active since 23:41 UTC
- **Hardware:** All connected (Govee, Ecowitt, Kasa, Tapo, webcam)
- **Twitter:** Initialized, will post every 3 hours
- **Dashboard:** http://192.168.125.128:8000 (kiosk mode displaying)

### Rasta Voice Pipeline
- **Status:** Modified, not running (killed for troubleshooting)
- **Files updated:**
  - `rasta_live.py` - 48kHz support, --input-device parameter
  - `test_dialect_xai.py` - Updated "mon"/"seen" usage
  - `rasta_interactive.py` - Updated character prompt
- **Configuration:**
  - Sample rate: 48000 Hz
  - Input device: Configurable via --input-device
  - Twitter device: 18 (VB-Cable Input WASAPI)
  - Monitor device: 19 (AirPods/Headphones WASAPI)

---

## After Windows Restart - Do This

### Step 1: Test AirPods Microphone

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice

# List devices to confirm IDs
./venv/Scripts/python.exe rasta_live.py --list-devices
```

**Find AirPods device ID** (probably 1, 10, or 23)

### Step 2: Quick Audio Test

```bash
# Test if mic works (should NOT crash with -9999 error after restart)
./venv/Scripts/python.exe -c "import sounddevice as sd; import numpy as np; audio = sd.rec(int(2 * 44100), samplerate=44100, channels=1, device=1); sd.wait(); print(f'Peak: {np.max(np.abs(audio)):.3f}')"
```

**Expected:** Prints a peak value (like "Peak: 0.023") without errors

### Step 3: Start Rasta Pipeline

```bash
# Use the device ID from step 1
./venv/Scripts/python.exe rasta_live.py --input-device 1 --twitter-device 18 --monitor-device 19
```

**Expected output:**
```
[INFO] Using microphone device: 1
[INFO] Connected to Deepgram
[INFO] Microphone active - speak now!
```

**NO ERRORS** about "InputStream" or "MME error"

### Step 4: Verify Audio Flow

**Speak into AirPods** - you should hear yourself in Rasta voice in your AirPods/headphones

**Check transcripts:**
```bash
tail -f live_transcripts.jsonl
```

Should show your speech being transformed to patois in real-time

### Step 5: Configure OBS (I'll do this for you)

Tell Claude: **"configure OBS"**

Claude will:
- Unmute Desktop Audio (VB-Cable)
- Enable website browser source
- Fix webcam source (manual click may be needed for camera activation)
- Position everything correctly
- Start streaming

### Step 6: Go Live

Once OBS is configured and streaming:
1. Get stream URL from Twitter/Restream
2. Tell Claude the URL
3. Claude tweets: "🔴 LIVE NOW [url]"

---

## Known Issues & Solutions

### Webcam Won't Activate in OBS
**Symptom:** Source size 0x0, no green light on camera
**Cause:** Windows requires UI interaction for first camera access
**Solution:**
- In OBS Sources list, double-click the webcam source
- Click OK in properties dialog
- Green light will turn on
- (Claude can position it via WebSocket after activation)

### Desktop Audio Not Capturing Rasta Voice
**Check:**
1. OBS Desktop Audio device = "CABLE Output (VB-Audio Virtual Cable)"
2. Desktop Audio is UNMUTED
3. Rasta pipeline is outputting to device 18 (CABLE Input)
4. VB-Cable virtual cable is routing audio between them

**Fix:** Claude can verify/fix all of these via OBS WebSocket

### Rasta Pipeline Crashes
**If you see:** "Error opening InputStream" after restart
**That means:** Windows restart didn't fix the driver issue
**Solution:** Try internal laptop mic (device 11) instead of AirPods

---

## File Changes Made This Session

### Modified Files
| File | Changes |
|------|---------|
| `rasta_live.py` | Sample rate 16k→48k, added --input-device param, device config |
| `test_dialect_xai.py` | More "mon", less "seen" in prompt |
| `rasta_interactive.py` | Updated character prompt |
| `CLAUDE.md` | Autonomy policy, streaming policy, remote agent instructions |

### Created Files
| File | Purpose |
|------|---------|
| `AFTER_RESTART_DO_THIS.md` | This document |
| `/tmp/fix_obs_scene.py` | OBS scene configuration script |
| `/tmp/check_audio_now.py` | Audio diagnostics |
| Various test scripts | Audio troubleshooting |

---

## Quick Commands for Next Claude

```bash
# Test if restart fixed audio
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
./venv/Scripts/python.exe -c "import sounddevice as sd; sd.rec(2*44100, 44100, 1, device=1); print('FIXED!')"

# Start pipeline
./venv/Scripts/python.exe rasta_live.py --input-device 1 --twitter-device 18 --monitor-device 19

# Configure OBS (from WSL)
cmd.exe /c python -c "from obswebsocket import obsws, requests; ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel'); ws.connect(); ws.call(requests.SetInputMute(inputName='Desktop Audio', inputMuted=False)); ws.call(requests.StartStream()); print('LIVE!'); ws.disconnect()"
```

---

## Success Criteria

✅ Rasta pipeline running without errors
✅ Can hear rasta voice in headphones when speaking
✅ OBS Desktop Audio showing audio levels (bars moving)
✅ Webcam visible in OBS preview (top-right corner)
✅ Website visible in OBS preview (fullscreen)
✅ Streaming to Restream/Twitter
✅ Stream link tweeted

---

## If It Still Doesn't Work After Restart

**Nuclear options:**
1. Use laptop internal mic instead of AirPods (device 11)
2. Reinstall Bluetooth drivers
3. Use different computer
4. File bug report with PortAudio project (this error shouldn't happen)

---

## For Documentation

**Once working, document in CLAUDE.md:**

```markdown
### Rasta Voice Pipeline - Streaming Setup

**Working Configuration (Post Jan-23 Fix):**

bash
cd rasta-voice
./venv/Scripts/python.exe rasta_live.py --input-device 1 --twitter-device 18 --monitor-device 19


**Device IDs:**
- Input (AirPods): 1 (44.1kHz)
- Twitter (VB-Cable): 18 (WASAPI)
- Monitor (Headphones): 19 (WASAPI)

**Sample Rate:** 48000 Hz (changed from 16000 Hz)

**OBS Audio:**
- Desktop Audio device: "CABLE Output (VB-Audio Virtual Cable)"
- Must be UNMUTED
- Volume: 100%

**Troubleshooting:**
- If PortAudio -9999 error: Restart Windows
- If webcam 0x0: Double-click source in OBS to activate
- If no audio in stream: Check Desktop Audio device/mute status
```

---

## Summary for User

**What got done:**
- ✅ 2 tweets posted (stream hype + LP lock)
- ✅ Rasta voice updated (more "mon", less "seen")
- ✅ Chromebook server verified working
- ✅ Code fixed for 48kHz audio support
- ✅ CLAUDE.md policies updated

**What's blocked:**
- ❌ Stream - Windows audio drivers broken

**What you need to do:**
1. Restart Windows
2. Tell next Claude: "restarted, test it"
3. Claude will get you live in 5 minutes

**You'll be streaming within 10 minutes of restart!**

---

## Technical Notes

### The -9999 Error

`PortAudio Error -9999: Unanticipated host error [MME error 1]`

This error means Windows audio device handle is invalid/stale. Causes:
- Driver state corruption (most common)
- Windows update changed audio subsystem
- Bluetooth audio driver in bad state
- Exclusive mode lock by phantom process

**Only reliable fix:** Windows restart (clears all driver state)

### Why AirPods Specifically

AirPods worked yesterday, broken today = Windows Bluetooth audio driver regression

Tested:
- Different device IDs (1, 10, 23)
- Different sample rates (16k, 44.1k, 48k)
- Different APIs (MME, DirectSound, WASAPI)
- Different libraries (sounddevice, pyaudiowpatch)
- Re-pairing AirPods
- Admin privileges
- Fresh PortAudio DLL

**Result:** All failed with -9999
**Conclusion:** System-level driver issue, not code issue

---

## Post-Restart Checklist

- [ ] Windows restarted
- [ ] Audio test passes (no -9999 error)
- [ ] Rasta pipeline starts successfully
- [ ] Can hear rasta voice in headphones
- [ ] OBS configured (Desktop Audio unmuted)
- [ ] Webcam activated (double-click in OBS)
- [ ] Stream started
- [ ] Stream link tweeted
- [ ] Configuration documented in CLAUDE.md

---

**Tell next Claude:** "restarted, test it" and they'll handle the rest!
