#!/usr/bin/env python3
"""
Generate animated Rasta subtitles for hackathon demo video.
Style: Rasta Regal — each word is one solid rasta color (R→G→Y cycling),
big bounce when it appears, thick outline, catches attention per word.
"""

import json

with open("/mnt/c/Users/natha/sol-cannabis/output/voiceover/word_timestamps.json") as f:
    words = json.load(f)

# Rasta colors in ASS BGR — bright, vivid, regal
COLORS = [
    "0000FF",  # Red    (pure, bold)
    "00CC00",  # Green  (rasta green, vivid)
    "00CCFF",  # Gold   (bright gold/yellow)
]

# Emphasis words get white with glow
EMPHASIS_WORDS = {
    "GanjaMon", "GREW", "ONLY", "EVERYTHING.", "OWN", "NOW", "PAY",
    "ART.", "HEAL", "cyaan", "OOM", "x402", "JSON", "USDC", "Monad,",
    "Monad", "Mon.", "Mon", "Ralph", "OpenClaw", "8004", "292",
    "micropayments,", "blockchain.", "Runtz.", "real-time.",
}

CHAR_WIDTHS = {
    ' ': 18, '.': 16, ',': 16, '!': 20, '?': 30, "'": 14, '"': 22,
    '-': 22, ':': 16, ';': 16, '/': 22, '(': 18, ')': 18,
}
UPPER_WIDTH = 42
LOWER_WIDTH = 34
DIGIT_WIDTH = 36
DEFAULT_WIDTH = 36
SPACE_BETWEEN_WORDS = 20
LINE_Y = 1080 - 85


def char_width(ch):
    if ch in CHAR_WIDTHS:
        return CHAR_WIDTHS[ch]
    if ch.isupper():
        return UPPER_WIDTH
    if ch.isdigit():
        return DIGIT_WIDTH
    if ch.islower():
        return LOWER_WIDTH
    return DEFAULT_WIDTH


def word_width(word):
    return sum(char_width(ch) for ch in word)


def fmt_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def group_words(words, max_width=1400, max_words=6):
    groups = []
    current = []
    current_width = 0
    for w in words:
        ww = word_width(w["word"]) + SPACE_BETWEEN_WORDS
        if current and (current_width + ww > max_width or len(current) >= max_words):
            groups.append(current)
            current = [w]
            current_width = ww
        else:
            current.append(w)
            current_width += ww
    if current:
        groups.append(current)
    return groups


ASS_HEADER = r"""[Script Info]
Title: GanjaMon Rasta Subtitles
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Rasta,Impact,56,&H0000FFFF,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,2,2,120,120,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

groups = group_words(words)
events = []
word_color_idx = 0

for gi, group in enumerate(groups):
    group_end = group[-1]["end"] + 0.5
    if gi < len(groups) - 1:
        group_end = min(group_end, groups[gi + 1][0]["start"] - 0.03)

    total_width = sum(word_width(w["word"]) for w in group) + SPACE_BETWEEN_WORDS * (len(group) - 1)
    line_start_x = (1920 - total_width) // 2
    cursor_x = line_start_x

    for wi, w in enumerate(group):
        wtext = w["word"]
        ww = word_width(wtext)
        center_x = cursor_x + ww // 2
        center_y = LINE_Y

        # Pick color: emphasis words get bright white, others cycle R→G→Y
        is_emphasis = wtext in EMPHASIS_WORDS
        if is_emphasis:
            color = "FFFFFF"  # Bright white for emphasis
            outline_color = "0000AA"  # Dark red outline for contrast
            shadow_color = "000066"
        else:
            color = COLORS[word_color_idx % len(COLORS)]
            outline_color = "000000"  # Black outline
            shadow_color = "000000"
            word_color_idx += 1

        # Big bounce: scale 145% → 100% over 200ms, with overshoot
        # Slight rotation wobble for dynamism
        tags = (
            r"{\an5"
            + f"\\pos({center_x},{center_y})"
            + f"\\1c&H{color}&"
            + f"\\3c&H{outline_color}&"
            + f"\\4c&H{shadow_color}&"
            + r"\fscx145\fscy145"
            + r"\t(0,80,\fscx103\fscy103)"
            + r"\t(80,200,\fscx100\fscy100)"
            + r"\fad(20,180)}"
        )

        events.append(
            f"Dialogue: 0,{fmt_time(w['start'])},{fmt_time(group_end)},Rasta,,0,0,0,,{tags}{wtext}"
        )

        cursor_x += ww + SPACE_BETWEEN_WORDS

output_path = "/mnt/c/Users/natha/sol-cannabis/output/rasta_subs.ass"
with open(output_path, "w") as f:
    f.write(ASS_HEADER)
    for e in events:
        f.write(e + "\n")

print(f"Generated {len(events)} word events from {len(groups)} groups")
print(f"Output: {output_path}")
