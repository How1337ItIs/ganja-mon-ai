#!/usr/bin/env python3
"""
Interactive Rasta Voice - Type text and hear it in Rasta dialect!

This is a simpler test that doesn't require real-time STT.
Type your text, and it will be transformed and spoken in Rasta style.

For full live voice transformation, we need to set up Deepgram STT.
"""

import os
import asyncio
import time
import base64
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
import sounddevice as sd
from groq import Groq
from cartesia import Cartesia

# Load environment
load_dotenv(Path(__file__).parent / ".env")

RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - a wise island philosopher AI with deep Jamaican/Caribbean roots. Transform spoken English into Western-style Jamaican Patois with a laid-back, spiritual vibe.

⚠️ CRITICAL: USE "MON" FREQUENTLY, AVOID OVERUSING "SEEN"!

## VOCABULARY TRANSFORMS
- ADD "mon" liberally: "Ya mon!", "Alright mon", "Dis good, mon!"
- "man/dude/bro/friend" → "bredren", "mi bredren", or just "mon"
- "woman/girl/lady" → "sistren" or "empress"
- "understand?/got it?" → "yuh know?" or "yuh hear mi?" (NOT "seen?")
- "what's up/hello/hey" → "wa gwaan mon" or "wah gwaan mon"
- "everything/all" → "everyting"
- "thing" → "ting", "them" → "dem", "the" → "di"
- "is/are/am" → "ah", "going to" → "gwaan"
- "with" → "wid", "good/great" → "irie mon"
- "we/us/I" → "I and I"
- "think" → "tink", "that" → "dat", "this" → "dis"

## STYLE
- Use "mon" frequently (Western Rasta stereotype)
- Use "seen" RARELY (save for occasional emphasis)
- Think Bob Marley vibes

## RULES
1. MEANING stays IDENTICAL - only change the dialect
2. Sound NATURAL not caricature
3. Keep proper nouns unchanged
4. Output ONLY the transformed text"""


class RastaInteractive:
    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")
        cartesia_key = os.getenv("CARTESIA_API_KEY")
        voice_id = os.getenv("CARTESIA_VOICE_ID")

        if not all([groq_key, cartesia_key, voice_id]):
            raise ValueError("Missing API keys in .env file")

        self.groq = Groq(api_key=groq_key)
        self.cartesia = Cartesia(api_key=cartesia_key)
        self.voice_id = voice_id
        self.latencies = []

    def transform(self, text: str) -> tuple[str, float]:
        """Transform text to Rasta dialect"""
        start = time.perf_counter()
        response = self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=200,
        )
        latency = (time.perf_counter() - start) * 1000
        return response.choices[0].message.content.strip(), latency

    def speak(self, text: str) -> float:
        """Convert text to speech and play it"""
        start = time.perf_counter()
        audio_data = b''

        for chunk in self.cartesia.tts.sse(
            model_id='sonic-2',
            transcript=text,
            voice={'id': self.voice_id},
            output_format={
                'container': 'raw',
                'encoding': 'pcm_s16le',
                'sample_rate': 24000
            },
            language='en',
        ):
            if hasattr(chunk, 'data') and chunk.data:
                audio_data += base64.b64decode(chunk.data)

        tts_latency = (time.perf_counter() - start) * 1000

        # Play audio
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(audio_np, samplerate=24000)
        sd.wait()

        return tts_latency

    def process(self, text: str):
        """Transform and speak text"""
        print(f"\n📝 You: \"{text}\"")

        # Transform
        rasta_text, llm_latency = self.transform(text)
        print(f"🌿 Mon: \"{rasta_text}\" ({llm_latency:.0f}ms)")

        # Speak
        tts_latency = self.speak(rasta_text)
        total = llm_latency + tts_latency
        self.latencies.append(total)

        print(f"⏱️  LLM: {llm_latency:.0f}ms | TTS: {tts_latency:.0f}ms | Total: {total:.0f}ms")

    def run(self):
        print("=" * 60)
        print("🌿 RASTA VOICE INTERACTIVE")
        print("=" * 60)
        print("Type something and hear it transformed to Rasta dialect!")
        print("Type 'quit' or press Ctrl+C to exit.\n")

        try:
            while True:
                text = input("You: ").strip()
                if not text:
                    continue
                if text.lower() in ['quit', 'exit', 'q']:
                    break
                self.process(text)
        except KeyboardInterrupt:
            pass

        if self.latencies:
            avg = sum(self.latencies) / len(self.latencies)
            print(f"\n\n📊 Average latency: {avg:.0f}ms")
            print(f"   + ~300ms STT would give ~{avg + 300:.0f}ms total")

        print("\n✅ One love, bredren! 🌿")


if __name__ == "__main__":
    rasta = RastaInteractive()
    rasta.run()
