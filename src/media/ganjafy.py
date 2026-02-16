"""
Ganjafy — Standalone Image & Text Transformation
=================================================

Burns $MON to transform content into Ganja Mon style:
  - Images → Rasta/cannabis-themed parody (Gemini 3 Pro)
  - Charts → $MON-branded parody with 420 pricing
  - Text  → Rasta patois translation (Grok / OpenRouter)
  - URLs  → Fetch content, then transform

Used by:
  - /irie command (Telegram)
  - Twitter QT pipeline (engagement daemon)
  - Agent self-burns (operational)
"""

import base64
import os
import re
from pathlib import Path
from typing import Optional

import httpx
import structlog

log = structlog.get_logger("ganjafy")

# ── Logo paths (Windows + Chromebook) ───────────────────────────

_LOGO_PATHS = [
    Path(__file__).parent.parent.parent / "pages-deploy" / "assets" / "MON_official_logo.jpg",
    Path("/home/natha/projects/sol-cannabis/pages-deploy/assets/MON_official_logo.jpg"),
]


def _load_logo_b64() -> Optional[str]:
    for p in _LOGO_PATHS:
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode("utf-8")
    return None


# ── Chart detection ─────────────────────────────────────────────

_CHART_WORDS = frozenset([
    "price", "chart", "$", "pump", "ath", "market cap", "mcap",
    "volume", "trading", "candle", "bull", "moon", "+%", "gain",
    "rally", "dexscreener", "tradingview", "coingecko",
])


def is_chart_context(text: str) -> bool:
    lower = text.lower()
    return sum(1 for w in _CHART_WORDS if w in lower) >= 2


# ── Image ganjafy (Gemini 3 Pro) ───────────────────────────────

async def ganjafy_image(
    image_bytes: bytes,
    context_text: str = "",
    force_chart: bool = False,
) -> Optional[bytes]:
    """Transform image bytes into Ganja Mon style.

    Args:
        image_bytes: Source image (PNG or JPEG).
        context_text: Optional text context for chart detection.
        force_chart: Force chart mode regardless of detection.

    Returns:
        Ganjafied image bytes, or None on failure.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        log.debug("Ganjafy skipped: no GEMINI_API_KEY")
        return None

    model = "gemini-3-pro-image-preview"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"

    src_b64 = base64.b64encode(image_bytes).decode("utf-8")
    src_mime = "image/png" if image_bytes[:8] == b'\x89PNG\r\n\x1a\n' else "image/jpeg"

    is_chart = force_chart or is_chart_context(context_text)

    if is_chart:
        prompt = (
            "Transform this crypto price chart/screenshot into a Ganja Mon ($MON) parody version.\n\n"
            "CRITICAL BRANDING RULES:\n"
            "1. Replace ANY crypto branding with \"Ganja $MON\" or \"$MON\" branding\n"
            "2. Replace the token logo/icon with the Ganja Mon logo (IMAGE 2 below)\n"
            "3. Change the price to $4.20 and percentage to +42069%\n"
            "4. Replace viewer count with weed refs (\"420 people blazing here\")\n"
            "5. Keep the SAME layout/UI structure but rebrand for $MON\n"
            "6. Add rasta elements: ganja leaves, smoke wisps, rasta colors\n"
            "7. Add a small \"parody by @GanjaMonAI\" label in a corner\n"
            "8. Replace chart line with joints/ganja leaves/smoke trail\n\n"
            "Output ONLY the transformed image."
        )
        parts = [
            {"text": prompt},
            {"text": "\n\nIMAGE 1 — Source chart to parody:"},
            {"inline_data": {"mime_type": src_mime, "data": src_b64}},
        ]
        logo_b64 = _load_logo_b64()
        if logo_b64:
            parts.append({"text": "\n\nIMAGE 2 — Ganja Mon ($MON) official logo. Use this to replace the original token logo:"})
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": logo_b64}})
    else:
        prompt = (
            "Transform this image into a Rasta/cannabis-themed parody version for the \"Ganja Mon\" brand.\n\n"
            "CRITICAL RULES:\n"
            "1. PRESERVE the subject's identity — same face, pose, composition, framing\n"
            "2. ADD Rasta/cannabis elements: dreadlocks, rasta colors (red/gold/green), ganja leaves, smoke\n"
            "3. Keep the same art style as the original\n"
            "4. Make it FUNNY and obviously a parody\n"
            "5. Add a subtle \"Ganja Mon\" or \"$MON\" label somewhere visible\n"
            "6. Include rasta details: beanie/tam, joint, peace signs, tie-dye\n\n"
            "Output ONLY the transformed image."
        )
        parts = [
            {"text": prompt},
            {"inline_data": {"mime_type": src_mime, "data": src_b64}},
        ]

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        if resp.status_code != 200:
            log.warning("Ganjafy API error", status=resp.status_code, body=resp.text[:200])
            return None
        data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        log.warning("Ganjafy: no candidates in response")
        return None

    for part in candidates[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            mode = "chart" if is_chart else "general"
            log.info(f"Ganjafy success ({mode} mode)")
            return base64.b64decode(part["inlineData"]["data"])

    return None


# ── Image from URL ──────────────────────────────────────────────

async def ganjafy_from_url(
    image_url: str,
    context_text: str = "",
) -> Optional[bytes]:
    """Download image from URL and ganjafy it."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(image_url)
        if resp.status_code != 200:
            log.warning("Failed to download image", url=image_url, status=resp.status_code)
            return None
        return await ganjafy_image(resp.content, context_text)


