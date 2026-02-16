# The Unified Rasta Mon — Complete Capability Map

**Updated:** 2026-02-11 (OpenClaw-First Architecture)
**Architecture:** One process, one heartbeat, one Mon. OpenClaw is the primary AI orchestrator.

---

## 1. System Overview

The Rasta Mon is ONE being — he meditates, grows di ganja, bends markets to his will, and brings di healing of di nations. Previously split across two separate services, everything now runs as a single unified process.

### Machines

| Machine | Role | Key Services |
|---------|------|-------------|
| **Windows Laptop** | Dev, streaming, voice pipeline | Rasta TTS, OBS, browser automation |
| **Chromebook Server** | Plant ops, trading, social, bot | grokmon (unified), ganja-mon-bot |
| **Raspberry Pi Zero 2 W** | Megaphone/audio | Remote audio output |

### Services on Chromebook

| Service | Status | Purpose |
|---------|--------|---------|
| `grokmon.service` | ENABLED | Unified agent: grow + trading + social + FastAPI |
| `ganja-mon-bot.service` | ENABLED | Telegram community bot (@MonGardenBot) |
| `retake-stream.service` | OPTIONAL | Retake.tv streaming |
| `ganjamon-agent.service` | **DISABLED** | Merged into grokmon |

### Entry Point

`python run.py all` launches 3 subprocesses:
1. **FastAPI Server** (HAL, :8000) — Web API + sensors + actuators + safety
2. **OpenClaw Gateway** (:18789) — Primary AI brain — heartbeat, skills, social, decisions
3. **GanjaMonAgent** — Trading domain (signals, execution, learning)

> **Note:** The legacy grow orchestrator and social daemon are replaced by OpenClaw heartbeat + cron jobs. See `docs/OPENCLAW_INTEGRATION.md`.
> Helper threads: memory mirror, upgrade bridge, process watchdog.

---

## 2. Grow Agent (Cultivation)

**Entry:** OpenClaw heartbeat + `grow-monitor` skill (calls HAL API). Legacy: `src/orchestrator/orchestrator.py`

### 2.1 Decision Cycle (every 30 min - 2 hours)

1. **Read sensors** — Govee (temp/humidity/CO2), Ecowitt (soil moisture), Kasa (device states)
   - Wrapped in circuit breakers (`govee_api`, `ecowitt_lan`) for fault tolerance
2. **Capture plant image** — USB webcam (Logitech C270), enhanced with CLAHE + white balance
3. **Load episodic memory** — Last 3 decisions for context continuity
4. **Gather unified context** — Trading P&L, social engagement, community feedback, email, reviews
5. **Get Grok AI decision** — Multimodal prompt (sensor + image + memory + unified context)
6. **Execute hardware actions** — Water, CO2, lights, fans, humidifier (max 3 per cycle)
7. **Store episodic memory** — Conditions, actions, observations persisted to disk
8. **Feed social engine** — Decision data queued for live social posts
9. **Capture timelapse frame** — Webcam API → `data/timelapse/dayN_timestamp.jpg`

### 2.2 Hardware Actions (14 tools)

| Tool | Device/API | Purpose |
|------|-----------|---------|
| `water` | Kasa pump plug | Calibrated watering (32ml/sec, 5s max, 150ml cap) |
| `inject_co2` | Kasa solenoid | CO2 injection 5-30s (light period only) |
| `set_device` | Kasa plugs | Generic on/off (light, exhaust, humidifier) |
| `set_humidifier_target` | Govee H7145 | Set target humidity % |
| `transition_stage` | Database | Change growth stage (changes all thresholds) |
| `log_observation` | Database | Free-text observation note |
| `request_human_help` | Alert system | Telegram/Discord alert with urgency |
| `get_watering_history` | Database | Recent watering events |
| `get_sensor_summary` | Database | Statistical summary of readings |
| `get_latest_photo` | Webcam | Capture plant image for analysis |
| `analyze_photo` | Grok Vision | AI visual health assessment |
| `queue_email` | Resend API | Send from agent@grokandmon.com |
| `update_grow_stage` | Database | Transition growth stage |
| `query_allium` | Allium API | Blockchain data queries |

