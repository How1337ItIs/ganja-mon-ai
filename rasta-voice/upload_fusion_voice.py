#!/usr/bin/env python3
"""
Upload fusion voice to ElevenLabs Professional Voice Cloning

Autonomous YOLO mode - creates PVC and uploads all samples.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()

UPLOAD_DIR = Path(__file__).parent / "elevenlabs_upload"
API_KEY = os.getenv("ELEVENLABS_API_KEY")

def upload_pvc():
    """Create and upload Professional Voice Clone."""
    client = ElevenLabs(api_key=API_KEY)

    print("Creating Ganja Mon Fusion Voice...")
    print(f"Uploading from: {UPLOAD_DIR}")

    # Collect all MP3 files
    all_files = list(UPLOAD_DIR.rglob("*.mp3"))
    print(f"Found {len(all_files)} files ({sum(f.stat().st_size for f in all_files) / 1024 / 1024:.1f}MB)")

    # Create PVC voice
    print("\nStep 1: Creating Professional Voice Clone...")

    try:
        # Use Instant Voice Cloning (IVC) - works with API, good for 1-2 mins audio
        # Select best cartoonish clips (Hermes + Little Jacob priority)
        hermes_files = [f for f in all_files if f.parent.name == "hermes"][:2]
        little_jacob_files = [f for f in all_files if f.parent.name == "little_jacob"][:2]
        rastamouse_files = [f for f in all_files if f.parent.name == "rastamouse"][:1]

        ivc_files = hermes_files + little_jacob_files + rastamouse_files

        print(f"Using Instant Voice Cloning with {len(ivc_files)} best clips:")
        for f in ivc_files:
            print(f"  - {f.parent.name}/{f.name}")

        # Clone voice using IVC - correct SDK method
        voice = client.voices.ivc.create(
            name="Ganja Mon Fusion",
            description="Cartoonish funny Jamaican rasta - Hermes Conrad + Little Jacob + Rastamouse fusion",
            files=[str(f) for f in ivc_files]
        )

        voice_id = voice.voice_id
        print(f"\nVoice created! ID: {voice_id}")
        print(f"\nUpdate .env:")
        print(f"ELEVENLABS_VOICE_ID={voice_id}")

        # Save voice ID
        voice_id_file = Path(__file__).parent / "FUSION_VOICE_ID.txt"
        voice_id_file.write_text(f"{voice_id}\n\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\nType: Instant Voice Clone\n")

        # Auto-update .env
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            env_content = env_file.read_text()
            if "ELEVENLABS_VOICE_ID=" in env_content:
                # Replace existing
                import re
                new_content = re.sub(
                    r'ELEVENLABS_VOICE_ID=.*',
                    f'ELEVENLABS_VOICE_ID={voice_id}',
                    env_content
                )
                env_file.write_text(new_content)
                print(f"\n.env updated automatically!")

        return voice_id

    except Exception as e:
        print(f"\nError: {e}")
        print(f"\nManual upload needed at: https://elevenlabs.io/app/voice-lab")
        return None


if __name__ == "__main__":
    print("="*60)
    print("ELEVENLABS PROFESSIONAL VOICE CLONING UPLOAD")
    print("="*60)
    upload_pvc()
