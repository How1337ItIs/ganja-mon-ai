# Rasta Voice Pipeline - Technical Handoff

## Project Status: PRODUCTION READY

The ElevenLabs-based pipeline is the **recommended production solution**. An experimental RVC (free) alternative exists but has quality issues.

---

## Quick Start

```bash
cd C:\Users\natha\sol-cannabis\rasta-voice

# Production mode (VB-Cable -> Twitter Spaces)
python rasta_live.py

# Test mode (output to speakers)
python rasta_live.py --test

# List audio devices
python rasta_live.py --list-devices
```

---

## Architecture

```
                    PRODUCTION PIPELINE (ElevenLabs)
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Your Mic  │────>│  Deepgram   │────>│    Groq     │
    │             │     │  (STT)      │     │  (Patois)   │
    └─────────────┘     │  Nova 2     │     │ llama-3.3   │
                        └─────────────┘     └─────────────┘
                                                  │
                                                  v
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Twitter   │<────│  VB-Cable   │<────│ ElevenLabs  │
    │   Spaces    │     │  (Virtual)  │     │  (Denzel)   │
    └─────────────┘     └─────────────┘     │  eleven_v3  │
                                            └─────────────┘

                    EXPERIMENTAL PIPELINE (RVC - Free)
    Mic -> Deepgram STT -> Groq -> edge-tts -> RVC -> VB-Cable
                                    │           │
                                    │           └── Mr.Bomboclaut model
                                    └── en-US-GuyNeural
```

### Component Details

| Component | Service | Model/Voice | Purpose |
|-----------|---------|-------------|---------|
| STT | Deepgram | Nova 2 | Real-time speech-to-text |
| LLM | Groq | llama-3.3-70b-versatile | Transform English to Patois |
| TTS | ElevenLabs | Denzel (dhwafD61uVd8h85wAZSE) | Jamaican voice synthesis |
| Audio | VB-Cable | - | Virtual audio routing to Twitter |

---

## File Structure

```
rasta-voice/
├── rasta_live.py           # MAIN - ElevenLabs pipeline (RECOMMENDED)
├── rasta_live_rvc.py       # EXPERIMENTAL - RVC pipeline (free, lower quality)
├── test_rvc.py             # RVC testing script
├── run_rasta_rvc.bat       # Batch file to run RVC with Python 3.10
├── .env                    # API keys (not committed)
├── requirements.txt        # Python dependencies
├── README.md               # User documentation
├── HANDOFF.md              # This file - technical documentation
│
├── rvc_models/             # RVC voice models (downloaded from HuggingFace)
│   ├── Mr.Bomboclaut.pth
│   ├── added_IVF126_Flat_nprobe_1_Mr.Bomboclaut_v2.index
│   ├── BlackHeroV2.pth
│   ├── added_IVF1161_Flat_nprobe_1_BlackHeroV2_v2.index
│   ├── bobmarley_e500_s9000.pth
│   └── added_IVF1188_Flat_nprobe_1_bobmarley_v2.index
│
├── .venv-rvc/              # Python 3.10 venv for RVC (separate from main)
│   └── ...                 # PyTorch 2.4.1, rvc-python, fairseq, edge-tts
│
└── test_*.mp3/wav          # Test audio files from development
```

---

## API Configuration

### Required Keys (in `.env`)

```env
# Deepgram (Speech-to-Text)
DEEPGRAM_API_KEY=your_key_here

# Groq (LLM for Patois transformation)
GROQ_API_KEY=your_key_here

# ElevenLabs (Text-to-Speech)
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE  # Denzel voice (optional, has default)
```

### ElevenLabs Voice Settings

```python
{
    'voice_id': 'dhwafD61uVd8h85wAZSE',  # Denzel - Jamaican, Raspy, Deep
    'model_id': 'eleven_v3',              # v3 supports [laughs], [sighs], etc.
    'stability': 0.0,                     # Creative mode for natural variation
    'similarity_boost': 0.8
}
```

---

## Cost Analysis

### ElevenLabs Pricing

| Tier | Characters/Month | Cost | Usage Per Response |
|------|------------------|------|-------------------|
| Free | 10,000 | $0 | ~50-200 chars |
| Creator | 100,000 | $22/month | ~500-2000 responses |

**Current Setup**: Creator tier (100,000 chars/month)

### Other Services

| Service | Cost | Notes |
|---------|------|-------|
| Deepgram | Pay-per-use | ~$0.0043/min |
| Groq | Free tier | Generous limits |
| VB-Cable | Free | Donationware |

---

## RVC Troubleshooting Journey

The RVC pipeline was explored as a free alternative but ultimately abandoned due to quality issues.

### Installation Challenges

1. **Python 3.13 Incompatible with RVC**
   - fairseq package requires Python <= 3.11
   - Created Python 3.10 venv using uv:
     ```bash
     uv venv .venv-rvc --python 3.10
     ```

2. **Python 3.11 fairseq dataclass errors**
   - Downgraded to Python 3.10 to resolve

3. **av package DLL blocked by Windows**
   - Error: `av.libs.libavutil was blocked`
   - Fix: Downgraded av to v12.0.0
     ```bash
     pip install av==12.0.0
     ```

4. **PyTorch 2.6 weights_only=True breaking model loading**
   - Fix: Downgraded to PyTorch 2.4.1
     ```bash
     pip install torch==2.4.1+cu121 torchaudio==2.4.1+cu121 --index-url https://download.pytorch.org/whl/cu121
     ```