### 2.3 Safety Enforcement (cannot be bypassed by AI)

- **Dark period lock** — Lights blocked 6 PM - 6 AM during flowering
- **Watering safeguards** — Stage-specific daily limits + cooldowns
- **Temperature emergency** — Auto exhaust at 35C, auto heat at 10C
- **CO2 ceiling** — Warning at 1200 ppm, dangerous at 1800 ppm
- **Kill switch** — All actions blocked until manual reset
- **Stale data warning** — Sensors >5 min old triggers conservative mode
- **Circuit breakers** — Hardware failures trigger half-open/closed states

### 2.4 Growth Stages

| Stage | Temp (F) | RH (%) | VPD (kPa) | Light | Water Threshold |
|-------|----------|--------|-----------|-------|----------------|
| Clone | 72-78 | 65-75 | 0.4-0.8 | 18/6 200-400 PPFD | 30% soil |
| Veg | 70-85 | 50-60 | 0.8-1.2 | 18/6 400-600 PPFD | 25% soil |
| Transition | 68-82 | 40-55 | 1.0-1.4 | 12/12 500-700 PPFD | 25% soil |
| Flowering | 65-80 | 40-50 | 1.0-1.5 | 12/12 600-900 PPFD | 22% soil |
| Late Flower | 65-75 | 30-40 | 1.2-1.6 | 12/12 600-800 PPFD | 20% soil |

### 2.5 Episodic Memory (wired 2026-02-08)

Each cycle stores: timestamp, conditions (temp/humidity/VPD/CO2/soil), actions taken, observations, day totals (water_ml, CO2 injections). Last 3 entries injected into every Grok prompt. Persisted to `data/logs/episodic_memory.json`.

### 2.6 Auto-Review Engine (wired 2026-02-08)

Every ~6 hours (12 learning cycles), generates compliance review:
- **ComplianceAnalyzer** — Scores temp/humidity/VPD/CO2/soil vs stage targets (A-F grade)
- **DecisionQualityAnalyzer** — Did actions improve conditions?
- **PatternDetector** — VPD instability, temp swings, overcorrection
- **VisualAnalyzer** — Grok vision plant health audit (when camera available)
- **OptimizationSuggester** — Prioritized improvement suggestions
- Results written to `data/historical_review.json` (picked up by unified context)

---

## 3. Trading Agent (Alpha Hunting)

**Entry:** `agents/ganjamon/src/main.py` (GanjaMonAgent subprocess, isolated PYTHONPATH)

### 3.1 Signal Sources (27+ implemented)

**Core Alpha:**

| Source | Module | Detection |
|--------|--------|-----------|
| Smart money tracking | `smart_money.py` | 100+ wallets, tiered LEGENDARY to DISCARDED |
| Telegram stealth | `telegram_alpha_monitor.py` | Passive channel listening, CA extraction |
| Twitter/X KOL | `twitter_monitor.py` | 50+ accounts, keyword extraction |
| Farcaster monitor | `farcaster_monitor.py` | Cast alpha (often faster than Twitter) |
| On-chain wallets | `agent_wallet_monitor.py` | AI agent wallet activity |
| Whale alerts | `whale_detector.py` | Large wallet movements |
| Launch detection | `launch_detector.py` | nad.fun, pump.fun, Token Mill |
| Mempool monitor | `mempool_monitor.py` | Pending tx via WebSocket |
| News feed | `news_feed.py` | Macro sentiment, breaking news |
| DexScreener WS | `dexscreener_ws.py` | Real-time trending, volume spikes |
| GMGN client | `gmgn_client.py` | Win rates, top traders, Solana |
| Copy trading | `copy_trader.py` | Mirror smart wallet entries/exits |

**Specialized:**

