# Windows Audio Routing - WORKING CONFIGURATION (Jan 24, 2026)

## ✅ VERIFIED WORKING SETUP

**This configuration is confirmed working as of Jan 24, 2026:**

```bash
cd rasta-voice
python start_pipeline.py
```

**Devices used:**
- Input: Device 29 (Realtek HD Audio Mic) @ 48kHz - STABLE
- Twitter: Device 16 (VB-Cable Input) @ 48kHz - STABLE
- Monitor: Device 17 (AirPods Pro) @ 48kHz - Changes on BT reconnect

**Audio flow:**
```
Laptop Mic (29) → Pipeline → VB-Cable (16) → OBS/Twitter Spaces
                               ↓
                         AirPods (17) → You hear yourself
```

## Problem Solved
Too many duplicate audio devices (19 inputs!) causing confusion. Device IDs keep changing when Bluetooth reconnects.

## What You Actually Have

### Physical Devices
- **Laptop microphone** (Intel Smart Sound / Realtek)
- **Laptop speakers** (Realtek)
- **AirPods Pro** (Bluetooth - IDs change on reconnect!)

### Virtual Devices
- **VB-Audio Virtual Cable** (one virtual audio cable for routing)
  - Has TWO endpoints:
    - **CABLE Input** (playback/output device) - Where you SEND audio TO
    - **CABLE Output** (recording/input device) - Where you CAPTURE audio FROM

## Simplified Routing for Rasta Voice

```
Your Mic → Python Pipeline → Deepgram STT → xAI → ElevenLabs TTS
                                                         ↓
                              ┌──────────────────────────┴────────────────────┐
                              ↓                                               ↓
                      CABLE Input (output dev)                    AirPods (output dev)
                              ↓                                    You hear yourself!
                      VB-Cable virtual wire
                              ↓
                      CABLE Output (input dev)
                              ↓
                      OBS/Twitter Spaces captures this
```

## Recommended Setup (Stable Device IDs)

**Use these specific devices:**

| Purpose | Device Name | Typical ID | Notes |
|---------|-------------|------------|-------|
| **Microphone** | Realtek HD Audio Mic | 29 | Stable ID, works reliably |
| **Stream Output** | CABLE Input 48kHz | 16 | VB-Cable for OBS/Twitter |
| **Monitoring** | AirPods Headphones | 17 | CHANGES on BT reconnect! |

**Alternative if AirPods problematic:**
- Use laptop speakers for monitoring (not ideal but stable ID)
- Or don't monitor (--no-monitor flag)

## Why So Many Devices?

Windows creates multiple "views" of the same hardware:
- **DirectSound** devices (low IDs: 0-10)
- **MME** devices (mid IDs: 8-15)
- **WASAPI** devices (high IDs: 15+) ← **Use these! Lower latency**

Same physical mic appears 3x with different IDs!

## How to Fix Device ID Changes

**Problem:** AirPods reconnecting shifts all device IDs

**Solutions:**
1. **Use the dashboard mic selector** to easily switch when IDs change
2. **Disable unused audio devices** in Windows Device Manager:
   - Disable: Stereo Mix, PC Speaker, extra Realtek outputs
   - Keep: One laptop mic, one speaker, VB-Cable, AirPods
3. **Keep AirPods always connected** during streaming sessions

## Cleaning Up Windows Audio

Run this to see what can be disabled:

```powershell
Get-PnpDevice -Class AudioEndpoint | Select-Object FriendlyName, Status
```

Disable duplicates in: Device Manager → Sound, video and game controllers

## Simplified Pipeline Start Command

```bash
# Stable setup without AirPods monitoring
./venv/Scripts/python.exe rasta_live.py \
  --input-device 29 \
  --twitter-device 16 \
  --no-monitor

# Or with AirPods (device 17 may change!)
./venv/Scripts/python.exe rasta_live.py \
  --input-device 29 \
  --twitter-device 16 \
  --monitor-device 17
```

## Testing Your Setup

1. Open Windows Sound Settings
2. **Input:** Select "Microphone (Realtek HD Audio)" - speak and watch blue bar move
3. **Output:** Select "Headphones (AirPods Pro)" - play test sound
4. Start pipeline with above command
5. Speak - hear rasta voice in AirPods

## OBS Configuration

When you add OBS:
- **Desktop Audio:** CABLE Output (captures what pipeline sends to CABLE Input)
- **Mic/Aux:** Muted (don't double-capture)

That's it! Simple: Pipeline → VB-Cable → OBS → Stream
