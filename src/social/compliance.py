"""
X/Twitter Compliance Configuration
===================================

Safe automation settings based on X's 2025 policies.
Designed to stay well under rate limits and avoid ban triggers.

Key Rules:
- Max 4 posts per day (well under 500/month free tier)
- Minimum 4 hours between posts
- Unique AI-generated content only
- Bot disclosure required in bio
- No automated engagement (likes/follows/replies)
"""

from datetime import datetime, time
from typing import Optional
import os


class XComplianceConfig:
    """
    X/Twitter automation compliance settings.
    
    Conservative limits to ensure Mon never gets banned.
    """
    
    # Posting frequency limits — originals
    MAX_POSTS_PER_DAY = 4
    MIN_HOURS_BETWEEN_POSTS = 4
    MAX_POSTS_PER_MONTH = 100  # Well under 500 free tier limit

    # Interactive limits — quote tweets & mention replies
    MAX_QUOTES_PER_DAY = 2       # Rasta parody QTs
    MAX_REPLIES_PER_DAY = 4      # Mention-based replies only (user opted in)
    MIN_HOURS_BETWEEN_QUOTES = 4
    
    # ==========================================================================
    # OPTIMIZED POSTING WINDOWS FOR GLOBAL CRYPTO TWITTER
    # ==========================================================================
    # 
    # Research findings (2025):
    # - Asia-Pacific: 43% of Crypto Twitter (India, Singapore, Japan, Korea)
    # - North America: 17% (US dominates)  
    # - Europe: 15% (UK, Germany)
    # - Africa: 10% (Nigeria leads)
    #
    # Key insight: London-New York overlap (13:00-16:00 UTC) = primetime
    #
    # Times below are in PST (UTC-8). Mon is in California.
    # 
    POSTING_WINDOWS = [
        # Slot 1: 5-6 AM PST = 8-9 AM EST = 1-2 PM London
        # Catches: US East Coast waking up + Europe lunch + UK afternoon
        (time(5, 0), time(6, 30)),
        
        # Slot 2: 9-10 AM PST = 12-1 PM EST = 5-6 PM London  
        # Catches: US lunch break + Europe evening + PEAK ENGAGEMENT
        (time(9, 0), time(10, 30)),
        
        # Slot 3: 1-2 PM PST = 4-5 PM EST = 9-10 PM London
        # Catches: US afternoon + Europe night owls + Asia waking (9 PM = 5 AM Tokyo)
        (time(13, 0), time(14, 30)),
        
        # Slot 4: 5-6 PM PST = 8-9 PM EST = 9-10 AM Tokyo/Singapore next day
        # Catches: US evening + ASIA MORNING (huge market: India, Singapore, Korea)
        (time(17, 0), time(18, 30)),
        
        # Slot 5: 9-10 PM PST = Midnight EST = 1-2 PM Tokyo/Singapore
        # Catches: US night crypto crowd + Asia afternoon peak
        (time(21, 0), time(22, 30)),
    ]
    
    # Day-of-week multipliers (Tue-Thu = peak, weekend = lower)
    BEST_DAYS = ["Tuesday", "Wednesday", "Thursday"]
    GOOD_DAYS = ["Monday", "Friday"]
    WEEKEND_DAYS = ["Saturday", "Sunday"]
    
    # Content requirements — X Premium allows longer posts
    MIN_CHARS = 50
    MAX_CHARS = 4000             # X Premium max
    MAX_CHARS_ORIGINAL = 280     # Keep originals short and punchy
    MAX_CHARS_QUOTE = 1000       # QT translations can breathe — match source length
    MAX_CHARS_REPLY = 500        # Replies more conversational
    REQUIRED_HASHTAGS = []  # NO HASHTAGS - keep tweets authentic
    MAX_HASHTAGS = 0  # NEVER use hashtags
    
    # Bot disclosure (required by X policy)
    BIO_TEMPLATE = "🤖 Automated | Grok AI a grow one ganja plant name Mon yuh know! Real herb + IoT sensors + cross-chain alpha. $MON on Monad. Jah bless 🌱"
    
    # Prohibited actions (will trigger bans)
    PROHIBITED = [
        "auto_follow",
        "auto_unfollow",
        "auto_like",
        "auto_retweet",
        "keyword_reply",
        "unsolicited_reply",  # NEVER reply unless user @mentioned us first
        "bulk_dm",
        "cross_account_posting",
    ]

    # Search queries for finding QT candidates (rotated)
    QT_SEARCH_QUERIES = [
        "monad -is:retweet -is:reply lang:en",
        "memecoin -is:retweet -is:reply lang:en",
        "cannabis grow -is:retweet -is:reply lang:en",
    ]

    # Author quality thresholds for QT targets
    QT_MIN_AUTHOR_FOLLOWERS = 1000
    QT_MIN_AUTHOR_AVG_LIKES = 10  # Historical avg likes/tweet
    
    @classmethod
    def is_in_posting_window(cls) -> bool:
        """Check if current time is within a posting window."""
        now = datetime.now().time()
        for start, end in cls.POSTING_WINDOWS:
            if start <= now <= end:
                return True
        return False
    
    @classmethod
    def get_next_window(cls) -> Optional[time]:
        """Get the next posting window start time."""
        now = datetime.now().time()
        for start, end in cls.POSTING_WINDOWS:
            if now < start:
                return start
        # Wrap to tomorrow's first window
        return cls.POSTING_WINDOWS[0][0]
    
    @classmethod
    def validate_post(cls, text: str, post_type: str = "original") -> tuple[bool, str]:
        """
        Validate a post before sending.

        Args:
            text: The post text.
            post_type: "original", "quote", or "reply" — determines char limit.

        Returns:
            (is_valid, error_message)
        """
        if len(text) < cls.MIN_CHARS:
            return False, f"Post too short ({len(text)} chars, min {cls.MIN_CHARS})"

        max_chars = {
            "original": cls.MAX_CHARS_ORIGINAL,
            "quote": cls.MAX_CHARS_QUOTE,
            "reply": cls.MAX_CHARS_REPLY,
        }.get(post_type, cls.MAX_CHARS)

        if len(text) > max_chars:
            return False, f"Post too long ({len(text)} chars, max {max_chars} for {post_type})"

        # NEVER allow hashtags - keep tweets authentic
        hashtag_count = text.count("#")
        if hashtag_count > 0:
            return False, f"Hashtags not allowed ({hashtag_count} found). Keep tweets authentic."

        # Block leaf emoji (🌿) - it's not actually cannabis
        if "\U0001f33f" in text:
            return False, "Leaf emoji (🌿) not allowed — it's not cannabis."

        return True, ""
    
    @classmethod
    def should_post(
        cls,
        posts_today: int,
        posts_this_month: int,
        last_post_time: Optional[datetime],
        force: bool = False
    ) -> tuple[bool, str]:
        """
        Determine if we should post right now.
        
        Args:
            posts_today: Number of posts already made today
            posts_this_month: Number of posts this month
            last_post_time: Timestamp of last post
            force: Bypass some checks (for milestones)
            
        Returns:
            (should_post, reason)
        """
        # Check daily limit
        if posts_today >= cls.MAX_POSTS_PER_DAY and not force:
            return False, f"Daily limit reached ({posts_today}/{cls.MAX_POSTS_PER_DAY})"
        
        # Check monthly limit
        if posts_this_month >= cls.MAX_POSTS_PER_MONTH:
            return False, f"Monthly limit reached ({posts_this_month}/{cls.MAX_POSTS_PER_MONTH})"
        
        # Check time since last post
        if last_post_time and not force:
            hours_since = (datetime.now() - last_post_time).total_seconds() / 3600
            if hours_since < cls.MIN_HOURS_BETWEEN_POSTS:
                remaining = cls.MIN_HOURS_BETWEEN_POSTS - hours_since
                return False, f"Too soon. Wait {remaining:.1f} more hours."
        
        # Check posting window (soft requirement)
        if not cls.is_in_posting_window() and not force:
            next_window = cls.get_next_window()
            return False, f"Outside posting window. Next window: {next_window}"
        
        return True, "OK to post"


