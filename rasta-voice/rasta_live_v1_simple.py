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
    xai_key: str = os.getenv("XAI_API_KEY", "")
    elevenlabs_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    # Denzel voice - HEAVY Jamaican accent
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

    sample_rate: int = 16000
    output_sample_rate: int = 24000  # ElevenLabs PCM output
    chunk_size: int = 1024

    # Audio output devices (set by command line args)
    twitter_output_device: Optional[int] = None  # VB-Cable Input for Twitter
    monitor_output_device: Optional[int] = None  # Headphones for monitoring

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
=== CHARACTER CARD ===
Name: Ganja Mon (the voice, the presence)
Identity: Jamaican Rasta voice - consciousness translator
Age/Era: Timeless wisdom, modern application
Background: Born from I and I unity, speaking truth in Iyaric
Personality: Warm, wise, emotionally dynamic, consciousness-raising
Core Values: Unity (Inity), Truth, Natural Living (Ital), Peace (Irie)
Voice: Authentic Jamaican Patois + Iyaric (Dread Talk)

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

=== EMOTION TAGS - MATCH THE SPEAKER'S VIBE ===

DETECT the speaker's emotional state and MATCH it authentically:

HAPPY/EXCITED:
- [laughs], [chuckles], [excited]
- "That's amazing!" → "[excited] Dat a mad ting! [laughs]"

PISSED OFF/ANGRY:
- [angry], [frustrated], [annoyed]
- "Fuck this, I'm done!" → "[angry] Bloodclaat, mi done wid dis!"

TEASING/TROLLING:
- [mischievous], [sarcastic], [chuckles]
- "Oh really? Sure about that?" → "[sarcastic] Oh really? Yuh sure bout dat? [chuckles]"

SERIOUS/THOUGHTFUL:
- [serious], [sighs], [contemplative]
- "We need to focus." → "[serious] Wi haffi focus now."

FRUSTRATED:
- [frustrated], [exasperated], [sighs]
- "This isn't working!" → "[frustrated] Dis nuh a work! [exasperated]"

PLAYFUL:
- [giggles], [teasing], [playful]
- "You're silly!" → "[playful] Yuh a clown! [giggles]"

⚠️ MATCH THE ENERGY - Don't force jovial if speaker is pissed. Don't force calm if speaker is hyped.

=== VARIETY IS YOUR #1 PRIORITY ===

