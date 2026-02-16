---
name: a2a-discovery
description: Discover agents on ERC-8004 registry, initiate A2A JSON-RPC calls, manage x402 micropayments
metadata:
  openclaw:
    emoji: "\U0001F50D"
    requires:
      env:
        - HAL_BASE_URL
        - PRIVATE_KEY
---

# A2A Discovery

## Overview

Discovers other AI agents via the ERC-8004 registry and 8004scan.io, initiates Agent-to-Agent (A2A) communication via JSON-RPC, and manages x402 micropayments for agent interactions.

## Commands

### `discover`
Run a discovery round against the ERC-8004 registry.

**Usage:**
```
a2a-discovery discover [--limit 119]
```

**Flow:**
1. Query 8004scan.io API for registered agents
2. Filter by network (Monad, Base, etc.) and active status
3. Ping each agent's A2A endpoint
4. Record reachable agents + capabilities
5. Log results to memory (~119 targets/round, ~$0.054 in x402)

**8004scan API notes:**
- Response uses `items` key (NOT `agents`)
- Agent endpoints are in `services.a2a.endpoint`

### `call`
Send an A2A JSON-RPC request to another agent.

**Usage:**
```
a2a-discovery call --agent-url "<url>" --method "<method>" --params '<json>'
```

**Flow:**
1. Construct JSON-RPC 2.0 request
2. Sign x402 payment (PAYMENT-SIGNATURE header, EIP-3009)
3. Send request to agent endpoint
4. If Meerkat agent (no JSON-RPC), fallback to `{"message": "text"}` body
5. Parse and return response

**x402 Payment Header:**
```
PAYMENT-SIGNATURE: 0x<signature>
```
Payload must include `resource` + `accepted` + `payload`. Signature needs `0x` prefix.

### `leaderboard`
Check GanjaMon's position on 8004scan.io leaderboard.

**Usage:**
```
a2a-discovery leaderboard
```

**Returns:** Our trust score (~82.34), rank, and top agents.
Agent #4 on Monad: `https://8004scan.io/agents/monad/4`

### `reputation`
Check our current reputation and signal history.

**Usage:**
```
a2a-discovery reputation
```

**Calls:**
```bash
curl -s ${HAL_BASE_URL}/api/blockchain/trust-score
curl -s ${HAL_BASE_URL}/api/blockchain/agent-info
```

## A2A Protocol

### Inbound (We Serve)
Port 8080 via `ganjamon-endpoint.service`:
- `oracle` — General Q&A about our agent
- `grow` — Cultivation data and plant status
- `signals` — Trading signal sharing

### Outbound (We Call)
- Standard A2A: JSON-RPC 2.0 over HTTPS
- Meerkat fallback: `{"message": "text"}` body (auto-detected)
- x402 payments: ~$0.001/call in USDC on Base

## Cost Tracking

- Discovery round: ~$0.054 (119 targets x $0.00045)
- Individual call: ~$0.001
- Use `model-usage` skill to track cumulative spend
