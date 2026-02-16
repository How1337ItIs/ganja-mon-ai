# Rasta Voice Pipeline - Changes Jan 24, 2026

## Critical Fixes

### 1. Audio Routing Corrected
**Problem:** Audio playing through laptop speakers instead of headphones, causing feedback loop

**Root cause:** Device IDs were wrong
- Device 18 = Laptop speakers (NOT VB-Cable!)
- Device 19 = Microphone (NOT headphones!)

**Solution:** Updated to correct stable device IDs
- Device 16 = VB-Cable Input (for streaming) ✅
- Device 17 = AirPods headphones (for monitoring) ✅
- Device 29 = Realtek mic (for input) ✅

### 2. Sample Rate Auto-Detection
**Problem:** Pipeline crashed with AirPods mic due to sample rate mismatch (16kHz vs 48kHz)

**Solution:** Added auto-detection in `rasta_live.py` lines 994-1001
```python
device_info = sd.query_devices(args.input_device)
device_sr = int(device_info['default_samplerate'])
config.sample_rate = device_sr
```

### 3. Deepgram Endpointing Improved
**Problem:** Sentences being cut off too quickly during natural pauses

**Solution:** Increased endpointing from 800ms → 1500ms
- Allows 1.5 second pauses before finalizing transcript
- Added `smart_format=true` for better punctuation

### 4. Dashboard Microphone Selector Added
**Problem:** Too many device options (19+), hard to identify correct mic

**Solution:**
- Added `/api/devices` endpoint with filtering (only real microphones)
- Added dropdown UI to select input device
- Added `/api/restart?device_id=X` to switch mics on the fly
- Added audio level meters (input/output visualization)

### 5. Device List Filtering
**Excluded from dropdown:**
- Virtual devices: CABLE Output, Stereo Mix
- System devices: Sound Mapper, Primary Driver
- Duplicate entries (same hardware, different APIs)

**Result:** 19 devices → ~4 real microphone choices

### 6. Simplified start_pipeline.py
**Changes:**
- Now uses Windows default microphone (no hardcoded ID)
- Auto-detects headphones by name pattern
- Only hardcodes VB-Cable (device 16) - most stable

## Files Modified

| File | Changes |
|------|---------|
| `rasta_live.py` | Sample rate auto-detection, improved Deepgram settings |
| `dashboard_working.py` | Added /api/devices, /api/restart, device filtering |
| `dashboard.html` | Added mic selector dropdown, audio level meters |
| `start_pipeline.py` | Updated device IDs, added auto-detection |
| `CLAUDE.md` | Documented correct device IDs, troubleshooting guide |
| `AUDIO_SETUP.md` | Added verified working configuration |
| `QUICKSTART.md` | Created quick reference guide |

## Files Created

- `test_audio_pipeline.py` - End-to-end pipeline test script
- `AUDIO_SETUP.md` - Comprehensive audio routing guide
- `QUICKSTART.md` - Quick start reference
- `CHANGELOG_2026-01-24.md` - This file

## Lessons Learned

1. **Always test browser UIs** - Don't assume they work
2. **Device IDs are unstable** - Bluetooth devices change IDs on reconnect
3. **Windows audio is messy** - Same hardware appears 3x with different IDs
4. **Auto-detection > hardcoding** - Reduces brittleness
5. **Filter device lists** - Users can't parse 19 options
6. **Test end-to-end** - Component tests aren't enough

## Verified Working

✅ Mic input from Realtek device 29
✅ TTS output to VB-Cable device 16 (for streaming)
✅ Monitoring output to AirPods device 17 (hear yourself)
✅ Dashboard mic selector with filtered list
✅ Auto-detection of default mic and headphones
✅ No feedback loop
✅ Proper dual output using threading

## Known Issues / Future Work

- [ ] AirPods device ID (17) changes on Bluetooth reconnect - need to re-select in dashboard
- [ ] Dashboard crashes when accessed from WSL (network isolation) - use Windows browser
- [ ] Too many background bash processes accumulating - need cleanup
- [ ] Audio level meters show simulated data - could read real levels from pipeline logs
- [ ] Emotion tags might still be spoken sometimes - need to verify eleven_v3 model behavior

## Quick Recovery Commands

If pipeline stops working:
```bash
cd C:\Users\natha\sol-cannabis\rasta-voice
python start_pipeline.py
```

If dashboard crashes:
```bash
taskkill /F /IM python3.13.exe
python dashboard_working.py
```

Check what's running:
```bash
tasklist | findstr python
```
