"""
Farcaster Social Client
========================

Posts casts, replies to mentions, and engages on Farcaster via Neynar API.
Uses the farcaster-agent node scripts for cast submission (x402 payments).

Farcaster is the PRIMARY engagement channel - replies and conversations happen here.
Twitter is original posts only (no replies - compliance risk).
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# Farcaster agent directory (has post-cast.js)
FARCASTER_AGENT_DIR = Path(__file__).parent.parent.parent / "agents" / "farcaster"

# APIs
NEYNAR_API = "https://api.neynar.com/v2/farcaster"
WARPCAST_API = "https://api.warpcast.com/v2"

# GanjaMon Farcaster identity
GANJAMON_FID = int(os.getenv("FARCASTER_FID", "2696987"))
GANJAMON_USERNAME = "ganjamon"


@dataclass
class Cast:
    hash: str
    author_username: str
    author_fid: int
    text: str
    parent_hash: Optional[str] = None
    timestamp: Optional[datetime] = None
    likes: int = 0
    recasts: int = 0
    replies: int = 0
    channel: Optional[str] = None


@dataclass
class CastResult:
    success: bool
    cast_hash: Optional[str] = None
    error: Optional[str] = None
    text: str = ""


class FarcasterClient:
    """
    Async Farcaster client for posting casts and engaging with community.

    Posting: via node post-cast.js (handles x402 USDC micropayments)
    Reading: via Neynar REST API

    Required env vars:
        NEYNAR_API_KEY - for reading feeds/notifications
        PRIVATE_KEY, SIGNER_PRIVATE_KEY, FID - for posting (via post-cast.js)
    """

    def __init__(self):
        self.neynar_key = os.getenv("NEYNAR_API_KEY", "")
        self.private_key = os.getenv("FARCASTER_PRIVATE_KEY", "")
        self.signer_key = os.getenv("FARCASTER_SIGNER_KEY", "")
        self.fid = GANJAMON_FID
        self._session: Optional[aiohttp.ClientSession] = None
        self._configured = bool(self.neynar_key)

        # Rate limiting
        self.min_minutes_between_posts = 15
        self.min_minutes_between_replies = 5
        self.last_post_time: Optional[datetime] = None
        self.last_reply_time: Optional[datetime] = None

        # Track replied-to casts to avoid duplicates
        self._replied_hashes: set = set()
        self._state_file = Path("data/farcaster_state.json")
        self._load_state()

    def _load_state(self):
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                self._replied_hashes = set(data.get("replied_hashes", []))
                if data.get("last_post_time"):
                    self.last_post_time = datetime.fromisoformat(data["last_post_time"])
                if data.get("last_reply_time"):
                    self.last_reply_time = datetime.fromisoformat(data["last_reply_time"])
            except Exception:
                pass

    def _save_state(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        # Keep only last 500 replied hashes
        recent_hashes = list(self._replied_hashes)[-500:]
        data = {
            "replied_hashes": recent_hashes,
            "last_post_time": self.last_post_time.isoformat() if self.last_post_time else None,
            "last_reply_time": self.last_reply_time.isoformat() if self.last_reply_time else None,
        }
        self._state_file.write_text(json.dumps(data, indent=2))

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"accept": "application/json"}
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ==================== POSTING ====================

    async def post_cast(self, text: str, parent_hash: Optional[str] = None,
                        embed_url: Optional[str] = None) -> CastResult:
        """
        Post a cast to Farcaster via the node script.

        Args:
            text: Cast text (max 1024 chars for Farcaster)
            parent_hash: If replying, the parent cast hash
            embed_url: Optional URL embed
        """
        # Farcaster hub enforces 320 BYTES. Truncate to 280 chars to be safe
        # (emoji can be 3-4 bytes each).
        if len(text) > 280:
            text = text[:277] + "..."

        if not FARCASTER_AGENT_DIR.exists():
            return CastResult(success=False, text=text, error="farcaster-agent dir not found")

        cmd = [
            "node", "src/post-cast.js", text,
        ]
        if parent_hash:
            cmd.extend(["--reply-to", parent_hash])
        if embed_url:
            cmd.extend(["--embed", embed_url])

        env = os.environ.copy()
        env["PRIVATE_KEY"] = self.private_key
        env["SIGNER_PRIVATE_KEY"] = self.signer_key
        env["FID"] = str(self.fid)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    cwd=str(FARCASTER_AGENT_DIR),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
            )

            if result.returncode == 0:
                # Try to extract hash from output
                cast_hash = None
                for line in result.stdout.split("\n"):
                    if "hash" in line.lower() or "0x" in line:
                        cast_hash = line.strip()
                        break

                logger.info(f"Farcaster cast posted: {text[:50]}...")
                return CastResult(success=True, cast_hash=cast_hash, text=text)
            else:
                error = result.stderr or result.stdout
                logger.error(f"Farcaster post failed: {error[:200]}")
                return CastResult(success=False, text=text, error=error[:200])

        except subprocess.TimeoutExpired:
            return CastResult(success=False, text=text, error="Timeout posting cast")
        except Exception as e:
            return CastResult(success=False, text=text, error=str(e))

    async def post(self, text: str, embed_url: Optional[str] = None) -> CastResult:
        """Post an original cast (rate-limited)."""
        if self.last_post_time:
            elapsed = (datetime.now() - self.last_post_time).total_seconds() / 60
            if elapsed < self.min_minutes_between_posts:
                return CastResult(
                    success=False, text=text,
                    error=f"Rate limited. Wait {self.min_minutes_between_posts - elapsed:.0f}m"
                )

        result = await self.post_cast(text, embed_url=embed_url)
        if result.success:
            self.last_post_time = datetime.now()
            self._save_state()
        return result

    async def reply(self, text: str, parent_hash: str) -> CastResult:
        """Reply to a cast (rate-limited, deduped)."""
        if parent_hash in self._replied_hashes:
            return CastResult(success=False, text=text, error="Already replied to this cast")

        if self.last_reply_time:
            elapsed = (datetime.now() - self.last_reply_time).total_seconds() / 60
            if elapsed < self.min_minutes_between_replies:
                return CastResult(
                    success=False, text=text,
                    error=f"Reply rate limited. Wait {self.min_minutes_between_replies - elapsed:.0f}m"
                )

        result = await self.post_cast(text, parent_hash=parent_hash)
        if result.success:
            self._replied_hashes.add(parent_hash)
            self.last_reply_time = datetime.now()
            self._save_state()
        return result

    # ==================== READING ====================

    async def get_notifications(self, limit: int = 25) -> List[Cast]:
        """Get recent notifications (mentions, replies).

        Tries Neynar first, falls back to Warpcast public API.
        """
        session = await self._get_session()

        # Try Neynar (requires active plan)
        if self._configured:
            try:
                url = f"{NEYNAR_API}/notifications"
                params = {"fid": self.fid, "limit": limit}
                headers = {"accept": "application/json", "x-api-key": self.neynar_key}
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        casts = []
                        for notif in data.get("notifications", []):
                            cast_data = notif.get("cast", {})
                            if not cast_data:
                                continue
                            casts.append(Cast(
                                hash=cast_data.get("hash", ""),
                                author_username=cast_data.get("author", {}).get("username", ""),
                                author_fid=cast_data.get("author", {}).get("fid", 0),
                                text=cast_data.get("text", ""),
                                parent_hash=cast_data.get("parent_hash"),
                                likes=cast_data.get("reactions", {}).get("likes_count", 0),
                                recasts=cast_data.get("reactions", {}).get("recasts_count", 0),
                            ))
                        return casts
                    elif resp.status == 402:
                        logger.debug("Neynar credits exceeded, skipping notifications")
            except Exception as e:
                logger.error(f"Neynar notifications error: {e}")

        # Fallback: get our own recent casts and look for replies
        # (Warpcast public API doesn't support notifications for other users)
        return []

    async def get_channel_feed(self, channel: str, limit: int = 25) -> List[Cast]:
        """Get recent casts from a channel.

        Tries Neynar first, falls back to Warpcast public API.
        """
        session = await self._get_session()

        # Try Neynar
        if self._configured:
            try:
                url = f"{NEYNAR_API}/feed/channels"
                params = {"channel_ids": channel, "limit": limit, "with_recasts": "false"}
                headers = {"accept": "application/json", "x-api-key": self.neynar_key}
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        casts = []
                        for item in data.get("casts", []):
                            casts.append(Cast(
                                hash=item.get("hash", ""),
                                author_username=item.get("author", {}).get("username", ""),
                                author_fid=item.get("author", {}).get("fid", 0),
                                text=item.get("text", ""),
                                channel=channel,
                                likes=item.get("reactions", {}).get("likes_count", 0),
                                recasts=item.get("reactions", {}).get("recasts_count", 0),
                                replies=item.get("replies", {}).get("count", 0),
                            ))
                        return casts
                    elif resp.status == 402:
                        logger.debug("Neynar credits exceeded, skipping channel feed")
            except Exception as e:
                logger.error(f"Neynar channel feed error: {e}")

        return []

    async def get_own_casts(self, limit: int = 10) -> List[Cast]:
        """Get our own recent casts via Warpcast public API (always free)."""
        session = await self._get_session()
        try:
            url = f"{WARPCAST_API}/casts"
            params = {"fid": self.fid, "limit": limit}
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

            casts = []
            for item in data.get("result", {}).get("casts", []):
                casts.append(Cast(
                    hash=item.get("hash", ""),
                    author_username=GANJAMON_USERNAME,
                    author_fid=self.fid,
                    text=item.get("text", ""),
                    likes=item.get("reactions", {}).get("count", 0),
                    recasts=item.get("recasts", {}).get("count", 0),
                    replies=item.get("replies", {}).get("count", 0),
                ))
            return casts

        except Exception as e:
            logger.error(f"Warpcast casts error: {e}")
            return []

    async def search_casts(self, query: str, limit: int = 10) -> List[Cast]:
        """Search for casts matching a query."""
        if not self._configured:
            return []

        session = await self._get_session()
        try:
            url = f"{NEYNAR_API}/cast/search"
            params = {"q": query, "limit": limit}
            headers = {"accept": "application/json", "x-api-key": self.neynar_key}
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

            casts = []
            for item in data.get("result", {}).get("casts", []):
                casts.append(Cast(
                    hash=item.get("hash", ""),
                    author_username=item.get("author", {}).get("username", ""),
                    author_fid=item.get("author", {}).get("fid", 0),
                    text=item.get("text", ""),
                    likes=item.get("reactions", {}).get("likes_count", 0),
                ))
            return casts

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_stats(self) -> dict:
        return {
            "configured": self._configured,
            "fid": self.fid,
            "replied_count": len(self._replied_hashes),
            "last_post": self.last_post_time.isoformat() if self.last_post_time else None,
            "last_reply": self.last_reply_time.isoformat() if self.last_reply_time else None,
        }
