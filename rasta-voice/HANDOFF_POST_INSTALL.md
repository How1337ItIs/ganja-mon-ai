# Post-Installation Handoff - VB-Cable Testing & Verification

**Date:** 2026-01-20
**Status:** ✅ Fresh VB-Cable installed → Windows restarting (Restart 2 of 2) → Ready for testing
**Session:** Continuation after VB-Cable installation and second Windows restart

---

## What Just Happened

### ✅ Completed Steps

1. **Verified clean uninstall:**
   - Ran `check_status.py` after first restart
   - Result: **ALL CLEAR** - No VB-Audio devices found
   - Confirmed complete removal of all old/corrupted drivers

2. **Installed fresh VB-Cable:**
   - Ran `install_vbaudio.ps1` PowerShell script
   - User clicked "Install Driver" button in installer GUI
   - Installation completed successfully
   - Installer closed cleanly

3. **User restarted Windows (second restart):**
   - This restart loads the fresh VB-Cable driver into Windows
   - Driver should now be active and ready to use

### 📋 Current State

- **VB-Audio drivers:** Freshly installed, should show 2 devices after restart
- **Voice pipeline code:** Ready and tested (`rasta_live.py`)
- **Windows:** Just completed second restart
- **Next action:** Verify installation and test audio quality

---

## What Needs to Happen Next

### STEP 1: Verify Clean Installation ✅

First, confirm VB-Cable installed correctly with exactly 2 devices:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe check_status.py
```

**Expected output:**
```
[INFO] STATUS: 2 VB-Audio device(s) found

VB-Cable (Standard):
  [X] CABLE Output (VB-Audio Virtual Cable)
      Type: INPUT, Channels: 2, Sample Rate: 48000.0 Hz
  [Y] CABLE Input (VB-Audio Virtual Cable)
      Type: OUTPUT, Channels: 2, Sample Rate: 48000.0 Hz

[OK] LOOKS GOOD: Clean VB-Cable installation detected

Next step: Test audio quality
```

**If this doesn't match:**
- Too many devices = something went wrong, investigate
- No devices = driver didn't load, restart again or reinstall
- "Error" status = driver corruption, may need alternative solution

### STEP 2: Test VB-Cable Audio Routing 🔊

Test that VB-Cable can handle audio without distortion:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice

# Test 1: Simple tone to VB-Cable (validates basic routing)
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000
```

**Expected:** No errors, completes without crashes

**If errors occur:**
- Sample rate mismatch = driver not configured correctly
- Device not found = VB-Cable didn't install properly
- Distortion/crackling = driver still corrupted (unlikely after fresh install)

### STEP 3: Test TTS Voice Quality 🎙️

Test the full voice pipeline with ElevenLabs TTS:

```bash
# Test with headphones (user will hear Jamaican voice)
venv/Scripts/python.exe rasta_live.py --test
```

**Expected:**
- No errors or warnings
- Crystal clear Jamaican voice through headphones
- No distortion, crackling, or garbling
- Voice sounds natural and authentic

**Test phrase:** "Wah gwaan, bredren? Dis a di Rasta voice test, seen?"

**If audio is distorted:**
- VB-Cable driver still has issues
- May need to try alternative (Voicemeeter, VB-Audio Point)

### STEP 4: Test VB-Cable Output (Silent Test) 🔇

Test routing to VB-Cable without local monitoring:

```bash
venv/Scripts/python.exe rasta_live.py --test --no-monitor
```

**Expected:**
- No audio heard locally (silent)
- No errors in console
- Script completes successfully

**What this tests:** Audio routing to VB-Cable works without headphone monitoring

### STEP 5: Run Live Voice Pipeline 🚀

