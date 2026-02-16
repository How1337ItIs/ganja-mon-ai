"""
Strategy Tracker with Goal Traceability
========================================

Tracks strategy performance separately from signal performance.
Auto-disables strategies below 40% win rate (min 10 trades).
Implements goal traceability to prevent drift.

Goals:
    G-1: Generate Alpha (trading profits)
    G-2: Grow Plant (healthy cultivation)
    G-3: Build Community (social engagement)

Pattern from: Legba/Loa framework goal traceability + openclaw-trading-assistant
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

log = structlog.get_logger("strategy_tracker")

DB_PATH = Path("data/strategy_tracker.db")


class Goal(str, Enum):
    ALPHA = "G-1"       # Generate Alpha
    GROW = "G-2"        # Grow Plant
    COMMUNITY = "G-3"   # Build Community


@dataclass
class StrategyPerformance:
    """Performance record for a trading strategy."""
    name: str
    goal: str = "G-1"
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    is_active: bool = True
    disabled_reason: str = ""
    last_trade_at: float = 0.0
    created_at: float = field(default_factory=time.time)

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_trades if self.total_trades > 0 else 0.0

    @property
    def avg_pnl(self) -> float:
        return self.total_pnl / self.total_trades if self.total_trades > 0 else 0.0

    @property
    def profit_factor(self) -> float:
        return self.wins / max(self.losses, 1)


@dataclass
class GoalProgress:
    """Progress tracking for a top-level goal."""
    goal: str
    description: str
    actions_24h: int = 0
    actions_7d: int = 0
    progress_score: float = 0.0   # 0.0-1.0
    last_action_at: float = 0.0
    stalled: bool = False         # True if no progress in 24h


# Strategy auto-disable thresholds
MIN_TRADES_FOR_DISABLE = 10
MIN_WIN_RATE = 0.40
MAX_CONSECUTIVE_LOSSES = 5
DECAY_RATE = 0.995  # Daily decay toward baseline


class StrategyTracker:
    """
    Tracks strategy performance and goal progress.

    Features:
    1. Per-strategy win/loss/PnL tracking
    2. Auto-disable underperforming strategies
    3. Goal traceability (every action maps to G-1/G-2/G-3)
    4. Stall detection (goal inactive >24h → alert)
    5. Strategy decay (inactive strategies lose confidence)
    """

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None
        self._strategies: Dict[str, StrategyPerformance] = {}
        self._goal_actions: Dict[str, List[float]] = {
            "G-1": [],
            "G-2": [],
            "G-3": [],
        }

    def _ensure_db(self) -> sqlite3.Connection:
        if self._db is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(str(DB_PATH))
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    name TEXT PRIMARY KEY,
                    goal TEXT DEFAULT 'G-1',
                    total_trades INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    max_drawdown REAL DEFAULT 0.0,
                    consecutive_losses INTEGER DEFAULT 0,
                    max_consecutive_losses INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    disabled_reason TEXT DEFAULT '',
                    last_trade_at REAL DEFAULT 0.0,
                    created_at REAL
                )
            """)
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS goal_actions (
                    goal TEXT,
                    action TEXT,
                    strategy TEXT,
                    details TEXT,
                    timestamp REAL
                )
            """)
            self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_goal_actions_goal_ts
                ON goal_actions(goal, timestamp)
            """)
            self._db.commit()

            # Load strategies
            for row in self._db.execute("SELECT * FROM strategies"):
                sp = StrategyPerformance(
                    name=row[0], goal=row[1], total_trades=row[2],
                    wins=row[3], losses=row[4], total_pnl=row[5],
                    max_drawdown=row[6], consecutive_losses=row[7],
                    max_consecutive_losses=row[8], is_active=bool(row[9]),
                    disabled_reason=row[10], last_trade_at=row[11],
                    created_at=row[12] or time.time(),
                )
                self._strategies[sp.name] = sp

        return self._db

    def register_strategy(self, name: str, goal: str = "G-1") -> StrategyPerformance:
        """Register a new strategy for tracking."""
        db = self._ensure_db()
        if name not in self._strategies:
            sp = StrategyPerformance(name=name, goal=goal)
            self._strategies[name] = sp
            db.execute(
                "INSERT OR IGNORE INTO strategies (name, goal, created_at) VALUES (?, ?, ?)",
                (name, goal, time.time()),
            )
            db.commit()
        return self._strategies[name]

    def record_trade(
        self,
        strategy: str,
        pnl_percent: float,
        details: str = "",
    ) -> StrategyPerformance:
        """Record a trade outcome for a strategy."""
        db = self._ensure_db()
        sp = self._strategies.get(strategy)
        if sp is None:
            sp = self.register_strategy(strategy)

        sp.total_trades += 1
        sp.total_pnl += pnl_percent
        sp.last_trade_at = time.time()

        if pnl_percent > 0:
            sp.wins += 1
            sp.consecutive_losses = 0
        else:
            sp.losses += 1
            sp.consecutive_losses += 1
            sp.max_consecutive_losses = max(sp.max_consecutive_losses, sp.consecutive_losses)

        # Track drawdown
        if pnl_percent < sp.max_drawdown:
            sp.max_drawdown = pnl_percent

        # Auto-disable check
        self._check_auto_disable(sp)

        # Persist
        db.execute(
            """UPDATE strategies SET total_trades=?, wins=?, losses=?, total_pnl=?,
               max_drawdown=?, consecutive_losses=?, max_consecutive_losses=?,
               is_active=?, disabled_reason=?, last_trade_at=?
               WHERE name=?""",
            (sp.total_trades, sp.wins, sp.losses, sp.total_pnl,
             sp.max_drawdown, sp.consecutive_losses, sp.max_consecutive_losses,
             int(sp.is_active), sp.disabled_reason, sp.last_trade_at, sp.name),
        )

        # Log goal action
        db.execute(
            "INSERT INTO goal_actions VALUES (?, ?, ?, ?, ?)",
            (sp.goal, "trade", strategy, details, time.time()),
        )
        db.commit()

        # Track goal actions in memory
        self._goal_actions.setdefault(sp.goal, []).append(time.time())

        return sp

    def _check_auto_disable(self, sp: StrategyPerformance) -> None:
        """Auto-disable underperforming strategies."""
        if not sp.is_active:
            return

        # Need minimum trades before judging
        if sp.total_trades < MIN_TRADES_FOR_DISABLE:
            return

        # Win rate check
        if sp.win_rate < MIN_WIN_RATE:
            sp.is_active = False
            sp.disabled_reason = f"Win rate {sp.win_rate:.0%} < {MIN_WIN_RATE:.0%} over {sp.total_trades} trades"
            log.warning("strategy_disabled", strategy=sp.name, reason=sp.disabled_reason)
            return

        # Consecutive losses check
        if sp.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            sp.is_active = False
            sp.disabled_reason = f"{sp.consecutive_losses} consecutive losses"
            log.warning("strategy_disabled", strategy=sp.name, reason=sp.disabled_reason)

    def record_goal_action(self, goal: str, action: str, strategy: str = "", details: str = "") -> None:
        """Record any action that contributes to a goal."""
        db = self._ensure_db()
        db.execute(
            "INSERT INTO goal_actions VALUES (?, ?, ?, ?, ?)",
            (goal, action, strategy, details, time.time()),
        )
        db.commit()
        self._goal_actions.setdefault(goal, []).append(time.time())

    def get_goal_progress(self) -> Dict[str, GoalProgress]:
        """Get progress for all goals."""
        db = self._ensure_db()
        now = time.time()
        day_ago = now - 86400
        week_ago = now - 7 * 86400

        progress = {}
        for goal, desc in [
            ("G-1", "Generate Alpha (trading profits)"),
            ("G-2", "Grow Plant (healthy cultivation)"),
            ("G-3", "Build Community (social engagement)"),
        ]:
            cursor = db.execute(
                "SELECT COUNT(*) FROM goal_actions WHERE goal=? AND timestamp>?",
                (goal, day_ago),
            )
            actions_24h = cursor.fetchone()[0]

            cursor = db.execute(
                "SELECT COUNT(*) FROM goal_actions WHERE goal=? AND timestamp>?",
                (goal, week_ago),
            )
            actions_7d = cursor.fetchone()[0]

            cursor = db.execute(
                "SELECT MAX(timestamp) FROM goal_actions WHERE goal=?",
                (goal,),
            )
            last = cursor.fetchone()[0] or 0

            # Progress score: ratio of actions vs expected
            expected_24h = {"G-1": 20, "G-2": 4, "G-3": 10}
            progress_score = min(actions_24h / expected_24h.get(goal, 10), 1.0)

            stalled = (now - last) > 86400 if last > 0 else True

            progress[goal] = GoalProgress(
                goal=goal,
                description=desc,
                actions_24h=actions_24h,
                actions_7d=actions_7d,
                progress_score=round(progress_score, 2),
                last_action_at=last,
                stalled=stalled,
            )

        return progress

    def get_stalled_goals(self) -> List[GoalProgress]:
        """Get goals that have stalled (no activity in 24h)."""
        return [g for g in self.get_goal_progress().values() if g.stalled]

    def get_strategy(self, name: str) -> Optional[StrategyPerformance]:
        self._ensure_db()
        return self._strategies.get(name)

    def get_active_strategies(self) -> Dict[str, StrategyPerformance]:
        self._ensure_db()
        return {n: s for n, s in self._strategies.items() if s.is_active}

    def get_disabled_strategies(self) -> Dict[str, StrategyPerformance]:
        self._ensure_db()
        return {n: s for n, s in self._strategies.items() if not s.is_active}

    def re_enable_strategy(self, name: str) -> bool:
        """Re-enable a disabled strategy (manual override)."""
        db = self._ensure_db()
        sp = self._strategies.get(name)
        if sp:
            sp.is_active = True
            sp.disabled_reason = ""
            sp.consecutive_losses = 0
            db.execute(
                "UPDATE strategies SET is_active=1, disabled_reason='', consecutive_losses=0 WHERE name=?",
                (name,),
            )
            db.commit()
            log.info("strategy_re_enabled", strategy=name)
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        self._ensure_db()
        goals = self.get_goal_progress()
        return {
            "total_strategies": len(self._strategies),
            "active": len([s for s in self._strategies.values() if s.is_active]),
            "disabled": len([s for s in self._strategies.values() if not s.is_active]),
            "goals": {
                g: {
                    "progress": gp.progress_score,
                    "actions_24h": gp.actions_24h,
                    "stalled": gp.stalled,
                }
                for g, gp in goals.items()
            },
            "top_strategies": sorted(
                [
                    {"name": s.name, "win_rate": round(s.win_rate, 2), "pnl": round(s.total_pnl, 1), "trades": s.total_trades}
                    for s in self._strategies.values()
                    if s.total_trades > 0
                ],
                key=lambda x: x["pnl"],
                reverse=True,
            )[:5],
        }


# Singleton
_instance: Optional[StrategyTracker] = None


def get_strategy_tracker() -> StrategyTracker:
    global _instance
    if _instance is None:
        _instance = StrategyTracker()
    return _instance
