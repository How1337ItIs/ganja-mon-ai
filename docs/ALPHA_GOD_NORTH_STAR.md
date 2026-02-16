# 🎯 Alpha God: The North Star for Intelligent Cross-Domain Trading

> **Last Updated:** 2026-02-11
> **Status:** ACTIVE — this document drives all trading development decisions

---

## Architecture: How The System Actually Works

### The Three Subprocesses (Updated Feb 11, 2026)

The root `run.py` (at `sol-cannabis/`) launches 3 processes via `python run.py all`:

| Process | Module | Role | Data Dir |
|---------|--------|------|----------|
| 1. **FastAPI** (HAL) | `src/api/app.py` | Web server, 82+ endpoints, sensor reads, actuators, safety | `sol-cannabis/data/` |
| 2. **OpenClaw Gateway** | `openclaw gateway run` (:18789) | Primary AI orchestrator — heartbeat, skills, social, decisions | `sol-cannabis/data/` |
| 3. **Trading Agent** | `agents/ganjamon/src/main.py` | Signal monitoring, paper/real trading | `agents/ganjamon/data/` |

**Critical detail:** The trading agent runs as a **subprocess with isolated PYTHONPATH** (`python -m main` in `agents/ganjamon/`). It is a separate codebase with its own `.env`, `data/`, and dependencies. **This isolation is a stepping stone, not the final architecture** — the north star is trading as an OpenClaw skill (see below).

Helper threads in `run.py all`: memory mirror (sensor snapshots → OpenClaw memory every 30m), upgrade bridge (OpenClaw → trading agent), process watchdog (respawns crashed subprocesses every 30s).

**Legacy mode:** `python run.py legacy` launches HAL + Orchestrator + Social + Research + Trading (5 processes). Grow orchestration, social posting, and research are now handled by OpenClaw heartbeat + cron jobs.

### Deployment

- `deploy.sh` copies `src/` and `run.py` to the Chromebook. It does **NOT** copy `agents/ganjamon/`.
- Trading agent deployed via `deploy_agent.sh [--all|--file PATH]`.
- The Chromebook project lives at `/home/natha/projects/sol-cannabis`.
- `systemd/grokmon.service` runs `python run.py all`.

### Future: Unified OpenClaw Bot

The north star is **one OpenClaw agent** where grow, trade, and social are all skills of a single agentic entity:
- Phase A: OpenClaw skills call trading agent Python functions via HAL API
- Phase B: Key trading capabilities become HAL API endpoints
- Phase C: Trading subprocess retired — OpenClaw cron triggers trading cycles
- See `docs/CAPABILITY_AUDIT_2026-02-11.md` Part 0 for the full migration path

### Two Data Directories

The system has TWO `data/` directories that serve different purposes:

| Directory | Written By | Contents |
|-----------|-----------|----------|
| `sol-cannabis/data/` | Orchestrator, social daemon, API | Grow sensors (`last_sensors.json`), engagement state, farcaster state, episodic memory, SQLite DB |
| `ganjamon-agent/data/` | Trading agent | Paper portfolio, brain state, observations, experience DB, signal weights, model registry |

Cross-domain intelligence (the `CrossDomainSynthesizer`) must read from BOTH directories.

### Inside The Trading Agent

The trading agent (`agents/ganjamon/`) has two key layers:

1. **`src/main.py`** (GanjaMonAgent, ~4100 lines): The orchestrator that initializes 33 signal source modules (Twitter, Farcaster, Telegram, DexScreener WS, whale detection, etc.), manages the signal queue, position management, risk management, and LLM routing.

2. **`src/learning/unified_brain.py`** (UnifiedBrain, ~2500 lines): The research engine that runs 5 domain loops (on-chain, perps, predictions, social, dev_signal), evaluates tokens via Grok AI consensus, and executes paper trades with adaptive parameters.

These are NOT competing brains — `main.py` orchestrates the signal infrastructure and `unified_brain.py` is one of several subsystems it manages.

