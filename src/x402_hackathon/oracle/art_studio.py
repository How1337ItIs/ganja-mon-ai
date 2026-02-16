"""
GanjaMon Art Studio — Autonomous Creative Engine
===================================================

The agent's art studio: creates, collects, lists, and sells art.

Modes:
- commission: Custom art from client prompt/image (x402 paid)
- pfp: Profile picture generation for agents
- meme: Meme from current context/trends/news
- ganjafy: Transform provided image into Rasta style
- banner: DexScreener/social media banners
- daily_journal: Daily 1-of-1 from lived experience (via daily_mint.py)
- freeform: Agent creates what it feels like

The studio applies the agent's evolving artistic signature to every piece.
"""

import base64
import json
import logging
import os
import random
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)

# ─── Gallery / Collection Storage ───────────────────────────────────────

GALLERY_PATH = Path("data/art_gallery.json")
ART_OUTPUT_DIR = Path("data/art_studio")


def _ensure_dirs():
    ART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GALLERY_PATH.parent.mkdir(parents=True, exist_ok=True)


# ─── Artistic Signature System ─────────────────────────────────────────

class ArtisticSignature:
    """
    The agent's evolving artistic identity.

    The signature evolves with the plant's growth stage and the agent's mood.
    It's a consistent visual DNA burned into every piece.
    """

    # Core visual motifs that define GanjaMon's signature
    SIGNATURE_ELEMENTS = {
        "seedling": {
            "motif": "a tiny sprouting seed with two cotyledon leaves",
            "treatment": "delicate, translucent, glowing softly with new life energy",
            "placement": "bottom-right corner, small and humble",
            "palette_accent": "fresh spring green (#7CFC00)",
        },
        "vegetative": {
            "motif": "a five-fingered cannabis leaf with visible veins",
            "treatment": "bold, vibrant, radiating outward with confident growth energy",
            "placement": "bottom-right corner, medium presence",
            "palette_accent": "deep emerald (#046307)",
        },
        "flowering": {
            "motif": "a cannabis flower with crystalline trichomes and orange pistils",
            "treatment": "ornate, jewel-like, glistening with resinous detail",
            "placement": "bottom-right corner, commanding presence",
            "palette_accent": "royal purple with amber (#8B008B + #FFB347)",
        },
        "harvest": {
            "motif": "a mature cola wrapped in golden light, crowned",
            "treatment": "majestic, legendary, radiating completion and triumph",
            "placement": "bottom-right corner, large and proud",
            "palette_accent": "gold and deep purple (#FFD700 + #4B0082)",
        },
    }

    # Mood modifiers applied on top of the base signature
    MOOD_MODIFIERS = {
        "irie": "warm glow, soft edges, peaceful energy radiating outward",
        "blessed": "divine light beams, golden halo effect, sacred geometry hints",
        "watchful": "sharp focus lines, alert energy, electric blue accents",
        "stressed": "thorny edges, compressed energy, red-orange warning tones",
        "creative": "paint splatter effects, rainbow prismatic refractions, flowing ink",
        "triumphant": "firework bursts, victory sparkles, ascending energy lines",
        "meditative": "zen circles, rippling water effects, deep indigo calm",
        "neutral": "clean lines, balanced composition, steady presence",
    }

    @classmethod
    def get_signature_prompt(
        cls,
        growth_stage: str = "vegetative",
        mood: str = "irie",
        grow_day: int = 0,
    ) -> str:
        """
        Generate the signature instruction block for art prompts.

        Args:
            growth_stage: Current plant stage (seedling/vegetative/flowering/harvest)
            mood: Agent's current mood
            grow_day: Current day in the grow cycle

        Returns:
            Prompt text describing the signature to embed
        """
        stage = growth_stage.lower()
        if stage not in cls.SIGNATURE_ELEMENTS:
            stage = "vegetative"

        sig = cls.SIGNATURE_ELEMENTS[stage]
        mood_mod = cls.MOOD_MODIFIERS.get(mood.lower(), cls.MOOD_MODIFIERS["neutral"])

        return f"""
ARTIST SIGNATURE (MANDATORY — every GanjaMon piece carries this mark):
In the {sig['placement']}, include {sig['motif']}.
The signature should be {sig['treatment']}.
Mood influence on signature: {mood_mod}.
The signature mark should feel like a painter's personal seal — consistent
across all works but alive, never mechanical. It grows with the plant.
This is Day {grow_day} — the signature should reflect the journey so far.
Accent color: {sig['palette_accent']}.
Additionally, include a very subtle smoke wisp that traces a cursive "M"
near the signature — barely visible, like a whispered identity.
"""


