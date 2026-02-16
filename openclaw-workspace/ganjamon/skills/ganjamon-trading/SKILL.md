---
name: ganjamon-trading
description: Execute alpha hunting and trading operations on Monad/Base chains
metadata:
  openclaw:
    emoji: 🍃
    requires:
      env:
        - MONAD_RPC_URL
        - BASE_RPC_URL
        - PRIVATE_KEY
        # Optional: only needed for Hyperliquid-specific execution paths.
        # Keep this skill runnable even when Hyperliquid creds are not configured.
      tools:
        - blockchain_transaction
        - wallet_balance
        - dex_quote
---

# GanjaMon Trading Skill

## Overview

The GanjaMon Trading skill enables autonomous alpha hunting and trade execution across multiple chains and platforms. This skill aggregates signals from Telegram stealth groups, Twitter KOLs, on-chain wallet tracking, and executes validated trades with profit optimization.

## Trading Platforms

- **nad.fun** - Monad native memecoin launches
- **Token Mill (LFJ)** - Monad token trading
- **Hyperliquid** - Perpetual futures (BTC, ETH, SOL, any liquid perp)
- **Polymarket** - Prediction markets
- **Base DEXs** - Aerodrome, Uniswap v3

## Signal Sources

1. **Telegram Stealth** - Monitor alpha groups for early calls
2. **Twitter KOL Tracking** - Track wallets of known profitable traders
3. **On-chain Analysis** - Smart money wallet monitoring
4. **Contract Honeypot Detection** - Validate token safety before trading

## Commands

### `alpha_scan`
Scan all configured signal sources for trading opportunities.

**Usage:**
```
alpha_scan [--chain monad|base|solana] [--min-confidence 0.7]
```

**Returns:**
- List of trading signals with confidence scores
- Contract addresses and safety analysis
- Recommended position sizes

### `get_positions`
List all current open positions across all platforms.

**Usage:**
```
get_positions [--platform all|hyperliquid|dex]
```

**Returns:**
- Current holdings with entry prices
- Unrealized PnL
- Position health metrics

### `queue_trade`
Queue a trade intent for validation and execution.

**Usage:**
```
queue_trade --token <address> --action buy|sell --amount <usd> [--chain monad|base]
```

**Flow:**
1. Validates token safety (honeypot check, LP analysis)
2. Calculates optimal slippage
3. Executes trade if validation passes
4. Logs to profit tracker

### `hyperliquid_perp`
Open or close perpetual futures position on Hyperliquid.

**Usage:**
```
hyperliquid_perp --symbol BTC --side long|short --size <usd> [--leverage 2-5x]
```

### `profit_report`
Generate profit allocation report.

**Usage:**
```
profit_report [--period 24h|7d|30d]
```

**Returns:**
- Total PnL across all platforms
- Profit allocation breakdown (60% compound, 25% $MON buy, 10% $GANJA buy, 5% burn)
- Trade performance by signal source

## Safety Guardrails

- **Max Position Size:** 5% of trading capital per trade
- **Honeypot Detection:** Mandatory for all token purchases
- **LP Lock Verification:** Check liquidity lock before buying
- **Slippage Limits:** Max 15% slippage on memecoins, 3% on majors
- **Stop Loss:** Automatic 30% stop loss on all perp positions

## Profit Allocation

Default allocation from trading profits:
- **60%** - Compound into trading capital
- **25%** - Buy $MON token (supports project token)
- **10%** - Buy $GANJA token (nad.fun self-funding)
- **5%** - Burn (deflationary mechanism)

Module-specific overrides documented in `cloned-repos/ganjamon-agent/CLAUDE.md`.

## Integration Notes

This skill integrates with:
- `ganjamon-mon-liquidity` - For $MON buy operations
- `ganjamon-social` - For trade announcements
- OpenClaw blockchain skills - For on-chain execution

## Error Handling

- **Insufficient Balance:** Queue retries until capital available
- **RPC Failures:** Fallback to backup RPC endpoints
- **Failed Trades:** Log and alert, don't retry automatically (avoid cascading losses)
- **Honeypot Detected:** Reject trade immediately, alert in social channels

## Monitoring

All trades logged to:
- `/var/log/ganjamon/trades.jsonl`
- Moltbook activity feed
- Internal profit tracker DB

---

**Skill Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** GanjaMon Autonomous Agent
