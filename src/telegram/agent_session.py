"""
GanjaMon Agent Telegram Session — Full user-account automation via Telethon.

This module gives the AI agent full control over a Telegram user account,
enabling capabilities that bots cannot access:
- Read any channel/group (including private alpha channels)
- Manage group info (description, title, photo, pinned messages)
- Manage bots via BotFather programmatically
- Post as a real user (not a bot)
- React, forward, vote in polls
- Moderate (ban/kick/mute members)

Rate-limited to stay under Telegram's radar. All actions have human-like
delays to avoid flood bans.

Usage:
    session = AgentTelegramSession()
    await session.start()

    # Read alpha channel
    msgs = await session.read_messages("@alpha_channel", limit=10)

    # Update group description
    await session.set_group_description(-1003584948806, "New description")

    # Post as user
    await session.post(-1003584948806, "Irie vibes from the grow tent!")

    await session.stop()
"""

import os
import time
import json
import random
import asyncio
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger("ganjamon.telegram.agent")

# Telethon imports — soft-fail if not installed (Windows dev doesn't need it)
try:
    from telethon import TelegramClient
    from telethon.tl.functions.messages import (
        EditChatAboutRequest,
        UpdatePinnedMessageRequest,
    )
    from telethon.tl.functions.channels import (
        EditTitleRequest,
        EditPhotoRequest,
        EditBannedRequest,
        GetParticipantsRequest,
    )
    from telethon.tl.types import (
        ChatBannedRights,
        ChannelParticipantsSearch,
    )
    from telethon.errors import (
        FloodWaitError,
        ChatAdminRequiredError,
        UserNotParticipantError,
        SessionPasswordNeededError,
    )
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.warning("Telethon not installed — AgentTelegramSession unavailable")


# Rate limit defaults
DEFAULT_MIN_DELAY = 30        # seconds between actions
READ_MIN_DELAY = 5            # reads are cheaper
POST_MIN_DELAY = 120          # 2 min between posts
MAX_DAILY_POSTS = 20          # safety cap
MAX_DAILY_ACTIONS = 200       # total actions per day

# Session path on Chromebook
DEFAULT_SESSION_PATH = "/home/natha/projects/sol-cannabis/data/telethon_session"
# Fallback for dev (Windows)
FALLBACK_SESSION_PATH = str(Path(__file__).parent.parent.parent / "data" / "telethon_session")

# Main group chat ID
MAIN_GROUP_ID = -1003584948806


