#!/usr/bin/env python3
"""
Clone a voice from an audio file to create a Jamaican accent voice.

Usage:
    python clone_voice.py path/to/jamaican_audio.mp3 "Rasta Mon"

Requirements:
    - 10-30 seconds of clear speech
    - Minimal background noise
    - Good audio quality

Suggested sources for Jamaican accent samples:
    - Bob Marley interviews (YouTube → mp3)
    - Jamaican news anchors
    - Reggae artist interviews
"""

import os
import sys
from dotenv import load_dotenv
from cartesia import Cartesia

load_dotenv()


def clone_voice(audio_path: str, voice_name: str):
    """Clone a voice from an audio file."""

    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return

    client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

    print(f"🎙️  Cloning voice from: {audio_path}")
    print(f"   Name: {voice_name}")

    try:
        # Read audio file
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        # Clone the voice
        voice = client.voices.clone(
            clip=audio_data,
            name=voice_name,
            description="Jamaican/Rasta accent voice for real-time dialect transformation",
            language="en",
        )

        voice_id = voice.id
        print(f"\n✅ Voice cloned successfully!")
        print(f"   Voice ID: {voice_id}")
        print(f"\n📝 Add this to your .env file:")
        print(f"   CARTESIA_VOICE_ID={voice_id}")

        return voice_id

    except Exception as e:
        print(f"\n❌ Error cloning voice: {e}")
        print("\nTips:")
        print("  - Audio should be 10-30 seconds")
        print("  - Use clear speech with minimal background noise")
        print("  - Supported formats: mp3, wav, m4a, ogg, flac")
        return None


def list_my_voices():
    """List voices you've created."""
    client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

    print("🎤 Your Custom Voices:")
    print("-" * 40)

    voices = client.voices.list()
    custom_count = 0

    for voice in voices:
        # Check if it's a custom voice (not in public library)
        is_public = getattr(voice, "is_public", True)
        if not is_public:
            name = getattr(voice, "name", "Unknown")
            voice_id = getattr(voice, "id", "")
            print(f"  🎙️  {name}")
            print(f"      ID: {voice_id}")
            custom_count += 1

    if custom_count == 0:
        print("  No custom voices yet. Clone one with:")
        print("  python clone_voice.py <audio_file> <voice_name>")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Clone voice:  python clone_voice.py <audio_file> <voice_name>")
        print("  List voices:  python clone_voice.py --list")
        print("\nExample:")
        print("  python clone_voice.py bob_marley_interview.mp3 'Rasta Mon'")
    elif sys.argv[1] == "--list":
        list_my_voices()
    elif len(sys.argv) >= 3:
        clone_voice(sys.argv[1], sys.argv[2])
    else:
        print("❌ Please provide both audio file and voice name")
        print("   python clone_voice.py <audio_file> <voice_name>")
