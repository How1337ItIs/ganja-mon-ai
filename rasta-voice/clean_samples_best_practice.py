#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Voice Samples - BEST PRACTICE for ElevenLabs PVC

Based on ElevenLabs recommendations:
- MINIMAL processing (AI mimics everything, keep it natural!)
- Simple ffmpeg filtering (skip Demucs for speed in YOLO mode)
- Keep natural pauses and character (no over-editing)
- Remove only excessive silence and obvious issues
"""

import subprocess
import argparse
import sys
from pathlib import Path
from typing import List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

VOICE_SAMPLES_DIR = Path(__file__).parent / "voice_samples"
CLEANED_DIR = Path(__file__).parent / "voice_samples_cleaned"
FFMPEG_PATH = r"C:\Users\natha\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"

# Sources that likely have background music (need Demucs)
MUSIC_SOURCES = ["hermes", "rastamouse", "little_jacob", "animated", "cool_runnings", "comedy"]

# Sources that are pure speech (interviews - minimal processing)
SPEECH_SOURCES = ["bob_marley", "lee_perry", "peter_tosh", "buju", "capleton", "sizzla",
                  "mutabaruka", "toots", "burning_spear", "yellowman", "jimmy_cliff",
                  "bunny_wailer", "shaggy", "sean_paul", "beenie_man", "bounty_killer",
                  "gregory_isaacs", "ska_artists", "vybz_kartel", "damian_marley",
                  "dennis_brown", "oku_onuora", "dancehall", "reggae_artists", "caribbean_comedy"]


def separate_vocals_ffmpeg(input_file: Path, output_file: Path):
    """Use ffmpeg bandpass filter to isolate vocals (fast, good enough for YOLO mode)."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(input_file),
        "-af",
        # Voice isolation filters:
        "highpass=f=200,"  # Remove low rumble
        "lowpass=f=3400,"  # Remove high freq (isolate speech range)
        "volume=2.0,"  # Boost vocals
        "silenceremove=stop_periods=-1:stop_duration=3:stop_threshold=-40dB,"  # Remove silence
        "loudnorm=I=-18:TP=-3",  # Normalize
        "-ar", "48000",
        "-ac", "1",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_file)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return True
    except Exception:
        return False


def minimal_cleanup(input_file: Path, output_file: Path):
    """
    Minimal cleanup for interview files:
    1. Remove excessive silence (3+ seconds)
    2. Light normalization
    3. That's it! (keep natural pauses, uhms, character)
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(input_file),
        "-af",
        # MINIMAL processing:
        "silenceremove=stop_periods=-1:stop_duration=3:stop_threshold=-40dB,"  # Remove silence >3s
        "loudnorm=I=-18:TP=-3",  # Light normalization only
        "-ar", "48000",  # 48kHz
        "-ac", "1",  # Mono
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_file)
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return True
    except Exception as e:
        print(f"  Cleanup failed: {e}")
        return False


def process_source(source_name: str, limit: int = 0) -> int:
    """Process all files from a source directory."""
    source_dir = VOICE_SAMPLES_DIR / source_name
    if not source_dir.exists():
        return 0

    mp3_files = sorted(source_dir.glob("*.mp3"))
    if limit > 0:
        mp3_files = mp3_files[:limit]

    if not mp3_files:
        return 0

    print(f"\n{'='*60}")
    print(f"Processing {source_name}: {len(mp3_files)} files")
    print(f"Type: {'MUSIC SEPARATION' if source_name in MUSIC_SOURCES else 'MINIMAL CLEANUP'}")
    print(f"{'='*60}")

    cleaned_count = 0
    for i, mp3_file in enumerate(mp3_files, 1):
        output_file = CLEANED_DIR / source_name / f"clean_{mp3_file.name}"

        if output_file.exists():
            print(f"  [{i}/{len(mp3_files)}] SKIP: {mp3_file.name} (already processed)")
            cleaned_count += 1
            continue

        print(f"  [{i}/{len(mp3_files)}] Processing: {mp3_file.name}")

        if source_name in MUSIC_SOURCES:
            # Use ffmpeg bandpass for cartoon/TV sources (fast, good enough)
            success = separate_vocals_ffmpeg(mp3_file, output_file)
        else:
            # Minimal cleanup for interviews
            success = minimal_cleanup(mp3_file, output_file)

        if success:
            cleaned_count += 1
            size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"    ✓ Cleaned: {size_mb:.1f}MB")

    return cleaned_count


def main():
    parser = argparse.ArgumentParser(description="Clean voice samples for ElevenLabs PVC")
    parser.add_argument("--source", type=str, help="Process specific source only")
    parser.add_argument("--limit", type=int, default=0, help="Limit files per source (for testing)")
    parser.add_argument("--cartoonish-only", action="store_true", help="Process only cartoonish sources (Hermes, Rastamouse, Little Jacob)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    args = parser.parse_args()

    # Determine which sources to process
    if args.source:
        sources = [args.source]
    elif args.cartoonish_only:
        sources = ["hermes", "rastamouse", "little_jacob", "animated", "cool_runnings"]
    else:
        # Process ALL sources
        sources = [d.name for d in VOICE_SAMPLES_DIR.iterdir() if d.is_dir()]

    if args.dry_run:
        print("Would process:")
        for src in sources:
            src_dir = VOICE_SAMPLES_DIR / src
            if src_dir.exists():
                count = len(list(src_dir.glob("*.mp3")))
                if args.limit:
                    count = min(count, args.limit)
                method = "DEMUCS" if src in MUSIC_SOURCES else "MINIMAL"
                print(f"  {src}: {count} files ({method})")
        return 0

    # Process sources
    total_cleaned = 0
    for source in sources:
        cleaned = process_source(source, limit=args.limit)
        total_cleaned += cleaned

    print(f"\n{'='*60}")
    print(f"CLEANING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total files cleaned: {total_cleaned}")
    print(f"Output directory: {CLEANED_DIR}")

    # Calculate total size
    total_size = sum(f.stat().st_size for f in CLEANED_DIR.rglob("*.mp3"))
    print(f"Total cleaned audio: {total_size / 1024 / 1024 / 1024:.2f}GB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
