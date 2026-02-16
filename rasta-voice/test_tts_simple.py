#!/usr/bin/env python3
"""Simple TTS test - plays to default audio device only."""
import os
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from pathlib import Path
from elevenlabs import ElevenLabs

load_dotenv(Path(__file__).parent / ".env")

def main():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")  # Denzel

    print("Generating TTS audio...")
    client = ElevenLabs(api_key=api_key)

    audio_data = client.text_to_speech.convert(
        text="Wah gwaan, mi people! How unu feeling today? Big up yuhself!",
        voice_id=voice_id,
        model_id="eleven_turbo_v2_5",
        output_format="pcm_24000",
    )

    audio_bytes = b''.join(audio_data)
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    print(f"Audio length: {len(audio_np)} samples at 24kHz = {len(audio_np)/24000:.2f} seconds")
    print("Playing to default audio device at 24kHz...")

    # Play directly - let sounddevice handle sample rate conversion
    sd.play(audio_np, samplerate=24000)
    sd.wait()

    print("Done!")

if __name__ == "__main__":
    main()
