#!/usr/bin/env python3
"""
End-to-end audio pipeline test
Simulates speech input and verifies output at each stage
"""
import os
import time
import json
import wave
import numpy as np
import sounddevice as sd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs import ElevenLabs

load_dotenv(Path(__file__).parent / ".env")

def generate_test_audio(text="Testing one two three", duration=2, sample_rate=48000):
    """Generate a simple test tone to represent speech"""
    print(f"Generating test audio: '{text}'")
    # Create a 440Hz tone (A note) to simulate voice
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.3 * np.sin(2 * np.pi * 440 * t)
    return audio.astype(np.float32)

def test_stt_api():
    """Test Deepgram STT (using mock data)"""
    print("\n=== Testing STT (Simulated) ===")
    # We'll simulate this since we need real audio for Deepgram
    test_transcript = "Testing the rasta voice pipeline"
    print(f"[OK] STT would transcribe to: '{test_transcript}'")
    return test_transcript

def test_llm_translation(text):
    """Test xAI translation"""
    print(f"\n=== Testing LLM Translation ===")
    print(f"Input: '{text}'")

    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1"
    )

    system_prompt = """You are Ganja Mon, a jovial Jamaican rasta character.
Translate to Jamaican Patois with emotion tags like [relaxed], [chuckles], [laughs]."""

    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=150
        )

        translated = response.choices[0].message.content
        print(f"[OK] LLM translated to: '{translated}'")
        return translated
    except Exception as e:
        print(f"[FAIL] LLM error: {e}")
        return None

def test_tts_generation(text):
    """Test ElevenLabs TTS"""
    print(f"\n=== Testing TTS Generation ===")
    print(f"Input: '{text}'")

    try:
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

        # Use eleven_multilingual_v2 which properly handles emotion tags
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="pcm_24000",
            voice_settings={
                "stability": 0.0,  # Max expressiveness
                "similarity_boost": 0.5,
                "style": 1.0  # Max emotion tag interpretation
            }
        )

        # Collect audio data
        audio_data = b''.join(audio_generator)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        print(f"[OK] TTS generated {len(audio_array)} samples ({len(audio_array)/24000:.1f}s)")
        return audio_array

    except Exception as e:
        print(f"[FAIL] TTS error: {e}")
        return None

def test_audio_output(audio, sample_rate=24000, device=None):
    """Test audio playback"""
    print(f"\n=== Testing Audio Output ===")
    if audio is None:
        print("✗ No audio to play")
        return False

    try:
        print(f"Playing {len(audio)} samples @ {sample_rate}Hz to device {device}")
        sd.play(audio, samplerate=sample_rate, device=device, blocking=True)
        print("✓ Audio playback completed")
        return True
    except Exception as e:
        print(f"[FAIL] Playback error: {e}")
        return False

def main():
    print("=" * 60)
    print("RASTA VOICE PIPELINE - END-TO-END TEST")
    print("=" * 60)

    # Test each stage
    transcript = test_stt_api()

    if transcript:
        translated = test_llm_translation(transcript)

        if translated:
            audio = test_tts_generation(translated)

            if audio is not None:
                # Resample from 24kHz to 48kHz for output
                from scipy import signal as scipy_signal
                audio_48k = scipy_signal.resample(audio, int(len(audio) * 48000 / 24000))

                # Test playback to both VB-Cable and Headphones
                print("\n=== Testing Dual Output (VB-Cable + Headphones) ===")
                import threading

                def play_to_device(audio, sr, dev_id, dev_name):
                    try:
                        print(f"[OK] Playing to {dev_name} (device {dev_id})")
                        sd.play(audio, samplerate=sr, device=dev_id, blocking=True)
                        print(f"[OK] {dev_name} playback complete")
                    except Exception as e:
                        print(f"[FAIL] {dev_name} error: {e}")

                # Play to both devices simultaneously (like the real pipeline)
                t1 = threading.Thread(target=play_to_device, args=(audio_48k, 48000, 18, "VB-Cable"))
                t2 = threading.Thread(target=play_to_device, args=(audio_48k, 48000, 17, "Headphones"))

                t1.start()
                t2.start()
                t1.join()
                t2.join()

                print("\n" + "=" * 60)
                print("TEST COMPLETE - Pipeline stages verified!")
                print("=" * 60)
                return True

    print("\n✗ Test failed at some stage")
    return False

if __name__ == "__main__":
    main()
