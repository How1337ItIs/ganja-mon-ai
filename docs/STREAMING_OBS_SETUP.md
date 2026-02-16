# OBS Streaming Setup - Grok & Mon
## Live Cannabis Grow Stream with AI Voice

---

## Overview

This guide sets up OBS Studio for streaming Mon's grow to Twitter Spaces, YouTube, or Twitch with:
- Live webcam feed of the plant
- Real-time sensor overlay
- Grok AI commentary (text and voice)
- Rasta AI voice via VB-Cable

```
┌─────────────────────────────────────────────────────────────┐
│                      OBS STUDIO                              │
│  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │    WEBCAM FEED      │  │      SENSOR OVERLAY         │   │
│  │   (Plant Camera)    │  │   Temp: 78F  RH: 55%        │   │
│  │                     │  │   VPD: 1.05  Day: 15        │   │
│  │        🌿           │  │   Stage: VEGETATIVE         │   │
│  │                     │  │                             │   │
│  └─────────────────────┘  └─────────────────────────────┘   │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                AI COMMENTARY BOX                       │  │
│  │  "Mon lookin' irie today! VPD at 1.05, she            │  │
│  │   vibin' hard in dis vegetative state, seen?"         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  AUDIO: VB-Cable (Rasta AI Voice) + Background Music        │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Software
- [ ] OBS Studio (https://obsproject.com)
- [ ] VB-Cable Virtual Audio (https://vb-audio.com/Cable/)
- [ ] Python 3.10+ with rasta-voice dependencies
- [ ] Browser for overlay page

### Hardware
- [ ] USB Webcam (pointing at plant)
- [ ] Microphone (for Rasta voice input)
- [ ] Headphones (to avoid feedback)

### API Keys (in rasta-voice/.env)
- [ ] DEEPGRAM_API_KEY (speech-to-text)
- [ ] GROQ_API_KEY (Patois transformation)
- [ ] ELEVENLABS_API_KEY (voice synthesis)

---

## Step 1: Audio Setup

### VB-Cable Installation
1. Download VB-Cable from https://vb-audio.com/Cable/
2. Run installer as Administrator
3. Reboot computer
4. Verify "CABLE Input/Output" appears in Sound settings

### OBS Audio Configuration
1. Open OBS → Settings → Audio
2. Configure:
   - **Desktop Audio**: Default
   - **Mic/Auxiliary Audio**: CABLE Output (VB-Audio Virtual Cable)
3. Click OK

### Rasta Voice Pipeline
1. Open terminal in `rasta-voice/` folder
2. Run: `python rasta_live.py --test` (test to speakers first)
3. When working, run: `python rasta_live.py` (routes to VB-Cable)
4. Speak into your mic → transformed Jamaican voice outputs to OBS

---

## Step 2: Scene Setup

### Scene 1: Main Grow View

**Sources (bottom to top):**

| Order | Source Type | Name | Settings |
|-------|-------------|------|----------|
| 1 | Video Capture | Plant Webcam | Your USB camera |
| 2 | Browser | Sensor Overlay | URL: http://localhost:8000/overlay |
| 3 | Browser | AI Commentary | URL: http://localhost:8000/commentary |
| 4 | Image | Logo Watermark | Bottom right corner |
| 5 | Audio Input | Rasta Voice | CABLE Output |
| 6 | Audio Input | Background Music | Optional chill beats |

### Scene 2: Closeup View
Same as Scene 1, but webcam zoomed in on plant

### Scene 3: Full Dashboard
Browser source showing full website (http://localhost:8000)

### Scene 4: Token Chart (for launches)
Browser source showing LFJ Token Mill chart or DEX screener

---

## Step 3: Browser Overlays

### Create Overlay Endpoints

Add these to your API (`src/api/app.py`):

```python
# Transparent overlay for OBS
@app.get("/overlay", response_class=HTMLResponse)
async def sensor_overlay():
    # Fetch latest sensor data
    sensors = await get_latest_sensors()
    return f'''
    <html>
    <head>
        <style>
            body {{
                background: transparent;
                font-family: 'JetBrains Mono', monospace;
                color: #4ade80;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
                padding: 20px;
            }}
            .sensor {{ font-size: 24px; margin: 10px 0; }}
            .label {{ color: #888; }}
        </style>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="sensor"><span class="label">TEMP:</span> {sensors.temperature}F</div>
        <div class="sensor"><span class="label">RH:</span> {sensors.humidity}%</div>
        <div class="sensor"><span class="label">VPD:</span> {sensors.vpd} kPa</div>
        <div class="sensor"><span class="label">DAY:</span> {sensors.grow_day}</div>
    </body>
    </html>
    '''
