# Context-Aware Voice Routing Plan

## Goal

Enable Ganja Mon to hear FULL Twitter Spaces conversations (you + other speakers) for context-aware translations, while preventing audio feedback loops.

---

## The Solution: Voicemeeter Banana + VB-Cable

Based on your research (WINDOWS_AUDIO_ARCHITECTURE.md, VB_CABLE_VOICEMEETER.md, STREAMING_PLATFORMS_AUDIO.md):

### Audio Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    VOICEMEETER BANANA                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUTS:                                                          │
│  ┌────────────────┐                                              │
│  │ HW Input 1     │  ← Your Physical Microphone                  │
│  │ [A1] [B1] [B2] │                                              │
│  └────────────────┘                                              │
│                                                                   │
│  ┌────────────────┐                                              │
│  │ VAIO (Virtual) │  ← Twitter Spaces Audio OUT (other speakers) │
│  │ [A1] [B2]      │                                              │
│  └────────────────┘                                              │
│                                                                   │
│  OUTPUTS:                                                         │
│  A1: Your Headphones (monitor everything)                        │
│  B1: Your Mic ONLY → For potential local recording               │
│  B2: Your Mic + Twitter Audio → Deepgram (for transcription)     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
           │                              │
           │ (B2 Mixed Output)            │
           ▼                              │
    ┌─────────────┐                       │
    │  Deepgram   │                       │
    │  (STT)      │                       │
    │             │                       │
    │  Hears:     │                       │
    │  - You      │                       │
    │  - Guests   │                       │
    └─────────────┘                       │
           │                              │
           ▼                              │
    ┌─────────────┐                       │
    │  Grok AI    │                       │
    │  (Patois)   │                       │
    │             │                       │
    │  With full  │                       │
    │  context!   │                       │
    └─────────────┘                       │
           │                              │
           ▼                              │
    ┌─────────────┐                       │
    │ ElevenLabs  │                       │
    │  (TTS)      │                       │
    └─────────────┘                       │
           │                              │
           ▼                              │
    ┌─────────────┐                       │
    │  VB-Cable   │ (Separate path!)     │
    │             │                       │
    │  NOT routed │                       │
    │  to Deepgram│                       │
    └─────────────┘                       │
           │                              │
           ▼                              │
    ┌─────────────────┐                   │
    │ Twitter Spaces  │                   │
    │                 │                   │
    │ Mic: CABLE Out  │───────────────────┘
    │ Speaker: VAIO   │ (captures others)
    └─────────────────┘
```

---

## Detailed Configuration

### 1. Install Software

**Already have:**
- ✅ VB-Cable

**Need to install:**
- Voicemeeter Banana (free from vb-audio.com)

### 2. Voicemeeter Configuration

**Hardware Inputs:**
- **Hardware Input 1:** Your physical microphone
  - Enable: [A1] [B2]
  - A1 = you hear yourself in headphones
  - B2 = goes to Deepgram mixed feed

**Virtual Inputs:**
- **VAIO (Voicemeeter Input):** Twitter Spaces audio output
  - Enable: [A1] [B2]
  - A1 = you hear other speakers
  - B2 = goes to Deepgram mixed feed

**Outputs:**
- **A1:** Your headphones (monitor everything)
- **B2:** Voicemeeter AUX Output → Deepgram captures this

### 3. Windows Audio Settings

**Playback Tab:**
- CABLE Input: 48000 Hz, 2 channel, 16 bit
- Voicemeeter Input (VAIO): 48000 Hz

**Recording Tab:**
- CABLE Output: 48000 Hz, 2 channel, 16 bit
- Voicemeeter Output: 48000 Hz
- Voicemeeter AUX Output: 48000 Hz

### 4. Twitter Spaces Configuration

**In Twitter Spaces audio settings:**
- **Microphone:** CABLE Output (VB-Audio Virtual Cable)
- **Speakers:** Voicemeeter Input (VAIO)

**Critical:** Speakers set to VAIO so we capture what others say!

### 5. Python Code Changes

**Update Deepgram input to capture Voicemeeter B2:**

```python
# Find Voicemeeter AUX Output (B2) - this has mixed audio
deepgram_input_device = find_audio_device("voicemeeter aux output", is_output=False)

# Ganja Mon output stays on VB-Cable (separate!)
ganja_mon_output = find_audio_device("cable input", is_output=True)
```

---

## Why This Works

### Prevents Feedback Loop

✅ **Ganja Mon voice:**
- ElevenLabs → VB-Cable Input
- VB-Cable Output → Twitter Spaces mic
- Does NOT go to Voicemeeter
- Does NOT reach Deepgram
- No feedback loop!

✅ **Full conversation context:**
- Your mic → Voicemeeter → B2 → Deepgram
- Twitter audio → Voicemeeter VAIO → B2 → Deepgram
- Deepgram transcribes ALL speakers
- Grok has full context!

---

## Implementation Steps

### Phase 1: Backup Current Setup

```bash
cp rasta_live.py rasta_live_v1_simple.py
```

### Phase 2: Install Voicemeeter Banana

1. Download from vb-audio.com/Voicemeeter
2. Run installer as Administrator
3. Reboot

### Phase 3: Configure Routing

1. Open Voicemeeter Banana
2. Set Hardware Input 1 to your mic
3. Set A1 to your headphones
4. Configure routing buttons as described above

### Phase 4: Update Code

Add:
- Conversation buffer (last 10 exchanges)
- Speaker diarization (optional, or just assume it's all context)
- Pass conversation history to Grok
- Only transform YOUR speech (detected as most recent)

### Phase 5: Test

1. Start in test mode
2. Play audio to VAIO (simulates other speaker)
3. Speak into mic
4. Verify Deepgram hears both
5. Verify Ganja Mon doesn't loop back

---

## Cost Estimate

**Deepgram with diarization:**
- Streaming: ~$0.0077/min
- 1 hour Space: ~$0.46
- Diarization: Included (or small additional fee)

**Total for 1 hour:** Under $0.50

**Verdict:** Very affordable!

---

## Rollback Plan

If issues occur:

```bash
# Revert to simple version
cp rasta_live_v1_simple.py rasta_live.py

# Or use git
git checkout rasta_live.py
```

---

## Next Steps

1. Install Voicemeeter Banana
2. Configure routing per this guide
3. Update Python code for multi-speaker context
4. Test thoroughly before first Space
5. Have simple version as backup

**Ready to implement this?**
