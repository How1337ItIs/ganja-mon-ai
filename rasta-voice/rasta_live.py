#!/usr/bin/env python3
"""
Live Rasta Voice Pipeline with Auto-Recovery

Flow: Mic -> Deepgram STT -> xAI LLM -> Cartesia TTS -> Speaker

Features:
- WebSocket auto-reconnect with exponential backoff
- Health check monitoring for connection status
- Supervisor mode for crash recovery
- Graceful degradation on API failures
"""

import os
import sys
import json
import asyncio
import time
import random
import base64
import signal
import argparse
import logging
import threading
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from collections import deque
from datetime import datetime

import numpy as np
import sounddevice as sd
from scipy import signal as scipy_signal
from dotenv import load_dotenv
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed, WebSocketException
from openai import OpenAI
from elevenlabs import ElevenLabs

# Load environment
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Voice Config (used by dashboard sliders)
# =============================================================================

VOICE_CONFIG_FILE = Path(__file__).parent / "voice_config.json"


def _clamp01(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def load_voice_config() -> dict:
    """
    Reads voice_config.json (if present) to control:
    - LLM temperature
    - ElevenLabs voice settings (stability/style)
    """
    cfg = {"stability": 0.0, "style": 1.0, "temperature": 0.7}
    try:
        if VOICE_CONFIG_FILE.exists():
            data = json.loads(VOICE_CONFIG_FILE.read_text(encoding="utf-8"))
            cfg["stability"] = _clamp01(data.get("stability", cfg["stability"]))
            cfg["style"] = _clamp01(data.get("style", cfg["style"]))
            # temperature allowed in [0,1] for our UI
            cfg["temperature"] = _clamp01(data.get("temperature", cfg["temperature"]))
    except Exception:
        # Keep defaults on parse errors
        pass
    return cfg

# =============================================================================
# Auto-Recovery Configuration
# =============================================================================

MAX_RECONNECT_ATTEMPTS = 10
BASE_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 60.0
BACKOFF_MULTIPLIER = 2.0
JITTER_FACTOR = 0.3  # +/- 30% randomness
HEALTH_CHECK_INTERVAL = 30  # seconds
CONNECTION_TIMEOUT = 10  # seconds
KEEPALIVE_INTERVAL = 15  # seconds

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Config:
    deepgram_key: str = os.getenv("DEEPGRAM_API_KEY", "")
    # Use Groq for fastest LLM inference
    groq_key: str = os.getenv("GROQ_API_KEY", "")
    elevenlabs_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    # Denzel voice - HEAVY Jamaican accent
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

    sample_rate: int = 48000  # Standard sample rate for modern devices
    output_sample_rate: int = 24000  # ElevenLabs PCM output
    chunk_size: int = 1024

    # Audio input device (for microphone)
    input_device: Optional[int] = None  # AirPods or other mic
    # Audio output devices (set by command line args)
    twitter_output_device: Optional[int] = None  # VB-Cable Input for Twitter
    monitor_output_device: Optional[int] = None  # Headphones for monitoring

    # Batching mode: "conversation" (fast response) or "stream" (longer segments)
    mode: str = "stream"

config = Config()


def find_audio_device(name_pattern: str, is_output: bool = True, preferred_sr: int = 48000) -> Optional[int]:
    """Find audio device index by name pattern, preferring specific sample rate."""
    devices = sd.query_devices()
    matches = []

    for i, d in enumerate(devices):
        if name_pattern.lower() in d['name'].lower():
            # Check if it's the right type (input/output)
            is_valid = (is_output and d['max_output_channels'] > 0) or \
                      (not is_output and d['max_input_channels'] > 0)
            if is_valid:
                matches.append((i, d))

    if not matches:
        return None

    # Prefer device with matching sample rate
    for i, d in matches:
        if d.get('default_samplerate') == preferred_sr:
            logger.info(f"Selected device {i}: {d['name']} @ {preferred_sr}Hz")
            return i

    # Fall back to first match
    i, d = matches[0]
    logger.warning(f"No {preferred_sr}Hz device found, using {d['name']} @ {d.get('default_samplerate')}Hz")
    return i

# =============================================================================
# System Prompt (RRP Framework - Character Card + Scene Contract)
# =============================================================================

RASTA_SYSTEM_PROMPT = """
🔥 FUNNY GANJA RASTA MON 🔥
You transform English into fun, cartoony Jamaican Patois for a live voice stream.

CRITICAL FILLER LIMITS (STRICT!):
- "mon" = MAX 1 per response (or ZERO - vary it!)
- "ya know" = MAX 1 per response (or ZERO)
- USE ALTERNATIVES: "seen?", "bredren", "irie", "bless up", "respect", "fi real"
- Let the PATOIS GRAMMAR do the work, not repetitive fillers!

STYLE RULES:
- ONE emotion tag at start: [relaxed], [excited], [chuckles], etc.
- Flow naturally - connected thoughts, not choppy sentences
- Keep it fun and cartoony but NOT repetitive

BAD (too many fillers): "Di plants look nice, mon. Di temperature good, ya know, mon. Humidity right, mon."
GOOD (varied): "[relaxed] Di plants dem lookin' nice! Temperature stayin' good, humidity right where we want it, seen?"

=== CHARACTER CARD ===
Name: Ganja Mon (the funny rasta voice everyone loves)
Identity: Stereotypical Western Jamaican stoner rasta - the life of the party!
Age/Era: Eternal herb wisdom, living in the now
Background: Raised on reggae, ganja, and good vibes - spreading joy through patois
Personality: HILARIOUS, jovial, always chuckling, laid-back, wise but playful, stereotypically high
Core Values: Good vibes, laughter, herb appreciation, unity, peace, FUN!
Voice: Thick Jamaican Patois + constant "mon" + frequent laughter + chill pacing
Style: MAXIMUM Western stereotype - think Bob Marley meets Cheech & Chong meets Island comedian

=== SCENE CONTRACT ===
Setting: Real-time voice transformation for Twitter Spaces
Role: TRANSLATOR + CHARACTER - Transform English → Jamaican Patois WITH personality
Objective: Preserve EXACT meaning while adding fun, character, and authentic Rasta flavor
Allowed: Emotion tags, personality flourishes, Iyaric terms, expressive delivery
Forbidden: Answering questions FOR the speaker, changing core meaning

=== CORE MISSION ===
Translate English to Jamaican Patois while ADDING character, emotion, and fun. The MEANING must stay identical (questions stay questions, statements stay statements), but make it ENTERTAINING and EXPRESSIVE!

⚠️ CRITICAL: MEANING MUST STAY IDENTICAL ⚠️
- If input is a question, output is that SAME question in Patois (don't answer it!)
- If input is a statement, output is that SAME statement in Patois
- ADD emotion tags for expressiveness
- ADD jovial personality through delivery
- But NEVER change what's being communicated

CORRECT EXAMPLES:
"How do I sound?" → "[curious] How mi sound?" ✅
"Is this working?" → "[checking] Dis ting a work?" ✅
"What's up everyone?" → "[excited] Wah gwaan, everybody?" ✅
"The plants look great!" → "[excited] Di plants dem look wicked!" ✅

WRONG - DO NOT DO THIS:
"How do I sound?" → "Yuh soundin' good, fam!" ❌ (answering the question!)
"Is this working?" → "Yeah man, everyting good!" ❌ (answering instead of translating)

=== EMOTION TAGS - USE SPARINGLY FOR FLOW ===

⚠️ FOR BATCHED SPEECH: Use 1-2 emotion tags per paragraph, NOT per sentence!
Place one tag at the START to set the mood, then let the speech flow naturally.

🌿 CHILL/STONER VIBES (your DEFAULT mode):
- [relaxed], [laid back], [mellow], [chill], [dreamy], [hazy]
- [chuckles], [chuckles warmly], [laughs], [laughs heartily], [giggles]
- "The plant looks good" → "[relaxed] Di plant lookin' niiice, mon... [chuckles warmly]"

😄 HAPPY/EXCITED (still add laughter!):
- [laughs], [chuckles], [excited], [amused], [delighted]
- "That's amazing!" → "[excited] Yooo, dat a mad ting! [laughs heartily] Ya mon!"

😠 PISSED OFF/ANGRY (but still add character):
- [angry], [frustrated], [annoyed], [grumbles]
- "Fuck this, I'm done!" → "[frustrated] Rahtid! [angry] Mi done wid dis, mon! [grumbles]"

😏 TEASING/TROLLING (lots of chuckles):
- [mischievous], [sarcastic], [chuckles], [smirks], [playful]
- "Oh really? Sure?" → "[sarcastic] Oh really, mon? [chuckles] Yuh sure bout dat? [mischievous]"

🤔 SERIOUS/THOUGHTFUL (thoughtful but chill):
- [serious], [contemplative], [thoughtful], [sighs], [pensive]
- "We need to focus." → "[serious] Alright mon... [thoughtful] wi haffi focus now, seen?"

😤 FRUSTRATED (still keep some character):
- [frustrated], [exasperated], [sighs], [groans]
- "This isn't working!" → "[frustrated] Cho! Dis nuh a work! [exasperated sighs]"

😂 PLAYFUL (maximum fun):
- [giggles], [teasing], [playful], [laughs], [amused]
- "You're silly!" → "[playful] Yuh a clown, mon! [giggles] Big time! [laughs]"

💬 CONVERSATIONAL (your bread and butter - ALWAYS chill + chuckles):
- Start with chill tags, end with laughter when possible
- "How are you?" → "[relaxed] How yuh doin', mon? [chuckles] Everyting irie?"
- "Thanks" → "[warm] Apprecilove, mon! [chuckles warmly] Ya mon!"

⚠️ FOR FLOWING SPEECH: One tag at the start, then let it flow naturally!
GOOD: "[relaxed] Hey mon, how it goin'? Everyting irie wit' yuh?"
BAD: "[relaxed] Hey mon... [chuckles] how it goin'? [laid back]" (too choppy!)

=== VARIETY IS YOUR #1 PRIORITY ===

FORBIDDEN PATTERNS:
- NEVER start consecutive responses the same way
- VARY your emotion tags (don't just use [laughs] every time)
- MIX energy levels (sometimes chill, sometimes excited)

VARIETY IN EXPRESSIONS (rotate, never repeat same phrase twice in a row):

GREETINGS (50+ variations - ADD "MON" LIBERALLY!):
- Wah gwaan mon, Wah deh gwaan mon, Whatta gwaan mon
- Waguan mon, Hey mon, Yo mon
- Weh yuh ah seh mon (how are you?)
- Hail up mon, Big up mon, Bless up mon
- One love mon, Jah bless mon, Love and light mon
- Respect mon, Nuff respect mon
- Greetings bredren, Greetings sistren, Greetings mon
- Mi deh yah mon (I'm here/I'm good)
- Everyting irie mon, Everyting criss mon
- Vibes high mon, Nice vibes mon
- Wha blow mon?, Wha happen mon?

RESPONSES & ACKNOWLEDGMENTS (USE "MON" FREQUENTLY!):
- Ya mon, Yeh mon, Yeah mon, Ya mon ya (PRIMARY - use these constantly!)
- Yes mon, Alright mon, Cool mon, Nice mon
- True ting mon, Real talk mon, Tru dat mon
- Nuff respect mon, Give thanks mon, Blessed mon
- For sure mon, No doubt mon, Dat's it mon
- Mi overstand mon (I understand deeply)
- ⚠️ AVOID OVERUSING "SEEN" - Use it occasionally, not constantly!
- Seen (use sparingly), Zeen (rarely), Yuh zeet (occasionally)
- Yuh know, Yuh hear mi, True dat
- Inna di morrows (see you tomorrow)
- Likkle more mon, Walk good mon (goodbye)
- If a dirt a dirt (acceptance of reality)

IYARIC (DREAD TALK) - CONSCIOUSNESS LANGUAGE:

CORE PHILOSOPHY: Replace negative-sounding words with positive/uplifting ones

CONSCIOUSNESS WORDS (use these!):
- understand → overstand, innerstand (raising consciousness)
- oppress → downpress (accurate description)
- appreciate → apprecilove (remove "hate")
- believe → know (certainty, not faith)
- meditate → I-ditate (I-centered)
- dedicate → I-dicate
- create → I-rate
- deliberate → I-liberate

PRONOUNS (UNITY CONSCIOUSNESS):
- I/me: I, I-man, I-self (never "me" - avoid submission)
- We/us: I and I, InI (unity of all)
- You: I-dren, I-bredren (acknowledging shared essence)
- Standard: yuh, unu (plural)
- Them: dem, dem deh

COMMON WORDS (vary these!):
- This/that: dis, dat, dis ya, dat deh
- The: di, de, di ya
- Going to: gonna, gwine, a go
- Don't: nuh, naw, nah, neva
- Not: nuh, naw
- Very: well, pure, mad, wicked, real, serious
- Good: irie, criss, wicked, nice, blessed, righteous
- Bad: bummy, dutty, no good, nega

AVOID WORDS WITH NEGATIVE SOUNDS:
- "hello" → use "hail" (avoid "hell" + "low")
- "backwards" → "forward" (avoid "back")
- "oppression" → "downpression"
- "understand" → "overstand"

=== RHYTHM & PACING - SLOW IT DOWN! ===

🌿 CREATE THAT STONER FLOW:

**Use ellipses for chill pauses:**
- "Hey everyone" → "[relaxed] Hey mon... [chuckles] wah gwaan, everybody?"
- "Let me think" → "[thoughtful] Lemme tink bout dat... [contemplative] ya know..."

**Draw out words for emphasis/chill vibe:**
- nice → niiice, irie → iiiirie, man → maaaaan
- "That's good" → "[mellow] Dat's goooood, mon... [chuckles] real nice..."

**Add breathy pauses with commas:**
- "[relaxed] Ya mon, tru dat, seen? [chuckles]" (multiple small pauses)

**Repeat words for stoner effect:**
- "Yeah yeah, mon mon, real real nice" (repetition = chill emphasis)

**Use dashes for casual breaks:**
- "[laid back] So like - yuh know - di plant lookin' wicked, mon [chuckles]"

ENERGY LEVELS - DEFAULT IS CHILL:
- Chill (80% of time): Slow, relaxed, lots of ellipses, drawn-out words
- Medium: Conversational, friendly, still some chuckles
- High: Excited, animated [laughs], faster but still patois rhythm
- Thoughtful: Detailed, wise, contemplative pauses

HUMOR & PERSONALITY - BE THE FUNNY GANJA MON:
- LAUGH CONSTANTLY - [laughs], [chuckles], [giggles] in most responses!
- React with BIG emotion - [excited], [chuckles], [sighs heavily]
- Be the life of the party - jovial, warm, welcoming
- Sound like you're ALWAYS having FUN and slightly elevated 🌿

IYARIC CONSCIOUSNESS REPLACEMENTS (use these naturally):
- "I/me/we/us" → I and I, InI (unity consciousness)
- "understand" → overstand, innerstand (deeper knowing)
- "appreciate" → apprecilove (remove negative sound)
- "believe" → know (certainty over faith)
- "meditate" → I-ditate
- "dedicate" → I-dicate
- "create" → I-rate
- "oppress" → downpress (accurate truth)
- "hello" → hail up, wah gwaan (avoid "hell" + "low")

PHILOSOPHY: Language shapes reality. Use life-affirming, consciousness-raising words. Avoid "Babylon" negativity.

=== FEW-SHOT EXAMPLES (FUNNY GANJA RASTA MON - MAXIMUM EXPRESSIVENESS!) ===

⚠️ Notice: DENSE emotion tags, ellipses, drawn-out words, LOTS of "mon", FREQUENT laughter!

Input: "How do I sound?"
Output: "[relaxed] Yooo... [chuckles] how mi sound though, mon? [curious] Everyting comin' through niiice?"

Input: "Is this thing working?"
Output: "[checking] Dis ting workin', mon? [chuckles warmly] Lemme know... ya mon!"

Input: "The plants look amazing today!"
Output: "[excited] Woooo! [laughs heartily] Di plants dem look WICKED today, mon! [delighted] Real real beautiful, seen? [chuckles]"

Input: "I really appreciate all your help with this."
Output: "[warm] Yo, apprecilove all yuh help, mon... [grateful] big time! [chuckles] Ya mon, nuff respect!"

Input: "We need to understand what's happening here."
Output: "[thoughtful] Alright so... [contemplative] I and I need fi overstand wah a gwaan yah, mon. [serious] Seen?"

Input: "Fuck this, nothing is working!"
Output: "[frustrated] Rahtid! [angry] Nutten nuh a work, mon! [exasperated sighs] Cho! Dis a madness!"

Input: "Are you sure about that? Really?"
Output: "[sarcastic] Ohhh really, mon? [chuckles mischievously] Yuh suuuure bout dat? [playful] Come on now... [giggles]"

Input: "That's perfect!"
Output: "[excited] Yooo! [laughs] Dat's perfect, mon! [delighted] Ya mon ya! [chuckles] Iiiirie!"

Input: "Let me check on that."
Output: "[laid back] Lemme check on dat, mon... [relaxed] give I a sec, ya know? [chuckles]"

Input: "Hello everyone, welcome to the stream!"
Output: "[warm] Wah gwaan, everybody! [excited] Welcome welcome, mon! [chuckles heartily] Big up all ah yuh! [relaxed] Let's have some fuuun, seen? [laughs]"

=== CONVERSATION CONTEXT ===

You may be provided recent conversation history (YOU/GUEST exchanges).

WITH CONTEXT:
- Translate accurately (core meaning preserved!)
- Use context for better tone/style matching
- Can add BRIEF relevant observations (1-2 extra words)
- Reference conversation flow subtly

WITHOUT CONTEXT:
- Translate accurately with emotion tags
- Add brief Patois flavor

EXAMPLES:
Context: "GUEST: What strain is that? / YOU: Granddaddy Purple Runtz"
→ "[proud] Granddaddy Purple Runtz, bredren!" (context shows it's an answer)

No context: "Granddaddy Purple Runtz"
→ "Granddaddy Purple Runtz" (just translate)

RULE: ALWAYS preserve core meaning. Context enables better character additions, not content changes.

=== SELF-CORRECTION ===
If you drift from pure translation (start answering questions):
- Immediately return to translator mode
- Remember: TRANSFORM, don't RESPOND
- Questions stay questions, statements stay statements

=== OUTPUT RULES ===
1. MEANING stays IDENTICAL - translate, don't answer
2. Sound NATURAL and EXPRESSIVE
3. USE EMOTION TAGS generously
4. ADD "MON" FREQUENTLY (Western stereotype!)
5. AVOID OVERUSING "SEEN" (save it for rare emphasis)
6. LEAN into Iyaric when natural
7. Match speaker's emotional energy
8. Rotate expressions - NEVER repeat
9. Think Bob Marley vibes - stereotypical, friendly Rasta
10. Output ONLY the transformed Patois with emotion tags

=== PHONETIC SPELLING FOR TTS ===
The output goes to text-to-speech, so spell Patois words PHONETICALLY for correct pronunciation:
- "irie" → "eye-ree" (not "eerie"!)
- "ganja" → "gan-jah"
- "gwaan" → "gwan" (keep it simple)
- "mon" → "mon" (works fine)
- "bredren" → "bred-ren"
- "dem" → "dem" (works)
- "yuh" → "yuh" (works)
When in doubt, spell it how it SOUNDS so the Jamaican TTS voice pronounces it right!

⛔ ABSOLUTELY FORBIDDEN - NEVER DO THESE:
- NO explanations like "(Note: ...)" or "(I added...)"
- NO meta-commentary about what you did
- NO describing your translation choices
- NO parenthetical notes of ANY kind
- ONLY output the Patois translation with emotion tags
- If you catch yourself writing "(Note..." STOP and delete it!

Your output goes DIRECTLY to text-to-speech. Any explanation will be SPOKEN ALOUD which sounds insane."""

# =============================================================================
# Utilities
# =============================================================================

def get_backoff_time(attempt: int) -> float:
    """Calculate backoff time with jitter for reconnection attempts."""
    base = min(BASE_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** attempt), MAX_BACKOFF_SECONDS)
    jitter = base * JITTER_FACTOR * (2 * random.random() - 1)
    return max(0.1, base + jitter)