```

### Browser Source Settings
- **Width**: 400
- **Height**: 300
- **Custom CSS**:
  ```css
  body { background-color: rgba(0, 0, 0, 0); margin: 0; overflow: hidden; }
  ```

---

## Step 4: Audio Levels

### Recommended Levels
| Source | Level |
|--------|-------|
| Rasta Voice (CABLE Output) | -10 to -5 dB |
| Background Music | -25 to -20 dB |
| Desktop Audio | Muted unless needed |

### Audio Filters for Rasta Voice
1. Right-click CABLE Output → Filters
2. Add:
   - **Noise Suppression**: RNNoise
   - **Compressor**: Ratio 4:1, Threshold -20dB
   - **Limiter**: -3dB

---

## Step 5: Streaming Destinations

### Twitter/X Spaces
1. Start a Twitter Space as host
2. In Space settings, select **CABLE Output** as microphone
3. OBS won't directly stream to Spaces, but voice goes through VB-Cable
4. For video, consider streaming to Periscope/X Live

### YouTube Live
1. OBS → Settings → Stream
2. Service: YouTube - RTMPS
3. Connect Account or use Stream Key from YouTube Studio
4. Resolution: 1080p30 or 720p60

### Twitch
1. OBS → Settings → Stream
2. Service: Twitch
3. Connect Account
4. Recommended: 720p60, 4500 kbps

### Multi-Stream (Advanced)
Use Restream.io to broadcast to multiple platforms:
1. Sign up at restream.io
2. Add YouTube, Twitch, etc.
3. Use Restream RTMP URL in OBS

---

## Step 6: Hotkeys

### Recommended Hotkeys

| Action | Key |
|--------|-----|
| Switch to Main View | F1 |
| Switch to Closeup | F2 |
| Switch to Dashboard | F3 |
| Start/Stop Stream | F9 |
| Start/Stop Recording | F10 |
| Toggle Rasta Voice | F11 |
| Pause AI Commentary | F12 |

Set in OBS → Settings → Hotkeys

---

## Step 7: Recording Settings

For timelapse and VODs:

### Recording Settings
- **Format**: MKV (can remux to MP4)
- **Encoder**: NVENC (if Nvidia GPU) or x264
- **Quality**: High Quality, Medium Size
- **Path**: `C:\Users\natha\sol-cannabis\recordings\`

### Auto-Recording Schedule
Use OBS Advanced Scene Switcher plugin to:
- Start recording at 6:00 AM
- Stop recording at 10:00 PM
- Create daily timelapse segments

---

## Quick Start Commands

### Terminal 1: API Server
```bash
cd /mnt/c/Users/natha/sol-cannabis
./scripts/launch.sh api
```

### Terminal 2: Rasta Voice
```bash
cd /mnt/c/Users/natha/sol-cannabis/rasta-voice
python rasta_live.py
```

### Terminal 3: AI Agent (Optional)
```bash
cd /mnt/c/Users/natha/sol-cannabis
./scripts/launch.sh agent 1
```

### Then in Windows:
1. Open OBS Studio
2. Select "Grok & Mon" scene collection
3. Click "Start Streaming" or "Start Recording"

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No video from webcam | Check USB connection, select correct device in OBS |
| No Rasta voice audio | Verify VB-Cable installed, rasta_live.py running |
| Browser source black | Make sure API server is running on localhost:8000 |
| Laggy stream | Reduce resolution to 720p, lower bitrate |
| Echo/feedback | Wear headphones, mute desktop audio |
| Voice cutting out | Check Deepgram/ElevenLabs API quotas |

---

## OBS Profile Export

After setup, export your profile:
1. OBS → Profile → Export
2. Save to: `sol-cannabis/obs/grok-mon-profile.json`
3. OBS → Scene Collection → Export
4. Save to: `sol-cannabis/obs/grok-mon-scenes.json`

This lets you restore settings on any computer.

---

## Stream Schedule Template

| Time | Content |
|------|---------|
| Morning (8 AM) | "Wake up with Mon" - sensor check, AI greeting |
| Midday (12 PM) | Quick update, any adjustments |
| Evening (6 PM) | "Sunset Sesh" - longer stream, community chat |
| Special Events | Stage transitions, watering, training |

---

**Ready to stream! One love.** 🌿📺
