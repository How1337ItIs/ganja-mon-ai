"""
Social Post Scheduler
=====================

Automated posting system for Grok & Mon.
Schedules and posts content at optimal times.

Integrates with:
- Agent decision cycles (post after decisions)
- Scheduled updates (morning/evening)
- Milestone triggers (holder count, price, etc.)
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from dataclasses import dataclass, field
import logging
import json
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .manager import MonSocialManager, SocialUpdate
from .xai_native import XAINativeSocial


logger = logging.getLogger(__name__)


@dataclass
class ScheduledPost:
    """A scheduled post"""
    id: str
    content: str
    scheduled_time: datetime
    posted: bool = False
    post_type: str = "manual"  # manual, daily, milestone, decision
    image_path: Optional[str] = None
    result: Optional[SocialUpdate] = None


@dataclass
class PostQueue:
    """Queue of posts to be sent"""
    posts: List[ScheduledPost] = field(default_factory=list)

    def add(self, post: ScheduledPost):
        self.posts.append(post)
        self.posts.sort(key=lambda x: x.scheduled_time)

    def get_pending(self) -> List[ScheduledPost]:
        return [p for p in self.posts if not p.posted]

    def mark_posted(self, post_id: str, result: SocialUpdate):
        for p in self.posts:
            if p.id == post_id:
                p.posted = True
                p.result = result
                break


class SocialScheduler:
    """
    Automated social posting scheduler.

    Features:
    - Scheduled daily updates (morning/evening)
    - Post-decision auto-tweets
    - Milestone triggers
    - Rate limiting
    - Queue management

    Example:
        scheduler = SocialScheduler()

        # Start scheduler
        scheduler.start()

        # Queue a post
        scheduler.queue_post("Mon's looking irie today!",
                            scheduled_time=datetime.now() + timedelta(hours=1))

        # Post immediately
        await scheduler.post_now("Breaking: Mon hit new milestone!")
    """

    def __init__(self, grow_day: int = 1, stage: str = "vegetative"):
        self.manager = MonSocialManager()
        self.xai = XAINativeSocial()
        self.scheduler = AsyncIOScheduler()

        self.grow_day = grow_day
        self.stage = stage

        self.queue = PostQueue()
        self.post_history: List[SocialUpdate] = []

        # Rate limiting
        self.min_minutes_between_posts = 30
        self.last_post_time: Optional[datetime] = None

        # State file for persistence
        self.state_file = Path("data/social_state.json")
        self._load_state()

    def _load_state(self):
        """Load scheduler state from disk"""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.grow_day = data.get("grow_day", 1)
                self.stage = data.get("stage", "vegetative")
                if data.get("last_post_time"):
                    self.last_post_time = datetime.fromisoformat(data["last_post_time"])
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")

    def _save_state(self):
        """Save scheduler state to disk"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "grow_day": self.grow_day,
            "stage": self.stage,
            "last_post_time": self.last_post_time.isoformat() if self.last_post_time else None,
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def start(self):
        """Start the scheduler with default jobs"""
        # Morning update (8 AM)
        self.scheduler.add_job(
            self._morning_update,
            CronTrigger(hour=8, minute=0),
            id="morning_update",
            replace_existing=True
        )

        # Evening update (6 PM)
        self.scheduler.add_job(
            self._evening_update,
            CronTrigger(hour=18, minute=0),
            id="evening_update",
            replace_existing=True
        )

        # Queue processor (every 5 minutes)
        self.scheduler.add_job(
            self._process_queue,
            IntervalTrigger(minutes=5),
            id="queue_processor",
            replace_existing=True
        )

        # -----------------------------------------------------------
        # Daily update at grow-light-on time (6 AM PST default)
        # Collects sensor data + AI decision, generates Rasta content,
        # and posts to Twitter + Farcaster via MonSocialManager.daily_update()
        # -----------------------------------------------------------
        light_on_hour = int(os.environ.get("LIGHT_ON_HOUR", "6"))
        self.scheduler.add_job(
            self._daily_grow_update,
            CronTrigger(hour=light_on_hour, minute=15),
            id="daily_grow_update",
            replace_existing=True,
        )

        # -----------------------------------------------------------
        # Trading summary every 6 hours
        # Reads paper portfolio and posts a performance blurb
        # -----------------------------------------------------------
        self.scheduler.add_job(
            self._trading_summary,
            IntervalTrigger(hours=6),
            id="trading_summary",
            replace_existing=True,
        )

        # -----------------------------------------------------------
        # Community engagement check every 2 hours
        # Finds engagement opportunities and logs them
        # -----------------------------------------------------------
        self.scheduler.add_job(
            self._community_engagement_check,
            IntervalTrigger(hours=2),
            id="community_engagement",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Social scheduler started (with grow-update, trading-summary, engagement jobs)")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self._save_state()
        logger.info("Social scheduler stopped")

    async def _get_real_sensor_data(self) -> tuple:
        """Get real sensor data from Govee sensors"""
        vpd = None
        health = "UNKNOWN"

        try:
            from hardware.govee import GoveeSensorHub
            govee = GoveeSensorHub()
            if await govee.is_connected():
                reading = await govee.read_all()
                vpd = reading.vpd
                # Determine health based on VPD
                if vpd:
                    if 0.8 <= vpd <= 1.3:
                        health = "GOOD"
                    elif 0.6 <= vpd <= 1.5:
                        health = "OK"
                    else:
                        health = "NEEDS ATTENTION"
        except Exception as e:
            logger.warning(f"Could not read sensors: {e}")

        return vpd, health

    async def _morning_update(self):
        """Generate and post morning update"""
        logger.info("Generating morning update...")

        # Get REAL sensor data
        vpd, health = await self._get_real_sensor_data()

        if vpd is None:
            logger.warning("No sensor data available for morning update - skipping post")
            return

        result = await self.manager.post_daily_update(
            day=self.grow_day,
            vpd=vpd,
            health=health,
            stage=self.stage,
            event="Morning check-in"
        )

        if result.posted:
            self.post_history.append(result)
            self.last_post_time = datetime.now()
            self._save_state()

    async def _evening_update(self):
        """Generate and post evening summary"""
        logger.info("Generating evening update...")

        # Get REAL sensor data
        vpd, health = await self._get_real_sensor_data()

        if vpd is None:
            logger.warning("No sensor data available for evening update - skipping post")
            return

        result = await self.manager.post_daily_update(
            day=self.grow_day,
            vpd=vpd,
            health=health,
            stage=self.stage,
            event="Evening wrap-up"
        )

        if result.posted:
            self.post_history.append(result)
            self.last_post_time = datetime.now()
            self._save_state()

    async def _daily_grow_update(self):
        """Daily update at grow-light-on: sensor data + AI decision + Rasta content to Twitter/Farcaster."""
        logger.info("Running daily grow update (light-on trigger)...")
        try:
            result = await self.manager.daily_update()
            if result.get("twitter", {}).get("posted") or result.get("farcaster", {}).get("posted"):
                self.last_post_time = datetime.now()
                self._save_state()
            logger.info(f"Daily grow update result: {result}")
        except Exception as exc:
            logger.error(f"Daily grow update failed: {exc}")

    async def _trading_summary(self):
        """Post a trading performance summary every 6 hours."""
        logger.info("Generating trading summary...")
        try:
            from .engagement_daemon import EngagementDaemon

            daemon = EngagementDaemon()
            portfolio = daemon._get_live_portfolio()

            if not portfolio:
                logger.debug("No portfolio data available for trading summary")
                return

            cash = portfolio.get("current_cash", 0)
            starting = portfolio.get("starting_balance", 1000)
            trades = portfolio.get("trades", [])
            open_trades = [t for t in trades if t.get("is_open")]
            total_pnl = sum(t.get("pnl_usd", 0) for t in trades)
            win_count = sum(1 for t in trades if t.get("pnl_usd", 0) > 0)
            total_count = len(trades)
            win_rate = (win_count / total_count * 100) if total_count > 0 else 0

            from .engagement_daemon import generate_content

            text = await generate_content(
                f"Drop a trading performance update -- FULL Rasta character.\n"
                f"Portfolio: ${cash:.0f} cash, {len(open_trades)} open positions.\n"
                f"Total PnL: ${total_pnl:.0f}, Win rate: {win_rate:.0f}% ({win_count}/{total_count}).\n"
                f"Starting balance was ${starting:.0f}.\n"
                f"Be honest about wins AND losses. Under 260 chars. NFA naturally. Just the post text.",
                max_tokens=150,
            )

            if text:
                # Post to Farcaster (primary)
                try:
                    from .farcaster import FarcasterClient
                    fc = FarcasterClient()
                    await fc.post(text[:280], embed_url="https://grokandmon.com")
                    logger.info(f"Trading summary posted to Farcaster: {text[:60]}...")
                except Exception as e:
                    logger.error(f"Trading summary Farcaster error: {e}")

                # Record in tracker
                try:
                    from src.learning.social_tracker import get_social_tracker
                    tracker = get_social_tracker()
                    tracker.record_post("farcaster", "trade_call", len(text))
                    tracker.export_json()
                except Exception:
                    pass

        except Exception as exc:
            logger.error(f"Trading summary failed: {exc}")

    async def _community_engagement_check(self):
        """Check for community engagement opportunities every 2 hours."""
        logger.info("Running community engagement check...")
        try:
            opportunities = await self.manager.find_engagement()
            sentiment = await self.manager.get_community_sentiment("AI cannabis grow crypto")

            # Log findings for the engagement daemon to pick up
            engagement_file = Path("data/engagement_opportunities.json")
            engagement_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "opportunities": opportunities,
                "sentiment_summary": sentiment.get("analysis", "")[:500],
            }
            engagement_file.write_text(json.dumps(data, indent=2))
            logger.info(f"Community engagement check: {len(opportunities)} opportunities found")

        except Exception as exc:
            logger.error(f"Community engagement check failed: {exc}")

    async def _process_queue(self):
        """Process pending posts in queue"""
        now = datetime.now()

        for post in self.queue.get_pending():
            if post.scheduled_time <= now:
                if self._can_post():
                    logger.info(f"Processing queued post: {post.id}")
                    result = await self._post_content(post.content, post.image_path)
                    self.queue.mark_posted(post.id, result)

                    if result.posted:
                        self.last_post_time = datetime.now()
                        self._save_state()

    def _can_post(self) -> bool:
        """Check if we can post (rate limiting)"""
        if self.last_post_time is None:
            return True

        minutes_since = (datetime.now() - self.last_post_time).total_seconds() / 60
        return minutes_since >= self.min_minutes_between_posts

    async def _post_content(
        self,
        content: str,
        image_path: Optional[str] = None
    ) -> SocialUpdate:
        """Post content to Twitter"""
        image_data = None
        if image_path and Path(image_path).exists():
            image_data = Path(image_path).read_bytes()

        update = SocialUpdate(text=content, image_data=image_data)

        try:
            if image_data:
                result = await self.manager.twitter.tweet_with_image(content, image_data)
            else:
                result = await self.manager.twitter.tweet(content)

            update.posted = result.success
            update.tweet_id = result.tweet_id
            update.error = result.error

        except Exception as e:
            update.error = str(e)

        return update

    def queue_post(
        self,
        content: str,
        scheduled_time: Optional[datetime] = None,
        image_path: Optional[str] = None,
        post_type: str = "manual"
    ) -> str:
        """
        Queue a post for later.

        Args:
            content: Tweet text
            scheduled_time: When to post (default: now)
            image_path: Optional image file path
            post_type: Type of post (manual, milestone, decision)

        Returns:
            Post ID
        """
        post_id = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.queue.posts)}"

        post = ScheduledPost(
            id=post_id,
            content=content,
            scheduled_time=scheduled_time or datetime.now(),
            post_type=post_type,
            image_path=image_path
        )

        self.queue.add(post)
        logger.info(f"Queued post {post_id} for {post.scheduled_time}")

        return post_id

    async def post_now(
        self,
        content: str,
        image_path: Optional[str] = None,
        bypass_rate_limit: bool = False
    ) -> SocialUpdate:
        """
        Post immediately.

        Args:
            content: Tweet text
            image_path: Optional image
            bypass_rate_limit: Skip rate limiting check

        Returns:
            SocialUpdate with results
        """
        if not bypass_rate_limit and not self._can_post():
            minutes_left = self.min_minutes_between_posts
            if self.last_post_time:
                elapsed = (datetime.now() - self.last_post_time).total_seconds() / 60
                minutes_left = self.min_minutes_between_posts - elapsed

            return SocialUpdate(
                text=content,
                error=f"Rate limited. Wait {minutes_left:.0f} more minutes."
            )

        result = await self._post_content(content, image_path)

        if result.posted:
            self.post_history.append(result)
            self.last_post_time = datetime.now()
            self._save_state()

        return result

    async def post_decision(
        self,
        decision: dict,
        vpd: float,
        health: str,
        image_data: Optional[bytes] = None
    ) -> Optional[SocialUpdate]:
        """
        Post after an AI decision cycle.

        Called by the agent after making decisions.
        Only posts if decision contains notable actions.
        """
        actions = decision.get("actions", [])
        if not actions:
            return None

        # Generate post about the decision
        action_summary = ", ".join(actions[:2])

        post = await self.xai.generate_mon_post(
            day=self.grow_day,
            vpd=vpd,
            health=health,
            stage=self.stage,
            event=f"Just took action: {action_summary}"
        )

        return await self.post_now(post.text, bypass_rate_limit=False)

    async def post_milestone(
        self,
        milestone_type: str,
        description: str,
        image_data: Optional[bytes] = None
    ) -> SocialUpdate:
        """
        Post a milestone achievement.

        Milestones bypass normal rate limiting.
        """
        result = await self.manager.post_milestone(
            milestone_type=milestone_type,
            description=description,
            day=self.grow_day,
            image_data=image_data
        )

        if result.posted:
            self.post_history.append(result)
            self.last_post_time = datetime.now()
            self._save_state()

        return result

    def update_grow_info(self, day: int, stage: str):
        """Update current grow day and stage"""
        self.grow_day = day
        self.stage = stage
        self._save_state()

    def get_stats(self) -> dict:
        """Get scheduler statistics"""
        return {
            "grow_day": self.grow_day,
            "stage": self.stage,
            "posts_today": len([
                p for p in self.post_history
                if p.timestamp and p.timestamp.date() == datetime.now().date()
            ]),
            "total_posts": len(self.post_history),
            "queue_size": len(self.queue.get_pending()),
            "last_post": self.last_post_time.isoformat() if self.last_post_time else None,
            "can_post_now": self._can_post(),
            "scheduler_running": self.scheduler.running
        }