class AgentTelegramSession:
    """Full Telegram user-account control for the GanjaMon agent."""

    def __init__(
        self,
        session_path: Optional[str] = None,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
    ):
        if not TELETHON_AVAILABLE:
            raise RuntimeError("Telethon is not installed. pip install telethon")

        self.session_path = session_path or os.getenv(
            "TELETHON_SESSION_PATH",
            DEFAULT_SESSION_PATH if Path(DEFAULT_SESSION_PATH + ".session").exists()
            else FALLBACK_SESSION_PATH
        )
        self.api_id = api_id or int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = api_hash or os.getenv("TELEGRAM_API_HASH", "")

        if not self.api_id or not self.api_hash:
            raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH required")

        self.client: Optional[TelegramClient] = None
        self._last_action_time = 0.0
        self._daily_posts = 0
        self._daily_actions = 0
        self._day_start = time.time()
        self._connected = False

    async def start(self) -> bool:
        """Connect and verify authorization."""
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            logger.error("Telethon session not authorized — run auth flow first")
            return False

        me = await self.client.get_me()
        logger.info(f"Agent session started as: {me.first_name} (@{me.username})")
        self._connected = True
        return True

    async def stop(self):
        """Disconnect gracefully."""
        if self.client:
            await self.client.disconnect()
            self._connected = False
            logger.info("Agent session disconnected")

    def _check_connected(self):
        if not self._connected:
            raise RuntimeError("Agent session not started — call start() first")

    def _reset_daily_counters(self):
        """Reset counters at midnight."""
        if time.time() - self._day_start > 86400:
            self._daily_posts = 0
            self._daily_actions = 0
            self._day_start = time.time()

    async def _rate_limit(self, min_delay: float = DEFAULT_MIN_DELAY):
        """Enforce human-like delays between actions."""
        self._reset_daily_counters()

        if self._daily_actions >= MAX_DAILY_ACTIONS:
            logger.warning("Daily action limit reached — skipping")
            raise RuntimeError(f"Daily action limit ({MAX_DAILY_ACTIONS}) reached")

        elapsed = time.time() - self._last_action_time
        if elapsed < min_delay:
            jitter = random.uniform(1, min(10, min_delay * 0.3))
            wait = min_delay - elapsed + jitter
            logger.debug(f"Rate limiting: waiting {wait:.1f}s")
            await asyncio.sleep(wait)

        self._last_action_time = time.time()
        self._daily_actions += 1

    async def _safe_execute(self, coro, min_delay: float = DEFAULT_MIN_DELAY):
        """Execute with rate limiting and flood wait handling."""
        self._check_connected()
        await self._rate_limit(min_delay)
        try:
            return await coro
        except FloodWaitError as e:
            logger.warning(f"Flood wait: {e.seconds}s — backing off")
            await asyncio.sleep(e.seconds + random.randint(5, 30))
            return await coro

    # ─── Reading ───────────────────────────────────────────────

    async def read_messages(
        self,
        entity: Union[str, int],
        limit: int = 10,
        offset_id: int = 0,
    ) -> list[dict]:
        """
        Read messages from any channel/group/user.

        Args:
            entity: Channel username (@name), chat ID, or invite link
            limit: Number of messages to fetch (max 100)
            offset_id: Start from this message ID (0 = latest)

        Returns:
            List of dicts with id, text, date, sender_id, reply_to
        """
        self._check_connected()
        await self._rate_limit(READ_MIN_DELAY)

        try:
            messages = await self.client.get_messages(
                entity, limit=min(limit, 100), offset_id=offset_id
            )
            return [
                {
                    "id": m.id,
                    "text": m.text or "",
                    "date": m.date.isoformat() if m.date else None,
                    "sender_id": m.sender_id,
                    "reply_to": m.reply_to.reply_to_msg_id if m.reply_to else None,
                    "forwards": m.forwards,
                    "views": m.views,
                }
                for m in messages
                if m
            ]
        except Exception as e:
            logger.error(f"Failed to read messages from {entity}: {e}")
            return []

    async def get_entity_info(self, entity: Union[str, int]) -> dict:
        """Get info about a channel/group/user."""
        self._check_connected()
        await self._rate_limit(READ_MIN_DELAY)

        try:
            e = await self.client.get_entity(entity)
            return {
                "id": e.id,
                "title": getattr(e, "title", None),
                "username": getattr(e, "username", None),
                "first_name": getattr(e, "first_name", None),
                "participants_count": getattr(e, "participants_count", None),
            }
        except Exception as e:
            logger.error(f"Failed to get entity info: {e}")
            return {}

    # ─── Posting ───────────────────────────────────────────────

    async def post(
        self,
        entity: Union[str, int],
        message: str,
        reply_to: Optional[int] = None,
        silent: bool = False,
    ) -> Optional[int]:
        """
        Post a message as the user account.

        Args:
            entity: Chat ID or username
            message: Text to send
            reply_to: Message ID to reply to
            silent: Send without notification

        Returns:
            Message ID of sent message, or None on failure
        """
        self._check_connected()
        self._reset_daily_counters()

        if self._daily_posts >= MAX_DAILY_POSTS:
            logger.warning(f"Daily post limit ({MAX_DAILY_POSTS}) reached")
            return None

        await self._rate_limit(POST_MIN_DELAY)

        try:
            result = await self.client.send_message(
                entity, message, reply_to=reply_to, silent=silent
            )
            self._daily_posts += 1
            logger.info(
                f"Posted to {entity} ({self._daily_posts}/{MAX_DAILY_POSTS} today)"
            )
            return result.id
        except FloodWaitError as e:
            logger.warning(f"Flood wait on post: {e.seconds}s")
            await asyncio.sleep(e.seconds + random.randint(10, 60))
            return None
        except Exception as e:
            logger.error(f"Failed to post to {entity}: {e}")
            return None

    async def send_file(
        self,
        entity: Union[str, int],
        file_path: str,
        caption: str = "",
    ) -> Optional[int]:
        """Send a file/photo with optional caption."""
        self._check_connected()
        self._reset_daily_counters()

        if self._daily_posts >= MAX_DAILY_POSTS:
            return None

        await self._rate_limit(POST_MIN_DELAY)

        try:
            result = await self.client.send_file(
                entity, file_path, caption=caption
            )
            self._daily_posts += 1
            return result.id
        except Exception as e:
            logger.error(f"Failed to send file to {entity}: {e}")
            return None

    # ─── Group Management ──────────────────────────────────────

    async def set_group_description(
        self, chat_id: int, description: str
    ) -> bool:
        """Update a group/channel description."""
        try:
            entity = await self.client.get_entity(chat_id)
            result = await self._safe_execute(
                self.client(EditChatAboutRequest(peer=entity, about=description))
            )
            logger.info(f"Group description updated for {chat_id}")
            return bool(result)
        except ChatAdminRequiredError:
            logger.error("Not admin — can't change group description")
            return False
        except Exception as e:
            logger.error(f"Failed to set group description: {e}")
            return False

    async def set_group_title(self, chat_id: int, title: str) -> bool:
        """Update a group/channel title."""
        try:
            entity = await self.client.get_entity(chat_id)
            result = await self._safe_execute(
                self.client(EditTitleRequest(channel=entity, title=title))
            )
            logger.info(f"Group title updated for {chat_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set group title: {e}")
            return False

    async def pin_message(
        self, chat_id: int, message_id: int, silent: bool = True
    ) -> bool:
        """Pin a message in a group."""
        try:
            entity = await self.client.get_entity(chat_id)
            result = await self._safe_execute(
                self.client(UpdatePinnedMessageRequest(
                    peer=entity, id=message_id, silent=silent
                ))
            )
            logger.info(f"Pinned message {message_id} in {chat_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to pin message: {e}")
            return False

    async def ban_user(
        self,
        chat_id: int,
        user_id: int,
        duration_hours: int = 0,
    ) -> bool:
        """
        Ban a user from a group.

        Args:
            chat_id: Group chat ID
            user_id: User to ban
            duration_hours: 0 = permanent, >0 = temporary
        """
        try:
            entity = await self.client.get_entity(chat_id)
            user = await self.client.get_entity(user_id)

            until_date = None
            if duration_hours > 0:
                until_date = int(time.time()) + (duration_hours * 3600)

            rights = ChatBannedRights(
                until_date=until_date,
                view_messages=True,
                send_messages=True,
            )
            result = await self._safe_execute(
                self.client(EditBannedRequest(
                    channel=entity, participant=user, banned_rights=rights
                ))
            )
            logger.info(f"Banned user {user_id} from {chat_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to ban user: {e}")
            return False

    async def get_participants(
        self, chat_id: int, limit: int = 100
    ) -> list[dict]:
        """Get group participants."""
        try:
            entity = await self.client.get_entity(chat_id)
            result = await self._safe_execute(
                self.client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(""),
                    offset=0,
                    limit=limit,
                    hash=0,
                )),
                min_delay=READ_MIN_DELAY,
            )
            return [
                {
                    "id": p.user_id,
                    "date": p.date.isoformat() if hasattr(p, "date") and p.date else None,
                }
                for p in result.participants
            ]
        except Exception as e:
            logger.error(f"Failed to get participants: {e}")
            return []

    # ─── BotFather Management ─────────────────────────────────

    async def botfather_command(self, command: str) -> str:
        """
        Send a command to BotFather and get the response.

        Args:
            command: e.g. "/setdescription", "/setabouttext"

        Returns:
            BotFather's response text
        """
        self._check_connected()
        await self._rate_limit(DEFAULT_MIN_DELAY)

        try:
            await self.client.send_message("@BotFather", command)
            await asyncio.sleep(3)  # Wait for response
            messages = await self.client.get_messages("@BotFather", limit=1)
            if messages:
                return messages[0].text or ""
            return ""
        except Exception as e:
            logger.error(f"BotFather command failed: {e}")
            return ""

    # ─── Alpha Channel Reading ─────────────────────────────────

    async def scan_alpha_channels(
        self, channels: list[str], limit: int = 5
    ) -> list[dict]:
        """
        Scan multiple alpha channels for recent messages.
        Used by trading signal aggregation.

        Args:
            channels: List of channel usernames or IDs
            limit: Messages per channel

        Returns:
            Combined list of messages with channel source
        """
        all_messages = []
        for channel in channels:
            msgs = await self.read_messages(channel, limit=limit)
            for msg in msgs:
                msg["source_channel"] = channel
            all_messages.extend(msgs)
            # Small delay between channels
            await asyncio.sleep(random.uniform(2, 5))

        # Sort by date descending
        all_messages.sort(
            key=lambda m: m.get("date", ""), reverse=True
        )
        return all_messages

    # ─── Convenience ───────────────────────────────────────────

    async def get_member_count(self, chat_id: int = MAIN_GROUP_ID) -> int:
        """Get current member count of a group."""
        self._check_connected()
        await self._rate_limit(READ_MIN_DELAY)
        try:
            full = await self.client.get_entity(chat_id)
            # Supergroups: need full chat info
            if hasattr(full, "participants_count") and full.participants_count:
                return full.participants_count
            # Fallback: count participants directly
            from telethon.tl.functions.channels import GetFullChannelRequest
            full_info = await self.client(GetFullChannelRequest(full))
            return full_info.full_chat.participants_count or 0
        except Exception as e:
            logger.error(f"Failed to get member count: {e}")
            return 0

    @property
    def stats(self) -> dict:
        """Current session stats."""
        return {
            "connected": self._connected,
            "daily_posts": self._daily_posts,
            "daily_actions": self._daily_actions,
            "max_daily_posts": MAX_DAILY_POSTS,
            "max_daily_actions": MAX_DAILY_ACTIONS,
        }


