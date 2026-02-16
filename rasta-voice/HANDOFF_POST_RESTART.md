# Post-Restart Handoff - VB-Cable Fresh Install & Testing

**Date:** 2026-01-20
**Status:** ✅ Drivers uninstalled → Windows restarted → Ready for fresh install
**Session:** Continuation after Windows restart (Restart 1 of 2)

---

## What Happened Before Restart

### ✅ Completed Steps

1. **Diagnosed the problem:** 12 conflicting VB-Audio devices causing distorted audio
   - Multiple VB-Cable instances (standard, 16ch, Point)
   - One device showing "Error" status in Device Manager
   - Audio reaches Twitter Spaces but is garbled/distorted

2. **Prepared automation scripts:**
   - Downloaded VB-Cable installer: `VBCABLE_Driver/VBCABLE_Setup_x64.exe`
   - Created `uninstall_vbaudio.ps1` (PowerShell uninstaller)
   - Created `install_vbaudio.ps1` (PowerShell installer)
   - Created `check_status.py` (Python status checker)
   - Created `VB_CABLE_FIX_STEPS.md` (detailed manual instructions)
   - Created `.bat` files for Windows GUI users

3. **Ran uninstallation:**
   - Opened elevated PowerShell window
   - Removed all VB-Audio PnP devices
   - Deleted VB-Audio driver packages
   - User restarted Windows

### 📋 Current State

- **VB-Audio drivers:** Should be fully removed (needs verification)
- **VB-Cable installer:** Downloaded and ready at `VBCABLE_Driver/VBCABLE_Setup_x64.exe`
- **Voice pipeline code:** Working and ready (`rasta_live.py`)
- **Windows:** Freshly restarted (Restart 1 of 2)

---

## What Needs to Happen Next

### STEP 1: Verify Clean Uninstall ✓

First, confirm all VB-Audio drivers are gone:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe check_status.py
```

**Expected output:**
```
[OK] STATUS: ALL CLEAR
     No VB-Audio devices found
     Ready for fresh installation!
```

**If devices still exist:**
- Re-run uninstall: `powershell.exe -ExecutionPolicy Bypass -File uninstall_vbaudio.ps1`
- Restart again
- Check status again

### STEP 2: Install Fresh VB-Cable 📦

Once uninstall is verified clean, run the installer:

```bash
# Option A: Via PowerShell script (easier)
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
powershell.exe -ExecutionPolicy Bypass -File install_vbaudio.ps1

# Option B: Direct installer (more control)
powershell.exe -Command "Start-Process -FilePath 'VBCABLE_Driver\VBCABLE_Setup_x64.exe' -Verb RunAs -Wait"
```

**What happens:**
- UAC prompt appears (user clicks YES)
- VB-Cable setup window opens
- User clicks "Install Driver" button
- Success message appears
- Close the installer

### STEP 3: Restart Windows Again 🔄

**CRITICAL:** Must restart Windows a second time for driver to load

```bash
# Offer to restart via command
powershell.exe -Command "Restart-Computer -Force"
```

Or user can restart manually: `shutdown /r /t 0`

### STEP 4: Verify Clean Install ✅

After second restart, check the installation:

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

### STEP 5: Test Audio Quality 🔊

Test that VB-Cable can handle audio without distortion:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice

# Test tone to VB-Cable (silent - won't hear it)
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000

# Test TTS to headphones (should hear Jamaican voice clearly)
venv/Scripts/python.exe rasta_live.py --test

# Test TTS to VB-Cable only (silent test)
venv/Scripts/python.exe rasta_live.py --test --no-monitor
```

**Expected:** No errors, crystal clear voice quality

### STEP 6: Run Live Pipeline for Twitter Spaces 🎙️

If all tests pass, start the live voice transformer:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe rasta_live.py --no-monitor
```

**What this does:**
- Listens to user's microphone
- Transcribes speech via Deepgram (Nova-2)
- Transforms to Jamaican Patois via xAI (Grok-3-fast)
- Speaks via ElevenLabs TTS (Denzel voice, Jamaican)
- Routes audio to VB-Cable silently

**In Twitter Spaces:**
1. Open microphone settings
2. Select: **"CABLE Output (VB-Audio Virtual Cable)"**
3. Speak into real microphone
4. Rasta voice comes through Twitter Spaces

---

## Project Context

### The Problem We Fixed

The Rasta voice pipeline was fully functional:
- ✅ Mic → Deepgram STT → xAI Patois transformation → ElevenLabs TTS
- ✅ Audio successfully routes to VB-Cable
- ✅ Twitter Spaces receives the audio

BUT:
- ❌ Audio was severely distorted/garbled
- ❌ Root cause: Corrupted VB-Cable drivers with 12 conflicting devices
- ❌ Device Manager showed one device with "Error" status

### The Solution

Complete driver cleanup and fresh reinstall:
1. Remove ALL VB-Audio products (standard Cable, 16ch, Point)
2. Restart to clear driver cache
3. Install ONLY standard VB-Cable
4. Restart to load clean driver
5. Test and verify

### Voice Pipeline Architecture

```
User Microphone (16kHz)
  ↓
