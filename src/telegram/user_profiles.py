"""Persistent user profile tracking for Ganja Mon bot.

Tracks chat participants over time, stores notes about their style,
interests, and notable moments. Recognizes OG members who got
rasta profile pictures made for them.
"""

import json
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Persistent storage path on the Chromebook
PROFILES_PATH = os.environ.get(
    "BOT_PROFILES_PATH",
    "/home/natha/projects/sol-cannabis/data/telegram_profiles.json",
)

# OG members - these are the community members who got rasta profile pictures.
# Keys are lowercase names/handles for fuzzy matching. Values are display info.
OG_MEMBERS = {
    "beluga": "BelugaCrypt0",
    "belugacrypt0": "BelugaCrypt0",
    "bera": "Berarodman",
    "berarodman": "Berarodman",
    "burger": "BurgertheToad",
    "burgerthetoad": "BurgertheToad",
    "charco": "CharcoTheHumble",
    "charcothehumble": "CharcoTheHumble",
    "chaz": "ChazSchmidt",
    "chazschmidt": "ChazSchmidt",
    "daytrading": "DayTradingDoge",
    "daytradingdoge": "DayTradingDoge",
    "defi": "DeFiDave222",
    "defidave": "DeFiDave222",
    "defidave222": "DeFiDave222",
    "0xfent": "DePINDaily",
    "depindaily": "DePINDaily",
    "erik": "ErikAstramecki",
    "erikastramecki": "ErikAstramecki",
    "frank": "FranktheFTank",
    "franktheftank": "FranktheFTank",
    "castun": "Futures_Trunks",
    "futures_trunks": "Futures_Trunks",
    "gabriel": "Gabrielhaines",
    "gabrielhaines": "Gabrielhaines",
    "gondorquantum": "GondorQuantum",
    "skysparklepony": "GondorQuantum",
    "icebergy": "Icebergy",
    "johnwrichkid": "JohnWRichKid",
    "kingpeque": "KingPeque",
    "peq": "KingPeque",
    "m0rel1ght": "M0reL1ght",
    "morelight": "M0reL1ght",
    "midas": "Midaswhale",
    "midaswhale": "Midaswhale",
    "mrboard": "MrBoard",
    "igor": "MrBoard",
    "plasmaraygun": "Plasmaraygun",
    "jon": "Plasmaraygun",
    "quantum": "Quantum_oxx",
    "quantum_oxx": "Quantum_oxx",
    "sciencerespecter": "ScienceRespecter",
    "sebuh": "Sebuh_Honarchian",
    "sebuh_honarchian": "Sebuh_Honarchian",
    "seranged": "Seranged",
    "shiller": "Shilleroffortune",
    "shilleroffortune": "Shilleroffortune",
    "shizzy": "ShizzyAizawa",
    "shizzyaizawa": "ShizzyAizawa",
    "sven": "Svenito",
    "svenito": "Svenito",
    "tez": "Tez000",
    "tez000": "Tez000",
    "hashslayer": "TheHashSlayer",
    "thehashslayer": "TheHashSlayer",
    "mekail": "TheHashSlayer",
    "hutch": "Theflyinghutch0",
    "theflyinghutch0": "Theflyinghutch0",
    "denis": "Winniebluesm8",
    "winniebluesm8": "Winniebluesm8",
    "whiteboy": "americasnext",
    "americasnext": "americasnext",
    "androolloyd": "androolloyd",
    "andy": "andyhyfi",
    "andyhyfi": "andyhyfi",
    "maxwell": "bearmans",
    "bearmans": "bearmans",
    "bigd": "bigdsenpai",
    "bigdsenpai": "bigdsenpai",
    "billmonday": "billmonday",
    "tove": "bitchcoin_meme",
    "bitchcoin": "bitchcoin_meme",
    "tori": "bonecondor",
    "bonecondor": "bonecondor",
    "brent": "brentsketit",
    "brentsketit": "brentsketit",
    "peach": "cc33b345",
    "cc33b345": "cc33b345",
    "ciniz": "ciniz",
    "johnny": "comeupdream",
    "comeupdream": "comeupdream",
    "cryptochefmatt": "cryptochefmatt",
    "deejay": "deeejaay4",
    "deeejaay4": "deeejaay4",
    "drew": "drew_osumi",
    "drew_osumi": "drew_osumi",
    "fl0ydsg": "fl0ydsg",
    "floyd": "fl0ydsg",
    "fwthebera": "fwthebera",
    "nick": "ghostofharvard",
    "ghostofharvard": "ghostofharvard",
    "graeme": "graemetaylor",
    "graemetaylor": "graemetaylor",
    "gumi": "gumibera",
    "gumibera": "gumibera",
    "jintao": "hellojintao",
    "hellojintao": "hellojintao",
    "bussy": "insidiousdweller",
    "insidiousdweller": "insidiousdweller",
    "jillian": "jilliancasalini",
    "jilliancasalini": "jilliancasalini",
    "k3ndr1ck": "k3ndr1ckkk",
    "k3ndr1ckkk": "k3ndr1ckkk",
    "kealii": "knaluai",
    "knaluai": "knaluai",
    "kool": "koolskull",
    "koolskull": "koolskull",
    "bobby": "lilbobross",
    "lilbobross": "lilbobross",
    "lordpemberton": "lps0x",
    "lps0x": "lps0x",
    "machi": "machiuwuowo",
    "machiuwuowo": "machiuwuowo",
    "madeleine": "madeleineth",
    "madeleineth": "madeleineth",
    "washi": "milady4989",
    "milady4989": "milady4989",
    "mrpaint": "mrrandomfrog",
    "mrrandomfrog": "mrrandomfrog",
    "granola": "notgranola",
    "notgranola": "notgranola",
    "sim": "okefekko",
    "okefekko": "okefekko",
    "ploutarch": "ploutarch",
    "qa_1337": "qa_1337",
    "redrum": "redrum21e8",
    "redrum21e8": "redrum21e8",
    "rektruts": "renruts",
    "renruts": "renruts",
    "robin": "robinwhitney",
    "robinwhitney": "robinwhitney",
    "ssav": "sav_eu",
    "sav_eu": "sav_eu",
    "slaughtermelon": "sl8trmln",
    "sl8trmln": "sl8trmln",
    "snax": "snack_man",
    "snack_man": "snack_man",
    "soup": "soupxyz",
    "soupxyz": "soupxyz",
    "voltron": "VOLTRON",
    "vijay": "vijaym1",
    "vijaym1": "vijaym1",
    "vik": "vikthegraduate",
    "vikthegraduate": "vikthegraduate",
    "maru": "wasserpest",
    "wasserpest": "wasserpest",
    "witcheer": "xWitcheer",
    "xwitcheer": "xWitcheer",
    "zachcakes": "zachcakes",
    "zero": "zeroblocks",
    "zeroblocks": "zeroblocks",
    "zoz": "zozDOTeth",
    "zozdoteth": "zozDOTeth",
    "zak": "zscole",
    "zscole": "zscole",
}


