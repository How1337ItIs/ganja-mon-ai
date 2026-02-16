#!/usr/bin/env python3
"""
Test the full STT → LLM pipeline without TTS.
Uses your microphone and prints transformed text in real-time.
Good for testing before you set up Cartesia.
"""

import os
import asyncio
import time
from dotenv import load_dotenv

import assemblyai as aai
from groq import Groq
import sounddevice as sd
import numpy as np

load_dotenv()

RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - transform English to Jamaican Patois.

Quick rules:
- "what's up/hello" → "wa gwaan"
- "understand?" → "seen?"
- "good/great" → "irie"
- "thing" → "ting", "the" → "di", "with" → "wid"
- "I/we" → "I and I"
- Add "mon", "seen?", "y'know" naturally
- Keep meaning identical, sound natural not caricature
- Output ONLY transformed text"""


class QuickPipelineTest:
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.running = False
        self.latencies = []

    def transform(self, text: str) -> tuple[str, float]:
        start = time.perf_counter()
        response = self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=150,
        )
        latency = (time.perf_counter() - start) * 1000
        return response.choices[0].message.content.strip(), latency

    def on_transcript(self, transcript: aai.RealtimeTranscript):
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            # Final transcript - transform it
            rasta, llm_ms = self.transform(transcript.text)
            self.latencies.append(llm_ms)

            print(f"\n📝 You: \"{transcript.text}\"")
            print(f"🌿 Mon: \"{rasta}\"")
            print(f"   ⏱️  LLM: {llm_ms:.0f}ms | Avg: {sum(self.latencies)/len(self.latencies):.0f}ms")
        else:
            # Partial transcript - show typing indicator
            print(f"\r🎤 {transcript.text}...", end="", flush=True)

    def on_error(self, error: aai.RealtimeError):
        print(f"\n❌ Error: {error}")

    async def run(self):
        print("=" * 60)
        print("🎤 RASTA VOICE PIPELINE TEST (no TTS)")
        print("=" * 60)
        print("Speak into your microphone. Text will be transformed.")
        print("This tests STT + LLM without audio output.")
        print("Press Ctrl+C to stop.\n")

        # Configure AssemblyAI
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            print("❌ Set ASSEMBLYAI_API_KEY in .env")
            return

        aai.settings.api_key = api_key

        transcriber = aai.RealtimeTranscriber(
            sample_rate=16000,
            on_data=self.on_transcript,
            on_error=self.on_error,
            encoding=aai.AudioEncoding.pcm_s16le,
        )

        transcriber.connect()
        print("✅ Connected to AssemblyAI\n")

        self.running = True

        def mic_callback(indata, frames, time_info, status):
            if self.running:
                audio_int16 = (indata * 32767).astype(np.int16)
                transcriber.stream(audio_int16.tobytes())

        try:
            with sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype=np.float32,
                blocksize=1024,
                callback=mic_callback
            ):
                print("🎙️  Microphone active - speak now!\n")
                while self.running:
                    await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping...")
        finally:
            self.running = False
            transcriber.close()

        if self.latencies:
            print(f"\n📊 Final Stats:")
            print(f"   Avg LLM latency: {sum(self.latencies)/len(self.latencies):.0f}ms")
            print(f"   + ~300ms STT = ~{sum(self.latencies)/len(self.latencies) + 300:.0f}ms without TTS")
            print(f"   + ~50ms TTS ≈ ~{sum(self.latencies)/len(self.latencies) + 350:.0f}ms total (target: 500-600ms)")


if __name__ == "__main__":
    asyncio.run(QuickPipelineTest().run())
