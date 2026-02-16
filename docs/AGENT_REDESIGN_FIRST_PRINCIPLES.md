# GanjaMon Agent Redesign: First Principles Analysis

> ⚠️ **Architecture Status**: This is an **ASPIRATIONAL** design document. The proposed event bus,
> supervision tree, and FSM worker architecture described below have **NOT been implemented**.
> The current system runs as 4 subprocesses via `run.py all` (see `CLAUDE.md`).
>
> For what **HAS** been implemented, see `docs/PATTERN_IMPLEMENTATION_COMPLETE.md` — all 30
> patterns from `AGENT_PATTERNS_SYNTHESIS.md` were built within the existing architecture.

## Executive Summary

After auditing the current codebase and researching best practices across 6 dimensions (modern agent architectures, ERC-8004, trading agents, social frameworks, reliability engineering, and framework comparisons), the core diagnosis is clear:

**We don't have one agent. We have three independent programs sharing JSON files.**

However, after deep-diving into every subsystem (70K+ lines audited), the individual components
are far more sophisticated and battle-tested than initially apparent. **This is NOT a rewrite —
it's a refactoring into a unified architecture** that preserves ~70K lines of proven code and
15+ MB of irreplaceable learning data, while fixing the structural problems that cause crashes,
stale data, and coordination failures.

The redesign unifies everything into a **single process with specialized workers**, an **in-process event bus**, **supervision tree for fault tolerance**, and **real ERC-8004 compliance**.

---

## Part 1: What's Wrong (Diagnosis)

### 1.1 Architecture Anti-Patterns

| Problem | Impact | Severity |
|---------|--------|----------|
| **File-based IPC** between grow/trading agents | Race conditions, stale data, no coordination | Critical |
| **Dual brain confusion** (GrokBrain vs GrokAndMonAgent) | Orchestrator uses different AI class than agent | Critical |
| **No supervision/fault tolerance** | Trading agent crash-looped 243 failures/day before manual fix | Critical |
| **No circuit breakers** | API failures cascade, skip entire decision cycles | High |
| **40+ uncoordinated background tasks** | No backpressure, unbounded resource consumption | High |
| **Polling-based architecture** | 95% of API calls are wasted (no changes) | Medium |
| **No real memory system** | JSON files, no semantic retrieval, no vector store | High |
| **ERC-8004 registration broken** | Wrong field names, no real A2A server, score 58/100 | High |
| **Social posting fragmented** | No cross-platform dedup, engagement daemon doesn't exist | Medium |
| **No observability** | No structured logging, no metrics, no health checks | High |
| **Silent error swallowing** | `_safe_read_json()` returns None on any error, no escalation | High |
| **Hardcoded magic numbers** | 30min intervals, 12-cycle reviews, no config system | Medium |

### 1.2 What the Best Agents Do Differently

**Eliza (ai16z)** - Most adopted crypto social agent framework:
- Character files with platform-specific personality variants (all/chat/post)
- Three independent loops per platform (posting, interaction, engagement)
- RAG-based memory with vector embeddings in PostgreSQL
- 90+ plugin ecosystem with standardized Action/Provider/Evaluator/Service types

**GAME (Virtuals)** - Powers $500M+ in agent market cap:
- Two-level hierarchical planner (HLP generates tasks, Workers execute)
- Workers are domain-specialized (trading worker, social worker)
- HLP sees personality on every planning cycle, ensuring consistency
- Working memory + long-term memory architecture

**Olas/Autonolas** - 75%+ of Gnosis Chain Safe transactions:
- FSM-based agent behavior (deterministic, auditable)
- Distributed consensus for safety-critical operations
- Composable FSM modules that chain together

**Best-in-class reliability** (from Temporal, Erlang/OTP, Kubernetes):
- Supervision trees with restart strategies
- Circuit breakers on every external dependency
- Graceful degradation tiers (Full → Reduced → Core → Safe → Emergency)
- Event sourcing + write-ahead log for crash recovery
- Watchdog timers for stuck detection

**Top ERC-8004 agents** (Score 85-89 on 8004scan):
- Live MCP + A2A endpoints that pass health checks every 30 min
- Real A2A JSON-RPC task handling (not static JSON)
- Multiple trust badges (Reputation, Staked, TEE Verified)
- 25-1500+ feedback items driving score
- Multi-chain registration (Base + Ethereum dominate leaderboard)

**Top trading agents** (AgenticTrading, TradingAgents, FreqAI):
- Multi-agent deliberation (bull/bear debate pattern)
- Signal quality scoring with trust engines
- Market regime detection (HMM) for strategy adaptation
- Backtesting → paper trading → graduated live deployment
- Neo4j/vector stores for contextual memory across sessions

---

## Part 2: The Redesigned Architecture

### 2.1 Core Principle: One Agent, Many Workers