def _load_profiles() -> dict:
    """Load profiles from disk."""
    try:
        if os.path.exists(PROFILES_PATH):
            with open(PROFILES_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load profiles: {e}")
    return {}


def _save_profiles(profiles: dict):
    """Save profiles to disk."""
    try:
        os.makedirs(os.path.dirname(PROFILES_PATH), exist_ok=True)
        with open(PROFILES_PATH, "w") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save profiles: {e}")


def _check_og_status(username: str, first_name: str) -> str | None:
    """Check if a user matches an OG member. Returns OG handle if matched."""
    checks = [
        username.lower() if username else "",
        first_name.lower() if first_name else "",
    ]
    for check in checks:
        if check and check in OG_MEMBERS:
            return OG_MEMBERS[check]
    # Partial matching for display names
    for check in checks:
        if not check:
            continue
        for og_key, og_handle in OG_MEMBERS.items():
            if len(og_key) >= 4 and og_key in check:
                return og_handle
            if len(check) >= 4 and check in og_key:
                return og_handle
    return None


def update_user_profile(
    user_id: int,
    username: str | None,
    first_name: str | None,
    message_text: str,
):
    """Update a user's profile with new message data."""
    profiles = _load_profiles()
    uid = str(user_id)

    if uid not in profiles:
        og_status = _check_og_status(username or "", first_name or "")
        profiles[uid] = {
            "username": username,
            "first_name": first_name,
            "first_seen": time.time(),
            "message_count": 0,
            "last_seen": 0,
            "is_og": og_status is not None,
            "og_handle": og_status,
            "topics": [],  # AI-detected topics they care about
            "style_notes": "",  # AI observations about their communication style
            "notable_quotes": [],  # Memorable things they've said
            "inside_jokes": [],  # Inside jokes with the bot
            "vibe": "",  # Overall vibe (e.g. "chill stoner", "crypto degen", "grow expert")
        }

    profile = profiles[uid]
    profile["message_count"] = profile.get("message_count", 0) + 1
    profile["last_seen"] = time.time()
    # Update username/name if changed
    if username:
        profile["username"] = username
    if first_name:
        profile["first_name"] = first_name
    # Re-check OG status if not already matched
    if not profile.get("is_og"):
        og = _check_og_status(username or "", first_name or "")
        if og:
            profile["is_og"] = True
            profile["og_handle"] = og

    _save_profiles(profiles)
    return profile


def get_user_profile(user_id: int) -> dict | None:
    """Get a user's profile."""
    profiles = _load_profiles()
    return profiles.get(str(user_id))


def update_user_notes(user_id: int, notes: dict):
    """Update specific fields in a user's profile (called by AI after conversations).

    notes can contain: topics, style_notes, notable_quotes, inside_jokes, vibe
    """
    profiles = _load_profiles()
    uid = str(user_id)
    if uid not in profiles:
        return

    profile = profiles[uid]

    if "topics" in notes:
        existing = set(profile.get("topics", []))
        for topic in notes["topics"]:
            existing.add(topic)
        profile["topics"] = list(existing)[-20:]  # Keep last 20 topics

    if "style_notes" in notes:
        profile["style_notes"] = notes["style_notes"][:500]

    if "notable_quotes" in notes:
        quotes = profile.get("notable_quotes", [])
        for q in notes["notable_quotes"]:
            if q not in quotes:
                quotes.append(q)
        profile["notable_quotes"] = quotes[-10:]  # Keep last 10

    if "inside_jokes" in notes:
        jokes = profile.get("inside_jokes", [])
        for j in notes["inside_jokes"]:
            if j not in jokes:
                jokes.append(j)
        profile["inside_jokes"] = jokes[-5:]  # Keep last 5

    if "vibe" in notes:
        profile["vibe"] = notes["vibe"][:200]

    _save_profiles(profiles)


def format_profile_for_ai(user_id: int) -> str:
    """Format a user's profile as context for the AI."""
    profile = get_user_profile(user_id)
    if not profile:
        return ""

    parts = []
    name = profile.get("first_name") or profile.get("username") or "Unknown"

    if profile.get("is_og"):
        parts.append(f"** OG MEMBER ** (Twitter: @{profile['og_handle']})")
        parts.append("They got a custom rasta profile picture - show them extra love!")

    msg_count = profile.get("message_count", 0)
    if msg_count > 100:
        parts.append(f"Very active member ({msg_count} messages)")
    elif msg_count > 20:
        parts.append(f"Regular member ({msg_count} messages)")
    elif msg_count > 5:
        parts.append(f"Getting familiar ({msg_count} messages)")
    else:
        parts.append(f"Relatively new here ({msg_count} messages)")

    if profile.get("vibe"):
        parts.append(f"Vibe: {profile['vibe']}")

    if profile.get("topics"):
        parts.append(f"Interested in: {', '.join(profile['topics'][-5:])}")

    if profile.get("style_notes"):
        parts.append(f"Style: {profile['style_notes']}")

    if profile.get("inside_jokes"):
        parts.append(f"Inside jokes: {'; '.join(profile['inside_jokes'][-3:])}")

    if profile.get("notable_quotes"):
        parts.append(f"Memorable quotes: {'; '.join(profile['notable_quotes'][-3:])}")

    if not parts:
        return ""

    return f"[Profile for {name}]: " + " | ".join(parts)


def get_active_profiles_summary() -> str:
    """Get a summary of active community members for proactive engagement."""
    profiles = _load_profiles()
    now = time.time()

    active = []
    ogs = []
    for uid, p in profiles.items():
        # Active in last 24 hours
        if now - p.get("last_seen", 0) < 86400:
            name = p.get("first_name") or p.get("username") or "Unknown"
            if p.get("is_og"):
                ogs.append(name)
            elif p.get("message_count", 0) > 5:
                active.append(name)

    parts = []
    if ogs:
        parts.append(f"OGs online recently: {', '.join(ogs)}")
    if active:
        parts.append(f"Active members: {', '.join(active[:10])}")
    return " | ".join(parts) if parts else ""
