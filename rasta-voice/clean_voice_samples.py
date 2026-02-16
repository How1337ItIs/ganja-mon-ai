#!/usr/bin/env python3
"""
Clean voice samples for ElevenLabs Professional Voice Cloning

Process:
1. Separate vocals from music (using ffmpeg filters)
2. Remove silence and music-only sections
3. Apply noise reduction
4. Normalize audio levels
5. Export clean speech-only clips

Requires: ffmpeg with libsox
"""

import subprocess
import json
from pathlib import Path
from typing import List, Tuple
import argparse

VOICE_SAMPLES_DIR = Path(__file__).parent / "voice_samples"
CLEANED_DIR = Path(__file__).parent / "voice_samples_cleaned"


def detect_speech_segments(audio_file: Path, min_silence_len: float = 1.0, silence_thresh: str = "-40dB") -> List[Tuple[float, float]]:
    """
    Detect segments with speech (non-silence) using ffmpeg silencedetect.
    Returns list of (start_time, end_time) tuples in seconds.
    """
    cmd = [
        "ffmpeg",
        "-i", str(audio_file),
        "-af", f"silencedetect=noise={silence_thresh}:d={min_silence_len}",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
    output = result.stdout

    # Parse silence detection output
    segments = []
    silence_start = None
    last_silence_end = 0.0

    for line in output.split('\n'):
        if 'silence_start' in line:
            time_str = line.split('silence_start: ')[1].split()[0]
            silence_start = float(time_str)
            # Add speech segment before this silence
            if silence_start > last_silence_end + 0.5:  # At least 0.5s of speech
                segments.append((last_silence_end, silence_start))

        if 'silence_end' in line:
            time_str = line.split('silence_end: ')[1].split('|')[0].strip()
            last_silence_end = float(time_str)

    return segments


def extract_vocals_only(input_file: Path, output_file: Path):
    """
    Use ffmpeg highpass/lowpass filters to isolate voice frequency range.
    Human speech is typically 85Hz - 8000Hz, with most energy 300-3400Hz.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-af",
        # Voice isolation filter chain:
        "highpass=f=100,"  # Remove rumble below 100Hz
        "lowpass=f=8000,"  # Remove highs above 8kHz
        "afftdn=nf=-25,"  # Denoise (FFT-based)
        "loudnorm=I=-18:TP=-3:LRA=11",  # Normalize to broadcast standards
        "-ar", "48000",  # 48kHz sample rate
        "-ac", "1",  # Mono
        "-c:a", "libmp3lame",
        "-b:a", "192k",  # 192kbps MP3
        str(output_file)
    ]

    subprocess.run(cmd, check=True, capture_output=True)


def process_file(input_file: Path, output_dir: Path, source_name: str) -> List[Path]:
    """
    Process a single audio file: clean, segment, and export.
    """
    print(f"Processing: {input_file.name}")

    # Step 1: Extract vocals and clean
    cleaned_file = output_dir / source_name / f"cleaned_{input_file.stem}.mp3"
    try:
        extract_vocals_only(input_file, cleaned_file)
    except subprocess.CalledProcessError as e:
        print(f"  ERROR cleaning {input_file.name}: {e}")
        return []

    # Step 2: Detect speech segments (removes long silences/music-only parts)
    segments = detect_speech_segments(cleaned_file, min_silence_len=2.0, silence_thresh="-35dB")

    if not segments:
        print(f"  WARNING: No speech detected in {input_file.name}")
        return []

    # Step 3: Extract speech segments as separate clips
    output_clips = []
    for i, (start, end) in enumerate(segments):
        duration = end - start
        if duration < 3.0:  # Skip very short segments
            continue
        if duration > 60.0:  # Cap at 60 seconds per clip
            duration = 60.0
            end = start + 60.0

        clip_file = output_dir / source_name / f"clip_{input_file.stem}_{i:03d}.mp3"

        cmd = [
            "ffmpeg",
            "-i", str(cleaned_file),
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",
            str(clip_file)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            output_clips.append(clip_file)
        except subprocess.CalledProcessError:
            continue

    print(f"  Extracted {len(output_clips)} speech clips")
    return output_clips


def main():
    parser = argparse.ArgumentParser(description="Clean voice samples for ElevenLabs")
    parser.add_argument("--source", type=str, help="Specific source directory to process (e.g. 'hermes', 'little_jacob')")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files per source (0 = no limit)")
    args = parser.parse_args()

    # Find all source directories
    source_dirs = [d for d in VOICE_SAMPLES_DIR.iterdir() if d.is_dir()]

    if args.source:
        source_dirs = [d for d in source_dirs if d.name == args.source]

    if not source_dirs:
        print(f"No source directories found in {VOICE_SAMPLES_DIR}")
        return 1

    # Process each source
    total_clips = 0
    stats = {}

    for source_dir in sorted(source_dirs):
        source_name = source_dir.name
        mp3_files = list(source_dir.glob("*.mp3"))

        if args.limit and args.limit > 0:
            mp3_files = mp3_files[:args.limit]

        if not mp3_files:
            continue

        if args.dry_run:
            print(f"\n{source_name}: {len(mp3_files)} files")
            for f in mp3_files[:5]:
                print(f"  - {f.name}")
            if len(mp3_files) > 5:
                print(f"  ... and {len(mp3_files) - 5} more")
            continue

        print(f"\n{'='*60}")
        print(f"Processing {source_name}: {len(mp3_files)} files")
        print(f"{'='*60}")

        clips_created = 0
        for mp3_file in mp3_files:
            clips = process_file(mp3_file, CLEANED_DIR, source_name)
            clips_created += len(clips)

        stats[source_name] = clips_created
        total_clips += clips_created

    if args.dry_run:
        print(f"\nWould process {len(source_dirs)} sources")
        return 0

    # Summary
    print(f"\n{'='*60}")
    print("CLEANING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total clips created: {total_clips}")
    print(f"\nBreakdown by source:")
    for source, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} clips")

    print(f"\nCleaned files saved to: {CLEANED_DIR}")
    print(f"\nNext step: Select best clips and upload to ElevenLabs PVC")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
