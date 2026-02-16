# Rasta Voice Pipeline

⚠️ **CRITICAL:** This pipeline is optimized for the Windows laptop, but the streaming agent may run it on other hosts when needed. Non-Windows hosts require equivalent audio routing (no VB-Cable/WASAPI), so adapt device setup accordingly.

Real-time voice transformer for Twitter Spaces and livestreaming. Transforms operator's voice into the "Funny Ganja Rasta Mon" character - the brand personality for @ganjamonai.

**Character:** Stereotypical Western Jamaican stoner rasta - jovial, constantly laughing, chill vibes, Bob Marley meets Cheech & Chong. Not politically correct, but ENTERTAINING!

## Pipeline Architecture

```
Laptop Mic → Deepgram STT → Groq LLM (Patois Translation, llama-3.1-8b-instant default) → ElevenLabs TTS → VB-Cable → Twitter Spaces
                                                                                      ↓
                                                                               Headphones (monitoring)
```

Alternate (dashboard): `grok_translate_dashboard.py` can use xAI Grok via `https://api.x.ai/v1` when configured.

## Key Files

| File | Purpose |
|------|---------|
| `rasta_live.py` | Main ElevenLabs pipeline with emotion tags |
| `start_pipeline.py` | Pipeline launcher (prevents duplicates) |
| `dashboard_working.py` | Web dashboard for pipeline control |
| `rasta_live_rvc.py` | RVC voice conversion pipeline (experimental) |
| `rasta_ralph_loop.py` | Iterative voice perfection system |
| `docs/RALPH_LOOP_REFERENCE.md` | Ralph Loop methodology documentation |

## Quick Start

**RECOMMENDED - prevents duplicate processes:**
```bash
cd C:\Users\natha\sol-cannabis\rasta-voice
python start_pipeline.py
```

**From WSL/Claude Code:**
```bash
powershell.exe -Command "cd C:\Users\natha\sol-cannabis\rasta-voice; python start_pipeline.py"
```

**Non-Windows hosts:** `cd /path/to/sol-cannabis/rasta-voice` then `python start_pipeline.py` (use host-specific audio routing).

## Voice Settings (Optimized for Expressiveness)

- **Voice:** ElevenLabs "Denzel" - Jamaican, Raspy, Deep
- **Model:** `eleven_v3` (supports emotion tags like `[laughs]`, `[chuckles]`, `[relaxed]`)
- **Stability:** 0.0 (maximum expressiveness - full creative mode)
- **Similarity Boost:** 0.5 (allows character variation)
- **Style:** 1.0 (MAXED - exaggerates emotion tags for character)

### Emotion Tags (Used by Groq LLM)

The system prompt instructs the LLM to add emotion tags sparingly:
- **Chill/Stoner:** `[relaxed]`, `[laid back]`, `[mellow]`, `[chill]`, `[dreamy]`
- **Laughter:** `[chuckles]`, `[laughs]`, `[giggles]`, `[chuckles warmly]`, `[laughs heartily]`
- **Expressive:** `[excited]`, `[sarcastic]`, `[frustrated]`, `[contemplative]`, etc.

**ONE emotion tag at the start** of each response - don't overuse!

## Pipeline Latency & Batching

**SmartBatcher Settings** (`rasta_live.py:517-521`):
```python
SILENCE_TIMEOUT = 2.0    # Flush after 2s silence
MAX_BATCH_DURATION = 8.0 # Flush after 8s continuous speech
MIN_BATCH_CHARS = 60     # Don't flush tiny fragments
MAX_BATCH_CHARS = 200    # FORCE flush at 200 chars (prevents huge TTS delays)
```

**Key Gotchas:**
1. **Deepgram accumulates continuous speech** - reading without pauses creates ONE massive transcript (500+ chars)
2. **Must split long transcripts** on sentence boundaries before batching
3. **`voice_config.json` OVERRIDES code defaults** - always check this file first!
4. **stability is counterintuitive:** `stability=1.0` = MONOTONE, `stability=0.0` = EXPRESSIVE

**voice_config.json (CORRECT settings):**
```json
{
  "stability": 0.0,
  "style": 1.0,
  "temperature": 0.9
}
```

## Audio Device Configuration (Windows WASAPI)

This section applies to Windows hosts only. If running elsewhere, skip and configure equivalent audio routing for your OS.

**CRITICAL - CORRECT DEVICE IDS (Jan 2026):**

| Device ID | Name | Purpose | Stability |
|-----------|------|---------|-----------|
| 29 | Realtek HD Audio Mic | Input (laptop mic) | STABLE |
| 16 | CABLE Input 48kHz | Output to stream | STABLE |
| 17 | Headphones (AirPods Pro) | Monitoring | Changes on BT reconnect |