**Integration gap:** The trading agent currently has ZERO awareness of OpenClaw. It could leverage blogwatcher (news scanning), summarize (research briefings), alpha-finder (multi-source alpha), and crypto-whale-monitor (whale tracking) as OpenClaw skills instead of reimplementing them in Python.

---

## .env State (Verified Feb 2026)

**File:** `cloned-repos/ganjamon-agent/.env`

### ✅ Keys That Are Set
| Key | Value Summary |
|-----|--------------|
| `TWITTER_BEARER_TOKEN` | Full token (reading KOL tweets) |
| `TWITTER_API_KEY/SECRET` | Set (OAuth for @themidaswhale) |
| `NEYNAR_API_KEY` | `C8751F9C-...` (Farcaster) |
| `XAI_API_KEY` | `xai-hX1l5...` (Grok AI) |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` (multi-model) |
| `MONAD_RPC_URL` | `https://rpc.monad.xyz` |
| `PRIVATE_KEY` / `EVM_PRIVATE_KEY` | Set (trading wallet) |
| `8004SCAN_API_KEY` | Set |
| `MOLTBOOK_API_KEY` | Set |
| `CLAWK_API_KEY` | Set |
| `LIVEPEER_API_KEY` | Set |
| `RETAKE_ACCESS_TOKEN` | Set |

### ❌ Keys That Are Empty
| Key | Impact |
|-----|--------|
| `TG_API_ID`, `TG_API_HASH`, `TG_PHONE` | Telegram alpha monitoring disabled |
| `GITHUB_TOKEN` | Dev monitoring rate-limited (60 req/hr) |
| `BASESCAN_API_KEY`, `ETHERSCAN_API_KEY` | No explorer-based discovery |
| `AGENT_TOKEN`, `AGENT_TOKEN_MARKET` | $GANJA token not launched |
| `TWITTER_ALPHA_LIST_ID` | No curated list |

### ⚠️ Feature Flags (gotchas)
| Flag | Value | Note |
|------|-------|------|
| `ENABLE_TWITTER` | `true` | **Was shadowed by a duplicate `false` on line 131 — FIXED** |
| `ENABLE_TRADING` | `false` | Real trading disabled, paper only. Likely intentional. |
| `ENABLE_PERPS_STRATEGIES` | `false` | |
| `ENABLE_PREDICTION_STRATEGIES` | `false` | |
| `ENABLE_FUNDING_ARB` | `false` | |
| `ENABLE_LIQUIDATION_HUNTER` | `false` | |
| `ENABLE_VAULT_COPY` | `false` | |
| `ENABLE_FARCASTER` | `true` | |
| `ENABLE_LEARNING` | `true` | |

---

## Parameter Fixes Applied (Feb 2026)

| Parameter | Old Value | New Value | Why |
|-----------|-----------|-----------|-----|
| `stop_loss_pct` | **-50%** | **-20%** | 8/9 trades hit SL |
| `min_score_threshold` | **2.0** | **4.0** | Too many garbage signals |
| `min_liquidity` | **$5,000** | **$10,000** | Thin liquidity |
| `position_size_pct` | **10%** | **5%** | Smaller risk |
| `max_positions` | **15** | **5** | Quality over quantity |
| `take_profit_2x` | **100%** | **80%** | Lock gains earlier |
| `trailing_trigger_pct` | **30%** | **20%** | Trail sooner |
| `time_exit_minutes` | **60** | **30** | Don't hold bags |
| `slow_grind_time_min` | **30** | **20** | Exit slow grinds |

---

## Cross-Domain Intelligence (Feb 2026)

### What Was Built

`src/trading/cross_domain_synthesizer.py` reads data from both directories:

| Domain | Source File | From |
|--------|-----------|------|
> **⚠️ Note:** These file paths reference `sol-cannabis/data/` and `ganjamon-agent/data/` (now `agents/ganjamon/data/`).
| Grow sensors | `sol-cannabis/data/last_sensors.json` | Orchestrator |
| Social engagement | `sol-cannabis/data/engagement_state.json`, `engagement_log.jsonl` | Social daemon |
| Farcaster | `sol-cannabis/data/farcaster_state.json` | Social daemon |
| Trading performance | `ganjamon-agent/data/paper_portfolio.json` | Trading agent |
| Brain state | `ganjamon-agent/data/unified_brain_state.json` | Trading agent |
| A2A queries | `sol-cannabis/data/agent_log.jsonl` | A2A endpoint |
| Reputation | `ganjamon-agent/data/reputation_cache.json` | Trading agent |
| Macro | `ganjamon-agent/data/macro_state.json` | Trading agent (macro loop) |

### How It Gates Trades

1. **System health < 30%** → block all trades
2. **Risk appetite < 0.2** → block all trades
3. **Strong bearish mood** (>70% confidence) → block new longs
4. **Low conviction** (<0.3 modifier) → skip trade
5. **Normal conditions** → apply position size modifier

### What Was Wired

- ✅ `CrossDomainSynthesizer` imported in `unified_brain.py`
- ✅ Initialized in `UnifiedBrain.__init__`
- ✅ Gate check in `_evaluate_and_trade` before every trade
- ✅ Position size modified by cross-domain conviction
- ✅ Macro awareness loop in `main.py` writes `macro_state.json`

---

## Bugs Found and Fixed (Feb 2026)

| Bug | Impact | Fix |
|-----|--------|-----|
| `_PROJECT_ROOT` path off by one level | Synthesizer couldn't read grow/social data | Changed to `.parent.parent` |
| `ENABLE_TWITTER=false` duplicate on line 131 | Twitter monitoring silently disabled | Removed duplicate |
| No synthesizer initialization in `__init__` | `self.synthesizer` was `None` at runtime | Added init block with `get_synthesizer()` |
| `macro_state.json` not written | Macro data didn't reach synthesizer | Added JSON write in `_macro_awareness_loop` |

---

## Roadmap

### Phase 1: SURVIVAL (Now)
- [x] Fix catastrophic adaptive parameters
- [x] Create CrossDomainSynthesizer
- [x] Fix synthesizer path bug
- [x] Fix ENABLE_TWITTER duplicate
- [x] Wire synthesis into trading gate
- [x] Deploy changes to Chromebook via `deploy_agent.sh`
- [ ] Verify agent starts on Chromebook
- [ ] Reset portfolio to clean $1000 if needed
- [ ] Run `setup_openclaw_crons.sh` to activate scheduled jobs

### Phase 2: FILL GAPS
- [ ] Set `TG_API_ID` / `TG_API_HASH` / `TG_PHONE` for Telegram alpha
- [ ] Set `GITHUB_TOKEN` for dev monitoring (5000 req/hr)
- [ ] Add health checks: each signal source reports last-signal timestamp
- [ ] Verify social sentiment data flows from social daemon → `engagement_state.json` → synthesizer

### Phase 3: DEEPER SYNTHESIS
- [ ] Weighted signal confluence scoring (2+ domains → higher conviction)
- [ ] Narrative tracking from news_feed + prediction_alpha
- [ ] Mood-adjusted stop losses (bearish → tighter, bullish → normal)

### Phase 4: EVOLUTION
- [ ] Ralph loop for parameter tuning after 50 trades
- [ ] Domain PnL tracking → auto-allocate capital to winners
- [ ] Signal source grading → demote losers, promote winners

---

## Files Modified

| File | Change |
|------|--------|
| `agents/ganjamon/src/learning/unified_brain.py` | Fixed AdaptiveParameters, added synthesizer import + init + gate |
| `agents/ganjamon/src/trading/__init__.py` | Created package |
| `agents/ganjamon/src/trading/cross_domain_synthesizer.py` | NEW: cross-domain intelligence + path fix |
| `agents/ganjamon/src/main.py` | Macro loop writes `macro_state.json` |
| `agents/ganjamon/.env` | Removed `ENABLE_TWITTER=false` duplicate |
| `docs/ALPHA_GOD_NORTH_STAR.md` | THIS FILE (corrected architecture Feb 9 + Feb 11) |
