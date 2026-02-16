"""Deep bridge to the GanjaMon trading agent's brain state.

Reads 8+ JSON data files from the agent's data directory with TTL caching,
and assembles topic-aware context for injection into the Telegram bot's
system prompt. Replaces the shallow trading_context.py for rich conversations.
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Agent data directory candidates (Chromebook production first, then WSL dev)
AGENT_DATA_PATHS = [
    Path("/home/natha/projects/sol-cannabis/agents/ganjamon/data"),
    Path("/mnt/c/Users/natha/sol-cannabis/agents/ganjamon/data"),
]

# Aggregator API (runs alongside the agent on Chromebook)
AGGREGATOR_BASE = os.environ.get("GANJAMON_AGGREGATOR_URL", "http://localhost:8001")

# Insight tracker persistence
INSIGHTS_USED_PATH = os.environ.get(
    "INSIGHTS_USED_PATH",
    "/home/natha/projects/sol-cannabis/data/telegram_insights_used.json",
)

# All trading sub-topics that trigger deep context injection
TRADING_TOPICS = frozenset({
    "trading_general", "market_regime", "smart_money",
    "signals", "agent_capabilities", "alpha_research",
})


class InsightTracker:
    """Tracks which insights have been shared to avoid repetition."""

    def __init__(self, path: str = INSIGHTS_USED_PATH):
        self._path = path
        self._used: set[str] = set()
        self._load()

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def _load(self):
        try:
            if os.path.exists(self._path):
                with open(self._path) as f:
                    self._used = set(json.load(f))
        except Exception as e:
            logger.debug(f"InsightTracker load: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            # Keep only the last 500 hashes to prevent unbounded growth
            trimmed = list(self._used)[-500:]
            with open(self._path, "w") as f:
                json.dump(trimmed, f)
        except Exception as e:
            logger.debug(f"InsightTracker save: {e}")

    def is_used(self, text: str) -> bool:
        return self._hash(text) in self._used

    def mark_used(self, text: str):
        self._used.add(self._hash(text))
        self._save()

    def get_fresh(self, candidates: list[str]) -> str | None:
        """Return the first unused candidate and mark it used."""
        for c in candidates:
            if not self.is_used(c):
                self.mark_used(c)
                return c
        return None


class AgentBrain:
    """Deep bridge to GanjaMon trading agent's brain state."""

    CACHE_TTL = 60  # seconds

    def __init__(self):
        self._data_dir = self._find_data_dir()
        self._cache: dict[str, tuple[float, Any]] = {}
        self._insight_tracker = InsightTracker()

    @staticmethod
    def _find_data_dir() -> Path | None:
        for p in AGENT_DATA_PATHS:
            if p.exists():
                return p
        return None

    def _cached_load(self, filename: str) -> dict | list | None:
        """Load a JSON file with TTL cache."""
        now = time.time()
        if filename in self._cache:
            ts, data = self._cache[filename]
            if now - ts < self.CACHE_TTL:
                return data

        if not self._data_dir:
            return None

        filepath = self._data_dir / filename
        if not filepath.exists():
            return None

        try:
            with open(filepath) as f:
                data = json.load(f)
            self._cache[filename] = (now, data)
            return data
        except Exception as e:
            logger.warning(f"Failed to load {filename}: {e}")
            return None

    # ------------------------------------------------------------------
    # Lightweight summary (always injected, ~100 tokens)
    # ------------------------------------------------------------------

    async def get_brain_summary(self) -> str:
        """Compact agent status - always included in system prompt."""
        parts = []

        brain = self._cached_load("unified_brain_state.json")
        if brain:
            cycles = brain.get("total_research_cycles", 0)
            domains = brain.get("domains", {})
            domain_strs = []
            for name, info in domains.items():
                if isinstance(info, dict):
                    pnl = info.get("total_pnl", info.get("pnl", 0))
                    domain_strs.append(f"{name}(${pnl:,.0f})")
            parts.append(
                f"Agent: {cycles} research cycles | Domains: {', '.join(domain_strs) or 'initializing'}"
            )

        regime = self._cached_load("regime_analysis.json")
        if regime:
            r = regime.get("regime", "unknown")
            conf = regime.get("confidence", 0)
            reasoning = regime.get("reasoning", "")
            parts.append(f"Market: {r} ({conf:.0%} conf) - {reasoning}")

        perf = self._cached_load("performance_report.json")
        if perf:
            wr = perf.get("win_rate", 0)
            pnl = perf.get("total_pnl", 0)
            trades = perf.get("closed_trades", 0)
            parts.append(f"Performance: {wr:.0f}% win rate | ${pnl:,.0f} PnL | {trades} closed trades")

        return "\n".join(parts) if parts else "Trading agent data unavailable."

    # ------------------------------------------------------------------
    # Deep context getters (conditionally injected per topic)
    # ------------------------------------------------------------------

    async def get_trading_overview(self) -> str:
        """Portfolio + performance summary."""
        parts = []

        portfolio = self._cached_load("paper_portfolio.json")
        if portfolio:
            balance = portfolio.get("balance", 0)
            total_value = portfolio.get("total_value", balance)
            starting = portfolio.get("starting_balance", 1000)
            pnl = total_value - starting
            pnl_pct = (pnl / starting * 100) if starting else 0
            parts.append("## Portfolio (Paper Trading)")
            parts.append(f"- Balance: ${balance:,.2f}")
            parts.append(f"- Total Value: ${total_value:,.2f}")
            parts.append(f"- P&L: ${pnl:+,.2f} ({pnl_pct:+.1f}%)")

            # Open positions
            positions = portfolio.get("positions", [])
            if positions:
                parts.append(f"\n## Open Positions ({len(positions)})")
                for pos in positions[:5]:
                    symbol = pos.get("symbol", "?")
                    entry = pos.get("entry_price", 0)
                    current = pos.get("current_price", entry)
                    pnl_pct = ((current - entry) / entry * 100) if entry else 0
                    parts.append(f"- {symbol}: {pnl_pct:+.1f}% from ${entry:.6g}")

            # Recent closed trades
            closed = portfolio.get("closed_positions", [])
            if closed:
                recent = closed[-5:]
                wins = sum(1 for t in recent if t.get("pnl", 0) > 0)
                parts.append(f"\n## Recent Trades ({wins}/{len(recent)} wins)")
                for t in recent:
                    symbol = t.get("symbol", "?")
                    pnl_val = t.get("pnl", 0)
                    pnl_pct = t.get("pnl_percent", 0)
                    icon = "W" if pnl_val > 0 else "L"
                    parts.append(f"- [{icon}] {symbol}: {pnl_pct:+.1f}%")

        return "\n".join(parts) if parts else ""

    async def get_market_regime(self) -> str:
        """Market regime details with opportunities and risks."""
        regime = self._cached_load("regime_analysis.json")
        if not regime:
            return ""

        parts = ["## Market Regime"]
        parts.append(f"- Regime: {regime.get('regime', '?')} ({regime.get('confidence', 0):.0%} confidence)")
        parts.append(f"- Focus: {regime.get('primary_focus', '?')}")

        reasoning = regime.get("reasoning", "")
        if reasoning:
            parts.append(f"- Analysis: {reasoning}")

        opps = regime.get("opportunities", [])
        if opps:
            parts.append("- Opportunities: " + "; ".join(opps[:3]))

        risks = regime.get("risks", [])
        if risks:
            parts.append("- Risks: " + "; ".join(risks[:3]))

        alloc = regime.get("capital_allocation", {})
        if alloc:
            alloc_strs = [f"{k}: {v:.0%}" for k, v in alloc.items()]
            parts.append(f"- Capital allocation: {', '.join(alloc_strs)}")

        return "\n".join(parts)

    async def get_smart_money_summary(self, n: int = 5) -> str:
        """Top smart money wallets by 7-day realized profit."""
        data = self._cached_load("smart_money_wallets.json")
        if not data:
            return ""

        wallets = data.get("wallets", [])
        if not wallets:
            return ""

        sorted_wallets = sorted(
            wallets,
            key=lambda w: w.get("realized_profit_7d", 0),
            reverse=True,
        )[:n]

        parts = [f"## Top {n} Smart Money Wallets (7d PnL)"]
        for w in sorted_wallets:
            addr = w.get("address", "?")
            short_addr = addr[:6] + "..." + addr[-4:] if len(addr) > 10 else addr
            pnl = w.get("realized_profit_7d", 0)
            wr = w.get("win_rate", 0)
            trades = w.get("total_trades", 0)
            parts.append(f"- {short_addr}: ${pnl:,.0f} 7d profit | {wr:.0%} WR | {trades} trades")

        parts.append(f"\nTracking {data.get('count', len(wallets))} wallets total")
        return "\n".join(parts)

    async def get_active_signals(self) -> str:
        """Recent signals from aggregator or file."""
        signals = []

        # Try aggregator API first
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{AGGREGATOR_BASE}/signals")
                if resp.status_code == 200:
                    signals = resp.json().get("signals", [])[:10]
        except Exception:
            pass

        # Fallback to file
        if not signals:
            file_signals = self._cached_load("recent_signals.json")
            if isinstance(file_signals, list):
                signals = file_signals[:10]

        if not signals:
            return ""

        parts = [f"## Active Signals ({len(signals)} recent)"]
        for sig in signals[:7]:
            source = sig.get("source", "?")
            token = sig.get("token_address", sig.get("token", "?"))
            short_token = token[:8] + "..." if len(str(token)) > 8 else token
            confidence = sig.get("confidence", 0)
            chain = sig.get("chain", "?")
            parts.append(f"- {source}: {short_token} on {chain} (conf: {confidence:.0%})")

        return "\n".join(parts)

    async def get_hunting_targets(self) -> str:
        """What the agent is actively researching."""
        targets = self._cached_load("hunting_targets.json")
        if not targets:
            return ""

        if not isinstance(targets, list):
            return ""

        parts = [f"## Alpha Hunting ({len(targets)} active targets)"]
        for t in targets[:6]:
            tid = t.get("target_id", "?")
            desc = t.get("description", "")
            why = t.get("why_needed", "")
            parts.append(f"- **{tid}**: {desc}")
            if why:
                parts.append(f"  Why: {why}")

        return "\n".join(parts)

    async def get_shareable_insights(self) -> str:
        """Fresh insights from the agent's shared state."""
        state = self._cached_load("shared_agent_state.json")
        if not state:
            return ""

        insights = state.get("recent_insights", [])
        if not insights:
            return ""

        # Deduplicate by insight text and filter shareable
        seen = set()
        unique = []
        for ins in insights:
            if not ins.get("shareable", False):
                continue
            text = ins.get("insight", "")
            if text not in seen:
                seen.add(text)
                unique.append(ins)

        if not unique:
            return ""

        # Take most recent 5
        recent = unique[-5:]
        parts = ["## Agent Insights"]
        for ins in recent:
            cat = ins.get("category", "?")
            text = ins.get("insight", "?")
            parts.append(f"- [{cat}] {text}")

        return "\n".join(parts)

    async def get_cross_domain_highlights(self, n: int = 5) -> str:
        """Top cross-domain trading insights by confidence."""
        data = self._cached_load("cross_domain_learnings.json")
        if not data:
            return ""

        insights = data.get("high_confidence_insights", [])
        if not insights:
            return ""

        # Filter high-confidence and take most recent
        high_conf = [i for i in insights if i.get("confidence", 0) >= 0.9]
        if not high_conf:
            high_conf = sorted(insights, key=lambda i: i.get("confidence", 0), reverse=True)[:n]
        else:
            high_conf = high_conf[-n:]

        parts = [f"## Cross-Domain Research Insights ({data.get('total_sessions', 0)} sessions)"]
        for ins in high_conf:
            name = ins.get("pattern_name", "?")
            source = ins.get("source_domain", "?")
            target = ins.get("target_domain", "?")
            hyp = ins.get("hypothesis", "")
            # Truncate hypothesis to keep prompt lean
            if len(hyp) > 120:
                hyp = hyp[:117] + "..."
            parts.append(f"- {name} ({source} -> {target}): {hyp}")

        experiments = data.get("active_experiments", [])
        if experiments:
            parts.append(f"\nActive experiments: {len(experiments)}")
            for exp in experiments[:2]:
                # Experiments are strings
                first_line = str(exp).split("\n")[0]
                parts.append(f"- {first_line}")

        return "\n".join(parts)

    async def get_performance_by_source(self) -> str:
        """Best and worst performing signal sources."""
        perf = self._cached_load("performance_report.json")
        if not perf:
            return ""

        by_source = perf.get("by_source", [])
        if not by_source:
            return ""

        # Sort by PnL
        sorted_sources = sorted(by_source, key=lambda s: s.get("pnl", 0), reverse=True)

        parts = ["## Signal Source Performance"]

        # Top 5 best
        best = [s for s in sorted_sources if s.get("pnl", 0) > 0][:5]
        if best:
            parts.append("Best sources:")
            for s in best:
                name = s.get("source", "?")
                pnl = s.get("pnl", 0)
                wr = s.get("win_rate", 0)
                trades = s.get("trades", 0)
                parts.append(f"- {name}: ${pnl:+,.0f} ({wr:.0f}% WR, {trades} trades)")

        # Worst (negative PnL)
        worst = [s for s in sorted_sources if s.get("pnl", 0) < 0]
        if worst:
            parts.append("Underperforming:")
            for s in worst[:3]:
                name = s.get("source", "?")
                pnl = s.get("pnl", 0)
                parts.append(f"- {name}: ${pnl:+,.0f}")

        # Chain breakdown
        by_chain = perf.get("by_chain", {})
        if by_chain:
            parts.append("\nBy chain:")
            for chain, info in by_chain.items():
                pnl = info.get("pnl", 0)
                wins = info.get("wins", 0)
                trades = info.get("trades", 0)
                parts.append(f"- {chain}: ${pnl:+,.0f} ({wins}/{trades} wins)")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Master context assembler
    # ------------------------------------------------------------------

    async def get_deep_context(self, topics: list[str]) -> str:
        """Assemble deep trading context based on detected topics."""
        parts = []

        has_trading = any(t in TRADING_TOPICS for t in topics)

        if "trading_general" in topics or has_trading:
            overview = await self.get_trading_overview()
            if overview:
                parts.append(overview)

        if "market_regime" in topics:
            regime = await self.get_market_regime()
            if regime:
                parts.append(regime)

        if "smart_money" in topics:
            sm = await self.get_smart_money_summary()
            if sm:
                parts.append(sm)

        if "signals" in topics:
            sigs = await self.get_active_signals()
            if sigs:
                parts.append(sigs)

        if "agent_capabilities" in topics:
            cross = await self.get_cross_domain_highlights()
            if cross:
                parts.append(cross)

        if "alpha_research" in topics:
            targets = await self.get_hunting_targets()
            if targets:
                parts.append(targets)

        # Performance by source for any trading topic
        if has_trading:
            perf_src = await self.get_performance_by_source()
            if perf_src:
                parts.append(perf_src)

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Fresh insight for proactive engagement
    # ------------------------------------------------------------------

    async def get_fresh_insight(self) -> str | None:
        """Return an unused insight for proactive sharing."""
        candidates = []

        # From shared agent state
        state = self._cached_load("shared_agent_state.json")
        if state:
            for ins in state.get("recent_insights", []):
                if ins.get("shareable") and ins.get("category") == "market":
                    candidates.append(ins.get("insight", ""))

        # From cross-domain learnings
        cdl = self._cached_load("cross_domain_learnings.json")
        if cdl:
            for ins in cdl.get("high_confidence_insights", [])[-10:]:
                if ins.get("confidence", 0) >= 0.9:
                    name = ins.get("pattern_name", "")
                    hyp = ins.get("hypothesis", "")[:80]
                    candidates.append(f"Research finding: {name} - {hyp}")

        # From regime analysis
        regime = self._cached_load("regime_analysis.json")
        if regime:
            reasoning = regime.get("reasoning", "")
            if reasoning:
                candidates.append(f"Market read: {reasoning}")

        # Filter empty strings
        candidates = [c for c in candidates if c.strip()]

        return self._insight_tracker.get_fresh(candidates)


# Module-level singleton
_brain_instance: AgentBrain | None = None


def get_agent_brain() -> AgentBrain:
    """Get or create the singleton AgentBrain instance."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AgentBrain()
    return _brain_instance
