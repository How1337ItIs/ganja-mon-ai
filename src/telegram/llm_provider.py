"""Shared LLM provider with xAI → OpenRouter fallback cascade.

Used by all telegram modules that need LLM completions.
Extracted as a standalone module to avoid circular imports
(personality.py ↔ deep_research.py).
"""

import os
import logging

import httpx

logger = logging.getLogger(__name__)

# --- xAI (primary) ---
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-4-1-fast-non-reasoning"

# --- OpenRouter (fallback when xAI is down or out of credits) ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "google/gemini-2.0-flash-001"

# Status codes that trigger fallback to next provider
_FALLBACK_STATUS_CODES = {429, 500, 502, 503, 504}


async def call_llm(
    messages: list[dict],
    max_tokens: int = 300,
    temperature: float = 0.9,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
) -> str | None:
    """Call LLM API, cascading xAI → OpenRouter on failure.

    Fallback triggers: 429 (credits exhausted), 5xx (server error),
    timeout, connection error, or any non-200 response.
    """
    # Build provider cascade: xAI first, OpenRouter as fallback
    providers = []
    if XAI_API_KEY:
        providers.append(("xAI", XAI_BASE_URL, XAI_API_KEY, XAI_MODEL))
    if OPENROUTER_API_KEY:
        providers.append(("OpenRouter", OPENROUTER_BASE_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL))

    if not providers:
        logger.error("No LLM API keys configured (XAI_API_KEY / OPENROUTER_API_KEY)")
        return None

    for provider_name, base_url, api_key, model in providers:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # NOTE: grok-4-1-fast-non-reasoning does NOT support frequency_penalty
            # or presence_penalty — both cause 400 errors. We accept but ignore them.
            # OpenRouter models generally DO support them, so only add for non-xAI.
            if provider_name != "xAI":
                if frequency_penalty:
                    payload["frequency_penalty"] = frequency_penalty
                if presence_penalty:
                    payload["presence_penalty"] = presence_penalty

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if provider_name != "xAI":
                        logger.info(f"LLM response via {provider_name} fallback ({model})")
                    return content
                elif resp.status_code in _FALLBACK_STATUS_CODES:
                    logger.warning(
                        f"{provider_name} returned {resp.status_code}, "
                        f"falling back to next provider... ({resp.text[:120]})"
                    )
                    continue  # try next provider
                else:
                    # Non-retryable error (400, 401, 403, etc.) — still try fallback
                    logger.error(f"{provider_name} API error {resp.status_code}: {resp.text[:200]}")
                    continue
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"{provider_name} connection failed ({e}), falling back...")
            continue
        except Exception as e:
            logger.error(f"{provider_name} unexpected error: {e}")
            continue

    logger.error("All LLM providers failed (xAI + OpenRouter)")
    return None
