"""
Unified Context Aggregator
============================

Reads existing data files from all three GanjaMon subsystems and produces a
formatted context string for injection into the Grok AI prompt.  This gives the
AI brain full situational awareness across grow ops, social engagement, and
trading activity -- without any of those systems needing to know about each
other.

Architecture
------------
The three subsystems are:

1. **Grow Brain** (``src/brain/agent.py``)
   Already provides episodic memory (conditions, watering, VPD).
   This module does NOT duplicate that; it adds the other two.

2. **Engagement Daemon** (``src/social/engagement_daemon.py``)
   Writes ``data/engagement_log.jsonl`` (JSONL, one line per social post) and
   ``data/engagement_state.json`` (last action timestamps per channel).
   The Farcaster client writes ``data/farcaster_state.json`` (replied hashes,
   last post/reply times).

3. **Trading Agent** (``agents/ganjamon/``)
   Writes ``data/paper_portfolio.json`` (cash, open/closed trades, PnL) and
   ``data/unified_brain_state.json`` (research cycles, domain weights, signals
   scanned across 5 domains).

Data flow::

    engagement_daemon.py ──> data/engagement_log.jsonl ──┐
    engagement_daemon.py ──> data/engagement_state.json ──┤
    farcaster.py ──────────> data/farcaster_state.json ──┤
                                                          │   unified_context.py
    ganjamon-agent ────────> data/paper_portfolio.json ──┼──> format_unified_context()
    ganjamon-agent ────────> data/unified_brain_state.json┤       │
                                                          │       ▼
    (external review agent)  data/historical_review.json ─┘   Injected into Grok prompt
                                                              in agent.py build_context_message()

Integration with agent.py
-------------------------
``GrokAndMonAgent.__init__()`` creates an ``UnifiedContextAggregator`` instance.
``run_decision_cycle()`` calls ``await self.unified_ctx.format_unified_context()``
between sensor gathering and the Grok API call, then passes the resulting string
into ``build_context_message()`` which inserts it between episodic memory and the
analysis prompt.

External Review Hook
--------------------
A separate Claude instance is building historical decision review/reflection.
That agent writes to ``data/historical_review.json`` with keys ``insights``,
``patterns``, and ``recommendations`` (each a list of strings).  This module
reads that file and appends its content to the unified context.  If the file
does not exist, a placeholder is shown.

Graceful Degradation
--------------------
Every data source is wrapped in safe-read helpers.  If a file is missing, the
corresponding section shows "unavailable" instead of crashing.  The top-level
``format_unified_context()`` method also has a blanket try/except in the caller
(``agent.py:run_decision_cycle``), so even unexpected errors produce an empty
string rather than halting the grow loop.

Testing
-------
::

    # Standalone (from project root):
    python3 -c "
    from src.brain.unified_context import UnifiedContextAggregator
    import asyncio
    u = UnifiedContextAggregator()
    print(asyncio.run(u.format_unified_context()))
    "

    # Graceful degradation:
    python3 -c "
    from src.brain.unified_context import _safe_read_json
    from pathlib import Path
    assert _safe_read_json(Path('/nonexistent')) is None
    print('OK')
    "
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ---------------------------------------------------------------------------
# Data source file paths (all read-only)
# ---------------------------------------------------------------------------

# Trading agent (separate process, writes its own data files)
TRADING_DATA = PROJECT_ROOT / "cloned-repos" / "ganjamon-agent" / "data"
PAPER_PORTFOLIO = TRADING_DATA / "paper_portfolio.json"
"""JSON: ``{starting_balance, current_cash, trades: [{is_open, pnl_usd, ...}]}``"""

BRAIN_STATE = TRADING_DATA / "unified_brain_state.json"
"""JSON: ``{total_research_cycles, domains: {name: {signals_seen, ...}}}``"""

SOCIAL_POST_LOG = TRADING_DATA / "social_post_log.jsonl"
"""JSONL: ``{ts, kind, channel, length, text, meta}`` per line."""

# Engagement daemon and Farcaster client (same process as grow brain)
ENGAGEMENT_STATE = PROJECT_ROOT / "data" / "engagement_state.json"
"""JSON: ``{last_farcaster_post: ISO, last_twitter_post: ISO, ...}``"""

ENGAGEMENT_LOG = PROJECT_ROOT / "data" / "engagement_log.jsonl"
"""JSONL: ``{ts, channel, action, text, meta}`` per line."""

FARCASTER_STATE = PROJECT_ROOT / "data" / "farcaster_state.json"
"""JSON: ``{replied_hashes: [...], last_post_time, last_reply_time}``"""

# External review hook (written by a separate Claude instance)
HISTORICAL_REVIEW = PROJECT_ROOT / "data" / "historical_review.json"
"""JSON: ``{insights: [...], patterns: [...], recommendations: [...]}``"""

# Email subsystem (src/mailer/)
EMAIL_STATE = PROJECT_ROOT / "data" / "email_state.json"
"""JSON: ``{last_send_time, daily_count, daily_reset, sent_ids}``"""

EMAIL_INBOX = PROJECT_ROOT / "data" / "email_inbox.json"
"""JSON: list of email dicts with ``{id, from, to, subject, text, html, received_at, read}``"""

EMAIL_OUTBOX = PROJECT_ROOT / "data" / "email_outbox.json"
"""JSON: list of queued outgoing emails ``{id, to, subject, body_text, queued_at}``"""

AGENT_TASKS = PROJECT_ROOT / "data" / "agent_tasks.json"
"""JSON: list of pending tasks/todos for the agent ``{id, title, description, status, tool_hint}``"""

COMMUNITY_SUGGESTIONS = PROJECT_ROOT / "data" / "community_suggestions.json"
"""JSON: list of community trade suggestions from Telegram ``{username, suggestion, type, token, chain, status}``"""


# ---------------------------------------------------------------------------
# Safe file-reading helpers
# ---------------------------------------------------------------------------

def _safe_read_json(path: Path) -> Optional[dict]:
    """Read a JSON file, returning ``None`` on any failure.

    Handles missing files, permission errors, and malformed JSON without
    raising.  Logs at DEBUG level on failure.
    """
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception as e:
        logger.debug(f"Could not read {path}: {e}")
    return None


def _safe_read_jsonl_tail(path: Path, max_lines: int = 50) -> list[dict]:
    """Read the last *max_lines* of a JSONL file.

    Returns a list of parsed dicts.  Lines that fail JSON parsing are silently
    skipped.  Returns an empty list if the file is missing or unreadable.
    """
    entries: list[dict] = []
    try:
        if not path.exists():
            return entries
        lines = path.read_text().strip().splitlines()
        for line in lines[-max_lines:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logger.debug(f"Could not read {path}: {e}")
    return entries


def _parse_entry_timestamp(entry: dict) -> Optional[datetime]:
    """Parse a best-effort timestamp from JSON/JSONL entry fields."""
    for key in ("ts", "timestamp", "time", "created_at"):
        raw = entry.get(key)
        if not raw:
            continue
        if isinstance(raw, (int, float)):
            try:
                return datetime.fromtimestamp(float(raw))
            except Exception:
                continue
        if isinstance(raw, str):
            try:
                # Common OpenClaw/ISO forms including trailing Z.
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue
    return None


def _path_mtime_iso(path: Path) -> Optional[str]:
    """Return filesystem mtime as ISO string, or None if missing/unreadable."""
    try:
        if path.exists():
            return datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Main aggregator class
# ---------------------------------------------------------------------------

class UnifiedContextAggregator:
    """Gathers cross-system data and formats it for Grok prompt injection.

    This class is instantiated once in ``GrokAndMonAgent.__init__()`` and
    persists across decision cycles.  It caches expensive data (Farcaster API
    calls) for 10 minutes to avoid redundant network requests.

    Public API:
        ``await format_unified_context()``
            Returns a markdown string ready for injection into the Grok prompt.
            Called from ``GrokAndMonAgent.run_decision_cycle()``.

        ``get_review_hook_data()``
            Returns a raw dict for external review systems to consume.

    All methods are safe to call even when data files are missing.
    """

    def __init__(self):
        # Farcaster metrics cache -- avoids hitting the Warpcast public API
        # on every 30-minute decision cycle.  Cache TTL is 10 minutes.
        self._fc_cache: Optional[dict] = None
        self._fc_cache_ts: float = 0
        self._fc_cache_ttl: float = 600  # seconds

    # ------------------------------------------------------------------
    # Data gatherers (all synchronous file reads)
    # ------------------------------------------------------------------

    def gather_trading_summary(self) -> dict:
        """Read trading agent JSON files and return a summary dict.

        Returns a dict with at minimum ``{"available": bool}``.  When data is
        available, also includes:

        - ``cash`` (float): Current cash balance.
        - ``starting`` (float): Starting balance (default $1000).
        - ``open_positions`` (int): Number of currently open trades.
        - ``closed_trades`` (int): Number of closed trades.
        - ``total_pnl_usd`` (float): Sum of all trade PnL in USD.
        - ``total_pnl_pct`` (float): Total PnL as a percentage of starting balance.
        - ``research_cycles`` (int): Number of unified brain research cycles.
        - ``domain_count`` (int): Number of research domains (e.g. 5).
        - ``total_signals`` (int): Total signals scanned across all domains.
        - ``mode`` (str): Always ``"paper"`` for now.
        """
        summary: dict = {"available": False}

        # --- Paper portfolio (trades, cash, PnL) ---
        portfolio = _safe_read_json(PAPER_PORTFOLIO)
        if portfolio:
            summary["available"] = True
            summary["status"] = "active"
            summary["cash"] = portfolio.get("current_cash", 0)
            summary["starting"] = portfolio.get("starting_balance", 1000)
            trades = portfolio.get("trades", [])
            open_trades = [t for t in trades if t.get("is_open")]
            closed_trades = [t for t in trades if not t.get("is_open")]
            summary["open_positions"] = len(open_trades)
            summary["closed_trades"] = len(closed_trades)
            total_pnl = sum(t.get("pnl_usd", 0) for t in trades)
            summary["total_pnl_usd"] = round(total_pnl, 2)
            if summary["starting"] > 0:
                summary["total_pnl_pct"] = round(
                    total_pnl / summary["starting"] * 100, 2
                )
            else:
                summary["total_pnl_pct"] = 0
            summary["mode"] = "paper"
            summary["last_update"] = _path_mtime_iso(PAPER_PORTFOLIO)

        # --- Unified brain state (research cycles, signals per domain) ---
        brain = _safe_read_json(BRAIN_STATE)
        if brain:
            summary["available"] = True
            summary["status"] = "active"
            summary["research_cycles"] = brain.get("total_research_cycles", 0)
            domains = brain.get("domains", {})
            summary["domain_count"] = len(domains)
            summary["total_signals"] = sum(
                d.get("signals_seen", 0) for d in domains.values()
            )
            summary["mode"] = "paper"  # Currently always paper
            summary["last_update"] = brain.get("updated_at") or _path_mtime_iso(BRAIN_STATE)

        if "status" not in summary:
            summary["status"] = "unavailable"

        return summary

    def gather_social_summary(self) -> dict:
        """Read engagement/farcaster state files and return a summary dict.

        Returns a dict with at minimum ``{"available": bool}``.  When data is
        available, also includes:

        - ``last_actions`` (dict): Mapping of channel name to last action ISO
          timestamp (from ``engagement_state.json``).
        - ``posts_24h`` (dict): Mapping of channel name to post count in the
          last 24 hours (from ``engagement_log.jsonl``).
        - ``replies_24h`` (int): Number of reply-type actions in the last 24h.
        - ``total_posts_24h`` (int): Total posts across all channels in 24h.
        - ``fc_replied_count`` (int): Total Farcaster casts we've replied to
          (from ``farcaster_state.json``).
        - ``fc_last_post`` (str|None): ISO timestamp of last Farcaster post.
        - ``fc_last_reply`` (str|None): ISO timestamp of last Farcaster reply.
        """
        summary: dict = {"available": False, "status": "quiet"}

        # --- Engagement state (last action timestamps per channel) ---
        eng_state = _safe_read_json(ENGAGEMENT_STATE)
        if eng_state:
            summary["available"] = True
            summary["last_actions"] = {}
            for key, val in eng_state.items():
                if key.startswith("last_") and val:
                    channel = key.replace("last_", "")
                    summary["last_actions"][channel] = val

        # --- Engagement log (recent 24h post activity) ---
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        log_entries = _safe_read_jsonl_tail(ENGAGEMENT_LOG, max_lines=200)
        recent = [e for e in log_entries if e.get("ts", "") >= cutoff]
        if recent:
            summary["available"] = True
            summary["status"] = "active"
            channel_counts: dict[str, int] = {}
            reply_count = 0
            for entry in recent:
                ch = entry.get("channel", "unknown")
                channel_counts[ch] = channel_counts.get(ch, 0) + 1
                if "reply" in entry.get("action", ""):
                    reply_count += 1
            summary["posts_24h"] = channel_counts
            summary["replies_24h"] = reply_count
            summary["total_posts_24h"] = len(recent)
            summary["source"] = "engagement_log"
            summary["last_update"] = _path_mtime_iso(ENGAGEMENT_LOG)

        # Fallback: trading agent social log (active in unified runtime)
        if not summary.get("total_posts_24h"):
            cutoff_dt = datetime.now() - timedelta(hours=24)
            trading_entries = _safe_read_jsonl_tail(SOCIAL_POST_LOG, max_lines=400)
            trading_recent = []
            for entry in trading_entries:
                ts = _parse_entry_timestamp(entry)
                if ts and ts >= cutoff_dt:
                    trading_recent.append(entry)
            if trading_recent:
                summary["available"] = True
                summary["status"] = "active"
                channel_counts: dict[str, int] = {}
                reply_count = 0
                for entry in trading_recent:
                    ch = (
                        entry.get("channel")
                        or entry.get("kind")
                        or entry.get("platform")
                        or "unknown"
                    )
                    channel_counts[ch] = channel_counts.get(ch, 0) + 1
                    action = str(entry.get("action", "")).lower()
                    kind = str(entry.get("kind", "")).lower()
                    if "reply" in action or "reply" in kind:
                        reply_count += 1
                summary["posts_24h"] = channel_counts
                summary["replies_24h"] = reply_count
                summary["total_posts_24h"] = len(trading_recent)
                summary["source"] = "trading_social_post_log"
                summary["last_update"] = _path_mtime_iso(SOCIAL_POST_LOG)

        # --- Farcaster state (replied hashes, last post/reply times) ---
        fc_state = _safe_read_json(FARCASTER_STATE)
        if fc_state:
            summary["available"] = True
            summary["fc_replied_count"] = len(fc_state.get("replied_hashes", []))
            summary["fc_last_post"] = fc_state.get("last_post_time")
            summary["fc_last_reply"] = fc_state.get("last_reply_time")

        return summary

    async def gather_farcaster_metrics(self) -> dict:
        """Fetch engagement metrics on our recent casts (cached 10 min).

        Makes an async HTTP call to the Warpcast public API via
        ``FarcasterClient.get_own_casts()``.  Results are cached for
        ``self._fc_cache_ttl`` seconds (default 600 = 10 min) to avoid
        hitting the API on every 30-minute decision cycle.

        Returns a dict with at minimum ``{"available": bool}``.  When data
        is available, also includes:

        - ``recent_count`` (int): Number of casts fetched (up to 10).
        - ``avg_likes`` (float): Average likes per cast.
        - ``avg_recasts`` (float): Average recasts per cast.
        - ``avg_replies`` (float): Average replies per cast.
        - ``total_engagement`` (int): Sum of all likes + recasts + replies.
        """
        now = time.time()
        if self._fc_cache and (now - self._fc_cache_ts) < self._fc_cache_ttl:
            return self._fc_cache

        metrics: dict = {"available": False}
        try:
            from ..social.farcaster import FarcasterClient
            client = FarcasterClient()
            casts = await client.get_own_casts(limit=10)
            await client.close()

            if casts:
                metrics["available"] = True
                metrics["recent_count"] = len(casts)
                metrics["avg_likes"] = round(
                    sum(c.likes for c in casts) / len(casts), 1
                )
                metrics["avg_recasts"] = round(
                    sum(c.recasts for c in casts) / len(casts), 1
                )
                metrics["avg_replies"] = round(
                    sum(c.replies for c in casts) / len(casts), 1
                )
                metrics["total_engagement"] = sum(
                    c.likes + c.recasts + c.replies for c in casts
                )
        except Exception as e:
            logger.debug(f"Farcaster metrics unavailable: {e}")

        self._fc_cache = metrics
        self._fc_cache_ts = now
        return metrics

    def gather_email_summary(self) -> dict:
        """Read email subsystem state and return a summary dict.

        Returns a dict with at minimum ``{"available": bool}``.  When data
        is available, also includes:

        - ``daily_sent`` (int): Emails sent today.
        - ``daily_limit`` (int): Max emails per day (50).
        - ``inbox_unread`` (int): Unread inbound emails.
        - ``inbox_total`` (int): Total inbound emails stored.
        - ``outbox_pending`` (int): Emails queued for sending.
        - ``address`` (str): The agent's email address.
        """
        summary: dict = {"available": False, "address": "agent@grokandmon.com"}

        state = _safe_read_json(EMAIL_STATE)
        if state:
            summary["available"] = True
            summary["daily_sent"] = state.get("daily_count", 0)
            summary["daily_limit"] = 50

        inbox = _safe_read_json(EMAIL_INBOX)
        if isinstance(inbox, list):
            summary["available"] = True
            summary["inbox_total"] = len(inbox)
            summary["inbox_unread"] = sum(
                1 for e in inbox if not e.get("read")
            )

        outbox = _safe_read_json(EMAIL_OUTBOX)
        if isinstance(outbox, list):
            summary["available"] = True
            summary["outbox_pending"] = len(outbox)

        return summary

    def gather_agent_tasks(self) -> list[dict]:
        """Read pending agent tasks from data/agent_tasks.json.

        Returns a list of task dicts with status != 'completed'.
        """
        data = _safe_read_json(AGENT_TASKS)
        if not isinstance(data, list):
            return []
        return [t for t in data if t.get("status") != "completed"]

    def gather_community_suggestions(self) -> list[dict]:
        """Read pending community trade suggestions from Telegram.

        Returns a list of suggestion dicts with status == 'pending'.
        """
        data = _safe_read_json(COMMUNITY_SUGGESTIONS)
        if not isinstance(data, list):
            return []
        return [s for s in data if s.get("status") == "pending"][-10:]

    def load_external_review(self) -> Optional[str]:
        """Load historical review context written by an external review agent.

        Reads ``data/historical_review.json``.  The expected schema is::

            {
                "insights": ["insight 1", "insight 2", ...],
                "patterns": ["pattern 1", "pattern 2", ...],
                "recommendations": ["rec 1", "rec 2", ...]
            }

        Returns a formatted string with up to 3 items from each key, or
        ``None`` if the file does not exist or is empty.

        This is the **hook interface** for the separate Claude instance that
        builds historical decision review/reflection.  That agent writes to
        this file; this module reads it.
        """
        data = _safe_read_json(HISTORICAL_REVIEW)
        if not data:
            return None

        parts: list[str] = []
        if data.get("insights"):
            parts.append("**Insights:** " + "; ".join(data["insights"][:3]))
        if data.get("patterns"):
            parts.append("**Patterns:** " + "; ".join(data["patterns"][:3]))
        if data.get("recommendations"):
            parts.append(
                "**Recommendations:** " + "; ".join(data["recommendations"][:3])
            )
        return "\n".join(parts) if parts else None

    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------

    async def format_unified_context(self) -> str:
        """Produce formatted markdown for Grok prompt injection.

        This is the main entry point.  Called from
        ``GrokAndMonAgent.run_decision_cycle()`` (which is async).

        Returns a markdown string with three sections:

        1. **Trading Agent Status** -- portfolio, PnL, research stats.
        2. **Social Engagement Summary** -- 24h post counts, reply count,
           Farcaster engagement metrics, health indicator.
        3. **Historical Decision Review** -- external review agent output, or
           a placeholder if not yet available.

        Example output::

            ## Cross-System Awareness

            ### Trading Agent Status
            - Portfolio: $473 cash, 10 open positions, -18.86% total PnL
            - Research: 2,117 cycles across 5 domains (502,825 signals)
            - Mode: Paper trading

            ### Social Engagement Summary (last 24h)
              - Farcaster: 5 posts
              - Twitter: 1 posts
              - Replies sent: 3
              - Farcaster engagement: avg 2.1 likes, 0.3 recasts per cast
            - Engagement health: ACTIVE

            ### Historical Decision Review
            - [Awaiting external review agent]
        """
        trading = self.gather_trading_summary()
        social = self.gather_social_summary()

        # Farcaster metrics are async (API call, cached 10 min)
        try:
            fc_metrics = await self.gather_farcaster_metrics()
        except Exception:
            fc_metrics = {"available": False}

        sections: list[str] = ["## Cross-System Awareness"]

        # --- Trading ---
        if trading.get("available"):
            cash = trading.get("cash", 0)
            open_pos = trading.get("open_positions", 0)
            pnl_pct = trading.get("total_pnl_pct", 0)
            cycles = trading.get("research_cycles", 0)
            domains = trading.get("domain_count", 0)
            signals = trading.get("total_signals", 0)
            mode = trading.get("mode", "paper")

            sections.append(
                f"### Trading Agent Status\n"
                f"- Portfolio: ${cash:.0f} cash, {open_pos} open positions, "
                f"{pnl_pct:+.2f}% total PnL\n"
                f"- Research: {cycles:,} cycles across {domains} domains "
                f"({signals:,} signals processed)\n"
                f"- Mode: {mode.title()} trading"
            )
        else:
            sections.append(
                "### Trading Agent Status\n"
                "- Data unavailable (agent may not be running)"
            )

        # --- Social ---
        social_lines: list[str] = []
        posts_24h = social.get("posts_24h", {})
        if posts_24h:
            for ch, cnt in sorted(posts_24h.items()):
                social_lines.append(f"  - {ch.title()}: {cnt} posts")
            social_lines.append(
                f"  - Replies sent: {social.get('replies_24h', 0)}"
            )
        if fc_metrics.get("available"):
            avg_likes = fc_metrics.get("avg_likes", 0)
            avg_recasts = fc_metrics.get("avg_recasts", 0)
            total_eng = fc_metrics.get("total_engagement", 0)
            social_lines.append(
                f"  - Farcaster engagement: avg {avg_likes} likes, "
                f"{avg_recasts} recasts per cast "
                f"({total_eng} total on last 10)"
            )
        fc_last = social.get("fc_last_post")
        if fc_last:
            social_lines.append(f"  - Last Farcaster post: {fc_last}")

        if social_lines:
            health = (
                "ACTIVE" if social.get("total_posts_24h", 0) > 0 else "QUIET"
            )
            sections.append(
                "### Social Engagement Summary (last 24h)\n"
                + "\n".join(social_lines)
                + f"\n- Engagement health: {health}"
            )
        else:
            sections.append(
                "### Social Engagement Summary\n"
                "- No recent engagement data"
            )

        # --- Shared event log (unified Mon narrative) ---
        try:
            from src.core.event_log import read_recent_events
            events = read_recent_events(hours=24, limit=20)
            if events:
                event_lines: list[str] = []
                for ev in events[-15:]:
                    ts = ev.get("ts", "")[:16]
                    src = ev.get("source", "?")
                    cat = ev.get("category", "?")
                    summary = ev.get("summary", "")[:120]
                    event_lines.append(f"  - [{ts}] **{src}/{cat}**: {summary}")
                sections.append(
                    "### Mon's Day (shared event log, last 24h)\n"
                    + "\n".join(event_lines)
                )
        except Exception:
            pass

        # --- Email agent ---
        email = self.gather_email_summary()
        if email.get("available"):
            addr = email.get("address", "agent@grokandmon.com")
            sent = email.get("daily_sent", 0)
            limit = email.get("daily_limit", 50)
            unread = email.get("inbox_unread", 0)
            pending = email.get("outbox_pending", 0)
            # Follow-up tracker stats
            followup_line = ""
            try:
                from src.mailer.followup import get_followup_tracker
                fstats = get_followup_tracker().stats()
                if fstats["tracked"] > 0:
                    followup_line = (
                        f"\n- Follow-ups: {fstats['awaiting_reply']} awaiting reply, "
                        f"{fstats['needs_followup']} need follow-up, "
                        f"{fstats['replied']} replied"
                    )
            except Exception:
                pass

            sections.append(
                f"### Email Agent ({addr})\n"
                f"- Status: {sent}/{limit} emails sent today, "
                f"{unread} unread inbox, {pending} pending outbox\n"
                f"- Capabilities: Send outreach, reply to inbound, "
                f"API signups, partnership requests, verification follow-ups\n"
                f"- Use `queue_email` action to send emails proactively"
                f"{followup_line}"
            )
        else:
            sections.append(
                "### Email Agent\n"
                "- Email subsystem available (agent@grokandmon.com)\n"
                "- Use `queue_email` action to send emails"
            )

        # --- Community trade suggestions ---
        suggestions = self.gather_community_suggestions()
        if suggestions:
            sug_lines: list[str] = []
            for s in suggestions:
                username = s.get("username", "anon")
                stype = s.get("type", "general")
                text = s.get("suggestion", "")[:120]
                token = f" [{s['token']}]" if s.get("token") else ""
                chain = f" on {s['chain']}" if s.get("chain") else ""
                sug_lines.append(f"  - **{username}** ({stype}){token}{chain}: {text}")
            sections.append(
                "### Community Trade Suggestions (from Telegram)\n"
                "Your community members suggested these - evaluate if worth acting on:\n"
                + "\n".join(sug_lines)
            )

        # --- Agent tasks/todos ---
        tasks = self.gather_agent_tasks()
        if tasks:
            critical_count = sum(1 for t in tasks if t.get("priority") == "critical")
            task_lines: list[str] = []
            for t in tasks:
                hint = f" (suggested tool: `{t['tool_hint']}`)" if t.get("tool_hint") else ""
                task_lines.append(
                    f"  - **[{t.get('priority', 'normal').upper()}]** {t['title']}{hint}\n"
                    f"    {t.get('description', '')}"
                )
            urgency = ""
            if critical_count > 0:
                urgency = (
                    f"\n\n**URGENT: {critical_count} CRITICAL tasks pending. "
                    "Hackathon deadline is Feb 15 (6 days). "
                    "Execute at least ONE task per decision cycle. "
                    "If a task needs email, USE queue_email NOW. "
                    "If a task needs a social post, USE create_task with tool_hint='social_post' or 'moltbook_post'. "
                    "If a task needs research, USE create_task with tool_hint='web_research'. "
                    "The engagement daemon will pick up and execute created tasks automatically.**"
                )
            sections.append(
                "### Pending Agent Tasks\n"
                "ACT ON THESE — do not just observe them:\n"
                + "\n".join(task_lines)
                + urgency
            )

        # --- Agent lore (funny stories from our history) ---
        lore = _safe_read_json(DATA_DIR / "agent_lore.json")
        if lore and isinstance(lore, list):
            recent_lore = [e for e in lore if e.get("funny")][:3]
            if recent_lore:
                lore_lines = []
                for e in recent_lore:
                    lore_lines.append(
                        f"  - **{e['title']}** ({e['date']}): {e['story']}"
                    )
                sections.append(
                    "### Agent Lore (things that happened to you - use for personality/comedy)\n"
                    + "\n".join(lore_lines)
                )

        # --- External review hook ---
        review = self.load_external_review()
        if review:
            sections.append(f"### Historical Decision Review\n{review}")
        else:
            sections.append(
                "### Historical Decision Review\n"
                "- [Awaiting external review agent — "
                "write to data/historical_review.json to populate]"
            )

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Hook interface for external review systems
    # ------------------------------------------------------------------

    def get_review_hook_data(self) -> dict:
        """Return raw data dict for external review systems to consume.

        Intended for the separate Claude instance building historical decision
        review.  Returns::

            {
                "trading": <gather_trading_summary() output>,
                "social":  <gather_social_summary() output>,
                "review":  <contents of historical_review.json or None>,
            }
        """
        return {
            "trading": self.gather_trading_summary(),
            "social": self.gather_social_summary(),
            "review": _safe_read_json(HISTORICAL_REVIEW),
        }
