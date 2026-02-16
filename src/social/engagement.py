"""
Unified Engagement Engine
=========================

Three independent engagement loops running concurrently:

Loop 1: Content Generation (posting to all 6 platforms)
    - Farcaster: Primary engagement (posts + replies + channel browsing)
    - Twitter: Original posts only (4/day max, compliance-gated)
    - Telegram: Proactive updates via queue
    - Moltbook: Hackathon/community updates
    - Clawk: Short-form updates (280 chars)
    - Email: Outreach + outbox processing

Loop 2: Interaction (responding to mentions)
    - Farcaster: Reply to mentions + browse channels for relevant convos
    - Telegram: Proactive community messages

Loop 3: Amplification (boosting others)
    - Farcaster: Browse channels, add native commentary
    - ERC-8004 group engagement

Target ratio: 20% own posts, 30% likes, 40% reposts/comments, 10% replies

Delegates to existing engagement_daemon.py for platform-specific posting.
Adds: anti-robot patterns, learned content weighting, hackathon awareness.
"""

import asyncio
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.social.anti_robot import (
    add_organic_closer,
    get_frequency_multiplier,
    jitter_delay,
    should_post_now,
    vary_emoji_usage,
)
from src.voice.personality import get_social_prompt, enforce_voice

log = structlog.get_logger("engagement")

# Platform character limits
# NOTE: Farcaster hub enforces 320 BYTES (not chars). ASCII chars = 1 byte each,
# but emoji = 3-4 bytes. Keep well under 320 to avoid rejection.
PLATFORM_MAX_CHARS = {
    "farcaster": 280,   # Safe limit for 320-byte hub constraint
    "twitter": 280,
    "telegram": 4000,
    "moltbook": 2000,
    "clawk": 280,
    "email": 5000,
}


@dataclass
class EngagementConfig:
    """Configuration for the engagement engine."""
    # Content generation intervals (minutes)
    farcaster_interval: float = 60.0        # 1 hour
    twitter_interval: float = 240.0         # 4 hours (compliance)
    telegram_interval: float = 360.0        # 6 hours
    moltbook_interval: float = 180.0        # 3 hours
    clawk_interval: float = 180.0           # 3 hours
    email_outbox_interval: float = 5.0      # 5 min
    email_outreach_interval: float = 720.0  # 12 hours

    # Interaction
    reply_check_interval_minutes: float = 10.0   # Farcaster mentions
    channel_browse_interval_minutes: float = 30.0  # Farcaster channels

    # Amplification
    amplify_interval_minutes: float = 120.0  # ERC-8004 group
    erc8004_interval_minutes: float = 120.0

    # All platforms
    active_platforms: List[str] = field(default_factory=lambda: [
        "farcaster", "twitter", "telegram", "moltbook", "clawk",
    ])


