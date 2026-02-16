# VB-Cable Audio Routing Fix - Post-Restart Handoff

**Date:** 2026-01-20
**Status:** Awaiting Windows restart → VB-Cable reinstall → Final testing

---

## Summary

We successfully built a working Rasta voice pipeline but encountered VB-Cable driver corruption that causes distorted audio. The pipeline WORKS and audio DOES reach Twitter Spaces, but quality is degraded due to a driver error.

### What Works ✅

- **Voice Pipeline**: Mic → Deepgram STT → xAI (Jamaican Patois) → ElevenLabs TTS → Audio output
- **TTS Quality**: Excellent when playing to headphones/default output (sounds perfect)
- **Audio Routing**: Successfully sends audio to VB-Cable, and Twitter Spaces receives it
- **Code**: All updated to use `rasta_live.py` (production pipeline with Deepgram/xAI/ElevenLabs)

### Current Problem ❌

- **VB-Cable Driver Error**: Device Manager shows one VB-Cable instance with "Error" status
- **Symptom**: Distorted/garbled audio when routing through VB-Cable to Twitter Spaces
- **Root Cause**: Corrupted/duplicate VB-Cable driver installation

---

## What Happened This Session

1. **Fixed deprecated AssemblyAI pipeline** → Switched to `rasta_live.py` using Deepgram
2. **Deleted broken scripts**: `rasta_pipeline_eleven.py`, `rasta_pipeline.py`
3. **Implemented audio routing**:
   - Added VB-Cable support for Twitter Spaces
   - Added dual-output capability (VB-Cable + Headphones)
   - Implemented sample rate conversion (24kHz → 48kHz for VB-Cable WASAPI)
4. **Discovered VB-Cable driver corruption**:
   - Multiple conflicting VB-Audio products installed
   - One VB-Cable instance shows "Error" in Device Manager
   - Causes constant noise and distortion

### Device Configuration Found

**VB-Audio Products Installed:**
- VB-Audio Virtual Cable (standard) - has Error instance
- VB-Audio Virtual Cable 16ch (multi-channel)
- VB-Audio Point (separate product)

**Working Devices (Before Corrupted Driver):**
- Device 8/17/21: CABLE Input (where TTS outputs)
- Device 3/12/24: CABLE Output (what Twitter uses as "mic")
- Device 5/14/18: Headphones (Realtek)

### Code Changes Made

**File: `/mnt/c/Users/natha/sol-cannabis/rasta-voice/rasta_live.py`**

Key updates:
- Uses scipy.signal.resample for high-quality 24kHz → 48kHz conversion
- Supports `--twitter-device` and `--monitor-device` args
- Has `--no-monitor` flag to disable headphone output
- Auto-detects VB-Cable and Headphones devices

**Sample rate strategy:**
- ElevenLabs outputs: 24kHz PCM
- VB-Cable WASAPI needs: 48kHz
- Resamples using scipy for quality

---

## Actions After Windows Restart

### Step 1: Verify VB-Cable Uninstalled

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe -c "import sounddevice as sd; [print(f'{i}: {d[\"name\"]}') for i, d in enumerate(sd.query_devices()) if 'CABLE' in d['name']]"
```

**Expected**: Should show NO devices (or very few if Windows audio hasn't cleared yet)

### Step 2: Reinstall VB-Cable Fresh

1. **Download**: https://vb-audio.com/Cable/ (click "Download" button - free version)
2. **Extract ZIP** to Downloads folder
3. **Run as Administrator**:
   - Right-click `VBCABLE_Setup_x64.exe`
   - "Run as administrator"
   - Click "Install Driver"
   - Wait for success message
4. **Restart Windows** (REQUIRED for driver to load)

### Step 3: Verify Clean Install

After second restart:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe test_vbcable.py --list
```

**Expected**: Should see:
- CABLE Input (VB-Audio Virtual Cable) - as OUTPUT device
- CABLE Output (VB-Audio Virtual Cable) - as INPUT device
- NO error devices
- NO "VB-Audio Point" or multi-channel versions (unless you want those)

### Step 4: Test VB-Cable Audio Quality

```bash
# Test tone to VB-Cable
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000

# If you hear distortion, the driver is still broken - repeat uninstall/reinstall
```

