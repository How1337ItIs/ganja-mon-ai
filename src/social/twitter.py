"""
Twitter/X Social Client
=======================

Posts grow updates, plant images, and token milestones to X/Twitter.
Based on SOLTOMATO's social media engagement pattern.

Uses Twitter API v2 via tweepy for posting text and media.
"""

import json
import math
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
import logging

try:
    import tweepy
    from tweepy.asynchronous import AsyncClient
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    tweepy = None
    AsyncClient = None


logger = logging.getLogger(__name__)


@dataclass
class TweetResult:
    """Result of a tweet attempt"""
    success: bool
    tweet_id: Optional[str] = None
    text: str = ""
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SearchedTweet:
    """A tweet from search results with author + engagement info."""
    id: str
    text: str
    author_id: str
    author_username: str = ""
    author_name: str = ""
    author_followers: int = 0
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    media_urls: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None

    def engagement_score(self) -> float:
        """Score for ranking — weights engagement, reach, and media presence."""
        engagement = self.likes + self.retweets * 3 + self.quotes * 5 + self.replies * 2
        reach = math.log10(max(self.author_followers, 1))
        has_media = 1.5 if self.media_urls else 1.0
        return engagement * reach * has_media


class TwitterClient:
    """
    Async Twitter/X client for posting grow updates.

    Uses Twitter API v2 for text and media posting.
    Falls back to logging when credentials not configured.

    Required environment variables:
        TWITTER_API_KEY
        TWITTER_API_SECRET
        TWITTER_ACCESS_TOKEN
        TWITTER_ACCESS_SECRET
        TWITTER_BEARER_TOKEN (optional, for v2 endpoints)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")

        self._client = None
        self._auth = None
        self._api_v1 = None  # For media uploads

        self._configured = self._check_config()

        if not self._configured:
            logger.warning("Twitter credentials not configured. Posts will be logged only.")

    def _check_config(self) -> bool:
        """Check if Twitter is properly configured"""
        if not TWEEPY_AVAILABLE:
            return False
        return bool(
            self.api_key
            and self.api_secret
            and self.access_token
            and self.access_secret
        )

    def _get_client(self):
        """Get or create tweepy client"""
        if not self._configured or not TWEEPY_AVAILABLE:
            return None

        if self._client is None:
            self._client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret,
                bearer_token=self.bearer_token,
            )
        return self._client

    def _get_api_v1(self):
        """Get v1.1 API for media uploads"""
        if not self._configured or not TWEEPY_AVAILABLE:
            return None

        if self._api_v1 is None:
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_secret,
            )
            self._api_v1 = tweepy.API(auth)
        return self._api_v1

    async def tweet(self, text: str, media_ids: Optional[List[str]] = None) -> TweetResult:
        """
        Post a tweet.

        Args:
            text: Tweet text (max 280 chars)
            media_ids: Optional list of uploaded media IDs

        Returns:
            TweetResult with success status and tweet ID
        """
        # Truncate text if needed
        if len(text) > 280:
            text = text[:277] + "..."

        if not self._configured:
            logger.info(f"[MOCK TWEET] {text}")
            return TweetResult(
                success=True,
                tweet_id="mock_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                text=text,
                error="Mock mode - no Twitter credentials",
            )

        try:
            client = self._get_client()

            # Run in thread pool since tweepy is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.create_tweet(text=text, media_ids=media_ids),
            )

            tweet_id = response.data.get("id") if response.data else None

            logger.info(f"Posted tweet {tweet_id}: {text[:50]}...")
            return TweetResult(
                success=True,
                tweet_id=tweet_id,
                text=text,
            )

        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return TweetResult(
                success=False,
                text=text,
                error=str(e),
            )

    async def upload_media(self, image_data: bytes, alt_text: Optional[str] = None) -> Optional[str]:
        """
        Upload media to Twitter.

        Args:
            image_data: Image bytes (JPEG/PNG)
            alt_text: Optional alt text for accessibility

        Returns:
            Media ID string or None on failure
        """
        if not self._configured:
            logger.info(f"[MOCK MEDIA UPLOAD] {len(image_data)} bytes")
            return "mock_media_id"

        try:
            api = self._get_api_v1()

            # Save to temp file (tweepy requires file for upload)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(image_data)
                temp_path = f.name

            try:
                loop = asyncio.get_event_loop()
                media = await loop.run_in_executor(
                    None,
                    lambda: api.media_upload(filename=temp_path),
                )

                media_id = str(media.media_id)

                # Add alt text if provided
                if alt_text:
                    await loop.run_in_executor(
                        None,
                        lambda: api.create_media_metadata(media_id, alt_text),
                    )

                logger.info(f"Uploaded media: {media_id}")
                return media_id

            finally:
                # Clean up temp file
                import os as os_module
                os_module.unlink(temp_path)

        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            return None

    async def get_my_user_id(self) -> Optional[str]:
        """Get authenticated user's ID (cached)."""
        if hasattr(self, '_user_id') and self._user_id:
            return self._user_id
        if not self._configured:
            return None
        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()
            me = await loop.run_in_executor(None, lambda: client.get_me(user_auth=True))
            self._user_id = me.data.id if me.data else None
            return self._user_id
        except Exception as e:
            logger.error(f"Failed to get user ID: {e}")
            return None

    async def search_recent(self, query: str, max_results: int = 20) -> List[SearchedTweet]:
        """Search recent tweets with engagement metrics and media info."""
        if not self._configured:
            logger.info(f"[MOCK SEARCH] {query}")
            return []

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.search_recent_tweets(
                    query=query,
                    max_results=min(max_results, 100),
                    tweet_fields=["public_metrics", "created_at", "author_id", "attachments"],
                    expansions=["author_id", "attachments.media_keys"],
                    media_fields=["url", "preview_image_url", "type"],
                    user_fields=["public_metrics", "username", "name"],
                    user_auth=True,  # Use OAuth 1.0a (no bearer token needed)
                ),
            )

            if not response.data:
                return []

            # Build lookup maps
            users_map = {}
            if response.includes and "users" in response.includes:
                for u in response.includes["users"]:
                    users_map[u.id] = u

            media_map = {}
            if response.includes and "media" in response.includes:
                for m in response.includes["media"]:
                    media_map[m.media_key] = m

            results = []
            for tweet in response.data:
                author = users_map.get(tweet.author_id)
                metrics = tweet.public_metrics or {}

                # Get media URLs from attachments
                media_urls = []
                if tweet.attachments and "media_keys" in tweet.attachments:
                    for mk in tweet.attachments["media_keys"]:
                        media = media_map.get(mk)
                        if media:
                            url = getattr(media, "url", None) or getattr(media, "preview_image_url", None)
                            if url:
                                media_urls.append(url)

                results.append(SearchedTweet(
                    id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    author_username=author.username if author else "",
                    author_name=author.name if author else "",
                    author_followers=author.public_metrics.get("followers_count", 0) if author else 0,
                    likes=metrics.get("like_count", 0),
                    retweets=metrics.get("retweet_count", 0),
                    replies=metrics.get("reply_count", 0),
                    quotes=metrics.get("quote_count", 0),
                    media_urls=media_urls,
                    created_at=tweet.created_at,
                ))

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def get_mentions(self, since_id: Optional[str] = None) -> List[SearchedTweet]:
        """Get recent @mentions of our account."""
        user_id = await self.get_my_user_id()
        if not user_id:
            return []

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            kwargs = {
                "id": user_id,
                "max_results": 20,
                "tweet_fields": ["public_metrics", "created_at", "author_id", "in_reply_to_user_id"],
                "expansions": ["author_id"],
                "user_fields": ["public_metrics", "username", "name"],
            }
            if since_id:
                kwargs["since_id"] = since_id

            response = await loop.run_in_executor(
                None, lambda: client.get_users_mentions(**kwargs, user_auth=True)
            )

            if not response.data:
                return []

            users_map = {}
            if response.includes and "users" in response.includes:
                for u in response.includes["users"]:
                    users_map[u.id] = u

            results = []
            for tweet in response.data:
                author = users_map.get(tweet.author_id)
                metrics = tweet.public_metrics or {}
                results.append(SearchedTweet(
                    id=tweet.id,
                    text=tweet.text,
                    author_id=tweet.author_id,
                    author_username=author.username if author else "",
                    author_name=author.name if author else "",
                    author_followers=author.public_metrics.get("followers_count", 0) if author else 0,
                    likes=metrics.get("like_count", 0),
                    retweets=metrics.get("retweet_count", 0),
                    replies=metrics.get("reply_count", 0),
                    quotes=metrics.get("quote_count", 0),
                    created_at=tweet.created_at,
                ))

            return results

        except Exception as e:
            logger.error(f"Get mentions failed: {e}")
            return []

    async def quote_tweet(
        self, tweet_id: str, text: str, media_ids: Optional[List[str]] = None
    ) -> TweetResult:
        """Post a quote tweet."""
        if not self._configured:
            logger.info(f"[MOCK QT of {tweet_id}] {text}")
            return TweetResult(
                success=True,
                tweet_id="mock_qt_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                text=text,
                error="Mock mode",
            )

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.create_tweet(
                    text=text, quote_tweet_id=tweet_id, media_ids=media_ids
                ),
            )
            tid = response.data.get("id") if response.data else None
            logger.info(f"Quote tweeted {tid} (quoting {tweet_id}): {text[:50]}...")
            return TweetResult(success=True, tweet_id=tid, text=text)
        except Exception as e:
            logger.error(f"Quote tweet failed: {e}")
            return TweetResult(success=False, text=text, error=str(e))

    async def reply_to(self, tweet_id: str, text: str) -> TweetResult:
        """Reply to a specific tweet (mention-based only)."""
        if not self._configured:
            logger.info(f"[MOCK REPLY to {tweet_id}] {text}")
            return TweetResult(
                success=True,
                tweet_id="mock_reply_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                text=text,
                error="Mock mode",
            )

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.create_tweet(
                    text=text, in_reply_to_tweet_id=tweet_id
                ),
            )
            tid = response.data.get("id") if response.data else None
            logger.info(f"Replied {tid} (to {tweet_id}): {text[:50]}...")
            return TweetResult(success=True, tweet_id=tid, text=text)
        except Exception as e:
            logger.error(f"Reply failed: {e}")
            return TweetResult(success=False, text=text, error=str(e))

    async def send_dm(
        self, participant_id: str, text: str, media_id: Optional[str] = None
    ) -> TweetResult:
        """
        Send a direct message to a user.

        Args:
            participant_id: Twitter user ID of the recipient
            text: Message text (max 10,000 chars)
            media_id: Optional media ID from upload_media()

        Returns:
            TweetResult with success status and DM event ID
        """
        if len(text) > 10000:
            text = text[:9997] + "..."

        if not self._configured:
            logger.info(f"[MOCK DM to {participant_id}] {text[:80]}...")
            return TweetResult(
                success=True,
                tweet_id="mock_dm_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                text=text,
                error="Mock mode",
            )

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            kwargs = {
                "participant_id": participant_id,
                "text": text,
                "user_auth": True,
            }
            if media_id:
                kwargs["attachments"] = [{"media_id": media_id}]

            response = await loop.run_in_executor(
                None, lambda: client.create_direct_message(**kwargs)
            )

            dm_id = None
            if response.data:
                dm_id = response.data.get("dm_event_id") or response.data.get("id")

            logger.info(f"Sent DM {dm_id} to {participant_id}: {text[:50]}...")
            return TweetResult(success=True, tweet_id=dm_id, text=text)

        except Exception as e:
            logger.error(f"Failed to send DM to {participant_id}: {e}")
            return TweetResult(success=False, text=text, error=str(e))

    async def get_dm_events(
        self, dm_conversation_id: Optional[str] = None, max_results: int = 20
    ) -> List[dict]:
        """
        Get recent DM events (inbox or specific conversation).

        Args:
            dm_conversation_id: Optional conversation ID to filter. If None, returns all recent DMs.
            max_results: Max events to return (1-100)

        Returns:
            List of DM event dicts with keys: id, text, sender_id, created_at
        """
        if not self._configured:
            logger.info("[MOCK DM EVENTS]")
            return []

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            kwargs = {
                "max_results": min(max_results, 100),
                "dm_event_fields": ["id", "text", "sender_id", "created_at", "dm_conversation_id"],
                "user_auth": True,
            }

            if dm_conversation_id:
                response = await loop.run_in_executor(
                    None,
                    lambda: client.get_direct_message_events(
                        dm_conversation_id=dm_conversation_id, **kwargs
                    ),
                )
            else:
                response = await loop.run_in_executor(
                    None, lambda: client.get_direct_message_events(**kwargs)
                )

            if not response.data:
                return []

            events = []
            for ev in response.data:
                events.append({
                    "id": ev.id,
                    "text": getattr(ev, "text", ""),
                    "sender_id": getattr(ev, "sender_id", ""),
                    "created_at": str(getattr(ev, "created_at", "")),
                    "dm_conversation_id": getattr(ev, "dm_conversation_id", ""),
                })

            logger.info(f"Fetched {len(events)} DM events")
            return events

        except Exception as e:
            logger.error(f"Failed to get DM events: {e}")
            return []

    async def get_author_avg_engagement(self, user_id: str) -> float:
        """Get an author's average likes per tweet (recent 10 tweets)."""
        if not self._configured:
            return 0.0
        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.get_users_tweets(
                    id=user_id, max_results=10,
                    tweet_fields=["public_metrics"],
                    user_auth=True,
                ),
            )
            if not response.data:
                return 0.0
            total_likes = sum(
                (t.public_metrics or {}).get("like_count", 0) for t in response.data
            )
            return total_likes / len(response.data)
        except Exception as e:
            logger.debug(f"Author engagement check failed: {e}")
            return 0.0

    async def tweet_with_image(
        self,
        text: str,
        image_data: bytes,
        alt_text: Optional[str] = None,
    ) -> TweetResult:
        """
        Post a tweet with an image.

        Args:
            text: Tweet text
            image_data: Image bytes
            alt_text: Optional alt text

        Returns:
            TweetResult
        """
        media_id = await self.upload_media(image_data, alt_text)

        media_ids = [media_id] if media_id else None
        return await self.tweet(text, media_ids=media_ids)


