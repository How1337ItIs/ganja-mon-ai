# Session: 2026-02-06 - Deep Brain Integration & Maintenance

## 1. Claude Code Updated on Chromebook

- **Before**: v2.1.11
- **After**: v2.1.34 (matches Windows laptop)
- Both system-wide (`/usr/lib/node_modules/`) and user (`~/.npm-global/`) installations updated

## 2. System Health Audit

All services confirmed running on Chromebook:

| Service | Status | Notes |
|---------|--------|-------|
| grokmon | Active | Cultivation agent, 3 processes |
| ganja-mon-bot | Active | Telegram bot (12h uptime) |
| ganjamon-agent | Active | Trading agent, polling Solana RPC |
| grokmon-watchdog | Active | Service watchdog |
| retake-stream | Active | 24/7 streaming |
| kiosk | Active | Dashboard display |

Ralph self-improvement loop: Running via cron every 4 hours. 211 upgrades deployed, 0 pending. Last run at 12:00 PST deployed 5 proactive analyzers (log, performance, code quality, timeout, signal evaluation).

## 3. Telegram Bot v7: Deep Brain Integration

### Problem

The Telegram bot (`@MonGardenBot`) could only surface basic portfolio data from the GanjaMon trading agent. Users asking about market research, smart money wallets, signals, trading strategies, or the agent's self-improvement progress got generic responses. The agent has 10+ rich data sources (750 cross-domain insights, 29 tracked wallets, 12 hunting targets, market regime analysis) that were invisible to the bot.

### Solution

Topic-aware conditional context injection. Non-trading conversations get a lightweight 3-line brain summary. Trading conversations get deep context assembled from the relevant data sources based on detected sub-topics.

### Files Changed

#### Created: `src/telegram/agent_brain.py`

New deep brain bridge module. Core components:

- **`AgentBrain` class** - Singleton with 60-second TTL-cached JSON loaders for 8+ agent data files
- **`InsightTracker`** - Tracks shared insight hashes in `data/telegram_insights_used.json` to prevent repeating the same insight in proactive engagement
- **`get_agent_brain()`** - Module-level singleton accessor

Data sources mapped to methods:

| Method | Data File | What It Returns |
|--------|-----------|----------------|
| `get_brain_summary()` | `unified_brain_state.json` + `regime_analysis.json` + `performance_report.json` | Always-injected 3-line summary: research cycles, domain PnL, market regime, win rate |
| `get_trading_overview()` | `paper_portfolio.json` | Portfolio balance, open positions, recent trades |
| `get_market_regime()` | `regime_analysis.json` | Regime (chop/bull/bear/crab), confidence, opportunities, risks, capital allocation |
| `get_smart_money_summary()` | `smart_money_wallets.json` | Top 5 wallets by 7d realized profit (of 29 tracked) |
| `get_active_signals()` | `recent_signals.json` + HTTP to localhost:8001 | Recent alpha signals with source, token, chain, confidence |
| `get_hunting_targets()` | `hunting_targets.json` | 12 active research targets (smart money trackers, whale watchers, etc.) |
| `get_shareable_insights()` | `shared_agent_state.json` | Deduplicated shareable insights (market regime, alpha predictions) |
| `get_cross_domain_highlights()` | `cross_domain_learnings.json` | Top 5 high-confidence insights from 750 total across 17 learning sessions |
| `get_performance_by_source()` | `performance_report.json` | Best/worst signal sources by PnL + chain breakdown |
| `get_deep_context(topics)` | Multiple | Master assembler: given detected topics, calls relevant getters |
| `get_fresh_insight()` | Multiple | Returns first unused insight for proactive engagement, marks it used |

#### Modified: `src/telegram/variation.py`

Added 6 trading sub-topic keyword categories to `TOPIC_KEYWORDS`:

```python
"trading_general": ["trading", "trade", "portfolio", "position", "p&l", "pnl", "bag", "plays", "alpha", "profit", "loss", "degen"]
"market_regime":   ["market", "bull", "bear", "crab", "regime", "sentiment", "trend", "chop", "macro", "btc dominance"]
"smart_money":     ["whale", "smart money", "wallet", "copy trade", "insider", "following"]
"signals":         ["signal", "alert", "call", "setup", "entry", "snipe", "detected"]
"agent_capabilities": ["capability", "can you", "what do you do", "brain", "skills", "how do you trade"]
"alpha_research":  ["research", "hunting", "edge", "alpha source", "investigating", "studying"]
```

These trigger dynamic deep context injection from `agent_brain.py` (no static `KNOWLEDGE_CHUNKS` needed).

#### Modified: `src/telegram/personality.py`

- **Import**: Replaced `from .trading_context import build_trading_context` with `from .agent_brain import get_agent_brain, TRADING_TOPICS`
- **`generate_response()`**: Trading context now conditional on detected topics:
  - Non-trading messages: inject `brain.get_brain_summary()` only (~100 tokens)
  - Trading messages: inject `brain_summary + brain.get_deep_context(topics)` (~500-800 tokens)
- **`generate_proactive_comment()`**: Now uses `brain.get_brain_summary()` instead of full `build_trading_context()`, plus injects `brain.get_fresh_insight()` for unique agent findings
- Kept `get_rasta_market_take()` import from `trading_context.py` (still used in proactive)

#### Modified: `src/telegram/bot.py`

- **Version**: v6 -> v7
- **Import**: Added `from .agent_brain import get_agent_brain`
- **`HIGH_PRIORITY_KEYWORDS`**: Added `"trading", "alpha", "whale", "smart money", "signals", "market"` (25% engagement chance)
- **`/start` help text**: Added 4 new commands to the help menu
- **4 new command handlers**:

| Command | What It Shows |
|---------|--------------|
| `/trading` | Portfolio overview + market regime + signal source performance |
| `/alpha` | Active signals + hunting targets (what the agent is researching) |
| `/brain` | Brain summary + cross-domain research highlights + shareable insights |
| `/signals` | Raw signal feed |

All command outputs truncated to Telegram's 4096 char limit.

### Architecture

```
User Message
    │
    ├── detect_topics() → ["trading_general", "smart_money", ...]
    │
    ├── NON-TRADING: brain.get_brain_summary() → 3 lines (~100 tokens)
    │   "Agent: 2117 cycles | Domains: on_chain($-6), perps($0)..."
    │   "Market: chop (50% conf) - Hunt individual setups."
    │   "Performance: 74% win rate | $2,260 PnL | 42 trades"
    │
    └── TRADING: brain.get_deep_context(topics) → rich data (~500-800 tokens)
        ├── get_trading_overview()      [if trading_general]
        ├── get_market_regime()         [if market_regime]
        ├── get_smart_money_summary()   [if smart_money]
        ├── get_active_signals()        [if signals]
        ├── get_cross_domain_highlights() [if agent_capabilities]
        ├── get_hunting_targets()       [if alpha_research]
        └── get_performance_by_source() [if any trading topic]
```

### Verification

- Bot restarted with zero errors
- `agent_brain.py` tested directly on Chromebook - all getters return correct data
- Bot polling Telegram successfully, v7 confirmed in logs
- Memory usage: 25MB (within 300MB limit)