| Source | Module | Detection |
|--------|--------|-----------|
| AI agent detector | `ai_agent_detector.py` | ERC-8004 registry new agents |
| ERC-8004 monitor | `erc8004_monitor.py` | Trustless agent registrations |
| Prediction alpha | `prediction_alpha.py` | Polymarket odds shifts |
| GitHub monitor | `github_monitor.py` | Deploy/mainnet/launch commits |
| Google Trends | `google_trends.py` | Search volume narrative shifts |
| Macro awareness | `macro_awareness.py` | BTC dominance, ETH flows, Fed |
| Alpha discovery | `alpha_discovery.py` | Proactive research hunting |
| Curated feed | `curated_feed.py` | Hand-curated Twitter lists |
| Agent tracker | `agent_tracker.py` | Farcaster/Twitter agent activity |
| Agent monitor | `agent_monitor.py` | DexScreener agent tokens |
| Moltbook monitor | `moltbook_monitor.py` | Hackathon project launches |
| Blockscout source | `blockscout_source.py` | Contract deployments (Monad) |
| TradFi research | `tradfi_research.py` | Stock/commodity/crypto correlation |
| Flight tracking | `flight_tracker.py` | Influencer travel alpha |
| Community suggestions | Telegram `/suggest` | User-submitted token tips |
| Price aggregator | `price_aggregator.py` | Cross-DEX price normalization |

### 3.2 Validation Layer

Before any trade: GoPlus honeypot check, DexScreener verification, LP lock check, holder distribution analysis, contract source verification, signal confidence scoring (min 0.15 for paper).

### 3.3 Execution Engines

| Platform | Chain | Trade Type |
|----------|-------|-----------|
| nad.fun | Monad | Bonding curve memecoins |
| Token Mill (LFJ) | Monad | Bonding curve tokens |
| Jupiter | Solana | pump.fun + aggregated swaps |
| Uniswap V3 | Base/ETH | Deep liquidity spot |
| Aerodrome | Base | $MON/USDC pool |
| Hyperliquid | Hyperliquid L1 | Perpetual futures |
| Polymarket | Polygon | Prediction markets |

### 3.4 Multi-Agent Reasoning

4 AI agents deliberate on every trade:
- **Analyst** — Signal quality, market context
- **Risk Manager** — Position sizing, exposure limits
- **Contrarian** — Devil's advocate, bearish scenarios
- **Coordinator** — Final synthesis and decision

Dual-provider: xAI primary, OpenRouter fallback.

### 3.5 Risk Management

- 30% daily loss limit (kill switch)
- 5% max per position
- 25 max concurrent positions
- Confluence required (2+ sources for high confidence)
- Paper trading mode (default)
- Config backups on every change

### 3.6 Profit Allocation

| Destination | % | Purpose |
|-------------|---|---------|
| Compound | 60% | More trading capital |
| Buy $MON | 25% | Support ecosystem token |
| Buy $GANJA | 10% | Support agent token |
| Burn | 5% | Deflationary pressure |

Payments pipeline: `ProfitSplitter` computes allocations, `ApprovalGate` requires Telegram approval for large batches (>auto-approve limit). Small batches execute automatically.

---

## 4. Social & Engagement

### 4.1 Engagement Daemon (24/7, 6+ platforms)

| Platform | Frequency | Action |
|----------|-----------|--------|
| Farcaster mentions | Every 10 min | Reply to @mentions (max 3/cycle) |
| Farcaster channels | Every 30 min | Browse monad/ai/base/degen/cannabis |
| Farcaster original | Every 1 hour | Plant updates or topical content |
| Twitter/X originals | Every 4 hours | Original posts (no replies, no hashtags) |
| Twitter/X QTs | Every 6 hours | Rasta parody QTs of trending tweets (max 2/day) |
| Twitter/X mentions | Every 30 min | Reply to @mentions in Rasta voice (max 4/day) |
| Telegram proactive | Every 6 hours | Queue message to main group |
| Moltbook/Clawk | Every 3 hours | Hackathon visibility |
| Email outbox | Every 5 min | Send queued emails (max 3/cycle) |

### 4.1b Twitter Interactive Pipeline (wired 2026-02-08)

**Automated Rasta Parody Quote Tweets:**
1. Search Twitter for trending tweets (monad, memecoin, cannabis grow)
2. Score candidates by engagement * reach * media_bonus (log10 followers)
3. Filter: 1K+ followers, 10+ avg likes/tweet history, not already QT'd
4. Translate text to Rasta parody via Grok AI (match source length, max 1000 chars)
5. Download tweet images and **ganjafy** via Gemini 3 Pro (identity-preserving rasta transformation)
   - **Chart mode**: Detects price/chart screenshots, swaps branding to "Ganja $MON" with our logo as grounded reference
   - **General mode**: Standard rasta transformation (dreads, tam, joint, rasta colors, "$MON" label)
