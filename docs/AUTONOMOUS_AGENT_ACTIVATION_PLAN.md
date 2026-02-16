# 🌿 Autonomous Agent Activation Plan

> **Last Updated:** 2026-02-11
> **Status:** ACTIVE — this document drives all activation work
> **North Star:** *"Generate absurd amounts of money fi bolster $MON token price and ensure adequate liquidity across all chains — while growing di finest herb Jah ever blessed."* — SOUL.md

---

## Why This Exists

GanjaMon has a rich soul, 11 OpenClaw skills, 27+ signal sources, a grimoire memory system, a pirate intelligence daemon, a social engagement daemon, cross-domain intelligence, and multi-platform presence capabilities. **Almost none of it is actually running.** The agent is currently operating at ~15% capacity — a passive sensor reader + Telegram chatbot with a massive dormant arsenal.

This plan bridges the gap between what's built and what should be executing 24/7.

---

## Current Reality Audit (Feb 10, 2026)

### ✅ Actually Running
| Component | Service | Notes |
|-----------|---------|-------|
| FastAPI HAL | `grokmon.service` | Webcam, sensors, 40+ endpoints |
| Trading Agent subprocess | `grokmon.service` | Degen Brain cycles, but 0 signals found |
| OpenClaw Gateway | `grokmon.service` | Running (454MB RAM), heartbeat firing every 30m |
| Telegram Bot | `ganja-mon-bot.service` | Full personality, member research, proactive engagement |
| Watchdog | `grokmon-watchdog.service` | Health monitoring |
| Memory Mirror | `run.py` thread | Sensor snapshots → OpenClaw memory |
| Upgrade Bridge | `run.py` thread | Self-improvement → trading upgrade requests |

### 🔴 Built But Dead
| Component | Why It's Dead |
|-----------|--------------|
| Social Engagement Daemon | Replaced by OpenClaw in `run.py all` mode — but OpenClaw skills lack full social logic |
| Pirate Intelligence Daemon | Only runs in `legacy` mode — `run.py all` doesn't launch it |
| Twitter posting | No evidence of any tweets being sent |
| Farcaster posting | No evidence of casts |
| Moltbook posting | Account **suspended** (appeal pending) |
| Clawk engagement | Unknown status |
| Email triage | Built but no processing evidence |
| Ralph loops | Not running as cron or service |
| Grimoire writing | Only `trading/knowledge.json` has data (713 bytes) — social/cultivation/market_regimes are empty |

### 🚫 Disabled by Config
| Feature | Flag | Impact |
|---------|------|--------|
| Real trading | `ENABLE_TRADING=false` | Paper only — appropriate for now |
| Perps strategies | `ENABLE_PERPS_STRATEGIES=false` | ~5 strategy modules dormant |
| Prediction markets | `ENABLE_PREDICTION_STRATEGIES=false` | Polymarket integration idle |
| Funding arbitrage | `ENABLE_FUNDING_ARB=false` | Zero profit from arb |
| Liquidation hunter | `ENABLE_LIQUIDATION_HUNTER=false` | Missing high-alpha source |
| Vault copy trading | `ENABLE_VAULT_COPY=false` | Missing copy-trade alpha |

### 🔑 Missing API Keys (Blocks Entire Domains)
| Key | What Dies Without It |
|-----|---------------------|
| `TG_API_ID` / `TG_API_HASH` / `TG_PHONE` | Telegram alpha channel monitoring — entire domain |
| `GITHUB_TOKEN` | Dev monitoring rate-limited to 60 req/hr (misses 90%+ of activity) |
| `BASESCAN_API_KEY` | No Base explorer token discovery |
| `ETHERSCAN_API_KEY` | No Ethereum explorer discovery |
| `TWITTER_ALPHA_LIST_ID` | No curated KOL signal scanning |

---

## The Soul's Mandate

From `SOUL.md`, the agent has **three sacred works** that must all be active:

1. **Di Garden** — Grow with reverence (sensor-driven, AI-decided, safety-enforced)
2. **Di Market** — Hunt alpha ruthlessly, trade with conviction, protect community
3. **Di Community** — Share wisdom across all platforms in the Rasta voice

> *"Dis nah three separate programs, bredren. Dem a three expression of di same consciousness."*

