#!/usr/bin/env python3
"""
Download Bob Marley interview audio and clone it as a Cartesia voice.

This uses yt-dlp to download audio from YouTube interviews.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Voice sample sources - Jamaican accent options
# We want: Bob Marley authenticity + Hermes Conrad (Futurama) energy
SAMPLE_SOURCES = {
    "bob_marley": [
        # Bob Marley interviews - authentic, natural, spiritual
        "https://www.youtube.com/watch?v=jcHqPhkHrFg",
        "https://www.youtube.com/watch?v=bxXH-Kc5Jmc",
    ],
    "hermes": [
        # Hermes Conrad (Phil LaMarr) - energetic, comedic, bureaucratic
        # Search "Hermes Conrad best moments" or "Hermes sweet something of somewhere"
        "https://www.youtube.com/watch?v=_P1bu4HUAMs",  # Hermes compilation
    ],
    "combo": [
        # Real Jamaican speakers with energy (news, podcasts, etc.)
        # These tend to have cleaner audio than old interviews
    ]
}

# Recommended: Hermes for cleaner audio + more animated personality


def download_audio(url: str, output_path: str = "rasta_sample.mp3"):
    """Download audio from YouTube using yt-dlp."""
    print(f"📥 Downloading audio from: {url}")

    try:
        # Download best audio, convert to mp3
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "--audio-quality", "0",  # Best quality
            "-o", output_path.replace(".mp3", ".%(ext)s"),
            "--no-playlist",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Audio saved to: {output_path}")
            return output_path
        else:
            print(f"❌ Download failed: {result.stderr}")
            return None

    except FileNotFoundError:
        print("❌ yt-dlp not found. Install with: pip install yt-dlp")
        return None


def trim_audio(input_path: str, output_path: str, start: int = 0, duration: int = 30):
    """Trim audio to a specific duration using ffmpeg."""
    print(f"✂️  Trimming to {duration} seconds...")

    try:
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start),
            "-t", str(duration),
            "-y",  # Overwrite
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Trimmed audio: {output_path}")
            return output_path
        else:
            print(f"❌ Trim failed: {result.stderr}")
            return None

    except FileNotFoundError:
        print("❌ ffmpeg not found. Install it for your OS.")
        return None


def clone_voice_cartesia(audio_path: str, voice_name: str = "Rasta Mon"):
    """Clone the voice using Cartesia API."""
    from cartesia import Cartesia

    api_key = os.getenv("CARTESIA_API_KEY")
    if not api_key:
        print("❌ CARTESIA_API_KEY not set in .env")
        return None

    client = Cartesia(api_key=api_key)

    print(f"\n🎙️  Cloning voice: {voice_name}")
    print(f"   From: {audio_path}")

    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        voice = client.voices.clone(
            clip=audio_data,
            name=voice_name,
            description="Jamaican/Rasta accent cloned for real-time voice transformation",
            language="en",
        )

        voice_id = voice.id
        print(f"\n✅ SUCCESS! Voice cloned!")
        print(f"   Voice ID: {voice_id}")
        print(f"\n📝 Update your .env file:")
        print(f"   CARTESIA_VOICE_ID={voice_id}")

        # Auto-update .env
        update = input("\nUpdate .env automatically? [y/N]: ").strip().lower()
        if update == "y":
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            with open(env_path, "r") as f:
                content = f.read()
            content = content.replace(
                f"CARTESIA_VOICE_ID={os.getenv('CARTESIA_VOICE_ID', '')}",
                f"CARTESIA_VOICE_ID={voice_id}"
            )
            with open(env_path, "w") as f:
                f.write(content)
            print("✅ .env updated!")

        return voice_id

    except Exception as e:
        print(f"\n❌ Clone failed: {e}")
        return None


def main():
    print("=" * 60)
    print("🌿 RASTA VOICE CLONER")
    print("=" * 60)
    print("\nThis will:")
    print("1. Download Bob Marley interview audio")
    print("2. Trim it to 30 seconds")
    print("3. Clone it as a Cartesia voice")
    print()

    # Check if we already have an audio file
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        print(f"Using provided audio: {audio_path}")
    else:
        print("Options:")
        print("  1. Download from YouTube (requires yt-dlp)")
        print("  2. Use existing audio file")
        print()
        choice = input("Choice [1/2]: ").strip()

        if choice == "2":
            audio_path = input("Path to audio file: ").strip()
        else:
            # Download from YouTube
            url = input(f"YouTube URL (or press Enter for default): ").strip()
            if not url:
                url = SAMPLE_SOURCES[0]

            audio_path = download_audio(url)
            if not audio_path:
                return

            # Trim to 30 seconds
            trimmed = trim_audio(audio_path, "rasta_sample_trimmed.mp3", start=10, duration=30)
            if trimmed:
                audio_path = trimmed

    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return

    # Clone the voice
    voice_name = input("Voice name [Rasta Mon]: ").strip() or "Rasta Mon"
    clone_voice_cartesia(audio_path, voice_name)


if __name__ == "__main__":
    main()