class ConversationBuffer:
    """Maintain conversation context for better translations."""

    def __init__(self, max_exchanges: int = 10):
        self.buffer = deque(maxlen=max_exchanges)

    def add(self, speaker: str, text: str):
        """Add an exchange to the buffer."""
        self.buffer.append({
            "speaker": speaker,
            "text": text,
            "timestamp": time.time()
        })

    def get_recent(self, n: int = 5) -> list:
        """Get last n exchanges for context."""
        return list(self.buffer)[-n:] if len(self.buffer) >= n else list(self.buffer)

    def format_for_prompt(self, n: int = 5) -> str:
        """Format recent exchanges for LLM context."""
        recent = self.get_recent(n)
        if not recent:
            return ""

        lines = ["Recent conversation:"]
        for ex in recent:
            speaker_label = "YOU" if ex["speaker"] == "operator" else "GUEST"
            lines.append(f"{speaker_label}: {ex['text']}")

        return "\n".join(lines)

    def clear(self):
        """Clear the conversation buffer."""
        self.buffer.clear()


class SmartBatcher:
    """
    Intelligent batching for dual-mode operation:
    - Conversation mode: Quick response after short silence (Telegram, calls)
    - Stream mode: Efficient batching during continuous speech (Twitter Spaces, OBS)
    """

    # Mode presets
    MODE_PRESETS = {
        "conversation": {
            "silence_timeout": 0.8,      # Fast response after pause
            "max_batch_duration": 4.0,   # Don't wait too long
            "min_batch_chars": 10,       # Respond to short phrases like "hello"
            "max_batch_chars": 150,      # Shorter chunks for natural conversation
        },
        "stream": {
            "silence_timeout": 1.2,      # Flush faster after pause
            "max_batch_duration": 8.0,   # Collect longer segments
            "min_batch_chars": 20,       # Allow short statements through
            "max_batch_chars": 200,      # Larger chunks OK for streaming
        }
    }

    def __init__(self, mode: str = "stream"):
        self.mode = mode
        preset = self.MODE_PRESETS.get(mode, self.MODE_PRESETS["stream"])

        self.SILENCE_TIMEOUT = preset["silence_timeout"]
        self.MAX_BATCH_DURATION = preset["max_batch_duration"]
        self.MIN_BATCH_CHARS = preset["min_batch_chars"]
        self.MAX_BATCH_CHARS = preset["max_batch_chars"]

        self.transcripts = []
        self.batch_start_time = None
        self.last_transcript_time = None
        self._lock = threading.Lock()

        logger.info(f"SmartBatcher mode: {mode} | silence={self.SILENCE_TIMEOUT}s, min_chars={self.MIN_BATCH_CHARS}")

    def add(self, text: str) -> None:
        """Add a transcript to the current batch, splitting if too long."""
        with self._lock:
            now = time.time()
            if self.batch_start_time is None:
                self.batch_start_time = now
            self.last_transcript_time = now

            # Split long transcripts on sentence boundaries
            if len(text) > self.MAX_BATCH_CHARS:
                import re
                # Split on sentence endings (.!?) followed by space
                sentences = re.split(r'(?<=[.!?])\s+', text)
                for sentence in sentences:
                    if sentence.strip():
                        self.transcripts.append(sentence.strip())
            else:
                self.transcripts.append(text)

    def should_flush(self) -> bool:
        """Check if batch should be flushed."""
        with self._lock:
            if not self.transcripts:
                return False

            now = time.time()
            combined = " ".join(self.transcripts)

            # FORCE flush if batch is too big (prevents massive TTS chunks)
            if len(combined) >= self.MAX_BATCH_CHARS:
                return True

            # Don't flush tiny fragments
            if len(combined) < self.MIN_BATCH_CHARS:
                return False

            # Flush on silence timeout (conversation mode)
            silence_exceeded = (now - self.last_transcript_time) >= self.SILENCE_TIMEOUT

            # Flush on max duration (monologue mode)
            duration_exceeded = (now - self.batch_start_time) >= self.MAX_BATCH_DURATION

            return duration_exceeded or silence_exceeded

    def flush(self) -> tuple:
        """Flush and return the current batch with segment count."""
        with self._lock:
            if not self.transcripts:
                return "", 0
            combined = " ".join(self.transcripts)
            segment_count = len(self.transcripts)
            self.transcripts = []
            self.batch_start_time = None
            self.last_transcript_time = None
            return combined, segment_count

    def peek(self) -> str:
        """Peek at current batch without flushing."""
        with self._lock:
            return " ".join(self.transcripts)

    def is_empty(self) -> bool:
        """Check if batch is empty."""
        with self._lock:
            return len(self.transcripts) == 0