If all tests pass, start the production voice transformer:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe rasta_live.py --no-monitor
```

**What happens:**
- Script starts listening to microphone
- Console shows: `Listening for speech...`
- When user speaks, it transcribes → transforms → speaks via TTS
- Audio routes to VB-Cable silently (no local playback)
- Keeps running until Ctrl+C

**Test it:**
1. Speak into microphone: "Hello, this is a test"
2. Wait 2-3 seconds for processing
3. Console shows transcription and Patois transformation
4. Audio plays to VB-Cable (won't hear locally)

### STEP 6: Configure Twitter Spaces 🐦

Guide user to set up Twitter Spaces with VB-Cable:

**Instructions for user:**
1. Open Twitter Spaces (web or app)
2. Start a Space or join as speaker
3. Click microphone settings/permissions
4. **Select microphone:** "CABLE Output (VB-Audio Virtual Cable)"
5. Speak into real microphone
6. Rasta voice comes through Twitter Spaces

**Verification:**
- User speaks normally into mic
- Rasta voice plays in Twitter Spaces
- Audio is clear, no distortion
- Latency is acceptable (~2-3 seconds)

---

## Architecture Reminder

### Voice Pipeline Flow
```
Real Microphone (16kHz)
  ↓
Deepgram STT (WebSocket, Nova-2 model)
  ↓ [Transcription]
"Hello, this is a test"
  ↓
xAI Grok-3-fast (Jamaican Patois transformation)
  ↓ [Translation]
"Wah gwaan, dis a di test, seen?"
  ↓
ElevenLabs TTS (Denzel voice, Turbo v2.5, 24kHz output)
  ↓ [Audio generation]
24kHz stereo audio
  ↓
[Scipy resample: 24kHz → 48kHz]
  ↓
VB-Cable Input (WASAPI, 48kHz stereo)
  ↓ [Internal virtual routing]
CABLE Output (appears as microphone in Windows)
  ↓
Twitter Spaces / OBS / Discord / etc.
```

### Key Technical Details

**Sample Rate Conversion:**
- ElevenLabs outputs 24kHz audio
- VB-Cable expects 48kHz (WASAPI default)
- `scipy.signal.resample` handles conversion in `rasta_live.py`

**Device Auto-Detection:**
- `rasta_live.py` scans `sounddevice.query_devices()`
- Looks for "CABLE" in device names
- Falls back to manual device selection if auto-detection fails

**Dual Output Mode:**
- Default: Sends to both VB-Cable AND headphones
- `--no-monitor` flag: VB-Cable only (silent)
- Useful for testing with headphones, production without

**Voice Configuration:**
- Model: `eleven_turbo_v2_5` (low latency, 24kHz output)
- Voice: "Denzel" (ID: `dhwafD61uVd8h85wAZSE`)
- Settings: Stability 0.0 (creative), similarity boost enabled
- Supports emotion tags: `[laughs]`, `[chuckles]`, `[sighs]`

---

## Project Context

### The Problem We Solved

Before this fix:
- ✅ Voice pipeline was fully functional (STT → Patois → TTS)
- ✅ Audio successfully routed to VB-Cable
- ✅ Twitter Spaces received the audio
- ❌ **BUT:** Audio was severely distorted/garbled

**Root Cause:** Corrupted VB-Cable drivers
- 12 conflicting VB-Audio devices installed
- Multiple versions mixed (standard, 16ch, Point)
- One device showing "Error" status in Device Manager
- Driver conflict caused audio corruption

### The Solution We Executed

Complete driver cleanup and fresh reinstall:
1. ✅ Removed ALL VB-Audio products (via PowerShell script)
2. ✅ Restarted Windows (cleared driver cache)
3. ✅ Installed ONLY standard VB-Cable (single clean install)
4. ✅ Restarted Windows again (loaded fresh driver) ← **YOU ARE HERE**
5. ⏳ Test and verify (next steps)

---

## File Inventory

### Core Voice Pipeline
| File | Purpose | Status |
|------|---------|--------|
| `rasta_live.py` | Main voice pipeline (Deepgram + xAI + ElevenLabs) | ✅ Working |
| `test_vbcable.py` | Audio device testing utility | ✅ Ready |
| `test_tts_simple.py` | Simple TTS quality test | ✅ Ready |
| `check_status.py` | VB-Cable status checker | ✅ Ready |

### Installation/Debugging Scripts
| File | Purpose | Status |
|------|---------|--------|
| `uninstall_vbaudio.ps1` | Automated driver uninstaller | ✅ Used (completed) |
| `install_vbaudio.ps1` | Automated driver installer | ✅ Used (completed) |
| `VBCABLE_Driver/VBCABLE_Setup_x64.exe` | Official VB-Cable installer | ✅ Used |
| `*.bat` files | Windows GUI wrappers for PowerShell scripts | 📖 Available |

### Documentation
| File | Purpose |
|------|---------|
| `VB_CABLE_FIX_STEPS.md` | Detailed manual fix instructions |
| `HANDOFF_VBCABLE_FIX.md` | Original handoff (pre-first-restart) |
| `HANDOFF_POST_RESTART.md` | Handoff after first restart (pre-install) |
| `HANDOFF_POST_INSTALL.md` | **This file** (post-install, ready to test) |

---

## Environment Variables

These should already be configured in user's environment:

```bash
DEEPGRAM_API_KEY=<user's key>         # Deepgram Nova-2 STT
XAI_API_KEY=<user's key>              # xAI Grok-3-fast LLM
ELEVENLABS_API_KEY=<user's key>       # ElevenLabs TTS
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE  # Denzel voice (Jamaican)
```

If any are missing, script will error immediately with clear message.

---

## Quick Command Reference

### Status & Diagnostics
```bash
# Check VB-Cable installation
venv/Scripts/python.exe check_status.py

