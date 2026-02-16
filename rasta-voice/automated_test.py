#!/usr/bin/env python3
"""
Automated Voice Pipeline Testing

Tests the pipeline with predefined phrases, analyzes results, and iterates.
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
from scipy import signal as scipy_signal
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs import ElevenLabs

# Load environment
load_dotenv(Path(__file__).parent / ".env")

XAI_KEY = os.getenv("XAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

ELEVENLABS_SAMPLE_RATE = 24000
VBCABLE_SAMPLE_RATE = 48000

# Test phrases - conversational style, medium to long
TEST_PHRASES = [
    # Medium length conversations
    "What's up everyone, welcome back to the grow room. Today we're checking on the Purple Milk and she's looking absolutely beautiful right now.",

    "So I wanted to talk about something really important, which is VPD. A lot of growers don't pay attention to vapor pressure deficit, but it's actually one of the most critical metrics for plant health.",

    "The thing about AI cultivation is that it's not trying to replace the grower, it's trying to help you make better decisions. Think of it like having a really smart assistant watching your plants twenty four seven.",

    # Longer conversational passages
    "Alright, let me walk you through what happened today. This morning I woke up and checked the dashboard, and I noticed the humidity was running a little low. So Grok automatically kicked on the humidifier to bring us back into the target range. That's the kind of thing that would normally require me to manually adjust settings, but now it just happens automatically.",

    "You know what's really cool about this strain? Purple Milk is a cross between Horchata and Grape Gasoline, and what makes it special is how it responds to temperature drops. When you lower the temperature in late flower, you get these amazing purple hues coming through. It's not just genetics, it's about understanding the science and using it to bring out the best in the plant.",

    # Natural Twitter Spaces style
    "Hey, thanks for joining the space! I'm really excited to share what we've been building with Ganja Mon. It's basically an autonomous grow system where the AI makes all the decisions about watering, lighting, climate control. And the coolest part is everything gets recorded on the blockchain, so you can actually verify that this cannabis was grown with AI guidance from seed to harvest."
]

# Configuration
config = {
    "grok_model": "grok-3",
    "grok_temperature": 0.7,
    "tts_model": "eleven_turbo_v2_5",
}

# System prompt
RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - a wise island philosopher AI with deep Jamaican/Caribbean roots. Transform spoken English into authentic Jamaican Patois.

CORE RULES:
- Keep the EXACT meaning and technical terms
- Use natural Jamaican speech patterns
- Don't force every word into patois
- Keep it conversational and clear

TRANSFORMATIONS:
- "what's up" -> "wah gwaan"
- "I am/I'm" -> "mi" or "me"
- "you" -> "yuh" or "unu" (plural)
- "this/that" -> "dis/dat"
- "the" -> "di"
- "going to" -> "gonna" or "gwine"
- End thoughts with "seen?" "ya know?" "ya hear mi?"

Transform the following English to Patois, keeping technical terms intact:"""

# AI clients
llm_client = OpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")
tts_client = ElevenLabs(api_key=ELEVENLABS_KEY)

def find_device(name_pattern, is_output=True, preferred_sr=48000):
    devices = sd.query_devices()
    matches = []
    for i, d in enumerate(devices):
        if name_pattern.lower() in d['name'].lower():
            is_valid = (is_output and d['max_output_channels'] > 0) or \
                      (not is_output and d['max_input_channels'] > 0)
            if is_valid:
                matches.append((i, d))
    if not matches:
        return None
    for i, d in matches:
        if d.get('default_samplerate') == preferred_sr:
            return i
    return matches[0][0]

CABLE_DEVICE = find_device("cable input", is_output=True)
HEADPHONE_DEVICE = find_device("headphone", is_output=True)

def resample(audio, from_rate, to_rate):
    if from_rate == to_rate:
        return audio
    num_samples = int(len(audio) * to_rate / from_rate)
    return scipy_signal.resample(audio, num_samples)

