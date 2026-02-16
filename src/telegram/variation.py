"""Response variation tracking to prevent repetitive chatbot behavior."""

import re
import random
import time
from collections import deque
from typing import Optional

# Track recent bot responses per group (stores last 10 responses)
_recent_responses: dict[int, deque] = {}
MAX_RECENT_RESPONSES = 10

# Track recent opening phrases used (to enforce variation)
_recent_openings: dict[int, deque] = {}
MAX_RECENT_OPENINGS = 15

# Common greeting/opening patterns to detect
OPENING_PATTERNS = [
    r"^(wah gwaan|wah gwan)",
    r"^(yo|yow|ayy+|hey|hi|hello)",
    r"^(bredren|mi bredren|fam|family)",
    r"^(seen|true|real talk)",
    r"^(big up|bless up|nuff respect)",
    r"^(rahtid|bumbaclot|bloodclot)",
    r"^(irie|nice|sweet)",
    r"^(hear me now|listen)",
    r"^(ayyy|yeahh? mon)",
]

# Mood/energy levels for variety
MOODS = [
    {"name": "chill", "temp": 0.85, "freq_penalty": 0.4, "pres_penalty": 0.3},
    {"name": "hyped", "temp": 0.95, "freq_penalty": 0.5, "pres_penalty": 0.4},
    {"name": "mellow", "temp": 0.75, "freq_penalty": 0.3, "pres_penalty": 0.2},
    {"name": "vibing", "temp": 0.9, "freq_penalty": 0.45, "pres_penalty": 0.35},
    {"name": "deep", "temp": 0.8, "freq_penalty": 0.35, "pres_penalty": 0.25},
]

# Topic keywords for knowledge injection
TOPIC_KEYWORDS = {
    "growing": ["grow", "plant", "veg", "flower", "harvest", "soil", "hydro", "nutrient", "vpd", "light", "water", "humidity", "temp", "training", "lst", "top", "defoli"],
    "strain": ["strain", "genetic", "indica", "sativa", "hybrid", "gdp", "runtz", "purple", "kush", "haze", "diesel", "cookie", "gelato", "terp"],
    "reggae": ["reggae", "dub", "dancehall", "bob", "marley", "tosh", "tubby", "perry", "jamaica", "rasta", "jah", "riddim", "ska", "rocksteady"],
    "token": ["token", "mon", "monad", "ca", "contract", "buy", "sell", "price", "dex", "swap", "bonding", "curve", "wallet"],
    "project": ["grok", "ai", "autonomous", "sensor", "camera", "dashboard", "website", "twitter"],
    # Trading sub-topics (deep context injected dynamically by agent_brain.py)
    "trading_general": ["trading", "trade", "portfolio", "position", "p&l", "pnl", "bag", "plays", "alpha", "profit", "loss", "degen"],
    "market_regime": ["market", "bull", "bear", "crab", "regime", "sentiment", "trend", "chop", "macro", "btc dominance"],
    "smart_money": ["whale", "smart money", "wallet", "copy trade", "insider", "following"],
    "signals": ["signal", "alert", "call", "setup", "entry", "snipe", "detected"],
    "agent_capabilities": ["capability", "can you", "what do you do", "brain", "skills", "how do you trade"],
    "alpha_research": ["research", "hunting", "edge", "alpha source", "investigating", "studying"],
    # ERC-8004 agent standard (triggers identity + technical context injection)
    "erc8004": ["8004", "erc-8004", "agent registry", "8004scan", "x402", "verification",
                "validate", "validator", "trust model", "identity registry", "agent standard"],
}


def record_bot_response(chat_id: int, response: str):
    """Record a bot response for variation tracking."""
    if chat_id not in _recent_responses:
        _recent_responses[chat_id] = deque(maxlen=MAX_RECENT_RESPONSES)

    _recent_responses[chat_id].append({
        "text": response,
        "opening": extract_opening(response),
        "time": time.time(),
    })

    # Also track the opening separately
    opening = extract_opening(response)
    if opening:
        if chat_id not in _recent_openings:
            _recent_openings[chat_id] = deque(maxlen=MAX_RECENT_OPENINGS)
        _recent_openings[chat_id].append(opening.lower())


def extract_opening(text: str) -> str:
    """Extract the opening word/phrase from a response."""
    if not text:
        return ""

    # Get first 3-4 words or first sentence, whichever is shorter
    text = text.strip()

    # Check for known patterns
    for pattern in OPENING_PATTERNS:
        match = re.match(pattern, text.lower())
        if match:
            return match.group(0)

    # Otherwise get first 2-3 words
    words = text.split()[:3]
    return " ".join(words).lower().rstrip(".,!?")


