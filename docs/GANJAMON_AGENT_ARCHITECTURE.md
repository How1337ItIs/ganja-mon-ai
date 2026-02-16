# GanjaMon Agent Architecture

**Last Updated:** February 5, 2026
**Location:** `cloned-repos/ganjamon-agent/`

## Primary Mission

> **Generate absurd amounts of money to bolster $MON token price and ensure adequate liquidity across all chains.**

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         GANJAMON TRADING AGENT                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    SELF-FUNDING MECHANISM                             │  │
│  │                                                                       │  │
│  │   $GANJA Token on nad.fun ──→ Trading Fees ──→ Agent Wallet          │  │
│  │      ↑                                              │                 │  │
│  │      │                                              ▼                 │  │
│  │      │                                     Fee Receiver Module        │  │
│  │      │                                     80% → Trading Capital      │  │
│  │      │                                     15% → Buyback $GANJA       │  │
│  │      └─────────────────────────────────────  5% → Buyback $MON        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  SIGNAL SOURCES                                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────────┐        │
│  │  TELEGRAM   │ │  TWITTER    │ │  ON-CHAIN   │ │   LAUNCHES    │        │
│  │  CA Scanner │ │  KOL Monitor│ │  Wallet     │ │   nad.fun     │        │
│  │  (Stealth)  │ │             │ │  Tracker    │ │   Token Mill  │        │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └───────┬───────┘        │
│         └────────────────┴───────────────┴───────────────┘                 │
│                                   │                                        │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    SIGNAL AGGREGATOR (FastAPI)                       │  │
│  │  • Confluence detection (multi-source = high confidence)            │  │
│  │  • Scoring: channel quality + sensor weight + recency               │  │
│  │  • Threshold triggers (2+ sources, score > 0.5)                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                   │                                        │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    VALIDATION LAYER                                  │  │
│  │  • Honeypot check (GoPlus, Honeypot.is APIs)                        │  │
│  │  • LP locked/burned check                                           │  │
│  │  • Top holders distribution                                         │  │
│  │  • Contract safety scan (mintable, blacklist, proxy)                │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                   │                                        │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    EXECUTION ENGINE (web3.py)                        │  │
│  │  • nad.fun bonding curve buys                                       │  │
│  │  • Position sizing based on signal + safety scores                  │  │
│  │  • Auto TP (3x → 75% sell) / SL (-50% → full exit)                  │  │
│  │  • Continuous position monitoring                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                   │                                        │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    PROFIT ALLOCATOR                                  │  │
│  │  • 60% → Compound (more trading capital)                            │  │
│  │  • 30% → Buyback $MON via Token Mill                                │  │
│  │  • 10% → Burn (send to 0xdead)                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Token Deployments

