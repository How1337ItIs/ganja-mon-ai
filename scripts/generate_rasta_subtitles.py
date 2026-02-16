#!/usr/bin/env python3
"""
Generate animated ASS subtitles — each word appears as spoken.

Rasta colors (red/gold/green) cycle per word. Words bounce in with glow.
Designed for maximum visual impact and attention-grabbing.

Usage:
    python3 scripts/generate_rasta_subtitles.py \
        --timing output/hackathon_narration_2min.json \
        --output output/hackathon_subtitles.ass
"""

import argparse
import json
import re
from pathlib import Path

# Rasta colors in ASS BGR: &HBBGGRR&
COLORS = [
    "&H0000FF&",   # red
    "&H00D4FF&",   # gold
    "&H00FF00&",   # green
]

ASS_HEADER = r"""[Script Info]
Title: GanjaMon Hackathon Demo
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,Impact,72,&H00FFFFFF,&H000000FF,&H00000000,&HCC000000,-1,0,0,0,100,100,2,0,1,4,2,2,40,40,50,1
Style: WordGlow,Impact,72,&H00FFFFFF,&H000000FF,&H2200AA00,&HCC000000,-1,0,0,0,100,100,2,0,4,8,0,2,40,40,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def clean_word(word: str) -> str:
    return re.sub(r'\[.*?\]', '', word).strip()


def generate_ass(words: list[dict], output_path: Path, words_per_line: int = 6):
    lines = [ASS_HEADER.strip()]
    color_idx = 0

    # Group words into display chunks for positioning
    i = 0
    while i < len(words):
        chunk = []
        for j in range(i, min(i + words_per_line, len(words))):
            cleaned = clean_word(words[j]["word"])
            if cleaned:
                chunk.append({**words[j], "display": cleaned})
        if not chunk:
            i += words_per_line
            continue

        line_start = chunk[0]["start"]
        line_end = chunk[-1]["end"] + 0.5

        # Build the full line text for positioning reference
        full_text = " ".join(w["display"] for w in chunk)

        # Each word appears individually when spoken, building up the line
        for wi, w in enumerate(chunk):
            word_start = w["start"]
            word_end = line_end  # word stays visible until line ends
            color = COLORS[color_idx % len(COLORS)]
            color_idx += 1

            # Build text: dim previous words + bright current word
            parts = []
            for pi in range(len(chunk)):
                wd = chunk[pi]["display"]
                if pi < wi:
                    # Already appeared — show in its assigned color, slightly faded
                    prev_color = COLORS[(color_idx - (wi - pi) - 1) % len(COLORS)]
                    parts.append(f"{{\\1c{prev_color}\\alpha&H44&}}{wd}")
                elif pi == wi:
                    # Current word — bright, bounce in
                    parts.append(
                        f"{{\\1c{color}\\alpha&H00&"
                        f"\\t(0,150,\\fscx115\\fscy115)"
                        f"\\t(150,300,\\fscx100\\fscy100)}}{wd}"
                    )
                else:
                    # Not yet appeared — invisible
                    parts.append(f"{{\\alpha&HFF&}}{wd}")

            text = " ".join(parts)

            start_str = format_time(word_start)
            end_str = format_time(word_end)

            # Glow layer behind current word
            glow_text_parts = []
            for pi in range(len(chunk)):
                wd = chunk[pi]["display"]
                if pi == wi:
                    glow_text_parts.append(
                        f"{{\\1c{color}\\3c{color}\\blur6\\bord8\\alpha&H66&"
                        f"\\t(0,200,\\alpha&HAA&)}}{wd}"
                    )
                else:
                    glow_text_parts.append(f"{{\\alpha&HFF&}}{wd}")

            glow_text = " ".join(glow_text_parts)
            lines.append(
                f"Dialogue: 0,{start_str},{end_str},WordGlow,,0,0,0,,{glow_text}"
            )

            # Main text layer
            lines.append(
                f"Dialogue: 1,{start_str},{end_str},Word,,0,0,0,,"
                f"{{\\3c&H000000&\\bord4\\shad2}}{text}"
            )

        # Final hold: show complete line brightly
        hold_start = format_time(chunk[-1]["end"])
        hold_end = format_time(line_end)
        final_parts = []
        for pi, w in enumerate(chunk):
            c = COLORS[(color_idx - len(chunk) + pi) % len(COLORS)]
            final_parts.append(f"{{\\1c{c}\\alpha&H00&}}{w['display']}")
        final_text = " ".join(final_parts)
        lines.append(
            f"Dialogue: 1,{hold_start},{hold_end},Word,,0,0,0,,"
            f"{{\\3c&H000000&\\bord4\\shad2\\fad(0,300)}}{final_text}"
        )

        i += words_per_line

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ASS subtitles: {output_path}")
    print(f"Dialogue lines: {len(lines) - ASS_HEADER.strip().count(chr(10)) - 1}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timing", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/hackathon_subtitles.ass"))
    parser.add_argument("--words-per-line", type=int, default=6)
    args = parser.parse_args()

    data = json.loads(args.timing.read_text())
    words = data["words"]
    print(f"Loaded {len(words)} words, duration {data['duration']:.1f}s")

    generate_ass(words, args.output, args.words_per_line)


if __name__ == "__main__":
    main()
