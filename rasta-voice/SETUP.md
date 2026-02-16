# Rasta Voice Pipeline Setup Guide

Real-time voice transformation for X Spaces that converts your speech to Jamaican Patois dialect.

## Quick Start

### 1. Install Dependencies

```bash
cd rasta-voice
pip install -r requirements.txt
```

### 2. Get API Keys

You need three API keys:

| Service | Get Key | Cost |
|---------|---------|------|
| **AssemblyAI** | https://assemblyai.com | ~$0.65/hr |
| **Groq** | https://console.groq.com | Free tier available! |
| **Cartesia** | https://cartesia.ai | ~$0.50/hr |

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Create a Rasta Voice in Cartesia

1. Go to https://play.cartesia.ai/
2. Create a new voice using Voice Design or clone from a sample
3. For authentic Rasta sound, clone from reggae artist interviews
4. Copy the Voice ID to your `.env` file

### 5. Test the Dialect Transform

```bash
python test_dialect.py
```

This tests just the LLM transformation without audio.

### 6. Run the Full Pipeline

```bash
python rasta_pipeline.py
```

---

## Virtual Audio Setup (for X Spaces)

To route the transformed voice into X Spaces, you need a virtual audio cable.

### Windows (VB-Cable)

1. Download VB-Cable: https://vb-audio.com/Cable/
2. Install and restart
3. In the pipeline, set output device to "CABLE Input"
4. In X Spaces/browser, set microphone to "CABLE Output"

```
Your Mic → Pipeline → VB-Cable Input → VB-Cable Output → X Spaces
```

### Mac (BlackHole)

1. Install BlackHole: `brew install blackhole-2ch`
2. Create Multi-Output Device in Audio MIDI Setup
3. Set pipeline output to BlackHole
4. Set browser mic to BlackHole

### Linux (PulseAudio)

```bash
# Create virtual sink
pactl load-module module-null-sink sink_name=VirtualMic sink_properties=device.description=VirtualMic

# Route to it
pactl load-module module-loopback source=VirtualMic.monitor
```

---

## Finding Your Audio Devices

Run this to list available audio devices:

```python
import sounddevice as sd
print(sd.query_devices())
```

Then set `OUTPUT_DEVICE_INDEX` in `.env` to the virtual cable's index.

---

## Latency Tuning

Target: **~500-600ms total** (hidden by deliberate Rasta speech cadence)

| Component | Expected | Optimize |
|-----------|----------|----------|
| AssemblyAI STT | ~300ms | Use shorter phrases |
| Groq LLM | ~100-200ms | Already optimized |
| Cartesia TTS | ~40-90ms | Use Sonic Turbo |

Tips:
- Speak in shorter phrases (5-10 words)
- Pause naturally between thoughts
- The "slow, deliberate" Rasta style hides the latency perfectly

---

## Troubleshooting

### "No audio input detected"
- Check microphone permissions
- Run `python -c "import sounddevice; print(sounddevice.query_devices())"` to verify mic

### High latency (>1s)
- Check your internet connection
- Try Groq's smaller model: `llama-3.1-8b-instant`
- Reduce `chunk_size` in config

### Voice sounds robotic
- Create a better voice clone in Cartesia
- Use audio samples with natural speech rhythm
- Try different Cartesia model: `sonic-english` vs `sonic-2`

### API errors
- Verify all keys in `.env` are correct
- Check API credit balances
- AssemblyAI requires a paid plan for real-time

---

## Cost Estimate

For a 1-hour X Space:
- AssemblyAI: ~$0.65
- Groq: ~$0.01 (basically free)
- Cartesia: ~$0.50

**Total: ~$1.20/hour**