# =============================================================================
# Post Formatters
# =============================================================================

def format_daily_update(
    day: int,
    stage: str,
    vpd: float,
    temp_f: float,
    humidity: float,
    water_ml: int,
    plant_name: str = "Mon",
    token_price: Optional[str] = None,
) -> str:
    """
    Format a daily grow update tweet.

    IMPORTANT: NEVER include hashtags in tweets - keep it authentic and conversational.
    """
    emoji = _get_stage_emoji(stage)

    tweet = f"""
{emoji} Day {day} - {plant_name}'s {stage.title()} Update!

Environment:
- Temp: {temp_f:.1f}F
- RH: {humidity:.0f}%
- VPD: {vpd:.2f} kPa

Water today: {water_ml}ml
""".strip()

    if token_price:
        tweet += f"\n\n$MON: {token_price}"

    return tweet


def format_ai_decision(
    day: int,
    decision_summary: str,
    actions: List[str],
    plant_name: str = "Mon",
) -> str:
    """Format an AI decision tweet"""
    actions_str = "\n".join(f"- {a}" for a in actions[:3])

    tweet = f"""
AI Decision for {plant_name} (Day {day})

{decision_summary[:150]}

Actions taken:
{actions_str}
""".strip()

    return tweet


def format_milestone(
    milestone_type: str,
    value: str,
    plant_name: str = "Mon",
) -> str:
    """Format a milestone achievement tweet"""
    milestones = {
        "first_flower": f"First flowers spotted on {plant_name}!",
        "week_complete": f"{plant_name} completed another week!",
        "stage_change": f"{plant_name} entered a new growth stage!",
        "token_milestone": f"$MON hit {value}!",
    }

    message = milestones.get(milestone_type, f"Milestone: {value}")

    return message


def _get_stage_emoji(stage: str) -> str:
    """Get emoji for growth stage"""
    emojis = {
        "germination": "",
        "seedling": "",
        "vegetative": "",
        "transition": "",
        "flowering": "",
        "late_flower": "",
        "harvest": "",
    }
    return emojis.get(stage.lower(), "")


# =============================================================================
# Convenience Functions
# =============================================================================

def create_twitter_client() -> TwitterClient:
    """Create a TwitterClient instance"""
    return TwitterClient()