5. **RTX 5070 Ti (sm_120) not supported by PyTorch**
   - Blackwell architecture (sm_120) not yet in stable PyTorch
   - Workaround: Run RVC on CPU instead of GPU
     ```python
     self.rvc = RVCInference(device="cpu")
     ```

### RVC Models Tested

| Model | Source | Quality | Notes |
|-------|--------|---------|-------|
| Mr.Bomboclaut | HuggingFace | Poor | Speech-trained but TTS chain produces artifacts |
| BlackHeroV2 | HuggingFace | Poor | Jamaican artist voice |
| Bob Marley | voice-models.com | Poor | Trained on singing, not speech |

### Pitch Testing Results

Tested BlackHeroV2 with pitch shifts from -4 to +4 semitones:
- All variants sounded unnatural
- User feedback: "sounds like a swedish dude" and "really fucking terrible"

### Conclusion

RVC + edge-tts chain produces artifacts. The TTS-to-RVC pipeline creates unnatural voice characteristics that don't match the quality of a natively trained voice like ElevenLabs' Denzel.

**Recommendation**: Use ElevenLabs ($22/month) for production quality.

---

## Audio Routing (Twitter Spaces)

### Setup

1. Install [VB-Cable](https://vb-audio.com/Cable/) (free donationware)
2. Reboot after installation
3. The pipeline auto-detects VB-Cable as output

### Twitter Configuration

1. Run `rasta_live.py`
2. In Twitter Spaces settings, select **"CABLE Output (VB-Audio)"** as your microphone
3. Wear headphones so your real mic doesn't pick up the TTS

### Audio Flow

```
Your Mic -> Deepgram -> Groq -> ElevenLabs TTS
                                     |
                                     v
Twitter Spaces <- "CABLE Output" <- VB-Cable Input <- sounddevice.play()
```

---

## Patois Transformation

The Groq LLM transforms English to Jamaican Patois using this prompt:

```python
IRIE_PROMPT = """Rewrite with Rastafarian vibes. Keep it natural.

RASTA GRAMMAR:
- "I/me/my" -> "I" or "I-man" (divine self)
- "we/us" -> "I and I" (unity)
- "you" -> "yuh", "them" -> "dem"
- Drop "is/are": "This is good" -> "Dis good"

RASTA EXPRESSIONS:
- "Jah" = God
- "irie" = good, peaceful
- "ital" = natural, organic
- "seen" = understood
- "forward" = go ahead
- "one love" = unity, peace

EXAMPLES:
- "Is this working?" -> "Dis ting working, seen?"
- "Hello everyone" -> "Wah gwaan, I and I"
- "Thanks, goodbye" -> "Give thanks, one love"
"""
```

---

## Performance

### Latency (ElevenLabs)

| Phrase Length | Latency |
|---------------|---------|
| Short (1-5 words) | 3-5 seconds |
| Medium (6-15 words) | 5-8 seconds |
| Long (15+ words) | 8-15 seconds |

Latency breakdown:
- Deepgram STT: ~300ms
- Groq LLM: ~500-1000ms
- ElevenLabs TTS: ~2-5 seconds (depends on output length)
- Audio playback: varies

### Latency (RVC - Not Recommended)

RVC adds ~5-10 seconds on top due to:
- edge-tts generation: ~1-2 seconds
- RVC conversion (CPU): ~3-8 seconds
- Total: 10-20+ seconds per phrase

---

## Dependencies

### Production (requirements.txt)

```
aiohttp>=3.9.0              # Deepgram WebSocket
groq>=0.4.0                 # Groq API client
elevenlabs>=1.0.0           # ElevenLabs TTS
numpy>=1.24.0               # Audio processing
sounddevice>=0.4.6          # Audio playback to VB-Cable
python-dotenv>=1.0.0        # Environment variables
```

### RVC Pipeline (separate venv)

```
# In .venv-rvc (Python 3.10)
torch==2.4.1+cu121
torchaudio==2.4.1+cu121
rvc-python
edge-tts
fairseq
av==12.0.0
```

---

## External Requirements

- **Python 3.13+** (main pipeline)
- **Python 3.10** (RVC pipeline, if using)
- **VB-Cable** (virtual audio driver)
- **FFmpeg** (in `~/Downloads/ffmpeg-bin/`)

---

## Future Improvements

1. **Faster TTS**: Investigate streaming TTS for lower latency
2. **Better free alternative**: Wait for RVC GPU support on RTX 50 series
3. **Voice cloning**: Train custom ElevenLabs voice for perfect Rasta accent
4. **Emotion detection**: Auto-add [laughs] tags based on input sentiment

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "VB-Cable not found" | Reboot after installing VB-Cable driver |
| No sound in Twitter | Select "CABLE Output" as mic in Twitter settings |
| High latency | Use shorter phrases; ElevenLabs is inherently slow |
| ElevenLabs quota exceeded | Check usage at elevenlabs.io; credits reset monthly |
| Mic not detected | Close other apps using microphone |
| RVC sm_120 error | Run on CPU (default in rasta_live_rvc.py) |

---

## Session Log (Jan 2026)

1. Started with ElevenLabs pipeline - worked great
2. Ran out of ElevenLabs credits
3. Explored RVC as free alternative
4. Downloaded Mr.Bomboclaut, BlackHeroV2, Bob Marley models
5. Struggled with Python version compatibility (3.13 -> 3.10)
6. Fixed PyTorch/fairseq/av issues
7. Tested RVC - quality was poor ("sounds like a swedish dude")
8. User paid for ElevenLabs Creator tier ($22/month, 100k chars)
9. Verified ElevenLabs pipeline working
10. Documented everything

**Final decision**: ElevenLabs is worth the $22/month for production-quality Jamaican voice.