# List all audio devices with IDs
venv/Scripts/python.exe rasta_live.py --list-devices

# Check environment variables
echo $DEEPGRAM_API_KEY
echo $XAI_API_KEY
echo $ELEVENLABS_API_KEY
```

### Testing (Step-by-Step)
```bash
# 1. Verify installation
venv/Scripts/python.exe check_status.py

# 2. Test VB-Cable routing
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000

# 3. Test TTS to headphones
venv/Scripts/python.exe rasta_live.py --test

# 4. Test TTS to VB-Cable (silent)
venv/Scripts/python.exe rasta_live.py --test --no-monitor
```

### Production Use
```bash
# Run live (VB-Cable only, no local audio)
venv/Scripts/python.exe rasta_live.py --no-monitor

# Run live (dual output: VB-Cable + headphones for monitoring)
venv/Scripts/python.exe rasta_live.py

# Manual device selection (if auto-detection fails)
venv/Scripts/python.exe rasta_live.py --twitter-device <NUM> --monitor-device <NUM>
```

---

## Troubleshooting

### If `check_status.py` shows wrong number of devices:

**No devices found:**
```bash
# Driver didn't load - restart Windows again
powershell.exe -Command "Restart-Computer -Force"
```

**More than 2 devices:**
```bash
# Something installed incorrectly - re-run uninstall
powershell.exe -ExecutionPolicy Bypass -File uninstall_vbaudio.ps1
# Then restart and reinstall
```

**Device shows "Error" status:**
- Driver corruption detected
- Try alternative: Voicemeeter (https://vb-audio.com/Voicemeeter/)

### If audio is distorted after clean install:

This would be very unusual after a fresh install. Options:
1. Check sample rate in Sound Control Panel (should be 48000 Hz)
2. Try VB-Audio Point instead (devices 40/41 from original scan)
3. Use Voicemeeter as alternative virtual audio router

### If auto-detection fails:

```bash
# List devices to find device numbers
venv/Scripts/python.exe rasta_live.py --list-devices