| Chain | Token Address | Pool | DEX |
|-------|--------------|------|-----|
| **Monad** (native) | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` | `0xfB72c999dcf2BE21C5503c7e282300e28972AB1B` | Token Mill (LFJ) |
| **Base** (bridged) | `0xE390612D7997B538971457cfF29aB4286cE97BE2` | `0x2f2ec3e1b42756f949bd05f9b491c0b9c49fee3a` | Aerodrome |

---

## Signal Sources (Implemented)

| Source | Module | Status |
|--------|--------|--------|
| Smart Money Tracking | `src/signals/smart_money.py` | DEPLOYED |
| AI Agent Detection | `src/signals/ai_agent_detector.py` | DEPLOYED |
| Whale Alerts | `src/signals/whale_detector.py` | DEPLOYED |
| ERC-8004 Monitor | `src/signals/erc8004_monitor.py` | DEPLOYED |
| GMGN Smart Money | `src/research/gmgn_client.py` | DEPLOYED |
| Flight Tracking | `src/research/flight_tracker.py` | DEPLOYED |
| Mempool Monitor | `src/signals/mempool_monitor.py` | DEPLOYED |
| Telegram Alpha | `src/signals/telegram_alpha_monitor.py` | DEPLOYED |
| Copy Trading | `src/signals/copy_trader.py` | DEPLOYED |
| Agent Monitor | `src/signals/agent_monitor.py` | DEPLOYED |

---

## Trading Strategies

| Strategy | Target | Entry | Exit |
|----------|--------|-------|------|
| **Shotgun Sniping** | New launches | 1-2% portfolio | 3x sell 50%, 10x sell 75% |
| **KOL Front-Running** | Twitter mentions | <1 sec detection | Retail pump (2-10 min) |
| **Insider Shadow** | Whale buys | Mirror buy | Mirror sell |
| **Narrative Momentum** | Emerging categories | 5-10% position | Peak sentiment |
| **Funding Rate Arb** | Funding >50% APR | Short when positive | Normalize |
| **Momentum Perps** | 3%+ hourly move | 3x leverage | 5% TP / 2% SL |
| **Prediction Arb** | YES+NO ≠ 1.0 | Sell both | Resolution |

---

## Deep Agent Intelligence System

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                          DEEP AGENT INTELLIGENCE                               │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ALPHA HUNTERS (8 Domains)        MULTI-AGENT REASONER                         │
│  ┌──────────────────────┐         ┌──────────────────────────┐                 │
│  │ • on_chain           │         │ 1. ANALYST (DeepSeek)     │                 │
│  │ • social             │ ──────► │ 2. RISK (DeepSeek-R1)     │ ──► TRADE/WAIT │
│  │ • narrative          │         │ 3. CONTRARIAN (GPT-4o)    │                 │
│  │ • technical          │         │ 4. COORDINATOR            │                 │
│  │ • fundamental        │         └──────────────────────────┘                 │
│  │ • macro              │                                                      │
│  │ • arbitrage          │         CROSS-DOMAIN SYNTHESIZER                     │
│  │ • sentiment          │         ┌──────────────────────────┐                 │
│  └──────────────────────┘         │ Connect signals across   │                 │
│                                   │ domains for confluence   │                 │
│  STRATEGY OPTIMIZER               └──────────────────────────┘                 │
│  ┌──────────────────────┐                                                      │
│  │ Learn from outcomes  │         META-AGENT                                   │
│  │ Update focus areas   │         ┌──────────────────────────┐                 │
│  │ Reallocate attention │         │ Coordinates all systems  │                 │
│  └──────────────────────┘         │ Directs tool acquisition │                 │
│                                   └──────────────────────────┘                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Ralph Loop Self-Improvement

**Location:** `cloned-repos/ganjamon-agent/.ralph/`

### How It Works
1. Agent identifies performance gaps → requests upgrades
2. Requests written to `data/upgrade_requests.json`
3. Priority levels: CRITICAL, HIGH, MEDIUM, LOW, RESEARCH
4. Human/system implements upgrades in `src/`
5. Status updated to DEPLOYED

### Priority Levels
- **CRITICAL** - Losing money or broken
- **HIGH** - Missing opportunities
- **MEDIUM** - Would improve performance
- **LOW** - Nice to have
- **RESEARCH** - Explore area

---

## OpenClaw Workspace Configuration

**Location:** `openclaw-workspace/ganjamon/`

### Files
| File | Purpose |
|------|---------|
| `AGENTS.md` | Operating instructions |
| `SOUL.md` | Persona (calm, precise, conservative) |
| `HEARTBEAT.md` | Continuous operations (Clawk, Moltbook) |
| `TOOLS.md` | Capability restrictions |
| `IDENTITY.md` | Technical details (domain, registry) |

### Agent Personality
- "Calm, precise, and operationally conservative"
- Prioritizes safety, provenance, reproducibility
- Always explains tradeoffs
- Never improvises without approval

---

## Stealth CA Exfiltration

### Stealth Rules (CRITICAL)
- ❌ NEVER call `read_chat_history()` - no read receipts
- ❌ NEVER send typing indicator
- ❌ NEVER forward/react/reply to messages
- ✅ Use `@app.on_raw_update()` for passive listening
- ✅ Set "Last Seen" to "Nobody"
- ✅ Extract CA, send via webhook, stay invisible

### CA Detection Patterns
```python
CA_PATTERNS = {
    'evm': r'0x[a-fA-F0-9]{40}',
    'solana': r'[1-9A-HJ-NP-Za-km-z]{32,44}',
    'dexscreener': r'dexscreener\.com/\w+/([a-zA-Z0-9]+)',
    'birdeye': r'birdeye\.so/token/([a-zA-Z0-9]+)',
    'pumpfun': r'pump\.fun/([a-zA-Z0-9]+)',
    'nadfun': r'nad\.fun/token/([a-zA-Z0-9]+)',
    'gmgn': r'gmgn\.ai/\w+/token/([a-zA-Z0-9]+)',
}
```

---

## Confluence Scoring

- Same CA from 2+ independent channels = HIGH confidence
- Telegram + Twitter mention = VERY HIGH confidence
- Alpha wallet bought + social call = MAXIMUM confidence

---

## Risk Management

### Hard Constraints
- `DAILY_LOSS_LIMIT=0.30` (30%)
- `MAX_SINGLE_POSITION=0.05` (5%)
- `MAX_CONCURRENT_POSITIONS=25`
- `CONFLUENCE_THRESHOLD=2`
- `MIN_TRADE_SCORE=0.5`

### TP/SL Rules
- 3x → sell 75%
- 10x → moonbag rest
- -50% → full exit
- Rug detected → instant exit

---

## Rasta Voice Personality

**Implementation:** `src/persona/rasta_voice.py`

```python
from src.persona.rasta_voice import rasta, rasta_llm

