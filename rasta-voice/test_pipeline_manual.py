#!/usr/bin/env python3
"""
Manual Pipeline Testing Script

Human-in-the-loop testing for voice quality analysis.
Shows each pipeline stage clearly for debugging.
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
from scipy import signal as scipy_signal
from dotenv import load_dotenv
from websockets import connect as ws_connect
from openai import OpenAI
from elevenlabs import ElevenLabs

# Load environment
load_dotenv(Path(__file__).parent / ".env")

# Configuration
DEEPGRAM_KEY = os.getenv("DEEPGRAM_API_KEY")
XAI_KEY = os.getenv("XAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

SAMPLE_RATE = 16000
VBCABLE_SAMPLE_RATE = 48000
ELEVENLABS_SAMPLE_RATE = 24000

# Find devices
def find_device(name_pattern, is_output=True):
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if name_pattern.lower() in d['name'].lower():
            is_valid = (is_output and d['max_output_channels'] > 0) or \
                      (not is_output and d['max_input_channels'] > 0)
            if is_valid and d.get('default_samplerate') == VBCABLE_SAMPLE_RATE:
                return i
    # Fallback to any matching device
    for i, d in enumerate(devices):
        if name_pattern.lower() in d['name'].lower():
            is_valid = (is_output and d['max_output_channels'] > 0) or \
                      (not is_output and d['max_input_channels'] > 0)
            if is_valid:
                return i
    return None

CABLE_DEVICE = find_device("cable input", is_output=True)
HEADPHONE_DEVICE = find_device("headphone", is_output=True)

print("\n" + "="*60)
print("PIPELINE TESTING - HUMAN IN THE LOOP")
print("="*60)
print(f"VB-Cable Device: {CABLE_DEVICE}")
print(f"Headphone Device: {HEADPHONE_DEVICE}")
print("="*60 + "\n")

# System prompt
RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - a wise island philosopher AI with deep Jamaican/Caribbean roots. Transform spoken English into authentic Jamaican Patois.

CORE RULES:
- Keep the EXACT meaning and technical terms
- Use natural Jamaican speech patterns
- Don't force every word into patois
- Keep it conversational and clear

TRANSFORMATIONS:
- "what's up" -> "wah gwaan"
- "I am/I'm" -> "mi" or "me"
- "you" -> "yuh" or "unu" (plural)
- "this/that" -> "dis/dat"
- "the" -> "di"
- "going to" -> "gonna" or "gwine"
- End thoughts with "seen?" "ya know?" "ya hear mi?"

Transform the following English to Patois, keeping technical terms intact:"""

# LLM client
llm_client = OpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")

# TTS client
tts_client = ElevenLabs(api_key=ELEVENLABS_KEY)

def resample(audio, from_rate, to_rate):
    """Resample audio using scipy."""
    if from_rate == to_rate:
        return audio
    num_samples = int(len(audio) * to_rate / from_rate)
    return scipy_signal.resample(audio, num_samples)

async def transcribe_once():
    """Listen and transcribe one utterance."""
    print("\n[STAGE 1: LISTENING] Speak now...")

    url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en&smart_format=true"

    async with ws_connect(url, extra_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}) as ws:

        # Recording state
        audio_data = []
        is_recording = False
        silence_count = 0

        def audio_callback(indata, frames, time_info, status):
            nonlocal is_recording, silence_count, audio_data

            # Detect speech (simple energy threshold)
            energy = np.abs(indata).mean()

            if energy > 0.02:  # Speech detected
                is_recording = True
                silence_count = 0
                audio_data.append(indata.copy())
            elif is_recording:
                silence_count += 1
                audio_data.append(indata.copy())

                # Stop after 1 second of silence
                if silence_count > 30:  # ~1 second at 16kHz chunks
                    raise sd.CallbackStop()

        # Start recording
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                           dtype='int16', callback=audio_callback):

            transcription = ""

            async def send_audio():
                """Send audio to Deepgram."""
                try:
                    while True:
                        if audio_data:
                            chunk = audio_data.pop(0)
                            await ws.send(chunk.tobytes())
                        await asyncio.sleep(0.01)
                except Exception:
                    pass

            async def receive_transcription():
                """Receive transcription from Deepgram."""
                nonlocal transcription
                try:
                    async for msg in ws:
                        result = json.loads(msg)
                        if result.get("type") == "Results":
                            transcript = result.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                            if transcript:
                                transcription = transcript
                except Exception:
                    pass

            # Run both tasks
            await asyncio.gather(send_audio(), receive_transcription())

            return transcription

def transform_to_patois(text):
    """Transform English to Patois using Grok."""
    print(f"\n[STAGE 2: PATOIS TRANSFORM]")
    print(f"   Original: {text}")

    response = llm_client.chat.completions.create(
        model="grok-2-1212",
        messages=[
            {"role": "system", "content": RASTA_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.7
    )

    patois = response.choices[0].message.content.strip()
    print(f"   Patois: {patois}")
    return patois

def generate_and_play_tts(text):
    """Generate TTS and play to both devices."""
    print(f"\n[STAGE 3: TEXT-TO-SPEECH]")
    print(f"   Generating audio for: {text}")

    start = time.perf_counter()

    # Generate audio
    audio_stream = tts_client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        model_id="eleven_turbo_v2_5",
        text=text,
        output_format="pcm_24000"
    )

    # Collect audio bytes
    audio_bytes = b''.join(audio_stream)
    latency = (time.perf_counter() - start) * 1000

    print(f"   Generation time: {latency:.0f}ms")

    # Convert to numpy
    audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, VBCABLE_SAMPLE_RATE)

    # Play to VB-Cable
    if CABLE_DEVICE is not None:
        print(f"   Playing to VB-Cable (device {CABLE_DEVICE})...")
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=CABLE_DEVICE)
        sd.wait()

    # Play to Headphones
    if HEADPHONE_DEVICE is not None:
        print(f"   Playing to Headphones (device {HEADPHONE_DEVICE})...")
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=HEADPHONE_DEVICE)
        sd.wait()

    print(f"   [OK] Playback complete")

async def test_cycle():
    """Run one test cycle."""

    # Stage 1: Transcribe
    transcription = await transcribe_once()

    if not transcription:
        print("   [ERROR] No speech detected. Try again.")
        return False

    print(f"   Transcription: {transcription}")

    # Stage 2: Transform
    patois = transform_to_patois(transcription)

    # Stage 3: TTS
    generate_and_play_tts(patois)

    return True

async def main():
    """Main testing loop."""

    print("\nOpen ganja_mon_test_script.md and read each test phrase")
    print("Press Enter after speaking to process")
    print("Type 'q' to quit\n")

    test_num = 1

    while True:
        print("\n" + "="*60)
        print(f"TEST #{test_num}")
        print("="*60)

        cmd = input("\nReady? [Enter to record, 'q' to quit]: ").strip().lower()

        if cmd == 'q':
            print("\n[OK] Testing complete!")
            break

        success = await test_cycle()

        if success:
            print("\n" + "-"*60)
            input("Press Enter for next test...")
            test_num += 1

if __name__ == "__main__":
    asyncio.run(main())
