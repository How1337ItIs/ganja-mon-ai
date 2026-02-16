#!/usr/bin/env python3
"""
Select best voice samples for ElevenLabs upload (YOLO mode - use raw!)

Strategy:
- Prioritize cartoonish sources (60%): Hermes, Rastamouse, Little Jacob
- Add authentic base (30%): Bob Marley, interviews
- Add character variety (10%): Lee Perry, dub poets
- Target: 3 hours = ~200MB of MP3
"""

import shutil
from pathlib import Path
import random

SAMPLES_DIR = Path(__file__).parent / "voice_samples"
OUTPUT_DIR = Path(__file__).parent / "elevenlabs_upload"
TARGET_MB = 200  # ~3 hours of MP3 audio

# Source priorities (weight for selection)
PRIORITY_SOURCES = {
    # Cartoonish/Funny (60% of dataset)
    "hermes": 0.25,  # Futurama - HIGHEST priority
    "little_jacob": 0.20,  # GTA IV - Second highest
    "rastamouse": 0.15,  # Kids show
    "animated": 0.05,
    "cool_runnings": 0.05,
    "comedy": 0.05,
    "caribbean_comedy": 0.05,

    # Authentic base (30%)
    "bob_marley": 0.15,
    "peter_tosh": 0.05,
    "bunny_wailer": 0.03,
    "burning_spear": 0.02,

    # Character variety (10%)
    "lee_perry": 0.05,
    "mutabaruka": 0.02,
    "buju": 0.02,
    "yellowman": 0.01,
}


def get_file_size_mb(file: Path) -> float:
    """Get file size in MB."""
    return file.stat().st_size / 1024 / 1024


def select_samples():
    """Select samples based on priority weights."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all available samples by source
    available = {}
    for source, weight in PRIORITY_SOURCES.items():
        source_dir = SAMPLES_DIR / source
        if source_dir.exists():
            files = list(source_dir.glob("*.mp3"))
            if files:
                available[source] = {
                    "files": files,
                    "weight": weight,
                    "total_mb": sum(get_file_size_mb(f) for f in files)
                }

    print(f"Found {len(available)} sources with samples")
    print(f"\nAvailable sources:")
    for source, data in sorted(available.items(), key=lambda x: x[1]['weight'], reverse=True):
        print(f"  {source}: {len(data['files'])} files, {data['total_mb']:.1f}MB (weight: {data['weight']:.0%})")

    # Calculate target MB per source based on weights
    selected_files = []
    total_mb = 0

    for source, data in sorted(available.items(), key=lambda x: x[1]['weight'], reverse=True):
        target_for_source = TARGET_MB * data['weight']
        source_mb = 0
        source_files = []

        # Shuffle for variety, then select until we hit target
        files = data['files'].copy()
        random.shuffle(files)

        for file in files:
            if source_mb >= target_for_source:
                break
            file_mb = get_file_size_mb(file)
            if total_mb + file_mb <= TARGET_MB:  # Don't exceed total
                source_files.append(file)
                source_mb += file_mb
                total_mb += file_mb

        selected_files.extend(source_files)
        print(f"\n{source}: Selected {len(source_files)} files ({source_mb:.1f}MB)")

    # Copy selected files to upload directory
    print(f"\nCopying {len(selected_files)} files ({total_mb:.1f}MB) to {OUTPUT_DIR}...")

    for i, file in enumerate(selected_files, 1):
        # Create source subdirectory for organization
        dest_dir = OUTPUT_DIR / file.parent.name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / file.name

        if not dest.exists():
            shutil.copy2(file, dest)

        if i % 10 == 0:
            print(f"  Copied {i}/{len(selected_files)}...")

    print(f"\n{'='*60}")
    print(f"SELECTION COMPLETE!")
    print(f"{'='*60}")
    print(f"Files selected: {len(selected_files)}")
    print(f"Total size: {total_mb:.1f}MB (~{total_mb * 1.0:.0f} minutes)")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"\nReady for ElevenLabs Professional Voice Cloning upload!")

    # Create upload instructions
    instructions = OUTPUT_DIR / "UPLOAD_INSTRUCTIONS.txt"
    instructions.write_text(f"""ELEVENLABS PROFESSIONAL VOICE CLONING UPLOAD

Total files: {len(selected_files)}
Total size: {total_mb:.1f}MB (~{total_mb * 1.0:.0f} minutes)

UPLOAD PROCESS:
1. Go to: https://elevenlabs.io/app/voice-lab
2. Click "Add Voice" → "Professional Voice Clone"
3. Upload ALL files from this directory: {OUTPUT_DIR}
4. Voice name: "Ganja Mon Fusion"
5. Description: "Cartoonish funny Jamaican rasta voice - fusion of Hermes Conrad, Little Jacob, Rastamouse, Bob Marley, and reggae legends"
6. Submit and wait for processing (30 min - 2 hours)
7. Copy the new voice ID
8. Update rasta_live.py ELEVENLABS_VOICE_ID

Voice blend:
- 60% Cartoonish (Hermes, Little Jacob, Rastamouse, comedy)
- 30% Authentic (Bob Marley, Peter Tosh, classics)
- 10% Character variety (Lee Perry, dub poets, modern)
""")

    print(f"\nInstructions saved to: {instructions}")


if __name__ == "__main__":
    select_samples()
