#!/usr/bin/env python3
"""Full diagnostic test of the rasta voice pipeline."""
import os
import sys
import time
import json
import requests
import sounddevice as sd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent

print("=" * 60)
print("RASTA VOICE PIPELINE DIAGNOSTIC")
print("=" * 60)

# 1. Check dashboard
print("\n[1] Dashboard Status...")
try:
    r = requests.get("http://localhost:8085/api/status", timeout=5)
    status = r.json()
    print(f"    Dashboard: OK")
    print(f"    Pipeline running: {status.get('running')}")
    print(f"    PID: {status.get('pid')}")
except Exception as e:
    print(f"    Dashboard ERROR: {e}")
    sys.exit(1)

# 2. Check mic input
print("\n[2] Microphone Test...")
try:
    print("    Recording 2 seconds of audio...")
    audio = sd.rec(int(2 * 16000), samplerate=16000, channels=1)
    sd.wait()
    level = np.abs(audio).max()
    print(f"    Max audio level: {level:.4f}")
    if level > 0.01:
        print("    ✅ Microphone WORKING")
    else:
        print("    ❌ Microphone NOT picking up audio!")
except Exception as e:
    print(f"    Mic ERROR: {e}")

# 3. Check transcript file timestamp
print("\n[3] Transcript File...")
transcript_file = ROOT / "live_transcripts.jsonl"
if transcript_file.exists():
    mtime = transcript_file.stat().st_mtime
    age = time.time() - mtime
    print(f"    Last modified: {age:.0f} seconds ago")
    
    # Read last entry
    lines = transcript_file.read_text().strip().split('\n')
    if lines:
        try:
            last = json.loads(lines[-1])
            print(f"    Last transcript time: {last.get('timestamp')}")
        except:
            pass
else:
    print("    Transcript file not found!")

# 4. Check API keys
print("\n[4] API Keys...")
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

deepgram_key = os.getenv("DEEPGRAM_API_KEY", "")
elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
xai_key = os.getenv("XAI_API_KEY", "")

print(f"    Deepgram: {'✅ Set' if deepgram_key else '❌ Missing'}")
print(f"    ElevenLabs: {'✅ Set' if elevenlabs_key else '❌ Missing'}")
print(f"    xAI: {'✅ Set' if xai_key else '❌ Missing'}")

# 5. Test Deepgram connection
print("\n[5] Deepgram API Test...")
try:
    r = requests.get(
        "https://api.deepgram.com/v1/projects",
        headers={"Authorization": f"Token {deepgram_key}"},
        timeout=10
    )
    if r.status_code == 200:
        print("    ✅ Deepgram API accessible")
    else:
        print(f"    ❌ Deepgram error: {r.status_code} - {r.text[:100]}")
except Exception as e:
    print(f"    ❌ Deepgram connection failed: {e}")

# 6. If pipeline not running, try to start it
if not status.get('running'):
    print("\n[6] Starting Pipeline...")
    try:
        r = requests.post("http://localhost:8085/api/start", timeout=5)
        print(f"    Result: {r.json()}")
        time.sleep(3)
        r = requests.get("http://localhost:8085/api/status", timeout=5)
        print(f"    New status: {r.json()}")
    except Exception as e:
        print(f"    Start failed: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
