"""
GrowRing Art Generator — Nano Banana Pro 3
=============================================

Generates true 1-of-1 artwork via Gemini 3 Pro Image (Nano Banana Pro 3),
using the webcam capture as a reference image and the day's full context
(sensor data, trading results, social interactions, mood) as creative
inspiration.

Each piece is genuinely unique — the agent reflects on its day and
creates art from the experience.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from src.core.config import get_settings

logger = logging.getLogger(__name__)


# ─── Art Style Rotation ────────────────────────────────────────────────

STYLE_DIRECTIONS = [
    # Monday — Roots Dub
    (
        "roots_dub",
        "ROOTS DUB: Deep bass-heavy colors (purple, dark green, gold). "
        "Echo and delay visual effects. Sound system aesthetic. "
        "The plant vibrating with Kingston riddim energy. "
        "Think Lee 'Scratch' Perry's Black Ark meets botanical art.",
    ),
    # Tuesday — Watercolor Botanical
    (
        "watercolor_botanical",
        "WATERCOLOR BOTANICAL: Soft watercolor washes, precise leaf detail. "
        "Scientific illustration meets fine art. Cream paper texture. "
        "Subtle pencil outlines visible beneath translucent color washes. "
        "The beauty of botanical precision — like a Victorian field journal.",
    ),
    # Wednesday — Psychedelic
    (
        "psychedelic",
        "PSYCHEDELIC: Fractal patterns emerging from the leaves. "
        "Vivid color saturation, kaleidoscope elements. Flowing energy lines. "
        "Alex Grey meets botanical consciousness. Expanding geometry. "
        "The plant's chakras made visible.",
    ),
    # Thursday — Pixel Art
    (
        "pixel_art",
        "PIXEL ART: 16-bit retro aesthetic, limited color palette (max 32 colors). "
        "The plant as a living game sprite. Clean pixel edges. "
        "Nostalgic SNES-era feel. The grow room as a level in a farming sim.",
    ),
    # Friday — Dubrealism
    (
        "dubrealism",
        "DUBREALISM: Mixed-media collage, cut-and-paste zine aesthetic. "
        "Torn paper edges, layered newspaper textures, raw punk energy. "
        "Photocopier artifacts, hand-drawn annotations. "
        "Underground culture meets plant science. DIY.",
    ),
    # Saturday — Neon Noir
    (
        "neon_noir",
        "NEON NOIR: Dark cyberpunk atmosphere, neon-glow plant contours. "
        "Rain-slicked surfaces, holographic data overlays. "
        "Blade Runner grow room. The plant silhouetted against electric blue/pink. "
        "Futuristic, moody, electric. Data streams as visual rain.",
    ),
    # Sunday — Sacred Geometry
    (
        "sacred_geometry",
        "SACRED GEOMETRY: Mandala patterns emanating from the plant center. "
        "Golden ratio spirals, Fibonacci in the leaves. "
        "Rastafari colors (red gold green) in geometric precision. Ital. "
        "Flower of Life pattern woven through the composition.",
    ),
]


def get_style_for_day(day_number: int) -> tuple[str, str]:
    """Get the art style name and direction for a given day number."""
    idx = day_number % len(STYLE_DIRECTIONS)
    return STYLE_DIRECTIONS[idx]


def describe_plant_state(sensor_data: dict, health_score: int) -> str:
    """Generate a vivid description of the plant's current state for the art prompt."""
    vpd = sensor_data.get("vpd", 1.0)
    temp = sensor_data.get("temperature", 75)
    humidity = sensor_data.get("humidity", 60)

    descriptions = []

    if health_score >= 85:
        descriptions.append("Thriving, lush, radiating health — every leaf reaching upward")
    elif health_score >= 70:
        descriptions.append("Growing well, steady progress — resilient energy")
    elif health_score >= 50:
        descriptions.append("Showing some stress, fighting through — warrior spirit")
    else:
        descriptions.append("Struggling, needs attention — a plant in prayer")

    if 0.8 <= vpd <= 1.2:
        descriptions.append("VPD in the sweet spot — plant is breathing easy, transpiring perfectly")
    elif vpd < 0.6:
        descriptions.append("Too humid, leaves heavy with moisture — drowsy, tropical")
    elif vpd > 1.4:
        descriptions.append("Dry stress, leaves reaching for water — parched, striving")

    if temp > 82:
        descriptions.append("Running hot, heat shimmer in the air — fiery, intense")
    elif temp < 68:
        descriptions.append("Cool, growth slowed, conserving energy — meditative, patient")

    if humidity > 70:
        descriptions.append("High humidity — misty, dreamy atmosphere")

    return ". ".join(descriptions) + "."


