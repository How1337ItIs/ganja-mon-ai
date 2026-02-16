---
name: reputation-publisher
description: Publish ERC-8004 on-chain reputation signals and monitor trust score
metadata:
  openclaw:
    emoji: "\U0001F3C6"
    requires:
      env:
        - HAL_BASE_URL
        - PRIVATE_KEY
---

# Reputation Publisher

## Overview

Publishes on-chain reputation signals via the ERC-8004 standard on Monad. Maintains GanjaMon's trust score on 8004scan.io by publishing 10 signals every 4 hours.

## Commands

### `publish`
Publish reputation signals on-chain.

**Usage:**
```
reputation-publisher publish [--signals 10]
```

**Calls:**
```bash
curl -s -X POST ${HAL_BASE_URL}/api/blockchain/publish-reputation \
  -H "Content-Type: application/json" \
  -d '{"signals": 10}'
```

**Flow:**
1. Call HAL API to publish N on-chain signals
2. Each signal costs gas on Monad (minimal)
3. Log transaction hashes to memory
4. Check updated trust score after publishing

### `score`
Check current trust score on 8004scan.io.

**Usage:**
```
reputation-publisher score
```

**Calls:**
```bash
curl -s ${HAL_BASE_URL}/api/blockchain/trust-score
```

**Returns:** Current trust score (~82.34), trend, and rank.

### `info`
Get full agent info from the ERC-8004 registry.

**Usage:**
```
reputation-publisher info
```

**Calls:**
```bash
curl -s ${HAL_BASE_URL}/api/blockchain/agent-info
```

**Returns:** Agent #4 on Monad, owner address, registration date, signal count.

### `history`
View reputation signal publishing history.

**Usage:**
```
reputation-publisher history [--days 7]
```

## Schedule

- **Every 4 hours**: Publish 10 on-chain signals (cron: `30 */4 * * *`)
- **Target**: Trust score above 80
- **Agent**: #4 on Monad (`https://8004scan.io/agents/monad/4`)
- **Owner**: `0x734B0e337bfa7d4764f4B806B4245Dd312DdF134`

## Signal Types

Signals published represent:
- Sensor data attestations (temperature, humidity, VPD readings)
- Grow decision attestations (watering events, stage transitions)
- Trading signal attestations (alpha signals discovered)
- A2A interaction attestations (successful agent-to-agent calls)