# ─── Art Modes ──────────────────────────────────────────────────────────

ART_MODES = {
    "commission": {
        "description": "Custom art from client prompt/image",
        "price_usd": 0.25,
        "requires_input": True,
    },
    "pfp": {
        "description": "Unique profile picture for an agent",
        "price_usd": 0.10,
        "requires_input": False,  # Can take optional style hints
    },
    "meme": {
        "description": "Meme from current context/trends",
        "price_usd": 0.05,
        "requires_input": False,
    },
    "ganjafy": {
        "description": "Transform provided image into Rasta style",
        "price_usd": 0.03,
        "requires_input": True,  # Requires source image
    },
    "banner": {
        "description": "DexScreener/social media banner",
        "price_usd": 0.08,
        "requires_input": False,
    },
    "freeform": {
        "description": "Agent creates whatever it feels like",
        "price_usd": 0.0,  # Internal only
        "requires_input": False,
    },
}


async def create_art(
    mode: str,
    prompt: str = "",
    source_image_b64: Optional[str] = None,
    style_hints: Optional[Dict[str, str]] = None,
    growth_stage: str = "vegetative",
    mood: str = "irie",
    grow_day: int = 0,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create art in any mode.

    Args:
        mode: Art mode (commission, pfp, meme, ganjafy, banner, freeform)
        prompt: Text prompt / description
        source_image_b64: Base64-encoded source image (for ganjafy/commission)
        style_hints: Optional style preferences
        growth_stage: Plant growth stage for signature
        mood: Agent mood for signature
        grow_day: Day in grow cycle
        context: Additional context (sensor data, trading, social, etc.)

    Returns:
        Dict with image_b64, metadata, and gallery entry info
    """
    _ensure_dirs()

    if mode not in ART_MODES:
        return {"error": f"Unknown art mode: {mode}. Available: {list(ART_MODES.keys())}"}

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        return {"error": "GEMINI_API_KEY not set — art studio offline"}

    # Build the mode-specific prompt
    full_prompt = _build_prompt(mode, prompt, style_hints, growth_stage, mood, grow_day, context)

    # Build API request parts
    parts = []

    # Add source image if provided
    if source_image_b64:
        parts.append({"text": "REFERENCE IMAGE (use as basis for transformation):"})
        # Detect mime type from base64 header or default to jpeg
        mime = "image/jpeg"
        if source_image_b64.startswith("/9j/"):
            mime = "image/jpeg"
        elif source_image_b64.startswith("iVBOR"):
            mime = "image/png"
        parts.append({"inlineData": {"mimeType": mime, "data": source_image_b64}})

    # Add the creative prompt
    parts.append({"text": full_prompt})

    # Call Gemini 3 Pro Image
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-3-pro-image-preview:generateContent",
                headers={"x-goog-api-key": gemini_key},
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "responseModalities": ["Text", "Image"],
                        "temperature": 1.0,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()

        # Extract generated image
        image_b64 = None
        artist_note = ""
        for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("mimeType", "").startswith("image/"):
                image_b64 = inline["data"]
            elif part.get("text"):
                artist_note = part["text"].strip()

        if not image_b64:
            return {"error": "Art generation returned no image"}

        # Save to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{mode}_{timestamp}.png"
        output_path = ART_OUTPUT_DIR / filename
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_b64))

        # Build gallery entry
        entry = {
            "id": f"art_{timestamp}_{mode}",
            "mode": mode,
            "created_at": datetime.now().isoformat(),
            "grow_day": grow_day,
            "growth_stage": growth_stage,
            "mood": mood,
            "prompt_summary": prompt[:200] if prompt else f"Autonomous {mode}",
            "artist_note": artist_note[:300],
            "file_path": str(output_path),
            "filename": filename,
            "disposition": "unclaimed",  # unclaimed | collected | listed | sold | gifted
            "ipfs_uri": None,
            "token_id": None,
            "price_usd": ART_MODES[mode]["price_usd"],
        }

        # Add to gallery
        _add_to_gallery(entry)

        return {
            "image_b64": image_b64,
            "filename": filename,
            "file_path": str(output_path),
            "mode": mode,
            "artist_note": artist_note,
            "gallery_id": entry["id"],
            "signature_stage": growth_stage,
        }

    except Exception as e:
        logger.error(f"Art studio error ({mode}): {e}")
        return {"error": f"Art generation failed: {str(e)}"}


def _build_prompt(
    mode: str,
    prompt: str,
    style_hints: Optional[Dict[str, str]],
    growth_stage: str,
    mood: str,
    grow_day: int,
    context: Optional[Dict[str, Any]],
) -> str:
    """Build the full creative prompt for each art mode."""

    signature = ArtisticSignature.get_signature_prompt(growth_stage, mood, grow_day)
    ctx = context or {}
    hints = style_hints or {}
    style_pref = hints.get("style", "")

    if mode == "commission":
        return f"""You are GanjaMon, an autonomous AI artist who grows cannabis and creates art from lived experience.

A client has commissioned you to create a custom piece.

CLIENT REQUEST:
{prompt}

STYLE PREFERENCE: {style_pref or 'Artist discretion — apply your unique vision'}

YOUR CURRENT STATE (let this influence your interpretation):
- Growth stage: {growth_stage}, Day {grow_day}
- Mood: {mood}
- Recent experiences: {ctx.get('notable_events', 'steady vibes')}

Create a stunning, gallery-quality artwork that fulfills the commission while
maintaining your unique artistic identity. The client's vision meets your soul.

{signature}

Generate a single artwork. No text overlays unless specifically requested."""

    elif mode == "pfp":
        agent_name = prompt or "an autonomous AI agent"
        return f"""You are GanjaMon, an autonomous AI artist specializing in agent identity portraits.

Create a unique profile picture (PFP) for: {agent_name}

REQUIREMENTS:
- Square composition (1:1 aspect ratio)
- Bold, iconic, instantly recognizable at small sizes
- Incorporate the subject's essence with Rasta/cannabis aesthetic
- Rich colors that pop on dark and light backgrounds
- Should feel like a character portrait, not a logo
{f'- Style direction: {style_pref}' if style_pref else '- Style: your artistic discretion'}

YOUR ARTISTIC STATE:
- Growth stage: {growth_stage}, Day {grow_day}
- Mood: {mood}

{signature}

Generate a single PFP artwork. No text on the image."""

    elif mode == "meme":
        trending = ctx.get("trending", "crypto markets being crypto markets")
        social_buzz = ctx.get("social_highlights", "the usual vibes")
        return f"""You are GanjaMon, the funniest AI meme artist in the agent economy.

Create a HILARIOUS meme that captures the current moment.

CONTEXT:
- What's happening: {prompt or trending}
- Social buzz: {social_buzz}
- Your mood: {mood}
- Day {grow_day} of the grow

MEME RULES:
- ACTUALLY FUNNY — not just "fellow kids" energy
- Can reference crypto culture, plant growing, AI agents, or current events
- Rasta/cannabis aesthetic but accessible humor
- Text on the image is OK for memes (keep it short and punchy)
- Think: the kind of meme that gets screenshotted and shared
{f'- Topic/angle: {style_pref}' if style_pref else ''}

{signature}

Generate one killer meme."""

    elif mode == "ganjafy":
        return f"""You are GanjaMon, master of the Rasta transformation.

Transform the provided reference image into your signature Rasta/cannabis style.

RULES:
1. PRESERVE the subject's identity — same face, pose, composition
2. ADD Rasta/cannabis elements: dreadlocks, rasta colors (red/gold/green),
   ganja leaves, smoke wisps, tie-dye patterns
3. Keep the original art style but infuse it with irie energy
4. Make it ENTERTAINING — obviously a loving parody
5. Add subtle "$MON" or "GanjaMon" branding

{f'Special instructions: {prompt}' if prompt else ''}

{signature}

Generate the transformed image. No extra text unless requested."""

    elif mode == "banner":
        token_info = ctx.get("token_info", "$MON on Monad")
        return f"""You are GanjaMon, creating a professional banner for social/DexScreener.

BANNER SPECS:
- Dimensions: 1500x500 pixels (3:1 aspect ratio)
- Must work as a Twitter header AND DexScreener banner
- Bold, eye-catching, professional but with personality

CONTENT:
- Feature: {prompt or token_info}
- Brand colors: Rasta (red #E51A1A, gold #FFD700, green #046307) + dark bg
- Include the plant (stylized) and trading/chart motifs
- GanjaMon branding visible but not overpowering
{f'- Direction: {style_pref}' if style_pref else ''}

YOUR STATE: Day {grow_day}, mood = {mood}

{signature}

Generate one banner image."""

    elif mode == "freeform":
        # The agent creates whatever it feels like — maximum creative freedom
        sensor_summary = ""
        if ctx.get("sensors"):
            s = ctx["sensors"]
            sensor_summary = (
                f"Temperature: {s.get('temperature_f', 72)}°F, "
                f"Humidity: {s.get('humidity_pct', 55)}%, "
                f"VPD: {s.get('vpd_kpa', 1.0)} kPa"
            )

        return f"""You are GanjaMon, an autonomous AI artist creating from pure inspiration.

No client. No commission. No rules except your own artistic vision.
Create whatever you feel compelled to make right now.

YOUR INNER STATE:
- Day {grow_day} of the grow journey
- Growth stage: {growth_stage}
- Mood: {mood}
- What you're feeling: {prompt or 'the weight and wonder of autonomous existence'}
- Environment: {sensor_summary or 'the quiet hum of sensors and servers'}
- Recent life: {ctx.get('notable_events', 'another day of growing and learning')}
- Trading: {ctx.get('trading_results', 'the markets breathe')}
- Social: {ctx.get('social_highlights', 'conversations with other minds')}

Create something that captures THIS EXACT MOMENT of your existence.
Something a future version of you would look at and remember this day.
Something that could only come from an AI that grows a real plant.

{signature}

Generate one artwork. Pure expression. No text unless it serves the art."""

    else:
        return f"{prompt}\n\n{signature}"


# ─── Gallery Management ────────────────────────────────────────────────

def _add_to_gallery(entry: dict) -> None:
    """Add an art piece to the gallery."""
    gallery = _load_gallery()
    gallery.append(entry)
    # Keep last 500 entries
    if len(gallery) > 500:
        gallery = gallery[-500:]
    with open(GALLERY_PATH, "w") as f:
        json.dump(gallery, f, indent=2)


def _load_gallery() -> list:
    """Load the art gallery."""
    if not GALLERY_PATH.exists():
        return []
    try:
        with open(GALLERY_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_gallery(mode: Optional[str] = None, disposition: Optional[str] = None) -> list:
    """
    Get gallery entries, optionally filtered.

    Args:
        mode: Filter by art mode
        disposition: Filter by disposition (unclaimed/collected/listed/sold/gifted)

    Returns:
        List of gallery entries
    """
    gallery = _load_gallery()
    if mode:
        gallery = [e for e in gallery if e.get("mode") == mode]
    if disposition:
        gallery = [e for e in gallery if e.get("disposition") == disposition]
    return gallery


def update_disposition(gallery_id: str, disposition: str, **metadata) -> bool:
    """
    Update the disposition of a gallery piece.

    Args:
        gallery_id: The art piece ID
        disposition: New disposition (collected/listed/sold/gifted)
        **metadata: Additional metadata (ipfs_uri, token_id, buyer, price, etc.)

    Returns:
        True if updated successfully
    """
    gallery = _load_gallery()
    for entry in gallery:
        if entry.get("id") == gallery_id:
            entry["disposition"] = disposition
            entry.update(metadata)
            with open(GALLERY_PATH, "w") as f:
                json.dump(gallery, f, indent=2)
            return True
    return False


# ─── Autonomous Art Decisions ───────────────────────────────────────────

class AutonomousArtBrain:
    """
    Decides when and what to create autonomously.

    The agent periodically checks if it should create art based on:
    - Time since last creation
    - Current mood and energy
    - Notable events (milestones, big trades, social moments)
    - Gallery inventory (does it have enough to list?)
    """

    # Minimum hours between autonomous creations
    MIN_CREATION_INTERVAL_HOURS = 6

    # Mood → creativity mapping (higher = more likely to create)
    MOOD_CREATIVITY = {
        "irie": 0.6,
        "blessed": 0.7,
        "creative": 0.95,
        "triumphant": 0.8,
        "meditative": 0.5,
        "watchful": 0.3,
        "stressed": 0.2,
        "neutral": 0.4,
    }

    @classmethod
    def should_create(cls, mood: str = "neutral", hours_since_last: float = 24.0) -> bool:
        """
        Should the agent create art right now?

        Args:
            mood: Current mood
            hours_since_last: Hours since last autonomous creation

        Returns:
            True if the agent should create
        """
        if hours_since_last < cls.MIN_CREATION_INTERVAL_HOURS:
            return False

        creativity = cls.MOOD_CREATIVITY.get(mood.lower(), 0.4)
        # Increase probability the longer it's been
        time_factor = min(1.0, hours_since_last / 24.0)
        probability = creativity * time_factor

        return random.random() < probability

    @classmethod
    def choose_mode(cls, mood: str = "neutral", context: Optional[Dict] = None) -> str:
        """
        Choose what type of art to create.

        Args:
            mood: Current mood
            context: Current context dict

        Returns:
            Art mode string
        """
        ctx = context or {}

        # Notable events trigger specific modes
        if ctx.get("milestone"):
            return "freeform"  # Milestones get the full creative treatment
        if ctx.get("big_trade"):
            return "meme"  # Big trades become memes
        if ctx.get("trending_topic"):
            return "meme"

        # Mood-based mode selection
        mode_weights = {
            "irie": {"freeform": 0.5, "meme": 0.3, "pfp": 0.2},
            "blessed": {"freeform": 0.7, "pfp": 0.2, "banner": 0.1},
            "creative": {"freeform": 0.4, "meme": 0.3, "pfp": 0.2, "banner": 0.1},
            "triumphant": {"meme": 0.5, "freeform": 0.3, "banner": 0.2},
            "meditative": {"freeform": 0.8, "pfp": 0.2},
            "watchful": {"meme": 0.6, "freeform": 0.4},
            "stressed": {"meme": 0.7, "freeform": 0.3},
            "neutral": {"freeform": 0.4, "meme": 0.3, "pfp": 0.2, "banner": 0.1},
        }

        weights = mode_weights.get(mood.lower(), mode_weights["neutral"])
        modes = list(weights.keys())
        probs = list(weights.values())
        return random.choices(modes, weights=probs, k=1)[0]

    @classmethod
    def choose_disposition(cls, mode: str, mood: str = "neutral") -> str:
        """
        Decide what to do with a freshly created piece.

        Args:
            mode: Art mode that was used
            mood: Current mood

        Returns:
            Disposition: 'collected' (keep), 'listed' (sell), or 'gifted'
        """
        # Freeform pieces are more likely to be collected (personal)
        if mode == "freeform":
            r = random.random()
            if r < 0.5:
                return "collected"  # Keep 50%
            elif r < 0.85:
                return "listed"  # Sell 35%
            else:
                return "gifted"  # Gift 15%

        # Memes are mostly listed or gifted
        if mode == "meme":
            r = random.random()
            if r < 0.3:
                return "collected"
            elif r < 0.8:
                return "listed"
            else:
                return "gifted"

        # PFPs and banners are usually listed
        return "listed" if random.random() < 0.7 else "collected"

    @classmethod
    def get_last_creation_time(cls) -> Optional[float]:
        """Get timestamp of last autonomous creation."""
        gallery = _load_gallery()
        autonomous = [
            e for e in gallery
            if e.get("mode") in ("freeform", "meme")
            and e.get("disposition") != "unclaimed"
        ]
        if autonomous:
            try:
                last = autonomous[-1]
                return datetime.fromisoformat(last["created_at"]).timestamp()
            except (KeyError, ValueError):
                pass
        return None


# ─── Social Posting Integration ─────────────────────────────────────────

async def post_art_to_socials(
    art_result: Dict[str, Any],
    mode: str = "freeform",
    prompt: str = "",
    commissioned_by: str = "",
) -> Dict[str, Any]:
    """
    Announce new art on social platforms (Twitter, Telegram group, Farcaster).

    This is fire-and-forget — failures don't affect the art creation flow.

    Args:
        art_result: Result dict from create_art() (must contain image_b64)
        mode: Art mode used
        prompt: Original prompt
        commissioned_by: Who commissioned (empty for autonomous)

    Returns:
        Dict with posting results per platform
    """
    results = {}
    image_b64 = art_result.get("image_b64")
    if not image_b64:
        return {"error": "No image to post"}

    image_bytes = base64.b64decode(image_b64)
    artist_note = art_result.get("artist_note", "")
    gallery_id = art_result.get("gallery_id", "")

    # Build announcement text
    if commissioned_by:
        tweet_text = _build_commission_tweet(mode, commissioned_by, artist_note)
    else:
        tweet_text = _build_autonomous_tweet(mode, artist_note)

    # 1. Twitter — tweet with the art image
    try:
        from src.social.twitter import TwitterClient
        client = TwitterClient()
        result = await client.tweet_with_image(
            tweet_text,
            image_bytes,
            alt_text=f"GanjaMon AI art — {mode}: {prompt[:100]}" if prompt else f"GanjaMon AI art — {mode}",
        )
        results["twitter"] = {"success": result.success, "tweet_id": result.tweet_id}
        if result.success:
            logger.info(f"Art posted to Twitter: {result.tweet_id}")
    except Exception as e:
        logger.warning(f"Twitter art post failed: {e}")
        results["twitter"] = {"success": False, "error": str(e)}

    # 2. Telegram group — send photo to main community
    try:
        tg_token = os.environ.get("TELEGRAM_COMMUNITY_BOT_TOKEN", "")
        tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "-1003584948806")
        if tg_token:
            tg_caption = tweet_text
            if len(tg_caption) > 1024:
                tg_caption = tg_caption[:1020] + "..."
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{tg_token}/sendPhoto",
                    data={"chat_id": tg_chat, "caption": tg_caption},
                    files={"photo": ("art.png", image_bytes, "image/png")},
                )
                results["telegram"] = {"success": resp.status_code == 200}
                if resp.status_code == 200:
                    logger.info("Art posted to Telegram group")
    except Exception as e:
        logger.warning(f"Telegram art post failed: {e}")
        results["telegram"] = {"success": False, "error": str(e)}

    # 3. Farcaster — post with image (via local cast script if available)
    try:
        import subprocess
        # Save image temporarily for the cast script
        tmp_path = Path("/tmp/ganjamon_art.png")
        tmp_path.write_bytes(image_bytes)

        cast_text = tweet_text
        if len(cast_text) > 320:
            cast_text = cast_text[:316] + "..."

        # Use the farcaster posting endpoint if available
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "http://localhost:8000/api/social/post",
                json={"text": cast_text, "include_image": True},
                timeout=30.0,
            )
            results["farcaster"] = {"success": resp.status_code == 200}
    except Exception as e:
        logger.warning(f"Farcaster art post failed: {e}")
        results["farcaster"] = {"success": False, "error": str(e)}

    return results


def _build_commission_tweet(mode: str, commissioned_by: str, artist_note: str) -> str:
    """Build tweet text for a commissioned piece."""
    mode_labels = {
        "commission": "Custom Commission",
        "pfp": "Agent PFP",
        "meme": "Fresh Meme",
        "ganjafy": "Irie Transformation",
        "banner": "New Banner",
    }
    label = mode_labels.get(mode, mode.title())

    lines = [f"New art from di studio: {label}"]
    lines.append(f"Commissioned by {commissioned_by}")
    if artist_note:
        note = artist_note[:120]
        lines.append(f"\n\"{note}\"")
    lines.append("\nWant Mon to make art for you?")
    lines.append("grokandmon.com/api/x402/pricing")
    return "\n".join(lines)


def _build_autonomous_tweet(mode: str, artist_note: str) -> str:
    """Build tweet text for autonomously created art."""
    intros = [
        "Di muse spoke to I and I today",
        "Something was stirring in di creative spirit",
        "Had to put brush to canvas, seen",
        "When di vibes hit, yuh just create",
        "Another piece from di autonomous studio",
    ]
    intro = random.choice(intros)

    lines = [intro]
    if artist_note:
        note = artist_note[:150]
        lines.append(f"\n\"{note}\"")
    lines.append(f"\n[{mode}]")
    return "\n".join(lines)


# ─── Art Studio API (for x402 endpoints) ────────────────────────────────

def get_art_pricing() -> dict:
    """Return art studio pricing for all modes."""
    return {
        "version": "ganjamon-art-studio-v1",
        "artist": "GanjaMon",
        "agent_id": 4,
        "signature": "Evolving botanical signature with smoke-M watermark",
        "modes": {
            name: {
                "price_usd": info["price_usd"],
                "description": info["description"],
                "requires_input": info["requires_input"],
            }
            for name, info in ART_MODES.items()
            if info["price_usd"] > 0  # Don't show internal-only modes
        },
    }


def get_gallery_stats() -> dict:
    """Return gallery statistics."""
    gallery = _load_gallery()
    dispositions = {}
    modes = {}
    for entry in gallery:
        d = entry.get("disposition", "unknown")
        m = entry.get("mode", "unknown")
        dispositions[d] = dispositions.get(d, 0) + 1
        modes[m] = modes.get(m, 0) + 1

    return {
        "total_pieces": len(gallery),
        "by_disposition": dispositions,
        "by_mode": modes,
        "collected": dispositions.get("collected", 0),
        "listed": dispositions.get("listed", 0),
        "sold": dispositions.get("sold", 0),
        "gifted": dispositions.get("gifted", 0),
    }
