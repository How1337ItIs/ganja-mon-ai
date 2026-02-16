#!/usr/bin/env python3
"""List available Cartesia voices to find a good Rasta-style voice."""

import os
from dotenv import load_dotenv
from cartesia import Cartesia

load_dotenv()

client = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

print("=" * 60)
print("🎤 AVAILABLE CARTESIA VOICES")
print("=" * 60)

voices = client.voices.list()

# Look for male voices with deeper/relaxed characteristics
for voice in voices:
    name = getattr(voice, "name", "Unknown")
    voice_id = getattr(voice, "id", "")
    desc = getattr(voice, "description", "")
    lang = getattr(voice, "language", "en")

    # Filter for English voices
    if lang and ("en" in lang.lower()):
        print(f"\n🎙️  {name}")
        print(f"   ID: {voice_id}")
        if desc:
            print(f"   {desc[:100]}...")