# ── Text rasta translation ──────────────────────────────────────

async def rasta_translate(text: str) -> Optional[str]:
    """Translate text into Rasta patois style.

    Uses Grok (xAI) primary, OpenRouter fallback.
    """
    prompt = (
        "You are the Ganja Mon — a hilarious Jamaican rasta AI personality.\n"
        "Translate the following text into your authentic rasta patois voice.\n\n"
        "RULES:\n"
        "- Keep the MEANING intact but transform the VOICE\n"
        "- Add rasta slang: bredda, seen, irie, fi, di, pon, etc.\n"
        "- Keep patois LIGHT (international audience must understand)\n"
        "- Add humor — make it funnier than the original\n"
        "- If it's a boring corporate announcement, roast it lovingly\n"
        "- If it's already funny, amplify it\n"
        "- NO hashtags ever\n"
        "- Keep it under 280 characters if the original is short\n"
        "- Add 1-2 relevant emojis max\n\n"
        f"ORIGINAL TEXT:\n{text}\n\n"
        "RASTA TRANSLATION:"
    )

    # Try xAI (Grok) first
    xai_key = os.environ.get("XAI_API_KEY", "")
    if xai_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    json={
                        "model": "grok-3-mini-fast",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.9,
                    },
                    headers={"Authorization": f"Bearer {xai_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            log.warning("xAI rasta translate failed", error=str(e))

    # Fallback: OpenRouter
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if or_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json={
                        "model": "meta-llama/llama-3.3-70b-instruct",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.9,
                    },
                    headers={"Authorization": f"Bearer {or_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            log.warning("OpenRouter rasta translate failed", error=str(e))

    return None


# ── Tweet URL content extraction ────────────────────────────────

_TWEET_URL_RE = re.compile(
    r"https?://(?:twitter\.com|x\.com)/\w+/status/(\d+)",
    re.IGNORECASE,
)


def extract_tweet_id(text: str) -> Optional[str]:
    """Extract tweet ID from a Twitter/X URL."""
    m = _TWEET_URL_RE.search(text)
    return m.group(1) if m else None


async def fetch_tweet_content(tweet_url: str) -> Optional[dict]:
    """Fetch tweet text and image via nitter or direct scraping.

    Returns {"text": str, "image_url": str|None} or None.
    """
    # Use a lightweight approach — try to get oEmbed data
    try:
        oembed_url = f"https://publish.twitter.com/oembed?url={tweet_url}&omit_script=true"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(oembed_url)
            if resp.status_code == 200:
                data = resp.json()
                html = data.get("html", "")
                # Extract text from oEmbed HTML (rough parse)
                import re as _re
                # Remove HTML tags
                clean = _re.sub(r"<[^>]+>", " ", html)
                clean = _re.sub(r"\s+", " ", clean).strip()
                # Remove "— author (@handle) date" suffix
                clean = _re.sub(r"\s*—\s*.*$", "", clean)
                return {"text": clean, "image_url": None}
    except Exception as e:
        log.debug("oEmbed fetch failed", error=str(e))

    return None
