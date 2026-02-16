"""GanjaMon email client using Resend REST API.

Handles sending, queuing, inbox management, and rate limiting.
Uses httpx (already a project dependency) for HTTP calls.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_API_URL = "https://api.resend.com/emails"
EMAIL_FROM = os.environ.get("EMAIL_FROM", "agent@grokandmon.com")

# File paths
DATA_DIR = Path(os.environ.get("EMAIL_DATA_DIR", "data"))
OUTBOX_PATH = DATA_DIR / "email_outbox.json"
INBOX_PATH = DATA_DIR / "email_inbox.json"
STATE_PATH = DATA_DIR / "email_state.json"

# Rate limits
MIN_SEND_INTERVAL = 300  # 5 minutes between sends
MAX_DAILY_SENDS = 50


class GanjaMonEmail:
    """Email client for GanjaMon agent."""

    def __init__(self):
        self._state = self._load_state()

    def _load_state(self) -> dict:
        try:
            if STATE_PATH.exists():
                return json.loads(STATE_PATH.read_text())
        except Exception as e:
            logger.debug(f"Email state load: {e}")
        return {
            "last_send_time": 0,
            "daily_count": 0,
            "daily_reset": datetime.now().strftime("%Y-%m-%d"),
            "sent_ids": [],
        }

    def _save_state(self):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            STATE_PATH.write_text(json.dumps(self._state, indent=2))
        except Exception as e:
            logger.debug(f"Email state save: {e}")

    def _check_rate_limit(self) -> bool:
        """Return True if sending is allowed."""
        now = time.time()
        today = datetime.now().strftime("%Y-%m-%d")

        # Reset daily counter
        if self._state.get("daily_reset") != today:
            self._state["daily_count"] = 0
            self._state["daily_reset"] = today

        # Check daily limit
        if self._state.get("daily_count", 0) >= MAX_DAILY_SENDS:
            logger.warning(f"Daily email limit reached ({MAX_DAILY_SENDS})")
            return False

        # Check minimum interval
        last_send = self._state.get("last_send_time", 0)
        if now - last_send < MIN_SEND_INTERVAL:
            logger.debug("Email send rate limited (too frequent)")
            return False

        return True

    async def send(
        self,
        to: str,
        subject: str,
        body_text: str = "",
        body_html: str = "",
    ) -> bool:
        """Send an email via Resend API.

        Returns True on success, False on failure.
        """
        if not RESEND_API_KEY:
            logger.error("RESEND_API_KEY not set, cannot send email")
            return False

        if not self._check_rate_limit():
            return False

        payload = {
            "from": EMAIL_FROM,
            "to": [to] if isinstance(to, str) else to,
            "subject": subject,
        }
        if body_html:
            payload["html"] = body_html
        if body_text:
            payload["text"] = body_text
        if not body_html and not body_text:
            logger.error("Email must have body_text or body_html")
            return False

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    email_id = data.get("id", "")
                    logger.info(f"Email sent to {to}: {subject} (id: {email_id})")

                    # Update state
                    self._state["last_send_time"] = time.time()
                    self._state["daily_count"] = self._state.get("daily_count", 0) + 1
                    sent_ids = self._state.get("sent_ids", [])
                    sent_ids.append(email_id)
                    self._state["sent_ids"] = sent_ids[-100:]  # Keep last 100
                    self._save_state()

                    # Track for follow-up
                    try:
                        from .followup import get_followup_tracker
                        get_followup_tracker().track_sent(
                            to=to if isinstance(to, str) else to[0],
                            subject=subject,
                            body_snippet=body_text[:200] if body_text else "",
                        )
                    except Exception as e:
                        logger.debug(f"Followup tracking: {e}")

                    return True
                else:
                    logger.error(f"Resend API error {resp.status_code}: {resp.text[:200]}")
                    return False

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

    def queue_send(self, to: str, subject: str, body: str):
        """Queue an email for sending by the daemon (with dedup)."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        outbox = []
        if OUTBOX_PATH.exists():
            try:
                outbox = json.loads(OUTBOX_PATH.read_text())
            except Exception:
                pass

        # Dedup: check if identical (to + subject) already in outbox
        for existing in outbox:
            if existing.get("to") == to and existing.get("subject") == subject:
                logger.debug(f"Email already in outbox for {to}: {subject} — skipping duplicate")
                return

        outbox.append({
            "id": str(uuid.uuid4())[:8],
            "to": to,
            "subject": subject,
            "body_text": body,
            "body_html": "",
            "queued_at": datetime.now().isoformat(),
        })
        OUTBOX_PATH.write_text(json.dumps(outbox, indent=2))
        logger.info(f"Email queued for {to}: {subject}")

    def get_inbox(self, unread_only: bool = True) -> list[dict]:
        """Get inbox emails."""
        if not INBOX_PATH.exists():
            return []
        try:
            inbox = json.loads(INBOX_PATH.read_text())
            if unread_only:
                return [e for e in inbox if not e.get("read")]
            return inbox
        except Exception as e:
            logger.debug(f"Inbox read error: {e}")
            return []

    def mark_read(self, message_id: str):
        """Mark an inbox message as read."""
        if not INBOX_PATH.exists():
            return
        try:
            inbox = json.loads(INBOX_PATH.read_text())
            for email in inbox:
                if email.get("id") == message_id:
                    email["read"] = True
            INBOX_PATH.write_text(json.dumps(inbox, indent=2))
        except Exception as e:
            logger.debug(f"Mark read error: {e}")

    def get_stats(self) -> dict:
        """Get email statistics."""
        return {
            "daily_sent": self._state.get("daily_count", 0),
            "daily_limit": MAX_DAILY_SENDS,
            "inbox_unread": len(self.get_inbox(unread_only=True)),
            "inbox_total": len(self.get_inbox(unread_only=False)),
        }


# Module-level singleton
_client: Optional[GanjaMonEmail] = None


def get_email_client() -> GanjaMonEmail:
    """Get or create the singleton email client."""
    global _client
    if _client is None:
        _client = GanjaMonEmail()
    return _client