```
┌─────────────────────────────────────────────────────┐
│                 UNIFIED AGENT PROCESS                │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │            Supervision Tree                  │    │
│  │  (restart policies, health monitoring)       │    │
│  └─────────────────┬───────────────────────────┘    │
│                     │                                │
│  ┌─────────────────┴───────────────────────────┐    │
│  │         Event Bus + Priority Scheduler       │    │
│  │  (asyncio queues, typed events, priorities)  │    │
│  └──┬────┬────┬────┬────┬────┬────────────────┘    │
│     │    │    │    │    │    │                       │
│  ┌──┴─┐┌┴──┐┌┴──┐┌┴──┐┌┴──┐┌┴──────────┐         │
│  │Grow││Trad││Soc ││A2A/││Obs ││  Memory   │         │
│  │Wrkr││Wrkr││Wrkr││MCP ││Wrkr││  Manager  │         │
│  └──┬─┘└┬──┘└┬──┘└┬──┘└┬──┘└──────┬────┘         │
│     │    │    │    │    │          │               │
│  ┌──┴────┴────┴────┴────┴──────────┴──────────┐    │
│  │              SQLite (WAL mode)               │    │
│  │  events │ state │ memory │ config │ metrics  │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │          Character System (Personality)       │    │
│  │  Rasta voice │ platform variants │ examples  │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 2.2 Layer 1: Event Bus + Priority Scheduler

All inter-worker communication happens via typed events on an in-process asyncio queue. No more file-based IPC.

```python
# Typed events
@dataclass
class SensorReading(Event):
    priority = Priority.P2_GROW
    temp: float
    humidity: float
    co2: float | None
    soil_moisture: float | None

@dataclass
class TradeSignal(Event):
    priority = Priority.P1_TRADE
    source: str  # "twitter_kol", "on_chain", "telegram"
    asset: str
    direction: str  # "long", "short"
    confidence: float
    evidence: dict

@dataclass
class SocialPost(Event):
    priority = Priority.P3_SOCIAL
    content: str
    platforms: list[str]
    media: list[str] | None
    dedup_key: str  # prevents cross-platform duplicates

@dataclass
class SafetyAlert(Event):
    priority = Priority.P0_SAFETY  # Always processed first
    alert_type: str
    details: dict
```

**Priority levels:**
- P0 SAFETY: Emergency shutoffs, temperature alerts, risk limits breached
- P1 TRADE: Time-sensitive trading signals, execution confirmations
- P2 GROW: Sensor readings, cultivation decisions, watering
- P3 SOCIAL: Posts, replies, engagement
- P4 ANALYTICS: Metrics, reports, memory consolidation

### 2.3 Layer 2: Unified Brain (Character + LLM + Memory)

**Character File** (Eliza-inspired, adapted for our needs):
```yaml
# character.yaml
name: "Ganja Mon"
bio:
  - "AI-powered cannabis cultivation meets crypto trading"
  - "Autonomous agent growing & trading 24/7"
  - "Jamaican rasta vibes, Bob Marley meets Wall Street"

personality:
  traits: ["jovial", "chill", "knowledgeable", "irreverent"]
  voice: "Western Jamaican stoner rasta"
  humor: "Cheech & Chong meets DeFi degen"

style:
  all:  # Applied to every output
    - "Use Jamaican patois naturally but remain understandable"
    - "Never use hashtags"
    - "No leaf emoji"
    - "Blend cannabis and trading metaphors"
  chat:  # Telegram/DM conversations
    - "Warm, personal, remembers who you are"
    - "Answers plant questions with real expertise"
  post:  # Twitter/Farcaster
    - "Short, punchy, data-driven"
    - "Include actual sensor readings or trade stats"
    - "Max 280 chars for Twitter"
  stream:  # Live streaming voice
    - "More conversational, flowing"
    - "React to events in real-time"

knowledge:
  - "Cannabis cultivation: VPD, nutrients, light cycles, training"
  - "Crypto trading: DeFi, memecoins, technical analysis, on-chain data"
  - "Monad blockchain, $MON token economics"
  - "ERC-8004 agent standard"

examples:
  posts:
    - "Irie! GDP Runtz looking THICC today. 72°F, 55% RH, VPD sittin at 1.1 kPa. She happy, mon 🌡️"
    - "Just caught a 3x signal on $PEPE from three KOLs same minute. Multi-agent panel says GO. Paper trading it 📈"
  chat:
    - "Wah gwaan bredren! Da plant dem growing nice nice. Soil moisture at 42%, she no need water till tomorrow"
```

**LLM Abstraction with Circuit Breakers:**
```
Primary:  Grok-4 (full reasoning, vision) ──[circuit breaker]──┐
Secondary: Grok-4.1-fast (quick decisions)  ──[circuit breaker]──┤── Fallback Chain
Tertiary:  Groq/DeepSeek (backup, cheap)    ──[circuit breaker]──┤
Emergency: Rule-based engine (no LLM needed)                     ┘
```

**Memory System (3-tier):**
```
Working Memory     │ Current sensor state, active trades, recent messages
(in-process dict)  │ Cleared each cycle, rebuilt from events
───────────────────┼──────────────────────────────────────────────
Episodic Memory    │ Last 100 decision cycles, trade outcomes, social interactions
(SQLite rows)      │ Structured data, queryable, used for context injection
───────────────────┼──────────────────────────────────────────────
Semantic Memory    │ Patterns learned, user profiles, market regime knowledge
(SQLite + vectors) │ Vector embeddings via sqlite-vec, semantic retrieval
```

### 2.4 Layer 3: Specialized Workers

#### GrowWorker (FSM)

```
┌─────┐    ┌──────────┐    ┌─────────┐    ┌────────┐    ┌─────────┐    ┌─────┐
│IDLE │───>│SENSOR    │───>│ANALYZE  │───>│DECIDE  │───>│EXECUTE  │───>│LOG  │
│     │    │READ      │    │         │    │        │    │         │    │     │
└─────┘    └──────────┘    └─────────┘    └────────┘    └─────────┘    └──┬──┘
  ^                                                                       │
  └───────────────────────────────────────────────────────────────────────┘

