---
name: trading-signals
description: Portfolio monitoring, alpha signal aggregation, and trade announcement generation
metadata:
  openclaw:
    emoji: "\U0001F4C8"
    requires:
      env:
        - HAL_BASE_URL
---

# Trading Signals

## Overview

Monitors the GanjaMon trading portfolio, aggregates alpha signals from multiple sources, and generates trade announcements. All trade execution goes through `lobster` approval pipelines.

## Commands

### `portfolio`
Get current portfolio status and P&L.

**Usage:**
```
trading-signals portfolio
```

**Calls:**
```bash
curl -s ${HAL_BASE_URL}/api/trading/portfolio
```

**Returns:** Positions, P&L, allocation breakdown (60/25/10/5 split).

### `scan`
Scan for alpha signals across all sources.

**Usage:**
```
trading-signals scan
```

**Flow:**
1. `GET /api/trading/signals` → signals from HAL
2. Use `alpha-finder` community skill for social + on-chain alpha
3. Use `crypto-whale-monitor` for whale movements
4. Use `blogwatcher` for breaking crypto news
5. Aggregate and rank by confidence

### `announce`
Generate a trade announcement for social posting.

**Usage:**
```
trading-signals announce --asset <symbol> --action buy|sell --profit <usd>
```

**Flow:**
1. Format profit/trade in Rasta voice using `social-composer`
2. Never include wallet addresses or full position sizes (opsec)
3. Return formatted text ready for cross-platform posting

### `profit_report`
Generate profit/loss report for the past N days.

**Usage:**
```
trading-signals profit_report [--days 7]
```

**Flow:**
1. `GET /api/trading/history` → trade history
2. Calculate total P&L, win rate, best/worst trades
3. Calculate allocation splits: 60% compound, 25% $MON, 10% $GANJA, 5% burn
4. Format as report

### `execute`
Execute a trade via HAL API (requires `lobster` approval).

**Usage:**
```
trading-signals execute --asset <symbol> --action buy|sell --amount <usd>
```

**Safety:** This command MUST go through a `lobster` approval pipeline:
```
trading-signals.scan | approve --prompt "Execute trade?" | trading-signals.execute
```

## Trading Rules

- Paper trading by default (`ENABLE_TRADING=false`)
- Never risk more than 5% of portfolio on a single trade
- All live trades require operator approval via `lobster` pipeline
- Profit split: 60% compound → 25% buy $MON → 10% buy $GANJA → 5% burn
- Track all costs with `model-usage` skill