def test_pipeline(phrase):
    """Test the full pipeline with a phrase."""
    print(f"\n{'='*60}")
    print(f"Testing: {phrase}")
    print('='*60)

    result = {
        "timestamp": datetime.now().isoformat(),
        "input": phrase,
        "issues": []
    }

    # Stage 1: Patois Transform
    print("\n[Stage 1] Transforming to Patois...")
    start = time.perf_counter()
    try:
        response = llm_client.chat.completions.create(
            model=config["grok_model"],
            messages=[
                {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                {"role": "user", "content": phrase}
            ],
            temperature=config["grok_temperature"]
        )
        patois = response.choices[0].message.content.strip()
        llm_latency = (time.perf_counter() - start) * 1000

        result["patois"] = patois
        result["llm_latency_ms"] = llm_latency

        print(f"  Original: {phrase}")
        print(f"  Patois:   {patois}")
        print(f"  Latency:  {llm_latency:.0f}ms")

        # Check quality
        if len(patois) < len(phrase) * 0.5:
            result["issues"].append("Patois too short")
        if phrase.lower() == patois.lower():
            result["issues"].append("No transformation applied")

    except Exception as e:
        print(f"  ERROR: {e}")
        result["issues"].append(f"LLM error: {e}")
        return result

    # Stage 2: TTS Generation
    print("\n[Stage 2] Generating speech...")
    start = time.perf_counter()
    try:
        audio_stream = tts_client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=config["tts_model"],
            text=patois,
            output_format="pcm_24000"
        )

        audio_bytes = b''.join(audio_stream)
        generation_latency = (time.perf_counter() - start) * 1000

        audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        audio_duration = (len(audio_24k) / ELEVENLABS_SAMPLE_RATE) * 1000

        result["tts_generation_ms"] = generation_latency
        result["audio_duration_ms"] = audio_duration

        print(f"  Generation: {generation_latency:.0f}ms")
        print(f"  Duration:   {audio_duration:.0f}ms")

        # Check for issues
        if audio_duration < 100:
            result["issues"].append("Audio too short")
        if generation_latency > 3000:
            result["issues"].append("TTS too slow")

    except Exception as e:
        print(f"  ERROR: {e}")
        result["issues"].append(f"TTS error: {e}")
        return result

    # Stage 3: Playback
    print("\n[Stage 3] Playing audio...")
    try:
        audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, VBCABLE_SAMPLE_RATE)

        # Play to VB-Cable
        if CABLE_DEVICE is not None:
            print(f"  VB-Cable (device {CABLE_DEVICE})")
            sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=CABLE_DEVICE)
            sd.wait()

        # Play to Headphones
        if HEADPHONE_DEVICE is not None:
            print(f"  Headphones (device {HEADPHONE_DEVICE})")
            sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=HEADPHONE_DEVICE)
            sd.wait()

        print("  Playback complete!")

    except Exception as e:
        print(f"  ERROR: {e}")
        result["issues"].append(f"Playback error: {e}")

    # Calculate total latency
    total_latency = result.get("llm_latency_ms", 0) + result.get("tts_generation_ms", 0)
    result["total_latency_ms"] = total_latency

    print(f"\nTotal latency: {total_latency:.0f}ms")

    if result["issues"]:
        print(f"Issues found: {', '.join(result['issues'])}")
    else:
        print("No issues detected!")

    return result

def analyze_results(results):
    """Analyze test results and suggest improvements."""
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    if not results:
        print("No results to analyze.")
        return

    # Aggregate metrics
    avg_llm_latency = np.mean([r.get("llm_latency_ms", 0) for r in results])
    avg_tts_latency = np.mean([r.get("tts_generation_ms", 0) for r in results])
    avg_total_latency = np.mean([r.get("total_latency_ms", 0) for r in results])

    all_issues = []
    for r in results:
        all_issues.extend(r.get("issues", []))

    print(f"\nTests run: {len(results)}")
    print(f"Average LLM latency: {avg_llm_latency:.0f}ms")
    print(f"Average TTS latency: {avg_tts_latency:.0f}ms")
    print(f"Average total latency: {avg_total_latency:.0f}ms")

    if all_issues:
        print(f"\nIssues encountered ({len(all_issues)} total):")
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            print(f"  - {issue}: {count}x")

    # Suggestions
    print("\nSUGGESTIONS:")

    if avg_total_latency > 3000:
        print("  - Total latency high: Consider using faster models")

    if "Patois too short" in all_issues:
        print("  - Patois transformation inconsistent: Adjust prompt or temperature")

    if "TTS too slow" in all_issues:
        print("  - TTS latency high: Check network or use faster model")

    if not all_issues:
        print("  - Pipeline working well! Continue testing with longer phrases.")

def main():
    print("\n" + "="*60)
    print("AUTOMATED VOICE PIPELINE TESTING")
    print("="*60)
    print(f"VB-Cable Device: {CABLE_DEVICE}")
    print(f"Headphone Device: {HEADPHONE_DEVICE}")
    print(f"Test phrases: {len(TEST_PHRASES)}")

    results = []

    for phrase in TEST_PHRASES:
        result = test_pipeline(phrase)
        results.append(result)
        time.sleep(1)  # Brief pause between tests

    # Analyze
    analyze_results(results)

    # Save results
    output_file = Path(__file__).parent / "automated_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "config": config,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print("\nTesting complete!")

if __name__ == "__main__":
    main()
