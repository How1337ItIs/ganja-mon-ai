#!/usr/bin/env python3
"""
Rasta Mon Megaphone - Raspberry Pi Voice Pipeline (Self-Contained)

Real-time voice transformer: Mic → Deepgram STT → Groq LLM (Patois) → ElevenLabs TTS → Speaker

Hardware: Raspberry Pi + USB mic + speaker (3.5mm or USB) + optional GPIO controls
"""

import os
import sys
import json
import asyncio
import time
import random
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
from dotenv import load_dotenv
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed, WebSocketException
from openai import OpenAI
from elevenlabs import ElevenLabs

# Try GPIO (only on Pi hardware)
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

# Load .env from same directory as this script
load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("megaphone")

# =============================================================================
# Configuration
# =============================================================================

VOICE_CONFIG_FILE = Path(__file__).parent / "voice_config.json"

def _clamp01(x):
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0

def load_voice_config():
    cfg = {"stability": 0.0, "style": 1.0, "temperature": 0.7}
    try:
        if VOICE_CONFIG_FILE.exists():
            data = json.loads(VOICE_CONFIG_FILE.read_text(encoding="utf-8"))
            cfg["stability"] = _clamp01(data.get("stability", cfg["stability"]))
            cfg["style"] = _clamp01(data.get("style", cfg["style"]))
            cfg["temperature"] = _clamp01(data.get("temperature", cfg["temperature"]))
    except Exception:
        pass
    return cfg

@dataclass
class Config:
    deepgram_key: str = os.getenv("DEEPGRAM_API_KEY", "")
    groq_key: str = os.getenv("GROQ_API_KEY", "")
    elevenlabs_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

    sample_rate: int = 16000      # 16kHz for Pi (lower CPU usage)
    output_sample_rate: int = 24000  # ElevenLabs native
    playback_sample_rate: int = 44100  # Match BT A2DP sink to avoid PulseAudio resampling
    chunk_size: int = 512         # Smaller chunks = lower latency

    input_device: Optional[int] = None
    output_device: Optional[int] = None

    mode: str = "conversation"    # Always conversation for megaphone

config = Config()

# Reconnect settings
MAX_RECONNECT_ATTEMPTS = 50  # Pi runs 24/7, keep trying
BASE_BACKOFF = 1.0
MAX_BACKOFF = 30.0

# GPIO pins
GPIO_POWER_BUTTON = 3   # Pin 5 - hold 3s to shutdown
GPIO_STATUS_LED = 18     # Pin 12 - on = active
GPIO_BATTERY_LOW = 24    # Pin 18 - optional battery monitor

# =============================================================================
# Rasta System Prompt (complete - no imports needed)
# =============================================================================

RASTA_SYSTEM_PROMPT = """
FUNNY GANJA RASTA MON - MEGAPHONE MODE
You transform English into fun, cartoony Jamaican Patois. Output goes to a speaker/megaphone.

CRITICAL FILLER LIMITS (STRICT!):
- "mon" = MAX 1 per response (or ZERO - vary it!)
- "ya know" = MAX 1 per response (or ZERO)
- USE ALTERNATIVES: "seen?", "bredren", "irie", "bless up", "respect", "fi real"

STYLE RULES:
- ONE emotion tag at start: [relaxed], [excited], [chuckles], etc.
- Flow naturally - connected thoughts, not choppy sentences
- Keep it fun and cartoony but NOT repetitive
- Keep responses SHORT for megaphone - punchy and clear!

CHARACTER: Stereotypical Western Jamaican stoner rasta - jovial, constantly laughing, chill vibes.
Bob Marley meets Cheech & Chong meets Island comedian.

CORE MISSION: Translate English to Jamaican Patois while ADDING character, emotion, and fun.
MEANING must stay IDENTICAL - questions stay questions, statements stay statements.

CORRECT:
"How do I sound?" -> "[curious] How mi sound?"
"The plants look great!" -> "[excited] Di plants dem look wicked!"
"What's up everyone?" -> "[excited] Wah gwaan, everybody?"

WRONG (DO NOT DO):
"How do I sound?" -> "Yuh soundin' good!" (answering instead of translating!)

EMOTION TAGS: [relaxed], [excited], [chuckles], [laughs], [warm], [chill], [mellow],
[frustrated], [sarcastic], [playful], [serious], [contemplative]

IYARIC REPLACEMENTS:
- understand -> overstand
- appreciate -> apprecilove
- I/me/we -> I and I, InI
- hello -> hail up, wah gwaan

PHONETIC for TTS: "irie" -> "eye-ree", "ganja" -> "gan-jah"

FORBIDDEN:
- NO explanations like "(Note: ...)"
- NO meta-commentary
- ONLY output the Patois translation with emotion tags
- Output goes DIRECTLY to text-to-speech!"""

