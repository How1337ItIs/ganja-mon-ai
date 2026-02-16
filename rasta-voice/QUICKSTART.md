# Rasta Voice Pipeline - Quick Start

## Start Everything (One Command)

```bash
cd C:\Users\natha\sol-cannabis\rasta-voice
python start_pipeline.py
```

That's it! Pipeline will:
- Auto-detect your Windows default microphone
- Output to VB-Cable (device 16) for streaming
- Auto-detect headphones for monitoring

## Open Dashboard

```bash
python dashboard_working.py
```

Then open: http://localhost:8085

## Verify It's Working

1. **Speak into your laptop microphone**
2. **Listen in your AirPods** - you should hear rasta voice after ~3-5 seconds
3. **Check dashboard** - transcripts should appear

## If Something Goes Wrong

### Audio through laptop speakers (feedback loop!)
**Fix:** Restart pipeline - device IDs probably changed
```bash
python start_pipeline.py
```

### Can't hear yourself
**Fix:** Check AirPods are connected and set as default output in Windows Sound Settings

### Mic not picking up voice
**Fix:**
1. Windows Sound Settings → Input
2. Select "Microphone (Realtek HD Audio)"
3. Speak - blue bar should move
4. If not, increase volume slider

### Too many devices in dashboard dropdown
**This is normal** - Windows shows duplicates. Look for:
- "Realtek" or "Intel" for laptop mic
- "Headset" or "Input" for AirPods mic (if you want to use that)

## Device IDs Reference

**Current stable IDs (Jan 2026):**
- 29 = Realtek laptop mic (STABLE)
- 16 = VB-Cable Input for streaming (STABLE)
- 17 = AirPods headphones (CHANGES on reconnect!)

**To see all devices:**
```bash
python rasta_live.py --list-devices
```

## For OBS/Streaming

In OBS:
1. Desktop Audio source → Select "CABLE Output (VB-Audio Virtual Cable)"
2. Mic/Aux → Muted (don't double-capture)

In Twitter Spaces:
1. Microphone → Select "CABLE Output (VB-Audio Virtual Cable)"

## Full Documentation

- `CLAUDE.md` - Complete system documentation
- `AUDIO_SETUP.md` - Detailed audio routing guide
- `docs/RALPH_LOOP_REFERENCE.md` - Ralph Loop methodology