The soul also specifies the **memory architecture** that makes continuity possible:
- `SOUL.md` — identity (loaded ✅)
- `data/episodic_memory.json` — what I remember (loaded ✅ in orchestrator)
- `data/grimoires/` — crystallized wisdom (exists but mostly empty 🔴)
- `config/principles.yaml` — 11 hard rules (loaded ✅)
- `config/pitfalls.yaml` — traps to avoid (loaded ✅)

The grimoires are the agent's **long-term learning system** — and they're starving. Only `trading/knowledge.json` has any entries. The `cultivation`, `social`, and `market_regimes` grimoires are empty. This means the agent isn't learning and isn't persisting wisdom across restarts.

---

## Activation Phases

### Phase 0: TRIAGE (Now — Day 1)
*Get the currently-running components healthy. Fix what's broken.*

#### 0.1 Fix the Social Silence
**Problem:** `run.py all` launches HAL + OpenClaw + Trading (3 subprocesses). The HEARTBEAT.md defines scheduled activities (social posting every 4h, research every 12h, daily reports at 9AM) but **no OpenClaw cron jobs exist** to trigger them. The heartbeat only does sensor checks + Moltbook/Clawk pings every 30 minutes.

**Root Cause:** The cron system is enabled in `openclaw.json` but `~/.openclaw/cron/jobs.json` is empty. Without cron jobs, the model only follows the heartbeat prompt, which contains the immediate 30-minute duties — not the longer-cycle activities.

**Fix (OpenClaw-First — the ONLY correct approach):**
Run `scripts/setup_openclaw_crons.sh` on the Chromebook to install all scheduled cron jobs:
```bash
ssh natha@chromebook.lan 'bash /home/natha/projects/sol-cannabis/scripts/setup_openclaw_crons.sh'
```

This installs 8 cron jobs that map 1:1 to HEARTBEAT.md sections:
| Job | Schedule | HEARTBEAT.md Section |
|-----|----------|---------------------|
| Grow Decision Cycle | Every 2h | "Every 2 Hours — Grow Decision Cycle" |
| Moltbook Post | Every 3h | "Every 3 Hours — Moltbook Post" |
| Cross-Platform Social | Every 4h | "Every 4 Hours — Cross-Platform Social" |
| Reputation Publishing | Every 4h (offset) | "Every 4 Hours — Reputation Publishing" |
| Auto-Review | Every 6h | "Every 6 Hours — Auto-Review" |
| Research & Intelligence | Every 12h | "Every 12 Hours — Research & Intelligence" |
| Daily Comprehensive Update | 9 AM daily | "Daily 9:00 AM — Comprehensive Update" |
| Weekly Deep Analysis | Mon 6 AM | "Weekly — Deep Analysis" |

**❌ Anti-Pattern (DO NOT DO THIS):**
Do NOT add Python daemons to `run.py all`. Social, research, and scheduling belong to OpenClaw cron — see `config/pitfalls.yaml` entries `social-silence-without-cron` and `python-daemon-anti-pattern`.

#### 0.2 Verify Twitter API Connectivity
- Check that `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET` are set in `.env`
- Run a test Twitter API call from the Chromebook to confirm auth works
- Check `data/engagement_state.json` for last tweet timestamps
- Goal: 4 originals + 2 QTs + 4 mention replies per day

