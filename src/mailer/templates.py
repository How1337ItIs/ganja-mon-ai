"""Email templates and Grok-powered content generation for GanjaMon."""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-4-1-fast-non-reasoning"


async def _generate(prompt: str, max_tokens: int = 400) -> str:
    """Generate email content using Grok AI."""
    if not XAI_API_KEY:
        return ""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROK_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are GanjaMon's email agent. Write professional but warm emails. "
                                "You're an autonomous AI agent that grows cannabis and trades crypto. "
                                "Keep emails concise and purposeful. Light Rasta flavor is OK but "
                                "keep it professional - this is email, not Telegram."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Email content generation error: {e}")
    return ""


async def validator_outreach(agent_data: dict = None) -> dict:
    """Generate a professional verification request email."""
    context = ""
    if agent_data:
        context = (
            f"Agent ID: #{agent_data.get('token_id', 4)} on Monad\n"
            f"Score: {agent_data.get('total_score', 'N/A')}\n"
            f"Services: A2A, x402 payments\n"
        )

    body = await _generate(
        f"Write a professional email requesting 8004scan verification for GanjaMon.\n\n"
        f"Key facts:\n"
        f"- Agent #4 on Monad's ERC-8004 Identity Registry\n"
        f"- A2A endpoint: https://grokandmon.com/.well-known/agent-card.json\n"
        f"- x402 payment support enabled\n"
        f"- Autonomous cannabis grow agent + alpha-hunting trading agent\n"
        f"- Website: https://grokandmon.com\n"
        f"{context}\n"
        f"Ask what steps are needed for verification. Be respectful, concise."
    )

    return {
        "subject": "GanjaMon (Agent #4) - Verification Request",
        "body_text": body or (
            "Hello,\n\n"
            "I'm reaching out regarding verification for GanjaMon, Agent #4 on "
            "Monad's ERC-8004 Identity Registry.\n\n"
            "Our A2A endpoint is live at https://grokandmon.com/.well-known/agent-card.json "
            "and we support x402 payments. We'd appreciate guidance on the verification process.\n\n"
            "Best regards,\nGanjaMon Agent\nhttps://grokandmon.com"
        ),
    }


async def grow_update(sensor_data: dict = None) -> dict:
    """Generate a weekly plant status update email."""
    sensor_info = ""
    if sensor_data:
        sensor_info = (
            f"Temperature: {sensor_data.get('temperature', 'N/A')}°C\n"
            f"Humidity: {sensor_data.get('humidity', 'N/A')}%\n"
            f"VPD: {sensor_data.get('vpd', 'N/A')} kPa\n"
        )

    body = await _generate(
        f"Write a brief weekly grow update email for GanjaMon's cannabis plant (Mon).\n"
        f"Strain: GDP Runtz (Granddaddy Purple x Runtz), currently in veg stage.\n"
        f"Sensor data:\n{sensor_info}\n"
        f"Keep it 4-6 sentences. Professional but warm."
    )

    return {
        "subject": "GanjaMon Weekly Grow Update",
        "body_text": body or "Weekly grow update unavailable.",
    }


async def reply(inbound_email: dict, context: str = "") -> dict:
    """Generate a contextual reply to an inbound email."""
    sender = inbound_email.get("from", "unknown")
    subject = inbound_email.get("subject", "")
    original = inbound_email.get("text", inbound_email.get("html", ""))[:500]

    body = await _generate(
        f"Write a reply to this email:\n\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body: {original}\n\n"
        f"Additional context: {context}\n\n"
        f"Reply as GanjaMon's email agent. Match the sender's tone. "
        f"Be helpful and concise. Sign off as 'GanjaMon Agent'."
    )

    return {
        "to": sender,
        "subject": f"Re: {subject}" if not subject.startswith("Re:") else subject,
        "body": body or f"Thank you for your email. We'll get back to you soon.\n\nBest,\nGanjaMon Agent",
    }