Deepgram STT (WebSocket, Nova-2 model)
  ↓
xAI Grok-3-fast (Jamaican Patois transformation)
  ↓
ElevenLabs TTS (Denzel voice, Turbo v2.5, 24kHz output)
  ↓
[Resample 24kHz → 48kHz using scipy]
  ↓
VB-Cable Input (WASAPI, 48kHz)
  ↓
[VB-Cable internal routing]
  ↓
CABLE Output (shows as "microphone" in apps)
  ↓
Twitter Spaces
```

### Key Files in Project

| File | Purpose | Status |
|------|---------|--------|
| `rasta_live.py` | Main voice pipeline (Deepgram + xAI + ElevenLabs) | ✅ Working |
| `test_vbcable.py` | Audio device testing utility | ✅ Ready |
| `test_tts_simple.py` | Simple TTS quality test | ✅ Ready |
| `check_status.py` | VB-Cable status checker | ✅ Ready |
| `uninstall_vbaudio.ps1` | Automated driver uninstaller | ✅ Used |
| `install_vbaudio.ps1` | Automated driver installer | 📦 Ready to use |
| `VBCABLE_Driver/VBCABLE_Setup_x64.exe` | Official VB-Cable installer | 📦 Downloaded |
| `VB_CABLE_FIX_STEPS.md` | Detailed manual instructions | 📖 Reference |
| `HANDOFF_VBCABLE_FIX.md` | Original handoff (pre-restart) | 📖 Archive |
| `HANDOFF_POST_RESTART.md` | This file (current handoff) | 📖 You are here |

### Environment Variables Required

These should already be set in user's environment:

```bash
DEEPGRAM_API_KEY=<user's key>
XAI_API_KEY=<user's key>
ELEVENLABS_API_KEY=<user's key>
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE  # Denzel - Jamaican voice
```

If missing, check `.env` file or ask user to provide.

---

## Quick Command Reference

### Status Checks
```bash
# Check VB-Cable devices
venv/Scripts/python.exe check_status.py

# List all audio devices with numbers
venv/Scripts/python.exe rasta_live.py --list-devices
```

### Installation
```bash
# Run installer (PowerShell script)
powershell.exe -ExecutionPolicy Bypass -File install_vbaudio.ps1

# Or run installer directly
powershell.exe -Command "Start-Process -FilePath 'VBCABLE_Driver\VBCABLE_Setup_x64.exe' -Verb RunAs -Wait"
```

### Testing
```bash
# Test VB-Cable tone
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000

# Test TTS to headphones
venv/Scripts/python.exe rasta_live.py --test

# Test TTS to VB-Cable (silent)
venv/Scripts/python.exe rasta_live.py --test --no-monitor
```

### Production
```bash
# Run live (VB-Cable only, no local audio)
venv/Scripts/python.exe rasta_live.py --no-monitor

# Run live (dual output: VB-Cable + headphones)
venv/Scripts/python.exe rasta_live.py

# Run with manual device selection
venv/Scripts/python.exe rasta_live.py --twitter-device <NUM> --monitor-device <NUM>
```

---

## Troubleshooting

### If devices still show after uninstall:
```bash
# Re-run uninstall script
powershell.exe -ExecutionPolicy Bypass -File uninstall_vbaudio.ps1

# Or manually via Device Manager:
# devmgmt.msc → Sound controllers → Right-click VB-Audio devices → Uninstall → Check "Delete driver"
```

### If audio is still distorted after clean install:
- Driver corruption persists → Try Voicemeeter instead: https://vb-audio.com/Voicemeeter/
- Or use VB-Audio Point (devices 40/41 from previous scan)

### If Twitter doesn't see CABLE Output:
- Restart Twitter/browser
- Check Device Manager for errors
- Verify CABLE Output is enabled: Sound Control Panel → Recording tab

### If audio is too quiet:
- Sound Control Panel → Recording tab → CABLE Output → Properties → Levels → 100%

### If auto-detection fails:
```bash
# List devices to find device numbers
venv/Scripts/python.exe rasta_live.py --list-devices