**Expected**: Clean 440Hz tone (you won't hear it unless monitoring CABLE Output somewhere)

### Step 5: Test TTS Quality

```bash
# Test TTS to default output (headphones) - verify voice sounds good
venv/Scripts/python.exe test_tts_simple.py

# Test TTS to VB-Cable (won't hear it - silent test)
venv/Scripts/python.exe rasta_live.py --test --no-monitor

# Test TTS to headphones (hear the quality)
venv/Scripts/python.exe rasta_live.py --test --monitor-device 5
```

**Expected**: Crystal clear Jamaican voice, no distortion

### Step 6: Run Live Pipeline for Twitter Spaces

```bash
# Start the live voice transformer
venv/Scripts/python.exe rasta_live.py --no-monitor
```

This will:
- Listen to your microphone
- Transform speech to Jamaican Patois
- Speak through ElevenLabs Denzel voice
- Route audio to VB-Cable

**In Twitter Spaces:**
1. Set microphone to **"CABLE Output (VB-Audio Virtual Cable)"**
2. Speak into your real mic
3. Rasta voice should come through in Twitter

---

## Troubleshooting

### If VB-Cable still has distortion after reinstall:

**Option A: Use VB-Audio Point instead**
- Device 34: Output (VB-Audio Point)
- Device 33: CABLE Output (VB-Audio Point) for Twitter
- Run with: `--twitter-device 34`

**Option B: Use Voicemeeter (better alternative)**
- Download: https://vb-audio.com/Voicemeeter/
- More robust than VB-Cable
- Has built-in audio mixer and routing

### If auto-detection fails:

List devices and manually specify:
```bash
venv/Scripts/python.exe rasta_live.py --list-devices
venv/Scripts/python.exe rasta_live.py --twitter-device <NUM>
```

### If audio is too quiet in Twitter:

Increase VB-Cable volume:
1. Sound Control Panel → Recording tab
2. Right-click "CABLE Output" → Properties
3. Levels tab → Set to 100%

---

## Command Reference

```bash
# List all audio devices
venv/Scripts/python.exe rasta_live.py --list-devices

# Test components (TTS to default output)
venv/Scripts/python.exe rasta_live.py --test

# Run live for Twitter (no local monitoring)
venv/Scripts/python.exe rasta_live.py --no-monitor

# Run live with headphone monitoring (dual output)
venv/Scripts/python.exe rasta_live.py

# Specify devices manually
venv/Scripts/python.exe rasta_live.py --twitter-device 21 --monitor-device 18

# Test VB-Cable routing
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000
```

---

## Key Files

| File | Purpose |
|------|---------|
| `rasta_live.py` | Main voice pipeline (Deepgram + xAI + ElevenLabs) |
| `test_vbcable.py` | Audio device testing utility |
| `test_tts_simple.py` | Simple TTS quality test |
| `voice_server.py` | Web dashboard server (separate, localhost only) |

---

## Technical Details

### Audio Flow
```
Your Mic
  → Deepgram STT (WebSocket, Nova-2 model)
  → xAI Grok-3-fast (Jamaican Patois transformation)
  → ElevenLabs TTS (Denzel voice, Turbo v2.5)
  → [Resample 24kHz → 48kHz using scipy]
  → VB-Cable Input (device 21 WASAPI)
  → [VB-Cable internal routing]
  → CABLE Output
  → Twitter Spaces
```

### Sample Rates
- **Microphone**: 16kHz (Deepgram requirement)
- **ElevenLabs output**: 24kHz PCM
- **VB-Cable WASAPI**: 48kHz (native)
- **Resampling**: scipy.signal.resample (high quality)

### Environment Variables Required
```bash
DEEPGRAM_API_KEY=your_key
XAI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE  # Denzel - Jamaican voice
```

---

## Success Criteria

After completing all steps, you should have:

1. ✅ VB-Cable installed with NO errors in Device Manager
2. ✅ Test tone plays cleanly through VB-Cable
3. ✅ TTS sounds perfect to headphones
4. ✅ TTS routes to Twitter Spaces without distortion
5. ✅ Can speak naturally and hear Rasta voice in Twitter

---

## Notes for Next Claude Instance

- The voice pipeline code is **complete and working**
- The ONLY remaining issue is the VB-Cable driver corruption
- After clean reinstall, everything should work immediately
- User has confirmed audio DOES reach Twitter Spaces (just distorted)
- Once VB-Cable is clean, run: `venv/Scripts/python.exe rasta_live.py --no-monitor`
- User should hear NOTHING locally (all audio goes to Twitter via VB-Cable)
- User will monitor by listening to themselves in Twitter Spaces

**Final Test Command:**
```bash
venv/Scripts/python.exe rasta_live.py --no-monitor
```

Then in Twitter Spaces: Select "CABLE Output" as microphone, speak, and the Rasta voice should come through clearly.