def get_recent_openings(chat_id: int) -> list[str]:
    """Get list of recent opening phrases used."""
    if chat_id not in _recent_openings:
        return []
    return list(_recent_openings[chat_id])


def get_recent_responses(chat_id: int) -> list[str]:
    """Get recent bot responses."""
    if chat_id not in _recent_responses:
        return []
    return [r["text"] for r in _recent_responses[chat_id]]


def get_anti_repetition_instruction(chat_id: int) -> str:
    """Generate instruction telling the AI what NOT to do."""
    openings = get_recent_openings(chat_id)

    if not openings:
        return ""

    # Get unique recent openings
    unique_openings = list(set(openings[-8:]))

    if len(unique_openings) < 2:
        return ""

    # Build instruction
    avoid_list = ", ".join(f'"{o}"' for o in unique_openings[:6])

    return f"""
ANTI-REPETITION: Your recent messages started with: {avoid_list}
DO NOT start this message with any of those openings. Use a completely different approach:
- Jump straight into the topic with no greeting
- Start with their name
- Start with a reaction to what they said
- Start mid-thought
- Use a DIFFERENT Rasta expression
"""


def detect_topics(text: str) -> list[str]:
    """Detect which topics a message is about."""
    text_lower = text.lower()
    detected = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                detected.append(topic)
                break

    return detected


def get_mood() -> dict:
    """Get a random mood for this response."""
    return random.choice(MOODS)


def get_mood_instruction(mood: dict) -> str:
    """Generate mood instruction for the AI."""
    mood_descriptions = {
        "chill": "You're feeling extra relaxed and mellow right now. Keep it chill, no rush.",
        "hyped": "You're feeling energetic and excited! Bring the hype!",
        "mellow": "You're in a reflective, thoughtful mood. Deeper vibes.",
        "vibing": "You're in the zone, good energy flowing. Natural and smooth.",
        "deep": "You're feeling philosophical today. Drop some wisdom.",
    }
    return f"[MOOD: {mood['name'].upper()}] {mood_descriptions.get(mood['name'], '')}"


# Knowledge chunks for topic-based injection (condensed from main prompt)
KNOWLEDGE_CHUNKS = {
    "growing": """You know growing DEEP:
- VPD: Clone 0.4-0.8, veg 0.8-1.2, flower 1.0-1.5
- Methods: Living soil, coco, DWC, RDWC
- Training: LST, topping, mainlining, ScrOG, defoliation
- Harvest: Cloudy trichomes = peak THC, amber = sedative
- Common issues: Light burn, nutrient lockout, pH drift""",

    "strain": """You know strains encyclopedically:
- GDP Runtz (Mon's strain): Granddaddy Purple x Runtz, indica-dom, 56-63 days flower, grape/berry/candy terps
- Legends: OG Kush, Sour Diesel, GSC, Blue Dream, Gelato, Wedding Cake
- Terpenes: Myrcene (sedating), Limonene (uplifting), Pinene (alert), Caryophyllene (anti-inflammatory)
- Breeders: Jungle Boys, Seed Junky, Compound, Archive, Exotic""",

    "reggae": """You LOVE reggae deeply:
- Legends: Bob Marley (Exodus, Natty Dread), Peter Tosh (Legalize It), Jimmy Cliff, Burning Spear, Dennis Brown, Gregory Isaacs
- Dub: King Tubby (THE originator), Lee "Scratch" Perry (Black Ark), Scientist, Augustus Pablo (melodica master)
- Evolution: Mento > Ska (Skatalites) > Rocksteady > Reggae > Dub > Dancehall (Yellowman) > Modern (Chronixx, Koffee)
- Sound systems: Coxsone's Downbeat, Duke Reid's Treasure Isle""",

    "token": """$MON Token details:
- CA: 0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b
- Chain: Monad (EVM L1, 10k TPS)
- Supply: 1B, on LFJ Token Mill (bonding curve)
- Buy: LFJ Token Mill or any Monad DEX with the CA""",

    "project": """Ganja Mon project:
- First AI-autonomously grown cannabis
- Grok AI (by xAI) reads sensors, controls everything
- No human intervention in growing decisions
- Live at grokandmon.com, @ganjamonai on Twitter
- Legal under CA Prop 64 (6 plants max, 21+)""",
}


def get_topic_knowledge(topics: list[str]) -> str:
    """Get relevant knowledge chunks for detected topics."""
    if not topics:
        return ""

    chunks = []
    for topic in topics[:2]:  # Max 2 topics to keep prompt lean
        if topic in KNOWLEDGE_CHUNKS:
            chunks.append(KNOWLEDGE_CHUNKS[topic])

    if not chunks:
        return ""

    return "\n\n[RELEVANT KNOWLEDGE FOR THIS MESSAGE]\n" + "\n\n".join(chunks)