# =============================================================================
# Pre-Built Post Templates
# =============================================================================

LAUNCH_DAY_POSTS = [
    {
        "time": "07:00",
        "content": "Day 1. Mon is live. Grok is in control.\n\nThe world's first AI-autonomous cannabis grow.\n\nWatch it happen: grokandmon.com",
        "type": "launch"
    },
    {
        "time": "12:00",
        "content": "6 hours in. Mon's environment:\n\nTemp: {temp}F\nRH: {humidity}%\nVPD: {vpd} kPa\n\nGrok's first decisions working smoothly.",
        "type": "update"
    },
    {
        "time": "18:00",
        "content": "Day 1 complete!\n\nMon survived her first day under AI control.\n\nGrok made {decisions} autonomous decisions.\n\nThis is just the beginning.",
        "type": "recap"
    }
]


def create_launch_day_scheduler(grow_day: int = 1) -> SocialScheduler:
    """Create scheduler pre-loaded with launch day posts"""
    scheduler = SocialScheduler(grow_day=grow_day, stage="seedling")

    today = datetime.now().date()

    for post_template in LAUNCH_DAY_POSTS:
        hour, minute = map(int, post_template["time"].split(":"))
        scheduled_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))

        # Skip if time has passed
        if scheduled_time <= datetime.now():
            continue

        scheduler.queue_post(
            content=post_template["content"],
            scheduled_time=scheduled_time,
            post_type=post_template["type"]
        )

    return scheduler


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from dotenv import load_dotenv
    load_dotenv()

    async def test():
        print("Testing Social Scheduler...")

        scheduler = SocialScheduler(grow_day=1, stage="seedling")

        print("\n1. Stats:")
        print(scheduler.get_stats())

        print("\n2. Queueing test post...")
        post_id = scheduler.queue_post(
            "Test post from scheduler!",
            scheduled_time=datetime.now() + timedelta(minutes=1)
        )
        print(f"Queued: {post_id}")

        print("\n3. Generating post with Grok...")
        post = await scheduler.xai.generate_mon_post(
            day=1,
            vpd=1.05,
            health="GOOD",
            stage="seedling",
            event="First day alive!"
        )
        print(f"Generated: {post.text}")

        print("\n4. Final stats:")
        print(scheduler.get_stats())

    asyncio.run(test())
