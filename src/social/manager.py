"""
Grok & Mon Social Manager
=========================

Combines xAI-native intelligence with Twitter posting:
- Uses Grok to generate on-brand posts
- Uses x_search for community monitoring
- Posts to X via Twitter API (until xAI adds native posting)

The brains are xAI, the mouth is Twitter API.
"""

import os
import asyncio
import base64
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import logging

from src.voice.personality import get_tweet_prompt, enforce_voice

from .xai_native import XAINativeSocial, GeneratedPost
from .twitter import TwitterClient, TweetResult

logger = logging.getLogger(__name__)

# Grok API settings for daily_update
_XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
_XAI_BASE_URL = "https://api.x.ai/v1"
_GROK_MODEL = "grok-4-1-fast-non-reasoning"


@dataclass
class SocialUpdate:
    """Complete social update with all components"""
    text: str
    image_data: Optional[bytes] = None
    image_alt: Optional[str] = None
    generated_by: str = "grok"
    posted: bool = False
    tweet_id: Optional[str] = None
    error: Optional[str] = None


class MonSocialManager:
    """
    Manages all social activity for Mon the cannabis plant.
    
    Uses Grok (xAI) for:
    - Generating witty, on-brand posts
    - Searching X for relevant conversations
    - Analyzing community sentiment
    
    Uses Twitter API for:
    - Actually posting tweets
    - Uploading plant images
    
    Example:
        manager = MonSocialManager()
        
        # Post a daily update with image
        result = await manager.post_daily_update(
            day=15,
            vpd=1.05,
            health="EXCELLENT",
            stage="vegetative",
            image_data=webcam_bytes
        )
        
        # Find engagement opportunities
        opportunities = await manager.find_engagement()
    """
    
    def __init__(self):
        # xAI for intelligence
        self.xai = XAINativeSocial()
        
        # Twitter for posting
        self.twitter = TwitterClient()
        
        # Track posting history
        self.post_history = []
        self.last_post_time = None
        
        # Rate limiting
        self.min_hours_between_posts = 4
        
    async def post_daily_update(
        self,
        day: int,
        vpd: float,
        health: str,
        stage: str = "vegetative",
        image_data: Optional[bytes] = None,
        event: Optional[str] = None,
        token_price: Optional[str] = None,
        force: bool = False,
    ) -> SocialUpdate:
        """
        Post a daily grow update to X.
        
        Args:
            day: Current grow day
            vpd: VPD reading in kPa
            health: Health status string
            stage: Growth stage
            image_data: Optional webcam image bytes
            event: Optional special event to highlight
            token_price: Optional $MON price to include
            force: Bypass rate limiting
            
        Returns:
            SocialUpdate with results
        """
        # Rate limiting check
        if not force and self.last_post_time:
            hours_since = (datetime.now() - self.last_post_time).total_seconds() / 3600
            if hours_since < self.min_hours_between_posts:
                return SocialUpdate(
                    text="",
                    error=f"Rate limited. Wait {self.min_hours_between_posts - hours_since:.1f} more hours.",
                    posted=False
                )
        
        # Generate post with Grok
        logger.info("Generating post with Grok...")
        generated = await self.xai.generate_mon_post(
            day=day,
            vpd=vpd,
            health=health,
            stage=stage,
            event=event,
            include_price=token_price
        )
        
        update = SocialUpdate(
            text=generated.text,
            image_data=image_data,
            image_alt=f"Mon the cannabis plant on day {day} - {stage} stage",
            generated_by="grok"
        )
        
        # Post to Twitter
        logger.info(f"Posting to X: {generated.text[:50]}...")
        
        try:
            if image_data:
                result = await self.twitter.tweet_with_image(
                    text=generated.text,
                    image_data=image_data,
                    alt_text=update.image_alt
                )
            else:
                result = await self.twitter.tweet(generated.text)
            
            update.posted = result.success
            update.tweet_id = result.tweet_id
            update.error = result.error
            
            if result.success:
                self.last_post_time = datetime.now()
                self.post_history.append({
                    "timestamp": self.last_post_time.isoformat(),
                    "day": day,
                    "text": generated.text,
                    "tweet_id": result.tweet_id
                })
                logger.info(f"Posted successfully: {result.tweet_id}")
            else:
                logger.warning(f"Post failed: {result.error}")
                
        except Exception as e:
            update.error = str(e)
            logger.error(f"Post exception: {e}")
        
        return update
    
    async def post_milestone(
        self,
        milestone_type: str,
        description: str,
        day: int,
        image_data: Optional[bytes] = None,
    ) -> SocialUpdate:
        """
        Post a milestone achievement.
        
        Milestones:
        - first_leaves: First true leaves
        - week_complete: Weekly milestone
        - stage_transition: New growth stage
        - flower_start: Flowering begins
        - trichomes: Trichome development
        - harvest_ready: Ready for harvest
        """
        prompt = f"""Generate a celebratory X post for Mon the cannabis plant.
Milestone: {milestone_type} - {description}
Day: {day}

Make it exciting but authentic, Jamaican vibes, 1-2 hashtags.
Max 280 chars. Just the tweet text."""

        # Use Grok directly for custom milestone
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.xai.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.xai.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.xai.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.9
                }
            )
            
            text = response.json()["choices"][0]["message"]["content"].strip()
        
        update = SocialUpdate(
            text=text,
            image_data=image_data,
            image_alt=f"Mon milestone: {milestone_type}"
        )
        
        # Post it
        if image_data:
            result = await self.twitter.tweet_with_image(text, image_data)
        else:
            result = await self.twitter.tweet(text)
        
        update.posted = result.success
        update.tweet_id = result.tweet_id
        update.error = result.error
        
        return update
    
    async def find_engagement(self) -> list:
        """
        Find posts to potentially engage with.
        
        Searches for:
        - #AICannabis discussions
        - Monad blockchain mentions
        - AI grow projects
        """
        results = await self.xai.search_x(
            "#AICannabis OR #Monad OR #AIGrow OR 'AI cannabis'",
            limit=10
        )
        return [{"query": results.query, "output": results.raw_output}]
    
    async def get_community_sentiment(self, topic: str = "AI cannabis") -> dict:
        """Get current sentiment around a topic."""
        return await self.xai.analyze_sentiment(topic)
    
    async def generate_reply(self, tweet_text: str, context: str = "") -> str:
        """
        Generate a reply to a tweet in Mon's voice.
        
        Args:
            tweet_text: The tweet to reply to
            context: Additional context about the conversation
            
        Returns:
            Reply text
        """
        prompt = f"""You are Mon's Grok - the AI caretaker of cannabis plant Mon.
Generate a friendly reply to this tweet:

Tweet: "{tweet_text}"
{f'Context: {context}' if context else ''}

Rules:
- Be friendly and helpful
- Cannabis/AI knowledge welcome
- Jamaican vibes, but don't overdo it
- Max 280 chars
- No hashtags in replies usually

Just the reply text:"""

        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.xai.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.xai.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.xai.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.8
                }
            )
            
            return response.json()["choices"][0]["message"]["content"].strip()
    
    async def daily_update(self) -> dict:
        """
        Full daily update pipeline: collect sensor data, generate Rasta Mon
        voice content via Grok, and post to Twitter + Farcaster.

        Returns a dict summarising what was posted and any errors.
        """
        import httpx

        results: dict = {
            "sensor_data": None,
            "content": None,
            "twitter": None,
            "farcaster": None,
            "errors": [],
        }

        # ------------------------------------------------------------------
        # 1. Collect live sensor data from the Chromebook server
        # ------------------------------------------------------------------
        sensor_data = await self._collect_sensor_data()
        results["sensor_data"] = sensor_data

        vpd = sensor_data.get("vpd", 1.0)
        temp_f = sensor_data.get("temperature_f", 77.0)
        humidity = sensor_data.get("humidity", 55.0)
        health = "GOOD" if 0.8 <= vpd <= 1.3 else ("OK" if 0.6 <= vpd <= 1.5 else "NEEDS ATTENTION")
        grow_day = int(os.getenv("GROW_DAY", "1"))
        stage = os.getenv("GROWTH_STAGE", "vegetative")

        # ------------------------------------------------------------------
        # 2. Generate Rasta Mon content via Grok
        # ------------------------------------------------------------------
        content = await self._generate_rasta_content(
            vpd=vpd,
            temp_f=temp_f,
            humidity=humidity,
            health=health,
            grow_day=grow_day,
            stage=stage,
        )
        if not content:
            content = (
                f"Day {grow_day}: Mon vibin at {vpd:.2f} VPD, {temp_f:.0f}F. "
                f"Health: {health}. Irie ting, ya dun know."
            )
        results["content"] = content

        # ------------------------------------------------------------------
        # 3. Post to Twitter
        # ------------------------------------------------------------------
        try:
            tweet_text = content[:280]
            tweet_result = await self.twitter.tweet(tweet_text)
            results["twitter"] = {
                "posted": tweet_result.success,
                "tweet_id": tweet_result.tweet_id,
                "error": tweet_result.error,
            }
            if tweet_result.success:
                self.last_post_time = datetime.now()
                self.post_history.append({
                    "platform": "twitter",
                    "timestamp": self.last_post_time.isoformat(),
                    "text": tweet_text,
                    "tweet_id": tweet_result.tweet_id,
                })
        except Exception as exc:
            err = f"Twitter post error: {exc}"
            logger.error(err)
            results["twitter"] = {"posted": False, "error": err}
            results["errors"].append(err)

        # ------------------------------------------------------------------
        # 4. Post to Farcaster
        # ------------------------------------------------------------------
        try:
            from .farcaster import FarcasterClient
            fc = FarcasterClient()
            cast_text = content[:280]
            cast_result = await fc.post(cast_text, embed_url="https://grokandmon.com")
            results["farcaster"] = {
                "posted": cast_result.success,
                "cast_hash": cast_result.cast_hash,
                "error": cast_result.error,
            }
            if cast_result.success:
                self.post_history.append({
                    "platform": "farcaster",
                    "timestamp": datetime.now().isoformat(),
                    "text": cast_text,
                    "cast_hash": cast_result.cast_hash,
                })
        except Exception as exc:
            err = f"Farcaster post error: {exc}"
            logger.error(err)
            results["farcaster"] = {"posted": False, "error": err}
            results["errors"].append(err)

        # ------------------------------------------------------------------
        # 5. Record in social tracker
        # ------------------------------------------------------------------
        try:
            from src.learning.social_tracker import get_social_tracker
            tracker = get_social_tracker()
            if results.get("twitter", {}).get("posted"):
                tracker.record_post("twitter", "plant_update", len(content))
            if results.get("farcaster", {}).get("posted"):
                tracker.record_post("farcaster", "plant_update", len(content))
            tracker.export_json()
        except Exception:
            pass

        logger.info(
            f"daily_update complete: twitter={results['twitter']}, "
            f"farcaster={results['farcaster']}"
        )
        return results

    # ------------------------------------------------------------------
    # Helpers for daily_update
    # ------------------------------------------------------------------

    async def _collect_sensor_data(self) -> dict:
        """Pull latest sensor readings. Tries local API, then mock defaults."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("http://localhost:8000/api/sensors/latest")
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "vpd": data.get("vpd_kpa") or data.get("vpd") or 1.0,
                        "temperature_f": data.get("temperature_f") or data.get("temp_f") or 77.0,
                        "humidity": data.get("humidity") or data.get("rh") or 55.0,
                    }
        except Exception as exc:
            logger.debug(f"Sensor API unavailable: {exc}")

        # Fallback mock
        return {"vpd": 1.0, "temperature_f": 77.0, "humidity": 55.0}

    async def _generate_rasta_content(
        self,
        vpd: float,
        temp_f: float,
        humidity: float,
        health: str,
        grow_day: int,
        stage: str,
    ) -> str:
        """Generate Rasta Mon voice content via Grok."""
        import httpx

        if not _XAI_API_KEY:
            return ""

        prompt = get_tweet_prompt(
            day=grow_day,
            vpd=vpd,
            health=health,
            stage=stage,
        )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{_XAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {_XAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": _GROK_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.85,
                    },
                )
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    return enforce_voice(text)
        except Exception as exc:
            logger.error(f"Rasta content generation error: {exc}")

        return ""

    def get_stats(self) -> dict:
        """Get social posting statistics."""
        return {
            "total_posts": len(self.post_history),
            "last_post": self.last_post_time.isoformat() if self.last_post_time else None,
            "twitter_configured": self.twitter._configured,
            "recent_posts": self.post_history[-5:] if self.post_history else []
        }


# =============================================================================
# Integration with Agent
# =============================================================================

async def post_from_decision(
    decision: dict,
    day: int,
    vpd: float,
    health: str,
    stage: str,
    image_data: Optional[bytes] = None,
) -> Optional[SocialUpdate]:
    """
    Post to X based on an AI decision cycle.
    
    Called from the agent after each decision if social_post is generated.
    
    Args:
        decision: The Grok decision dict (may contain social_post key)
        day: Current grow day
        vpd: VPD reading
        health: Health status
        stage: Growth stage
        image_data: Optional webcam capture
        
    Returns:
        SocialUpdate if posted, None if no post generated
    """
    # Check if decision has a social post
    social_post = decision.get("social_post")
    if not social_post:
        return None
    
    manager = MonSocialManager()
    
    # Use the pre-generated post text, or generate fresh
    update = SocialUpdate(text=social_post, image_data=image_data)
    
    try:
        if image_data:
            result = await manager.twitter.tweet_with_image(
                social_post, 
                image_data,
                alt_text=f"Mon day {day}"
            )
        else:
            result = await manager.twitter.tweet(social_post)
        
        update.posted = result.success
        update.tweet_id = result.tweet_id
        update.error = result.error
        
    except Exception as e:
        update.error = str(e)
    
    return update


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("Testing MonSocialManager...")
        manager = MonSocialManager()
        
        print("\n1. Getting community sentiment...")
        sentiment = await manager.get_community_sentiment("AI cannabis grow")
        print(f"Sentiment: {sentiment.get('analysis', '')[:300]}...")
        
        print("\n2. Finding engagement opportunities...")
        opportunities = await manager.find_engagement()
        print(f"Found: {opportunities[0].get('output', '')[:300]}...")
        
        print("\n3. Generating daily update (not posting)...")
        from .xai_native import XAINativeSocial
        xai = XAINativeSocial()
        post = await xai.generate_mon_post(
            day=7,
            vpd=0.95,
            health="GOOD",
            stage="clone",
            event="Roots showing at clone collar!"
        )
        print(f"Would post: {post.text}")
        
        print("\n4. Stats:")
        print(manager.get_stats())
        
    import sys
    sys.path.insert(0, ".")
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test())