# ─── Auth Helper ───────────────────────────────────────────────

async def reauthorize_session(
    session_path: str = DEFAULT_SESSION_PATH,
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    phone: Optional[str] = None,
    code: Optional[str] = None,
) -> dict:
    """
    Two-step re-authorization for expired Telethon sessions.

    Step 1 (code=None): Sends verification code to phone.
    Step 2 (code=<code>): Completes sign-in with the code.

    Returns:
        {"status": "code_sent"} or {"status": "authorized"} or {"status": "error", ...}
    """
    if not TELETHON_AVAILABLE:
        return {"status": "error", "message": "Telethon not installed"}

    _api_id = api_id or int(os.getenv("TELEGRAM_API_ID", "0"))
    _api_hash = api_hash or os.getenv("TELEGRAM_API_HASH", "")
    _phone = phone or os.getenv("TELEGRAM_PHONE", "")
    state_file = "/tmp/telethon_auth_state.json"

    client = TelegramClient(session_path, _api_id, _api_hash)
    await client.connect()

    if await client.is_user_authorized():
        await client.disconnect()
        return {"status": "already_authorized"}

    if code is None:
        # Step 1: Request code
        result = await client.send_code_request(_phone)
        with open(state_file, "w") as f:
            json.dump({"phone_code_hash": result.phone_code_hash}, f)
        await client.disconnect()
        return {"status": "code_sent", "phone": _phone}
    else:
        # Step 2: Complete with code
        try:
            with open(state_file) as f:
                state = json.load(f)
            await client.sign_in(
                _phone, code, phone_code_hash=state["phone_code_hash"]
            )
            authorized = await client.is_user_authorized()
            await client.disconnect()
            if authorized:
                return {"status": "authorized"}
            else:
                return {"status": "error", "message": "Sign-in failed"}
        except SessionPasswordNeededError:
            await client.disconnect()
            return {"status": "error", "message": "2FA password required"}
        except Exception as e:
            await client.disconnect()
            return {"status": "error", "message": str(e)}
