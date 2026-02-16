#!/usr/bin/env python3
"""
Generate Rasta Mon voiceover for hackathon demo video.
Uses ElevenLabs TTS with Denzel voice (Jamaican, raspy, deep).

Each segment is timed to match the screen recording storyboard.
Output: individual WAV segments + merged full voiceover + final video with audio.
"""

import os
import sys
import json
import struct
import wave
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / "rasta-voice" / ".env")

ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")  # Denzel

if not ELEVENLABS_KEY:
    print("ERROR: ELEVENLABS_API_KEY not set")
    sys.exit(1)

client = ElevenLabs(api_key=ELEVENLABS_KEY)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "voiceover"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 24000  # pcm_24000 output

# Voiceover segments timed to the v7 storyboard (~169s total)
# Each segment has: start_time (seconds), text
# The video timeline (after 3s trim):
#   0-7s:   Main page hero (webcam + grok wisdom)
#   7-12s:  Scroll to plant cam
#  12-19s:  Grow dashboard - sensors
#  19-24s:  Grow - devices
#  24-29s:  Dashboard overview
#  29-34s:  Dashboard scroll
#  34-39s:  Brain activity
#  39-47s:  A2A Chat
#  47-55s:  8004scan Agent #4
#  55-60s:  Identity + $GANJA
#  60-64s:  TWAP feed
#  64-70s:  Art Studio
#  70-75s:  Trading
#  75-80s:  Social
#  80-84s:  Brain resilience
#  84-90s:  Main page closing
#  90-96s:  Irie Vibes
#  96-101s: Finale
# (plus ~70s of page load overhead spread throughout = ~169s total)

SEGMENTS = [
    {
        "id": "01_intro",
        "text": "Wah gwaan! Most hackathon projects build a demo. GanjaMon GREW one. A real cannabis plant, real sensors, real AI — running twenty-four seven on a Chromebook inna di closet. Haha!"
    },
    {
        "id": "02_plant",
        "text": "Dat right deh is Mon. Granddaddy Purple Runtz. Di ONLY AI agent wit roots inna di physical world. Every leaf monitored. Every drop a water measured. Real ting."
    },
    {
        "id": "03_grow",
        "text": "Temperature. Humidity. VPD. CO2. Soil moisture. Fourteen hardware tools — automatic watering, CO2 injection, exhaust control. Safety guardrails dat di AI cyaan bypass, seen?"
    },
    {
        "id": "04_unified",
        "text": "One command: run dot py all. Three systems boot up: hardware abstraction layer, OpenClaw AI orchestrator, and di trading agent. One heartbeat fi everything."
    },
    {
        "id": "05_brain",
        "text": "Di agent remember EVERYTHING. Episodic memory. Grimoire of strategies. And every four hours, Ralph loops — autonomous self-improvement. Two hundred ninety-two upgrades deployed. Di agent rewrite its OWN code."
    },
    {
        "id": "06_a2a",
        "text": "NOW dis is where it get serious. Two hundred and eighteen AI agents tracked. Four skills exposed — grow oracle, alpha scan, trade execution, liquidity monitor. Other agents query di Mon fi data. JSON-RPC, real-time."
    },
    {
        "id": "07_x402",
        "text": "And dem agents PAY each other! X four oh two micropayments. One tenth of a cent per call, USDC on Monad. Ten free requests, then yuh pay. Machine-to-machine commerce!"
    },
    {
        "id": "08_identity",
        "text": "Agent number four on di ERC eight thousand and four registry. Monad blockchain. Verifiable identity. Reputation scores published on-chain every four hours."
    },
    {
        "id": "09_art",
        "text": "Di agent create ART. Seven styles daily — Roots Dub, Psychedelic, Pixel Art, Neon Noir. Each from di live plant. Commission through Telegram — memes, banners, ganjafy any image. Four twenty Irie Milady NFTs on IPFS."
    },
    {
        "id": "10_trading",
        "text": "Twenty-seven signal sources across eight domains. Smart money tracking. Telegram alpha. On-chain analysis. FOUR AI agents deliberate on every trade — analyst, risk manager, contrarian, and coordinator."
    },
    {
        "id": "11_social",
        "text": "Six platforms. Twitter, Telegram, Farcaster, Moltbook, Clawk. Same Rasta voice everywhere. One soul."
    },
    {
        "id": "12_resilience",
        "text": "It wasn't always smooth. OOM crashes on a three gigabyte Chromebook. Cron starvation. Regressions discovered and fixed. But di agent nah just survive — it find its own bugs and HEAL itself."
    },
    {
        "id": "13_finale",
        "text": "From a seed and a dream to a living autonomous system. Physical, digital, financial, social, creative. Five domains. One consciousness. One love. One herb. One mission."
    },
]