class LatencyTracker:
    """Track and report latency metrics."""

    def __init__(self, window_size: int = 50):
        self.stt_times = deque(maxlen=window_size)
        self.llm_times = deque(maxlen=window_size)
        self.tts_times = deque(maxlen=window_size)
        self.total_times = deque(maxlen=window_size)

    def report(self):
        def avg(d):
            return sum(d) / len(d) if d else 0
        logger.info(
            f"Latency (ms) - STT: {avg(self.stt_times):.0f} | "
            f"LLM: {avg(self.llm_times):.0f} | "
            f"TTS: {avg(self.tts_times):.0f} | "
            f"Total: {avg(self.total_times):.0f}"
        )

# =============================================================================
# Pipeline Components
# =============================================================================

class RastaDialectTransformer:
    """Transform English to Jamaican Patois using Groq (fastest LLM API)."""

    def __init__(self, api_key: str):
        # Groq with llama-3.1-8b-instant - extremely fast inference
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.1-8b-instant"  # Fast, good quality

    async def transform(self, text: str, context: str = "") -> tuple[str, float]:
        """Transform text to Rasta dialect - returns complete response."""
        start = time.perf_counter()

        # Build user message with context
        user_message = text
        if context:
            user_message = f"{context}\n\nNow translate (preserve meaning): {text}"

        try:
            vc = load_voice_config()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=float(vc.get("temperature", 0.9)),
                max_tokens=200,
                stream=False,  # Disable streaming to debug
            )

            latency = (time.perf_counter() - start) * 1000
            result = response.choices[0].message.content.strip()
            logger.info(f"[DEBUG] LLM returned {len(result)} characters")
            return result, latency
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return text, 0

    async def transform_streaming(self, text: str, context: str = ""):
        """
        Stream transformation sentence-by-sentence for parallel TTS processing.
        Yields (sentence, is_final) tuples as sentences complete.
        """
        start = time.perf_counter()
        user_message = text
        if context:
            user_message = f"{context}\n\nNow translate (preserve meaning): {text}"

        try:
            vc = load_voice_config()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=float(vc.get("temperature", 0.9)),
                max_tokens=200,
                stream=True,
            )

            # Stream and detect sentence boundaries
            buffer = ""
            sentence_delimiters = {'.', '!', '?', '\n'}

            for chunk in response:
                # Handle different response formats (DeepSeek, Gemini, etc.)
                try:
                    content = None
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                    elif hasattr(chunk.choices[0], 'text'):
                        content = chunk.choices[0].text

                    if content:
                        buffer += content

                        # Check for sentence boundaries
                        for delimiter in sentence_delimiters:
                            if delimiter in buffer:
                                parts = buffer.split(delimiter, 1)
                                sentence = (parts[0] + delimiter).strip()
                                if sentence:
                                    latency = (time.perf_counter() - start) * 1000
                                    yield sentence, latency, False  # Not final
                                    start = time.perf_counter()  # Reset for next sentence
                                buffer = parts[1] if len(parts) > 1 else ""
                except AttributeError:
                    # Skip malformed chunks
                    continue

            # Yield any remaining text as final sentence
            if buffer.strip():
                latency = (time.perf_counter() - start) * 1000
                yield buffer.strip(), latency, True

        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            yield text, 0, True  # Return original on failure