# Manually specify devices
venv/Scripts/python.exe rasta_live.py --twitter-device <CABLE_INPUT_NUM> --monitor-device <HEADPHONE_NUM>
```

### If Twitter doesn't see CABLE Output:

1. Restart Twitter/browser
2. Check Windows Sound Control Panel → Recording tab → Enable CABLE Output
3. Set CABLE Output volume to 100% (Properties → Levels)
4. Verify device isn't muted

### If latency is too high (>5 seconds):

- Check internet connection (Deepgram/ElevenLabs are cloud APIs)
- Try switching to `--test` mode to isolate TTS latency
- Monitor console for slow API responses

---

## Success Criteria

Everything is working perfectly when:

1. ✅ `check_status.py` shows exactly 2 VB-Cable devices (CABLE Input + CABLE Output)
2. ✅ No devices show "Error" status in output
3. ✅ `test_vbcable.py` completes without errors
4. ✅ `rasta_live.py --test` produces crystal clear Jamaican voice
5. ✅ No distortion, crackling, garbling, or audio artifacts
6. ✅ User can speak into microphone and hear Rasta voice in real-time
7. ✅ Twitter Spaces receives clean audio when using CABLE Output as microphone
8. ✅ Latency is acceptable (~2-3 seconds from speech to output)

---

## Quick Start for Next Claude Instance

**User just restarted Windows after installing fresh VB-Cable. Run these commands:**

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice

# 1. Verify clean installation (should show 2 devices)
venv/Scripts/python.exe check_status.py

# 2. Test VB-Cable routing
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000

# 3. Test TTS quality to headphones
venv/Scripts/python.exe rasta_live.py --test

# 4. Test TTS to VB-Cable (silent test)
venv/Scripts/python.exe rasta_live.py --test --no-monitor

# 5. If all tests pass, run production pipeline
venv/Scripts/python.exe rasta_live.py --no-monitor

# 6. Guide user: Set Twitter Spaces mic to "CABLE Output"
```

**Expected timeline:** ~5 minutes (verify + test + production)

---

## Notes for Next Claude Instance

### Current Status
- **Post-second-restart state:** Fresh VB-Cable installed and loaded
- **Driver state:** Clean, no conflicts expected
- **Next action:** Verify installation, then test audio quality

### What's Already Done
- ✅ All old/corrupted drivers removed
- ✅ Fresh VB-Cable installed via official installer
- ✅ Two Windows restarts completed
- ✅ Voice pipeline code is ready and tested
- ✅ All environment variables configured

### What's NOT Done Yet
- ⏳ Verification that VB-Cable installed correctly
- ⏳ Audio quality testing
- ⏳ Live pipeline testing with Twitter Spaces
- ⏳ User confirmation that audio is clear

### User Expectations
- User expects fast, automated testing
- User wants clear pass/fail on each test
- User wants to get to Twitter Spaces ASAP
- Final goal: Clean, distortion-free Rasta voice in Twitter Spaces

### Important: Sample Rate Handling
The `rasta_live.py` script handles sample rate conversion automatically:
- ElevenLabs TTS outputs 24kHz mono/stereo
- VB-Cable WASAPI expects 48kHz
- `scipy.signal.resample` converts 24kHz → 48kHz
- No user configuration needed

### Working Directory
```
Windows: C:\Users\natha\sol-cannabis\rasta-voice\
WSL:     /mnt/c/Users/natha/sol-cannabis/rasta-voice/
```

All commands use WSL path. Python runs via Windows venv: `venv/Scripts/python.exe`

---

## Final Checklist

Before marking complete, verify:

- [ ] `check_status.py` shows exactly 2 VB-Cable devices
- [ ] No "Error" status in Device Manager
- [ ] `test_vbcable.py --vb --sr 48000` completes without errors
- [ ] `rasta_live.py --test` produces clear Jamaican voice
- [ ] No distortion or audio artifacts
- [ ] User successfully tests in Twitter Spaces
- [ ] Rasta voice is clear, authentic, and properly Jamaican
- [ ] Latency is acceptable for live conversation

---

**Status:** Ready for testing and verification
**Likelihood of success:** Very high - clean install completed, just needs validation
**Estimated time to completion:** 5-10 minutes

**LET'S TEST! 🎙️🔊**