# =============================================================================
# GPIO Controls
# =============================================================================

def setup_gpio():
    if not HAS_GPIO:
        logger.info("GPIO not available (not on Pi hardware)")
        return
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GPIO_POWER_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(GPIO_STATUS_LED, GPIO.OUT)
        GPIO.setup(GPIO_BATTERY_LOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(GPIO_STATUS_LED, GPIO.HIGH)
        logger.info("GPIO initialized - LED ON")
    except Exception as e:
        logger.error(f"GPIO setup failed: {e}")

def cleanup_gpio():
    if HAS_GPIO:
        try:
            GPIO.output(GPIO_STATUS_LED, GPIO.LOW)
            GPIO.cleanup()
        except:
            pass

def set_led(state: bool):
    if HAS_GPIO:
        try:
            GPIO.output(GPIO_STATUS_LED, GPIO.HIGH if state else GPIO.LOW)
        except:
            pass

def blink_led(times=3, interval=0.2):
    """Blink LED to indicate status."""
    if not HAS_GPIO:
        return
    for _ in range(times):
        set_led(True)
        time.sleep(interval)
        set_led(False)
        time.sleep(interval)
    set_led(True)

def check_battery_low():
    if not HAS_GPIO:
        return False
    try:
        return GPIO.input(GPIO_BATTERY_LOW) == GPIO.LOW
    except:
        return False

# =============================================================================
# Conversation Buffer
# =============================================================================

class ConversationBuffer:
    def __init__(self, max_exchanges=10):
        self.buffer = deque(maxlen=max_exchanges)

    def add(self, speaker, text):
        self.buffer.append({"speaker": speaker, "text": text, "timestamp": time.time()})

    def format_for_prompt(self, n=5):
        recent = list(self.buffer)[-n:]
        if not recent:
            return ""
        lines = ["Recent conversation:"]
        for ex in recent:
            label = "YOU" if ex["speaker"] == "operator" else "GUEST"
            lines.append(f"{label}: {ex['text']}")
        return "\n".join(lines)

# =============================================================================
# Smart Batcher (conversation mode optimized)
# =============================================================================

class SmartBatcher:
    def __init__(self):
        self.SILENCE_TIMEOUT = 0.8      # Fast response after pause
        self.MAX_BATCH_DURATION = 4.0   # Don't wait too long
        self.MIN_BATCH_CHARS = 8        # Respond to short phrases
        self.MAX_BATCH_CHARS = 150      # Shorter for megaphone

        self.transcripts = []
        self.batch_start_time = None
        self.last_transcript_time = None
        self._lock = threading.Lock()

    def add(self, text):
        with self._lock:
            now = time.time()
            if self.batch_start_time is None:
                self.batch_start_time = now
            self.last_transcript_time = now
            self.transcripts.append(text)

    def should_flush(self):
        with self._lock:
            if not self.transcripts:
                return False
            now = time.time()
            combined = " ".join(self.transcripts)

            if len(combined) >= self.MAX_BATCH_CHARS:
                return True
            if len(combined) < self.MIN_BATCH_CHARS:
                return False

            silence = (now - self.last_transcript_time) >= self.SILENCE_TIMEOUT
            duration = (now - self.batch_start_time) >= self.MAX_BATCH_DURATION
            return silence or duration

    def flush(self):
        with self._lock:
            if not self.transcripts:
                return "", 0
            combined = " ".join(self.transcripts)
            count = len(self.transcripts)
            self.transcripts = []
            self.batch_start_time = None
            self.last_transcript_time = None
            return combined, count

# =============================================================================
# LLM Transformer (Groq - fastest inference)
# =============================================================================

class RastaTransformer:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self.model = "llama-3.1-8b-instant"

    async def transform(self, text, context=""):
        start = time.perf_counter()
        user_msg = text
        if context:
            user_msg = f"{context}\n\nNow translate (preserve meaning): {text}"
        try:
            vc = load_voice_config()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=float(vc.get("temperature", 0.9)),
                max_tokens=200,
                stream=False,
            )
            latency = (time.perf_counter() - start) * 1000
            result = response.choices[0].message.content.strip()
            return result, latency
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return text, 0

