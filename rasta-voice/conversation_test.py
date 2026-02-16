#!/usr/bin/env python3
"""
Two-Speaker Conversation Simulator

Tests natural conversation flow:
- Speaker A (Operator): English → Patois transformation → TTS
- Speaker B (Natural Rasta): Native Patois → TTS (different voice)
"""

import os
import time
from pathlib import Path

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

# Second voice for natural speaker (we'll use a different ElevenLabs voice)
NATURAL_SPEAKER_VOICE = "bIHbv24MWmeRgasZH58o"  # Will (friendly, natural)

ELEVENLABS_SAMPLE_RATE = 24000
VBCABLE_SAMPLE_RATE = 48000

# AI clients
llm_client = OpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")
tts_client = ElevenLabs(api_key=ELEVENLABS_KEY)

# Transformation prompt (for Operator)
TRANSFORM_PROMPT = """You are "Ganja Mon" - transform the following English to authentic Jamaican Patois.

CORE RULES:
- Keep the EXACT meaning
- Use natural Jamaican speech patterns
- Don't force every word into patois
- Keep technical terms intact

TRANSFORMATIONS:
- "what's up" -> "wah gwaan"
- "I am/I'm" -> "mi"
- "you" -> "yuh" or "unu"
- "this/that" -> "dis/dat"
- "the" -> "di"
- End with "seen?" "ya know?" "ya hear mi?"

Transform this to Patois:"""

# Natural speaker prompt (for Guest)
NATURAL_SPEAKER_PROMPT = """You are a natural Jamaican Rasta speaker having a conversation about cannabis cultivation and AI.

Respond to what was just said in AUTHENTIC Jamaican Patois. Be conversational, friendly, and knowledgeable.

Use natural Jamaican expressions:
- "Wah gwaan" (what's up)
- "seen" / "ya know" / "ya hear mi" (acknowledgments)
- "bredren" / "sistren" (brother/sister)
- "inna" (in the)
- "fi" (for/to)
- "dem" (plural/them)
- "nuh" (don't/not)

Keep responses 2-3 sentences. Sound like you're genuinely interested in the topic.

Previous statement: """

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

def speak_as_operator(text):
    """Operator speaks (English → Patois → TTS with Denzel voice)."""
    print(f"\n[OPERATOR] (Original): {text}")

    # Transform to Patois
    response = llm_client.chat.completions.create(
        model="grok-3",
        messages=[
            {"role": "system", "content": TRANSFORM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.7
    )
    patois = response.choices[0].message.content.strip()
    print(f"[OPERATOR] (Patois): {patois}")

    # Generate TTS with Denzel voice (Jamaican)
    audio_stream = tts_client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        model_id="eleven_turbo_v2_5",
        text=patois,
        output_format="pcm_24000"
    )

    audio_bytes = b''.join(audio_stream)
    audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, VBCABLE_SAMPLE_RATE)

    # Play
    if HEADPHONE_DEVICE is not None:
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=HEADPHONE_DEVICE)
        sd.wait()

    return patois

def speak_as_natural_guest(previous_statement):
    """Natural Rasta speaker responds (generates native Patois)."""
    print(f"\n[NATURAL GUEST] Responding to: '{previous_statement[:50]}...'")

    # Generate natural Patois response
    response = llm_client.chat.completions.create(
        model="grok-3",
        messages=[
            {"role": "system", "content": NATURAL_SPEAKER_PROMPT},
            {"role": "user", "content": previous_statement}
        ],
        temperature=0.8
    )
    patois = response.choices[0].message.content.strip()
    print(f"[NATURAL GUEST] (Patois): {patois}")

    # Generate TTS with different voice
    audio_stream = tts_client.text_to_speech.convert(
        voice_id=NATURAL_SPEAKER_VOICE,
        model_id="eleven_turbo_v2_5",
        text=patois,
        output_format="pcm_24000"
    )

    audio_bytes = b''.join(audio_stream)
    audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, VBCABLE_SAMPLE_RATE)

    # Play
    if HEADPHONE_DEVICE is not None:
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=HEADPHONE_DEVICE)
        sd.wait()

    return patois

# Conversation script
CONVERSATION = [
    # Operator opens the conversation
    ("operator", "Hey everyone, thanks for joining the space! Today I want to talk about how we're using AI to grow cannabis. We have this system called Ganja Mon that monitors everything automatically."),

    # Natural speaker responds
    ("guest", None),  # Will respond to previous

    # Operator continues
    ("operator", "Exactly! So the way it works is we have sensors measuring temperature, humidity, VPD, and CO2 levels. Then the AI analyzes all that data and makes decisions about when to turn on lights, fans, or the humidifier."),

    # Natural speaker asks a question
    ("guest", None),

    # Operator explains
    ("operator", "That's a great question. The AI uses something called VPD, which is vapor pressure deficit. It's basically the relationship between temperature and humidity, and it tells you how much the plant is transpiring. Different growth stages need different VPD targets."),

    # Natural speaker reacts
    ("guest", None),

    # Operator concludes
    ("operator", "Yeah, and the coolest part is everything gets recorded on the Monad blockchain. So you can verify the entire grow from start to finish. It's completely transparent and trustless."),

    # Final response
    ("guest", None),
]

def run_conversation():
    print("\n" + "="*60)
    print("TWO-SPEAKER CONVERSATION SIMULATION")
    print("="*60)
    print("Speaker A (Operator): English -> Patois (Denzel voice)")
    print("Speaker B (Natural Guest): Native Patois (Will voice)")
    print("="*60)

    previous_statement = ""

    for i, (speaker, text) in enumerate(CONVERSATION):
        print(f"\n{'='*60}")
        print(f"Turn {i+1}")
        print('='*60)

        if speaker == "operator":
            patois = speak_as_operator(text)
            previous_statement = patois
        else:  # guest
            patois = speak_as_natural_guest(previous_statement)
            previous_statement = patois

        # Pause between speakers
        time.sleep(1.5)

    print("\n" + "="*60)
    print("CONVERSATION COMPLETE!")
    print("="*60)
    print("\nANALYSIS QUESTIONS:")
    print("1. Did the transformed Patois sound natural?")
    print("2. Did it blend well with the native speaker?")
    print("3. Were there any awkward phrases or mistranslations?")
    print("4. Could you tell which was translated vs. native?")
    print("5. What improvements would make it more authentic?")

if __name__ == "__main__":
    run_conversation()
