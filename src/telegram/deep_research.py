"""Deep member research pipeline for Ganja Mon bot.

Enriches user profiles by looking up OG members on external sources:
- Twitter/X profiles (via xAI Grok web search)
- On-chain wallet activity (via DexScreener)
- Community knowledge cross-referencing

Runs as a background task, periodically researching members who
interact with the bot. Stores findings in the user profile system.
"""

import json
import logging
import os
import time
from pathlib import Path

from .user_profiles import _load_profiles, _save_profiles
from .community_knowledge import OG_INTEL
from .llm_provider import call_llm

logger = logging.getLogger(__name__)

# Research state persistence
RESEARCH_STATE_PATH = os.environ.get(
    "BOT_RESEARCH_STATE_PATH",
    "/home/natha/projects/sol-cannabis/data/telegram_research_state.json",
)

# How often to re-research a member (7 days)
RESEARCH_COOLDOWN = 7 * 86400

# Max members to research per cycle (avoid API spam)
MAX_RESEARCH_PER_CYCLE = 3


def _load_research_state() -> dict:
    """Load research timestamps and results."""
    try:
        if os.path.exists(RESEARCH_STATE_PATH):
            with open(RESEARCH_STATE_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"Failed to load research state: {e}")
    return {}


def _save_research_state(state: dict):
    """Save research state."""
    try:
        os.makedirs(os.path.dirname(RESEARCH_STATE_PATH), exist_ok=True)
        with open(RESEARCH_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.debug(f"Failed to save research state: {e}")


async def _grok_research(prompt: str) -> str | None:
    """Call Grok to research a member (with OpenRouter fallback)."""
    messages = [
        {"role": "system", "content": (
            "You are a research assistant. Extract factual information "
            "about crypto/web3 community members from their public profiles. "
            "Return ONLY valid JSON with the fields requested. "
            "If you can't find info, return empty values. Never fabricate."
        )},
        {"role": "user", "content": prompt},
    ]
    return await call_llm(messages, max_tokens=500, temperature=0.2)


async def research_member(twitter_handle: str, existing_intel: dict | None = None) -> dict | None:
    """Research a community member by their Twitter handle.

    Uses Grok's web knowledge to enrich what we already know.
    Returns a dict of new findings or None.
    """
    existing_summary = ""
    if existing_intel:
        name = existing_intel.get("name", twitter_handle)
        projects = existing_intel.get("projects", [])
        persona = existing_intel.get("persona", "")
        existing_summary = (
            f"We already know: Name={name}, "
            f"Projects={', '.join(projects) if projects else 'unknown'}, "
            f"Persona={persona[:100] if persona else 'unknown'}"
        )

    prompt = (
        f"Research the crypto/web3 personality @{twitter_handle} on Twitter/X.\n\n"
        f"{existing_summary}\n\n"
        "Return a JSON object with any NEW information you can find:\n"
        '{\n'
        '  "recent_activity": "What they\'ve been tweeting about recently (1-2 sentences)",\n'
        '  "new_projects": ["any new projects or roles not in existing data"],\n'
        '  "follower_count": "approximate follower count if known",\n'
        '  "notable_recent": "any notable recent tweets, takes, or events (1 sentence)",\n'
        '  "wallet_activity": "any known on-chain activity or NFT/token holdings",\n'
        '  "communities": ["active communities/DAOs they participate in"],\n'
        '  "conversation_hooks": ["2-3 things the bot could bring up to start a good convo with them"]\n'
        '}\n\n'
        "Only include fields where you have REAL info. Return {} if you know nothing new."
    )

    result = await _grok_research(prompt)
    if not result:
        return None

    try:
        clean = result.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            clean = clean.rsplit("```", 1)[0]
        parsed = json.loads(clean)
        # Filter out empty/null values
        return {k: v for k, v in parsed.items() if v} or None
    except (json.JSONDecodeError, IndexError):
        logger.debug(f"Failed to parse research result: {result[:100]}")
        return None


async def enrich_profile_from_research(user_id: str, og_handle: str, research: dict):
    """Merge research findings into a user's profile."""
    profiles = _load_profiles()
    if user_id not in profiles:
        return

    profile = profiles[user_id]

    # Store raw research data
    if "research" not in profile:
        profile["research"] = {}

    profile["research"]["last_updated"] = time.time()
    profile["research"]["source"] = f"@{og_handle}"

    if research.get("recent_activity"):
        profile["research"]["recent_activity"] = research["recent_activity"]

    if research.get("notable_recent"):
        profile["research"]["notable_recent"] = research["notable_recent"]

    if research.get("follower_count"):
        profile["research"]["follower_count"] = research["follower_count"]

    if research.get("wallet_activity"):
        profile["research"]["wallet_activity"] = research["wallet_activity"]

    if research.get("conversation_hooks"):
        profile["research"]["conversation_hooks"] = research["conversation_hooks"][:5]

    if research.get("new_projects"):
        existing_topics = set(profile.get("topics", []))
        for proj in research["new_projects"]:
            existing_topics.add(proj)
        profile["topics"] = list(existing_topics)[-20:]

    if research.get("communities"):
        existing_topics = set(profile.get("topics", []))
        for comm in research["communities"]:
            existing_topics.add(comm)
        profile["topics"] = list(existing_topics)[-20:]

    _save_profiles(profiles)
    logger.info(f"Enriched profile for {og_handle} (user {user_id})")


async def run_research_cycle():
    """Run a background research cycle on members who need it.

    Called periodically by the bot's job queue. Picks members who:
    1. Are OGs with Twitter handles
    2. Haven't been researched recently (cooldown)
    3. Have been active recently (worth researching)
    """
    research_state = _load_research_state()
    profiles = _load_profiles()
    now = time.time()
    researched = 0

    # Build a list of members to research (prioritize active OGs)
    candidates = []
    for uid, profile in profiles.items():
        og_handle = profile.get("og_handle")
        if not og_handle:
            continue

        # Check cooldown
        last_researched = research_state.get(og_handle, {}).get("last_researched", 0)
        if now - last_researched < RESEARCH_COOLDOWN:
            continue

        # Prioritize recently active members
        last_seen = profile.get("last_seen", 0)
        msg_count = profile.get("message_count", 0)
        priority = msg_count + (1000 if now - last_seen < 86400 else 0)
        candidates.append((priority, uid, og_handle))

    # Sort by priority (most active first)
    candidates.sort(reverse=True)

    for _, uid, og_handle in candidates[:MAX_RESEARCH_PER_CYCLE]:
        existing_intel = OG_INTEL.get(og_handle)
        logger.info(f"Researching @{og_handle}...")

        findings = await research_member(og_handle, existing_intel)
        if findings:
            await enrich_profile_from_research(uid, og_handle, findings)
            researched += 1

        # Update research state
        if og_handle not in research_state:
            research_state[og_handle] = {}
        research_state[og_handle]["last_researched"] = now
        research_state[og_handle]["found_data"] = bool(findings)

    if researched > 0:
        _save_research_state(research_state)
        logger.info(f"Research cycle complete: {researched} members enriched")


def get_research_context(user_id: int) -> str:
    """Get research-enriched context for a user's profile.

    Called during response generation to inject deeper member knowledge.
    """
    profiles = _load_profiles()
    uid = str(user_id)
    if uid not in profiles:
        return ""

    profile = profiles[uid]
    research = profile.get("research", {})
    if not research:
        return ""

    parts = []
    if research.get("recent_activity"):
        parts.append(f"Recent Twitter activity: {research['recent_activity']}")
    if research.get("notable_recent"):
        parts.append(f"Notable: {research['notable_recent']}")
    if research.get("wallet_activity"):
        parts.append(f"On-chain: {research['wallet_activity']}")
    if research.get("conversation_hooks"):
        hooks = "; ".join(research["conversation_hooks"][:3])
        parts.append(f"Good convo starters: {hooks}")

    return "\n".join(parts) if parts else ""