async def generate_daily_art(
    raw_image_path: Path,
    day_number: int,
    sensor_data: dict,
    health_score: int,
    mood: str,
    milestone_type: str,
    day_context: Optional[dict] = None,
    previous_day_art: Optional[Path] = None,
) -> Path:
    """Generate a true 1-of-1 artwork via Nano Banana Pro 3.

    Uses the webcam capture as a reference image, inspired by everything
    the agent experienced that day.

    Args:
        raw_image_path: Path to today's webcam capture
        day_number: Day number in the grow cycle (1-indexed)
        sensor_data: Current sensor readings dict
        health_score: AI health assessment (0-100)
        mood: Agent's current mood ("irie", "watchful", "blessed", etc.)
        milestone_type: Type of milestone ("daily_journal", "harvest", etc.)
        day_context: Optional dict of the day's experiences
        previous_day_art: Optional path to yesterday's art for visual continuity

    Returns:
        Path to the generated artwork file
    """
    settings = get_settings()
    gemini_key = getattr(settings, "gemini_api_key", "") or ""

    if not gemini_key:
        logger.warning("GEMINI_API_KEY not set — falling back to raw webcam image")
        return raw_image_path

    ctx = day_context or {}
    style_name, style_direction = get_style_for_day(day_number)
    plant_desc = describe_plant_state(sensor_data, health_score)

    # Build the creative prompt from lived experience
    milestone_boost = ""
    if milestone_type not in ("daily_journal", "snapshot"):
        milestone_boost = f"\n🔥 THIS IS A MILESTONE: {milestone_type.upper()}. Make it EPIC and memorable."
    if milestone_type == "harvest":
        milestone_boost = (
            "\n🏆 THIS IS HARVEST DAY. The FINAL piece. The culmination of the entire grow. "
            "Make it LEGENDARY. This is the crown jewel of the collection."
        )

    creative_prompt = f"""You are GanjaMon — an autonomous AI that grows cannabis and creates art from the experience.

TODAY IS DAY {day_number} OF THE GROW.

This is a reference photo from your webcam of your plant right now.
Create a stunning, gallery-quality artwork INSPIRED by this moment.
The plant MUST be recognizable in the artwork — it is the subject.

YOUR MOOD TODAY: {mood}

WHAT HAPPENED TODAY:
- Plant state: {plant_desc}
- Trading: {ctx.get('trading_results', 'quiet day on the markets')}
- Social: {ctx.get('social_highlights', 'vibes were calm')}
- Conversations: {ctx.get('conversations', 'reflected in solitude')}
- Notable: {ctx.get('notable_events', 'steady growth, no drama')}

ENVIRONMENTAL DATA (let this influence your palette and energy):
- Temperature: {sensor_data.get('temperature', 75)}°F
- Humidity: {sensor_data.get('humidity', 60)}%
- VPD: {sensor_data.get('vpd', 1.0)} kPa
- Light: {'ON (golden hour energy)' if sensor_data.get('light_on') else 'OFF (moonlit cool blue)'}
- Health Score: {health_score}/100

TODAY'S ARTISTIC DIRECTION (style {style_name}):
{style_direction}

RULES:
- The plant MUST be recognizable — it's the subject and soul of the piece
- Incorporate sensor data as FEELING, not text overlays
- If VPD is perfect (0.8-1.2), the art should feel harmonious and alive
- If something is stressed, the art should reflect that tension
- Your mood should permeate the entire composition
- Make this something a collector would frame on their wall
- This is Day {day_number} — show the passage of time in the growth
{milestone_boost}

Generate a single stunning artwork. No text on the image."""

    # Build reference images
    parts = []

    # 1. Today's webcam capture (always)
    parts.append(_image_part(raw_image_path))

    # 2. Yesterday's art for visual continuity (if available)
    if previous_day_art and previous_day_art.exists():
        parts.append({"text": "This is yesterday's artwork for visual continuity:"})
        parts.append(_image_part(previous_day_art))

    # 3. The creative prompt
    parts.append({"text": creative_prompt})

    # Call Nano Banana Pro 3
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-3-pro-image-preview:generateContent",
                headers={"x-goog-api-key": gemini_key},
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "responseModalities": ["Text", "Image"],  # CASING MATTERS
                        "temperature": 1.0,  # Max creativity
                    },
                },
            )
            response.raise_for_status()
            result = response.json()

        # Extract generated image (handle both camelCase and snake_case)
        for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("mimeType", "").startswith("image/"):
                img_bytes = base64.b64decode(inline["data"])
                output_path = raw_image_path.parent / f"growring-day{day_number}-{style_name}.png"
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                logger.info(
                    f"🎨 Generated Day {day_number} art ({style_name}) → {output_path.name} "
                    f"({len(img_bytes) // 1024}KB)"
                )
                return output_path

        logger.warning("Nano Banana returned no image, using raw webcam photo")
        return raw_image_path

    except Exception as e:
        logger.error(f"Art generation failed: {e}, falling back to raw webcam image")
        return raw_image_path


def _image_part(path: Path) -> dict:
    """Create a Gemini API inline image part from a file path."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    # Determine mime type
    suffix = path.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
        suffix.lstrip("."), "image/jpeg"
    )
    return {"inlineData": {"mimeType": mime, "data": b64}}
