# 🎙️ OUTRAGEOUS JAMAICAN VOICE UPGRADE PLAN

**Goal:** Make the Ganja Mon voice sound MORE Jamaican - thick, heavy patois that's unmistakably irie.

**Date:** 2026-01-19
**Status:** Ready for implementation

---

## Current Stack

```
Mic → Deepgram STT → Groq LLM (Patois) → ElevenLabs TTS → VB-Cable → Twitter
```

- **Voice:** ElevenLabs "Denzel" (`dhwafD61uVd8h85wAZSE`) - Jamaican, Raspy, Deep
- **Model:** `eleven_v3` with emotion tags (`[laughs]`, `[sighs]`)
- **Problem:** Not THICK enough. Sounds "polite Jamaican" not "yard mon"

---

## Available Assets (Already Downloaded!)

### RVC Models in `rasta-voice/rvc_models/`

| Model | Style | Epochs | Best For |
|-------|-------|--------|----------|
| `Mr.Bomboclaut.pth` | TikTok Jamaican Guy | 400 | **MOST EXPRESSIVE** - thick patois, high energy |
| `BlackHeroV2.pth` | Dancehall Artist | 650 | Reggae cadence, rhythmic |
| `bobmarley_e500_s9000.pth` | Bob Marley | 500 | Legendary tone, spiritual vibe |

### ElevenLabs Alternatives (Shared Library)

Search queries to try:
- `patois` - Heavy dialect voices
- `rasta` or `reggae` - Cultural voices
- `caribbean` - Regional accents
- `jamaican heavy` - Thick accent

---

## Upgrade Options (Pick One)

### Option A: Swap ElevenLabs Voice (5 min)

**Fastest** - Just change the voice ID in `.env`

1. Run voice search:
   ```bash
   cd c:\Users\natha\sol-cannabis\rasta-voice
   python search_voices.py
   ```

2. Listen to samples and pick the thickest accent

3. Update `.env`:
   ```
   ELEVENLABS_VOICE_ID=<new_voice_id>
   ```

4. Test:
   ```bash
   python rasta_live.py --test
   ```

**Pros:** Quick, no extra processing
**Cons:** Limited by what's in ElevenLabs library

---

### Option B: RVC Pipeline (30 min) ⭐ RECOMMENDED

**Best quality** - Chain ElevenLabs through RVC voice conversion

```
Text → Groq → ElevenLabs Denzel → Mr.Bomboclaut RVC → THICK PATOIS OUTPUT
```

The RVC model "re-voices" the audio to sound like Mr. Bomboclaut's thick Jamaican accent while keeping the words and emotion from ElevenLabs.

1. Verify RVC setup:
   ```bash
   cd c:\Users\natha\sol-cannabis\rasta-voice
   python test_rvc.py
   ```

2. Run the RVC pipeline:
   ```bash
   python rasta_live_rvc.py --test
   ```

3. Tune pitch if needed (Mr.Bomboclaut may need pitch adjustment):
   - `-2` to `-4` for deeper voice
   - `+2` to `+4` for higher pitch

**Pros:** MAXIMUM Jamaican authenticity, uses your downloaded models
**Cons:** More latency (~200-500ms extra), requires more CPU

---

### Option C: Hybrid Experimentation (1 hour)

Try different combinations:

| Base Voice | RVC Model | Expected Result |
|------------|-----------|-----------------|
| Denzel | Mr.Bomboclaut | Thick TikTok energy |
| Denzel | BlackHeroV2 | Smooth dancehall |
| Denzel | Bob Marley | Legendary reggae tone |
| Justin (Caribbean) | Mr.Bomboclaut | Double-thick patois |

---

## Voice Tuning Parameters

### ElevenLabs Settings (`rasta_live.py` line 142-145)

```python
voice_settings={
    'stability': 0.0,       # 0.0=Creative (enables laughs), 0.5=Natural, 1.0=Robust
    'similarity_boost': 0.8  # Higher = more like original voice
}
```

- **For MORE expression:** `stability: 0.0`, `similarity_boost: 0.7`
- **For natural patois:** `stability: 0.3`, `similarity_boost: 0.8`

### RVC Settings (if using `rasta_live_rvc.py`)

Key parameters to experiment with:
- **Pitch shift:** `-4` to `+4` semitones
- **Index rate:** `0.5` to `0.8` (higher = more like training voice)
- **Filter radius:** `3` (smoothing, keep at 3)

---

## Quick Test Commands

```bash
# Test ElevenLabs only (current)
python rasta_live.py --test

# Test with RVC overlay (thicker)
python rasta_live_rvc.py --test

# Search for new voices
python search_voices.py

# List audio devices
python rasta_live.py --list-devices
```

---

## External Resources

### More RVC Models
- [Hugging Face: Jamaican RVC](https://huggingface.co/models?search=jamaican+rvc)
- [voice-models.com](https://voice-models.com) - Search "jamaican" or "patois"
- [weights.gg](https://weights.gg) - Community RVC uploads

### ElevenLabs Deep Dives
- [Jamaican Accent Generator](https://elevenlabs.io/text-to-speech/jamaican-accent)
- Shared Voice Library: Search in ElevenLabs dashboard

### Alternative TTS (if ElevenLabs not thick enough)
- **facebook/mms-tts-jam** - Meta's Jamaican Creole TTS (HuggingFace)
- **Coqui XTTS v2** - Local TTS with accent cloning (requires reference audio)

---

## Recommended Next Step

👉 **Try Option B first** - Run `python rasta_live_rvc.py --test` with Mr.Bomboclaut

This uses your already-downloaded models and should produce the THICKEST Jamaican output.

If RVC latency is too high for live use, fall back to Option A and find a heavier ElevenLabs voice.

---

## Success Criteria

✅ Voice sounds "yard mon" not "tourist Jamaican"
✅ Patois is thick but still understandable
✅ Emotion tags ([laughs], [chuckles]) still work
✅ Latency under 2 seconds total for live streaming
✅ MON/mon puns come through clearly

---

*One love, bredren! 🇯🇲*
