---
name: ganjamon-mon-liquidity
description: Monitor $MON token liquidity across Monad and Base chains
metadata:
  openclaw:
    emoji: 💧
    requires:
      env:
        - MONAD_RPC_URL
        - BASE_RPC_URL
        # Optional: improves bridge health checks if configured.
      contracts:
        - monad_mon_token
        - base_mon_token
        - aerodrome_pool
---

# GanjaMon MON Liquidity Skill

## Overview

The GanjaMon MON Liquidity skill monitors liquidity depth, trading volume, and cross-chain bridge health for the $MON token on Monad (native) and Base (bridged via Wormhole NTT).

## Token Addresses

### Monad (Native Chain)
- **Contract:** `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`
- **Market:** `0xfB72c999dcf2BE21C5503c7e282300e28972AB1B` (Token Mill)
- **Trade:** [LFJ Token Mill](https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b)

### Base (Bridged via Wormhole NTT)
- **Contract:** `0xE390612D7997B538971457cfF29aB4286cE97BE2`
- **Pool:** `0x2f2ec3e1b42756f949bd05f9b491c0b9c49fee3a` (MON/USDC on Aerodrome)
- **Trade:** [Aerodrome Finance](https://aerodrome.finance/swap?from=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&to=0xE390612D7997B538971457cfF29aB4286cE97BE2)

## Bridge Infrastructure

### Wormhole NTT Bridge
- **Monad -> Base:** WORKING (locks on Monad, mints on Base)
- **Base -> Monad:** WORKING (burns on Base, unlocks on Monad)
- **VAA Attestation Time:** ~30 seconds (fast!)

See: `.claude/context/token.md` for complete bridge contract addresses.
See: `docs/NTT_DEPLOYMENT_LESSONS.md` for debugging lessons.

## Commands

### `liquidity_status`
Get current liquidity depth across all chains and markets.

**Usage:**
```
liquidity_status [--chain all|monad|base] [--format json|summary]
```

**Returns:**
- Total liquidity in USD across all pools
- MON/USDC pool depth on Base (Aerodrome)
- Token Mill market depth on Monad
- 24h trading volume
- Price comparison across chains (arbitrage opportunities)

### `bridge_health`
Check Wormhole NTT bridge health and recent transfers.

**Usage:**
```
bridge_health [--recent 10]
```

**Returns:**
- Recent bridge transactions (last N)
- VAA attestation times
- Stuck/pending transfers (if any)
- Transceiver peer relationships status

### `buy_mon`
Execute $MON token buy with trading profits (25% allocation).

**Usage:**
```
buy_mon --amount <usd> [--chain monad|base]
```

**Flow:**
1. Checks liquidity on both chains
2. Selects chain with best price (after gas costs)
3. Executes swap via DEX
4. Logs purchase to profit tracker

**Integration:** Called automatically by `ganjamon-trading` skill after profitable trades.

### `mon_metrics`
Generate comprehensive $MON token metrics report.

**Usage:**
```
mon_metrics [--period 24h|7d|30d]
```

**Returns:**
- Market cap (fully diluted)
- Circulating supply (Monad + Base)
- Holder count per chain
- Top 10 holders
- Trading volume breakdown
- Liquidity depth over time
- Bridge transfer volume

### `arbitrage_check`
Check for price discrepancies between Monad and Base.

**Usage:**
```
arbitrage_check [--min-spread 2%]
```

**Returns:**
- Price on Monad (Token Mill)
- Price on Base (Aerodrome)
- Spread percentage
- Estimated profit after gas/bridge fees
- Recommendation: execute arbitrage if profitable

### `add_liquidity`
Add liquidity to MON/USDC pool on Base (Aerodrome).

**Usage:**
```
add_liquidity --mon-amount <tokens> --usdc-amount <tokens>
```

**Flow:**
1. Approves MON and USDC for Aerodrome router
2. Adds liquidity with optimal ratio
3. Receives LP tokens
4. Logs liquidity provision event

## Price Feeds

Primary price sources:
1. **Monad:** Token Mill API (`https://lfj.gg/api/...`)
2. **Base:** Aerodrome pool reserves
3. **Fallback:** CoinGecko API (if available)

## Liquidity Thresholds

Alert thresholds for liquidity monitoring:

| Metric | Warning | Critical |
|--------|---------|----------|
| **Total Liquidity** | < $10k | < $5k |
| **Base Pool TVL** | < $5k | < $2k |
| **24h Volume** | < $500 | < $100 |
| **Bridge Stuck Txs** | > 0 | > 3 |

## Integration Notes

This skill integrates with:
- `ganjamon-trading` - Receives profit allocations for $MON buys
- `ganjamon-social` - Posts liquidity milestones to social channels
- Wormholescan API - For bridge transaction monitoring

## Bridge Debugging

**CRITICAL:** When investigating bridge transactions, ALWAYS query the Wormholescan API for ALL VAAs, not just the UI. The UI may show an orphan transceiver's VAA while valid VAAs exist elsewhere.

```bash
# Get all VAAs for a transaction
curl "https://api.wormholescan.io/api/v1/operations?txHash=0x..."

# Check specific transceiver's VAAs
curl "https://api.wormholescan.io/api/v1/vaas/{chainId}/{emitterAddress}"
```

See: `.claude/rules/wormhole-ntt.md` for complete debugging protocol.

## Monitoring & Alerts

Liquidity alerts triggered when:
- **TVL drops** below warning threshold
- **Volume dries up** (< 10% of 7-day average)
- **Bridge transaction stuck** for > 5 minutes
- **Price spread** between chains > 10% (arbitrage opportunity)
- **Large holder dumps** (> 5% of supply)

Alerts posted to:
- Internal logs: `/var/log/ganjamon/liquidity.log`
- Telegram: @MonGardenBot DMs to admin
- Moltbook: Activity feed (for major events)

## Error Handling

- **RPC Failures:** Fallback to backup RPC endpoints (Alchemy, Infura)
- **API Rate Limits:** Exponential backoff with jitter
- **Price Feed Unavailable:** Use last known price, alert after 15 minutes
- **Bridge Transaction Failed:** Log error, investigate with Wormholescan API

---

**Skill Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** GanjaMon Autonomous Agent
