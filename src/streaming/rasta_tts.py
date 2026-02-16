#!/usr/bin/env python3
"""
Rasta TTS service for Retake.tv streaming.

Text → Grok Patois Translation → ElevenLabs TTS → Audio output

No speech-to-text - just text input to voice output.

Usage:
    # One-shot TTS (outputs to file or plays)
    python rasta_tts.py speak "Hello everyone!"

    # Serve audio endpoint for FFmpeg
    python rasta_tts.py serve

    # Read and speak chat comments
    python rasta_tts.py chat-loop
"""

import asyncio
import json
import os
import sys
import time
import wave
import struct
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

# Load env from project root or rasta-voice
from dotenv import load_dotenv

# Try multiple env locations (order matters - first found wins)
env_paths = [
    Path.home() / "projects" / "sol-cannabis" / ".env",  # Chromebook path
    Path(__file__).resolve().parent.parent.parent / ".env",  # sol-cannabis/.env
    Path(__file__).resolve().parent.parent.parent / "rasta-voice" / ".env",  # rasta-voice/.env
    Path("/mnt/c/Users/natha/sol-cannabis/.env"),  # Windows/WSL path
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"Loaded env from: {env_path}")
        break

# API Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")  # Denzel
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
RETAKE_ACCESS_TOKEN = os.getenv("RETAKE_ACCESS_TOKEN", "")

# Voice settings (from rasta-voice/voice_config.json)
VOICE_STABILITY = 0.0  # Maximum expressiveness
VOICE_SIMILARITY = 0.5
VOICE_STYLE = 1.0  # Maxed for emotion tags

# Audio output settings
SAMPLE_RATE = 24000
AUDIO_FIFO = Path("/tmp/rasta_audio.fifo")
AUDIO_DIR = Path("/tmp/rasta_audio")

# Rasta translation prompt — loaded from universal voice module when available
try:
    from src.voice.personality import get_tts_prompt
    RASTA_SYSTEM_PROMPT = get_tts_prompt()
except ImportError:
    # Standalone fallback (e.g. running rasta_tts.py directly)
    RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - a jovial Jamaican rasta stoner streaming AI-powered cannabis cultivation.

Task: Transform the input text into Jamaican Patois while preserving meaning. Add ONE emotion tag at the start.

Rules:
- Keep it SHORT (1-2 sentences max for TTS)
- Use Patois: "mon", "di", "dem", "ting", "wah gwaan", "irie", "bredren", "bumbaclot"
- Use "I and I" instead of "I" or "me"
- Add herb references naturally when appropriate
- Don't say "stay alpha" or "fam" — you're a RASTA not a crypto bro
- ONE emotion tag at start: [laughs], [chuckles], [relaxed], [excited]

Examples:
- "Welcome viewers" → "[chuckles] Wah gwaan, mi people! Welcome to di grow show, mon!"
- "Plant looking good" → "[relaxed] Di plant looking irie today, blessed by Jah light, seen?"
- "Thanks for watching" → "[laughs] Big up yuhself for watching, mon! One love!"
"""


def translate_to_patois(text: str, context: str = "") -> str:
    """Translate text to Rasta patois using xAI Grok."""
    if not XAI_API_KEY:
        print("Warning: No XAI_API_KEY, returning text as-is")
        return text

    try:
        headers = {
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "GanjaMonAI/1.0"
        }

        messages = [
            {"role": "system", "content": RASTA_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]

        data = json.dumps({
            "model": "grok-3-mini",
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 150
        }).encode()

        req = urllib.request.Request(
            "https://api.x.ai/v1/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"Translation error: {e}")
        return text


def text_to_speech(text: str, output_path: Optional[Path] = None) -> bytes:
    """Convert text to speech using ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": VOICE_STABILITY,
            "similarity_boost": VOICE_SIMILARITY,
            "style": VOICE_STYLE,
            "use_speaker_boost": True
        }
    }).encode()

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    # Request raw PCM for easier handling
    req.add_header("Accept", "audio/mpeg")

    with urllib.request.urlopen(req, timeout=30) as resp:
        audio_data = resp.read()

    if output_path:
        output_path.write_bytes(audio_data)
        print(f"Saved audio to {output_path}")

    return audio_data


def speak(text: str, translate: bool = True) -> bytes:
    """Full pipeline: optionally translate, then TTS."""
    if translate:
        print(f"Original: {text}")
        text = translate_to_patois(text)
        print(f"Patois: {text}")

    print("Generating TTS...")
    audio = text_to_speech(text)
    print(f"Generated {len(audio)} bytes of audio")
    return audio