**WRONG DEVICE IDS (DO NOT USE):**
- Device 18 = **Laptop Speakers** (causes feedback loop!)
- Device 19 = **Microphone** (not headphones!)
- Device 21 = Intel mic (works but 44.1kHz, prefer device 29 @ 48kHz)

**Running the Pipeline (RECOMMENDED METHOD):**
```bash
cd rasta-voice
python start_pipeline.py  # Auto-detects default mic + headphones
```

Uses:
- Input: Windows default microphone (auto-detected)
- Twitter: Device 16 (VB-Cable 48kHz) - hardcoded, stable
- Monitor: Auto-detects headphones (searches for "headphone" @ 48kHz)

## Dashboard

- **URL:** http://localhost:8085
- **Features:** Start/Stop pipeline, live transcripts, voice controls
- **API Endpoints:**
  - `POST /api/start` - Start pipeline with correct audio devices
  - `POST /api/stop` - Stop pipeline
  - `GET /api/status` - Check if running
  - `GET /api/transcripts` - Get transcript history

## Audio Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Audio through laptop speakers | Wrong device ID for monitoring | Use device 17 (AirPods), NOT 18 (speakers) |
| Feedback loop / echo | Speakers feeding back to mic | Ensure monitoring uses headphones, not speakers |
| Can't hear yourself | AirPods device ID changed | Use dashboard mic selector or `--list-devices` |
| Mic not picking up voice | Wrong input device | Set Windows default mic or use device 29 |
| Pipeline crashes immediately | Wrong sample rate for device | Pipeline now auto-detects sample rate ✅ |
| Too many devices showing | Windows duplicates | Use dashboard filtered list (only real mics) |

## PortAudio -9999 Error Fix

**Symptom:** `Error opening InputStream: Unanticipated host error [PaErrorCode -9999]` on ALL microphones

**Root Cause:** Windows **Microphone Privacy** was turned OFF.

**Diagnosis Steps:**
1. Open `ms-settings:privacy-microphone`
2. Check "Microphone access" is **ON**
3. Check "Let apps access your microphone" is **ON**

## OBS Studio Configuration

**Version:** 32.0.4
**WebSocket:** Port 4455, Password: `h2LDVnmFYDUpSVel`

**Audio Sources:**
| Source | Device | Purpose | Default State |
|--------|--------|---------|---------------|
| Desktop Audio | CABLE Output (VB-Audio Virtual Cable) | Captures rasta TTS output | **MUST BE UNMUTED** |
| Mic/Aux | Default | Not used for rasta voice | Muted |

**Browser Sources (URLs from Chromebook server):**
- Mon Plant Cam: `http://192.168.125.128:8000/api/webcam/stream`
- Sensor Bar: `http://192.168.125.128:8000/overlay/bar`
- Commentary Overlay: `http://192.168.125.128:8000/overlay/commentary`

### Starting OBS Correctly

**IMPORTANT:** OBS must be started from its bin directory to find locale files:
```bash
cd "/c/Program Files/obs-studio/bin/64bit" && ./obs64.exe &
```

### OBS WebSocket Commands (Python)

```python
from obswebsocket import obsws, requests

# Connect
ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel')
ws.connect()

# Unmute VB-Cable (REQUIRED for rasta voice to stream!)
ws.call(requests.SetInputMute(inputName='Desktop Audio', inputMuted=False))

ws.disconnect()
```

## Complete System Restore Procedure

⚠️ **RUN THESE COMMANDS ON THE HOST RUNNING THE RASTA PIPELINE (Windows examples below).**

1. **Start Pipeline:**
   ```bash
   cd /c/Users/natha/sol-cannabis/rasta-voice
   ./venv/Scripts/python.exe start_pipeline.py
   ```

2. **Start OBS:**
   ```bash
   cd "/c/Program Files/obs-studio/bin/64bit" && ./obs64.exe &
   ```

3. **Unmute VB-Cable in OBS:**
   ```python
   from obswebsocket import obsws, requests
   ws = obsws('localhost', 4455, 'h2LDVnmFYDUpSVel')
   ws.connect()
   ws.call(requests.SetInputMute(inputName='Desktop Audio', inputMuted=False))
   ws.disconnect()
   ```

4. **Verify Audio Flow:**
   ```
   Your Mic → Deepgram STT → Groq LLM (Patois) → ElevenLabs TTS
                                                        ↓
                                  ┌─────────────────────┴─────────────────────┐
                                  ↓                                           ↓
                        Device 18: VB-Cable Input                   Device 19: Headphones
                                  ↓                                    (you hear yourself)
                        VB-Cable Virtual Cable
                                  ↓
                        OBS Desktop Audio (CABLE Output)
                                  ↓
                        Restream → Twitter/X + Twitch
   ```

5. **Test by speaking** - you should hear rasta voice in headphones AND see audio meters move in OBS.