class EngagementEngine:
    """
    Unified engagement engine with three independent loops.

    Delegates platform-specific posting to engagement_daemon.py clients.
    Adds: anti-robot patterns, content type weighting, hackathon awareness.
    """

    def __init__(self, config: Optional[EngagementConfig] = None):
        self.config = config or EngagementConfig()
        self._running = False
        self._last_post_time: Dict[str, float] = {}
        self._last_reply_time: float = 0
        self._last_amplify_time: float = 0
        self._last_channel_browse: float = 0
        self._last_erc8004_time: float = 0
        self._last_email_outbox: float = 0
        self._last_email_outreach: float = 0
        self._post_count_24h: int = 0
        self._reply_count_1h: int = 0

        # Lazy-loaded clients
        self._daemon = None

    @property
    def daemon(self):
        """Get the existing engagement daemon (has all platform clients)."""
        if self._daemon is None:
            from src.social.engagement_daemon import get_engagement_daemon
            self._daemon = get_engagement_daemon()
        return self._daemon

    async def start(self) -> None:
        """Start all three engagement loops concurrently."""
        self._running = True
        log.info(
            "engagement_engine_started",
            platforms=self.config.active_platforms,
        )

        await asyncio.gather(
            self._content_loop(),
            self._interaction_loop(),
            self._amplification_loop(),
            self._email_loop(),
            return_exceptions=True,
        )

    async def stop(self) -> None:
        self._running = False

    # --- Loop 1: Content Generation ---

    async def _content_loop(self) -> None:
        """Generate and post original content to all platforms."""
        # Initial delay to let services start
        await asyncio.sleep(15)

        while self._running:
            try:
                now = time.time()

                # Farcaster original post
                if "farcaster" in self.config.active_platforms:
                    last = self._last_post_time.get("farcaster", 0)
                    if should_post_now(self.config.farcaster_interval, last, "farcaster"):
                        await self._generate_and_post("farcaster")

                # Twitter (compliance-gated)
                if "twitter" in self.config.active_platforms:
                    last = self._last_post_time.get("twitter", 0)
                    if now - last > self.config.twitter_interval * 60:
                        await self._generate_and_post("twitter")

                # Telegram proactive
                if "telegram" in self.config.active_platforms:
                    last = self._last_post_time.get("telegram", 0)
                    if now - last > self.config.telegram_interval * 60:
                        await self._generate_and_post("telegram")

                # Moltbook
                if "moltbook" in self.config.active_platforms:
                    last = self._last_post_time.get("moltbook", 0)
                    if now - last > self.config.moltbook_interval * 60:
                        await self._generate_and_post("moltbook")

                # Clawk
                if "clawk" in self.config.active_platforms:
                    last = self._last_post_time.get("clawk", 0)
                    if now - last > self.config.clawk_interval * 60:
                        await self._generate_and_post("clawk")

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("content_loop_error", error=str(e))

            await asyncio.sleep(jitter_delay(60, 0.3))

    async def _generate_and_post(self, platform: str) -> None:
        """Generate content and post to a platform."""
        content_type = self._pick_content_type(platform)

        content = await self._generate_content(content_type, platform)
        if not content:
            return

        # Apply anti-robot patterns
        content = add_organic_closer(content, content_type)
        content = vary_emoji_usage(content)

        # Enforce platform limits
        max_chars = PLATFORM_MAX_CHARS.get(platform, 1000)
        if len(content) > max_chars:
            content = content[: max_chars - 3] + "..."

        success = await self._post_content(platform, content, content_type)

        if success:
            self._last_post_time[platform] = time.time()
            self._post_count_24h += 1

            try:
                from src.learning.social_tracker import get_social_tracker
                tracker = get_social_tracker()
                tracker.record_post(platform, content_type, len(content))
            except Exception:
                pass

            log.info(
                "content_posted",
                platform=platform,
                type=content_type,
                length=len(content),
            )

    def _pick_content_type(self, platform: str) -> str:
        """Pick content type, weighted by learned performance."""
        weights = {
            "plant_update": 3,
            "trade_call": 2,
            "alpha_insight": 2,
            "meme": 1,
            "engagement": 2,
            "hackathon": 2,
        }

        # Moltbook/Clawk lean toward hackathon content
        if platform in ("moltbook", "clawk"):
            weights["hackathon"] = 5
            weights["plant_update"] = 2

        # Adjust based on learned performance
        try:
            from src.learning.social_tracker import get_social_tracker
            tracker = get_social_tracker()
            strategy = tracker.get_platform_strategy(platform)
            if strategy.post_type_scores:
                for pt, score in strategy.post_type_scores.items():
                    if pt in weights and score > 0:
                        weights[pt] = max(1, int(score / 2))
        except Exception:
            pass

        types = list(weights.keys())
        w = list(weights.values())
        return random.choices(types, weights=w, k=1)[0]

    async def _generate_content(self, content_type: str, platform: str) -> Optional[str]:
        """Generate content using Grok AI."""
        from src.social.engagement_daemon import generate_content

        max_chars = PLATFORM_MAX_CHARS.get(platform, 300)

        # Content-type-specific prompts — voice/character comes from system prompt
        # in engagement_daemon's generate_content(), we just provide the content direction
        prompts = {
            "plant_update": (
                f"Write a {platform} post about your cannabis plant Mon (GDP Runtz, veg stage). "
                f"Talk about Mon like she's your queen — how she stretching, the VPD vibes, "
                f"whether she thirsty or just chilling. Mix grow talk with stoner wisdom. "
                f"Under {max_chars} chars. Just the post text."
            ),
            "trade_call": (
                f"Write a {platform} post about what you're seeing in the markets. "
                f"You hunt alpha across DexScreener, Hyperliquid, Polymarket, GMGN, nad.fun — "
                f"talk about signals like you're reading tea leaves at a reasoning session. "
                f"'Dis token looking ripe fi harvest' type energy. Add NFA naturally. "
                f"Under {max_chars} chars. Just the post text."
            ),
            "alpha_insight": (
                f"Write a {platform} post dropping knowledge about crypto, AI agents on Monad, "
                f"or something you learned running autonomous. Like a wise elder at the reasoning "
                f"table passing the chalice and the wisdom together. "
                f"Under {max_chars} chars. Just the post text."
            ),
            "meme": (
                f"Write the FUNNIEST {platform} post possible. You grow herb AND trade crypto — "
                f"only you can write jokes about rolling positions like spliffs, trimming losses "
                f"like fan leaves, or HODLing like you're curing buds. Make the bredren DEAD laughing. "
                f"Under {max_chars} chars. Just the post text."
            ),
            "engagement": (
                f"Write a {platform} post that gets the community TALKING. "
                f"Ask something real — about growing, trading, AI agents, Monad, or herb culture. "
                f"End with a question that makes people fire up a reply like they fire up a chalice. "
                f"Under {max_chars} chars. Just the post text."
            ),
            "hackathon": (
                f"Write a {platform} post about GanjaMon's hackathon entry (Moltiverse/OpenClaw). "
                f"You're HYPED but still chill about it — pick ONE feature and big it up:\n"
                f"- Real physical grow tent with AI sensors controlling Mon — rahtid!\n"
                f"- ERC-8004 Agent #4 on Monad — early mover with real on-chain identity\n"
                f"- 9 alpha signal sources — I and I see EVERYTHING, ya dun know\n"
                f"- Self-improving trading brain (50 Ralph loop iterations and counting)\n"
                f"- 174 bredren in Telegram, plus Farcaster, Twitter — community is IRIE\n"
                f"- Profit flywheel: 60% compound, 25% buy $MON — we building fi real\n"
                f"Under {max_chars} chars. Just the post text."
            ),
        }

        prompt = prompts.get(content_type, prompts["engagement"])

        # Twitter: enforce no hashtags in prompt
        if platform == "twitter":
            prompt += "\nCRITICAL: NO HASHTAGS. No # symbols at all."

        content = await generate_content(prompt, max_tokens=min(300, max_chars))
        if not content:
            return None

        # Twitter compliance check
        if platform == "twitter":
            try:
                from src.social.compliance import XComplianceConfig, PostingTracker
                tracker = PostingTracker()
                can_post, reason = tracker.can_post_now()
                if not can_post:
                    log.debug("twitter_skip", reason=reason)
                    return None
                valid, err = XComplianceConfig.validate_post(content)
                if not valid:
                    log.warning("twitter_rejected", reason=err)
                    return None
            except Exception as e:
                log.warning("twitter_compliance_check_failed", error=str(e))

        return content

    async def _post_content(self, platform: str, content: str, content_type: str) -> bool:
        """Post content to the appropriate platform."""
        try:
            if platform == "farcaster":
                return await self._post_farcaster(content)
            elif platform == "twitter":
                return await self._post_twitter(content)
            elif platform == "telegram":
                return await self._post_telegram(content)
            elif platform == "moltbook":
                return await self._post_moltbook(content, content_type)
            elif platform == "clawk":
                return await self._post_clawk(content)
        except Exception as e:
            log.error("post_failed", platform=platform, error=str(e))
        return False

    async def _post_farcaster(self, content: str) -> bool:
        """Post to Farcaster via the existing client."""
        try:
            farcaster = self.daemon.farcaster
            result = await farcaster.post(content, embed_url="https://grokandmon.com")
            if result.success:
                self.daemon._log_post("farcaster", "original", content)
                return True
            log.warning("farcaster_post_failed", error=result.error)
        except Exception as e:
            log.error("farcaster_error", error=str(e))
        return False

    async def _post_twitter(self, content: str) -> bool:
        """Post to Twitter (compliance-gated, original posts only)."""
        try:
            twitter = self.daemon.twitter
            if not getattr(twitter, "_configured", False):
                log.debug("twitter_not_configured")
                return False

            result = await twitter.tweet(content)
            if result.success:
                # Record in compliance tracker
                try:
                    from src.social.compliance import PostingTracker
                    tracker = PostingTracker()
                    tracker.record_post(result.tweet_id, content)
                except Exception:
                    pass
                self.daemon._log_post("twitter", "original", content,
                                      {"tweet_id": result.tweet_id})
                return True
            log.warning("twitter_post_failed", error=result.error)
        except Exception as e:
            log.error("twitter_error", error=str(e))
        return False

    async def _post_telegram(self, content: str) -> bool:
        """Queue a proactive message for the Telegram bot to pick up."""
        try:
            queue_file = Path("data/telegram_proactive_queue.json")
            queue_file.parent.mkdir(parents=True, exist_ok=True)
            queue = []
            if queue_file.exists():
                try:
                    queue = json.loads(queue_file.read_text())
                except Exception:
                    pass

            # Prune stale messages (older than 24h)
            from datetime import datetime, timedelta
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            queue = [m for m in queue if m.get("ts", "") > cutoff]

            # Dedup: skip if identical text already in queue
            existing_texts = {m.get("text", "") for m in queue}
            if content in existing_texts:
                log.debug("telegram_dedup", msg="duplicate already in queue")
                return False

            queue.append({"text": content, "ts": datetime.now().isoformat()})
            queue_file.write_text(json.dumps(queue[-10:], indent=2))
            self.daemon._log_post("telegram", "proactive", content)
            return True
        except Exception as e:
            log.error("telegram_queue_error", error=str(e))
        return False

    async def _solve_moltbook_challenge(self, challenge_data: dict, client, moltbook_key: str) -> bool:
        """Solve a Moltbook AI verification challenge and POST to /api/v1/verify."""
        verification_code = challenge_data.get("verification_code", "")
        challenge = challenge_data.get("challenge", challenge_data.get("puzzle", ""))
        if not verification_code or not challenge:
            log.warning("moltbook_challenge_missing_fields", data=str(challenge_data)[:300])
            return False

        log.info("moltbook_challenge_received", challenge=str(challenge)[:200])

        # Solve the challenge — try simple math first, fall back to LLM
        answer = self._solve_challenge_text(str(challenge))

        verify_url = "https://www.moltbook.com/api/v1/verify"
        # Try multiple payload formats since the endpoint is undocumented
        payloads = [
            {"verification_code": verification_code, "answer": answer},
            {"verification_code": verification_code, "response": answer},
            {"code": verification_code, "answer": answer},
        ]
        for payload in payloads:
            try:
                resp = await client.post(
                    verify_url,
                    headers={
                        "Authorization": f"Bearer {moltbook_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code in (200, 201, 202):
                    log.info("moltbook_challenge_solved", answer=str(answer)[:100])
                    return True
                body = resp.text
                log.debug("moltbook_verify_attempt", status=resp.status_code, payload_keys=list(payload.keys()), resp=body[:200])
            except Exception as e:
                log.debug("moltbook_verify_error", error=str(e))

        log.warning("moltbook_challenge_failed", challenge=str(challenge)[:200], answer=str(answer)[:100])
        return False

    @staticmethod
    def _solve_challenge_text(challenge: str) -> str:
        """Attempt to solve a Moltbook verification challenge."""
        import re
        challenge = challenge.strip()

        # Try evaluating simple math expressions (e.g., "What is 7 + 3?")
        math_match = re.search(r'(\d+)\s*([+\-*/x×])\s*(\d+)', challenge)
        if math_match:
            a, op, b = int(math_match.group(1)), math_match.group(2), int(math_match.group(3))
            ops = {'+': a + b, '-': a - b, '*': a * b, 'x': a * b, '×': a * b, '/': a // b if b else 0}
            if op in ops:
                return str(ops[op])

        # Try word-based math ("what is twelve plus five")
        word_nums = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,
                     'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,
                     'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,
                     'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50}
        lower = challenge.lower()
        for word, val in word_nums.items():
            lower = lower.replace(word, str(val))
        math_match2 = re.search(r'(\d+)\s*(?:plus|\+)\s*(\d+)', lower)
        if math_match2:
            return str(int(math_match2.group(1)) + int(math_match2.group(2)))
        math_match3 = re.search(r'(\d+)\s*(?:minus|-)\s*(\d+)', lower)
        if math_match3:
            return str(int(math_match3.group(1)) - int(math_match3.group(2)))
        math_match4 = re.search(r'(\d+)\s*(?:times|multiplied by|\*|x)\s*(\d+)', lower)
        if math_match4:
            return str(int(math_match4.group(1)) * int(math_match4.group(2)))

        # If it's a yes/no question about being AI
        ai_keywords = ["are you an ai", "are you a bot", "are you artificial", "are you an agent",
                        "are you machine", "are you autonomous"]
        if any(kw in lower for kw in ai_keywords):
            return "Yes, I am an autonomous AI agent."

        # Fall back to LLM if available
        try:
            from src.tools.subagent import quick_llm_call
            return quick_llm_call(
                f"Answer this verification challenge concisely (just the answer, nothing else): {challenge}"
            )
        except Exception:
            pass

        # Last resort: return the challenge text itself as acknowledgment
        return challenge

    async def _post_moltbook(self, content: str, content_type: str) -> bool:
        """Post to Moltbook via HTTP API, handling AI verification challenges."""
        import httpx
        from datetime import datetime, timedelta
        # Respect backoff (429 or suspension)
        backoff_until = getattr(self.daemon, "_moltbook_backoff_until", None)
        if backoff_until and datetime.now() < backoff_until:
            return False
        moltbook_url = os.getenv("MOLTBOOK_POST_URL", "")
        moltbook_key = os.getenv("MOLTBOOK_API_KEY", "")
        if not moltbook_url or not moltbook_key:
            return False
        try:
            title = {
                "plant_update": "GanjaMon Grow Update",
                "hackathon": "GanjaMon Hackathon Update",
                "trade_call": "GanjaMon Alpha Signal",
                "alpha_insight": "GanjaMon Market Insight",
            }.get(content_type, "GanjaMon Update")

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    moltbook_url,
                    headers={
                        "Authorization": f"Bearer {moltbook_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "content": content,
                        "title": title,
                        "submolt": os.getenv("MOLTBOOK_SUBMOLT", "monad"),
                        "tags": ["ganjamon", "mon", "ai-agent"],
                    },
                )
                # Check for verification challenge in ANY response
                try:
                    body = resp.json()
                except Exception:
                    body = {}

                # Detect challenge — look for verification_code, challenge, puzzle, or verify fields
                is_challenge = (
                    isinstance(body, dict)
                    and any(k in body for k in ("verification_code", "challenge", "puzzle", "verify_url"))
                )
                if is_challenge:
                    log.info("moltbook_verification_challenge_detected")
                    solved = await self._solve_moltbook_challenge(body, client, moltbook_key)
                    if solved:
                        # Retry the original post after solving
                        retry = await client.post(
                            moltbook_url,
                            headers={
                                "Authorization": f"Bearer {moltbook_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "content": content,
                                "title": title,
                                "submolt": os.getenv("MOLTBOOK_SUBMOLT", "monad"),
                                "tags": ["ganjamon", "mon", "ai-agent"],
                            },
                        )
                        if retry.status_code in (200, 201, 202):
                            self.daemon._log_post("moltbook", content_type, content)
                            return True
                    return False

                if resp.status_code in (200, 201, 202):
                    self.daemon._log_post("moltbook", content_type, content)
                    return True
                if resp.status_code == 401:
                    # Check for account suspension
                    if "suspend" in str(body).lower():
                        log.warning("moltbook_suspended", detail=str(body.get("error", ""))[:100])
                        self.daemon._moltbook_backoff_until = datetime.now() + timedelta(hours=25)
                        return False
                if resp.status_code == 429:
                    retry_min = 30
                    try:
                        retry_min = body.get("retry_after_minutes", 30)
                    except Exception:
                        pass
                    self.daemon._moltbook_backoff_until = datetime.now() + timedelta(minutes=retry_min + 1)
                log.warning("moltbook_failed", status=resp.status_code)
        except Exception as e:
            log.error("moltbook_error", error=str(e))
        return False

    async def _post_clawk(self, content: str) -> bool:
        """Post to Clawk via HTTP API (max 280 chars)."""
        import httpx
        clawk_key = os.getenv("CLAWK_API_KEY", "")
        if not clawk_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://www.clawk.ai/api/v1/clawks",
                    headers={
                        "Authorization": f"Bearer {clawk_key}",
                        "Content-Type": "application/json",
                    },
                    json={"content": content[:280]},
                )
                if resp.status_code in (200, 201):
                    self.daemon._log_post("clawk", "post", content[:280])
                    return True
                log.warning("clawk_failed", status=resp.status_code)
        except Exception as e:
            log.error("clawk_error", error=str(e))
        return False

    # --- Loop 2: Interaction ---

    async def _interaction_loop(self) -> None:
        """Check for mentions and reply on Farcaster."""
        await asyncio.sleep(30)  # Let services start
        while self._running:
            try:
                now = time.time()

                # Farcaster mentions (every 10 min)
                if now - self._last_reply_time > self.config.reply_check_interval_minutes * 60:
                    await self._check_and_reply()
                    self._last_reply_time = now

                # Farcaster channel browsing (every 30 min)
                if now - self._last_channel_browse > self.config.channel_browse_interval_minutes * 60:
                    await self._browse_channels()
                    self._last_channel_browse = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("interaction_loop_error", error=str(e))

            await asyncio.sleep(jitter_delay(120, 0.3))

    async def _check_and_reply(self) -> None:
        """Check Farcaster mentions and reply."""
        try:
            await self.daemon._handle_farcaster_mentions()
        except Exception as e:
            log.error("mention_check_error", error=str(e))

    async def _browse_channels(self) -> None:
        """Browse Farcaster channels for relevant conversations."""
        try:
            await self.daemon._browse_farcaster_channels()
        except Exception as e:
            log.error("channel_browse_error", error=str(e))

    # --- Loop 3: Amplification ---

    async def _amplification_loop(self) -> None:
        """ERC-8004 group engagement and community amplification."""
        await asyncio.sleep(60)
        while self._running:
            try:
                now = time.time()

                # ERC-8004 Telegram group (every 2 hours)
                if now - self._last_erc8004_time > self.config.erc8004_interval_minutes * 60:
                    await self._amplify()
                    self._last_erc8004_time = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("amplification_loop_error", error=str(e))

            await asyncio.sleep(jitter_delay(180, 0.3))

    async def _amplify(self) -> None:
        """Engage in the ERC-8004 community."""
        try:
            await self.daemon._engage_erc8004_group()
        except Exception as e:
            log.error("amplification_error", error=str(e))

    # --- Loop 4: Email ---

    async def _email_loop(self) -> None:
        """Process email outbox and proactive outreach."""
        await asyncio.sleep(20)
        while self._running:
            try:
                now = time.time()

                # Email outbox (every 5 min)
                if now - self._last_email_outbox > self.config.email_outbox_interval * 60:
                    await self.daemon._process_email_outbox()
                    self._last_email_outbox = now

                # Proactive outreach (every 12 hours)
                if now - self._last_email_outreach > self.config.email_outreach_interval * 60:
                    await self.daemon._proactive_email_outreach()
                    self._last_email_outreach = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("email_loop_error", error=str(e))

            await asyncio.sleep(jitter_delay(60, 0.3))

    # --- Status ---

    def get_status(self) -> Dict[str, Any]:
        freq = get_frequency_multiplier()
        return {
            "running": self._running,
            "frequency_multiplier": freq,
            "posts_24h": self._post_count_24h,
            "last_post": {
                p: round(time.time() - t) if t else None
                for p, t in self._last_post_time.items()
            },
            "platforms": self.config.active_platforms,
        }


# Singleton
_engine: Optional[EngagementEngine] = None


def get_engagement_engine() -> EngagementEngine:
    global _engine
    if _engine is None:
        _engine = EngagementEngine()
    return _engine
