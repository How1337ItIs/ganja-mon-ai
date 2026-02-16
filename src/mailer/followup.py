"""Email follow-up tracker for GanjaMon.

Tracks outbound emails and detects when replies arrive.  If no reply
within ``FOLLOWUP_DAYS``, queues a gentle follow-up via the email client.

Data persisted to ``data/email_followups.json``.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("EMAIL_DATA_DIR", "data"))
FOLLOWUP_PATH = DATA_DIR / "email_followups.json"

# Follow-up policy
FOLLOWUP_DAYS = 3          # Days before first follow-up
MAX_FOLLOWUPS = 2           # Max follow-ups per thread (then give up)
COOLDOWN_DAYS = 7           # Min days between follow-ups to same recipient


class FollowupTracker:
    """Track outbound emails and queue follow-ups for unanswered ones."""

    def __init__(self):
        self._entries: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if FOLLOWUP_PATH.exists():
            try:
                return json.loads(FOLLOWUP_PATH.read_text())
            except Exception as e:
                logger.debug(f"Followup load error: {e}")
        return []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        FOLLOWUP_PATH.write_text(json.dumps(self._entries, indent=2))

    # ------------------------------------------------------------------
    # Record outbound
    # ------------------------------------------------------------------

    def track_sent(self, to: str, subject: str, body_snippet: str = ""):
        """Record an outbound email for follow-up tracking.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body_snippet: First ~200 chars of body (for context in follow-up).
        """
        # Normalise
        to_lower = to.lower().strip()

        # Don't track noreply / bounce addresses
        if any(p in to_lower for p in ("noreply", "no-reply", "mailer-daemon", "bounce")):
            return

        # Don't double-track same recipient + subject
        for e in self._entries:
            if e["to"].lower() == to_lower and e["subject"] == subject:
                logger.debug(f"Already tracking email to {to}: {subject}")
                return

        self._entries.append({
            "to": to,
            "subject": subject,
            "body_snippet": body_snippet[:200],
            "sent_at": datetime.now().isoformat(),
            "replied": False,
            "replied_at": None,
            "followups_sent": 0,
            "last_followup_at": None,
            "closed": False,  # True when replied or max followups reached
        })
        self._save()
        logger.info(f"Tracking email to {to} for follow-up: {subject}")

    # ------------------------------------------------------------------
    # Match inbound replies
    # ------------------------------------------------------------------

    def check_reply(self, from_addr: str, subject: str) -> bool:
        """Check if an inbound email is a reply to a tracked outbound.

        Marks the tracked entry as replied if matched.

        Returns True if this was a matched reply.
        """
        from_lower = from_addr.lower().strip()
        # Normalise subject (strip Re:/Fwd: prefixes)
        clean_subj = _strip_reply_prefix(subject).lower().strip()

        matched = False
        for entry in self._entries:
            if entry["closed"] and entry["replied"]:
                continue
            entry_subj = _strip_reply_prefix(entry["subject"]).lower().strip()
            # Match: same recipient replied, and subject matches
            if entry["to"].lower() == from_lower and entry_subj == clean_subj:
                entry["replied"] = True
                entry["replied_at"] = datetime.now().isoformat()
                entry["closed"] = True
                matched = True
                logger.info(f"Reply received from {from_addr} for: {entry['subject']}")

        if matched:
            self._save()
        return matched

    # ------------------------------------------------------------------
    # Get emails needing follow-up
    # ------------------------------------------------------------------

    def get_stale_emails(self) -> list[dict]:
        """Return tracked emails that need a follow-up.

        An email is stale when:
        - Not replied to
        - Not closed (< MAX_FOLLOWUPS sent)
        - Sent >= FOLLOWUP_DAYS ago (or last follow-up >= FOLLOWUP_DAYS ago)
        """
        now = datetime.now()
        stale = []

        for entry in self._entries:
            if entry["closed"] or entry["replied"]:
                continue
            if entry["followups_sent"] >= MAX_FOLLOWUPS:
                entry["closed"] = True
                continue

            # Check timing
            ref_time_str = entry.get("last_followup_at") or entry["sent_at"]
            try:
                ref_time = datetime.fromisoformat(ref_time_str)
            except (ValueError, TypeError):
                continue

            if (now - ref_time) >= timedelta(days=FOLLOWUP_DAYS):
                stale.append(entry)

        if any(e["closed"] for e in self._entries):
            self._save()  # persist any newly closed entries

        return stale

    def record_followup_sent(self, to: str, subject: str):
        """Mark that a follow-up was sent for this tracked email."""
        to_lower = to.lower().strip()
        clean_subj = _strip_reply_prefix(subject).lower().strip()

        for entry in self._entries:
            entry_subj = _strip_reply_prefix(entry["subject"]).lower().strip()
            if entry["to"].lower() == to_lower and entry_subj == clean_subj:
                entry["followups_sent"] += 1
                entry["last_followup_at"] = datetime.now().isoformat()
                if entry["followups_sent"] >= MAX_FOLLOWUPS:
                    entry["closed"] = True
                break

        self._save()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Summary stats for unified context injection."""
        total = len(self._entries)
        awaiting = sum(1 for e in self._entries if not e["closed"] and not e["replied"])
        replied = sum(1 for e in self._entries if e["replied"])
        stale = len(self.get_stale_emails())
        return {
            "tracked": total,
            "awaiting_reply": awaiting,
            "replied": replied,
            "needs_followup": stale,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_reply_prefix(subject: str) -> str:
    """Remove Re:/Fwd: prefixes for matching."""
    import re
    return re.sub(r"^(Re:\s*|Fwd?:\s*)+", "", subject, flags=re.IGNORECASE).strip()


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_tracker: Optional[FollowupTracker] = None


def get_followup_tracker() -> FollowupTracker:
    global _tracker
    if _tracker is None:
        _tracker = FollowupTracker()
    return _tracker
