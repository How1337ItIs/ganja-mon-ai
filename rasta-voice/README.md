# Rasta Voice Pipeline

Real-time voice transformation for Twitter Spaces. Converts your speech into Jamaican Patois with an authentic Rasta voice.

## Pipeline Flow

```
Mic → Deepgram STT → Groq LLM (Patois) → ElevenLabs TTS (Denzel) → VB-Cable → Twitter Spaces
```

## Quick Start

```bash
cd rasta-voice

# Production mode (VB-Cable → Twitter Spaces)
python rasta_live.py

# Test mode (output to speakers)
python rasta_live.py --test

# List audio devices
python rasta_live.py --list-devices
```

## Text-to-Text Translator (no voice, no emotion tags)

This uses the same Ganja Mon personality, but outputs plain text only (no `[laughs]`-style tags).

```bash
cd rasta-voice

# One-shot
python rasta_text_translate.py "Hello everyone, welcome to the space!"

# Pipe input
echo "I appreciate you all for joining." | python rasta_text_translate.py

# Interactive REPL
python rasta_text_translate.py --repl
```

## Requirements

### API Keys (in `.env`)

```env
DEEPGRAM_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
XAI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE  # Denzel voice (optional, has default)
```

### Software

- **Python 3.13+** (main pipeline)
- **VB-Cable** - Virtual audio driver for routing to Twitter
- **FFmpeg** - Audio processing (in `~/Downloads/ffmpeg-bin/`)

### Python Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Voice Settings

The Denzel voice from ElevenLabs is configured with:
- Model: `eleven_v3` (supports expressive sounds like [laughs], [sighs])
- Stability: `0.0` (Creative mode for natural variation)
- Similarity Boost: `0.8`

### Patois Transformation

The Groq LLM transforms your speech using Rastafarian grammar and expressions:

| English | Patois |
|---------|--------|
| I/me/my | I, I-man |
| we/us | I and I |
| you | yuh |
| them | dem |
| "Is this working?" | "Dis ting working, seen?" |
| "Hello everyone" | "Wah gwaan, I and I" |
| "Thanks, goodbye" | "Give thanks, one love" |

### Audio Routing (Twitter Spaces)

1. Install [VB-Cable](https://vb-audio.com/Cable/)
2. The pipeline auto-detects VB-Cable as output
3. In Twitter Spaces, select "CABLE Output" as your microphone

## Files

| File | Description |
|------|-------------|
| `rasta_live.py` | Main pipeline (ElevenLabs) |
| `rasta_live_rvc.py` | Alternative pipeline (RVC - experimental) |
| `test_rvc.py` | RVC testing script |
| `.env` | API keys (not committed) |
| `requirements.txt` | Python dependencies |

## ElevenLabs Subscription

- **Free tier**: 10,000 chars/month
- **Creator tier**: 100,000 chars/month ($22/month)
- Characters used per response: ~50-200 depending on length

## Alternative: RVC Pipeline (Free but Lower Quality)

An experimental free alternative using RVC voice conversion:

```bash
# Uses Python 3.10 venv (RVC compatibility)
.venv-rvc\Scripts\python.exe rasta_live_rvc.py --test
```

### RVC Models Available

| Model | Type | Quality |
|-------|------|---------|
| Mr.Bomboclaut | Jamaican TikTok | Speech-trained |
| BlackHero V2 | Jamaican Artist | Mixed |
| Bob Marley | Reggae Legend | Singing-trained |

**Note**: RVC quality doesn't match ElevenLabs. The TTS→RVC chain produces artifacts.

## Troubleshooting

### No audio output
- Check `--list-devices` for available outputs
- Ensure VB-Cable is installed and not in use by another app

### Mic not detected
- Close other apps using the microphone (Voice Recorder, etc.)
- Check Windows sound settings

### High latency
- Shorter phrases process faster
- ElevenLabs latency is typically 3-6 seconds for short phrases

### ElevenLabs quota exceeded
- Check usage at elevenlabs.io
- Credits reset monthly
- Consider upgrading to Creator plan

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Your Mic  │────▶│  Deepgram   │────▶│    Groq     │
│             │     │  (STT)      │     │  (Patois)   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Twitter   │◀────│  VB-Cable   │◀────│ ElevenLabs  │
│   Spaces    │     │  (Virtual)  │     │  (Denzel)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Credits

- **Deepgram** - Speech-to-text (Nova 2 model)
- **Groq** - LLM inference (llama-3.3-70b-versatile)
- **ElevenLabs** - Text-to-speech (Denzel voice, eleven_v3 model)
- **VB-Audio** - Virtual audio cable