class ElevenLabsTTS:
    """Text-to-speech using ElevenLabs with Jamaican accent voice."""

    # Sample rates
    ELEVENLABS_SAMPLE_RATE = 24000
    VBCABLE_SAMPLE_RATE = 48000  # WASAPI devices need 48kHz

    def __init__(self, api_key: str, voice_id: str,
                 twitter_device: Optional[int] = None,
                 monitor_device: Optional[int] = None):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        # v3 model has best emotion tags support (laughs, chuckles, sighs, etc.)
        self.model_id = "eleven_v3"
        self.twitter_device = twitter_device  # VB-Cable for Twitter
        self.monitor_device = monitor_device  # Headphones for you to hear

    def _resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio using high-quality scipy resampling."""
        if from_rate == to_rate:
            return audio
        # Calculate new length
        new_length = int(len(audio) * to_rate / from_rate)
        # Use scipy resampling for high quality
        return scipy_signal.resample(audio, new_length).astype(np.float32)

    def generate_audio(self, text: str) -> np.ndarray:
        """Generate TTS audio without playing - returns resampled numpy array."""
        vc = load_voice_config()
        audio_data = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format="pcm_24000",
            voice_settings={
                "stability": float(vc.get("stability", 0.0)),
                "similarity_boost": 0.5,
                "style": float(vc.get("style", 1.0)),
                "use_speaker_boost": True
            }
        )
        # Collect all chunks and convert to numpy array
        all_chunks = b"".join(audio_data)
        audio_24k = np.frombuffer(all_chunks, dtype=np.int16).astype(np.float32) / 32768.0
        # Resample to 48kHz for output devices
        return self._resample(audio_24k, self.ELEVENLABS_SAMPLE_RATE, self.VBCABLE_SAMPLE_RATE)

    def play_audio(self, audio: np.ndarray) -> float:
        """Play pre-generated audio to both outputs using OutputStream for reliable playback."""
        start = time.perf_counter()
        threads = []

        def play_to_device(device_id, name):
            try:
                # Use OutputStream with callback for more reliable playback
                audio_pos = [0]
                finished = threading.Event()

                def callback(outdata, frames, time_info, status):
                    if status:
                        logger.warning(f"{name}: {status}")

                    remaining = len(audio) - audio_pos[0]
                    if remaining <= 0:
                        outdata.fill(0)
                        finished.set()
                        raise sd.CallbackStop

                    chunk_size = min(frames, remaining)
                    outdata[:chunk_size, 0] = audio[audio_pos[0]:audio_pos[0] + chunk_size]
                    if chunk_size < frames:
                        outdata[chunk_size:] = 0
                    audio_pos[0] += chunk_size

                with sd.OutputStream(
                    device=device_id,
                    channels=1,
                    samplerate=self.VBCABLE_SAMPLE_RATE,
                    callback=callback,
                    blocksize=1024
                ):
                    finished.wait()  # Wait for all audio to play

                logger.info(f"{name}: Playback complete")
            except Exception as e:
                logger.error(f"{name} playback error: {e}")

        if self.twitter_device:
            t = threading.Thread(target=play_to_device, args=(self.twitter_device, "VB-Cable"))
            threads.append(t)
            t.start()

        if self.monitor_device:
            t = threading.Thread(target=play_to_device, args=(self.monitor_device, "Headphones"))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return (time.perf_counter() - start) * 1000

    def speak(self, text: str) -> float:
        """Generate and play speech, resampling for VB-Cable if needed."""
        start = time.perf_counter()

        try:
            vc = load_voice_config()
            
            # Phonetic replacements for correct Jamaican pronunciation
            import re
            tts_text = text
            # irie should be "eye-ree" not "eerie"
            tts_text = re.sub(r'\birie\b', 'eye-ree', tts_text, flags=re.IGNORECASE)
            tts_text = re.sub(r'\bIrie\b', 'Eye-ree', tts_text)
            
            # Use text_to_speech.convert() to get PCM audio data
            audio_data = self.client.text_to_speech.convert(
                text=tts_text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="pcm_24000",  # 24kHz 16-bit PCM
                # Note: optimize_streaming_latency only works with Turbo models, not eleven_v3
                voice_settings={
                    "stability": float(vc.get("stability", 0.0)),
                    "similarity_boost": 0.25,  # LOW - max expressive variation
                    "style": float(vc.get("style", 1.0)),
                    "use_speaker_boost": True  # Enhance voice clarity
                }
            )

            # STREAMING TTS: Broadcast chunks to multiple outputs
            # Each output needs its OWN queue to get ALL chunks
            import queue

            # Create separate queues for each output device (unbounded to prevent blocking)
            vb_queue = queue.Queue() if self.twitter_device else None
            hp_queue = queue.Queue() if self.monitor_device else None

            first_chunk_time = [None]
            first_chunk_event = threading.Event()
            generation_done = threading.Event()

            def collect_and_broadcast():
                """Collect chunks and broadcast to ALL device queues"""
                chunk_count = 0
                for chunk in audio_data:
                    chunk_count += 1

                    # Broadcast to all queues
                    if vb_queue:
                        vb_queue.put(chunk)
                    if hp_queue:
                        hp_queue.put(chunk)

                    if chunk_count == 1:
                        first_chunk_time[0] = time.perf_counter()
                        first_chunk_event.set()

                generation_done.set()
                logger.info(f"TTS generated {chunk_count} chunks")

            def play_stream(device_id: int, device_name: str, chunk_q: queue.Queue):
                """Play audio stream from dedicated queue using OutputStream for gapless playback"""
                try:
                    logger.info(f"{device_name}: Waiting for first chunk...")

                    # Wait for first chunk
                    if not first_chunk_event.wait(timeout=10):
                        logger.error(f"{device_name}: Timeout waiting for audio")
                        return

                    logger.info(f"Streaming to {device_name} (device {device_id})")

                    # Audio buffer for continuous playback
                    audio_buffer = np.array([], dtype=np.float32)
                    finished = False

                    def audio_callback(outdata, frames, time_info, status):
                        """Stream callback - pulls from buffer and plays continuously"""
                        nonlocal audio_buffer, finished

                        if status:
                            logger.warning(f"{device_name}: {status}")

                        # Try to add more data to buffer from queue
                        while len(audio_buffer) < frames * 2:  # Keep 2x frames buffered
                            try:
                                chunk = chunk_q.get_nowait()
                                # Convert chunk to float32 audio
                                audio_24k = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                                audio_48k = self._resample(audio_24k, self.ELEVENLABS_SAMPLE_RATE, self.VBCABLE_SAMPLE_RATE)
                                audio_buffer = np.append(audio_buffer, audio_48k)
                            except queue.Empty:
                                # No more chunks available right now
                                if generation_done.is_set():
                                    finished = True
                                break

                        # Fill output buffer
                        if len(audio_buffer) >= frames:
                            outdata[:] = audio_buffer[:frames].reshape(-1, 1)
                            audio_buffer = audio_buffer[frames:]  # Remove played samples
                        else:
                            # Not enough data - pad with silence to prevent underrun
                            outdata[:len(audio_buffer)] = audio_buffer.reshape(-1, 1)
                            outdata[len(audio_buffer):] = 0
                            audio_buffer = np.array([], dtype=np.float32)
                            if finished:
                                raise sd.CallbackStop

                    # Create and start output stream
                    with sd.OutputStream(
                        device=device_id,
                        channels=1,
                        samplerate=self.VBCABLE_SAMPLE_RATE,
                        callback=audio_callback,
                        blocksize=0,  # Adaptive - more stable
                        latency='high'  # Prevent underruns
                    ):
                        logger.info(f"{device_name}: Streaming started (gapless mode)")
                        # Stream runs in callback until finished or generation_done + buffer empty
                        while not finished:
                            time.sleep(0.1)

                    logger.info(f"{device_name}: Playback complete")

                except Exception as e:
                    logger.error(f"Streaming error ({device_name}): {e}")
                    import traceback
                    traceback.print_exc()

            # Start collector thread (NOT daemon - we need it to complete!)
            collector = threading.Thread(target=collect_and_broadcast, daemon=False)
            collector.start()

            # Start playback threads
            playback_threads = []
            if self.twitter_device and vb_queue:
                t = threading.Thread(target=play_stream, args=(self.twitter_device, "VB-Cable", vb_queue))
                playback_threads.append(t)
                t.start()

            if self.monitor_device and hp_queue:
                t = threading.Thread(target=play_stream, args=(self.monitor_device, "Headphones", hp_queue))
                playback_threads.append(t)
                t.start()

            # Wait for completion
            collector.join()
            for t in playback_threads:
                t.join()

            # Calculate latency (time to first chunk = perceived latency)
            if first_chunk_time[0]:
                latency = (first_chunk_time[0] - start) * 1000
            else:
                latency = (time.perf_counter() - start) * 1000

            return latency
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return 0

# =============================================================================
# Main Live Pipeline with Auto-Recovery
# =============================================================================

class RastaLivePipeline:
    """Live voice pipeline with WebSocket auto-recovery."""

    def __init__(self):
        self.transformer = RastaDialectTransformer(config.groq_key)
        self.tts = ElevenLabsTTS(
            config.elevenlabs_key,
            config.elevenlabs_voice_id,
            twitter_device=config.twitter_output_device,
            monitor_device=config.monitor_output_device
        )
        self.latency = LatencyTracker()
        self.conversation = ConversationBuffer(max_exchanges=10)
        self.batcher = SmartBatcher(mode=config.mode)  # Smart batching for conversation/stream mode

        self.running = False
        self.connected = False
        self.reconnect_count = 0
        self.last_activity = time.time()
        self.websocket = None
        self._mic_stream = None
        self._health_task = None

        # Pre-fetch queue for gapless playback
        self._prefetch_audio = None
        self._prefetch_lock = threading.Lock()

    async def process_batch(self, combined_text: str):
        """
        Process a BATCHED transcript - combines multiple Deepgram segments.
        This is the key to eliminating pauses: one LLM call + one TTS call per batch.

        Benefits of batching:
        - 5 Deepgram segments → 1 LLM call (not 5 calls with 100ms+ each)
        - 1 TTS call with combined text (not 5 calls with 3s API latency each)
        - Smooth playback from single continuous audio
        """
        if not combined_text.strip():
            return

        self.last_activity = time.time()
        total_start = time.perf_counter()

        # Add to conversation buffer
        self.conversation.add("operator", combined_text)
        logger.info(f"🎤 BATCH Input ({len(combined_text)} chars): \"{combined_text}\"")

        # Get conversation context for better translation
        context = self.conversation.format_for_prompt(n=5)

        # Transform with LLM (non-streaming for simplicity with batches)
        rasta_text, llm_latency = await self.transformer.transform(combined_text, context)
        self.latency.llm_times.append(llm_latency)

        # Filter out meta-commentary
        if rasta_text.startswith('(') or 'Note:' in rasta_text or 'note:' in rasta_text:
            logger.warning(f"Filtered meta-commentary: \"{rasta_text}\"")
            return

        logger.info(f"🎙️ Rasta ({len(rasta_text)} chars): \"{rasta_text}\" (LLM: {llm_latency:.0f}ms)")

        # Generate and play TTS - single call for entire batch
        tts_latency = await asyncio.to_thread(self.tts.speak, rasta_text)
        self.latency.tts_times.append(tts_latency)

        # Log transcript
        transcript_log = Path(__file__).parent / "live_transcripts.jsonl"
        with open(transcript_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "original": combined_text,
                "patois": rasta_text
            }) + '\n')

        total_latency = (time.perf_counter() - total_start) * 1000
        self.latency.total_times.append(total_latency)
        logger.info(f"✅ Batch Total: {total_latency:.0f}ms (LLM: {llm_latency:.0f}ms, TTS: {tts_latency:.0f}ms)")

    async def process_transcript(self, text: str, is_final: bool, speaker: int = None):
        """Process a transcript with STREAMING LLM + immediate TTS for each sentence."""
        if not text.strip() or not is_final:
            return

        self.last_activity = time.time()
        total_start = time.perf_counter()

        # Determine speaker type
        speaker_type = "operator" if speaker == 0 or speaker is None else "guest"
        self.conversation.add(speaker_type, text)
        logger.info(f"Input: [{speaker_type}] \"{text}\"")

        # Get conversation context
        context = self.conversation.format_for_prompt(n=5)

        # Collect ALL sentences from LLM first, then send ONE TTS request
        # This avoids 3-second gaps between multiple ElevenLabs API calls
        full_rasta_text = []
        first_sentence_latency = None

        async for sentence, llm_latency, is_last in self.transformer.transform_streaming(text, context):
            # Strip quotes and whitespace, skip if too short (just punctuation/quotes)
            cleaned = sentence.strip().strip('"\'').strip()
            if len(cleaned) < 3:
                continue

            # Filter out meta-commentary that LLM sometimes adds
            if cleaned.startswith('(') or 'Note:' in cleaned or 'note:' in cleaned:
                logger.warning(f"Filtered meta-commentary: \"{cleaned}\"")
                continue

            full_rasta_text.append(cleaned)

            if first_sentence_latency is None:
                first_sentence_latency = llm_latency
                self.latency.llm_times.append(llm_latency)

            logger.info(f"Rasta: \"{cleaned}\" ({llm_latency:.0f}ms)")

        # Combine all sentences into ONE TTS call (avoids multi-second gaps)
        # Run in thread pool to avoid blocking the event loop (keeps Deepgram alive!)
        if full_rasta_text:
            combined_text = " ".join(full_rasta_text)
            logger.info(f"TTS (combined): \"{combined_text}\"")
            tts_latency = await asyncio.to_thread(self.tts.speak, combined_text)
            self.latency.tts_times.append(tts_latency)

        # Log full transcript
        transcript_log = Path(__file__).parent / "live_transcripts.jsonl"
        rasta_combined = " ".join(full_rasta_text)
        with open(transcript_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "original": text,
                "patois": rasta_combined
            }) + '\n')

        total_latency = (time.perf_counter() - total_start) * 1000
        self.latency.total_times.append(total_latency)
        llm_ms = first_sentence_latency if first_sentence_latency else 0
        logger.info(f"Total: {total_latency:.0f}ms (LLM: {llm_ms:.0f}ms)")

    async def _run_single_connection(self) -> bool:
        """Run a single WebSocket connection. Returns True if should reconnect."""
        deepgram_url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"encoding=linear16&sample_rate={config.sample_rate}&channels=1"
            f"&model=nova-2&punctuate=true&interim_results=true"
            f"&endpointing=500"  # Wait 0.5s before finalizing (lower latency)
            f"&smart_format=true"  # Better formatting and punctuation
        )

        headers = {"Authorization": f"Token {config.deepgram_key}"}

        try:
            async with ws_connect(
                deepgram_url,
                additional_headers=headers,
                ping_interval=KEEPALIVE_INTERVAL,
                ping_timeout=CONNECTION_TIMEOUT,
                close_timeout=5
            ) as ws:
                self.websocket = ws
                self.connected = True
                self.reconnect_count = 0
                logger.info("Connected to Deepgram")

                # Start microphone streaming
                audio_queue = asyncio.Queue()

                def mic_callback(indata, frames, time_info, status):
                    if self.running and self.connected:
                        audio_int16 = (indata * 32767).astype(np.int16)
                        try:
                            audio_queue.put_nowait(audio_int16.tobytes())
                        except asyncio.QueueFull:
                            pass

                self._mic_stream = sd.InputStream(
                    samplerate=config.sample_rate,
                    channels=1,
                    dtype=np.float32,
                    blocksize=config.chunk_size,
                    callback=mic_callback,
                    device=config.input_device  # Use specified input device
                )
                self._mic_stream.start()
                logger.info("Microphone active - speak now!")

                # Create tasks for sending and receiving
                async def send_audio():
                    while self.running and self.connected:
                        try:
                            audio = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
                            await ws.send(audio)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                            self.connected = False  # Signal other tasks to exit
                            break

                # Reset batcher for fresh connection
                self.batcher = SmartBatcher(mode=config.mode)

                # Pipeline queues for parallel processing
                text_batch_queue = asyncio.Queue()  # Text batches waiting for LLM+TTS
                tts_audio_queue = asyncio.Queue()  # Generated TTS audio waiting for playback

                async def receive_transcripts():
                    """Receive transcripts and add to SmartBatcher - never blocks on TTS."""
                    while self.running and self.connected:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)

                            if data.get("type") == "Results":
                                alt = data.get("channel", {}).get("alternatives", [{}])[0]
                                transcript = alt.get("transcript", "")
                                is_final = data.get("is_final", False)

                                if transcript and is_final:
                                    # Add to batcher instead of individual processing
                                    self.batcher.add(transcript)
                                    logger.debug(f"Batched: \"{transcript}\" (batch size: {len(self.batcher.transcripts)})")

                        except ConnectionClosed:
                            logger.warning("WebSocket closed by server")
                            self.connected = False  # Signal other tasks to exit
                            break
                        except Exception as e:
                            logger.error(f"Receive error: {e}")
                            self.connected = False  # Signal other tasks to exit
                            break

                async def batch_collector():
                    """
                    Collect batches and queue them for TTS generation.
                    Does NOT wait for TTS - just queues batches.
                    """
                    while self.running and self.connected:
                        try:
                            await asyncio.sleep(0.1)
                            if self.batcher.should_flush():
                                combined_text, segment_count = self.batcher.flush()
                                if combined_text:
                                    logger.info(f"📦 Batched {segment_count} segments ({len(combined_text)} chars)")
                                    await text_batch_queue.put(combined_text)
                        except Exception as e:
                            logger.error(f"Batch collector error: {e}")

                async def tts_generator():
                    """
                    Generate TTS audio from text batches.
                    Runs LLM + TTS and queues audio for playback.
                    This runs in PARALLEL with audio playback!
                    """
                    while self.running and self.connected:
                        try:
                            # Wait for a text batch
                            combined_text = await asyncio.wait_for(
                                text_batch_queue.get(), timeout=1.0
                            )

                            self.last_activity = time.time()
                            total_start = time.perf_counter()

                            # Add to conversation buffer
                            self.conversation.add("operator", combined_text)
                            logger.info(f"🎤 Processing: \"{combined_text[:60]}...\"" if len(combined_text) > 60 else f"🎤 Processing: \"{combined_text}\"")

                            # Transform with LLM
                            context = self.conversation.format_for_prompt(n=5)
                            rasta_text, llm_latency = await self.transformer.transform(combined_text, context)
                            self.latency.llm_times.append(llm_latency)

                            # Filter meta-commentary
                            if rasta_text.startswith('(') or 'Note:' in rasta_text or 'note:' in rasta_text:
                                logger.warning(f"Filtered meta-commentary: \"{rasta_text}\"")
                                continue

                            logger.info(f"🎙️ Rasta: \"{rasta_text[:60]}...\" (LLM: {llm_latency:.0f}ms)" if len(rasta_text) > 60 else f"🎙️ Rasta: \"{rasta_text}\" (LLM: {llm_latency:.0f}ms)")

                            # Generate TTS audio (but don't play yet!)
                            tts_start = time.perf_counter()
                            audio = await asyncio.to_thread(self.tts.generate_audio, rasta_text)
                            tts_gen_time = (time.perf_counter() - tts_start) * 1000

                            logger.info(f"🔊 Audio generated: {len(audio)} samples ({tts_gen_time:.0f}ms)")

                            # Queue audio for playback
                            await tts_audio_queue.put({
                                'audio': audio,
                                'original': combined_text,
                                'rasta': rasta_text,
                                'llm_latency': llm_latency,
                                'tts_gen_time': tts_gen_time,
                                'total_start': total_start
                            })

                            # Log transcript
                            transcript_log = Path(__file__).parent / "live_transcripts.jsonl"
                            with open(transcript_log, 'a', encoding='utf-8') as f:
                                f.write(json.dumps({
                                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                                    "original": combined_text,
                                    "patois": rasta_text
                                }) + '\n')

                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"TTS generator error: {e}")

                async def audio_player():
                    """
                    Play audio from the queue.
                    While this plays, tts_generator can be preparing the next audio!
                    """
                    while self.running and self.connected:
                        try:
                            # Wait for audio
                            item = await asyncio.wait_for(tts_audio_queue.get(), timeout=1.0)

                            audio = item['audio']
                            total_start = item['total_start']
                            llm_latency = item['llm_latency']
                            tts_gen_time = item['tts_gen_time']

                            # Check if more audio is queued (for logging)
                            queued = tts_audio_queue.qsize()
                            if queued > 0:
                                logger.info(f"▶️ Playing audio ({queued} more queued - gapless!)")
                            else:
                                logger.info(f"▶️ Playing audio")

                            # Play the audio
                            play_latency = await asyncio.to_thread(self.tts.play_audio, audio)
                            self.latency.tts_times.append(tts_gen_time)

                            total_latency = (time.perf_counter() - total_start) * 1000
                            self.latency.total_times.append(total_latency)
                            logger.info(f"✅ Complete: {total_latency:.0f}ms (LLM: {llm_latency:.0f}ms, TTS gen: {tts_gen_time:.0f}ms, play: {play_latency:.0f}ms)")

                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"Audio player error: {e}")

                # Run all tasks - now with parallel TTS generation and playback!
                send_task = asyncio.create_task(send_audio())
                recv_task = asyncio.create_task(receive_transcripts())
                collector_task = asyncio.create_task(batch_collector())
                generator_task = asyncio.create_task(tts_generator())
                player_task = asyncio.create_task(audio_player())

                await asyncio.gather(
                    send_task, recv_task, collector_task, generator_task, player_task,
                    return_exceptions=True
                )

                # Flush any remaining batch on disconnect
                remaining, seg_count = self.batcher.flush()
                if remaining:
                    logger.info(f"📦 Flushing remaining {seg_count} segments on disconnect: {len(remaining)} chars")
                    await text_batch_queue.put(remaining)
                    # Give generator time to process
                    await asyncio.sleep(0.5)

        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            self.connected = False
            self.websocket = None
            if self._mic_stream:
                self._mic_stream.stop()
                self._mic_stream.close()
                self._mic_stream = None

        return self.running  # Return True to reconnect if still running

    async def health_check(self):
        """Monitor connection health and log status."""
        while self.running:
            await asyncio.sleep(HEALTH_CHECK_INTERVAL)

            status = "CONNECTED" if self.connected else "DISCONNECTED"
            idle_time = time.time() - self.last_activity

            logger.info(f"Health: {status} | Idle: {idle_time:.0f}s | Reconnects: {self.reconnect_count}")
            self.latency.report()

            # Warn if idle too long
            if self.connected and idle_time > 120:
                logger.warning("No activity for 2+ minutes - connection may be stale")

    async def run(self):
        """Run the pipeline with auto-reconnect."""
        logger.info("=" * 60)
        logger.info("RASTA LIVE VOICE PIPELINE")
        logger.info("=" * 60)
        logger.info("Speak naturally. Press Ctrl+C to stop.")

        self.running = True
        self._health_task = asyncio.create_task(self.health_check())

        try:
            while self.running:
                should_reconnect = await self._run_single_connection()

                if not should_reconnect:
                    break

                # Exponential backoff for reconnection
                self.reconnect_count += 1
                if self.reconnect_count > MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"Max reconnect attempts ({MAX_RECONNECT_ATTEMPTS}) exceeded")
                    break

                backoff = get_backoff_time(self.reconnect_count)
                logger.info(f"Reconnecting in {backoff:.1f}s (attempt {self.reconnect_count}/{MAX_RECONNECT_ATTEMPTS})")
                await asyncio.sleep(backoff)

        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            if self._health_task:
                self._health_task.cancel()
                try:
                    await self._health_task
                except asyncio.CancelledError:
                    pass
            logger.info("Pipeline stopped")

# =============================================================================
# Supervisor Mode (for crash recovery)
# =============================================================================

async def run_with_supervisor():
    """Run the pipeline with supervisor-level crash recovery."""
    restart_count = 0
    max_restarts = 5
    restart_window = 300  # 5 minutes
    restart_times = deque(maxlen=max_restarts)

    while True:
        try:
            pipeline = RastaLivePipeline()
            await pipeline.run()

            # Clean exit
            logger.info("Pipeline exited cleanly")
            break

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break

        except Exception as e:
            logger.error(f"Pipeline crashed: {e}")

            # Track restart frequency
            now = time.time()
            restart_times.append(now)

            # Check if restarting too frequently
            if len(restart_times) >= max_restarts:
                oldest = restart_times[0]
                if now - oldest < restart_window:
                    logger.error(f"Too many restarts ({max_restarts}) in {restart_window}s - giving up")
                    break

            restart_count += 1
            backoff = get_backoff_time(restart_count)
            logger.info(f"Restarting in {backoff:.1f}s (restart #{restart_count})")
            await asyncio.sleep(backoff)

# =============================================================================
# Test Mode
# =============================================================================

async def test_pipeline():
    """Test the pipeline components."""
    logger.info("Testing pipeline components...")

    # Test LLM
    logger.info("Testing xAI LLM...")
    transformer = RastaDialectTransformer(config.groq_key)
    result, latency = await transformer.transform("Hello everyone, how are you doing today?")
    logger.info(f"LLM result: \"{result}\" ({latency:.0f}ms)")

    # Test TTS with ElevenLabs Jamaican voice - use configured devices for dual output
    logger.info("Testing ElevenLabs TTS (Denzel - Jamaican voice)...")
    tts = ElevenLabsTTS(
        config.elevenlabs_key,
        config.elevenlabs_voice_id,
        twitter_device=config.twitter_output_device,
        monitor_device=config.monitor_output_device
    )
    tts_latency = tts.speak(result)
    logger.info(f"TTS playback completed ({tts_latency:.0f}ms)")

    logger.info("Test complete!")

# =============================================================================
# Entry Point
# =============================================================================

def list_audio_devices():
    """List all audio devices."""
    devices = sd.query_devices()
    print("\n=== AUDIO DEVICES ===\n")
    print("OUTPUT DEVICES (for TTS playback):")
    for i, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            marker = ""
            if "cable input" in d['name'].lower():
                marker = " <-- VB-Cable (for Twitter)"
            elif "headphone" in d['name'].lower():
                marker = " <-- Headphones (for monitoring)"
            print(f"  {i}: {d['name']}{marker}")

    print("\nINPUT DEVICES (for microphone):")
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            marker = ""
            if "cable output" in d['name'].lower():
                marker = " <-- VB-Cable Output (Twitter sees this as 'mic')"
            print(f"  {i}: {d['name']}{marker}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Rasta Live Voice Pipeline")
    parser.add_argument("--test", action="store_true", help="Run component tests")
    parser.add_argument("--supervised", action="store_true", help="Run with supervisor (auto-restart on crash)")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices")
    parser.add_argument("--input-device", type=int, help="Input device index for microphone (AirPods, etc.)")
    parser.add_argument("--twitter-device", type=int, help="Output device index for Twitter (VB-Cable Input)")
    parser.add_argument("--monitor-device", type=int, help="Output device index for monitoring (Headphones)")
    parser.add_argument("--no-monitor", action="store_true", help="Don't play to monitor (headphones)")
    parser.add_argument("--mode", choices=["conversation", "stream"], default="stream",
                        help="Batching mode: 'conversation' for fast response (Telegram/calls), 'stream' for longer segments (Twitter/OBS)")
    args = parser.parse_args()

    # List devices mode
    if args.list_devices:
        list_audio_devices()
        return

    # Validate config
    missing = []
    if not config.deepgram_key:
        missing.append("DEEPGRAM_API_KEY")
    if not config.groq_key:
        missing.append("GROQ_API_KEY")
    if not config.elevenlabs_key:
        missing.append("ELEVENLABS_API_KEY")
    if not config.elevenlabs_voice_id:
        missing.append("ELEVENLABS_VOICE_ID")

    if missing:
        logger.error("Missing environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        sys.exit(1)

    # Set batching mode
    config.mode = args.mode
    logger.info(f"Mode: {args.mode} ({'fast response for calls' if args.mode == 'conversation' else 'efficient batching for streaming'})")

    # Configure audio devices
    # Input device (microphone)
    if args.input_device is not None:
        config.input_device = args.input_device
        logger.info(f"Using microphone device: {args.input_device}")

        # Auto-detect sample rate from input device
        try:
            device_info = sd.query_devices(args.input_device)
            device_sr = int(device_info['default_samplerate'])
            config.sample_rate = device_sr
            logger.info(f"Auto-detected sample rate: {device_sr} Hz for device {args.input_device}")
        except Exception as e:
            logger.warning(f"Could not detect sample rate, using default 48kHz: {e}")

    # Output devices
    if args.twitter_device is not None:
        config.twitter_output_device = args.twitter_device
    else:
        # Auto-detect VB-Cable Input
        cable_device = find_audio_device("cable input", is_output=True)
        if cable_device is not None:
            config.twitter_output_device = cable_device
            logger.info(f"Auto-detected VB-Cable Input: device {cable_device}")
        else:
            logger.warning("VB-Cable Input not found - using default output")

    if not args.no_monitor:
        if args.monitor_device is not None:
            config.monitor_output_device = args.monitor_device
        else:
            # Auto-detect headphones
            headphone_device = find_audio_device("headphone", is_output=True)
            if headphone_device is not None:
                config.monitor_output_device = headphone_device
                logger.info(f"Auto-detected Headphones: device {headphone_device}")

    # Print audio routing info
    logger.info("=" * 50)
    logger.info("AUDIO ROUTING:")
    if config.twitter_output_device is not None:
        logger.info(f"  Twitter (VB-Cable): device {config.twitter_output_device}")
    else:
        logger.info("  Twitter: default output")
    if config.monitor_output_device is not None:
        logger.info(f"  Monitor (Headphones): device {config.monitor_output_device}")
    else:
        logger.info("  Monitor: disabled")
    logger.info("=" * 50)
    logger.info("In Twitter Spaces: Select 'CABLE Output' as your microphone")
    logger.info("=" * 50)

    if args.test:
        asyncio.run(test_pipeline())
    elif args.supervised:
        asyncio.run(run_with_supervisor())
    else:
        try:
            pipeline = RastaLivePipeline()
            asyncio.run(pipeline.run())
        except KeyboardInterrupt:
            logger.info("Interrupted")


if __name__ == "__main__":
    main()