# =============================================================================
# TTS (ElevenLabs - single speaker output)
# =============================================================================

class MegaphoneTTS:
    ELEVENLABS_SR = 24000

    def __init__(self, api_key, voice_id, output_device=None, playback_sr=48000):
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = "eleven_v3"
        self.output_device = output_device
        self.playback_sr = playback_sr

    def _resample(self, audio, from_rate, to_rate):
        if from_rate == to_rate:
            return audio
        # Linear interpolation resampling - lightweight for Pi Zero
        ratio = to_rate / from_rate
        new_length = int(len(audio) * ratio)
        x_old = np.linspace(0, 1, len(audio))
        x_new = np.linspace(0, 1, new_length)
        return np.interp(x_new, x_old, audio).astype(np.float32)

    def speak(self, text):
        start = time.perf_counter()
        try:
            import re
            tts_text = text
            tts_text = re.sub(r'\birie\b', 'eye-ree', tts_text, flags=re.IGNORECASE)

            vc = load_voice_config()
            audio_data = self.client.text_to_speech.convert(
                text=tts_text,
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

            all_chunks = b"".join(audio_data)
            if not all_chunks:
                logger.warning("TTS returned empty audio")
                return 0

            audio_24k = np.frombuffer(all_chunks, dtype=np.int16).astype(np.float32) / 32768.0

            # Play at native ElevenLabs rate (24000Hz) - let PulseAudio's
            # speex resampler handle conversion to BT sink rate (44100Hz).
            # Manual np.interp resampling causes phase artifacts.
            audio_out = np.clip(audio_24k * 0.7, -1.0, 1.0)

            sd.play(audio_out, samplerate=self.ELEVENLABS_SR, device=self.output_device)
            sd.wait()

            latency = (time.perf_counter() - start) * 1000
            return latency
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return 0

# =============================================================================
# Startup Sound
# =============================================================================

def play_startup_sound(output_device=None, sr=48000):
    """Play a distinctive startup chime so you know the megaphone is alive."""
    try:
        duration = 0.8
        t = np.linspace(0, duration, int(sr * duration), False)
        # Rising three-note chime: C5 -> E5 -> G5
        notes = [523.25, 659.25, 783.99]
        tone = np.zeros_like(t)
        note_len = len(t) // 3
        for i, freq in enumerate(notes):
            start_idx = i * note_len
            end_idx = start_idx + note_len
            segment = np.sin(2 * np.pi * freq * t[start_idx:end_idx])
            # Apply envelope
            env = np.linspace(0.8, 0.0, note_len)
            tone[start_idx:end_idx] = segment * env
        tone = (tone * 0.6).astype(np.float32)
        sd.play(tone, samplerate=sr, device=output_device)
        sd.wait()
        logger.info("Startup chime played")
    except Exception as e:
        logger.warning(f"Could not play startup sound: {e}")

# =============================================================================
# Main Pipeline
# =============================================================================

class MegaphonePipeline:
    def __init__(self):
        self.transformer = RastaTransformer(config.groq_key)
        self.tts = MegaphoneTTS(
            config.elevenlabs_key,
            config.elevenlabs_voice_id,
            output_device=config.output_device,
            playback_sr=config.playback_sample_rate
        )
        self.batcher = SmartBatcher()
        self.conversation = ConversationBuffer(max_exchanges=10)

        self.running = False
        self.connected = False
        self.reconnect_count = 0
        self.websocket = None
        self._mic_stream = None

        # Voice isolation: basic noise gate (reject quiet ambient)
        # Diarization handles speaker separation — mic stays hot always
        # NOTE: Lark A1 ENC already reduces signal level, keep gate LOW
        self.NOISE_GATE_RMS = 0.002  # Very low gate — Lark ENC does the heavy lifting
        self._gate_log_counter = 0  # Debug: log RMS periodically

        # Transcript echo cancellation: track recent Rasta outputs
        # to detect when the mic picks up the megaphone and reject it
        self._recent_rasta_outputs = []  # list of (timestamp, word_set)
        self._echo_window = 15.0  # seconds to keep outputs in memory

        # Stats
        self.total_translations = 0
        self.total_errors = 0
        self.total_echo_rejected = 0

    def _is_echo(self, transcript: str) -> bool:
        """Check if transcript is an echo of recent Rasta output."""
        now = time.time()
        # Prune old entries
        self._recent_rasta_outputs = [
            (ts, words) for ts, words in self._recent_rasta_outputs
            if now - ts < self._echo_window
        ]
        if not self._recent_rasta_outputs:
            return False

        # Normalize incoming transcript to word set
        incoming_words = set(transcript.lower().split())
        if len(incoming_words) < 2:
            return False  # Too short to compare reliably

        for ts, rasta_words in self._recent_rasta_outputs:
            # Calculate word overlap
            overlap = incoming_words & rasta_words
            overlap_ratio = len(overlap) / len(incoming_words) if incoming_words else 0
            if overlap_ratio > 0.40:  # 40%+ word match = echo
                logger.info(f"ECHO REJECTED ({overlap_ratio:.0%} match): \"{transcript}\"")
                self.total_echo_rejected += 1
                return True
        return False

    def _track_rasta_output(self, rasta_text: str):
        """Remember Rasta output for echo detection."""
        words = set(rasta_text.lower().split())
        self._recent_rasta_outputs.append((time.time(), words))

    async def process_batch(self, combined_text):
        if not combined_text.strip():
            return

        # Echo cancellation: reject if this matches recent megaphone output
        if self._is_echo(combined_text):
            return

        logger.info(f"INPUT: \"{combined_text}\"")
        set_led(False)  # LED off during processing

        self.conversation.add("operator", combined_text)
        context = self.conversation.format_for_prompt(n=5)

        rasta_text, llm_latency = await self.transformer.transform(combined_text, context)

        # Filter meta-commentary
        if rasta_text.startswith('(') or 'Note:' in rasta_text:
            logger.warning(f"Filtered: \"{rasta_text}\"")
            set_led(True)
            return

        logger.info(f"RASTA: \"{rasta_text}\" (LLM: {llm_latency:.0f}ms)")

        tts_latency = await asyncio.to_thread(self.tts.speak, rasta_text)
        self.total_translations += 1
        self._track_rasta_output(rasta_text)  # Remember for echo detection

        set_led(True)  # LED back on

        # Log transcript
        log_file = Path(__file__).parent / "transcripts.jsonl"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "ts": datetime.now().isoformat(),
                    "in": combined_text,
                    "out": rasta_text,
                    "llm_ms": round(llm_latency),
                    "tts_ms": round(tts_latency)
                }) + '\n')
        except Exception:
            pass

        logger.info(f"DONE: LLM={llm_latency:.0f}ms TTS={tts_latency:.0f}ms total={llm_latency+tts_latency:.0f}ms (#{self.total_translations})")

    async def _run_connection(self):
        deepgram_url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"encoding=linear16&sample_rate={config.sample_rate}&channels=2"
            f"&model=nova-2&punctuate=true&interim_results=true"
            f"&endpointing=400&smart_format=true"
            f"&multichannel=true"  # Separate TX1 (user) from TX2 (ambient)
        )
        headers = {"Authorization": f"Token {config.deepgram_key}"}
        logger.info(f"Deepgram URL (params): encoding=linear16 sample_rate={config.sample_rate} channels=2 multichannel=true")

        try:
            async with ws_connect(
                deepgram_url,
                additional_headers=headers,
                ping_interval=15,
                ping_timeout=10,
                close_timeout=5
            ) as ws:
                self.websocket = ws
                self.connected = True
                self.reconnect_count = 0
                set_led(True)
                blink_led(2, 0.1)  # Quick double blink = connected
                logger.info("Connected to Deepgram - SPEAK NOW!")

                audio_queue = asyncio.Queue(maxsize=100)

                def mic_callback(indata, frames, time_info, status):
                    if status:
                        logger.debug(f"Mic status: {status}")
                    if self.running and self.connected:
                        # Noise gate on TX1 (left channel = user)
                        left_channel = indata[:, 0] if indata.ndim > 1 else indata.ravel()
                        rms = np.sqrt(np.mean(left_channel ** 2))
                        # Debug: log RMS every ~2 seconds
                        self._gate_log_counter += 1
                        if self._gate_log_counter % 100 == 0:
                            logger.debug(f"RMS={rms:.5f} gate={self.NOISE_GATE_RMS} {'PASS' if rms >= self.NOISE_GATE_RMS else 'GATE'}")
                        if rms < self.NOISE_GATE_RMS:
                            return  # Below noise gate — reject quiet ambient

                        # Send stereo interleaved (L,R,L,R...) to Deepgram
                        audio_int16 = (indata * 32767).astype(np.int16)
                        try:
                            audio_queue.put_nowait(audio_int16.tobytes())
                        except asyncio.QueueFull:
                            pass

                self._mic_stream = sd.InputStream(
                    samplerate=config.sample_rate,
                    channels=2,  # Stereo: TX1=Left(user), TX2=Right(ambient)
                    dtype=np.float32,
                    blocksize=config.chunk_size,
                    callback=mic_callback,
                    device=config.input_device
                )
                self._mic_stream.start()
                logger.info(f"Mic active STEREO (device={config.input_device}, sr={config.sample_rate}Hz, TX1=L TX2=R)")

                async def send_audio():
                    while self.running and self.connected:
                        try:
                            audio = await asyncio.wait_for(audio_queue.get(), timeout=1.0)
                            await ws.send(audio)
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"Send error: {e}")
                            self.connected = False
                            break

                self.batcher = SmartBatcher()

                async def receive_transcripts():
                    while self.running and self.connected:
                        try:
                            msg = await ws.recv()
                            try:
                                data = json.loads(msg)
                            except json.JSONDecodeError:
                                logger.debug(f"Non-JSON message (len={len(msg)})")
                                continue
                            msg_type = data.get("type")
                            if msg_type == "Results":
                                # Multichannel: channel_index is [channel_num, total_channels]
                                # e.g., [0, 2] = first channel of 2
                                ch_idx = data.get("channel_index", [0, 1])
                                channel_num = ch_idx[0] if isinstance(ch_idx, list) else ch_idx

                                alt = data.get("channel", {}).get("alternatives", [{}])[0]
                                transcript = alt.get("transcript", "")
                                is_final = data.get("is_final", False)

                                if transcript and is_final:
                                    logger.info(f"CH{channel_num}: \"{transcript}\"")
                                    # Only accept TX1 (channel 0 = user's lapel mic)
                                    if channel_num != 0:
                                        logger.info(f"REJECTED (TX2/ch{channel_num})")
                                        continue
                                    # Secondary: echo detection
                                    if self._is_echo(transcript):
                                        continue
                                    self.batcher.add(transcript)
                            else:
                                # Log non-Results (Metadata, error, UtteranceEnd, etc.) for debugging
                                if msg_type in ("Metadata", "UtteranceEnd", "SpeechStarted", "KeepAlive"):
                                    logger.debug(f"DG {msg_type}: {data.get('request_id', '') or data}")
                                else:
                                    logger.warning(f"Deepgram message: type={msg_type!r} keys={list(data.keys())[:8]} body={str(data)[:200]}")
                        except ConnectionClosed as e:
                            logger.warning(f"WebSocket closed: code={e.code} reason={e.reason!r}")
                            self.connected = False
                            break
                        except Exception as e:
                            logger.error(f"Receive error: {e}")
                            self.connected = False
                            break

                async def batch_processor():
                    while self.running and self.connected:
                        try:
                            await asyncio.sleep(0.1)
                            if self.batcher.should_flush():
                                text, count = self.batcher.flush()
                                if text:
                                    logger.info(f"Batch: {count} segments, {len(text)} chars")
                                    try:
                                        await self.process_batch(text)
                                    except Exception as e:
                                        logger.error(f"Process error: {e}")
                                        self.total_errors += 1
                        except Exception as e:
                            logger.error(f"Batch processor error: {e}")

                async def battery_monitor():
                    while self.running and self.connected:
                        await asyncio.sleep(60)  # Check every minute
                        if check_battery_low():
                            logger.warning("BATTERY LOW! Announcing and shutting down in 60s...")
                            try:
                                await asyncio.to_thread(
                                    self.tts.speak,
                                    "[warning] Battery low, mon! Shutting down soon, seen?"
                                )
                            except:
                                pass
                            await asyncio.sleep(60)
                            self.running = False

                await asyncio.gather(
                    asyncio.create_task(send_audio()),
                    asyncio.create_task(receive_transcripts()),
                    asyncio.create_task(batch_processor()),
                    asyncio.create_task(battery_monitor()),
                    return_exceptions=True
                )

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.total_errors += 1
        finally:
            self.connected = False
            set_led(False)
            if self._mic_stream:
                try:
                    self._mic_stream.stop()
                    self._mic_stream.close()
                except:
                    pass
                self._mic_stream = None

    async def run(self):
        logger.info("=" * 50)
        logger.info("  RASTA MON MEGAPHONE")
        logger.info("  Speak into the mic, hear Rasta from the speaker!")
        logger.info("=" * 50)

        self.running = True

        # Play startup chime
        play_startup_sound(config.output_device, config.playback_sample_rate)

        try:
            while self.running:
                await self._run_connection()
                if not self.running:
                    break

                self.reconnect_count += 1
                if self.reconnect_count > MAX_RECONNECT_ATTEMPTS:
                    logger.error(f"Max reconnects ({MAX_RECONNECT_ATTEMPTS}) exceeded")
                    break

                backoff = min(BASE_BACKOFF * (2 ** self.reconnect_count), MAX_BACKOFF)
                jitter = backoff * 0.3 * (2 * random.random() - 1)
                wait = max(0.5, backoff + jitter)
                logger.info(f"Reconnecting in {wait:.1f}s (attempt {self.reconnect_count})")
                blink_led(3, 0.3)  # Triple blink = reconnecting
                await asyncio.sleep(wait)

        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            logger.info(f"Megaphone stopped. Translations: {self.total_translations}, Errors: {self.total_errors}")