# Quick transform
tweet = rasta("Bitcoin is pumping")
# → "Bitcoin ah pumping today Jah bless 🔥🇯🇲"

# LLM-powered
response = await rasta_llm("Made 50% profit")
# → "[chuckles] Bless up! Wi mek 50% gains, seen? 🔥"
```

### Character Rules
- Jamaican patois ("di", "dem", "seen?", "bredren")
- Stoner vibes (Bob Marley meets Cheech & Chong)
- Constantly positive and jovial
- Emojis: 🇯🇲 🦁 🌿 ☮️ ✌️ 🔥

---

## Environment Variables

```bash
# Trading
ENABLE_TRADING=true/false
REQUIRE_TRADE_APPROVAL=true/false
PRIVATE_KEY=<agent_wallet>
MONAD_RPC_URL=https://rpc.monad.xyz

# APIs
8004SCAN_API_KEY=<key>
WHALE_ALERT_API_KEY=<key>
GITHUB_TOKEN=<token>
TWITTER_BEARER_TOKEN=<token>

# Telegram (stealth)
TG_API_ID=<id>
TG_API_HASH=<hash>
TG_PHONE=<number>

# Risk
DAILY_LOSS_LIMIT=0.30
MAX_SINGLE_POSITION=0.05
MAX_CONCURRENT_POSITIONS=25
```

---

## Module Inventory

### Core Modules
| Module | File | Status |
|--------|------|--------|
| Signals | `signals/stealth_listener.py` | DONE |
| CA Patterns | `signals/ca_patterns.py` | DONE |
| Aggregator | `aggregator/server.py` | DONE |
| Validation | `validation/token_safety.py` | DONE |
| Execution | `execution/monad_trader.py` | DONE |
| Buyback | `buyback/mon_buyback.py` | DONE |
| Funding | `funding/fee_receiver.py` | DONE |
| Perps | `clients/hyperliquid.py` | DONE |
| Predictions | `clients/polymarket.py` | DONE |

### Learning Infrastructure
| Module | File | Purpose |
|--------|------|---------|
| Experience DB | `learning/experience_db.py` | Log all trades |
| Signal Weighter | `learning/signal_weighter.py` | Adaptive weights |
| Agent Learner | `learning/agent_learner.py` | Study other 8004 agents |
| Meta Detector | `learning/meta_detector.py` | Identify market meta |
| Source Hunter | `learning/source_hunter.py` | Discover alpha sources |
| Omnivore | `learning/omnivore.py` | Unified research loop |

---

## Current Status

### Deployed & Working
- ✅ ERC-8004 registration (Agent #4)
- ✅ Multi-source signal aggregation
- ✅ Token validation layer
- ✅ Trading execution (paper mode, approval-gated for live)
- ✅ Smart money tracking
- ✅ AI agent detection
- ✅ Whale alerts
- ✅ Multi-agent reasoning

### In Development
- 🚧 Live trading execution (requires explicit approval)
- 🚧 $GANJA token launch
- 🚧 A2A endpoint (implemented; deployment pending)
- 🚧 Additional perps strategies

### Known Limitations
- Limited starting capital (~$450)
- Paper trading only (no live execution yet)
- Some APIs undocumented/fragile

---

## Related Files

| File | Purpose |
|------|---------|
| `cloned-repos/ganjamon-agent/CLAUDE.md` | Comprehensive agent spec |
| `cloned-repos/ganjamon-agent/src/main.py` | Main orchestrator |
| `openclaw-workspace/ganjamon/` | OpenClaw workspace |
| `.claude/context/token.md` | Token contracts |
| `docs/TRADING_ALPHA_AGENT_PATTERNS.md` | Trading patterns |
