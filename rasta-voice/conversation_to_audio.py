#!/usr/bin/env python3
"""
Save Two-Speaker Conversation to Audio File
"""

import os
import time
from pathlib import Path
import wave

import numpy as np
from scipy import signal as scipy_signal
from scipy.io import wavfile
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs import ElevenLabs

# Load environment
load_dotenv(Path(__file__).parent / ".env")

XAI_KEY = os.getenv("XAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")
NATURAL_SPEAKER_VOICE = "bIHbv24MWmeRgasZH58o"

ELEVENLABS_SAMPLE_RATE = 24000
OUTPUT_SAMPLE_RATE = 48000

llm_client = OpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")
tts_client = ElevenLabs(api_key=ELEVENLABS_KEY)

TRANSFORM_PROMPT = """Transform to authentic Jamaican Patois, keeping meaning intact. Use natural expressions like "wah gwaan", "seen", "bredren", "di", "fi". End with "seen?" or "ya know?"."""

NATURAL_SPEAKER_PROMPT = """You are a natural Jamaican Rasta speaker. Respond in 2-3 sentences of authentic Patois. Be friendly and knowledgeable about cannabis cultivation. Previous statement:"""

def resample(audio, from_rate, to_rate):
    if from_rate == to_rate:
        return audio
    num_samples = int(len(audio) * to_rate / from_rate)
    return scipy_signal.resample(audio, num_samples)

def generate_audio(text, voice_id):
    """Generate TTS audio."""
    audio_stream = tts_client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_turbo_v2_5",
        text=text,
        output_format="pcm_24000"
    )
    audio_bytes = b''.join(audio_stream)
    audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, OUTPUT_SAMPLE_RATE)
    return audio_48k

def speak_as_operator(text):
    """Transform and generate operator speech."""
    print(f"\n[OPERATOR]: {text[:60]}...")

    response = llm_client.chat.completions.create(
        model="grok-3",
        messages=[
            {"role": "system", "content": TRANSFORM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.7
    )
    patois = response.choices[0].message.content.strip()
    print(f"  -> Patois: {patois[:60]}...")

    audio = generate_audio(patois, ELEVENLABS_VOICE_ID)
    return audio, patois

def speak_as_guest(previous):
    """Generate natural guest response."""
    print(f"\n[GUEST] Responding...")

    response = llm_client.chat.completions.create(
        model="grok-3",
        messages=[
            {"role": "system", "content": NATURAL_SPEAKER_PROMPT},
            {"role": "user", "content": previous}
        ],
        temperature=0.8
    )
    patois = response.choices[0].message.content.strip()
    print(f"  -> {patois[:60]}...")

    audio = generate_audio(patois, NATURAL_SPEAKER_VOICE)
    return audio, patois

# Conversation
CONVERSATION = [
    ("operator", "Hey everyone, thanks for joining the space! Today I want to talk about how we're using AI to grow cannabis. We have this system called Ganja Mon that monitors everything automatically."),
    ("guest", None),
    ("operator", "Exactly! So the way it works is we have sensors measuring temperature, humidity, VPD, and CO2 levels. Then the AI analyzes all that data and makes decisions about when to turn on lights, fans, or the humidifier."),
    ("guest", None),
    ("operator", "That's a great question. The AI uses something called VPD, which is vapor pressure deficit. It's basically the relationship between temperature and humidity, and it tells you how much the plant is transpiring."),
    ("guest", None),
    ("operator", "Yeah, and the coolest part is everything gets recorded on the Monad blockchain. So you can verify the entire grow from start to finish. It's completely transparent."),
    ("guest", None),
]

def create_silence(duration_seconds):
    """Create silence buffer."""
    return np.zeros(int(OUTPUT_SAMPLE_RATE * duration_seconds), dtype=np.float32)

def main():
    print("\n" + "="*60)
    print("CREATING CONVERSATION AUDIO FILE")
    print("="*60)

    all_audio = []
    previous = ""

    for i, (speaker, text) in enumerate(CONVERSATION):
        print(f"\nTurn {i+1}/{len(CONVERSATION)}")

        if speaker == "operator":
            audio, patois = speak_as_operator(text)
            previous = patois
        else:
            audio, patois = speak_as_guest(previous)
            previous = patois

        all_audio.append(audio)
        all_audio.append(create_silence(1.5))  # Pause between speakers

    # Concatenate all audio
    print("\nCombining audio...")
    full_audio = np.concatenate(all_audio)

    # Convert to int16 for WAV
    audio_int16 = (full_audio * 32767).astype(np.int16)

    # Save
    output_file = Path(__file__).parent / "ganja_mon_conversation.wav"
    wavfile.write(output_file, OUTPUT_SAMPLE_RATE, audio_int16)

    duration = len(full_audio) / OUTPUT_SAMPLE_RATE
    print(f"\n{'='*60}")
    print("SUCCESS!")
    print(f"{'='*60}")
    print(f"File: {output_file}")
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"Sample rate: {OUTPUT_SAMPLE_RATE} Hz")
    print("="*60)

if __name__ == "__main__":
    main()
