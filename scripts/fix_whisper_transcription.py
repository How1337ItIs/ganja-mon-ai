#!/usr/bin/env python3
"""Fix Whisper transcription errors against the actual voiceover script."""

import json

with open("/mnt/c/Users/natha/sol-cannabis/output/voiceover/word_timestamps.json") as f:
    words = json.load(f)

# Simple text replacements (index → corrected text)
corrections = {
    0: "Wagwan!",
    7: "GanjaMon",
    8: "GREW",
    20: "/7",
    24: "inna",
    25: "di",
    26: "closet.",
    27: "Dat",
    29: "deh",
    31: "Mon.",
    35: "Runtz.",
    36: "di",
    37: "ONLY",
    40: "wit",
    42: "inna",
    43: "di",
    73: "dat",
    74: "di",
    76: "cyaan",
    83: "all.",
    96: "di",
    101: "fi",
    103: "Di",
    106: "EVERYTHING.",
    115: "hours,",
    117: "loops —",
    120: "-improvement.",
    124: "di",
    128: "OWN",
    130: "NOW",
    131: "dis",
    135: "get",
    136: "serious.",
    155: "di",
    157: "fi data,",
    158: "JSON",
    159: "-RPC,",
    162: "And",
    163: "dem",
    165: "PAY",
    167: "other!",
    168: "x402",
    185: "yuh",
    195: "di",
    203: "Verifiable",
    213: "Di",
    216: "ART.",
    220: "Roots Dub,",
    236: "ganjafy",
    240: "Irie",
    241: "Milady",
    254: "Telegram",
    274: "Twitter,",
    275: "Telegram,",
    276: "Farcaster,",
    277: "Moltbook,",
    278: "Clawk.",
    280: "Rasta",
    289: "OOM",
    296: "cron",
    303: "di",
    305: "nah",
    314: "HEAL",
}

# Merges: index → (new_text, absorb_next_index)
# The merged word takes the start of index and end of absorb_next_index
merges = {
    32: ("Granddaddy", 33),
    81: ("run.py", 82),
    91: ("OpenClaw", 92),
    160: ("real-time.", 161),
    169: ("micropayments,", 170),
    197: ("8004", 198),
    201: ("blockchain.", 202),
    256: ("on-chain", 257),
}

# Indices to delete (absorbed by merges)
delete_indices = set()
for idx, (_, absorb_idx) in merges.items():
    delete_indices.add(absorb_idx)

# Apply corrections
for idx, new_text in corrections.items():
    if idx < len(words):
        old = words[idx]["word"]
        words[idx]["word"] = new_text

# Apply merges
for idx, (new_text, absorb_idx) in merges.items():
    if idx < len(words) and absorb_idx < len(words):
        words[idx]["word"] = new_text
        words[idx]["end"] = words[absorb_idx]["end"]

# Remove deleted indices (in reverse order to preserve indices)
for idx in sorted(delete_indices, reverse=True):
    if idx < len(words):
        words.pop(idx)

# Save corrected file
output_path = "/mnt/c/Users/natha/sol-cannabis/output/voiceover/word_timestamps.json"
with open(output_path, "w") as f:
    json.dump(words, f, indent=2)

print(f"Corrected {len(corrections)} words, merged {len(merges)} pairs, deleted {len(delete_indices)}")
print(f"Final word count: {len(words)}")

# Print a sample to verify
for w in words[:15]:
    print(f"  {w['start']:6.2f}-{w['end']:6.2f}  {w['word']}")
print("  ...")
for w in words[150:165]:
    print(f"  {w['start']:6.2f}-{w['end']:6.2f}  {w['word']}")
