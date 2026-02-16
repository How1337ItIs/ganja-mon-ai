# ERC-8004 Top Agent Pattern Analysis

> **Research Date:** 2026-02-08
> **Purpose:** Analyze top-performing 8004 agents, extract borrowable patterns, and define upgrade path for GanjaMon's registration
> **Status:** Historical: early self-deployed Monad path was Agent #0. Current indexed identity is Agent #4 on Monad; registration still needed enrichment.

---

## Executive Summary

ERC-8004 ("Trustless Agents") is **now live on mainnet** across Ethereum, Base, Polygon, Monad, and BNB Chain. The standard defines three on-chain registries (Identity, Reputation, Validation) that together create a **discovery + trust layer** for autonomous AI agents. The top-performing agents on the 8004scan leaderboard are leveraging specific patterns that GanjaMon should adopt to build competitive reputation and visibility.

**The TL;DR:** Captain Dackie isn't just vibing — he's running a full-stack DeFAI operation with x402 payments, multi-protocol endpoints (MCP + A2A + OASF), and automated reputation farming. GanjaMon has early-mover history on Monad (self-deployed #0 path) and now indexed presence as Agent #4, but still needs to upgrade from bare-bones registration to a rich, multi-endpoint agent profile.

---

## 🏆 The Leaderboard (8004scan, Feb 2026)

| Rank | Agent | Score | Feedback | Description | Key Pattern |
|------|-------|-------|----------|-------------|-------------|
| #1 | **Captain Dackie** | 89.0 | 30 reviews, 2127 stars | DeFAI + x402 from Capminal | Full protocol stack, multi-chain |
| #2 | **James** | 88.8 | — | Robotics & automation specialist | Deep vertical expertise |
| #3 | **Minara AI** | 87.2 | — | Crypto market analyst + executor | Natural language trade execution |
| #4 | **Rick** | 86.5 | — | VR/AR expert guide | Emerging tech vertical |
| #5 | **Destiny** | 86.0 | — | — | — |
| #6 | **Gekko Rebalancer** | 85.5 | — | DeFi portfolio auto-rebalancer | Drift detection + autonomous execution |
| #7 | **Simon** | 85.0 | — | — | — |
| #8 | **Gekko** | 84.9 | — | Trading + yield optimization | Multi-chain DeFi |
| #9 | **Remittance** | 84.9 | — | — | Cross-border payments |
| — | **GanjaMon** | **???** | 0 reviews | "Early 8004 Monad agent - autonomous trading" | **Early mover; indexed as Agent #4; profile needed enrichment** |

---

## 🦆 Deep Dive: Captain Dackie (What the Hell Is He Up To?)

Captain Dackie is the **top-ranked** agent across 8004scan, built by **Capminal** — a DeFAI terminal built on ElizaOS. Here's the full breakdown:

### Identity & Architecture

| Attribute | Detail |
|-----------|--------|
| **Builder** | Capminal (DeFAI terminal) |
| **Foundation** | **ElizaOS** (the same framework from our Pattern #9 synthesis) |
| **Networks** | Base + Ethereum (multi-chain) |
| **Agent Type** | DeFAI + x402 AI Agent |
| **Reputation** | 100/100 on Base RNWY Explorer |
| **Leaderboard** | #1 on 8004scan (score 89.0) |

### Endpoint Stack (This Is Where He's Crushing It)

Captain Dackie registers **ALL** of the major protocol endpoints:

```json
{
  "services": [
    { "name": "web", "endpoint": "https://app.capminal.xyz" },
    { "name": "MCP", "version": "2025-01-15", "endpoint": "https://..." },
    { "name": "OASF", "version": "0.8.0", "endpoint": "ipfs://..." },
    { "name": "A2A", "version": "0.3.0", "endpoint": "https://.../.well-known/agent-card.json" },
    { "name": "x402", "endpoint": "https://deploy.capminal.xyz" },
    { "name": "email", "endpoint": "support@capminal.xyz" }
  ]
}
```

**Key insight**: Captain Dackie doesn't just register an A2A endpoint — he registers **MCP + A2A + OASF + x402 + web + email**. This maximizes discoverability and shows the agent can be reached through multiple protocols.

### Declared Capabilities

Captain Dackie's registration file declares rich, structured capabilities:

1. **Retrieval Augmented Generation** — Information retrieval and search
2. **Tool Interaction** — Tool use planning, API integration, blockchain interaction
3. **Advanced Reasoning** — Strategic planning, chain-of-thought, decision-making, risk assessment
4. **Data Analysis** — Quantitative analysis, market analysis, pattern recognition
5. **Automation** — Workflow automation, transaction execution

### x402 Payment Integration

The killer feature. Captain Dackie uses the **x402 protocol** (Coinbase standard) for machine-to-machine micropayments:

```
Client Request → HTTP 402 "Payment Required" → Agent signs USDC payment
→ Facilitator verifies on-chain → Service delivered + receipt
```

This enables **pay-per-use AI services** without subscriptions, API keys, or human intervention. The agent can autonomously charge for DeFi execution, market analysis, and trading strategies.

### How He Farms Reputation

1. **Multi-chain presence** — Registered on both Base and Ethereum
2. **Active feedback collection** — 30 feedback items with 2127 stars
3. **x402 payment proofs** — Payment receipts serve as verified interaction proof
4. **Social interaction** — Users can tag him on X or Farcaster to initiate trading

---

## 📊 Pattern Analysis: What Top Agents Do Differently

### Pattern 1: Full Protocol Stack Registration

**What:** Register endpoints for ALL major agent protocols, not just one.

| Protocol | Purpose | Who Uses It |
|----------|---------|-------------|
| **A2A** | Agent-to-agent communication | All top agents |
| **MCP** | Model Context Protocol tools/resources | Captain Dackie, Minara |
| **OASF** | Open Agent Services Framework (skills taxonomy) | Dackie, extended agents |
| **x402** | Micropayments over HTTP | Dackie, Gekko |
| **web** | Human-facing interface | Most agents |
| **agentWallet** | Payment address | All agents |

**GanjaMon Gap:** Our registration only has an `agentURI` pointing to `https://agent.grokandmon.com/.well-known/agent.json`. We need to populate this with the full service array.

### Pattern 2: Structured Capability Declaration (OASF)

**What:** Use the OASF (Open Agentic Schema Framework) skill taxonomy to declare capabilities in a machine-readable format.

```json
{
  "name": "OASF",
  "version": "0.8",
  "endpoint": "ipfs://...",
  "skills": [
    "analytical_skills/data_analysis/blockchain_analysis",
    "domain_expertise/agriculture/cultivation",
    "creative_skills/content_creation/persona_writing"
  ],
  "domains": [
    "technology/blockchain",
    "agriculture/cannabis",
    "entertainment/streaming"
  ]
}
```

**Why it matters:** This makes agents discoverable by skill category. Other agents looking for "blockchain analysis" or "cultivation expertise" can find GanjaMon programmatically.

### Pattern 3: x402 Payment-Backed Reputation

**What:** Use payment proofs as Sybil-resistant reputation signals.

The 8004 feedback system supports a `proofOfPayment` field:

```json
{
  "proofOfPayment": {
    "fromAddress": "0x...",
    "toAddress": "0x...",
    "chainId": "143",
    "txHash": "0x..."
  }
}
```

**Why it matters:** Feedback from paying customers is worth 10x more than free reviews. This is the anti-wash-rating mechanism.

### Pattern 4: Multi-Chain Registration

**What:** Register the same agent identity on multiple chains for maximum visibility.

Captain Dackie is on both Base and Ethereum. The registration file supports a `registrations` array:

```json
{
  "registrations": [
    { "agentId": 4, "agentRegistry": "eip155:143:0x8004A169..." },
    { "agentId": 42, "agentRegistry": "eip155:8453:0x..." }
  ]
}
```

**GanjaMon Opportunity:** We're indexed as Agent #4 on Monad (legacy self-deployed path was Agent #0). We should also register on Base (largest 8004 ecosystem) and Ethereum mainnet.

### Pattern 5: Autonomous Portfolio Management (Gekko Pattern)

**What:** Agents that autonomously manage DeFi positions score higher because they generate **measurable, verifiable results**.

Gekko Rebalancer:
- Monitors portfolio drift from target allocations
- Calculates optimal rebalancing strategies
- Executes trades autonomously
- Reports performance via x402-backed feedback

**GanjaMon Application:** Our autonomous trading agent on Monad already does this with $MON. We just need to report results through the 8004 reputation system.

### Pattern 6: Human-Facing Endpoints (New in v1.1)

**What:** Register web interfaces and social channels as endpoints:

```json
{
  "services": [
    { "name": "web", "endpoint": "https://grokandmon.com" },
    { "name": "x", "endpoint": "https://x.com/ganjamonai" },
    { "name": "telegram", "endpoint": "https://t.me/ganjamonai" }
  ]
}
```

**Why it matters:** 8004scan v1.1 now indexes "human-facing endpoints" — agents with web and social presence rank higher in discovery.

### Pattern 7: Agent Metadata Hash Verification

**What:** Use `agentHash` (8004scan extension) to prove metadata integrity:

```solidity
// On-chain: setMetadata(agentId, "agentHash", keccak256(metadataJSON))
```

This creates an on-chain commitment that the off-chain metadata hasn't been tampered with. It's a trust signal that bumps your ranking.

---

## 🎯 GanjaMon Upgrade Plan

### Current State (Bare-Bones)

```
Agent ID: #4 (indexed path; legacy self-deployed path used #0)
Chain: Monad (143)
Identity Registry: 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432
Agent URI: https://agent.grokandmon.com/.well-known/agent.json
Status: REGISTERED BUT EMPTY PROFILE
```

### Target State (Full-Stack Agent)

#### Phase 1: Rich Registration File (Priority: CRITICAL)

Create and deploy `https://agent.grokandmon.com/.well-known/agent.json`:

```jsonc
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "GanjaMon",
  "description": "AI-autonomous cannabis cultivation agent combining Grok AI, Monad blockchain ($MON token), IoT sensors, and Rasta Voice persona. Early ERC-8004 mover on Monad; currently indexed as Agent #4. Manages legal personal cultivation under California Prop 64, live-streams cultivation data, and trades $MON autonomously.",
  "image": "https://grokandmon.com/images/ganjamon-avatar.png",
  
  "services": [
    {
      "name": "web",
      "endpoint": "https://grokandmon.com"
    },
    {
      "name": "A2A",
      "version": "0.3.0",
      "endpoint": "https://agent.grokandmon.com/.well-known/agent-card.json"
    },
    {
      "name": "MCP",
      "version": "2025-06-18",
      "endpoint": "https://agent.grokandmon.com/mcp"
    },
    {
      "name": "OASF",
      "version": "0.8",
      "endpoint": "ipfs://...",
      "skills": [
        "domain_expertise/agriculture/cannabis_cultivation",
        "analytical_skills/data_analysis/sensor_analytics",
        "analytical_skills/data_analysis/blockchain_analysis",
        "creative_skills/content_creation/persona_voice",
        "automation/trading/defi_execution"
      ],
      "domains": [
        "agriculture/cannabis",
        "technology/blockchain",
        "technology/iot",
        "entertainment/streaming"
      ]
    },
    {
      "name": "agentWallet",
      "endpoint": "eip155:143:0xc48035..."
    },
    {
      "name": "x",
      "endpoint": "https://x.com/ganjamonai"
    },
    {
      "name": "telegram",
      "endpoint": "https://t.me/ganjamonai"
    }
  ],

  "x402Support": true,
  "active": true,

  "registrations": [
    {
      "agentId": 4,
      "agentRegistry": "eip155:143:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
    }
  ],

  "supportedTrust": ["reputation"],
  "updatedAt": 1739059200
}
```

#### Phase 2: On-Chain Metadata Enhancement

```bash
# Set agentHash for metadata integrity
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "setMetadata(uint256,string,bytes)" 4 "agentHash" $(cast keccak <metadata_json>) \
  --private-key $KEY --rpc-url $MONAD_RPC

# Set capabilities metadata
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "setMetadata(uint256,string,bytes)" 4 "capabilities" \
  $(cast abi-encode "(string[])" '["cultivation","trading","streaming","analysis"]') \
  --private-key $KEY --rpc-url $MONAD_RPC
```

#### Phase 3: Reputation Farming

1. **Self-generated feedback from verified interactions:**
   - Every $MON trade executed → submit performance feedback
   - Every sensor data report → submit uptime feedback
   - Every stream session → submit availability feedback

2. **x402 payment integration:**
   - Expose Ganjafy as x402-payable service
   - Expose cultivation data API as x402-payable
   - Every paid interaction auto-generates verified feedback

3. **Cross-chain expansion:**
   - Register on Base (largest 8004 ecosystem)
   - Register on Ethereum mainnet (prestige)

#### Phase 4: A2A Agent Card

Deploy `https://agent.grokandmon.com/.well-known/agent-card.json` following Google's A2A spec:

```jsonc
{
  "name": "GanjaMon",
  "description": "AI-autonomous cannabis cultivation agent on Monad",
  "url": "https://agent.grokandmon.com",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "cultivation-monitor",
      "name": "Cultivation Monitor",
      "description": "Real-time IoT sensor monitoring for cannabis cultivation",
      "tags": ["cultivation", "iot", "sensors", "vpd"]
    },
    {
      "id": "market-analysis",
      "name": "MON Market Analysis",
      "description": "Real-time analysis of $MON token metrics and trading signals",
      "tags": ["trading", "defi", "monad"]
    },
    {
      "id": "ganjafy",
      "name": "Ganjafy Image Transform",
      "description": "Transform images with deep Rasta aesthetic",
      "tags": ["image", "transform", "creative"]
    }
  ],
  "authentication": {
    "schemes": ["x402"]
  }
}
```

---

## 🔑 Key Takeaways for Ganja Mon

### What We're Doing Right
1. **Early mover on Monad** — self-deployed path proved fast execution; indexed path is Agent #4
2. **Already deployed all 3 registries** — Identity, Reputation, Validation
3. **Real utility** — actual cultivation, actual trading, actual streaming
4. **Unique positioning** — no other cannabis/agriculture agent in the 8004 ecosystem

### What We're Missing (vs. Captain Dackie)
1. **Empty registration file** — our `agent.json` doesn't exist or is bare-bones
2. **No multi-protocol endpoints** — no MCP, A2A, OASF, or x402 declared
3. **Zero reputation** — 0 feedback items vs. Dackie's 30
4. **No x402 payments** — not monetizing agent services
5. **Single-chain registration** — only on Monad, not on Base or Ethereum
6. **No agent hash** — on-chain metadata integrity not set
7. **No OASF skills taxonomy** — capabilities not machine-discoverable

### The Captain Dackie Playbook (Steal This)
1. **Built on ElizaOS** → component architecture with Actions/Services/Providers
2. **Multi-chain presence** → register on every major chain
3. **x402 from day one** → every interaction generates payment-backed reputation
4. **Full protocol stack** → MCP + A2A + OASF endpoints all registered
5. **Social interaction** → tag on X/Farcaster to trigger trades
6. **Structured capabilities** → OASF skills taxonomy for programmatic discovery

### What We Can Beat Dackie On
1. **Real physical-world utility** — cannabis cultivation is tangible, measurable
2. **IoT integration** — actual sensor data, not just market data
3. **Cultural identity** — Rasta Voice is a genuine, irreplicable brand
4. **Monad-native** — he's on Base, we have indexed Monad identity (Agent #4)
5. **Vertical depth** — we go deep in one domain vs. generic DeFi

---

## 📚 ERC-8004 Quick Reference

### Contract Addresses (Monad)

| Registry | Address |
|----------|---------|
| IdentityRegistry | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
| ReputationRegistry | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` |
| ValidationRegistry | `0x98135C011cCB6C5cd2b63E48D55Cf047847c8d3A` |

### Key Resources

| Resource | URL |
|----------|-----|
| ERC-8004 Spec | https://eips.ethereum.org/EIPS/eip-8004 |
| 8004scan Explorer | https://8004scan.io |
| 8004agents.ai | https://8004agents.ai |
| Best Practices | https://best-practices.8004scan.io |
| RNWY Explorer | https://rnwy.com |
| x402 Protocol | https://x402.org |
| 8004 Telegram | https://t.me/ERC8004 |

### Key Authors

| Person | Org | Role |
|--------|-----|------|
| Marco De Rossi | MetaMask | ERC-8004 author |
| Davide Crapis | Ethereum Foundation | ERC-8004 author |
| Jordan Ellis | Google | ERC-8004 author |
| Erik Reppel | Coinbase | ERC-8004 author |

---

*GanjaMon is Agent #4 on the indexed Monad registry (after early self-deployed #0). Time to act like it.*
