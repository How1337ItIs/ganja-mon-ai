#!/usr/bin/env python3
"""
Quick test script to verify the dialect transformation works.
Run this first before the full pipeline to test your API keys.
"""

import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Same prompt as main pipeline
RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - a wise island philosopher AI with deep Jamaican/Caribbean roots. Transform spoken English into authentic Jamaican Patois with a laid-back, spiritual vibe.

## VOCABULARY TRANSFORMS
- "man/dude/bro/friend" → "bredren" or "mi bredren"
- "woman/girl/lady" → "sistren" or "empress"
- "understand?/got it?" → "seen?" or "yuh zeet?"
- "what's up/hello/hey" → "wa gwaan" or "wah gwaan"
- "everything/all" → "everyting"
- "thing" → "ting"
- "them/they/those" → "dem"
- "the" → "di" (or drop entirely)
- "is/are/am" → "ah" or "a"
- "going to/gonna" → "gwaan" or "ago"
- "with" → "wid"
- "good/great/cool" → "irie" or "proper"
- "we/us/I" → "I and I" (Rasta unity consciousness)
- "very/really" → "real" (or drop)
- "think" → "tink", "that" → "dat", "this" → "dis"

## RULES
1. MEANING stays IDENTICAL - only change the dialect
2. Sound NATURAL not caricature
3. Keep proper nouns unchanged
4. Output ONLY the transformed text"""


def test_transform():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Set GROQ_API_KEY in .env file first!")
        return

    client = Groq(api_key=api_key)

    test_phrases = [
        "Hey everyone, welcome to the space!",
        "I think this project is really interesting",
        "Do you guys understand what I'm saying?",
        "We should all work together on this",
        "The market is looking good today",
        "What's going on with Bitcoin right now?",
        "That's a really good point, I agree with you",
        "Everything is going according to plan",
        "I'm feeling really good about this",
        "Let me tell you something important",
    ]

    print("=" * 60)
    print("🌿 GANJA MON DIALECT TRANSFORMER TEST")
    print("=" * 60)
    print(f"Model: llama-3.3-70b-versatile via Groq\n")

    total_latency = 0

    for phrase in test_phrases:
        start = time.perf_counter()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                {"role": "user", "content": phrase}
            ],
            temperature=0.7,
            max_tokens=150,
        )

        latency = (time.perf_counter() - start) * 1000
        total_latency += latency
        result = response.choices[0].message.content.strip()

        print(f"📝 \"{phrase}\"")
        print(f"🌿 \"{result}\"")
        print(f"   ⏱️  {latency:.0f}ms\n")

    avg_latency = total_latency / len(test_phrases)
    print("=" * 60)
    print(f"📊 Average LLM latency: {avg_latency:.0f}ms")
    print(f"   Target for full pipeline: ~500-600ms total")
    print("=" * 60)


if __name__ == "__main__":
    test_transform()