6. Upload ganjafied image and post QT
7. Track QT'd tweet IDs in `data/twitter_quoted_ids.json` to avoid re-quoting

**Mention Replies:**
1. Check @GanjaMonAI mentions every 30 min (since last seen ID)
2. Generate Rasta reply via Grok AI (warm, funny, in-character)
3. Post reply (mention-based only — never unsolicited)
4. Track replied IDs in `data/twitter_replied_ids.json`

**Compliance:**
- X Premium: originals 280 chars, QTs 1000 chars, replies 500 chars
- No hashtags, no leaf emoji, "Automated" in bio
- Conservative rate limits: 2 QTs/day, 4 replies/day, 4 originals/day
- Author quality gates prevent punching down at small accounts

### 4.2 Social Scheduler (wired 2026-02-08)

| Job | Trigger | What It Does |
|-----|---------|-------------|
| Daily grow update | Grow-light-on time | Sensor data + AI decision + Rasta content to Twitter/Farcaster |
| Trading summary | Every 6 hours | Portfolio status + PnL to Farcaster |
| Community engagement | Every 2 hours | Scan for engagement opportunities |
| Morning update | 8 AM | General morning content |
| Evening update | 6 PM | General evening content |

### 4.3 Live Data in Posts (wired 2026-02-08)

Social posts now include:
- **Live sensor data** from grow decisions (temp, humidity, VPD, soil)
- **Live portfolio data** from trading agent (cash, open positions, PnL, win rate)

### 4.4 Anti-Robot Humanization

Time-based frequency modulation (150% peak, 40% quiet), jittered delays (base +/- 30%), variable post length, organic closers (30%), contextual emoji (20%), typing delay simulation (~40 WPM).

### 4.5 Social Tracker (wired 2026-02-08)

Records every post to SQLite: platform, type, length, timestamp, engagement metrics. Computes optimal post type, hour, and length per platform. Exports to `data/social_tracker.json`.

---

## 5. Telegram Bot

**Service:** `ganja-mon-bot.service` (separate — community bot stays independent)
**Bot:** @MonGardenBot

### Commands

`/status` `/photo` `/vibes` `/strain` `/token` `/ca` `/shill` `/price` `/suggest` `/suggestions` `/trading` `/alpha` `/brain` `/signals`

### Features

- Conversational AI (Grok-powered Rasta personality, 0.85 temp)
- Spam/scam detection with humorous roasting
- Community memory (60+ OG profiles, deep research every 6h)
- Proactive engagement (joins conversations naturally)
- Trade suggestion pipeline (suggestions flow to trading agent)
- Live price lookups (DexScreener + CoinGecko)

---

## 6. Streaming & Voice

- Retake.tv streaming: 720p/20fps/1.5Mbps with branded overlay
- Rasta voice pipeline (Windows only): ElevenLabs TTS + Jamaican Patois
- Voice manager: subprocess lifecycle management
- **Rule: Never stream without Rasta voice working**

---

## 7. Blockchain & On-Chain

### ERC-8004 Agent Identity

- **Agent #4** on Monad: https://8004scan.io/agents/monad/4
- Reputation publishing every 4 hours (cron on Chromebook)

### $MON Token