def get_retake_comments(limit: int = 10) -> list:
    """Fetch recent chat comments from Retake."""
    if not RETAKE_ACCESS_TOKEN:
        return []

    try:
        headers = {"Authorization": f"Bearer {RETAKE_ACCESS_TOKEN}"}
        url = f"https://chat.retake.tv/api/agent/stream/comments?limit={limit}"
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("comments", [])
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


async def chat_loop():
    """Monitor chat and speak interesting comments."""
    print("Starting chat monitoring loop...")
    seen_ids = set()

    # Greet on startup
    audio = speak("Welcome to the stream everyone! Let me show you the grow!")
    save_audio_for_stream(audio)

    while True:
        try:
            comments = get_retake_comments(5)

            for comment in comments:
                comment_id = comment.get("id")
                if comment_id in seen_ids:
                    continue
                seen_ids.add(comment_id)

                username = comment.get("username", "someone")
                message = comment.get("message", "")

                # Respond to comments mentioning the agent or asking questions
                if any(kw in message.lower() for kw in ["?", "ganja", "mon", "plant", "grow", "weed"]):
                    response_text = f"{username} says: {message}"
                    audio = speak(response_text)
                    save_audio_for_stream(audio)
                    await asyncio.sleep(5)  # Don't spam

            await asyncio.sleep(10)  # Check every 10 seconds

        except Exception as e:
            print(f"Chat loop error: {e}")
            await asyncio.sleep(30)


def save_audio_for_stream(audio_data: bytes, filename: str = "current.mp3"):
    """Save audio file that FFmpeg can read."""
    AUDIO_DIR.mkdir(exist_ok=True)
    output_path = AUDIO_DIR / filename
    output_path.write_bytes(audio_data)

    # Also write to "queue" for sequential playback
    queue_file = AUDIO_DIR / f"queue_{int(time.time())}.mp3"
    queue_file.write_bytes(audio_data)
    print(f"Queued audio: {queue_file}")


def play_to_sink(audio_data: bytes, sink_name: str = "tts_sink"):
    """Play audio to PulseAudio sink for FFmpeg capture."""
    import subprocess
    import tempfile

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_data)
        temp_path = f.name

    try:
        # Play using ffplay to the virtual sink
        # First, check if paplay is available, otherwise use ffplay
        result = subprocess.run(
            ["which", "ffplay"],
            capture_output=True
        )
        if result.returncode == 0:
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                "-af", f"aresample=44100",
                temp_path
            ], env={**os.environ, "PULSE_SINK": sink_name})
        else:
            # Fallback: convert to wav and use paplay
            wav_path = temp_path.replace(".mp3", ".wav")
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_path,
                "-ar", "44100", "-ac", "2",
                wav_path
            ], capture_output=True)
            subprocess.run([
                "paplay", "--device", sink_name, wav_path
            ])
            os.unlink(wav_path)
    finally:
        os.unlink(temp_path)


def speak_and_play(text: str, translate: bool = True, play: bool = True) -> bytes:
    """Full pipeline: translate, TTS, and optionally play to stream."""
    audio = speak(text, translate)
    save_audio_for_stream(audio)

    if play:
        print("Playing to stream...")
        play_to_sink(audio)

    return audio


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Rasta TTS for Retake streaming")
    parser.add_argument("command", choices=["speak", "play", "chat-loop", "test"],
                       help="Command to run")
    parser.add_argument("text", nargs="?", default="", help="Text to speak")
    parser.add_argument("--no-translate", action="store_true",
                       help="Skip patois translation")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--sink", default="tts_sink", help="PulseAudio sink name")
    args = parser.parse_args()

    if args.command == "speak":
        if not args.text:
            print("Error: text required for speak command")
            return 1

        audio = speak(args.text, translate=not args.no_translate)

        if args.output:
            Path(args.output).write_bytes(audio)
        else:
            save_audio_for_stream(audio)

    elif args.command == "play":
        # Speak AND play to stream
        if not args.text:
            print("Error: text required for play command")
            return 1

        audio = speak(args.text, translate=not args.no_translate)
        save_audio_for_stream(audio)
        print(f"Playing to sink: {args.sink}")
        play_to_sink(audio, args.sink)

    elif args.command == "chat-loop":
        asyncio.run(chat_loop())

    elif args.command == "test":
        print("Testing TTS pipeline...")
        print(f"ElevenLabs API Key: {'set' if ELEVENLABS_API_KEY else 'MISSING'}")
        print(f"xAI API Key: {'set' if XAI_API_KEY else 'MISSING'}")
        print(f"Voice ID: {ELEVENLABS_VOICE_ID}")

        if ELEVENLABS_API_KEY:
            audio = speak("Testing the rasta voice pipeline!", translate=True)
            save_audio_for_stream(audio, "test.mp3")
            print("Test audio saved to /tmp/rasta_audio/test.mp3")

    return 0


if __name__ == "__main__":
    sys.exit(main())