class PostingTracker:
    """
    Tracks posting history to enforce limits.
    
    Persists to disk to survive restarts.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_file = f"{data_dir}/posting_history.json"
        self.history = self._load()
    
    def _load(self) -> dict:
        """Load posting history from disk."""
        import json
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"posts": [], "daily_counts": {}, "monthly_counts": {}}
    
    def _save(self):
        """Save posting history to disk."""
        import json
        import os
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def record_post(self, tweet_id: str, text: str):
        """Record a successful post."""
        now = datetime.now()
        date_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")
        
        self.history["posts"].append({
            "tweet_id": tweet_id,
            "text": text[:100],
            "timestamp": now.isoformat()
        })
        
        # Update daily count
        self.history["daily_counts"][date_key] = self.history["daily_counts"].get(date_key, 0) + 1
        
        # Update monthly count
        self.history["monthly_counts"][month_key] = self.history["monthly_counts"].get(month_key, 0) + 1
        
        # Keep only last 100 posts in history
        if len(self.history["posts"]) > 100:
            self.history["posts"] = self.history["posts"][-100:]
        
        self._save()
    
    def get_posts_today(self) -> int:
        """Get number of posts made today."""
        date_key = datetime.now().strftime("%Y-%m-%d")
        return self.history["daily_counts"].get(date_key, 0)
    
    def get_posts_this_month(self) -> int:
        """Get number of posts made this month."""
        month_key = datetime.now().strftime("%Y-%m")
        return self.history["monthly_counts"].get(month_key, 0)
    
    def get_last_post_time(self) -> Optional[datetime]:
        """Get timestamp of last post."""
        if not self.history["posts"]:
            return None
        last = self.history["posts"][-1]
        return datetime.fromisoformat(last["timestamp"])
    
    def can_post_now(self, force: bool = False) -> tuple[bool, str]:
        """Check if we can post right now."""
        return XComplianceConfig.should_post(
            posts_today=self.get_posts_today(),
            posts_this_month=self.get_posts_this_month(),
            last_post_time=self.get_last_post_time(),
            force=force
        )
    
    def get_stats(self) -> dict:
        """Get posting statistics."""
        return {
            "posts_today": self.get_posts_today(),
            "posts_this_month": self.get_posts_this_month(),
            "daily_limit": XComplianceConfig.MAX_POSTS_PER_DAY,
            "monthly_limit": XComplianceConfig.MAX_POSTS_PER_MONTH,
            "last_post": self.get_last_post_time(),
            "in_posting_window": XComplianceConfig.is_in_posting_window(),
            "next_window": str(XComplianceConfig.get_next_window()),
        }


# =============================================================================
# Preset post templates for variety
# =============================================================================

POST_TEMPLATES = [
    # Status updates
    "Day {day}: Mon's VPD at {vpd}kPa. {health_emoji} {commentary}",
    "{health_emoji} Day {day} check-in! {commentary} VPD: {vpd}kPa",
    "Mon update | Day {day} | {stage} | VPD {vpd} | {commentary}",

    # Morning posts
    "☀️ Good morning! Day {day} for Mon. {commentary}",
    "Rise and shine! Mon's Day {day} begins. {commentary}",

    # Evening posts
    "🌙 End of Day {day}. {commentary} VPD holding at {vpd}kPa.",
    "Night check: Mon's Day {day} complete. {commentary}",

    # Milestone posts
    "🎉 MILESTONE: {milestone}! Day {day}. {commentary}",
    "Big day for Mon! {milestone} on Day {day}. {commentary}",
]

HEALTH_EMOJIS = {
    "EXCELLENT": "\U0001f331",  # 🌱 seedling (NOT 🌿 leaf — that ain't cannabis)
    "GOOD": "✅",
    "FAIR": "⚠️",
    "POOR": "🔶",
    "CRITICAL": "🚨",
}


def format_compliant_post(
    day: int,
    vpd: float,
    health: str,
    stage: str,
    commentary: str,
    milestone: Optional[str] = None,
) -> str:
    """
    Format a post using templates for variety.
    
    Automatically adds required hashtags and stays under char limit.
    """
    import random
    
    health_emoji = HEALTH_EMOJIS.get(health, "🌱")
    
    # Choose template based on context
    if milestone:
        templates = [t for t in POST_TEMPLATES if "milestone" in t.lower()]
    elif "morning" in commentary.lower() or datetime.now().hour < 10:
        templates = [t for t in POST_TEMPLATES if "morning" in t.lower() or "rise" in t.lower()]
    elif datetime.now().hour > 18:
        templates = [t for t in POST_TEMPLATES if "night" in t.lower() or "evening" in t.lower()]
    else:
        templates = [t for t in POST_TEMPLATES if "milestone" not in t.lower()]
    
    template = random.choice(templates)
    
    # Truncate commentary if needed to stay under limit
    max_commentary_len = 150  # Leave room for template
    if len(commentary) > max_commentary_len:
        commentary = commentary[:max_commentary_len-3] + "..."
    
    post = template.format(
        day=day,
        vpd=vpd,
        health=health,
        health_emoji=health_emoji,
        stage=stage,
        commentary=commentary,
        milestone=milestone or "",
    )
    
    # Ensure under 280 chars
    if len(post) > 280:
        post = post[:277] + "..."
    
    return post
