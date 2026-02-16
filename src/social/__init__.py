"""
Social Media Module
===================
X/Twitter integration for posting grow updates and engaging community.

Usage:
    from src.social import TwitterClient, format_daily_update

    client = TwitterClient()  # Uses env vars for credentials

    tweet = format_daily_update(
        day=49,
        stage="flowering",
        vpd=1.15,
        temp_f=77.0,
        humidity=45,
        water_ml=200,
    )

    result = await client.tweet(tweet)
"""

from .twitter import (
    TwitterClient,
    TweetResult,
    create_twitter_client,
    format_daily_update,
    format_ai_decision,
    format_milestone,
)

from .xai_native import (
    XAINativeSocial,
    GeneratedPost,
    XSearchResult,
)

from .manager import (
    MonSocialManager,
    SocialUpdate,
    post_from_decision,
)

from .scheduler import (
    SocialScheduler,
    create_launch_day_scheduler,
)

from .farcaster import (
    FarcasterClient,
    CastResult,
)

from .engagement_daemon import (
    EngagementDaemon,
    get_engagement_daemon,
)

__all__ = [
    # Twitter
    "TwitterClient",
    "TweetResult",
    "create_twitter_client",
    "format_daily_update",
    "format_ai_decision",
    "format_milestone",
    # xAI Native
    "XAINativeSocial",
    "GeneratedPost",
    "XSearchResult",
    # Manager
    "MonSocialManager",
    "SocialUpdate",
    "post_from_decision",
    # Scheduler
    "SocialScheduler",
    "create_launch_day_scheduler",
    # Farcaster
    "FarcasterClient",
    "CastResult",
    # Engagement Daemon
    "EngagementDaemon",
    "get_engagement_daemon",
]
