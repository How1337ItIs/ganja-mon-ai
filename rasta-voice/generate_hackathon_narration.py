#!/usr/bin/env python3
"""
Generate hackathon narration WAV + word-level timing JSON for subtitle sync.

Uses ElevenLabs convert_with_timestamps to get character-level alignment,
then derives word timestamps for ASS subtitle generation.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import wave
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from elevenlabs import ElevenLabs


DEFAULT_VOICE_ID = "dhwafD61uVd8h85wAZSE"
DEFAULT_MODEL_ID = "eleven_v3"
DEFAULT_SAMPLE_RATE = 24000


def parse_args() -> argparse.Namespace:
    root = Path(__file__).parent
    parser = argparse.ArgumentParser(
        description="Generate hackathon narration WAV + timing from text lines."
    )
    parser.add_argument(
        "--input", type=Path,
        default=root / "hackathon_2min_narration.txt",
    )
    parser.add_argument(
        "--output", type=Path,
        default=root.parent / "output" / "hackathon_narration_2min.wav",
    )
    parser.add_argument("--pause-ms", type=int, default=300)
    parser.add_argument(
        "--voice-id",
        default=os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID),
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--stability", type=float, default=0.5)
    parser.add_argument("--style", type=float, default=1.0)
    parser.add_argument("--similarity-boost", type=float, default=0.5)
    return parser.parse_args()


def load_lines(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    lines: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text:
            continue
        if text.startswith("#"):
            continue
        text = re.sub(r"^\[[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}\]\s*", "", text)
        if text:
            lines.append(text)
    if not lines:
        raise ValueError(f"No narration lines found in {path}")
    return lines


def chars_to_words(alignment: dict, time_offset: float = 0.0) -> list[dict]:
    """Convert character-level alignment to word-level timestamps."""
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])

    words = []
    current_word = ""
    word_start = None

    for i, ch in enumerate(chars):
        if ch == " " or ch == "\n":
            if current_word:
                words.append({
                    "word": current_word,
                    "start": word_start + time_offset,
                    "end": ends[i - 1] + time_offset,
                })
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = starts[i]
            current_word += ch

    # Last word
    if current_word and word_start is not None:
        words.append({
            "word": current_word,
            "start": word_start + time_offset,
            "end": ends[len(chars) - 1] + time_offset,
        })

    return words


def synthesize_with_timestamps(
    client: ElevenLabs,
    text: str,
    *,
    voice_id: str,
    model_id: str,
    stability: float,
    style: float,
    similarity_boost: float,
) -> tuple[bytes, dict]:
    """Returns (pcm_bytes, alignment_dict)."""
    resp = client.text_to_speech.convert_with_timestamps(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format="pcm_24000",
        voice_settings={
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": True,
        },
    )
    audio_bytes = base64.b64decode(resp.audio_base_64)
    alignment = {}
    if resp.alignment:
        alignment = {
            "characters": list(resp.alignment.characters),
            "character_start_times_seconds": list(resp.alignment.character_start_times_seconds),
            "character_end_times_seconds": list(resp.alignment.character_end_times_seconds),
        }
    return audio_bytes, alignment


def write_wav(path: Path, frames: bytes, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames)


def main() -> None:
    args = parse_args()

    load_dotenv(Path(__file__).parent / ".env")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ELEVENLABS_API_KEY in rasta-voice/.env")

    lines = load_lines(args.input)
    client = ElevenLabs(api_key=api_key)

    # Join all lines into ONE text block for a single natural-flowing TTS call
    full_text = "\n\n".join(lines)
    print(f"Loaded {len(lines)} paragraphs, {len(full_text)} chars total")
    print(f"Synthesizing entire narration as ONE call (stability={args.stability})...")

    audio, alignment = synthesize_with_timestamps(
        client, full_text,
        voice_id=args.voice_id,
        model_id=args.model_id,
        stability=args.stability,
        style=args.style,
        similarity_boost=args.similarity_boost,
    )

    all_words = chars_to_words(alignment)
    duration_seconds = len(audio) / 2 / DEFAULT_SAMPLE_RATE

    write_wav(args.output, audio, DEFAULT_SAMPLE_RATE)

    # Save word timing JSON alongside WAV
    timing_path = args.output.with_suffix(".json")
    with open(timing_path, "w") as f:
        json.dump({"words": all_words, "duration": duration_seconds}, f, indent=2)
    print(f"Timing: {timing_path} ({len(all_words)} words)")

    print(f"\nOutput: {args.output}")
    print(f"Duration: {duration_seconds:.2f}s ({duration_seconds / 60:.2f}m)")
    print(f"Paragraphs: {len(lines)}")
    print(f"Voice: {args.voice_id}")
    print(f"Model: {args.model_id}")
    print(f"Settings: stability={args.stability}, similarity_boost={args.similarity_boost}, style={args.style}")


if __name__ == "__main__":
    main()
