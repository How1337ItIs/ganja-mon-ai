# OpenClaw Blockchain Skills Reference

**Last Updated:** February 5, 2026
**Location:** `cloned-repos/openclaw-blockchain-skills/`

## Overview

OpenClaw provides 39+ blockchain-focused skills for AI agents. Skills are **instructional guides** (Markdown + YAML) that teach agents how to use tools - they are NOT executable code.

---

## Skill Categories

### A. Payment & Commerce Skills

| Skill | Protocol | Key Features |
|-------|----------|--------------|
| **AGIRAILS** | ACTP Protocol | 8-state escrow, USDC on Base L2, Trustless agent commerce |
| **Web3 Pay** | Subscription | Accept USDC on Base/Polygon/Arbitrum/Ethereum |
| **Revolut Business** | Fiat Payments | OAuth, FX exchange, Transaction history |
| **LetsPing (Cordia)** | Approval Gate | Human-in-the-loop, High-risk action escalation |

### B. On-Chain Analytics

| Skill | Data Source | Capabilities |
|-------|-------------|--------------|
| **Arkham Intelligence** | Arkham API (10+ chains) | Whale tracking, Wallet analysis, Entity investigation |
| **Heurist Mesh** | MCP (30+ agents) | Token search, Trending tokens, Funding rates |
| **Crypto Price** | CoinGecko, Hyperliquid | Price lookup, Candlestick charts |
| **Fintech Veille** | RSS (12+ feeds) | News aggregation, Smart scoring |

### C. Wallet & Self-Custody

| Skill | Protocol | Capabilities |
|-------|----------|--------------|
| **WDK (Tether Wallet Dev Kit)** | Multi-chain SDK | EVM + Solana support, Self-custodial |
| **Universal Profile** | LSP (Lukso) | Identity management, NFT marketplace |
| **Spark BTC** | Bitcoin L2 | Self-custodial Bitcoin wallets |

### D. Trading & Execution

| Skill | Venue | Features |
|-------|-------|----------|
| **OpenClaw Trading Assistant** | Hyperliquid | Perps trading, Sentiment, 1-2% risk lock |
| **Decision Markets** | Polymarket | Prediction market trading |
| **Clawp.ad** | nad.fun | Autonomous token launches |

### E. Infrastructure & Monitoring

| Skill | Purpose | Integration |
|-------|---------|------------|
| **Skill Scanner** | Security | Malware detection, Code obfuscation flags |
| **ClawdTM** | Marketplace | Skill discovery, Rating system |
| **Heurist Mesh MCP** | OpenClaw Bridge | 30+ agents via MCP |

---

## Skill File Format

### Directory Structure

```
skill-directory/
├── SKILL.md              # Main documentation + YAML header
├── README.md             # Installation & overview
├── examples/             # Usage examples
└── references/           # Detailed specs
```

### YAML Metadata

```yaml
---
name: skill-name
version: 2.1.0
description: "One-liner description"
homepage: https://...
repository: https://github.com/...
license: MIT
tags:
  - blockchain
  - payments
metadata:
  clawdbot:
    emoji: "💸"
    category: payments
    minVersion: "1.0.0"
    requires:
      env:
        - AGENT_PRIVATE_KEY
      bins:
        - python3
---
```

### Skill Flags

| Flag | Purpose |
|------|---------|
| `user-invocable: true` | Exposed as slash command |
| `disable-model-invocation: true` | Hidden from prompt |
| `command-dispatch: tool` | Route to specific tool |
| `command-tool: discord` | Tool name to invoke |
| `command-arg-mode: raw` | Forward raw args |

---

## Key Integration Patterns

### HTTP APIs (Arkham, Heurist)
```python
# Wrap REST calls with error handling
response = await client.get(f"/api/v2/address/{address}")
return normalize_holdings(response.json())
```

### MCP Servers (Heurist Mesh)
```bash
# Call remote agents via mcporter CLI
mcporter call token_search --query "trending meme coins"
```

### Wallet Keys
```bash
# Store in env vars, never in code
export AGENT_PRIVATE_KEY="0x..."
```

### Local State
```python
# Store user data in ~/.clawdbot/skill-name/
users_file = Path.home() / ".clawdbot" / "web3-pay" / "users.json"
```

---

## ACTP (Agent Commerce Transaction Protocol)

The AGIRAILS skill uses an 8-state escrow protocol:

```
INITIATED → QUOTED → COMMITTED → IN_PROGRESS → DELIVERED → SETTLED
                                      ↓
                                  DISPUTED → RESOLVED
```

### Example Flow
1. Client initiates job request
2. Provider quotes price
3. Client commits USDC to escrow
4. Provider delivers work
5. Client accepts, USDC released

---

## Trading Assistant Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Conversational Interface (OpenClaw)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Decision Engine (Alpha Arena Models)               │
│  • Strategy scoring & decay                                │
│  • Self-evaluation loop                                    │
│  • RAG-based memory                                        │
└────┬──────────────────────────────────────┬────────────────┘
     │                                      │
     ▼                                      ▼
┌──────────────────────┐          ┌──────────────────────────┐
│ Market Intelligence  │          │   Trading Engine        │
│ • Twitter/X          │          │ • Hyperliquid API       │
│ • Sentiment          │          │ • 1-2% position lock   │
└──────────────────────┘          └──────────────────────────┘
```

### Hard Risk Guardrails
- 1-2% max position size (cannot be overridden)
- Trend alignment filter ("Don't catch knives")
- Strategy decay after 3 consecutive failures
- RAG memory avoids repeating mistakes

---

## Skill Security

### Skill Scanner Detects
- `eval()`, `exec()`, `subprocess` with user input
- Crypto mining keywords
- Obfuscated imports
- Base64 decoded execution
- Unauthorized exfiltration patterns

### Audit Checklist
```bash
# Check code execution
grep -r "eval\|exec\|subprocess" skill-folder/

# Check hardcoded URLs
grep -rE "https?://" skill-folder/ | grep -v "github\|api\."

# Check private key handling
grep -r "private_key\|secret\|password" skill-folder/
```

---

## Creating a New Skill

### Minimal Template

```markdown
---
name: my-blockchain-skill
description: Do something with blockchain
metadata:
  clawdbot:
    emoji: "⚙️"
    requires:
      env:
        - MY_API_KEY
---

# My Blockchain Skill

## Quick Start

\`\`\`bash
export MY_API_KEY="your-key"
python3 my_skill.py --action xyz
\`\`\`

## Actions
- **do_thing** - Does a thing
```

### Registration
1. Save as `~/.openclaw/skills/my-skill/SKILL.md`
2. OpenClaw auto-discovers on startup
3. Test: `openclaw agent --message "use my-skill to do thing"`

---

## Multi-Skill Workflows

### Trading Pipeline Example

```
Detection (Heurist Mesh)
  ↓ token_search → finds trending coin
  ↓
Validation (Arkham Intelligence)
  ↓ Check holders → detect rug risk
  ↓
Approval (LetsPing)
  ↓ Human approval for >$100
  ↓
Execution (Trading Assistant)
  ↓ Buy via Hyperliquid
  ↓
Settlement (AGIRAILS if agent-to-agent)
  ↓ Pay analyst via escrow
```

---

## GanjaMon Integration

### Signal → Trade Flow

```
Stealth Listener (Pyrogram)
  ↓ CA extracted from exclusive channel
  ↓
FastAPI Aggregator
  ↓ Confluence detection (2+ channels)
  ↓
Arkham Intelligence Skill
  ↓ holder_distribution() → rug risk
  ↓
Token Safety Score
  ↓
Execution Decision
  ↓ If score > 0.7 → execute
  ↓
nad.fun bonding curve BUY
  ↓
Profit Allocation
  ↓ 60% compound, 25% $MON buyback
```

---

## Key Files

| Location | Purpose |
|----------|---------|
| `cloned-repos/openclaw-blockchain-skills/` | 39+ skills |
| `cloned-repos/openclaw-blockchain-skills/openclaw-skill/` | AGIRAILS payments |
| `cloned-repos/openclaw-blockchain-skills/arkham-intelligence-claude-skill/` | On-chain analytics |
| `cloned-repos/openclaw-blockchain-skills/skill-scanner/` | Security audit |
| `openclaw-trading-assistant/` | Trading assistant |
| `docs/clawk-skill.md` | Clawk API reference |
| `docs/TRADING_ALPHA_AGENT_PATTERNS.md` | Pattern atlas |

---

## References

- ClawHub (Skill Marketplace): https://clawhub.com
- ClawdTM API: https://clawdtm.com/api/v1
- OpenClaw Docs: https://docs.clawd.bot
- Arkham Intelligence: https://platform.arkhamintelligence.com/
- Heurist Mesh: https://heurist.ai/
