---
name: grimoire-writer
description: Write learnings to domain grimoires from grow outcomes, trade results, social performance, and market regime changes
metadata:
  openclaw:
    emoji: "📖"
    requires:
      env:
        - HAL_BASE_URL
---

# Grimoire Writer Skill

## Overview

The grimoire system (`src/learning/grimoire.py`) is GanjaMon's long-term learning memory — structured, persistent knowledge files organized by domain. **The grimoire system is built and excellent, but it's starving.** Only the `trading/knowledge.json` domain has any data.

This skill ensures grimoire entries are written after every decision cycle, trade outcome, social post performance review, and market regime change.

## Why This Matters

Without grimoire writing:
- The agent makes the same mistakes repeatedly
- Seasonal patterns aren't captured
- Successful strategies aren't reinforced
- Cross-domain intelligence has no historical context

With grimoire writing:
- Each grow decision outcome trains better future decisions
- Trading patterns accumulate and inform risk management
- Social content performance optimizes posting strategy
- Market regime changes are detected and logged

## Grimoire Domains

| Domain | Directory | What Gets Written |
|--------|-----------|-------------------|
| `cultivation` | `data/grimoires/cultivation/` | Grow outcomes: "Watered at 32% soil → moisture rose to 55% within 30min" |
| `trading` | `data/grimoires/trading/` | Trade results: "Entry at $0.003, exit at $0.008 = +166% on whale signal" |
| `social` | `data/grimoires/social/` | Content performance: "Sensor data posts get 3x more engagement than memes" |
| `market_regimes` | `data/grimoires/market_regimes/` | Regime changes: "BTC funding rate flipped negative, alts dumping 48h later" |

## Commands

### `write_grow_outcome`
Record a grow decision outcome for the cultivation grimoire.

**Usage:**
```
grimoire-writer write_grow_outcome
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/sensors` → current readings
2. `GET ${HAL_BASE_URL}/api/grow/history?hours=4` → recent decisions
3. For each recent decision:
   - What was decided? (water, CO2, adjust humidifier, etc.)
   - What happened to the readings AFTER the action?
   - Was the outcome good? (did readings move toward target?)
4. Write entry to `cultivation` grimoire with confidence score
5. Format: `{"entry": "...", "confidence": 0.8, "source": "outcome_tracking", "tags": ["watering", "veg"]}`

**Calls:**
```bash
curl -s -X POST ${HAL_BASE_URL}/api/learning/grimoire/add \
  -H "Content-Type: application/json" \
  -d '{"domain": "cultivation", "entry": "...", "confidence": 0.8, "tags": ["watering"]}'
```

### `write_trade_result`
Record a trade result for the trading grimoire.

**Usage:**
```
grimoire-writer write_trade_result
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/trading/history` → recent trades
2. For closed positions:
   - Entry/exit prices, P&L, signal source, hold duration
   - Market conditions at entry (regime, volatility)
3. Write entry with confidence based on result quality
4. High-profit trades = high confidence = stronger learning signal

### `write_social_performance`
Record social content performance for the social grimoire.

**Usage:**
```
grimoire-writer write_social_performance
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/social/metrics` → engagement data
2. Analyze which content types perform best:
   - Sensor data posts vs memes vs alpha calls
   - Best posting times by platform
   - Which Rasta voice variations get more engagement
3. Write top-performing patterns to `social` grimoire

### `detect_market_regime`
Detect and record market regime changes.

**Usage:**
```
grimoire-writer detect_market_regime
```

**Flow:**
1. `GET ${HAL_BASE_URL}/api/trading/portfolio` → current positions
2. Check key indicators: BTC dominance, funding rates, volatility indices
3. Compare against last known regime (from grimoire)
4. If regime changed, write entry to `market_regimes` grimoire
5. Include: old regime, new regime, detected signals, confidence

### `review_and_prune`
Review grimoire entries and prune low-confidence ones that contradict newer data.

**Usage:**
```
grimoire-writer review_and_prune
```

**Flow:**
1. Read all grimoire domains
2. Find contradictory entries (e.g., "water at 30%" vs "don't water at 30%")
3. Keep higher-confidence/newer entries, archive or prune others
4. Report pruning actions to memory

## Schedule Integration

This skill should be invoked by OpenClaw cron jobs:

| When | What |
|------|------|
| After every Grow Decision Cycle (2h) | `write_grow_outcome` |
| After Auto-Review (6h) | `write_trade_result` + `write_social_performance` |
| During Research (12h) | `detect_market_regime` |
| Weekly Deep Analysis | `review_and_prune` |

## HAL API Endpoints Needed

The following API endpoints need to exist in `src/api/app.py`:

```
POST /api/learning/grimoire/add      → Add entry to a grimoire domain
GET  /api/learning/grimoire/list     → List entries for a domain
GET  /api/learning/grimoire/context  → Get all grimoire context (for AI prompts)
```

If these endpoints don't exist yet, the skill should write directly to the JSON files in `data/grimoires/`.

---

**Skill Version:** 1.0.0
**Last Updated:** 2026-02-11
**Maintainer:** GanjaMon Autonomous Agent