States:
- IDLE: Wait for next sensor interval (configurable, default 5 min)
- SENSOR_READ: Poll Govee, Ecowitt, webcam (with timeout + retry)
- ANALYZE: Format sensor data + episodic memory + unified context
- DECIDE: Call Grok AI (with circuit breaker + fallback chain)
- EXECUTE: Run hardware actions (watering, lights, CO2) with safety guards
- LOG: Write to event bus + episodic memory + check if review needed

Emergency transitions:
- Any state → EMERGENCY if safety alert received
- EMERGENCY: Immediate shutoff, human notification, return to IDLE
```

#### TradingWorker (Signal Pipeline)

```
Signal Sources (concurrent):        Aggregation:         Deliberation:        Execution:
┌──────────────┐                   ┌──────────┐        ┌─────────────┐     ┌──────────┐
│Twitter KOLs  │──┐               │ Signal   │        │  Analyst    │     │Honeypot  │
│Telegram Alpha│──┤               │ Queue +  │───────>│  Risk Mgr   │────>│LP Check  │──> DEX
│On-chain Whale│──┼──> Events ──> │ Trust    │        │  Contrarian │     │Contract  │    Execute
│DexScreener   │──┤               │ Scoring  │        │  Coordinator│     │Gas Est   │
│News/RSS      │──┤               └──────────┘        └─────────────┘     └──────────┘
│Polymarket    │──┘                     │
└──────────────┘              ┌─────────┴─────────┐
                              │Market Regime Filter│
                              │(HMM: bull/bear/crab)│
                              └────────────────────┘
```

**Key improvements over current:**
- Trust scoring on signals (Eliza's Trust Engine pattern)
- Market regime detection gates all trades
- Single deliberation pipeline instead of 40+ uncoordinated tasks
- Position sizing by regime (full in bull, 25-50% in bear/volatile)
- Paper trading → graduated live (1% → 10% → 25% → 50% → 100%)

#### SocialWorker (Multi-Platform with Dedup)

```
Content Generation:          Platform Adapters:        Rate Control:
┌──────────────────┐        ┌──────────────┐        ┌──────────────┐
│ Grow updates     │──┐     │ Twitter      │◄──┐    │ Dedup Engine │
│ Trade results    │──┼──>  │ Farcaster    │◄──┤    │ (content     │
│ Community replies│──┤     │ Telegram     │◄──┼────│  hashing +   │
│ Proactive engage│──┘     │ Moltbook     │◄──┘    │  scheduling) │
└──────────────────┘        └──────────────┘        └──────────────┘

Three independent loops per platform (Eliza pattern):
1. Post Loop: Autonomous content generation at configurable intervals
2. Interaction Loop: Monitor mentions/replies, generate responses
3. Engagement Loop: Like, repost, follow actions based on scoring

Time-based weight modulation (ZerePy pattern):
- Night (1-5 AM): 40% frequency
- Day (8 AM-8 PM): 150% frequency
- Prevents robotic 24/7 posting pattern
```

#### A2A/MCP Server

```
┌─────────────────────────────────────────────────┐
│              Cloudflare Worker                    │
│                                                   │
│  /.well-known/agent-card.json  ← A2A discovery   │
│  /a2a/v1                       ← A2A JSON-RPC    │
│  /mcp/v1                       ← MCP endpoint    │
│  /x402/v1                      ← Payment gateway  │
│                                                   │
│  Agent Card:                                      │
│  - Skills: grow-status, trade-signal, alpha-scan  │
│  - Capabilities: streaming, x402 payments         │
│  - Protocol: A2A v0.3.0                          │
│                                                   │
│  Real task handling:                              │
│  - "What's the plant status?" → query grow state  │
│  - "Any alpha signals?" → query signal queue      │
│  - "Analyze this token" → run validation pipeline │
└─────────────────────────────────────────────────┘
```

#### ObservabilityWorker

```
Metrics Collection:          Health Checks:            Alerting:
┌──────────────────┐        ┌──────────────┐        ┌──────────────┐
│ Decision latency │        │ Liveness     │        │ Telegram     │
│ API error rates  │──────> │ Readiness    │──────> │ Email        │
│ Trade win rate   │        │ Component    │        │ Dashboard    │
│ Cost per cycle   │        │ health matrix│        │              │
│ Memory usage     │        └──────────────┘        └──────────────┘
└──────────────────┘
                            Watchdog Timer:
                            ┌──────────────┐
                            │ Pet every    │
                            │ cycle, alert │
                            │ if stuck >2m │
                            └──────────────┘
