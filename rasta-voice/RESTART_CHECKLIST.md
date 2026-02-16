# Post-Restart Quick Checklist

**Read full context**: `HANDOFF_VBCABLE_FIX.md`

## Immediate Steps After Windows Restart

### 1. Reinstall VB-Cable (5 minutes)
```
1. Download: https://vb-audio.com/Cable/
2. Extract ZIP
3. Right-click VBCABLE_Setup_x64.exe → Run as administrator
4. Click "Install Driver"
5. Restart Windows again
```

### 2. Verify Clean Install
```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
venv/Scripts/python.exe test_vbcable.py --list
```
Should show CABLE Input and CABLE Output with NO errors.

### 3. Test Audio Quality
```bash
# Test tone (should be clean 440Hz beep)
venv/Scripts/python.exe test_vbcable.py --vb --sr 48000

# Test TTS (should sound perfect)
venv/Scripts/python.exe test_tts_simple.py
```

### 4. Run Live Pipeline
```bash
venv/Scripts/python.exe rasta_live.py --no-monitor
```

### 5. Configure Twitter Spaces
- Set microphone to "CABLE Output (VB-Audio Virtual Cable)"
- Speak into your real mic
- Rasta voice should come through clearly

---

## If Still Having Issues

Tell Claude: "Read HANDOFF_VBCABLE_FIX.md and continue from Step X"