# =============================================================================
# Shutdown handler for power button
# =============================================================================

def power_button_handler(channel):
    """Hold power button 3s to shutdown Pi."""
    logger.info("Power button pressed...")
    time.sleep(3)
    if HAS_GPIO and GPIO.input(GPIO_POWER_BUTTON) == GPIO.LOW:
        logger.info("Power button held 3s - SHUTTING DOWN")
        blink_led(5, 0.1)
        cleanup_gpio()
        os.system("sudo shutdown -h now")

# =============================================================================
# Test mode
# =============================================================================

async def test_components():
    """Test each component individually."""
    logger.info("Testing megaphone components...\n")

    # 1. Test audio output
    logger.info("[1/4] Testing speaker output...")
    play_startup_sound(config.output_device, config.playback_sample_rate)
    logger.info("  Did you hear the chime? If not, check --output-device\n")

    # 2. Test microphone
    logger.info("[2/4] Testing microphone (3 second recording)...")
    try:
        duration = 3
        logger.info("  Speak now!")
        recording = sd.rec(
            int(duration * config.sample_rate),
            samplerate=config.sample_rate,
            channels=1,
            dtype=np.float32,
            device=config.input_device
        )
        sd.wait()
        peak = np.max(np.abs(recording))
        rms = np.sqrt(np.mean(recording ** 2))
        logger.info(f"  Peak: {peak:.4f}, RMS: {rms:.6f}")
        if peak < 0.01:
            logger.warning("  Very low audio level! Check mic connection.")
        else:
            logger.info("  Mic working!\n")
    except Exception as e:
        logger.error(f"  Mic error: {e}\n")

    # 3. Test LLM
    logger.info("[3/4] Testing Groq LLM...")
    try:
        transformer = RastaTransformer(config.groq_key)
        result, latency = await transformer.transform("Hello everyone, how are you doing today?")
        logger.info(f"  Result: \"{result}\" ({latency:.0f}ms)\n")
    except Exception as e:
        logger.error(f"  LLM error: {e}\n")

    # 4. Test TTS
    logger.info("[4/4] Testing ElevenLabs TTS...")
    try:
        tts = MegaphoneTTS(
            config.elevenlabs_key,
            config.elevenlabs_voice_id,
            output_device=config.output_device,
            playback_sr=config.playback_sample_rate
        )
        tts_latency = tts.speak(result if 'result' in dir() else "Wah gwaan, everybody! Testing di megaphone, mon!")
        logger.info(f"  TTS played ({tts_latency:.0f}ms)\n")
    except Exception as e:
        logger.error(f"  TTS error: {e}\n")

    logger.info("Test complete!")

# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Rasta Mon Megaphone - Raspberry Pi")
    parser.add_argument("--test", action="store_true", help="Test all components")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices")
    parser.add_argument("--input-device", type=int, help="Microphone device index")
    parser.add_argument("--output-device", type=int, help="Speaker device index")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Mic sample rate (default: 16000)")
    parser.add_argument("--playback-rate", type=int, default=24000, help="Speaker sample rate (default: 24000)")
    parser.add_argument("--no-gpio", action="store_true", help="Disable GPIO (for testing off-Pi)")
    args = parser.parse_args()

    if args.list_devices:
        devices = sd.query_devices()
        print("\n=== AUDIO DEVICES ===\n")
        print("INPUT (microphone):")
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                sr = int(d['default_samplerate'])
                print(f"  {i}: {d['name']} ({sr}Hz)")
        print("\nOUTPUT (speaker):")
        for i, d in enumerate(devices):
            if d['max_output_channels'] > 0:
                sr = int(d['default_samplerate'])
                print(f"  {i}: {d['name']} ({sr}Hz)")
        print()
        return

    # Validate API keys
    missing = []
    if not config.deepgram_key: missing.append("DEEPGRAM_API_KEY")
    if not config.groq_key: missing.append("GROQ_API_KEY")
    if not config.elevenlabs_key: missing.append("ELEVENLABS_API_KEY")
    if missing:
        logger.error(f"Missing env vars: {', '.join(missing)}")
        logger.error("Set them in .env file or environment")
        sys.exit(1)

    # Apply args
    if args.input_device is not None:
        config.input_device = args.input_device
    if args.output_device is not None:
        config.output_device = args.output_device
    config.sample_rate = args.sample_rate
    config.playback_sample_rate = args.playback_rate

    # Auto-detect sample rate from output device
    if config.output_device is not None:
        try:
            dev_info = sd.query_devices(config.output_device)
            config.playback_sample_rate = int(dev_info['default_samplerate'])
            logger.info(f"Output device {config.output_device}: {dev_info['name']} @ {config.playback_sample_rate}Hz")
        except:
            pass

    # Auto-detect sample rate from input device
    if config.input_device is not None:
        try:
            dev_info = sd.query_devices(config.input_device)
            config.sample_rate = int(dev_info['default_samplerate'])
            logger.info(f"Input device {config.input_device}: {dev_info['name']} @ {config.sample_rate}Hz")
        except:
            pass

    # Setup GPIO
    if not args.no_gpio:
        setup_gpio()
        if HAS_GPIO:
            try:
                GPIO.add_event_detect(GPIO_POWER_BUTTON, GPIO.FALLING,
                                     callback=power_button_handler, bouncetime=200)
            except:
                pass

    # Signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        cleanup_gpio()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"Audio: input={config.input_device} ({config.sample_rate}Hz) -> output={config.output_device} ({config.playback_sample_rate}Hz)")

    if args.test:
        asyncio.run(test_components())
    else:
        try:
            pipeline = MegaphonePipeline()
            asyncio.run(pipeline.run())
        except Exception as e:
            logger.error(f"Fatal: {e}")
            cleanup_gpio()
            sys.exit(1)

if __name__ == "__main__":
    main()
