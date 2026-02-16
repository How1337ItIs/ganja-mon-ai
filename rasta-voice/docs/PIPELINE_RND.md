# Rasta Voice Pipeline - Research & Development Log

## Overview

Real-time voice transformation pipeline: **Mic → Deepgram STT → Groq LLM → ElevenLabs TTS → Audio Output**

**Goal:** Transform operator's voice into "Funny Ganja Rasta Mon" character with minimal latency for live streaming.

---

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Microphone │───▶│ Deepgram    │───▶│ SmartBatcher│───▶│ Groq LLM    │
│  (48kHz)    │    │ STT         │    │ (batching)  │    │ (Patois)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                   ┌─────────────┐    ┌─────────────┐           │
                   │ Dual Output │◀───│ ElevenLabs  │◀──────────┘
                   │ (parallel)  │    │ TTS         │
                   └─────────────┘    └─────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
    ┌───────────────┐        ┌───────────────┐
    │ VB-Cable      │        │ Headphones    │
    │ (to stream)   │        │ (monitoring)  │
    └───────────────┘        └───────────────┘
```

---

## Key Components

### 1. SmartBatcher (`rasta_live.py:510-580`)
Intelligent batching for dual-mode operation:
- **Conversation mode:** Quick response after silence
- **Monologue mode:** Efficient batching during continuous speech

### 2. Parallel TTS Pipeline (`rasta_live.py:1165-1330`)
Three async tasks running concurrently:
- `batch_collector()` - Collects and queues text batches
- `tts_generator()` - Generates TTS audio (runs while audio plays!)
- `audio_player()` - Plays audio from queue

### 3. Dual Audio Output (`rasta_live.py:820-870`)
Uses threading to play to both outputs simultaneously:
- VB-Cable (device 16) → OBS → Stream
- Headphones (device 19) → Operator monitoring

---

## Experiments & Findings

### Experiment 1: Basic Per-Sentence Processing
**Date:** Jan 2026 (initial)
**Approach:** Process each Deepgram transcript individually
**Result:** ❌ Long pauses between sentences, choppy speech
**Latency:** 5-8 seconds per sentence (TTS API bottleneck)

### Experiment 2: SmartBatcher Introduction
**Date:** Jan 27, 2026
**Approach:** Batch multiple transcripts before processing
**Parameters:**
```python
SILENCE_TIMEOUT = 1.5  # seconds
MAX_BATCH_DURATION = 12.0  # seconds
MIN_BATCH_CHARS = 30
```
**Result:** ⚠️ Better batching but 1.5s too short - natural breathing pauses triggered premature flush
**Learning:** Natural speech has 1-2s pauses between sentences

### Experiment 3: Increased Silence Timeout
**Date:** Jan 27, 2026
**Approach:** Increase timeout to allow natural pauses
**Parameters:**
```python
SILENCE_TIMEOUT = 3.0  # seconds (was 1.5)
MIN_BATCH_CHARS = 80  # (was 30)
MIN_SEGMENTS = 2  # new requirement
```
**Result:** ❌ TOO aggressive - Deepgram sent entire paragraph (493 chars) as ONE transcript
**Problem:** TTS had to generate 36 seconds of audio at once = 15+ second delay
**Learning:** Deepgram accumulates continuous speech into one `is_final` transcript

### Experiment 4: MAX_BATCH_CHARS + Sentence Splitting
**Date:** Jan 27, 2026
**Approach:** Force flush at character limit AND split long transcripts
**Parameters:**
```python
SILENCE_TIMEOUT = 2.0  # balanced
MAX_BATCH_DURATION = 8.0  # reduced
MIN_BATCH_CHARS = 60
MAX_BATCH_CHARS = 200  # FORCE flush (new!)
```
**Code:** Split transcripts >200 chars on sentence boundaries before adding to batcher
**Result:** ✅ SUCCESS! Batches now 60-120 chars, gapless playback working
**Evidence:** Logs show `📦 Batched 2 segments (107 chars)` and `▶️ Playing audio (1 more queued - gapless!)`

### Experiment 5: LLM Prompt Tuning (Filler Reduction)
**Date:** Jan 27, 2026
**Problem:** Too many "mon" and "ya know" in every response - sounded repetitive
**Root Cause:** Prompt said "3-4 fillers per paragraph" but each ~100 char batch was treated as a paragraph
**Fix:** Strict limits in prompt:
```
- "mon" = MAX 1 per response (or ZERO)
- "ya know" = MAX 1 per response (or ZERO)
- USE ALTERNATIVES: "seen?", "bredren", "irie", "bless up", "respect", "fi real"
```
**Result:** ✅ Much more varied speech, less repetitive

### Experiment 6: Voice Config Fix (Expressiveness)
**Date:** Jan 27, 2026
**Problem:** Voice sounded monotone/flat despite emotion tags
**Root Cause:** `voice_config.json` had `stability: 1.0` (WRONG!)
- stability=1.0 means MINIMUM expressiveness (flat, consistent)
- stability=0.0 means MAXIMUM expressiveness (varied, emotional)
**Fix:**
```json
{
  "stability": 0.0,   // was 1.0 (WRONG!)
  "style": 1.0,       // was 0.8
  "temperature": 0.9  // was 0.7
}
```
**Result:** ✅ Emotion tags like [excited] and [chuckles] now actually performed
**Learning:** ALWAYS check voice_config.json - it overrides code defaults!

---

## Current Best Settings

```python
# SmartBatcher parameters (rasta_live.py:517-521)
SILENCE_TIMEOUT = 2.0    # Flush after 2s silence
MAX_BATCH_DURATION = 8.0 # Flush after 8s continuous speech
MIN_BATCH_CHARS = 60     # Don't flush tiny fragments
MAX_BATCH_CHARS = 200    # FORCE flush at 200 chars
```

```python
# ElevenLabs TTS settings (rasta_live.py)
VOICE_ID = "dhwafD61uVd8h85wAZSE"  # Denzel - Jamaican, Raspy
MODEL = "eleven_v3"  # Supports emotion tags
STABILITY = 0.0      # Maximum expressiveness
SIMILARITY_BOOST = 0.5
STYLE = 1.0          # Maxed for emotion tags
```

---

## Latency Breakdown

Typical single batch (200 chars):
| Stage | Time | Notes |
|-------|------|-------|
| Deepgram STT | ~500ms | Real-time streaming |
| Batcher wait | 2000ms | Silence timeout |
| Groq LLM | 500-900ms | Fast! |
| ElevenLabs TTS | 2000-4000ms | **Bottleneck** |
| Audio playback | Variable | Depends on text length |
| **Total to first audio** | **~5-7 seconds** | After you stop speaking |

---

## Known Issues

### Issue 1: Deepgram Large Transcripts
**Problem:** When reading continuously, Deepgram accumulates ALL speech into one massive `is_final` transcript
**Symptom:** 493 chars = 15+ second TTS generation delay
**Mitigation:** Split long transcripts on sentence boundaries before batching

### Issue 2: Audio Device ID Changes
**Problem:** Bluetooth devices (AirPods) get new device IDs when reconnecting
**Symptom:** Audio goes to wrong device or no audio
**Mitigation:** Auto-detect headphones by name pattern, or use dashboard selector

### Issue 3: TTS API Latency
**Problem:** ElevenLabs takes 2-4 seconds per request regardless of text length
**Symptom:** Unavoidable delay before first audio
**Mitigation:** Parallel TTS generation (generate next while playing current)

---

## Ideas to Try

### 1. Deepgram Interim Results
Use `interim_results=True` to get partial transcripts during speech (not just at end)
- Pro: More frequent, smaller chunks
- Con: May get duplicate/revised text

### 2. Deepgram Utterance End
Configure `utterance_end_ms` to force more frequent `is_final` transcripts
- Default seems to wait for long pauses

### 3. Streaming TTS
ElevenLabs supports streaming - could start playing before full audio generated
- Already partially implemented but may need optimization

### 4. Local TTS
Use local TTS (Coqui, Piper) to eliminate API latency
- Pro: Sub-100ms latency
- Con: Voice quality may not match ElevenLabs

### 5. Predictive Pre-generation
Start generating TTS for likely responses before user finishes speaking
- Very experimental, may waste API calls

---

## File References

| File | Purpose |
|------|---------|
| `rasta_live.py` | Main pipeline (1400+ lines) |
| `start_pipeline.py` | Launcher with device config |
| `dashboard_working.py` | Web UI for control |
| `live_transcripts.jsonl` | Log of all transcriptions |

---

## Testing Scripts

### Short Test (conversation mode)
```
"Hey everyone, how's it going? Just checking in on the plant real quick."
```

### Long Test (monologue mode)
```
"Alright everyone, welcome back to another update on Mon. She's looking
absolutely beautiful today. The purple coloration is really starting to
come through on the upper colas. That's those granddaddy purple genetics
expressing themselves. I did some light defoliation yesterday, just
removing a few of the larger fan leaves that were blocking light to the
lower bud sites. Nothing too aggressive."
```

---

## Key Lessons Learned

### 1. Deepgram Behavior
- **Continuous speech = one massive transcript.** When reading without pauses, Deepgram accumulates ALL speech into a single `is_final` transcript (493+ chars)
- **Must split long transcripts** on sentence boundaries before batching
- **Natural speech has 1-2s pauses** between sentences for breathing - batcher timeout must account for this

### 2. ElevenLabs TTS Settings
- **`stability` is counterintuitive:** HIGH stability = FLAT/MONOTONE, LOW stability = EXPRESSIVE
- **`voice_config.json` overrides code defaults** - always check this file first when debugging
- **Emotion tags only work with `stability=0`** and `style=1.0`

### 3. Batching Trade-offs
- **Too small batches** (30 chars) = choppy, repetitive fillers per chunk
- **Too large batches** (500 chars) = massive TTS delay, poor responsiveness
- **Sweet spot: 60-200 chars** with sentence boundary splitting

### 4. Parallel Processing
- **Queue naming matters** - `audio_queue` shadowed mic audio queue, caused cryptic errors
- **Gapless playback requires pre-generation** - start generating next chunk while current plays

### 5. LLM Prompt Design
- **"Per paragraph" limits don't work** when paragraphs are small batches
- **Use absolute limits:** "MAX 1 per response" not "3-4 per paragraph"
- **Provide alternatives** to prevent repetitive fallbacks

---

## Changelog

### 2026-01-27 (Session 2)
- Fixed voice_config.json: stability 1.0→0.0, style 0.8→1.0
- Updated LLM prompt with strict filler limits (max 1 "mon" per response)
- Confirmed Experiment 4 success: gapless playback working
- Created this R&D documentation

### 2026-01-27 (Session 1)
- Added SmartBatcher for intelligent batching
- Implemented parallel TTS generation pipeline
- Added sentence splitting for long transcripts
- Tuned parameters: SILENCE_TIMEOUT 1.5→3.0→2.0, added MAX_BATCH_CHARS=200
- Fixed queue name collision bug (audio_queue → tts_audio_queue)

---

*Last updated: 2026-01-27*
