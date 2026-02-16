# VB-Cable Fix - Step-by-Step Guide

**Status:** Ready to execute
**Date:** 2026-01-20

---

## What I've Prepared For You

I've automated as much as possible. Here's what's ready:

✅ **Downloaded:** VB-Cable installer (C:\Users\natha\sol-cannabis\rasta-voice\VBCABLE_Driver\VBCABLE_Setup_x64.exe)
✅ **Created:** Automated uninstall script (uninstall_vbaudio.ps1)
✅ **Created:** Automated install script (install_vbaudio.ps1)

---

## STEP 1: Uninstall VB-Audio Drivers

**Open PowerShell as Administrator:**
1. Press `Win + X`
2. Click "Windows PowerShell (Admin)" or "Terminal (Admin)"

**Run the uninstall script:**
```powershell
cd C:\Users\natha\sol-cannabis\rasta-voice
.\uninstall_vbaudio.ps1
```

**What it does:**
- Finds all VB-Audio devices
- Shows them in a table
- Asks for confirmation
- Removes all drivers
- Offers to restart Windows

**Answer 'y' to both prompts** (uninstall and restart)

---

## STEP 2: After First Restart

After Windows restarts, verify VB-Cable is gone:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe -c "import sounddevice as sd; devices = [(i, d['name']) for i, d in enumerate(sd.query_devices()) if 'CABLE' in d['name'].upper()]; print('VB-Audio devices found:' if devices else 'All clear!'); [print(f'  {i}: {name}') for i, name in devices]"
```

**Expected:** Should say "All clear!" with no devices listed

---

## STEP 3: Install VB-Cable Fresh

**Open PowerShell as Administrator again:**
```powershell
cd C:\Users\natha\sol-cannabis\rasta-voice
.\install_vbaudio.ps1
```

**What it does:**
- Runs VBCABLE_Setup_x64.exe with admin rights
- GUI will open - click "Install Driver"
- Wait for success message
- Offers to restart Windows

**Answer 'y' to restart**

---

## STEP 4: After Second Restart - Verify Clean Install

Run this to see the new clean VB-Cable devices:

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe rasta_live.py --list-devices
```

**Expected:** Should see exactly 2 VB-Cable devices:
- CABLE Input (VB-Audio Virtual Cable) - OUTPUT device
- CABLE Output (VB-Audio Virtual Cable) - INPUT device

---

## STEP 5: Test VB-Cable Audio Quality

```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000
```

**Expected:** Should run without errors (you won't hear anything unless monitoring CABLE Output)

---

## STEP 6: Test TTS Pipeline

Test that the voice sounds good to headphones:

```bash
venv/Scripts/python.exe rasta_live.py --test
```

**Expected:** You should hear clear Jamaican voice through your headphones, NO distortion

---

## STEP 7: Run Live Pipeline for Twitter Spaces

```bash
venv/Scripts/python.exe rasta_live.py --no-monitor
```

**What this does:**
- Listens to your microphone
- Transforms speech to Jamaican Patois via xAI
- Speaks through ElevenLabs (Denzel voice)
- Routes audio to VB-Cable (silent on your end)

**In Twitter Spaces:**
1. Click microphone settings
2. Select **"CABLE Output (VB-Audio Virtual Cable)"** as your mic
3. Speak into your real mic
4. Your Rasta voice should come through in Twitter!

---

## Alternative Commands

### If you want to hear yourself while streaming:
```bash
venv/Scripts/python.exe rasta_live.py
```
(Outputs to both VB-Cable AND your headphones)

### If auto-detection fails:
```bash
# List devices with numbers
venv/Scripts/python.exe rasta_live.py --list-devices

# Manually specify devices
venv/Scripts/python.exe rasta_live.py --twitter-device <NUM> --monitor-device <NUM>
```

---

## Troubleshooting

### If audio is distorted after reinstall:
The driver is still corrupted. Repeat STEP 1-3 or try:
- **Voicemeeter:** https://vb-audio.com/Voicemeeter/ (more robust alternative)
- **VB-Audio Point:** Already have this installed, can try using device 40

### If audio is too quiet in Twitter:
1. Open Sound Control Panel (Win + R → `mmsys.cpl`)
2. Recording tab
3. Right-click "CABLE Output" → Properties
4. Levels tab → Set to 100%

### If Twitter doesn't see CABLE Output:
- Restart Twitter
- Unplug/replug headphones to refresh audio devices
- Check Device Manager for any errors

---

## Quick Reference

| File | Purpose |
|------|---------|
| `uninstall_vbaudio.ps1` | Removes all VB-Audio drivers |
| `install_vbaudio.ps1` | Installs VB-Cable fresh |
| `rasta_live.py` | Main voice pipeline (Deepgram + xAI + ElevenLabs) |
| `test_vbcable.py` | Audio device testing |
| `VB_CABLE_FIX_STEPS.md` | This file |

---

## Environment Variables Required

Make sure these are set in your terminal:
```bash
export DEEPGRAM_API_KEY=your_key
export XAI_API_KEY=your_key
export ELEVENLABS_API_KEY=your_key
export ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE
```

Or add them to `.env` file in rasta-voice folder.

---

**Ready to start? Run STEP 1!**
