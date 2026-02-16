#!/usr/bin/env python3
"""
A/B Test: xAI Native vs OpenRouter for Grok latency comparison
"""
import asyncio
import time
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TEST_SENTENCES = [
    "Hey everyone, welcome to the stream today",
    "The cannabis plants are looking absolutely amazing right now",
    "Let me explain what's happening with the Monad blockchain integration",
    "I really appreciate everyone tuning in, this is going to be fun",
    "What do you think about the new setup, is the audio quality good?"
]

SYSTEM_PROMPT = """Transform to Jamaican Patois with emotion tags.
Add [chuckles], [laughs], etc. Keep meaning identical."""

async def test_xai_native(text: str) -> tuple[str, float, float]:
    """Test xAI native API"""
    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1"
    )

    start = time.perf_counter()
    first_chunk_time = None
    chunks = []

    response = client.chat.completions.create(
        model="grok-4-1-fast",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.9,
        max_tokens=200,
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()
            chunks.append(chunk.choices[0].delta.content)

    total_time = (time.perf_counter() - start) * 1000
    ttft = (first_chunk_time - start) * 1000 if first_chunk_time else total_time
    result = ''.join(chunks)

    return result, ttft, total_time

async def test_openrouter(text: str) -> tuple[str, float, float]:
    """Test OpenRouter"""
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    start = time.perf_counter()
    first_chunk_time = None
    chunks = []

    response = client.chat.completions.create(
        model="x-ai/grok-2-1212",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.9,
        max_tokens=200,
        stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter()
            chunks.append(chunk.choices[0].delta.content)

    total_time = (time.perf_counter() - start) * 1000
    ttft = (first_chunk_time - start) * 1000 if first_chunk_time else total_time
    result = ''.join(chunks)

    return result, ttft, total_time

async def run_ab_test():
    """Run A/B comparison"""
    print("=" * 70)
    print("A/B TEST: xAI Native vs OpenRouter")
    print("=" * 70)
    print()

    xai_ttfts = []
    xai_totals = []
    or_ttfts = []
    or_totals = []

    for i, sentence in enumerate(TEST_SENTENCES, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: \"{sentence}\"")
        print(f"{'='*70}")

        # Test xAI Native
        print("\n[xAI NATIVE]")
        result, ttft, total = await test_xai_native(sentence)
        xai_ttfts.append(ttft)
        xai_totals.append(total)
        print(f"  TTFT (Time to First Token): {ttft:.0f}ms")
        print(f"  Total Time: {total:.0f}ms")
        print(f"  Output: {result[:80]}...")

        await asyncio.sleep(1)  # Brief pause between tests

        # Test OpenRouter
        print("\n[OPENROUTER]")
        result, ttft, total = await test_openrouter(sentence)
        or_ttfts.append(ttft)
        or_totals.append(total)
        print(f"  TTFT (Time to First Token): {ttft:.0f}ms")
        print(f"  Total Time: {total:.0f}ms")
        print(f"  Output: {result[:80]}...")

        await asyncio.sleep(1)  # Brief pause

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    avg_xai_ttft = sum(xai_ttfts) / len(xai_ttfts)
    avg_xai_total = sum(xai_totals) / len(xai_totals)
    avg_or_ttft = sum(or_ttfts) / len(or_ttfts)
    avg_or_total = sum(or_totals) / len(or_totals)

    print(f"\nxAI Native Average:")
    print(f"  TTFT: {avg_xai_ttft:.0f}ms")
    print(f"  Total: {avg_xai_total:.0f}ms")

    print(f"\nOpenRouter Average:")
    print(f"  TTFT: {avg_or_ttft:.0f}ms")
    print(f"  Total: {avg_or_total:.0f}ms")

    print(f"\nDifference:")
    print(f"  TTFT: {avg_or_ttft - avg_xai_ttft:+.0f}ms ({'+' if avg_or_ttft > avg_xai_ttft else ''}{((avg_or_ttft / avg_xai_ttft - 1) * 100):.1f}%)")
    print(f"  Total: {avg_or_total - avg_xai_total:+.0f}ms ({'+' if avg_or_total > avg_xai_total else ''}{((avg_or_total / avg_xai_total - 1) * 100):.1f}%)")

    winner = "xAI Native" if avg_xai_total < avg_or_total else "OpenRouter"
    print(f"\n🏆 WINNER: {winner}")

if __name__ == "__main__":
    asyncio.run(run_ab_test())
