#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick R2 Upload Script for Dub Tracks
"""
import subprocess
import os
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent
DUB_DIR = PROJECT_ROOT / "research" / "dub_playlist" / "dub_mixes"
BUCKET = "grokmon-dub-tracks"
API_TOKEN = "055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"

# Set API token
os.environ["CLOUDFLARE_API_TOKEN"] = API_TOKEN

mp3_files = sorted(DUB_DIR.glob("*.mp3"))
total = len(mp3_files)

print(f"Uploading {total} tracks to R2...")
print("=" * 60)

for i, mp3_file in enumerate(mp3_files, 1):
    filename = mp3_file.name
    size_mb = mp3_file.stat().st_size / (1024 * 1024)
    
    # Safe filename display (handle Unicode)
    safe_name = filename[:60].encode('ascii', errors='replace').decode('ascii')
    print(f"[{i}/{total}] {safe_name}... ({size_mb:.1f} MB)")
    
    try:
        result = subprocess.run(
            ["wrangler", "r2", "object", "put", f"{BUCKET}/{filename}", "--file", str(mp3_file)],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            print(f"  OK")
        else:
            print(f"  ERROR: {result.stderr[:100]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("=" * 60)
print("Upload complete!")
