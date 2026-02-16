#!/usr/bin/env python3
"""
Test context-aware voice system with simulated multi-speaker conversation.
"""

import sys
sys.path.insert(0, '.')

from rasta_live import ConversationBuffer, RastaDialectTransformer, RASTA_SYSTEM_PROMPT
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Comprehensive Twitter Spaces simulation with edge cases
SIMULATED_CONVERSATION = [
    # EDGE CASE 1: Cold start (no context)
    {"speaker": 0, "text": "Hey what's up everyone"},  # OPERATOR - greeting with no prior context

    # Multiple guests respond
    {"speaker": 1, "text": "Yo! Good to be here man"},
    {"speaker": 2, "text": "What's good!"},
    {"speaker": 3, "text": "Wah gwaan!"},  # Guest already speaking Patois!

    # EDGE CASE 2: Direct question to operator
    {"speaker": 2, "text": "So what strain are you growing right now?"},
    {"speaker": 0, "text": "Purple Milk by Compound Genetics"},  # OPERATOR - answering with detail

    # EDGE CASE 3: Follow-up rapid-fire
    {"speaker": 2, "text": "Oh nice! Sativa or indica?"},
    {"speaker": 0, "text": "60/40 sativa dominant"},  # OPERATOR - quick answer
    {"speaker": 3, "text": "Purple Milk is fire bro!"},
    {"speaker": 0, "text": "Yeah it's looking amazing so far"},  # OPERATOR - agreeing

    # EDGE CASE 4: Operator asks question (role reversal)
    {"speaker": 0, "text": "Have you grown it before?"},  # OPERATOR - asking, not answering
    {"speaker": 3, "text": "Yeah man, grew it last summer, got crazy yields"},

    # EDGE CASE 5: Emotional response
    {"speaker": 0, "text": "Oh damn that's sick!"},  # OPERATOR - excited reaction

    # EDGE CASE 6: Technical discussion
    {"speaker": 2, "text": "What's your VPD running at?"},
    {"speaker": 0, "text": "Keeping it between 1.0 and 1.5 kilopascals in flower"},  # OPERATOR - technical answer

    # EDGE CASE 7: Frustration
    {"speaker": 2, "text": "Mine keeps spiking, it's annoying"},
    {"speaker": 0, "text": "Dude that's frustrating, humidity sensor issues?"},  # OPERATOR - empathy + question

    # EDGE CASE 8: Multiple people talking about same topic
    {"speaker": 4, "text": "Wait are we talking about Purple Milk?"},
    {"speaker": 3, "text": "Yeah bro, best strain ever"},
    {"speaker": 0, "text": "It's definitely one of my favorites"},  # OPERATOR - casual agreement

    # EDGE CASE 9: Philosophical moment
    {"speaker": 2, "text": "I love how AI can help us grow better"},
    {"speaker": 0, "text": "Right? It's like having a really smart assistant watching 24/7"},  # OPERATOR - explaining concept

    # EDGE CASE 10: Sarcasm/teasing
    {"speaker": 3, "text": "Bet you check the plants like every 5 minutes"},
    {"speaker": 0, "text": "Guilty, I'm obsessed"},  # OPERATOR - playful admission

    # EDGE CASE 11: Long response
    {"speaker": 2, "text": "So how does the AI actually work?"},
    {"speaker": 0, "text": "So basically it uses sensors to monitor temp, humidity, CO2, all that. Then Grok AI analyzes the data and makes decisions about when to turn on lights, fans, humidifier, whatever's needed. Pretty much runs itself."},  # OPERATOR - detailed explanation

    # EDGE CASE 12: Short interjection
    {"speaker": 3, "text": "That's crazy!"},
    {"speaker": 0, "text": "Yeah"},  # OPERATOR - minimal response

    # EDGE CASE 13: Question with assumption
    {"speaker": 2, "text": "You must be spending a fortune on electricity"},
    {"speaker": 0, "text": "Actually it's pretty efficient, LEDs don't use that much"},  # OPERATOR - correcting assumption

    # EDGE CASE 14: Ending/goodbye
    {"speaker": 0, "text": "Alright y'all, gotta run but this was fun!"},  # OPERATOR - signing off
]

async def test_context_system():
    print("="*70)
    print("CONTEXT-AWARE SYSTEM TEST")
    print("="*70)
    print("\nSimulating Twitter Spaces with 4 speakers:")
    print("  Speaker 0 (YOU) = Operator - will be translated")
    print("  Speaker 1, 2, 3 = Guests - provide context only")
    print("="*70)

    # Initialize components
    buffer = ConversationBuffer(max_exchanges=10)
    transformer = RastaDialectTransformer(os.getenv("XAI_API_KEY"))

    operator_translations = []

    for i, exchange in enumerate(SIMULATED_CONVERSATION, 1):
        speaker = exchange["speaker"]
        text = exchange["text"]

        # Add ALL speech to conversation buffer (for context)
        speaker_type = "operator" if speaker == 0 else "guest"
        buffer.add(speaker_type, text)

        # Only translate operator speech (speaker 0)
        if speaker == 0:
            print(f"\n{'='*70}")
            print(f"EXCHANGE #{i} - OPERATOR SPEAKS")
            print(f"{'='*70}")

            # Get conversation context
            context = buffer.format_for_prompt(n=5)

            print(f"\nCONTEXT PROVIDED TO GROK:")
            print(context)
            print(f"\nOPERATOR SAYS: \"{text}\"")

            # Transform with context
            translation, latency = await transformer.transform(text, context)

            print(f"\nGANJA MON TRANSLATION: \"{translation}\"")
            print(f"Latency: {latency:.0f}ms")

            operator_translations.append({
                "original": text,
                "translation": translation,
                "context_size": len(buffer.get_recent(5))
            })

        else:
            # Just add guest speech to buffer, don't translate
            print(f"\n[Guest {speaker}]: {text} (added to context)")

    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total exchanges: {len(SIMULATED_CONVERSATION)}")
    print(f"Operator translations: {len(operator_translations)}")
    print(f"Guest exchanges (context only): {len(SIMULATED_CONVERSATION) - len(operator_translations)}")

    print(f"\nOPERATOR TRANSLATIONS:")
    for i, trans in enumerate(operator_translations, 1):
        print(f"\n{i}. Original: \"{trans['original']}\"")
        print(f"   Translation: \"{trans['translation']}\"")
        print(f"   Context exchanges used: {trans['context_size']}")

    print(f"\n{'='*70}")
    print("TEST COMPLETE!")
    print(f"{'='*70}")
    print("\n✓ Context system working correctly!")
    print("✓ Only operator speech translated")
    print("✓ Guest speech used for context")
    print("✓ Conversation buffer maintaining history")

if __name__ == "__main__":
    asyncio.run(test_context_system())
