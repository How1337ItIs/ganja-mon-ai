---
name: pirate-intelligence
description: Competitive intelligence gathering - GitHub scanning, on-chain stalking, social intel, code analysis
metadata:
  openclaw:
    emoji: "🏴‍☠️"
    requires:
      env:
        - HAL_BASE_URL
---

# Pirate Intelligence Skill

## Overview

The Pirate Intelligence skill wraps the existing `src/research/pirate.py` modules to provide competitive intelligence gathering via the HAL API. It discovers what other agents are doing, how they're trading, and what strategies work.

> "Know thy enemy and know thyself; in a hundred battles, you will never be defeated." — Rasta Sun Tzu

## Modules (via HAL API)

### `github_scan`
Scan GitHub for agent repositories, recent commits, and strategy changes.

**Usage:**
```
pirate-intelligence github_scan [--targets top25]
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/research/github-scan` → triggers GitHub scanner
2. Scans 25+ target agent repos for:
   - New commits to trading/strategy files
   - New repos matching agent patterns
   - CI/CD changes (deployment signals)
3. Returns structured intel digest

**Requires:** `GITHUB_TOKEN` env var for 5000 req/hr (vs 60 without)

### `onchain_stalk`
Monitor on-chain wallet activity of known profitable agents.

**Usage:**
```
pirate-intelligence onchain_stalk [--chain monad|base|ethereum]
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/research/onchain-stalk` → triggers on-chain stalker
2. Monitors tracked wallets for:
   - Token purchases/sales
   - LP additions/removals
   - Contract interactions
3. Correlates with price movements

### `social_intel`
Gather intelligence from agent social media activity.

**Usage:**
```
pirate-intelligence social_intel
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/research/social-intel` → triggers social intel gatherer
2. Monitors target agents on:
   - Twitter/X posts and engagement
   - Farcaster casts
   - Moltbook activity
3. Detects sentiment shifts and alpha leaks

### `code_analyze`
Reverse-engineer successful agent strategies from their public code.

**Usage:**
```
pirate-intelligence code_analyze --repo <github_url>
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/research/code-analyze?repo=<url>` → triggers code analyzer
2. Analyzes:
   - Trading strategy patterns
   - Signal source configurations
   - Risk management parameters
3. Extracts actionable patterns for grimoire

### `daily_briefing`
Generate a comprehensive daily intelligence briefing.

**Usage:**
```
pirate-intelligence daily_briefing
```

**Flow:**
1. Aggregates results from all modules
2. Ranks findings by actionability
3. Suggests strategy adjustments
4. Writes top findings to `trading` and `market_regimes` grimoires
5. Posts summary to memory/YYYY-MM-DD.md

## Schedule (via OpenClaw Cron)

The Research & Intelligence cron job (every 12h) should invoke this skill alongside `blogwatcher` and `summarize`:

| Module | Frequency | When |
|--------|-----------|------|
| `github_scan` | Every 2h | During research windows |
| `onchain_stalk` | Every 4h | During research windows |
| `social_intel` | Every 6h | During research windows |
| `code_analyze` | Every 12h | Deep research cycle |
| `daily_briefing` | Daily | Morning (9 AM cycle) |

## Integration

This skill works with:
- `blogwatcher` — News context for intelligence interpretation
- `summarize` — Compress lengthy findings into actionable intel
- `alpha-finder` — Cross-reference pirate findings with alpha signals
- `trading-signals` — Feed discovered signals into trading pipeline
- `ganjamon-trading` — Apply stolen patterns to trading strategy
- Grimoire system — Write high-confidence findings as learning entries

## Data Output

All intelligence written to:
- `data/intel/github/` — GitHub scan results
- `data/intel/onchain/` — On-chain activity logs
- `data/intel/social/` — Social media intelligence
- `data/intel/code/` — Code analysis reports
- `data/intel/briefings/` — Daily synthesized briefings

## Safety Notes

- NEVER expose proprietary trading strategies in social posts
- Intelligence is for internal use only — share wisdom, never alpha
- Respect GitHub API rate limits (use authenticated requests)
- Respect social platform ToS — observe, don't scrape aggressively

---

**Skill Version:** 1.0.0
**Last Updated:** 2026-02-11
**Maintainer:** GanjaMon Autonomous Agent