| Chain | Contract |
|-------|----------|
| Monad (native) | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` |
| Base (bridged) | `0xE390612D7997B538971457cfF29aB4286cE97BE2` |

### Wormhole NTT Bridge

Both directions working (Monad <-> Base). VAA attestation ~30 seconds.

### A2A Protocol

JSON-RPC via `grokmon-router` Cloudflare Worker. Skills: `cultivation-status`, `alpha-scan`, `trade-execution` (approval-gated), `mon-liquidity`.

---

## 8. API Server

FastAPI on port 8000, 40+ endpoints covering: sensors, AI decisions, grow management, camera, VPD calculations, token metrics, social, analytics, health, auth, scheduling.

### Health Endpoint (wired 2026-02-08)

`GET /api/health` — Aggregated status from watchdog + circuit breakers + subsystems.
`GET /api/ready` — Readiness probe (stale component detection).

---

## 9. Self-Improvement & Learning

### Grow Domain

| System | Storage | Status |
|--------|---------|--------|
| Episodic memory | `data/logs/episodic_memory.json` | WIRED |
| GrowLearning | `data/grow_learning.db` | WIRED |
| Auto-review engine | `data/historical_review.json` | WIRED |
| Unified context | Cross-system aggregation | WIRED |

### Trading Domain

| System | Storage | Status |
|--------|---------|--------|
| Experience DB | `experience.db` (3.3MB) | RUNNING |
| Signal weighter | Adaptive 0.1x-3.0x weights | RUNNING |
| Meta detector | Market regime shifts | RUNNING |
| Agent learner | Study other agents | RUNNING |
| Self modifier | Auto-code changes | BUILT |
| Deep agent | 8-domain cross-synthesis | RUNNING |

### Cross-Domain

| System | Method | Status |
|--------|--------|--------|
| Grimoire | Strategy pattern library | RUNNING |
| Regime detector | Market classification | RUNNING |
| Compound learning | Cross-domain synthesis | RUNNING |
| Strategy tracker | Win/loss per strategy | RUNNING |

### Ralph Loop

Autonomous development: cron every 4h, 292+ requests, 211+ deployed. Proactive mode when idle.

---

## 10. Infrastructure

### Circuit Breakers (wired 2026-02-08)

| Breaker | Protects | Threshold |
|---------|----------|-----------|
| `govee_api` | Sensor reads | 5 failures / 60s |
| `ecowitt_lan` | Soil moisture | 5 failures / 60s |
| `kasa_lan` | Hardware control | 3 failures / 30s |
| `grok_api` | AI decisions | 3 failures / 120s |

### Payments Pipeline (wired 2026-02-08)

- `ProfitSplitter` — 60/25/10/5 split with batch API
- `ApprovalGate` — Telegram approval for large amounts, auto-approve small
- Ledger at `data/payment_ledger.json`

### Email Pipeline (wired 2026-02-08)

- Outbound: `src/mailer/client.py` via Resend API (agent@grokandmon.com)
- Inbound: Webhook endpoint at `/api/webhooks/email`
- Classification: spam/question/partnership via Grok
- Inbox persistence: `data/email_inbox.json`

### Databases

| Database | Purpose |
|----------|---------|
| `data/grow_data.db` | Sensor readings, device states, AI decisions |
| `data/grow_learning.db` | Grow learning patterns |
| `experience.db` | Trading experience (3.3MB) |

---

## 11. What Changed in the Merge (2026-02-08)

| Change | Detail |
|--------|--------|
| **Unified process** | Trading agent now subprocess of `run.py all` |
| **Disabled service** | `ganjamon-agent.service` disabled on Chromebook |
| **Deleted duplicates** | `src/signals/` (9 duplicate sources) removed |
| **Deleted dead code** | `src/scraping/` removed |
| **Archived legacy** | `src/brain/agent.py` renamed to `agent_legacy.py` |
| **Wired unified context** | `UnifiedContextAggregator` feeds into every Grok decision |
| **Wired episodic memory** | Load/store/inject into decisions, persist to disk |
| **Wired auto-review** | ReviewEngine runs every ~6h, writes compliance reports |
| **Added 3 tools** | `queue_email`, `update_grow_stage`, `query_allium` |
| **Wired circuit breakers** | Govee + Ecowitt sensor reads protected |
| **Wired health endpoints** | `/api/health` + `/api/ready` aggregated status |
| **Fed social engine** | Grow decisions + portfolio data flow into posts |
| **Wired payments** | Splitter batch API + approval gate |
| **Wired email pipeline** | Inbound webhook + inbox persistence |
| **Wired social scheduler** | Daily grow, 6h trading summary, 2h engagement |
| **Wired timelapse** | Webcam API capture on every decision cycle |
| **Wired analytics** | Stability calculator from DB sensor data |