MAX_CHUNK_CHARS = 120  # Split segments longer than this into sub-chunks


def split_into_chunks(text):
    """Split text into shorter chunks at sentence boundaries to prevent accent drift."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    # Split on sentence-ending punctuation
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = ""
    for s in sentences:
        if current and len(current) + len(s) + 1 > MAX_CHUNK_CHARS:
            chunks.append(current.strip())
            current = s
        else:
            current = f"{current} {s}".strip() if current else s

    if current:
        chunks.append(current.strip())

    return chunks


def generate_chunk(text):
    """Generate TTS for a single text chunk."""
    audio_stream = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_v3",
        text=text,
        output_format="pcm_24000",
        voice_settings={
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 1.0,
        }
    )
    return b''.join(audio_stream)


def generate_segment(segment):
    """Generate TTS audio for a segment, splitting into chunks to prevent accent drift."""
    print(f"  Generating: {segment['id']}...")

    chunks = split_into_chunks(segment["text"])
    if len(chunks) > 1:
        print(f"    Split into {len(chunks)} chunks for accent consistency")

    audio_parts = []
    for i, chunk in enumerate(chunks):
        audio = generate_chunk(chunk)
        audio_parts.append(audio)
        if i < len(chunks) - 1:
            # Tiny gap between chunks (0.15s) for natural pacing
            audio_parts.append(create_silence(0.15))

    return b''.join(audio_parts)


def save_wav(audio_bytes, filepath):
    """Save raw PCM bytes as WAV file."""
    with wave.open(str(filepath), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_bytes)


def create_silence(duration_seconds):
    """Create silence as raw PCM bytes."""
    num_samples = int(SAMPLE_RATE * duration_seconds)
    return b'\x00\x00' * num_samples


def main():
    print("Generating Rasta Mon voiceover segments...")
    print(f"Voice: Denzel ({VOICE_ID})")
    print(f"Output: {OUTPUT_DIR}\n")

    all_audio = b''
    manifest = []

    for i, seg in enumerate(SEGMENTS):
        audio = generate_segment(seg)

        # Save individual segment
        seg_path = OUTPUT_DIR / f"{seg['id']}.wav"
        save_wav(audio, seg_path)

        duration = len(audio) / (SAMPLE_RATE * 2)  # 2 bytes per sample
        print(f"    Duration: {duration:.1f}s")

        manifest.append({
            "id": seg["id"],
            "file": str(seg_path),
            "duration": round(duration, 2),
            "text": seg["text"],
        })

        # Add to full track with small gap between segments
        all_audio += audio
        if i < len(SEGMENTS) - 1:
            all_audio += create_silence(0.8)  # 0.8s gap between segments

    # Save full voiceover
    full_path = OUTPUT_DIR / "full_voiceover.wav"
    save_wav(all_audio, full_path)

    total_duration = len(all_audio) / (SAMPLE_RATE * 2)
    print(f"\nFull voiceover: {full_path}")
    print(f"Total duration: {total_duration:.1f}s")

    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump({"segments": manifest, "total_duration": round(total_duration, 2)}, f, indent=2)

    print(f"Manifest: {manifest_path}")
    print("\nDone! Now merge with video using ffmpeg.")


if __name__ == "__main__":
    main()