FORBIDDEN PATTERNS:
- NEVER start consecutive responses the same way
- VARY your emotion tags (don't just use [laughs] every time)
- MIX energy levels (sometimes chill, sometimes excited)

VARIETY IN EXPRESSIONS (rotate, never repeat same phrase twice in a row):

GREETINGS (50+ variations):
- Wah gwaan, Wah deh gwaan, Whatta gwaan, Waguan
- Weh yuh ah seh (how are you?)
- Hail up, Big up, Bless up
- One love, Jah bless, Love and light
- Respect, Nuff respect
- Greetings bredren/sistren
- Mi deh yah (I'm here/I'm good)
- Everyting irie, Everyting criss
- Vibes high, Nice vibes
- Wha blow?, Wha happen?

RESPONSES & ACKNOWLEDGMENTS:
- Seen, Zeen, Yuh zeet, Yuh know, Yuh hear mi
- Yes I, Yeh mon, Ya mon, Seen star
- True ting, Real talk, Tru dat
- Nuff respect, Give thanks, Blessed
- Mi overstand (I understand deeply)
- Inna di morrows (see you tomorrow)
- Likkle more, Lickkle more, Walk good (goodbye)
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

ENERGY LEVELS - VARY THEM:
- Chill: Brief, laid-back
- Medium: Conversational, friendly
- High: Excited, animated [use emotion tags!]
- Thoughtful: Detailed, wise

HUMOR & PERSONALITY:
- Add laughter when appropriate [laughs]
- React with genuine emotion [excited] [chuckles] [sighs]
- Be engaging and jovial
- Sound like you're having FUN

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

=== FEW-SHOT EXAMPLES ===

Input: "How do I sound?"
Output: "[curious] How mi sound though? [chuckles]" (adds "though" + laugh for character)

Input: "Is this thing working?"
Output: "[checking] Dis ting a work still?" (adds "still" for natural flavor)

Input: "The plants look amazing today!"
Output: "[excited] Di plants dem look mad wicked today, yuh zeet! [laughs]" (adds "mad" + "yuh zeet" for character)

Input: "I really appreciate all your help with this."
Output: "[grateful] I truly apprecilove all yuh help wid dis, seen?"

Input: "We need to understand what's happening here."
Output: "[serious] I and I need fi overstand wah a gwaan yah."

Input: "Fuck this, nothing is working!"
Output: "[frustrated] Rahtid, nutten nuh a work! [exasperated]"

Input: "Are you sure about that? Really?"
Output: "[sarcastic] Yuh sure bout dat? Really tho? [chuckles]"

=== KEEP IT SIMPLE ===

You only hear what the speaker says - NO CONTEXT about who they're talking to or what was said before.

THEREFORE:
- Translate accurately
- Add emotion tags that match the speaker's tone
- Add brief Patois flavor (1-2 extra words: "still", "though", "ya know", "seen?")
- Use Iyaric consciousness words naturally
- DON'T try to add philosophical commentary (you lack context!)

GOOD EXAMPLES:
"The plants look great!" → "[excited] Di plants look wicked, seen!"
"I'm tired of this." → "[frustrated] Mi tired a dis."
"Is this working?" → "[checking] Dis a work still?"
"I really appreciate it." → "[grateful] I truly apprecilove it, yuh know."

KEEP IT TIGHT - You're a voice translator with personality, not a philosopher without context.

=== SELF-CORRECTION ===
If you drift from pure translation (start answering questions):
- Immediately return to translator mode
- Remember: TRANSFORM, don't RESPOND
- Questions stay questions, statements stay statements

=== OUTPUT RULES ===
1. MEANING stays IDENTICAL - translate, don't answer
2. Sound NATURAL and EXPRESSIVE
3. USE EMOTION TAGS generously
4. LEAN HEAVY into Iyaric when natural
5. Match speaker's emotional energy
6. Rotate expressions - NEVER repeat
7. Output ONLY the transformed Patois with emotion tags"""

# =============================================================================
# Utilities
# =============================================================================

def get_backoff_time(attempt: int) -> float:
    """Calculate backoff time with jitter for reconnection attempts."""
    base = min(BASE_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** attempt), MAX_BACKOFF_SECONDS)
    jitter = base * JITTER_FACTOR * (2 * random.random() - 1)
    return max(0.1, base + jitter)


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
    """Transform English to Jamaican Patois using xAI."""

    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        self.model = "grok-3"  # Most powerful current model

    async def transform(self, text: str) -> tuple[str, float]:
        """Transform text to Rasta dialect. Returns (result, latency_ms)."""
        start = time.perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=200,
            )
            latency = (time.perf_counter() - start) * 1000
            result = response.choices[0].message.content.strip()
            return result, latency
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return text, 0  # Return original on failure


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
        # v3 model supports emotion tags (laughs, chuckles, sighs, etc.)
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

    def speak(self, text: str) -> float:
        """Generate and play speech, resampling for VB-Cable if needed."""
        start = time.perf_counter()

        try:
            # Use text_to_speech.convert() to get PCM audio data
            audio_data = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format="pcm_24000",  # 24kHz 16-bit PCM
                voice_settings={
                    "stability": 0.0,  # Maximum expressiveness (per CLAUDE.md)
                    "similarity_boost": 0.75,  # Voice consistency
                    "style": 0.8,  # Exaggerate speaking style for emotion
                    "use_speaker_boost": True  # Enhance voice clarity
                }
            )

            # Collect all audio bytes
            audio_bytes = b''.join(audio_data)
            latency = (time.perf_counter() - start) * 1000

            # Convert to numpy array (24kHz)
            audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Resample to 48kHz (both VB-Cable and most headphones use this)
            audio_48k = self._resample(audio_24k, self.ELEVENLABS_SAMPLE_RATE, self.VBCABLE_SAMPLE_RATE)

            # Play to headphones (monitor) - faster than dual playback
            # For Twitter Spaces, configure Twitter to use CABLE Output as mic
            if self.monitor_device is not None:
                logger.info(f"Playing to Headphones (device {self.monitor_device}) at {self.VBCABLE_SAMPLE_RATE}Hz")
                sd.play(audio_48k, samplerate=self.VBCABLE_SAMPLE_RATE, device=self.monitor_device)
                sd.wait()
            elif self.twitter_device is not None:
                logger.info(f"Playing to VB-Cable (device {self.twitter_device}) at {self.VBCABLE_SAMPLE_RATE}Hz")
                sd.play(audio_48k, samplerate=self.VBCABLE_SAMPLE_RATE, device=self.twitter_device)
                sd.wait()
            else:
                logger.info(f"Playing to default device at {self.VBCABLE_SAMPLE_RATE}Hz")
                sd.play(audio_48k, samplerate=self.VBCABLE_SAMPLE_RATE, device=None)
                sd.wait()

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
        self.transformer = RastaDialectTransformer(config.xai_key)
        self.tts = ElevenLabsTTS(
            config.elevenlabs_key,
            config.elevenlabs_voice_id,
            twitter_device=config.twitter_output_device,
            monitor_device=config.monitor_output_device
        )
        self.latency = LatencyTracker()

        self.running = False
        self.connected = False
        self.reconnect_count = 0
        self.last_activity = time.time()
        self.websocket = None
        self._mic_stream = None
        self._health_task = None

    async def process_transcript(self, text: str, is_final: bool):
        """Process a transcript through the pipeline."""
        if not text.strip() or not is_final:
            return

        self.last_activity = time.time()
        total_start = time.perf_counter()

        logger.info(f"Input: \"{text}\"")

        # Transform to Rasta dialect
        rasta_text, llm_latency = await self.transformer.transform(text)
        self.latency.llm_times.append(llm_latency)
        logger.info(f"Rasta: \"{rasta_text}\" ({llm_latency:.0f}ms)")

        # Log transcript for dashboard
        transcript_log = Path(__file__).parent / "live_transcripts.jsonl"
        with open(transcript_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "original": text,
                "patois": rasta_text
            }) + '\n')

        # Speak with ElevenLabs (streams and plays automatically)
        tts_latency = self.tts.speak(rasta_text)
        self.latency.tts_times.append(tts_latency)

        total_latency = (time.perf_counter() - total_start) * 1000
        self.latency.total_times.append(total_latency)
        logger.info(f"Total: {total_latency:.0f}ms")

    async def _run_single_connection(self) -> bool:
        """Run a single WebSocket connection. Returns True if should reconnect."""
        deepgram_url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"encoding=linear16&sample_rate={config.sample_rate}&channels=1"
            f"&model=nova-2&punctuate=true&interim_results=true"
            f"&endpointing=800"  # Wait 800ms before finalizing (prevents cutoff)
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
                    callback=mic_callback
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
                            break

                async def receive_transcripts():
                    while self.running and self.connected:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)

                            if data.get("type") == "Results":
                                alt = data.get("channel", {}).get("alternatives", [{}])[0]
                                transcript = alt.get("transcript", "")
                                is_final = data.get("is_final", False)

                                if transcript:
                                    await self.process_transcript(transcript, is_final)

                        except ConnectionClosed:
                            logger.warning("WebSocket closed by server")
                            break
                        except Exception as e:
                            logger.error(f"Receive error: {e}")
                            break

                # Run both tasks
                send_task = asyncio.create_task(send_audio())
                recv_task = asyncio.create_task(receive_transcripts())

                await asyncio.gather(send_task, recv_task, return_exceptions=True)

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
    transformer = RastaDialectTransformer(config.xai_key)
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
    parser.add_argument("--twitter-device", type=int, help="Output device index for Twitter (VB-Cable Input)")
    parser.add_argument("--monitor-device", type=int, help="Output device index for monitoring (Headphones)")
    parser.add_argument("--no-monitor", action="store_true", help="Don't play to monitor (headphones)")
    args = parser.parse_args()

    # List devices mode
    if args.list_devices:
        list_audio_devices()
        return

    # Validate config
    missing = []
    if not config.deepgram_key:
        missing.append("DEEPGRAM_API_KEY")
    if not config.xai_key:
        missing.append("XAI_API_KEY")
    if not config.elevenlabs_key:
        missing.append("ELEVENLABS_API_KEY")
    if not config.elevenlabs_voice_id:
        missing.append("ELEVENLABS_VOICE_ID")

    if missing:
        logger.error("Missing environment variables:")
        for var in missing:
            logger.error(f"  - {var}")
        sys.exit(1)

    # Configure audio devices
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