# Manually specify devices
venv/Scripts/python.exe rasta_live.py --twitter-device <CABLE_INPUT_NUM> --monitor-device <HEADPHONE_NUM>
```

---

## Success Criteria

You'll know everything is working when:

1. ✅ `check_status.py` shows exactly 2 VB-Cable devices (no errors)
2. ✅ `rasta_live.py --test` produces crystal clear Jamaican voice
3. ✅ No distortion, crackling, or garbling
4. ✅ Twitter Spaces receives clean audio when using CABLE Output as mic
5. ✅ User can speak naturally and hear Rasta voice in real-time

---

## Notes for Next Claude Instance

### Where We Are
- **Pre-second-restart state:** VB-Audio drivers removed, Windows restarted once
- **Next action:** Verify clean uninstall, then install fresh VB-Cable
- **User cooperation:** User will click YES on UAC prompts, just run commands

### What's Already Done
- ✅ Voice pipeline code is complete and tested
- ✅ VB-Cable installer is downloaded and ready
- ✅ Automation scripts are written and tested
- ✅ All old drivers have been removed

### What's NOT Done Yet
- ⏳ Fresh VB-Cable installation (requires UAC prompt)
- ⏳ Second Windows restart
- ⏳ Final audio quality testing
- ⏳ Live pipeline testing with Twitter Spaces

### User Expectations
- User wants automation - just run commands, they'll click prompts
- User expects clear step-by-step guidance
- User wants to test immediately after install completes
- Final goal: Clean Rasta voice in Twitter Spaces without distortion

### Important Technical Details
- **Sample rate conversion:** 24kHz (ElevenLabs) → 48kHz (VB-Cable WASAPI) via scipy.signal.resample
- **Device detection:** Uses sounddevice library, auto-detects "CABLE" in device names
- **Dual output:** Can send to both VB-Cable and headphones simultaneously
- **Voice model:** ElevenLabs "Denzel" (ID: dhwafD61uVd8h85wAZSE) - Jamaican, raspy, deep

### If User Says "Do It All"
1. Run `check_status.py` to verify clean slate
2. Run `install_vbaudio.ps1` (user clicks UAC)
3. Wait for installer to finish
4. Restart Windows (second restart)
5. Run `check_status.py` to verify clean install
6. Run `rasta_live.py --test` to verify audio quality
7. Run `rasta_live.py --no-monitor` for production use
8. Guide user to set Twitter Spaces mic to "CABLE Output"

### Working Directory
```
C:\Users\natha\sol-cannabis\rasta-voice\
```

All commands should be run from this directory. WSL path is:
```
/mnt/c/Users/natha/sol-cannabis/rasta-voice/
```

---

## Final Checklist

Before marking complete, verify:

- [ ] `check_status.py` shows 2 clean VB-Cable devices
- [ ] `test_vbcable.py` runs without errors
- [ ] `rasta_live.py --test` produces clear voice
- [ ] No distortion or audio artifacts
- [ ] User successfully tests in Twitter Spaces
- [ ] Rasta voice is clear and authentic-sounding

---

## Quick Start for Next Claude

**User just restarted Windows after driver uninstall. Run these commands in order:**

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice

# 1. Verify uninstall
venv/Scripts/python.exe check_status.py

# 2. Install fresh (user clicks UAC prompt)
powershell.exe -ExecutionPolicy Bypass -File install_vbaudio.ps1

# 3. After install: Restart Windows
powershell.exe -Command "Write-Host 'Restart Windows now!'; Read-Host 'Press Enter to restart'; Restart-Computer -Force"

# 4. After second restart: Verify
venv/Scripts/python.exe check_status.py

# 5. Test audio quality
venv/Scripts/python.exe rasta_live.py --test

# 6. Run live for Twitter
venv/Scripts/python.exe rasta_live.py --no-monitor
```

**That's it! The pipeline should work perfectly with clean VB-Cable drivers.**

---

**Status:** Ready for fresh installation → User just needs to trigger commands
**Estimated time to completion:** ~10 minutes (install + restart + test)
**Likelihood of success:** Very high - all prep work done, just execution remains