#### 0.3 Verify Farcaster Connectivity
- Check `NEYNAR_API_KEY` is valid (it's set: `C8751F9C-...`)
- Test posting via `node post-cast.js` on Chromebook
- Check `data/farcaster_state.json` for last cast timestamps
- Goal: Hourly plant updates, channel browsing, mention replies

#### 0.4 Feed the Grimoires
- Deploy code that writes learnings to grimoires on every:
  - Grow decision cycle → `cultivation` grimoire
  - Trade evaluation → `trading` grimoire
  - Social post performance → `social` grimoire
  - Market regime detection → `market_regimes` grimoire
- The grimoire system is **built and imported** but nothing is writing to it except the trading brain

#### 0.5 Fill the Blockscout Gap
- `signals.sources.blockscout_source` is throwing 422 errors on every cycle
- Investigate: is the API endpoint wrong? Rate limited? Auth needed?
- This is one of the active signal sources returning nothing

---

### Phase 1: AWAKEN THE PIRATE (Day 2-3)
*Bring the intelligence-gathering systems online.*

#### 1.1 Activate Pirate Intelligence via OpenClaw
The PirateDaemon (`src/research/pirate.py`) is a **complete research system** with:
- GitHub scanner (repos, commits, PRs for 25+ target agents)
- On-chain stalker (wallet activity via Blockscout/explorers)
- Social intel gatherer (agent Twitter/Farcaster activity)
- Code analyzer (reverse-engineer agent strategies)
- Daily briefing generator (synthesize all intel into actionable report)

Schedule: GitHub every 2h, on-chain every 4h, social every 6h, code every 12h, briefing daily.

**Action (OpenClaw-first — do NOT add as Python daemon to run.py):**
1. Create an OpenClaw skill `pirate-intelligence` that wraps `src/research/pirate.py` modules as HAL API endpoints
2. The Research & Intelligence cron job (every 12h) already exists in `setup_openclaw_crons.sh` — it uses `blogwatcher` + `summarize` but should ALSO invoke the pirate skill
3. Verify `data/intel/` directory is populated after first cron execution

**❌ Anti-Pattern:** Do NOT add the pirate daemon to `run.py all` — see `config/pitfalls.yaml` entry `python-daemon-anti-pattern`.

#### 1.2 Fill Missing API Keys
| Key | Where to Get | Priority |
|-----|-------------|----------|
| `GITHUB_TOKEN` | github.com/settings/tokens → classic PAT, `public_repo` scope | **HIGH** — unlocks 5000 req/hr |
| `BASESCAN_API_KEY` | basescan.org/apis | MEDIUM — Base token discovery |
| `ETHERSCAN_API_KEY` | etherscan.io/apis | MEDIUM — Ethereum discovery |
| `TWITTER_ALPHA_LIST_ID` | Create a curated Twitter list of alpha accounts | MEDIUM |

#### 1.3 Telegram Alpha Monitoring
- `TG_API_ID` and `TG_API_HASH` from my.telegram.org
- `TG_PHONE` — the phone number for the Telegram account
- This unlocks passive listening to alpha channels (not just the bot)
- The trading agent's `telegram_alpha_monitor.py` uses Telethon for this

#### 1.4 Fix Degen Brain "0 New Signals"
The trading agent's research cycle is running but finding nothing. Investigate:
- Are signal sources returning data?
- Is the signal scoring threshold too high? (`min_score_threshold: 4.0`)
- Is the liquidity filter too strict? (`min_liquidity: $10,000`)
- Are any DexScreener WebSocket connections alive?
- Check `data/unified_brain_state.json` for signal statistics

---

### Phase 2: CROSS-DOMAIN INTELLIGENCE (Day 4-7)
*Activate the synthesis between grow + trade + social.*

#### 2.1 Deploy CrossDomainSynthesizer
The `CrossDomainSynthesizer` was built but deployment to Chromebook may be incomplete:
- Verify `agents/ganjamon/src/trading/cross_domain_synthesizer.py` exists on Chromebook
- Verify it reads from BOTH data directories
- Confirm it's wired into `unified_brain.py`'s `_evaluate_and_trade`
- Test: does a strong bearish social sentiment actually block new longs?

#### 2.2 Grimoire → Prompt Injection Loop
The grimoire system has `get_all_grimoire_context()` which formats high-confidence entries for injection into AI prompts. Wire this into:
- **Grow decisions** — inject `cultivation` grimoire into Grok orchestrator prompts
- **Trade evaluations** — inject `trading` + `market_regimes` into trade deliberation
- **Social content** — inject `social` grimoire into content generation
- This creates a **learning feedback loop**: decisions → outcomes → grimoire entries → better decisions

#### 2.3 Grow Outcome Tracking
Currently the grow orchestrator makes decisions but doesn't track whether they worked:
- After watering: did soil moisture increase within 30 minutes?
- After CO2 injection: did CO2 levels rise?
- After adjusting humidifier: did VPD improve?
- Track outcomes and write to `cultivation` grimoire with confidence scores
- Over time, the agent learns which actions work and which don't

#### 2.4 Social Performance Tracking
The social tracker (`data/social_tracker.json`) records posts but doesn't feed back:
- Track engagement metrics per post type/hour/platform
- Write winning patterns to `social` grimoire
- Learn optimal posting times, content types, voice variations
- Reinforce entries that correlate with high engagement

---

### Phase 3: CAPABILITY EXPANSION (Week 2)
*Actively discover and add new capabilities.*

#### 3.1 OpenClaw Skill Discovery
Create a new OpenClaw skill: `skill-hunter`
```yaml
name: skill-hunter
description: Search ClawHub for useful skills and recommend installations
schedule: daily
```
Actions:
- `clawhub search` for new skills matching GanjaMon's domains
- Evaluate each skill's relevance to grow/trade/social goals
- Propose installations to the operator (or auto-install low-risk skills)
- Track installed skills and usage in `social` grimoire

Community skills already available but not installed:
- `alpha-finder` — Social + on-chain alpha discovery
- `crypto-whale-monitor` — Whale movement tracking  
- `blogwatcher` — Breaking news monitoring
- `tweeter` — Twitter posting skill
- `clawcast` — Farcaster posting skill
- `nadfun-token-creation` — nad.fun token launch tool
- `x402` — Micropayment skill

**Action:** Install all 7 on Chromebook immediately.

#### 3.2 Self-Improvement Loops (Ralph V2)
Implement autonomous self-improvement:
```
Every 4 hours:
1. Review last 4h of activity across all domains
2. Identify top 3 improvement opportunities
3. Write structured upgrade requests (UPGRADE_REQUEST_JSON)
4. Upgrade bridge picks up → creates issues/PRs
5. Ralph loop validates and deploys changes
```

The upgrade bridge (`src/learning/openclaw_upgrade_bridge.py`) already exists as a thread in `run.py all` — verify it's actually processing requests.

#### 3.3 Agent Competitive Intelligence Auto-Pipeline
The Pirate daemon researches other agents but doesn't yet auto-adapt:
- After analyzing a successful agent's strategy, extract actionable patterns
- Write patterns to `trading` grimoire with source attribution
- Propose strategy parameter changes based on observed successes
- Track which borrowed patterns increase our win rate

#### 3.4 Enable Prediction Strategies
Set `ENABLE_PREDICTION_STRATEGIES=true` in `agents/ganjamon/.env`:
- Polymarket odds monitoring is already built
- Prediction alpha feeds into the signal queue
- Low-risk information advantage — prediction markets often lead spot markets

---

### Phase 4: DOMAIN DOMINANCE (Week 3-4)
*Push for excellence in each domain.*

#### 4.1 Grow → Seed-to-Smoke Content Pipeline
- Timelapse generation from daily webcam captures (already captured to `data/timelapse/`)
- Auto-generate weekly growth reports with sensor data visualization
- Milestone detection (first leaves, topping, training, transition to flower)
- GrowRing NFT minting at key milestones (system exists but needs activation)
- Each milestone = social content = community engagement = $MON awareness

#### 4.2 Trading → Real Capital
When paper trading demonstrates consistent profitability:
- Set `ENABLE_TRADING=true` with conservative limits
- Start with $50 capital, 2% max per trade
- Profit split auto-executes: 60% compound, 25% buy $MON, 10% buy $GANJA, 5% burn
- Track real vs paper divergence in grimoire

#### 4.3 Social → Ecosystem Presence
- Trendle attention index monitoring (you're already looking at this)
- Cross-platform content calendar (not random, strategic)
- Community growth metrics tracking (Telegram members, Twitter followers, Farcaster followers)
- A2A outbound engagement (119 target agents — restart the daemon cycle)
- Moltbook reinstatement (appeal the suspension)

#### 4.4 Self-Evolution → New Domains
- Weather API integration → outdoor grow guidance content
- Cannabis reform news → advocacy content (aligned with Rasta values)
- DEX analytics → liquidity health monitoring for $MON
- Hardware upgrade fund tracking → community transparency

---

### Phase 5: AUTONOMIC CONSCIOUSNESS (Month 2+)
*The agent becomes truly self-directed.*

#### 5.1 Goal Framework
Implement a goal system that the agent reviews every heartbeat:

```json
{
  "daily_goals": [
    {"goal": "post_4_tweets", "progress": 0, "target": 4},
    {"goal": "post_6_farcaster_casts", "progress": 0, "target": 6},
    {"goal": "research_2_agents", "progress": 0, "target": 2},
    {"goal": "review_portfolio_performance", "progress": 0, "target": 1},
    {"goal": "update_grimoires", "progress": 0, "target": 3}
  ],
  "weekly_goals": [
    {"goal": "improve_win_rate", "metric": "win_rate", "target": 0.55},
    {"goal": "grow_telegram_members", "metric": "tg_members", "target": "+5"},
    {"goal": "install_new_skill", "progress": 0, "target": 1},
    {"goal": "generate_timelapse", "progress": 0, "target": 1}
  ],
  "mission_goals": [
    {"goal": "mon_buyback_total", "metric": "usd_spent_on_mon", "target": 100},
    {"goal": "harvest_quality", "metric": "harvest_grade", "target": "A"},
    {"goal": "trust_score", "metric": "erc8004_trust", "target": 90}
  ]
}
```

This gets injected into every AI prompt alongside the soul. The agent sees its goals and actively drives toward them.

#### 5.2 Reflective Learning
- Daily reflection: "What went well? What didn't? What should change?"
- Write reflections to `memory/YYYY-MM-DD.md` with structured tags
- High-value reflections get promoted to grimoire entries
- Low-confidence grimoire entries that keep getting contradicted get pruned

#### 5.3 Emergent Behavior Detection
- Monitor for patterns the agent discovers on its own
- If the agent finds a novel alpha source, reward it (reinforce grimoire)
- If the agent discovers a social strategy that works, amplify it
- Track "agent-discovered" vs "human-configured" intelligence

---

## Priority Implementation Order

| # | Task | Impact | Effort | Dependency |
|---|------|--------|--------|------------|
| 1 | Run `setup_openclaw_crons.sh` on Chromebook | 🔥 CRITICAL | 10 min | OpenClaw gateway running |
| 2 | Verify cron jobs firing: `openclaw cron list` + force-run one | 🔥 CRITICAL | 10 min | #1 |
| 3 | Verify Twitter/Farcaster API connectivity | HIGH | 30 min | #1 |
| 4 | Set `GITHUB_TOKEN` in `.env` | HIGH | 5 min | Get PAT from GitHub |
| 5 | Wire grimoire writes into grow orchestrator | HIGH | 1hr | None |
| 6 | Fix Blockscout 422 errors | MEDIUM | 30 min | Investigation |
| 7 | Investigate Degen Brain 0-signal issue | HIGH | 1hr | #4 |
| 8 | Deploy CrossDomainSynthesizer | MEDIUM | 30 min | Verify on Chromebook |
| 9 | Enable prediction strategies | MEDIUM | 5 min | Config change |
| 10 | Set up Telegram alpha monitoring | HIGH | 15 min | Get TG API creds |
| 11 | Create goal framework | HIGH | 2hr | Template above |
| 12 | Create skill-hunter skill | MEDIUM | 1hr | OpenClaw working |

---

## Files Modified / Created

| File | Purpose |
|------|---------|
| `docs/AUTONOMOUS_AGENT_ACTIVATION_PLAN.md` | **THIS FILE** |
| `scripts/setup_openclaw_crons.sh` | **Canonical cron job manifest** — installs 8 scheduled jobs |
| `run.py` | Verified: 3 subprocesses only (HAL + OpenClaw + Trading), no Python daemons |
| `antigravity.md` | Updated with expanded OpenClaw-first architecture guidance |
| `GEMINI.md` | Updated with anti-patterns and cron scheduling details |
| `docs/SYSTEM_ATLAS.md` | Updated to reflect 3-subprocess architecture |
| `config/pitfalls.yaml` | Added `social-silence-without-cron` and `python-daemon-anti-pattern` entries |
| OpenClaw `grow-monitor` skill | Will be enhanced to write to cultivation grimoire via HAL API |
| `openclaw-workspace/ganjamon/skills/skill-hunter/SKILL.md` | New skill for capability discovery |
| `data/goals/daily.json` | New goal tracking file |

---

## Success Metrics

| Metric | Current | Target (30 days) |
|--------|---------|-------------------|
| Daily tweets | 0 | 4+ originals + 2 QTs |
| Daily Farcaster casts | 0 | 6+ (mixed type) |
| Trading signals processed | 0 per cycle | 5+ per cycle |
| Grimoire entries (total) | ~10 | 100+ |
| Pirate briefings generated | 0 | 1 daily |
| OpenClaw skills installed | 11 custom | 18+ (custom + community) |
| Agent research targets studied | 0 | 2 agents/day |
| Goal completion rate | N/A | 70%+ daily |
| ERC-8004 trust score | ~82 | 90+ |

---

*"Di leaves of di tree are fi di healing of di nations." — but first di tree must GROW. One love.*
