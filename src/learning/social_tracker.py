"""
Social Performance Tracker
==========================

Tracks engagement per post type and platform.
Learns what content generates most engagement.
Feeds into posting strategy and grimoire.

Metrics tracked:
    - Post type performance (plant_update, trade_call, alpha_insight, meme, reply)
    - Platform performance (farcaster, twitter, telegram)
    - Time-of-day effectiveness
    - Content length effectiveness
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.learning.grimoire import get_grimoire

log = structlog.get_logger("social_tracker")

DB_PATH = Path("data/social_performance.db")


@dataclass
class PostRecord:
    """A social media post with engagement tracking."""
    id: int = 0
    platform: str = ""          # farcaster, twitter, telegram
    post_type: str = ""         # plant_update, trade_call, alpha_insight, meme, reply, engagement
    content_length: int = 0
    posted_at: float = field(default_factory=time.time)
    hour_of_day: int = 0
    day_of_week: int = 0        # 0=Mon, 6=Sun

    # Engagement metrics (updated later)
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    views: int = 0
    engagement_score: float = 0.0  # Weighted composite


@dataclass
class ContentStrategy:
    """Learned content strategy for a platform."""
    platform: str
    best_post_type: str = ""
    best_hour: int = 12
    best_length_range: tuple = (50, 200)
    post_type_scores: Dict[str, float] = field(default_factory=dict)
    sample_size: int = 0


class SocialTracker:
    """
    Tracks social media performance and learns optimal posting strategy.
    """

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None

    def _ensure_db(self) -> sqlite3.Connection:
        if self._db is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(str(DB_PATH))
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    post_type TEXT,
                    content_length INTEGER,
                    posted_at REAL,
                    hour_of_day INTEGER,
                    day_of_week INTEGER,
                    likes INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    reposts INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    engagement_score REAL DEFAULT 0.0
                )
            """)
            self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_platform
                ON posts(platform, posted_at)
            """)
            self._db.commit()
        return self._db

    def record_post(
        self,
        platform: str,
        post_type: str,
        content_length: int,
    ) -> int:
        """Record a new post."""
        db = self._ensure_db()
        import datetime
        now = datetime.datetime.now()

        cursor = db.execute(
            "INSERT INTO posts (platform, post_type, content_length, posted_at, hour_of_day, day_of_week) VALUES (?, ?, ?, ?, ?, ?)",
            (platform, post_type, content_length, time.time(), now.hour, now.weekday()),
        )
        db.commit()

        # Track goal action
        from src.learning.strategy_tracker import get_strategy_tracker
        tracker = get_strategy_tracker()
        tracker.record_goal_action("G-3", f"post:{post_type}", f"social_{platform}", f"{platform}:{post_type}")

        return cursor.lastrowid

    def update_engagement(
        self,
        post_id: int,
        likes: int = 0,
        replies: int = 0,
        reposts: int = 0,
        views: int = 0,
    ) -> None:
        """Update engagement metrics for a post."""
        db = self._ensure_db()

        # Weighted engagement score
        # Replies are most valuable (conversations), then reposts, then likes
        score = replies * 3.0 + reposts * 2.0 + likes * 1.0 + views * 0.01

        db.execute(
            "UPDATE posts SET likes=?, replies=?, reposts=?, views=?, engagement_score=? WHERE id=?",
            (likes, replies, reposts, views, score, post_id),
        )
        db.commit()

    def get_platform_strategy(self, platform: str) -> ContentStrategy:
        """Learn optimal posting strategy for a platform."""
        db = self._ensure_db()

        # Get post type performance
        rows = db.execute(
            """SELECT post_type, AVG(engagement_score), COUNT(*)
               FROM posts WHERE platform=? AND engagement_score > 0
               GROUP BY post_type ORDER BY AVG(engagement_score) DESC""",
            (platform,),
        ).fetchall()

        type_scores = {}
        best_type = ""
        best_score = 0
        total_samples = 0
        for row in rows:
            type_scores[row[0]] = round(row[1], 2)
            total_samples += row[2]
            if row[1] > best_score:
                best_score = row[1]
                best_type = row[0]

        # Get best hour
        hour_row = db.execute(
            """SELECT hour_of_day, AVG(engagement_score)
               FROM posts WHERE platform=? AND engagement_score > 0
               GROUP BY hour_of_day ORDER BY AVG(engagement_score) DESC LIMIT 1""",
            (platform,),
        ).fetchone()
        best_hour = hour_row[0] if hour_row else 12

        # Get best content length range
        length_row = db.execute(
            """SELECT
                 CASE
                   WHEN content_length < 50 THEN 'short'
                   WHEN content_length < 150 THEN 'medium'
                   WHEN content_length < 280 THEN 'long'
                   ELSE 'very_long'
                 END as len_bucket,
                 AVG(engagement_score)
               FROM posts WHERE platform=? AND engagement_score > 0
               GROUP BY len_bucket ORDER BY AVG(engagement_score) DESC LIMIT 1""",
            (platform,),
        ).fetchone()

        length_map = {
            "short": (10, 50),
            "medium": (50, 150),
            "long": (150, 280),
            "very_long": (280, 500),
        }
        best_length = length_map.get(length_row[0], (50, 200)) if length_row else (50, 200)

        strategy = ContentStrategy(
            platform=platform,
            best_post_type=best_type,
            best_hour=best_hour,
            best_length_range=best_length,
            post_type_scores=type_scores,
            sample_size=total_samples,
        )

        # Store in grimoire
        if total_samples >= 10:
            grimoire = get_grimoire("social")
            grimoire.add(
                key=f"strategy:{platform}",
                content=(
                    f"Best {platform} strategy: {best_type} posts "
                    f"at {best_hour}:00, "
                    f"length {best_length[0]}-{best_length[1]} chars. "
                    f"Type scores: {type_scores}"
                ),
                confidence=min(0.3 + total_samples * 0.02, 0.9),
                source="social_tracker",
                tags=["strategy", platform],
            )
            grimoire.save()

        return strategy

    def export_json(self, path: Optional[str] = None) -> str:
        """Export recent posts and platform strategies to a JSON file.

        Args:
            path: Output file path (default ``data/social_tracker.json``).

        Returns:
            Absolute path of the written file.
        """
        import datetime as _dt

        out_path = Path(path) if path else Path("data/social_tracker.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        db = self._ensure_db()

        # Last 50 posts
        rows = db.execute(
            "SELECT id, platform, post_type, content_length, posted_at, "
            "hour_of_day, day_of_week, likes, replies, reposts, views, engagement_score "
            "FROM posts ORDER BY posted_at DESC LIMIT 50"
        ).fetchall()

        posts = []
        for r in rows:
            posts.append({
                "id": r[0],
                "platform": r[1],
                "post_type": r[2],
                "content_length": r[3],
                "posted_at": r[4],
                "hour_of_day": r[5],
                "day_of_week": r[6],
                "likes": r[7],
                "replies": r[8],
                "reposts": r[9],
                "views": r[10],
                "engagement_score": r[11],
            })

        # Strategies per platform
        strategies = {}
        for platform in ("twitter", "farcaster", "telegram"):
            try:
                strat = self.get_platform_strategy(platform)
                strategies[platform] = {
                    "best_post_type": strat.best_post_type,
                    "best_hour": strat.best_hour,
                    "best_length_range": list(strat.best_length_range),
                    "post_type_scores": strat.post_type_scores,
                    "sample_size": strat.sample_size,
                }
            except Exception:
                strategies[platform] = {}

        payload = {
            "exported_at": _dt.datetime.now().isoformat(),
            "total_posts": len(posts),
            "strategies": strategies,
            "recent_posts": posts,
        }

        out_path.write_text(json.dumps(payload, indent=2))
        log.info("social_tracker.export_json", path=str(out_path), posts=len(posts))
        return str(out_path.resolve())

    def get_status(self) -> Dict[str, Any]:
        db = self._ensure_db()
        total = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        with_engagement = db.execute("SELECT COUNT(*) FROM posts WHERE engagement_score > 0").fetchone()[0]

        platforms = {}
        for row in db.execute(
            "SELECT platform, COUNT(*), AVG(engagement_score) FROM posts GROUP BY platform"
        ):
            platforms[row[0]] = {"posts": row[1], "avg_engagement": round(row[2] or 0, 2)}

        return {
            "total_posts": total,
            "with_engagement": with_engagement,
            "platforms": platforms,
        }


# Singleton
_instance: Optional[SocialTracker] = None


def get_social_tracker() -> SocialTracker:
    global _instance
    if _instance is None:
        _instance = SocialTracker()
    return _instance
