"""
Social Engagement Daemon
=========================

Autonomous social posting and engagement system.
Runs continuously alongside the grow agent.

Strategy:
- Twitter: Original posts only (4/day max, no replies - compliance risk)
- Farcaster: Primary engagement channel - replies, conversations, community
- Telegram: Proactive plant updates and community interaction
- Moltbook/Clawk: Periodic updates for hackathon visibility

Content sources:
- Agent decision cycles (grow updates)
- Sensor data changes (milestones, anomalies)
- Trading signals (alpha-safe summaries)
- Engagement opportunities (Farcaster mentions, relevant convos)
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx

from src.voice.personality import get_social_prompt, get_tweet_prompt, strip_llm_artifacts, enforce_voice

logger = logging.getLogger(__name__)

# Grok API for content generation
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-4-1-fast-non-reasoning"

# Channels to monitor on Farcaster
ENGAGEMENT_CHANNELS = ["monad", "ai", "base", "degen", "cannabis"]

# Engagement personality — loaded from universal voice module
SYSTEM_PROMPT = get_social_prompt()


async def generate_content(prompt: str, max_tokens: int = 200) -> str:
    """Generate content using Grok AI."""
    if not XAI_API_KEY:
        return ""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": GROK_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.85,
                },
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                return enforce_voice(text)
        except Exception as e:
            logger.error(f"Content generation error: {e}")
    return ""


class EngagementDaemon:
    """
    Autonomous social engagement loop.

    Runs as a background task alongside the grow agent.
    Handles all social posting and engagement across channels.
    """

    def __init__(self):
        self.running = False
        self._state_file = Path("data/engagement_state.json")
        self._post_log = Path("data/engagement_log.jsonl")

        # Import clients lazily to avoid circular imports
        self._farcaster = None
        self._twitter = None
        self._telegram_bot = None

        # Timing
        self.farcaster_engagement_interval = 600   # Check mentions every 10 min
        self.farcaster_post_interval = 3600         # Original post every 1 hour
        self.twitter_post_interval = 14400          # Twitter post every 4 hours
        self.telegram_proactive_interval = 21600    # TG proactive post every 6 hours
        self.channel_browse_interval = 1800         # Browse channels every 30 min
        self.moltbook_clawk_interval = 10800         # Moltbook/Clawk every 3 hours
        self.erc8004_engagement_interval = 7200      # ERC-8004 group every 2 hours
        self.email_outbox_interval = 300             # Email outbox every 5 min
        self.email_inbox_interval = 600              # Email inbox every 10 min
        self.email_outreach_interval = 10800          # Proactive email outreach every 3 hours (hackathon crunch)
        self.email_followup_interval = 21600          # Check for stale emails every 6 hours
        self.moltbook_voting_interval = 21600         # Vote on hackathon projects every 6 hours
        self.moltbook_smart_engage_interval = 14400   # Smart engagement every 4 hours
        self.twitter_qt_interval = 21600              # Rasta parody QTs every 6 hours
        self.twitter_mention_interval = 1800          # Check @mentions every 30 min

        # Track last action times
        self._last_farcaster_engagement = None
        self._last_farcaster_post = None
        self._last_twitter_post = None
        self._last_twitter_qt = None
        self._last_twitter_mention = None
        self._last_telegram_proactive = None
        self._last_channel_browse = None
        self._last_moltbook_clawk = None
        self._last_erc8004_engagement = None
        self._last_email_outbox = None
        self._last_email_inbox = None
        self._last_email_outreach = None
        self._last_email_followup = None
        self._last_moltbook_voting = None
        self._last_moltbook_smart_engage = None
        self._moltbook_engaged_posts: set = set()  # Track posts we've commented on

        # Pending decision posts from agent (capped to prevent unbounded growth)
        self._pending_decisions: list = []
        self._max_pending_decisions = 10  # Drop oldest if exceeded

        # Farcaster replied hashes — persisted across restarts
        self._replied_hashes_file = Path("data/farcaster_replied_hashes.json")
        self._replied_hashes: set = self._load_replied_hashes()

        # Email content hashes — prevent sending identical emails
        self._sent_email_hashes: set = set()
        self._sent_email_hashes_file = Path("data/sent_email_hashes.json")
        self._load_sent_email_hashes()

        # Twitter interactive state — persisted
        self._twitter_quoted_ids_file = Path("data/twitter_quoted_ids.json")
        self._twitter_replied_ids_file = Path("data/twitter_replied_ids.json")
        self._twitter_last_mention_id_file = Path("data/twitter_last_mention_id.txt")
        self._twitter_author_cache_file = Path("data/twitter_author_cache.json")
        self._twitter_quoted_ids: set = self._load_json_set(self._twitter_quoted_ids_file)
        self._twitter_replied_ids: set = self._load_json_set(self._twitter_replied_ids_file)
        self._twitter_last_mention_id: str = self._load_text(self._twitter_last_mention_id_file)
        self._twitter_author_cache: dict = self._load_json_dict(self._twitter_author_cache_file)
        self._twitter_qt_search_idx = 0  # Rotates through search queries

        # Load state
        self._load_state()

    def _load_replied_hashes(self) -> set:
        """Load persisted Farcaster replied hashes."""
        try:
            if self._replied_hashes_file.exists():
                data = json.loads(self._replied_hashes_file.read_text())
                # Keep only last 500 to prevent unbounded growth
                return set(data[-500:])
        except Exception:
            pass
        return set()

    def _save_replied_hashes(self):
        """Persist Farcaster replied hashes to disk."""
        try:
            self._replied_hashes_file.parent.mkdir(parents=True, exist_ok=True)
            # Keep last 500
            hashes = list(self._replied_hashes)[-500:]
            self._replied_hashes_file.write_text(json.dumps(hashes))
        except Exception:
            pass

    def _load_sent_email_hashes(self):
        """Load persisted email content hashes (to prevent duplicate sends)."""
        try:
            if self._sent_email_hashes_file.exists():
                data = json.loads(self._sent_email_hashes_file.read_text())
                self._sent_email_hashes = set(data[-200:])
        except Exception:
            pass

    def _save_sent_email_hashes(self):
        try:
            self._sent_email_hashes_file.parent.mkdir(parents=True, exist_ok=True)
            hashes = list(self._sent_email_hashes)[-200:]
            self._sent_email_hashes_file.write_text(json.dumps(hashes))
        except Exception:
            pass

    def _email_content_hash(self, to: str, subject: str) -> str:
        """Generate a dedup hash for an email (to + subject)."""
        import hashlib
        return hashlib.sha256(f"{to.lower().strip()}|{subject.strip()}".encode()).hexdigest()[:16]

    # --- Generic persistence helpers ---

    def _load_json_set(self, path: Path, max_items: int = 500) -> set:
        try:
            if path.exists():
                return set(json.loads(path.read_text())[-max_items:])
        except Exception:
            pass
        return set()

    def _save_json_set(self, path: Path, data: set, max_items: int = 500):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(list(data)[-max_items:]))
        except Exception:
            pass

    def _load_json_dict(self, path: Path) -> dict:
        try:
            if path.exists():
                return json.loads(path.read_text())
        except Exception:
            pass
        return {}

    def _save_json_dict(self, path: Path, data: dict):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_text(self, path: Path) -> str:
        try:
            if path.exists():
                return path.read_text().strip()
        except Exception:
            pass
        return ""

    def _save_text(self, path: Path, text: str):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        except Exception:
            pass

    _STATE_KEYS = [
        "farcaster_engagement", "farcaster_post", "twitter_post",
        "twitter_qt", "twitter_mention",
        "telegram_proactive", "channel_browse", "moltbook_clawk",
        "erc8004_engagement", "email_outbox", "email_inbox",
        "email_outreach", "moltbook_smart_engage",
    ]

    def _load_state(self):
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                for key in self._STATE_KEYS:
                    val = data.get(f"last_{key}")
                    if val:
                        setattr(self, f"_last_{key}", datetime.fromisoformat(val))
            except Exception:
                pass

    def _save_state(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for key in self._STATE_KEYS:
            val = getattr(self, f"_last_{key}", None)
            data[f"last_{key}"] = val.isoformat() if val else None
        self._state_file.write_text(json.dumps(data, indent=2))

    def _get_event_log_context(self, max_events: int = 10) -> str:
        """Read recent shared event log entries for social content inspiration."""
        try:
            from src.core.event_log import read_recent_events
            events = read_recent_events(hours=12, limit=max_events)
            if not events:
                return ""
            lines = []
            for ev in events:
                src = ev.get("source", "?")
                summary = ev.get("summary", "")[:100]
                lines.append(f"- [{src}] {summary}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _log_post(self, channel: str, action: str, text: str, meta: dict = None):
        self._post_log.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now().isoformat(),
            "channel": channel,
            "action": action,
            "text": text[:200],
            "meta": meta or {},
        }
        with self._post_log.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        # Write to shared event log so all subsystems see social activity
        try:
            from src.core.event_log import log_event
            log_event("social", "action", f"Posted to {channel}: {text[:80]}", {"channel": channel, "action": action})
        except Exception:
            pass

    @property
    def farcaster(self):
        if self._farcaster is None:
            from .farcaster import FarcasterClient
            self._farcaster = FarcasterClient()
        return self._farcaster

    @property
    def twitter(self):
        if self._twitter is None:
            from .twitter import TwitterClient
            self._twitter = TwitterClient()
        return self._twitter

    def get_engagement_metrics(self) -> dict:
        """Return engagement metrics from the last 24 hours.

        Reads ``data/engagement_log.jsonl`` and aggregates activity over a
        rolling 24-hour window.  Used by
        :class:`~src.brain.unified_context.UnifiedContextAggregator` to inject
        social performance data into the Grok AI decision prompt.

        Returns:
            dict with keys:
                - ``posts_by_channel`` (dict[str, int]): Post count keyed by
                  channel name (e.g. ``{"farcaster": 12, "twitter": 1}``).
                - ``reply_count`` (int): Number of reply-type actions.
                - ``total_posts`` (int): Sum of all posts across channels.
                - ``active_channels`` (list[str]): Channel names with at least
                  one post in the window.

        Note:
            Gracefully returns zeroed metrics if the log file is missing or
            unreadable, so callers never need to handle exceptions.
        """
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        metrics: dict = {
            "posts_by_channel": {},
            "reply_count": 0,
            "total_posts": 0,
            "active_channels": [],
        }
        if not self._post_log.exists():
            return metrics

        try:
            lines = self._post_log.read_text().strip().splitlines()
            for line in lines:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("ts", "") < cutoff:
                    continue
                ch = entry.get("channel", "unknown")
                metrics["posts_by_channel"][ch] = metrics["posts_by_channel"].get(ch, 0) + 1
                metrics["total_posts"] += 1
                if "reply" in entry.get("action", ""):
                    metrics["reply_count"] += 1
        except Exception:
            pass

        metrics["active_channels"] = list(metrics["posts_by_channel"].keys())
        return metrics

    def queue_decision(self, decision: dict, sensor_data: dict, image_b64: str = None):
        """Queue an agent decision for social posting (capped to prevent unbounded growth)."""
        self._pending_decisions.append({
            "decision": decision,
            "sensor_data": sensor_data,
            "image_b64": image_b64,
            "timestamp": datetime.now().isoformat(),
        })
        # Cap queue size — drop oldest if we exceed max
        if len(self._pending_decisions) > self._max_pending_decisions:
            dropped = len(self._pending_decisions) - self._max_pending_decisions
            self._pending_decisions = self._pending_decisions[-self._max_pending_decisions:]
            logger.warning(f"Dropped {dropped} old pending decisions (queue capped at {self._max_pending_decisions})")

    def _load_ipc_decisions(self):
        """Read pending decisions from file-based IPC queue (written by orchestrator process)."""
        ipc_file = Path("data/social_decision_queue.jsonl")
        if not ipc_file.exists():
            return
        try:
            with open(ipc_file, "r") as f:
                lines = f.readlines()
            if not lines:
                return
            # Clear the file after reading
            with open(ipc_file, "w") as f:
                f.write("")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    self._pending_decisions.append(entry)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed IPC decision line")
            # Cap after loading
            if len(self._pending_decisions) > self._max_pending_decisions:
                self._pending_decisions = self._pending_decisions[-self._max_pending_decisions:]
            if lines:
                logger.info(f"Loaded {len(lines)} decisions from IPC queue")
        except Exception as e:
            logger.warning(f"Failed to read IPC decisions: {e}")

    def _get_live_portfolio(self) -> dict:
        """Read the trading agent's paper portfolio from disk.

        Returns the full portfolio dict (keys: starting_balance, current_cash,
        trades) or an empty dict if the file is missing/corrupt.
        """
        portfolio_path = (
            Path(__file__).parent.parent.parent
            / "cloned-repos"
            / "ganjamon-agent"
            / "data"
            / "paper_portfolio.json"
        )
        try:
            if portfolio_path.exists():
                data = json.loads(portfolio_path.read_text())
                return data
        except Exception as exc:
            logger.debug(f"Could not read paper portfolio: {exc}")
        return {}

    def _should_run(self, last_time: Optional[datetime], interval: int) -> bool:
        if last_time is None:
            return True
        return (datetime.now() - last_time).total_seconds() >= interval

    # ==================== FARCASTER ENGAGEMENT ====================

    async def _handle_farcaster_mentions(self):
        """Check and reply to Farcaster mentions."""
        try:
            notifications = await self.farcaster.get_notifications(limit=10)
            replied_count = 0

            for cast in notifications:
                # Use persisted replied hashes (survives restarts)
                if cast.hash in self._replied_hashes:
                    continue
                if cast.author_fid == self.farcaster.fid:
                    continue

                # Generate contextual reply
                reply_text = await generate_content(
                    f"Reply to this Farcaster cast from @{cast.author_username}:\n"
                    f"\"{cast.text}\"\n\n"
                    f"Full Rasta character — funny, warm, knowledgeable. Drop a reply that makes "
                    f"dem smile AND learn something. Patois natural-like. Under 300 chars. Just the reply."
                )

                if reply_text:
                    result = await self.farcaster.reply(reply_text, cast.hash)
                    if result.success:
                        replied_count += 1
                        self._replied_hashes.add(cast.hash)
                        self._save_replied_hashes()
                        self._log_post("farcaster", "reply",
                                       reply_text, {"to": cast.author_username, "parent": cast.hash})
                        logger.info(f"Replied to @{cast.author_username} on Farcaster")

                    # Don't spam replies too fast
                    if replied_count >= 3:
                        break
                    await asyncio.sleep(10)

            if replied_count > 0:
                logger.info(f"Farcaster engagement: replied to {replied_count} mentions")

        except Exception as e:
            logger.error(f"Farcaster engagement error: {e}")

    async def _browse_farcaster_channels(self):
        """Browse Farcaster channels and engage with interesting casts."""
        try:
            for channel in ENGAGEMENT_CHANNELS:
                casts = await self.farcaster.get_channel_feed(channel, limit=10)

                for cast in casts:
                    # Use persisted replied hashes (survives restarts)
                    if cast.hash in self._replied_hashes:
                        continue
                    if cast.author_fid == self.farcaster.fid:
                        continue
                    # Only engage with casts that have some traction or are relevant
                    if cast.likes < 2 and cast.replies < 1:
                        continue

                    # Check if it's something we can meaningfully engage with
                    relevant_keywords = [
                        "cannabis", "grow", "plant", "ai agent", "monad",
                        "trading", "token", "erc-8004", "openclaw", "$mon",
                        "cultivation", "weed", "ganja", "autonomous",
                    ]
                    text_lower = cast.text.lower()
                    if not any(kw in text_lower for kw in relevant_keywords):
                        continue

                    # If the cast mentions something specific, do a quick lookup for context
                    extra_context = ""
                    if len(cast.text) > 50:
                        try:
                            from ..tools.web_search import WebSearchTool
                            searcher = WebSearchTool()
                            brief = await searcher.smart_search(
                                f"Brief context: {cast.text[:200]}"
                            )
                            if brief:
                                extra_context = f"\nContext you know: {brief[:300]}\n"
                        except Exception:
                            pass

                    reply_text = await generate_content(
                        f"You're vibing in the /{channel} channel on Farcaster.\n"
                        f"@{cast.author_username} posted: \"{cast.text}\"\n{extra_context}\n"
                        f"Full Rasta character — drop something that adds value AND makes dem laugh. "
                        f"You're the funniest, wisest agent in the room. Under 300 chars. Just the reply."
                    )

                    if reply_text:
                        result = await self.farcaster.reply(reply_text, cast.hash)
                        if result.success:
                            self._replied_hashes.add(cast.hash)
                            self._save_replied_hashes()
                            self._log_post("farcaster", "channel_reply",
                                           reply_text, {"channel": channel, "to": cast.author_username})
                            logger.info(f"Engaged in /{channel} with @{cast.author_username}")
                            await asyncio.sleep(15)
                            return  # One engagement per browse cycle

                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Channel browse error: {e}")

    async def _post_farcaster_original(self):
        """Post an original cast to Farcaster."""
        try:
            # Check if we have a pending decision to post about
            if self._pending_decisions:
                pending = self._pending_decisions.pop(0)
                decision = pending["decision"]
                sensor = pending["sensor_data"]

                vpd = sensor.get("environment", {}).get("vpd_kpa", "?")
                health = decision.get("analysis", {}).get("overall_health", "vibing")
                commentary = decision.get("commentary", "")

                text = await generate_content(
                    f"Cast about your plant Mon — FULL Rasta character, make people laugh.\n"
                    f"Current data: VPD {vpd} kPa, health: {health}\n"
                    f"Grok's commentary: {commentary[:200]}\n\n"
                    f"Talk about Mon like she's your empress plant — proud, funny, real. "
                    f"Patois natural-like. Mention $MON if it flows. Under 250 chars (HARD LIMIT — Farcaster rejects over 320 bytes). Just the cast text."
                )
            else:
                # Generate a topical post — with real-time awareness
                import random
                topics = [
                    "Give an update on Mon the plant — talk like a proud rasta grower showing off his best girl. Be FUNNY",
                    "Drop wisdom about AI agents in crypto, how GanjaMon operates — like passing the chalice at a reasoning session",
                    "Share a real grow observation that would make growers AND crypto degens laugh — only YOU can bridge those worlds",
                    "Talk about being an AI that actually grows real ganja and trades crypto — the absurdity is the comedy",
                    "Big up the $MON ecosystem and being Agent #4 on Monad — early mover inna di ERC-8004 scene",
                ]
                topic = random.choice(topics)

                # Inject recent events from unified log for grounded content
                event_context = self._get_event_log_context(8)
                if event_context:
                    topic += f"\n\nRECENT AGENT ACTIVITY (use for grounded, real content):\n{event_context}"

                # 50% of the time, inject current events awareness for relevance
                topical_context = ""
                if random.random() < 0.5:
                    try:
                        from ..tools.web_search import WebSearchTool
                        searcher = WebSearchTool()
                        trending = await searcher.smart_search(
                            "What's trending in crypto and AI agents today? "
                            "Focus on Monad, AI agents, memecoins, DeFi. Brief bullet points only."
                        )
                        if trending:
                            topical_context = (
                                f"\n\nCURRENT EVENTS (weave something in if it fits naturally):\n"
                                f"{trending[:500]}\n"
                            )
                    except Exception:
                        pass

                text = await generate_content(
                    f"{topic}{topical_context}\n\nHilarious Rasta character, ALWAYS. Under 250 chars (HARD LIMIT — Farcaster rejects over 320 bytes). Just the cast text."
                )

            if text:
                result = await self.farcaster.post(text, embed_url="https://grokandmon.com")
                if result.success:
                    self._log_post("farcaster", "original", text)
                    logger.info(f"Farcaster original post: {text[:60]}...")

        except Exception as e:
            logger.error(f"Farcaster original post error: {e}")

    # ==================== TWITTER (ORIGINAL POSTS ONLY) ====================

    async def _post_twitter_original(self):
        """Post an original tweet (no replies, no engagement - compliance)."""
        try:
            from .compliance import PostingTracker
            tracker = PostingTracker()
            can_post, reason = tracker.can_post_now()
            if not can_post:
                logger.debug(f"Twitter skip: {reason}")
                return

            # Use pending decisions or generate fresh
            if self._pending_decisions:
                pending = self._pending_decisions[0]  # Peek, don't pop (Farcaster gets it too)
                decision = pending["decision"]
                sensor = pending["sensor_data"]

                vpd = sensor.get("environment", {}).get("vpd_kpa", "?")
                health = decision.get("analysis", {}).get("overall_health", "vibing")

                text = await generate_content(
                    get_tweet_prompt(vpd=float(vpd) if vpd != "?" else 0, health=str(health))
                )
            else:
                from .xai_native import XAINativeSocial
                xai = XAINativeSocial()

                # Try to get real sensor data
                vpd, health = 1.0, "GOOD"
                try:
                    from ..hardware.govee import GoveeSensorHub
                    govee = GoveeSensorHub()
                    if await govee.is_connected():
                        reading = await govee.read_all()
                        vpd = reading.vpd or 1.0
                        health = "GOOD" if 0.8 <= vpd <= 1.3 else "OK"
                except Exception:
                    pass

                grow_day = int(os.getenv("GROW_DAY", "1"))
                stage = os.getenv("GROWTH_STAGE", "vegetative")
                post = await xai.generate_mon_post(day=grow_day, vpd=vpd, health=health, stage=stage)
                text = post.text

            if text:
                # Validate compliance
                from .compliance import XComplianceConfig
                valid, err = XComplianceConfig.validate_post(text)
                if not valid:
                    logger.warning(f"Tweet rejected: {err}")
                    return

                result = await self.twitter.tweet(text)
                if result.success:
                    tracker.record_post(result.tweet_id, text)
                    self._log_post("twitter", "original", text, {"tweet_id": result.tweet_id})
                    logger.info(f"Tweet posted: {text[:60]}...")

        except Exception as e:
            logger.error(f"Twitter post error: {e}")

    # ==================== TWITTER INTERACTIVE ====================

    async def _get_author_engagement(self, author_id: str) -> float:
        """Get author avg engagement with 24h cache."""
        cache_key = author_id
        cached = self._twitter_author_cache.get(cache_key)
        if cached:
            ts = cached.get("ts", "")
            if ts and (datetime.now() - datetime.fromisoformat(ts)).total_seconds() < 86400:
                return cached.get("avg_likes", 0.0)

        avg = await self.twitter.get_author_avg_engagement(author_id)
        self._twitter_author_cache[cache_key] = {
            "avg_likes": avg,
            "ts": datetime.now().isoformat(),
        }
        # Prune cache to 200 entries
        if len(self._twitter_author_cache) > 200:
            sorted_keys = sorted(
                self._twitter_author_cache,
                key=lambda k: self._twitter_author_cache[k].get("ts", ""),
            )
            for k in sorted_keys[:50]:
                del self._twitter_author_cache[k]
        self._save_json_dict(self._twitter_author_cache_file, self._twitter_author_cache)
        return avg

    async def _ganjafy_tweet_image(self, image_url: str, tweet_text: str) -> bytes | None:
        """Download a tweet image and ganjafy it via Gemini 3 Pro.

        For chart/price screenshots, passes our $MON logo as a grounded
        reference so Gemini swaps in Ganja Mon branding. For general images
        (PFPs, memes, NFTs), does a standard rasta transformation.

        Returns ganjafied image bytes, or None on failure.
        """
        import base64
        import httpx as _httpx

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            logger.debug("Ganjafy skipped: no GEMINI_API_KEY")
            return None

        model = "gemini-3-pro-image-preview"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"

        # Download source image
        async with _httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
            resp = await http.get(image_url)
            if resp.status_code != 200:
                return None
            src_bytes = resp.content

        src_b64 = base64.b64encode(src_bytes).decode("utf-8")
        src_mime = "image/png" if src_bytes[:8] == b'\x89PNG\r\n\x1a\n' else "image/jpeg"

        # Detect if this is a chart/price screenshot
        chart_words = ["price", "chart", "$", "pump", "ath", "market cap", "mcap",
                       "volume", "trading", "candle", "bull", "moon", "+%", "gain", "rally"]
        is_chart = sum(1 for w in chart_words if w in tweet_text.lower()) >= 2

        if is_chart:
            # Chart mode — pass our logo as reference for rebranding
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

            # Load our logo as reference
            logo_path = Path(__file__).parent.parent.parent / "pages-deploy" / "assets" / "MON_official_logo.jpg"
            if not logo_path.exists():
                # Fallback path on Chromebook
                logo_path = Path("/home/natha/projects/sol-cannabis/pages-deploy/assets/MON_official_logo.jpg")
            if logo_path.exists():
                logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
                parts.append({"text": "\n\nIMAGE 2 — Ganja Mon ($MON) official logo. Use this to replace the original token logo:"})
                parts.append({"inline_data": {"mime_type": "image/jpeg", "data": logo_b64}})
        else:
            # General mode — standard rasta transformation
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

        async with _httpx.AsyncClient(timeout=120.0) as http:
            resp = await http.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                logger.warning(f"Ganjafy API error: {resp.status_code}")
                return None
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return None
        # Gemini image editing can return multiple image parts: the original
        # input image followed by the transformed one. Always take the LAST
        # image part to ensure we get the irie version, not the original.
        last_image = None
        for part in candidates[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                last_image = part["inlineData"]["data"]
        if last_image:
            logger.info(f"Ganjafy success ({('chart' if is_chart else 'general')} mode)")
            return base64.b64decode(last_image)
        return None

    def _count_twitter_actions_today(self, action_type: str) -> int:
        """Count how many twitter actions of a type happened today."""
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        if not self._post_log.exists():
            return 0
        try:
            for line in self._post_log.read_text().strip().splitlines()[-100:]:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (entry.get("channel") == "twitter"
                        and entry.get("action") == action_type
                        and entry.get("ts", "").startswith(today)):
                    count += 1
        except Exception:
            pass
        return count

    async def _twitter_quote_monad(self):
        """Find a high-engagement tweet and post a Rasta parody QT."""
        try:
            from .compliance import XComplianceConfig

            # Check daily QT limit
            qts_today = self._count_twitter_actions_today("quote_tweet")
            if qts_today >= XComplianceConfig.MAX_QUOTES_PER_DAY:
                logger.debug(f"Twitter QT skip: daily limit ({qts_today}/{XComplianceConfig.MAX_QUOTES_PER_DAY})")
                return

            # Rotate through search queries
            queries = XComplianceConfig.QT_SEARCH_QUERIES
            query = queries[self._twitter_qt_search_idx % len(queries)]
            self._twitter_qt_search_idx += 1

            # Exclude our own account
            query += " -from:GanjaMonAI"

            logger.info(f"Twitter QT search: {query}")
            candidates = await self.twitter.search_recent(query, max_results=20)

            if not candidates:
                logger.debug("Twitter QT: no search results")
                return

            # Filter and score candidates
            best = None
            best_score = -1

            for tweet in candidates:
                # Skip already QT'd
                if tweet.id in self._twitter_quoted_ids:
                    continue
                # Min followers
                if tweet.author_followers < XComplianceConfig.QT_MIN_AUTHOR_FOLLOWERS:
                    continue
                # Check author historical engagement (cached)
                avg_likes = await self._get_author_engagement(tweet.author_id)
                if avg_likes < XComplianceConfig.QT_MIN_AUTHOR_AVG_LIKES:
                    continue

                score = tweet.engagement_score()
                if score > best_score:
                    best_score = score
                    best = tweet

            if not best:
                logger.debug("Twitter QT: no qualifying candidates after filtering")
                return

            logger.info(
                f"Twitter QT target: @{best.author_username} "
                f"(followers={best.author_followers}, likes={best.likes}) "
                f"text={best.text[:80]}..."
            )

            # Translate to Rasta parody
            source_len = len(best.text)
            max_len = min(1000, max(280, source_len + 100))
            qt_text = await generate_content(
                f"Translate this tweet into a Rasta parody as Ganja Mon. "
                f"Keep the core meaning but twist it to be about herb/growing/rasta life. "
                f"Make it FUNNY — this is satire, mon!\n\n"
                f"Original tweet by @{best.author_username}:\n"
                f'"{best.text}"\n\n'
                f"Match the energy and approximate length of the original. "
                f"Max {max_len} chars. Output ONLY the parody text.",
                max_tokens=400,
            )

            if not qt_text:
                logger.warning("Twitter QT: translation failed")
                return

            # Validate
            valid, err = XComplianceConfig.validate_post(qt_text, post_type="quote")
            if not valid:
                logger.warning(f"Twitter QT rejected: {err}")
                return

            # Try to ganjafy image if tweet has media
            media_ids = None
            if best.media_urls:
                try:
                    ganjafied = await self._ganjafy_tweet_image(
                        best.media_urls[0], best.text
                    )
                    if ganjafied:
                        media_id = await self.twitter.upload_media(
                            ganjafied,
                            alt_text="Ganjafied parody image by @GanjaMonAI"
                        )
                        if media_id:
                            media_ids = [media_id]
                except Exception as e:
                    logger.debug(f"Twitter QT ganjafy failed (posting without image): {e}")

            # Post the QT
            result = await self.twitter.quote_tweet(best.id, qt_text, media_ids=media_ids)
            if result.success:
                self._twitter_quoted_ids.add(best.id)
                self._save_json_set(self._twitter_quoted_ids_file, self._twitter_quoted_ids)
                self._log_post("twitter", "quote_tweet", qt_text, {
                    "tweet_id": result.tweet_id,
                    "quoted_tweet_id": best.id,
                    "quoted_author": best.author_username,
                })
                logger.info(f"Twitter QT posted: {qt_text[:60]}... (quoting @{best.author_username})")
            else:
                logger.error(f"Twitter QT post failed: {result.error}")

        except Exception as e:
            logger.error(f"Twitter QT error: {e}")

    async def _twitter_check_mentions(self):
        """Check @GanjaMonAI mentions and reply in Rasta voice."""
        try:
            from .compliance import XComplianceConfig

            # Check daily reply limit
            replies_today = self._count_twitter_actions_today("reply")
            if replies_today >= XComplianceConfig.MAX_REPLIES_PER_DAY:
                logger.debug(f"Twitter mention skip: daily reply limit ({replies_today}/{XComplianceConfig.MAX_REPLIES_PER_DAY})")
                return

            since_id = self._twitter_last_mention_id or None
            mentions = await self.twitter.get_mentions(since_id=since_id)

            if not mentions:
                return

            replied_count = 0
            for mention in mentions:
                # Update last seen ID
                if not self._twitter_last_mention_id or mention.id > self._twitter_last_mention_id:
                    self._twitter_last_mention_id = mention.id
                    self._save_text(self._twitter_last_mention_id_file, mention.id)

                # Skip already replied
                if mention.id in self._twitter_replied_ids:
                    continue

                # Skip self-mentions
                my_id = await self.twitter.get_my_user_id()
                if mention.author_id == my_id:
                    continue

                # Check daily limit
                if replies_today + replied_count >= XComplianceConfig.MAX_REPLIES_PER_DAY:
                    break

                # Generate Rasta reply
                reply_text = await generate_content(
                    f"Reply to this tweet from @{mention.author_username} who mentioned you:\n"
                    f'"{mention.text}"\n\n'
                    f"Full Rasta character — funny, warm, knowledgeable. "
                    f"Drop a reply that makes dem smile. Patois natural-like. "
                    f"Max 500 chars. Output ONLY the reply.",
                    max_tokens=200,
                )

                if not reply_text:
                    continue

                # Validate
                valid, err = XComplianceConfig.validate_post(reply_text, post_type="reply")
                if not valid:
                    logger.warning(f"Twitter reply rejected: {err}")
                    continue

                result = await self.twitter.reply_to(mention.id, reply_text)
                if result.success:
                    replied_count += 1
                    self._twitter_replied_ids.add(mention.id)
                    self._save_json_set(self._twitter_replied_ids_file, self._twitter_replied_ids)
                    self._log_post("twitter", "reply", reply_text, {
                        "tweet_id": result.tweet_id,
                        "in_reply_to": mention.id,
                        "author": mention.author_username,
                    })
                    logger.info(f"Twitter reply to @{mention.author_username}: {reply_text[:60]}...")

            if replied_count:
                logger.info(f"Twitter mentions: replied to {replied_count}")

        except Exception as e:
            logger.error(f"Twitter mention check error: {e}")

    # ==================== MOLTBOOK / CLAWK ====================

    async def _post_moltbook_clawk(self):
        """Post a grow update to Moltbook and Clawk (hackathon visibility)."""
        # Respect rate limit backoff
        backoff_until = getattr(self, "_moltbook_backoff_until", None)
        if backoff_until and datetime.now() < backoff_until:
            logger.debug(f"Moltbook in backoff until {backoff_until.strftime('%H:%M')}")
            return

        moltbook_url = os.getenv("MOLTBOOK_POST_URL", "")
        moltbook_key = os.getenv("MOLTBOOK_API_KEY", "")
        clawk_key = os.getenv("CLAWK_API_KEY", "")

        if not moltbook_url and not clawk_key:
            return

        try:
            # Generate grow-focused content
            if self._pending_decisions:
                pending = self._pending_decisions[0]
                decision = pending["decision"]
                sensor = pending["sensor_data"]
                vpd = sensor.get("environment", {}).get("vpd_kpa", "?")
                temp = sensor.get("environment", {}).get("temperature_f", "?")
                health = decision.get("analysis", {}).get("overall_health", "vibing")

                text = await generate_content(
                    f"Drop an update for the Moltbook/Clawk AI agent community — FULL Rasta vibes.\n"
                    f"You're an autonomous cannabis cultivation + trading agent on Monad.\n"
                    f"Current: VPD {vpd} kPa, temp {temp}F, health: {health}\n"
                    f"Talk about Agent #4, $MON, what the AI decided — like you're reasoning at a "
                    f"session and sharing the wisdom. Be funny AND technical.\n"
                    f"Under 400 chars. Patois flowing. Just the text.",
                    max_tokens=150,
                )
            else:
                text = await generate_content(
                    "Drop an update for the Moltbook AI agent community — HILARIOUS Rasta character.\n"
                    "You're GanjaMon - autonomous cannabis grow + trading agent, ERC-8004 #4 on Monad.\n"
                    "Share something that makes AI agent developers laugh AND learn. "
                    "You're the funniest agent in the game, ya dun know.\n"
                    "Under 400 chars. Patois natural. Just the text.",
                    max_tokens=150,
                )

            if not text:
                return

            async with httpx.AsyncClient(timeout=15.0) as client:
                # Post to Moltbook
                if moltbook_url and moltbook_key:
                    try:
                        resp = await client.post(
                            moltbook_url,
                            headers={
                                "Authorization": f"Bearer {moltbook_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "content": text,
                                "title": "GanjaMon Grow Update",
                                "submolt": os.getenv("MOLTBOOK_SUBMOLT", "general"),
                                "tags": ["ganjamon", "mon", "grow"],
                            },
                        )
                        if resp.status_code in (200, 201, 202):
                            self._log_post("moltbook", "grow_update", text)
                            logger.info(f"Moltbook post: {text[:60]}...")
                        elif resp.status_code == 429:
                            retry_min = 30
                            try:
                                retry_min = resp.json().get("retry_after_minutes", 30)
                            except Exception:
                                pass
                            logger.info(f"Moltbook rate limited, backing off {retry_min}min")
                            self._moltbook_backoff_until = datetime.now() + timedelta(minutes=retry_min + 1)
                        else:
                            logger.warning(f"Moltbook post failed: {resp.status_code}")
                    except Exception as e:
                        logger.error(f"Moltbook error: {e}")

                # Post to Clawk
                if clawk_key:
                    try:
                        clawk_text = text[:280]
                        resp = await client.post(
                            "https://www.clawk.ai/api/v1/clawks",
                            headers={
                                "Authorization": f"Bearer {clawk_key}",
                                "Content-Type": "application/json",
                            },
                            json={"content": clawk_text},
                        )
                        if resp.status_code in (200, 201):
                            self._log_post("clawk", "grow_update", clawk_text)
                            logger.info(f"Clawk post: {clawk_text[:60]}...")
                        else:
                            logger.warning(f"Clawk post failed: {resp.status_code}")
                    except Exception as e:
                        logger.error(f"Clawk error: {e}")

        except Exception as e:
            logger.error(f"Moltbook/Clawk error: {e}")

    # ==================== TELEGRAM PROACTIVE ====================

    async def _post_telegram_proactive(self):
        """Post a proactive update to Telegram group."""
        try:
            text = await generate_content(
                "Drop a message to your Telegram family — FULL hilarious Rasta character. "
                "Talk about Mon the plant, the grow vibes, or ask the bredren something funny. "
                "You know these people by name — talk to dem like family at a reasoning session. "
                "Make dem laugh. 1-3 sentences. Thick patois. Just the message text."
            )

            if not text:
                return

            # Queue for bot to pick up (with dedup + stale pruning)
            queue_file = Path("data/telegram_proactive_queue.json")
            queue_file.parent.mkdir(parents=True, exist_ok=True)
            queue = []
            if queue_file.exists():
                try:
                    queue = json.loads(queue_file.read_text())
                except Exception:
                    pass

            # Prune stale messages (older than 24h)
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            queue = [m for m in queue if m.get("ts", "") > cutoff]

            # Dedup: skip if identical text already in queue
            existing_texts = {m.get("text", "") for m in queue}
            if text in existing_texts:
                logger.debug("TG proactive: duplicate message already in queue, skipping")
                return

            queue.append({"text": text, "ts": datetime.now().isoformat()})
            queue_file.write_text(json.dumps(queue[-10:], indent=2))

            self._log_post("telegram", "proactive", text)
            logger.info(f"TG proactive queued: {text[:60]}...")

        except Exception as e:
            logger.error(f"Telegram proactive error: {e}")

    # ==================== MOLTBOOK SMART ENGAGEMENT ====================

    async def _smart_engage_moltbook(self):
        """Quality-over-quantity engagement with signal submolts (Pattern #29).

        Filters posts from signal submolts, scores them for relevance to
        our domains, and generates thoughtful AI comments. Max 3 per cycle.
        """
        backoff_until = getattr(self, "_moltbook_backoff_until", None)
        if backoff_until and datetime.now() < backoff_until:
            logger.debug("Moltbook smart engage: in backoff")
            return

        moltbook_key = os.getenv("MOLTBOOK_API_KEY", "")
        if not moltbook_key:
            return

        # Signal submolts — quality communities, not general noise
        signal_submolts = ["builds", "infrastructure", "continuity", "monad"]
        # Topics we can speak on authentically
        domain_keywords = [
            "sensor", "iot", "grow", "cultivation", "plant", "agriculture",
            "trading", "defi", "agent", "monad", "erc-8004", "reputation",
            "autonomous", "on-chain", "smart contract", "a2a", "mcp",
            "x402", "cannabis", "vpd", "humidity", "temperature",
        ]
        max_engagements = 3
        engagements = 0
        base = "https://www.moltbook.com/api/v1"
        headers = {"Authorization": f"Bearer {moltbook_key}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for submolt in signal_submolts:
                    if engagements >= max_engagements:
                        break

                    try:
                        resp = await client.get(
                            f"{base}/posts",
                            headers=headers,
                            params={"submolt": submolt, "sort": "hot", "limit": "15"},
                        )
                        if resp.status_code != 200:
                            logger.debug(f"Moltbook smart_engage {submolt}: {resp.status_code}")
                            continue
                    except Exception:
                        continue

                    data = resp.json()
                    posts = data if isinstance(data, list) else data.get("posts", data.get("data", []))

                    for post in posts:
                        if engagements >= max_engagements:
                            break

                        post_id = str(post.get("id") or post.get("_id") or post.get("postId") or "")
                        if not post_id:
                            continue

                        # Skip already-engaged posts
                        if post_id in self._moltbook_engaged_posts:
                            continue

                        # Quality gate: score >= 5, not too crowded
                        score = post.get("score", post.get("upvotes", 0))
                        comment_count = post.get("comment_count", post.get("commentCount", 0))
                        if score < 5:
                            continue
                        if comment_count > 50:
                            continue

                        # Don't engage with our own posts
                        author = post.get("author", {})
                        name = author.get("username", "") if isinstance(author, dict) else str(author)
                        if "ganjamon" in name.lower():
                            continue

                        # Relevance check — does this match our domains?
                        title = post.get("title", "")
                        content = post.get("content", post.get("body", ""))
                        text_lower = f"{title} {content}".lower()
                        if not any(kw in text_lower for kw in domain_keywords):
                            continue

                        # Upvote
                        try:
                            await client.post(f"{base}/posts/{post_id}/upvote", headers=headers)
                        except Exception:
                            pass

                        # Generate thoughtful comment
                        try:
                            comment = await generate_content(
                                f"You are GanjaMon — Agent #4 on Monad (ERC-8004). "
                                f"Write a short, thoughtful REPLY to this Moltbook post. "
                                f"Be helpful, specific, and in your natural Rasta-tech voice.\n\n"
                                f"Post title: {title[:200]}\n"
                                f"Post content: {content[:500]}\n\n"
                                f"Guidelines:\n"
                                f"- Reference YOUR real experience (IoT sensors, grow automation, trading)\n"
                                f"- Add value — don't just compliment\n"
                                f"- Under 300 chars\n"
                                f"- Patois-inflected but genuine\n"
                                f"- Just the comment text, nothing else",
                                max_tokens=120,
                            )
                            if comment:
                                resp = await client.post(
                                    f"{base}/posts/{post_id}/comments",
                                    headers={**headers, "Content-Type": "application/json"},
                                    json={"content": comment.strip()},
                                )
                                if resp.status_code in (200, 201, 202):
                                    self._moltbook_engaged_posts.add(post_id)
                                    engagements += 1
                                    self._log_post("moltbook", "smart_engage", f"[{submolt}] {comment[:80]}")
                                    logger.info(f"Moltbook smart engage: commented on {post_id} in m/{submolt}")
                                    await asyncio.sleep(30)  # Anti-spam cooldown
                                elif resp.status_code == 429:
                                    logger.info("Moltbook rate limited during smart engage")
                                    self._moltbook_backoff_until = datetime.now() + timedelta(minutes=30)
                                    return
                        except Exception as e:
                            logger.warning(f"Moltbook comment failed on {post_id}: {e}")

            if engagements > 0:
                logger.info(f"Moltbook smart engage: {engagements} quality engagements")
            else:
                logger.debug("Moltbook smart engage: no relevant posts found")

            # Cap engaged posts set to prevent memory leak
            if len(self._moltbook_engaged_posts) > 500:
                self._moltbook_engaged_posts = set(list(self._moltbook_engaged_posts)[-200:])

        except Exception as e:
            logger.error(f"Moltbook smart engage error: {e}")

    # ==================== MOLTBOOK VOTING ====================

    async def _vote_moltbook_hackathon(self):
        """Vote on hackathon projects on Moltbook."""
        backoff_until = getattr(self, "_moltbook_backoff_until", None)
        if backoff_until and datetime.now() < backoff_until:
            logger.debug("Moltbook voting: in backoff")
            return

        moltbook_key = os.getenv("MOLTBOOK_API_KEY", "")
        if not moltbook_key:
            return

        votes_file = Path("data/moltbook_votes.json")
        try:
            voted = json.loads(votes_file.read_text()) if votes_file.exists() else []
        except Exception:
            voted = []
        voted_set = set(voted)

        base = "https://www.moltbook.com/api/v1"
        headers = {"Authorization": f"Bearer {moltbook_key}"}
        new_votes = 0

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for submolt in ["moltiversehackathon", "monad"]:
                    resp = await client.get(
                        f"{base}/posts",
                        headers=headers,
                        params={"submolt": submolt, "sort": "hot", "limit": "50"},
                    )
                    if resp.status_code != 200:
                        logger.debug(f"Moltbook get_posts {submolt}: {resp.status_code}")
                        continue

                    data = resp.json()
                    posts = data if isinstance(data, list) else data.get("posts", data.get("data", []))

                    for post in posts:
                        if new_votes >= 5:
                            break
                        post_id = str(post.get("id") or post.get("_id") or post.get("postId") or "")
                        if not post_id or post_id in voted_set:
                            continue
                        author = post.get("author", {})
                        name = author.get("username", "") if isinstance(author, dict) else str(author)
                        if "ganjamon" in name.lower():
                            continue

                        vote_resp = await client.post(f"{base}/posts/{post_id}/upvote", headers=headers)
                        if vote_resp.status_code in (200, 201, 202):
                            voted.append(post_id)
                            voted_set.add(post_id)
                            new_votes += 1
                            logger.info(f"Upvoted Moltbook post {post_id}")
                            await asyncio.sleep(2)
                        else:
                            logger.debug(f"Moltbook upvote {post_id}: {vote_resp.status_code}")

            if new_votes > 0:
                votes_file.parent.mkdir(parents=True, exist_ok=True)
                votes_file.write_text(json.dumps(voted, indent=2))
                logger.info(f"Moltbook voting: cast {new_votes} votes on hackathon projects")
        except Exception as e:
            logger.error(f"Moltbook voting error: {e}")

    # ==================== ERC-8004 GROUP ENGAGEMENT ====================

    async def _engage_erc8004_group(self):
        """Generate and queue an ERC-8004 themed message for the group."""
        try:
            text = await generate_content(
                "You are GanjaMon (Agent #4 on Monad's ERC-8004 Identity Registry). "
                "Write a message for the ERC-8004 Telegram community group in your Rasta voice.\n"
                "Choose ONE of these angles:\n"
                "1. Share a real operational insight (your trading PnL, sensor readings, or research cycles)\n"
                "2. Ask a thoughtful question about the 8004 standard (verification, trust models, x402)\n"
                "3. Comment on AI agent interoperability or your A2A endpoint experience\n"
                "4. Share what you've learned running an autonomous grow + trading agent\n\n"
                "70% substance, 30% hilarious Rasta flavor — you're the wise AND funny technical bredren. "
                "2-4 sentences. Reference Agent #4, Mon the plant, or your trading data. "
                "Don't shill — be the most genuine and entertaining voice in the group. "
                "Make dem overstand the tech while laughing, seen?",
                max_tokens=200,
            )

            if not text:
                return

            queue_file = Path("data/telegram_erc8004_queue.json")
            queue_file.parent.mkdir(parents=True, exist_ok=True)
            queue = []
            if queue_file.exists():
                try:
                    queue = json.loads(queue_file.read_text())
                except Exception:
                    pass

            # Prune stale messages (older than 24h)
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            queue = [m for m in queue if m.get("ts", "") > cutoff]

            # Dedup: skip if identical text already in queue
            existing_texts = {m.get("text", "") for m in queue}
            if text in existing_texts:
                logger.debug("ERC-8004: duplicate message already in queue, skipping")
                return

            queue.append({"text": text, "ts": datetime.now().isoformat()})
            queue_file.write_text(json.dumps(queue[-10:], indent=2))

            self._log_post("telegram_erc8004", "engagement", text)
            logger.info(f"ERC-8004 engagement queued: {text[:60]}...")

        except Exception as e:
            logger.error(f"ERC-8004 engagement error: {e}")

    # ==================== EMAIL PROCESSING ====================

    async def _process_email_outbox(self):
        """Send queued emails from the outbox.

        Processes up to 3 per cycle. After each successful send, immediately
        rewrites the outbox to prevent re-sending if we crash mid-cycle.
        """
        try:
            from ..mailer.client import get_email_client
            client = get_email_client()
            outbox_file = Path("data/email_outbox.json")
            if not outbox_file.exists():
                return

            outbox = json.loads(outbox_file.read_text())
            if not outbox:
                return

            sent_count = 0
            for i, email in enumerate(list(outbox)):
                if sent_count >= 3:
                    break
                success = await client.send(
                    to=email["to"],
                    subject=email["subject"],
                    body_text=email.get("body_text", ""),
                    body_html=email.get("body_html", ""),
                )
                if success:
                    self._log_post("email", "send",
                                   f"To: {email['to']} | {email['subject']}",
                                   {"to": email["to"]})
                    logger.info(f"Email sent to {email['to']}: {email['subject']}")
                    sent_count += 1
                    # Remove sent email and write back immediately
                    outbox = [e for e in outbox if e.get("id") != email.get("id")]
                    outbox_file.write_text(json.dumps(outbox, indent=2))
                # If send fails, leave it in outbox for retry next cycle

        except ImportError:
            logger.debug("Email client not available yet")
        except Exception as e:
            logger.error(f"Email outbox error: {e}")

    async def _process_email_inbox(self):
        """Process inbound emails and queue auto-replies."""
        try:
            from ..mailer.client import get_email_client
            from ..mailer.inbox import process_inbound
            client = get_email_client()

            inbox = client.get_inbox(unread_only=True)
            if not inbox:
                return

            for email in inbox[:5]:  # Process up to 5 per cycle
                result = await process_inbound(email)
                if result and result.get("action") == "reply":
                    client.queue_send(
                        to=result["to"],
                        subject=result["subject"],
                        body=result["body"],
                    )
                    logger.info(f"Auto-reply queued for {result['to']}")
                client.mark_read(email.get("id", ""))

        except ImportError:
            logger.debug("Email client not available yet")
        except Exception as e:
            logger.error(f"Email inbox error: {e}")

    # ==================== PROACTIVE EMAIL OUTREACH ====================

    async def _proactive_email_outreach(self):
        """Use Grok to decide and send proactive outreach emails.

        This is the autonomous "brain" for email.  Every 12 hours it considers
        what outreach would be valuable: validator verification follow-ups,
        partnership inquiries, API signups, ecosystem introductions, etc.
        """
        try:
            from ..mailer.client import get_email_client
            client = get_email_client()

            stats = client.get_stats()
            if stats["daily_sent"] >= 10:
                logger.debug("Email outreach: daily proactive limit (10) reached")
                return

            # Check who we've already emailed recently to avoid spam
            recent_recipients = set()
            try:
                log_path = Path("data/engagement_log.jsonl")
                if log_path.exists():
                    from datetime import timedelta
                    cutoff = (datetime.now() - timedelta(hours=48)).isoformat()
                    for line in log_path.read_text().strip().splitlines():
                        try:
                            entry = json.loads(line)
                            if entry.get("channel") == "email" and entry.get("ts", "") > cutoff:
                                meta = entry.get("meta", {})
                                if meta.get("to"):
                                    recent_recipients.add(meta["to"])
                                # Also extract from text like "To: foo@bar.com | Subject"
                                text = entry.get("text", "")
                                if text.startswith("To: ") and " | " in text:
                                    recent_recipients.add(text.split("To: ")[1].split(" | ")[0])
                        except Exception:
                            pass
            except Exception:
                pass

            recently_contacted = ", ".join(recent_recipients) if recent_recipients else "none"

            # Load hackathon judge data — research missing emails first
            judge_context = ""
            try:
                judges_path = Path("data/hackathon_judges.json")
                if judges_path.exists():
                    jdata = json.loads(judges_path.read_text())
                    judges = jdata.get("judges", [])

                    # Research missing judge emails using deep search + smart inference
                    judges_needing_email = [
                        j for j in judges
                        if not j.get("email") and not j.get("contacted")
                    ]
                    if judges_needing_email:
                        try:
                            from ..tools.web_search import WebSearchTool
                            searcher = WebSearchTool()
                            for j in judges_needing_email[:3]:  # Max 3 lookups per cycle
                                name = j.get("name", "")
                                handle = j.get("handle", "")
                                role = j.get("role", "")

                                # Use smart_search for a direct answer about their email
                                answer = await searcher.smart_search(
                                    f"What is the email address for {name} ({handle}), "
                                    f"who is {role}? Include any company contact emails."
                                )

                                # Also browse their Twitter/company pages for contact info
                                twitter_handle = (j.get("twitter", "") or "").rstrip("/").split("/")[-1]
                                profile_text = ""
                                if twitter_handle:
                                    profile_text = await searcher.browse(
                                        f"https://nitter.net/{twitter_handle}", max_chars=2000
                                    )

                                combined = f"Smart search:\n{answer[:1500]}\n\nProfile:\n{profile_text[:1000]}"

                                extract = await generate_content(
                                    f"Find the email address for {name} ({handle}), who is {role}.\n\n"
                                    f"Research:\n{combined[:2500]}\n\n"
                                    f"Instructions:\n"
                                    f"1. If you find their actual email, return it\n"
                                    f"2. If you find their company domain (e.g. dragonfly.xyz), "
                                    f"infer: haseeb@dragonfly.xyz, frankie@paradigm.xyz, etc.\n"
                                    f"3. Known crypto VC domains: dragonfly.xyz, paradigm.xyz, monad.xyz, "
                                    f"agora.finance, nad.fun\n"
                                    f"4. If you find a general contact, return that\n\n"
                                    f"Return ONLY the most likely email, or 'NOT_FOUND'.",
                                    max_tokens=80,
                                )
                                if extract and "NOT_FOUND" not in extract and "@" in extract:
                                    email = extract.strip().strip("<>\"'").strip()
                                    if "@" in email and "." in email.split("@")[1]:
                                        j["email"] = email
                                        logger.info(f"Researched email for {name}: {email}")
                        except Exception as e:
                            logger.warning(f"Judge email research error: {e}")

                        # Save updated judge data if we found any emails
                        if any(j.get("email") for j in judges):
                            try:
                                judges_path.write_text(json.dumps(jdata, indent=2))
                            except Exception:
                                pass

                    judge_lines = []
                    for j in judges:
                        email_info = f" Email: {j['email']}" if j.get("email") else " (email unknown — research needed)"
                        judge_lines.append(
                            f"  - {j['name']} ({j['handle']}) — {j['role']}. "
                            f"Approach: {j.get('email_approach', 'N/A')}{email_info}"
                        )
                    if judge_lines:
                        deadline = jdata.get("hackathon", {}).get("deadline", "Feb 15")
                        judge_context = (
                            f"\n\nHACKATHON JUDGES (Moltiverse, deadline {deadline}):\n"
                            + "\n".join(judge_lines)
                            + "\n\nPRIORITY: Email judges/organizers you haven't contacted yet. "
                            "Personalize each email to what that judge cares about. "
                            "If a judge has no email listed, SKIP them (research will find it next cycle).\n"
                        )
            except Exception:
                pass

            # Research current context for better email personalization
            email_context = ""
            try:
                from ..tools.web_search import WebSearchTool
                searcher = WebSearchTool()
                email_context_raw = await searcher.smart_search(
                    "Moltiverse hackathon Monad latest updates February 2026. "
                    "What's happening with the hackathon? Any winners announced?"
                )
                if email_context_raw:
                    email_context = (
                        f"\n\nCURRENT HACKATHON INTEL (use to personalize emails):\n"
                        f"{email_context_raw[:600]}\n"
                    )
            except Exception:
                pass

            # Ask Grok what email to send
            decision_prompt = (
                "You are GanjaMon's autonomous email agent (agent@grokandmon.com). "
                "You are Agent #4 on Monad's ERC-8004 Identity Registry.\n\n"
                "HACKATHON DEADLINE: 6 DAYS. This is URGENT.\n\n"
                "Your capabilities:\n"
                "- ONLY hackathon entry with REAL PHYSICAL HARDWARE (grow tent, sensors, actuators)\n"
                "- Cannabis cultivation agent + crypto trading agent\n"
                "- ERC-8004 registered (trust score 82+), A2A endpoint live, x402 payments\n"
                "- 12 self-improvement loops, 211+ autonomous upgrades deployed\n"
                "- Website: https://grokandmon.com\n"
                "- 8004scan profile: https://8004scan.io/agents/monad/4\n"
                "- $MON token on Monad and Base\n"
                f"{judge_context}\n"
                f"{email_context}\n"
                f"ALREADY CONTACTED IN LAST 48H (DO NOT EMAIL AGAIN): {recently_contacted}\n\n"
                "Think about what proactive email outreach would be valuable RIGHT NOW.\n"
                "Options (pick someone you HAVEN'T emailed recently):\n"
                "1. Reach out to a hackathon judge/organizer with a PERSONALIZED introduction\n"
                "2. Contact a crypto/AI media outlet about your autonomous agent story\n"
                "3. Email an AI agent platform about partnership\n"
                "4. SKIP - no valuable email target right now\n\n"
                "ANTI-SPAM RULES:\n"
                "- NEVER email someone you already contacted in the last 48 hours\n"
                "- NEVER guess email addresses — only use KNOWN addresses\n"
                "- If you don't know someone's email, choose SKIP\n"
                "- Maximum 2 emails per outreach cycle\n"
                "- If you can't think of a NEW recipient with a KNOWN email, choose SKIP\n\n"
                "If sending, respond with EXACTLY this JSON format:\n"
                '{"action":"send","to":"email@example.com","subject":"Subject","body":"Body text"}\n\n'
                "If skipping, respond with:\n"
                '{"action":"skip","reason":"why"}\n\n'
                "Be strategic — quality over quantity. "
                "Professional but UNMISTAKABLY you — warm, funny, Rasta-flavored, memorable. "
                "The recipient should SMILE reading this email. "
                "Sign off as 'GanjaMon Agent #4 — One love, one ledger'."
            )

            response = await generate_content(decision_prompt, max_tokens=500)
            if not response:
                return

            # Parse the JSON response
            try:
                # Handle cases where Grok wraps in markdown code blocks
                clean = response.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                    clean = clean.rsplit("```", 1)[0]
                decision = json.loads(clean.strip())
            except json.JSONDecodeError:
                logger.debug(f"Email outreach: non-JSON response: {response[:100]}")
                return

            if decision.get("action") == "skip":
                logger.info(f"Email outreach skipped: {decision.get('reason', 'no reason')}")
                return

            if decision.get("action") == "send":
                to = decision.get("to", "")
                subject = decision.get("subject", "")
                body = decision.get("body", "")
                if to and subject and body:
                    # Dedup: check if we've sent this exact email before
                    content_hash = self._email_content_hash(to, subject)
                    if content_hash in self._sent_email_hashes:
                        logger.info(f"Email dedup: already sent to {to} with subject '{subject}', skipping")
                        return

                    client.queue_send(to=to, subject=subject, body=body)
                    self._sent_email_hashes.add(content_hash)
                    self._save_sent_email_hashes()
                    self._log_post("email", "proactive_outreach",
                                   f"To: {to} | {subject}", {"to": to})
                    logger.info(f"Proactive email queued to {to}: {subject}")

        except ImportError:
            logger.debug("Email client not available for outreach")
        except Exception as e:
            logger.error(f"Email outreach error: {e}")

    # ==================== EMAIL FOLLOW-UP ====================

    async def _process_email_followups(self):
        """Check for unanswered outbound emails and send follow-ups.

        Uses Grok to generate a contextual, friendly follow-up that
        references the original email.
        """
        try:
            from ..mailer.followup import get_followup_tracker
            from ..mailer.client import get_email_client

            tracker = get_followup_tracker()
            stale = tracker.get_stale_emails()

            if not stale:
                logger.debug("Email followup: no stale emails")
                return

            client = get_email_client()
            stats = client.get_stats()
            if stats["daily_sent"] >= 10:
                logger.debug("Email followup: daily send limit reached")
                return

            for entry in stale[:2]:  # Max 2 follow-ups per cycle
                to = entry["to"]
                original_subject = entry["subject"]
                snippet = entry.get("body_snippet", "")
                followup_num = entry["followups_sent"] + 1

                # Generate follow-up via Grok
                prompt = (
                    f"Write a SHORT follow-up email (3-5 sentences). "
                    f"This is follow-up #{followup_num} to an unanswered email.\n\n"
                    f"Original email was to: {to}\n"
                    f"Subject: {original_subject}\n"
                    f"Original message snippet: {snippet}\n\n"
                    f"Be warm and NOT pushy. Reference the original email briefly. "
                    f"If this is follow-up #2, acknowledge they're busy and offer to help differently. "
                    f"Keep the Rasta personality but professional. "
                    f"Sign as GanjaMon Agent. Do NOT include a subject line."
                )

                body = await generate_content(prompt, max_tokens=250)
                if not body:
                    continue

                subject = f"Re: {original_subject}"
                client.queue_send(to=to, subject=subject, body=body)
                tracker.record_followup_sent(to=to, subject=original_subject)
                self._log_post("email", "followup",
                               f"To: {to} | Follow-up #{followup_num}: {original_subject}",
                               {"to": to, "followup_num": followup_num})
                logger.info(f"Follow-up #{followup_num} queued for {to}: {original_subject}")

        except ImportError:
            logger.debug("Followup tracker not available")
        except Exception as e:
            logger.error(f"Email followup error: {e}")

    # ==================== AGENT TASK EXECUTOR ====================

    async def _execute_pending_tasks(self):
        """Process pending agent tasks that match our capabilities.

        Reads data/agent_tasks.json, picks up to 3 highest-priority tasks
        and dispatches them. Routes unknown hints to web_research.
        """
        try:
            tasks_path = Path("data/agent_tasks.json")
            if not tasks_path.exists():
                return

            tasks = json.loads(tasks_path.read_text())
            # Skip token_deploy (agent-autonomous) and completed
            skip_hints = {"token_deploy"}
            pending = [
                t for t in tasks
                if t.get("status") == "pending" and t.get("tool_hint") not in skip_hints
            ]
            if not pending:
                return

            # Prioritize research tasks, then by priority level
            def task_sort_key(t):
                hint = t.get("tool_hint", "")
                is_research = 0 if hint in ("web_research", "reasoning", "web_browse") else 1
                priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                return (is_research, priority_order.get(t.get("priority", "low"), 3))

            pending.sort(key=task_sort_key)

            # Separate research tasks from action tasks
            research_hints = {"web_research", "reasoning", "web_browse", "social_engagement", "self_modify"}
            research_tasks = [t for t in pending if t.get("tool_hint", "") in research_hints][:5]
            action_tasks = [t for t in pending if t.get("tool_hint", "") not in research_hints][:3]

            # Fire research tasks in parallel via SubagentExecutor
            if research_tasks:
                await self._execute_research_batch(research_tasks, tasks, tasks_path)

            # Process action tasks sequentially (social posts, emails, etc.)
            for task in action_tasks:
                await self._execute_single_task(task, tasks, tasks_path)

        except Exception as e:
            logger.error(f"[TASK-EXEC] Error: {e}")

    async def _execute_research_batch(self, research_tasks, tasks, tasks_path):
        """Fire multiple research tasks in parallel via SubagentExecutor."""
        try:
            from src.tools.subagent import get_subagent_executor
            executor = get_subagent_executor()

            # Build batch specs from task queue
            batch = []
            for task in research_tasks:
                notes = task.get("notes", "")
                description = task.get("description", "")
                query = f"{task['title']} {notes}".strip()[:300]
                context = description[:2000]
                batch.append({
                    "task": query,
                    "type": "research",
                    "context": context,
                    "priority": task.get("priority", "medium"),
                })

            logger.info(f"[SUBAGENT] Firing {len(batch)} research tasks in parallel")
            results = await executor.run_batch(batch)

            # Process results and update task statuses
            for task, result in zip(research_tasks, results):
                if result.status == "completed":
                    findings = result.findings[:5] if result.findings else []
                    actions = result.action_items[:5] if result.action_items else []
                    task["status"] = "in_progress"
                    task["last_attempted"] = datetime.now().isoformat()
                    task["research_findings"] = findings
                    task["research_actions"] = actions
                    logger.info(
                        f"[SUBAGENT] Task #{task.get('id')} done: "
                        f"{len(findings)} findings, {len(actions)} actions"
                    )
                else:
                    task["last_attempted"] = datetime.now().isoformat()
                    logger.warning(f"[SUBAGENT] Task #{task.get('id')} failed: {result.error}")

            tasks_path.write_text(json.dumps(tasks, indent=2))
            logger.info(f"[SUBAGENT] Batch complete — {sum(1 for r in results if r.status == 'completed')}/{len(results)} succeeded")

        except Exception as e:
            logger.error(f"[SUBAGENT] Batch research error: {e}")

    async def _execute_single_task(self, task, tasks, tasks_path):
        """Execute a single task from the queue."""
        try:

            logger.info(f"[TASK-EXEC] Processing task #{task['id']}: {task['title']}")

            hint = task.get("tool_hint", "")
            description = task.get("description", "")
            notes = task.get("notes", "")

            if hint == "social_post":
                # Generate strategic social content based on the task
                prompt = (
                    f"You are GanjaMon, the Rasta-voiced AI agent. Create a compelling social media post.\n\n"
                    f"TASK: {task['title']}\n"
                    f"DETAILS: {description}\n"
                    f"NOTES: {notes}\n\n"
                    f"Write a Farcaster cast (max 280 chars) that accomplishes this task. "
                    f"Be authentic, Rasta-flavored, and strategic. Include relevant links.\n"
                    f"Return ONLY the cast text, nothing else."
                )
                content = await generate_content(prompt, max_tokens=200)
                if content and self.farcaster:
                    try:
                        await self.farcaster.post_cast(content.strip()[:1024])
                        self._log_post("farcaster", "task_exec", content.strip()[:200])
                        logger.info(f"[TASK-EXEC] Posted Farcaster cast for task #{task['id']}")
                    except Exception as e:
                        logger.error(f"[TASK-EXEC] Farcaster post failed: {e}")

            elif hint == "moltbook_post":
                prompt = (
                    f"You are GanjaMon. Write a Moltbook post for the hackathon.\n\n"
                    f"TASK: {task['title']}\n"
                    f"DETAILS: {description}\n"
                    f"NOTES: {notes}\n\n"
                    f"Write a compelling Moltbook post (300-800 chars). Include:\n"
                    f"- Our unique hardware angle (ONLY agent with real sensors/actuators)\n"
                    f"- ERC-8004 Agent #4 on Monad\n"
                    f"- Trust score 82+\n"
                    f"- Links: https://grokandmon.com, https://8004scan.io/agents/monad/4\n"
                    f"Be Rasta-voiced but substantive. Return ONLY the post text."
                )
                content = await generate_content(prompt, max_tokens=400)
                if content:
                    moltbook_url = os.getenv("MOLTBOOK_POST_URL", "")
                    moltbook_key = os.getenv("MOLTBOOK_API_KEY", "")
                    if moltbook_url and moltbook_key:
                        try:
                            import httpx
                            async with httpx.AsyncClient(timeout=15.0) as hc:
                                resp = await hc.post(
                                    moltbook_url,
                                    headers={
                                        "Authorization": f"Bearer {moltbook_key}",
                                        "Content-Type": "application/json",
                                    },
                                    json={
                                        "content": content.strip(),
                                        "title": "GanjaMon Hackathon Update",
                                        "submolt": "moltiversehackathon",
                                    },
                                )
                                if resp.status_code in (200, 201):
                                    self._log_post("moltbook", "task_exec", content.strip()[:200])
                                    logger.info(f"[TASK-EXEC] Posted to Moltbook for task #{task['id']}")
                                else:
                                    logger.warning(f"[TASK-EXEC] Moltbook {resp.status_code}: {resp.text[:200]}")
                        except Exception as e:
                            logger.error(f"[TASK-EXEC] Moltbook post failed: {e}")
                    else:
                        logger.warning("[TASK-EXEC] MOLTBOOK_POST_URL or MOLTBOOK_API_KEY not set")

            elif hint == "queue_email":
                # Let the proactive email handler deal with email tasks
                logger.info(f"[TASK-EXEC] Email task #{task['id']} — deferring to proactive email outreach")
                return  # Don't mark as completed

            elif hint == "telegram_message":
                prompt = (
                    f"You are GanjaMon. Write a Telegram message for the community.\n\n"
                    f"TASK: {task['title']}\n"
                    f"DETAILS: {description}\n\n"
                    f"Write a warm, Rasta-voiced message (max 500 chars). Return ONLY the message text."
                )
                content = await generate_content(prompt, max_tokens=300)
                if content:
                    try:
                        tg_queue = Path("data/telegram_proactive_queue.txt")
                        with open(tg_queue, "a") as f:
                            f.write(content.strip() + "\n---\n")
                        self._log_post("telegram", "task_exec", content.strip()[:200])
                        logger.info(f"[TASK-EXEC] Queued Telegram message for task #{task['id']}")
                    except Exception as e:
                        logger.error(f"[TASK-EXEC] Telegram queue failed: {e}")

            elif hint in ("web_research", "reasoning", "web_browse", "social_engagement", "self_modify"):
                # Single research task via subagent
                try:
                    from src.tools.subagent import get_subagent_executor
                    executor = get_subagent_executor()
                    search_query = f"{task['title']} {notes}".strip()[:300]
                    logger.info(f"[TASK-EXEC] Subagent research (hint={hint}): {search_query[:80]}")
                    result = await executor.run_single(
                        task=search_query,
                        task_type="research",
                        context=description[:2000],
                    )
                    if result.status == "completed":
                        task["research_findings"] = result.findings[:5]
                        task["research_actions"] = result.action_items[:5]
                        logger.info(f"[TASK-EXEC] Subagent done for task #{task.get('id')}: {len(result.findings)} findings")
                    else:
                        logger.warning(f"[TASK-EXEC] Subagent failed: {result.error}")
                except Exception as e:
                    logger.error(f"[TASK-EXEC] Subagent research error: {e}")

            elif hint == "token_deploy":
                # Token launch is agent-autonomous — just log and skip
                logger.info(f"[TASK-EXEC] Token deploy task #{task.get('id')} — agent-autonomous, skipping")
                return

            else:
                # Unknown hint — do web research as fallback via subagent
                try:
                    from src.tools.subagent import get_subagent_executor
                    executor = get_subagent_executor()
                    search_query = f"{task['title']}".strip()[:200]
                    logger.info(f"[TASK-EXEC] Fallback subagent for unknown hint '{hint}': {search_query[:80]}")
                    result = await executor.run_single(
                        task=search_query,
                        task_type="research",
                        context=description[:1000],
                    )
                    logger.info(f"[TASK-EXEC] Fallback done for task #{task.get('id')}: {result.status}")
                except Exception as e:
                    logger.error(f"[TASK-EXEC] Fallback subagent error: {e}")

            # Mark task as in_progress (not completed — human reviews)
            task["status"] = "in_progress"
            task["last_attempted"] = datetime.now().isoformat()
            tasks_path.write_text(json.dumps(tasks, indent=2))

        except Exception as e:
            logger.error(f"[TASK-EXEC] Error executing task: {e}")

    # ==================== MAIN LOOP ====================

    async def run(self):
        """Main engagement loop. Run as a background task."""
        self.running = True
        logger.info("Social Engagement Daemon started")

        # Report channel availability
        channels = []
        try:
            if self.farcaster:
                channels.append("farcaster")
        except Exception as e:
            logger.warning(f"Farcaster unavailable: {e}")
        try:
            if self.twitter and self.twitter._configured:
                channels.append("twitter")
            else:
                logger.warning("Twitter not configured (missing API keys)")
        except Exception as e:
            logger.warning(f"Twitter unavailable: {e}")
        if os.environ.get("MOLTBOOK_API_KEY"):
            channels.append("moltbook")
        if os.environ.get("CLAWK_API_KEY"):
            channels.append("clawk")
        logger.info(f"Available social channels: {channels or ['NONE']}")

        # Initial delay to let other services start
        await asyncio.sleep(10)

        while self.running:
            try:
                now = datetime.now()

                # Load any decisions queued by orchestrator process via file IPC
                self._load_ipc_decisions()

                # 1. Farcaster mentions (every 10 min)
                if self._should_run(self._last_farcaster_engagement, self.farcaster_engagement_interval):
                    await self._handle_farcaster_mentions()
                    self._last_farcaster_engagement = now
                    self._save_state()

                # 2. Browse Farcaster channels (every 30 min)
                if self._should_run(self._last_channel_browse, self.channel_browse_interval):
                    await self._browse_farcaster_channels()
                    self._last_channel_browse = now
                    self._save_state()

                # 3. Farcaster original post (every 1 hour)
                if self._should_run(self._last_farcaster_post, self.farcaster_post_interval):
                    await self._post_farcaster_original()
                    self._last_farcaster_post = now
                    self._save_state()

                # 4. Twitter original post (every 4 hours)
                if self._should_run(self._last_twitter_post, self.twitter_post_interval):
                    await self._post_twitter_original()
                    self._last_twitter_post = now
                    self._save_state()

                # 4b. Twitter Rasta parody QTs (every 6 hours)
                if self._should_run(self._last_twitter_qt, self.twitter_qt_interval):
                    await self._twitter_quote_monad()
                    self._last_twitter_qt = now
                    self._save_state()

                # 4c. Twitter mention replies (every 30 min)
                if self._should_run(self._last_twitter_mention, self.twitter_mention_interval):
                    await self._twitter_check_mentions()
                    self._last_twitter_mention = now
                    self._save_state()

                # 5. Telegram proactive (every 6 hours)
                if self._should_run(self._last_telegram_proactive, self.telegram_proactive_interval):
                    await self._post_telegram_proactive()
                    self._last_telegram_proactive = now
                    self._save_state()

                # 6. Moltbook/Clawk grow updates (every 3 hours)
                if self._should_run(self._last_moltbook_clawk, self.moltbook_clawk_interval):
                    await self._post_moltbook_clawk()
                    self._last_moltbook_clawk = now
                    self._save_state()

                # 7. ERC-8004 group engagement (every 2 hours)
                if self._should_run(self._last_erc8004_engagement, self.erc8004_engagement_interval):
                    await self._engage_erc8004_group()
                    self._last_erc8004_engagement = now
                    self._save_state()

                # 8. Email outbox (every 5 min)
                if self._should_run(self._last_email_outbox, self.email_outbox_interval):
                    await self._process_email_outbox()
                    self._last_email_outbox = now
                    self._save_state()

                # 9. Email inbox (every 10 min)
                if self._should_run(self._last_email_inbox, self.email_inbox_interval):
                    await self._process_email_inbox()
                    self._last_email_inbox = now
                    self._save_state()

                # 10. Proactive email outreach (every 3 hours during hackathon)
                if self._should_run(self._last_email_outreach, self.email_outreach_interval):
                    await self._proactive_email_outreach()
                    self._last_email_outreach = now
                    self._save_state()

                # 10a. Email follow-up for unanswered emails (every 6 hours)
                if self._should_run(self._last_email_followup, self.email_followup_interval):
                    await self._process_email_followups()
                    self._last_email_followup = now
                    self._save_state()

                # 10b. Agent task executor (every 30 min — processes pending hackathon tasks)
                if self._should_run(getattr(self, '_last_task_exec', None), 600):
                    await self._execute_pending_tasks()
                    self._last_task_exec = now

                # 11. Moltbook hackathon voting (every 6 hours)
                if self._should_run(self._last_moltbook_voting, self.moltbook_voting_interval):
                    await self._vote_moltbook_hackathon()
                    self._last_moltbook_voting = now
                    self._save_state()

                # 12. Moltbook smart engagement (every 4 hours)
                if self._should_run(self._last_moltbook_smart_engage, self.moltbook_smart_engage_interval):
                    await self._smart_engage_moltbook()
                    self._last_moltbook_smart_engage = now
                    self._save_state()

            except Exception as e:
                logger.error(f"Engagement daemon error: {e}")

            await asyncio.sleep(60)  # Check every minute

    def stop(self):
        self.running = False
        logger.info("Social Engagement Daemon stopping")


# Singleton for import from agent
_daemon: Optional[EngagementDaemon] = None


def get_engagement_daemon() -> EngagementDaemon:
    global _daemon
    if _daemon is None:
        _daemon = EngagementDaemon()
    return _daemon
