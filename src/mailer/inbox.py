"""Inbound email processing for GanjaMon.

Classifies intent, filters spam, generates auto-replies, and persists
every inbound message to ``data/email_inbox.json`` for later review.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-4-1-fast-non-reasoning"

INBOX_PATH = Path(os.environ.get("EMAIL_DATA_DIR", "data")) / "email_inbox.json"

# Spam signals
SPAM_KEYWORDS = [
    "unsubscribe", "click here", "limited time", "act now",
    "guaranteed", "free money", "winner", "selected",
    "nigerian prince", "lottery", "inheritance",
]

# Domains that are likely spam
SPAM_DOMAINS = [
    "noreply@", "mailer-daemon", "bounce",
]


def is_spam(email_data: dict) -> bool:
    """Check if an email is spam."""
    sender = (email_data.get("from") or "").lower()
    subject = (email_data.get("subject") or "").lower()
    body = (email_data.get("text") or "").lower()

    # Check sender domain
    for pattern in SPAM_DOMAINS:
        if pattern in sender:
            return True

    # Check content
    content = f"{subject} {body}"
    spam_hits = sum(1 for kw in SPAM_KEYWORDS if kw in content)
    return spam_hits >= 2


async def classify_intent(email_data: dict) -> str:
    """Classify the intent of an inbound email.

    Returns one of: "question", "partnership", "verification", "feedback", "spam", "other"
    """
    if is_spam(email_data):
        return "spam"

    if not XAI_API_KEY:
        return "other"

    sender = email_data.get("from", "")
    subject = email_data.get("subject", "")
    body = (email_data.get("text") or email_data.get("html", ""))[:300]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
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
                                "Classify this email's intent into ONE of: "
                                "question, partnership, verification, feedback, spam, other. "
                                "Reply with just the single word."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"From: {sender}\nSubject: {subject}\nBody: {body}",
                        },
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1,
                },
            )
            if resp.status_code == 200:
                intent = resp.json()["choices"][0]["message"]["content"].strip().lower()
                if intent in ("question", "partnership", "verification", "feedback", "spam", "other"):
                    return intent
    except Exception as e:
        logger.debug(f"Intent classification error: {e}")

    return "other"


async def process_inbound(email_data: dict) -> Optional[dict]:
    """Process an inbound email and decide on action.

    Returns a reply dict if auto-reply is appropriate, None otherwise.
    """
    intent = await classify_intent(email_data)
    logger.info(f"Email from {email_data.get('from')}: intent={intent}")

    if intent == "spam":
        logger.info("Spam email, ignoring")
        return None

    # Auto-reply for questions, verification requests, and partnerships
    if intent in ("question", "verification", "partnership"):
        from .templates import reply as generate_reply
        context = f"Email classified as: {intent}"
        result = await generate_reply(email_data, context=context)
        return {
            "action": "reply",
            "to": result["to"],
            "subject": result["subject"],
            "body": result["body"],
        }

    # For feedback and other, just acknowledge
    if intent == "feedback":
        sender = email_data.get("from", "")
        subject = email_data.get("subject", "")
        return {
            "action": "reply",
            "to": sender,
            "subject": f"Re: {subject}" if not subject.startswith("Re:") else subject,
            "body": (
                "Thank you for your feedback! The GanjaMon team appreciates you taking "
                "the time to reach out. We'll review your message and follow up if needed.\n\n"
                "One love,\nGanjaMon Agent\nhttps://grokandmon.com"
            ),
        }

    # "other" - no auto-reply
    return None


# ---------------------------------------------------------------------------
# Webhook-facing helper: classify, persist, and optionally auto-reply
# ---------------------------------------------------------------------------

async def process_inbound_email(payload: dict) -> dict:
    """Process an inbound email webhook payload end-to-end.

    1. Classify intent via Grok (question, partnership, verification,
       feedback, spam, other).
    2. Append the email (with classification) to ``data/email_inbox.json``.
    3. If auto-reply is appropriate, queue it via the email client.

    Args:
        payload: Raw webhook body (keys: from, to, subject, text, html, headers).

    Returns:
        A summary dict with ``id``, ``intent``, ``auto_reply`` (bool), and
        any ``error``.
    """
    email_id = str(uuid.uuid4())[:8]

    # --- classify ---
    intent = await classify_intent(payload)

    # --- persist to inbox JSON ---
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    inbox: list = []
    if INBOX_PATH.exists():
        try:
            inbox = json.loads(INBOX_PATH.read_text())
        except Exception:
            pass

    entry = {
        "id": email_id,
        "from": payload.get("from", ""),
        "to": payload.get("to", ""),
        "subject": payload.get("subject", ""),
        "text": payload.get("text", ""),
        "html": payload.get("html", ""),
        "received_at": datetime.now().isoformat(),
        "intent": intent,
        "read": False,
        "raw_headers": payload.get("headers", {}),
    }
    inbox.append(entry)
    # Cap at 200 entries
    inbox = inbox[-200:]
    INBOX_PATH.write_text(json.dumps(inbox, indent=2))

    logger.info(f"Inbound email {email_id} from {entry['from']}: intent={intent}")

    # --- check if this is a reply to a tracked outbound ---
    try:
        from .followup import get_followup_tracker
        was_reply = get_followup_tracker().check_reply(
            from_addr=entry["from"],
            subject=entry["subject"],
        )
        if was_reply:
            logger.info(f"Matched as reply to tracked outbound from {entry['from']}")
    except Exception as e:
        logger.debug(f"Followup reply check: {e}")

    # --- auto-reply if appropriate ---
    auto_reply = False
    try:
        reply_result = await process_inbound(payload)
        if reply_result and reply_result.get("action") == "reply":
            from .client import get_email_client
            client = get_email_client()
            client.queue_send(
                to=reply_result["to"],
                subject=reply_result["subject"],
                body=reply_result["body"],
            )
            auto_reply = True
            logger.info(f"Auto-reply queued for {reply_result['to']}")
    except Exception as exc:
        logger.error(f"Auto-reply error for {email_id}: {exc}")

    return {
        "id": email_id,
        "intent": intent,
        "auto_reply": auto_reply,
    }