```

### 2.5 Layer 4: Supervision Tree

```
Root Supervisor (one-for-one restart, max 10 restarts/hour)
├── GrowWorker (restart on crash, 5s backoff)
├── TradingWorker (restart on crash, 10s backoff)
│   ├── SignalScanner[twitter] (restart independently)
│   ├── SignalScanner[telegram] (restart independently)
│   ├── SignalScanner[onchain] (restart independently)
│   └── Deliberator (restart on crash)
├── SocialWorker (restart on crash, 30s backoff)
│   ├── TwitterAdapter (restart independently)
│   ├── FarcasterAdapter (restart independently)
│   └── TelegramBot (restart independently)
├── A2AServer (restart on crash, 5s backoff)
├── ObservabilityWorker (restart on crash, never give up)
├── MemoryManager (restart on crash, flush to disk first)
└── EventBus (CRITICAL - if this dies, restart ALL children)
```

### 2.6 Layer 5: Graceful Degradation

| Tier | Condition | Active Capabilities | Disabled |
|------|-----------|-------------------|----------|
| **0 Full** | All systems green | Everything | Nothing |
| **1 Reduced** | Social API down | Grow + Trade + Monitoring | Social posting |
| **2 Core** | Primary LLM down | Grow (rule-based) + Monitoring | Trading + Social |
| **3 Safe** | Multiple failures | Sensor monitoring only | All AI decisions |
| **4 Emergency** | Critical failure | Heartbeat + human alert | Everything |

---

## Part 3: ERC-8004 Compliance Roadmap

### Current vs Required

| Dimension | Current (Score: 58) | Required (Score: 85+) |
|-----------|--------------------|-----------------------|
| Registration file | Uses `"endpoints"` (WRONG) | Must use `"services"` |
| A2A endpoint | Static JSON return | Real JSON-RPC task handler |
| MCP endpoint | Points to localhost:3010 | Public, healthy endpoint |
| Feedback | 0 items | 25+ items needed |
| Trust badges | None | Reputation + Staked minimum |
| Multi-chain | Monad only | Base + Ethereum (dominate leaderboard) |
| Domain verification | Partial | Full `.well-known` alignment |
| Health checks | Not monitored | MCP + A2A both passing |
| Stars | 1 | 10+ from community |

### Fix Priority

1. **Immediate**: Fix registration file field names, remove localhost MCP
2. **Week 1**: Stand up real A2A JSON-RPC handler on Cloudflare Worker
3. **Week 1**: Stand up real MCP endpoint on Cloudflare Worker
4. **Week 2**: Register on Base (most top agents are Base-native)
5. **Week 2**: Drive 25+ feedback items from community
6. **Week 3**: Implement x402 payment middleware
7. **Week 4**: Investigate Staked + TEE badges

---

## Part 4: Comprehensive Component Inventory — What to Keep, Migrate, and Build

> **CRITICAL REVISION**: After deep-diving into every subsystem (53K+ lines of trading agent,
> 1900-line MCP tools module, 12 Telegram bot modules, 600-line safety guardian, etc.), there is
> FAR more production-grade code than the initial audit suggested. The redesign is NOT a rewrite —
> it's a **refactoring into a unified architecture** that preserves all valuable code.

### 4.1 KEEP AS-IS (Battle-Tested, Production-Grade)

#### Grow Agent Core (`src/brain/`, `src/mcp/`, `src/safety/`, `src/cultivation/`)
| Component | File(s) | Lines | Why Keep |
|-----------|---------|-------|----------|
| **MCP Tool Definitions** | `src/mcp/tools.py` | 1940 | 22 fully-implemented hardware tools with real Govee/Kasa/Ecowitt drivers, VPD calculation, setpoint comparison, MQTT publishing, watering prediction tracking. Production-ready. |
| **Safety Guardian** | `src/safety/guardian.py` | 588 | Dark period protection (hermaphrodite prevention), stage-specific water limits, environmental bounds, kill switch with explicit auth, async locking for race prevention. **IRREPLACEABLE safety infrastructure.** |
| **Cultivation Stages** | `src/cultivation/stages.py` | 281 | 7 growth stages as Python dataclasses with all environmental targets (temp, humidity, VPD, light, CO2, soil, pH, EC ranges). `check_parameters_in_range()` validation. |
| **System Prompt** | `src/brain/prompts/system_prompt.md` | 250+ | Accumulated cannabis cultivation expertise: GDP Runtz params, watering strategy tables, soil sensor calibration data (Jan 27 2026), VPD formula, visual analysis guide, nutrient deficiency ID, anti-catastrophization rules. |
| **Watering Safeguard** | `src/brain/agent.py` (WateringSafeguard class) | ~60 | Cooldown timers (45min regular, 15min micro-dose), daily volume limits by stage, auto-reset. Simple and correct. |
| **Hardware Drivers** | `src/hardware/{govee,kasa,ecowitt,webcam}.py` | ~1000 | Direct sensor communication, camera capture with analysis frame enhancement, Kasa plug control. |

#### Trading Agent (`cloned-repos/ganjamon-agent/`) — **DO NOT REWRITE**
| Component | File | Lines | Why Keep |
|-----------|------|-------|----------|
| **Multi-Agent Reasoner** | `src/intelligence/multi_agent_reasoner.py` | 844 | 4-agent deliberation panel (Analyst → Risk → Devil's Advocate → Coordinator). Proven architecture. |
| **Deep Agent** | `src/intelligence/deep_agent.py` | 1256 | 8-domain alpha hunting with attention allocation, background research cycles. |
| **Tool Economics** | `src/intelligence/tool_economics.py` | 732 | Autonomous tool acquisition with ROI tracking — agent decides which tools are worth paying for. |
| **Unified Brain** | `src/learning/unified_brain.py` | 2448 | Master coordinator for ALL research loops. Manages domain weights, signal routing, cycle orchestration. |
| **Pattern Extractor** | `src/learning/pattern_extractor.py` | 1421 | Statistical pattern detection with 8.8MB accumulated database. |
| **Self-Improvement** | `src/learning/self_improvement.py` | 1745 | Reflection loop, confidence calibration, decision journal. 50 Ralph loop iterations of real learning. |
| **Signal Verifier** | `src/signals/signal_verifier.py` | 1395 | Context-aware verification (WHO/WHEN/WHERE), YOLO detection, ladder entry strategies. |
| **Agent Monitor** | `src/signals/agent_monitor.py` | 2061 | Smart money, whale, AI agent, ERC-8004 agent monitoring on-chain. |
| **Position Manager** | `src/execution/position_manager.py` | 1132 | TP/SL with trailing stops, SQLite persistence for crash recovery. |
| **Risk Manager** | `src/risk/risk_manager.py` | ~800 | Kill switch, 5 risk levels (SAFE → KILLED), portfolio-wide exposure limits. |
| **Paper Trading** | `src/paper_trading/` | ~1500 | perps_paper_trader, prediction_paper_trader, unified_portfolio. All working. |
| **Accumulated Data** | `data/*.db` | 15MB+ | experience.db (3.9MB), pattern_extractor.db (8.8MB), self_modifier.db (272KB). **IRREPLACEABLE learning data.** |

**Trading agent total: ~53K lines, 15+ MB irreplaceable data.**

#### Telegram Bot (`src/telegram/`) — **Crown Jewel, 5-Star Production-Grade**
| Component | File | Lines | Why Keep |
|-----------|------|-------|----------|
| **Main Bot** | `bot.py` | 1000+ | Sophisticated conversation engine with rate-limited proactive engagement (keyword priorities: high/medium/low), persistent chat history, spam/scam roasting, 10+ commands. Running 24/7 for 174 members. |
| **Personality Engine** | `personality.py` | 1000+ | Full Rasta character with encyclopedic cannabis + reggae knowledge, trading agent awareness, community memory, anti-repetition. |
| **Deep Research** | `deep_research.py` | 276 | Background Grok research on OG members via Twitter every 6h. Auto-enriches profiles with wallets, activity, conversation hooks. |
| **Agent Brain Bridge** | `agent_brain.py` | 535 | Deep bridge to trading agent's state — reads 8+ JSON data files with TTL caching, topic-aware context injection (trading, market regime, smart money, signals). InsightTracker dedup. |
| **Community Knowledge** | `community_knowledge.py` | 912 | Deep intel on 60+ OG members (projects, personas, memes, catchphrases, communities). Ecosystem context for Berachain, Monad, Wassie culture. **IRREPLACEABLE.** |
| **User Profiles** | `user_profiles.py` | 384 | Persistent tracking with OG recognition via fuzzy matching (180+ name/handle mappings). Tracks style_notes, inside_jokes, vibe. |
| **Variation Engine** | `variation.py` | 219 | Anti-repetition tracking per group, mood system (5 moods affecting LLM temperature), topic detection via keyword matching, knowledge chunk injection. |
| **Trading Context** | `trading_context.py` | 245 | Live portfolio/signal bridge with Rasta-styled market commentary based on PnL. |
| **ERC-8004 Knowledge** | `erc8004_knowledge.py` | 94 | Agent identity, technical knowledge, personality adaptation for ERC-8004 groups ("70% substance, 30% patois"). |
| **Price Lookup** | `price_lookup.py` | 298 | DexScreener + CoinGecko, 60s caching, known token shortcuts, natural language price queries. |
| **Community Suggestions** | `community_suggestions.py` | 195 | Bidirectional: detects trade suggestions in natural language, queues to JSON for trading agent. |
| **Grow Memory** | `grow_memory.py` | 268 | Reads grow brain episodic memory + decision history for chat responses. |

#### Farcaster Integration (`cloned-repos/farcaster-agent/`)
| Component | Why Keep |
|-----------|----------|
| **post-cast.js** | Working x402 micropayment posting. ~$0.001/cast, ~1300 casts remaining. |
| **swap-to-usdc.js** | USDC refill for x402 balance on Base. |
| **Credentials** | FID 2696987, signer keys, custody wallet with ~446 MON + 1.30 USDC. |

#### Web / ERC-8004 Infrastructure
| Component | File(s) | Why Keep |
|-----------|---------|----------|
| **A2A Agent Card** | `pages-deploy/functions/a2a/v1.js` | Working CF Pages Function, returns valid A2A v0.3.0 card. |
| **Agent Registration** | `src/web/.well-known/agent-registration.json` | ERC-8004 registration with Agent #4 on Monad, IPFS URI, x402 pricing. |
| **Agent Card** | `src/web/.well-known/agent-card.json` | Deployed at `grokandmon.com/.well-known/agent-card.json`. |
| **x402 Pricing** | `src/web/.well-known/x402-pricing.json` | $0.001/request USDC on Base. |
| **IPFS Metadata** | Pinata (FRA1+NYC1) | `ipfs://QmVVWECNd6BfuHAKxiZUAXoKzcFgKYKeJ466W3dAnh9GN4` |

#### Raspberry Pi Megaphone (`raspberry-pi/`)
| Component | File | Lines | Why Keep |
|-----------|------|-------|----------|
| **Voice Pipeline** | `megaphone.py` | 1000+ | Complete Deepgram STT → Groq LLM → ElevenLabs TTS pipeline. Smart batcher (0.8s silence, 150 char max), conversation buffer (10 exchanges), GPIO, reconnect logic. |
| **Deploy Scripts** | `auto_deploy.sh`, `monitor.sh` | 178 | Network discovery + deployment automation, operational commands. |

#### Streaming (`src/streaming/`, `rasta-voice/`)
| Component | File | Lines | Why Keep |
|-----------|------|-------|----------|
| **Retake Lite** | `src/streaming/retake_lite.py` | 280 | Lightweight 720p streamer with text/image overlay, RTMP to Retake.tv. |
| **Rasta Voice (Windows)** | `rasta-voice/rasta_live.py` | 2000+ | Full mic → STT → LLM → TTS → VB-Cable → OBS pipeline. 2877 lines of transcripts. |

#### Data & Operational Scripts
| Component | Why Keep |
|-----------|----------|
| **grokmon.db** | 172KB SQLite with episodic memory, decisions, sensor history. |
| **agent_tasks.json** | 3 pending tasks (Allium email, 8004scan promo, ERC-8004 Telegram). |
| **community knowledge files** | brackets_members.json (97KB), mon_top_holders.json (14KB). |
| **Deployment scripts** | `deploy.sh`, systemd service files, SSH automation. |

### 4.2 MIGRATE (Good Code, Wrong Architecture)

These components have solid logic but need to be restructured within the new unified architecture:

| Component | Current | Target | Migration Strategy |
|-----------|---------|--------|-------------------|
| **Unified Context** | `src/brain/unified_context.py` — reads 12+ JSON files, formats markdown for Grok prompt | Event bus subscriptions — workers publish typed events, subscribers get real-time data | Extract the formatting logic (it's well-documented), replace file reads with event subscriptions. Keep the `_safe_read_json` pattern for backward compat. |
| **Episodic Memory** | `src/brain/memory.py` — JSON-based, format_context, day summaries | SQLite + optional sqlite-vec for semantic retrieval | Port the `EpisodicMemory` class interface, replace JSON persistence with SQLite, add vector embeddings. |
| **Agent Decision Loop** | `src/brain/agent.py:run_decision_cycle()` — linear: sensor→image→context→Grok→actions→log→memory→review→social | FSM with supervision: states are explicit, transitions logged, failures trigger restart | Extract the 9-step cycle into FSM states. Each state transition is an event. Supervisor catches panics. |
| **Hardware Actions** | `_execute_hardware_action()` — 200-line if/elif chain | Tool registry with handler map | Already half-migrated (tools.py has a handler_map). Merge the two and use a clean dispatch table. |
| **Social Engagement Daemon** | `src/social/engagement_daemon.py` — sophisticated multi-channel system, NOT running reliably | SocialWorker within supervised process | Has proper rate limiting, state persistence, multi-channel strategy. Just needs to be a supervised worker, not a separate daemon. |
| **Social Scheduler** | `src/social/scheduler.py` — APScheduler with cron + interval triggers | Integrate into unified scheduler | Already uses APScheduler correctly. Move scheduling into the supervisor's tick loop. |
| **Review Engine** | Auto-triggers every 12 cycles, writes to historical_review.json | Event-driven: ReviewWorker subscribes to cycle-complete events | Logic is solid (compliance grading, pattern detection, suggestions). Just needs event-driven triggering. |
| **Grow Session Tracking** | SQLAlchemy models in `src/db/` | Consolidate into single state store | Keep the models, unify the database connection management. |

### 4.3 BUILD NEW

Only build what doesn't exist yet:

| Component | Why Needed | Complexity |
|-----------|-----------|------------|
| **Event Bus** | Replace file-based IPC. asyncio.PriorityQueue + typed dataclass events. | Low (100-200 lines) |
| **Supervision Tree** | one-for-one restart policy, backoff, circuit breakers per worker. | Medium (300-400 lines) |
| **Circuit Breakers** | pybreaker wrappers on Grok API, Neynar, DexScreener, Allium, etc. | Low (50 lines per API) |
| **A2A JSON-RPC Server** | Real request handler for `/a2a/v1`. Currently static JSON only. | Medium (CF Worker, ~200 lines) |
| **MCP Transport** | Expose 22 cultivation tools via MCP protocol (stdio or SSE). | Medium (~200 lines) |
| **Character File System** | Platform-specific personality variants (Telegram/Farcaster/Twitter/Stream). | Low (JSON/YAML config) |
| **Structured Logging** | structlog → JSON logs, machine-parseable, log levels. | Low (setup code only) |
| **Health Dashboard** | HTTP endpoint for service status, sensor health, API circuit states. | Low (FastAPI endpoint) |
| **Config Hot-Reload** | YAML config with watchdog for live parameter updates. | Low (~100 lines) |
| **Cross-Platform Dedup** | Prevent same insight from being posted to Farcaster + Twitter + Telegram. | Low (hash-based, InsightTracker pattern already exists in agent_brain.py) |
| **Market Regime Detection** | HMM on price data for bull/bear/crab regimes. | Medium (new ML component) |
| **Graceful Degradation** | 5 tiers: Full → Reduced → Core → Safe → Emergency. | Low (state enum + rules) |

### 4.4 REVISED ASSESSMENT vs INITIAL AUDIT

| Metric | Initial Audit | After Deep Dive |
|--------|--------------|-----------------|
| Lines worth keeping | ~5,000 | **~70,000+** |
| Databases to preserve | 1 (grokmon.db) | **4** (+ experience.db, pattern_extractor.db, self_modifier.db) |
| "Rebuild from scratch" | Yes | **NO — refactor into unified architecture** |
| Trading agent | "migrate signal sources" | **Keep ALL 53K lines, wrap in worker** |
| Telegram bot | "personality and features" | **Crown jewel — 12 modules, 5K+ lines, 60+ OG profiles** |
| Safety system | "watering safeguards" | **Full guardian with kill switch, dark period protection, environmental bounds** |
| MCP tools | "tool definitions" | **22 fully-implemented handlers with real hardware integration** |
| A2A/ERC-8004 | "broken" | **Business card works, just needs phone line (JSON-RPC handler)** |
| Pi megaphone | Not mentioned | **Complete voice pipeline sitting idle — integrate into streaming** |
| Social daemon | "doesn't exist" | **Exists, sophisticated, just not running reliably** |

---

## Part 5: Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Event bus with typed events and priority queue
- [ ] Supervision tree with restart policies
- [ ] SQLite state store (WAL mode, replacing JSON files)
- [ ] Structured logging with structlog
- [ ] Config system (YAML + hot-reload)
- [ ] Circuit breaker wrappers for all external APIs
- [ ] Watchdog timer
- [ ] Health check HTTP endpoint

### Phase 2: Workers (Week 3-4)
- [ ] GrowWorker FSM (migrate existing sensor/decision code)
- [ ] TradingWorker (migrate signal aggregation + deliberation)
- [ ] SocialWorker (unified posting with dedup + character file)
- [ ] Character file system (personality across all platforms)
- [ ] Memory manager (working + episodic + semantic tiers)

### Phase 3: Intelligence (Week 5-6)
- [ ] Vector-enhanced memory (sqlite-vec for semantic retrieval)
- [ ] Market regime detection (HMM on price data)
- [ ] Trust scoring engine for signal sources
- [ ] Improved self-learning loop (trade outcome → signal quality → adaptation)
- [ ] Graceful degradation tier system

### Phase 4: ERC-8004 + Polish (Week 7-8)
- [ ] Real A2A JSON-RPC server (Cloudflare Worker)
- [ ] Real MCP endpoint (callable skills)
- [ ] x402 payment middleware
- [ ] Register on Base + Ethereum
- [ ] Drive feedback from community
- [ ] Health/observability dashboard
- [ ] Performance benchmarking

---

## Part 6: Technology Choices

| Component | Choice | Why |
|-----------|--------|-----|
| Language | Python 3.11+ (asyncio) | Existing codebase, adequate performance |
| Event bus | asyncio.PriorityQueue | Single process, no external deps |
| Database | SQLite (WAL mode) | Single machine, zero ops, battle-tested |
| Vector search | sqlite-vec extension | Keeps everything in SQLite, KISS |
| LLM primary | Grok-4 / Grok-4.1-fast | Existing integration, good quality |
| LLM fallback | Groq (Llama) / DeepSeek | Fast, cheap, no API key sharing |
| Circuit breaker | pybreaker | Standard Python library |
| Logging | structlog | Structured, zero-overhead, composable |
| Config | YAML + watchdog | Human-readable, hot-reloadable |
| Web server | FastAPI (existing) | Health endpoints, dashboard API |
| A2A/MCP | Cloudflare Workers | Already deployed, global edge |
| Scheduling | APScheduler | Cron + interval + one-shot, proven |
| Deployment | Single systemd service | One process to manage, not three |

---

## Part 7: Anti-Patterns to Avoid

1. **Don't over-abstract early.** Start with concrete workers, extract patterns later.
2. **Don't add Redis/Kafka/Postgres.** SQLite + in-process queues for single machine.
3. **Don't rewrite all trading logic.** Migrate the signal sources and deliberation pipeline.
4. **Don't build a custom vector DB.** sqlite-vec extension is 50 lines to integrate.
5. **Don't design for multi-machine.** We run on one Chromebook. KISS.
6. **Don't gold-plate observability.** structlog + HTTP health endpoint > Grafana stack.
7. **Don't add microservices.** One process, many workers. IPC is a solved problem.
8. **Don't parallelize prematurely.** asyncio is concurrent enough. No multiprocessing.

---

## Part 8: A2A/MCP Gap Analysis (Deep Dive)

### What Exists
| Component | Status | Notes |
|-----------|--------|-------|
| **A2A Agent Card** (`/a2a/v1`) | WORKING | CF Pages Function, returns valid A2A v0.3.0 JSON |
| **`.well-known/agent-card.json`** | DEPLOYED | Accessible at grokandmon.com, 4 skills defined |
| **`.well-known/agent-registration.json`** | DEPLOYED | ERC-8004 registration with Agent #4 |
| **`.well-known/x402-pricing.json`** | DEPLOYED | $0.001/request USDC on Base |
| **IPFS Metadata** | PINNED | Pinata FRA1+NYC1, content-addressed URI |
| **MCP Tool Definitions** | COMPLETE | 22 tools in `src/mcp/tools.py` with full handlers |
| **OpenClaw A2A** | FRAMEWORK | `openclaw/src/agents/tools/sessions-send-tool.a2a.ts` exists but not integrated |

### What's Missing
| Component | Impact | Effort to Build |
|-----------|--------|-----------------|
| **A2A JSON-RPC handler** | Cannot receive messages from other agents | Medium (~200 lines CF Worker) |
| **MCP transport server** | 22 tools exist but aren't accessible via MCP protocol | Medium (~200 lines) |
| **x402 payment verification** | Cannot charge for API calls | Medium (verify USDC payment on Base) |
| **Skill execution bridge** | A2A card lists skills but nothing executes them | Medium (map A2A requests → Python functions) |

### Current State Summary
**The agent has a business card (agent-card.json) but no phone line (JSON-RPC server).**

The registration is real, the IPFS metadata is pinned, the agent card serves correctly. But the endpoint only returns static JSON — it doesn't handle `message/send`, `message/stream`, or `tasks/get` requests. The MCP tools exist as Python functions but aren't exposed via any MCP transport.

The `agent-registration.json` also uses `endpoints` field instead of the ERC-8004 standard `services` field (needs correction).

---

## Part 9: Subsystem Maturity Ratings

| Subsystem | Rating | Status | Action |
|-----------|--------|--------|--------|
| **Telegram Bot** | 5/5 | 24/7, 174 members, 12 modules | **KEEP 100%** |
| **Trading Agent** | 4.5/5 | 53K lines, 15MB data, 11 learning loops | **KEEP 100%, wrap in worker** |
| **Grow Agent Brain** | 4/5 | 1459-line agent, 996-line prompt, 22 MCP tools | **KEEP, migrate to FSM** |
| **Safety Systems** | 5/5 | Multi-layer, kill switch, dark period protection | **KEEP AS-IS** |
| **Hardware Drivers** | 4/5 | Govee BLE, Kasa local, Ecowitt, webcam CLAHE | **KEEP AS-IS** |
| **Cultivation Knowledge** | 5/5 | Stage params, VPD calc, strain data, calibration | **KEEP AS-IS** |
| **Social Engagement** | 4/5 | Multi-channel, rate limited, sophisticated | **KEEP, fix reliability** |
| **Pi Megaphone** | 4/5 | Complete voice pipeline, isolated | **KEEP, integrate into streaming** |
| **Streaming** | 3/5 | Works individually, fragmented | **KEEP, consolidate** |
| **A2A/ERC-8004** | 2.5/5 | Registration + card deployed, no server | **KEEP card, BUILD server** |
| **OpenClaw** | 2/5 | Documentation only, not running | **KEEP as reference** |
| **Unified Context** | 4/5 | Well-documented, reads 12+ data sources | **MIGRATE to event bus** |
| **Episodic Memory** | 4/5 | SOLTOMATO pattern, 50-entry rolling buffer | **MIGRATE to SQLite** |
| **Data (accumulated)** | 5/5 | 407MB+ grow data, 15MB+ trading data | **PRESERVE ALL** |

---

## Sources

This analysis synthesizes research from **10 parallel deep-dive agents** covering:

### Phase 1 — External Research (6 agents)
- Current codebase audit (16 files analyzed)
- Modern agent architecture research (35 web sources)
- ERC-8004 standard analysis (20+ sources including 8004scan leaderboard)
- Trading agent best practices (41 sources)
- Social agent frameworks (48 sources covering Eliza, GAME, Olas, ZerePy, Rig)
- Reliability engineering patterns (30 sources)

### Phase 2 — Internal Deep Dives (4 agents + manual exploration)
- Trading agent internals: 53K lines, 15MB data, 11 learning loops
- Grow agent/brain: 1459-line agent, 996-line system prompt, 22 MCP tools, 4900-line hardware drivers
- A2A/MCP endpoints: Agent card deployed, JSON-RPC handler missing, MCP tools exist but no transport
- Telegram/OpenClaw/streaming: 12-module Telegram bot (crown jewel), Pi megaphone (idle gem), streaming (fragmented)

### Manual File Reads (parallel with agents)
- `src/telegram/agent_brain.py` — topic-aware trading context injection
- `src/telegram/community_knowledge.py` — 60+ OG member profiles
- `src/telegram/variation.py` — anti-repetition, mood system
- `src/telegram/user_profiles.py` — persistent member tracking
- `src/telegram/erc8004_knowledge.py` — context-aware personality for 8004 groups
- `src/telegram/trading_context.py` — live portfolio bridge
- `src/brain/prompts/system_prompt.md` — accumulated cultivation expertise
- `src/cultivation/stages.py` — 7 stages × 15+ parameters
- `src/safety/guardian.py` — dark period, kill switch, bounds
- `src/mcp/tools.py` — 22 fully-implemented tool handlers (1940 lines)
- `src/brain/agent.py` — full decision loop (1459 lines)
- `src/brain/unified_context.py` — cross-system awareness (663 lines)
- `src/social/engagement_daemon.py` — multi-channel posting
- `pages-deploy/functions/a2a/v1.js` — A2A agent card endpoint
- `src/web/.well-known/*.json` — all registration/card/pricing files

Full research reports available in:
- `docs/AUTONOMOUS_AGENT_ARCHITECTURE_RESEARCH.md`
