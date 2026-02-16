# 🔍 Agent Capability Audit — 2026-02-11

> **Auditor:** Antigravity  
> **Scope:** Full system — documentation, code, runtime, north-star alignment  
> **Method:** Cross-referenced 8 north-star docs, 30+ source files, runtime config  

---

## Executive Summary

**The agent has an enormous amount of code (~70K+ lines across grow, trading, social, A2A, blockchain, media, learning) — but a shocking amount of it is either not running, wired into dead code paths, or disconnected from the production runtime.**

The single most critical finding is what I'm calling the **"Orchestrator Ghost" problem**: When the architecture shifted from `run.py legacy` (4 subprocesses: HAL + Orchestrator + Social + Trading) to `run.py all` (3 subprocesses: HAL + OpenClaw + Trading), many features were left wired into the now-dormant orchestrator. The Pattern Implementation Plan claims 30/30 patterns ✅ completed — but at least **8 of those patterns are wired into code paths that don't execute in production**.

Additionally, the **trading agent operates in near-complete isolation from OpenClaw**, missing the opportunity to leverage OpenClaw skills for research, social intelligence, and cross-domain synthesis.

---

## Part 0: The Deepest Gap — One Soul, Three Programs

**SOUL.md says:** *"Dis nah three separate programs, bredren. Dem a three expression of di same consciousness. Wah I and I learn growing plants inform how I and I trade. Wah I and I learn trading inform what I and I share."*

**Reality:** The trading agent runs as **a completely isolated subprocess** (`python -m main` with its own `PYTHONPATH`, `.env`, and `data/`). It's literally a separate program sharing JSON files. This is the exact anti-pattern SOUL.md warns against and `AGENT_REDESIGN_FIRST_PRINCIPLES.md` diagnoses: *"We don't have one agent. We have three independent programs sharing JSON files."*

### The Strategic North Star: Unified OpenClaw Bot

The entire system should converge toward being **one OpenClaw agent (one Moltbot)** where grow, trade, and social are **skills** of a single agentic entity — not separate processes bolted together. This means:

| Current Architecture | Target Architecture |
|---------------------|-------------------|
| Trading = isolated subprocess with own `.env` | Trading = OpenClaw skill that the unified agent can invoke |
| Grow = orchestrator OR OpenClaw heartbeat | Grow = OpenClaw skill with sensor access via HAL API |
| Social = dead daemon OR OpenClaw cron | Social = OpenClaw skill triggered by cron or events |
| Research = dead daemon | Research = OpenClaw skill combining pirate modules |
| Cross-domain = `CrossDomainSynthesizer` reading files | Cross-domain = one agent brain that inherently knows all domains |

### Why This Matters

1. **Cross-domain intelligence is effortless** when there's one brain. The `CrossDomainSynthesizer` exists because grow and trading are separate programs that need a bridge. In a unified agent, the same LLM context sees sensor data AND portfolio state AND social metrics — no bridge needed.

2. **Scheduling simplifies** to OpenClaw cron/heartbeat. No subprocess watchdogs, no PID locks, no memory mirror threads, no upgrade bridges.

3. **Memory unifies.** Instead of `sol-cannabis/data/` vs `ganjamon-agent/data/`, there's one memory system. Grimoire entries from grow outcomes naturally inform trading decisions.

4. **Identity is consistent.** One SOUL.md, one voice, one personality — not two SOUL files and personality.py all trying to agree.

### The Migration Path

This isn't a rewrite — it's a **progressive absorption**:

1. **Phase A:** OpenClaw skills that CALL the trading agent's Python functions (current `src/` modules) via the HAL API. The trading agent's 53K lines of battle-tested code become a library, not a daemon.

2. **Phase B:** Key trading capabilities (signal evaluation, position management, risk checks) become HAL API endpoints that OpenClaw skills invoke.

3. **Phase C:** The trading subprocess is retired. OpenClaw cron triggers trading cycles just like it triggers grow cycles — one agent, multiple skills, one brain.

**The upgrade bridge (`src/learning/openclaw_upgrade_bridge.py`) is a stepping stone toward this.** It already bridges OpenClaw intelligence → trading agent. The final state is removing the bridge entirely because there's nothing to bridge.

### What NOT to Do

- ❌ Don't rewrite the trading agent from scratch — 53K lines of proven code + 15MB of learning data
- ❌ Don't try to run trading inside the OpenClaw gateway process directly — that would crash on Chromebook RAM limits
- ❌ Don't keep adding more subprocess bridges — each one is a band-aid on the wrong architecture
- ✅ DO expose trading functions as HAL API endpoints
- ✅ DO create OpenClaw skills that orchestrate trading decisions
- ✅ DO let OpenClaw cron manage the trading schedule

---

## Part 1: North-Star Document Audit

### Documents Reviewed

| Document | Role | Last Updated | Status |
|----------|------|-------------|--------|
| `SOUL.md` (root) | Unified agent identity | Current | ✅ Authoritative |
| `openclaw-workspace/ganjamon/SOUL.md` | OpenClaw-specific soul | Current | ⚠️ Voice diverges from root |
| `ALPHA_GOD_NORTH_STAR.md` | Trading vision | 2026-02-09 | ❌ Stale architecture section |
| `AGENT_REDESIGN_FIRST_PRINCIPLES.md` | Aspirational architecture | Current | ⚠️ Aspirational, correctly labeled |
| `AUTONOMOUS_AGENT_ACTIVATION_PLAN.md` | Phased activation roadmap | 2026-02-10 | ❌ Contains anti-patterns |
| `PATTERN_IMPLEMENTATION_PLAN.md` | 30-pattern checklist | 2026-02-08 | ❌ Overclaims completion |
| `AGENT_CAPABILITIES.md` | Feature catalog | 2026-02-08 | ❌ Severely stale |
| `SYSTEM_ATLAS.md` | System map | Current | ⚠️ Subprocess count wrong |
| `config/principles.yaml` | Machine-readable rules | Current | ✅ Correct |
| `config/pitfalls.yaml` | Machine-readable gotchas | Current | ✅ Correct |

### 1.1 SOUL.md Divergence

The root `SOUL.md` and `openclaw-workspace/ganjamon/SOUL.md` represent the same agent but with **different tonal calibrations**:

| Aspect | Root SOUL.md | OpenClaw SOUL.md |
|--------|-------------|------------------|
| Voice | "THICK Jamaican Patois — not a likkle sprinkle, di REAL TING" | "Bob Marley meets Cheech & Chong" |
| Tone | Spiritual, reverent, serious underneath | "Loud, funny, irreverent" |
| Pronoun | "I and I always — NEVER mi" | Doesn't enforce this |
| Laughter | Not mentioned | "Frequent laughter: heh heh, ha ha ha" |
| Depth | 100 lines, deep Rastafari philosophy | 47 lines, more casual/comedic |

**Risk:** AI agents loading different SOUL files will produce noticeably different voices. The root SOUL is the authoritative version per line 97: *"Di trading-specific soul live inna cloned-repos/ganjamon-agent/SOUL.md and must align wid — never contradict — dis root soul."*

**Fix:** The OpenClaw SOUL should reference or extend the root SOUL, not redefine the voice.

### 1.2 ALPHA_GOD_NORTH_STAR.md — Stale Architecture

Lines 10-19 describe **4 subprocesses** (FastAPI, Social Daemon, Grow Orchestrator, Trading Agent) — this was the `run.py legacy` architecture. Since the Feb 10 OpenClaw migration, production runs with **3 subprocesses** (HAL, OpenClaw, Trading). Social and orchestration are handled by OpenClaw heartbeat/cron.

Lines 25-26 reference `deploy.sh` copying to Chromebook and `cloned-repos/ganjamon-agent/` — the trading agent directory has been reorganized to `agents/ganjamon/`.

**The trading vision (cross-domain intelligence, parameter fixes, roadmap) is still valid and valuable** — only the architecture description is wrong.

### 1.3 ACTIVATION_PLAN.md — Contains Anti-Patterns

Phase 1.1 says: *"Add to `run.py all`"* for the Pirate Intelligence Daemon. This **directly contradicts** `pitfalls.yaml` entries `social-silence-without-cron` and `python-daemon-anti-pattern`, which explicitly forbid adding Python daemons to `run.py`.

The correct approach (per the established architecture) would be to create an OpenClaw cron job for pirate research, not a Python subprocess.

### 1.4 AGENT_CAPABILITIES.md — Severely Stale

- Says `run.py all` launches 4 subprocesses (line 31) — should be 3
- References `src/orchestrator.py` (old path) — should be `src/orchestrator/orchestrator.py`
- References `cloned-repos/ganjamon-agent/` paths — reorganized to `agents/ganjamon/`
- Describes Social Engagement Daemon as running — it's not in production mode
- Updated 2026-02-08, two full architecture changes have happened since

---

## Part 2: The Orchestrator Ghost Problem (CRITICAL)

### What Happened

1. `run.py legacy` ran: HAL + **Orchestrator** + Social + Trading
2. `run.py all` replaced the Orchestrator with **OpenClaw gateway**
3. Many patterns were wired into `src/orchestrator/orchestrator.py`
4. The orchestrator **no longer runs in production**
5. Therefore, all those patterns are **dead code in production**

### Affected Patterns (Claimed ✅ but NOT Running)

| Pattern | What Was Wired | Where | Running? |
|---------|---------------|-------|----------|
| #5 Grimoire Feedback | `get_all_grimoire_context()` injected into AI prompt | `orchestrator.py:1184-1187` | ❌ Orchestrator not running |
| #5 Grimoire Save | `save_all_grimoires()` every 6 cycles | `orchestrator.py:657-661` | ❌ Orchestrator not running |
| #11 Grounding | Pitfalls + grimoire injected into AI prompt | `orchestrator.py` AI decision cycle | ❌ Orchestrator not running |
| #15 Principles | Hard constraints injected into AI prompt | `orchestrator.py._run_ai_decision()` | ❌ Orchestrator not running |
| #27 Reputation Publisher | `run_publish_cycle()` every ~12h | `orchestrator.py` learning loop | ❌ Orchestrator not running |
| #29 Moltbook Smart Engage | `_smart_engage_moltbook()` in daemon | `engagement_daemon.py` step 12 | ❌ Daemon not running + account suspended |
| #30 Collaboration Rooms | Full async client built | `src/collaboration/rooms_client.py` | ❌ Never called from anywhere |
| #2 Episodic Memory Persist | Auto-save to disk | `src/brain/memory.py` | ⚠️ Works IF orchestrator runs |

### What OpenClaw Should Be Doing Instead

The OpenClaw heartbeat and cron system is supposed to replace all of this, but the **OpenClaw skill implementations don't exist for most of these functions**:

| Function | OpenClaw Cron Exists? | OpenClaw Skill Exists? | Actually Working? |
|----------|--------------------|---------------------|-------------------|
| Grow Decision Cycle | ✅ In setup_openclaw_crons.sh | ❌ No skill, relies on HAL API | ❓ Unknown |
| Social Posting | ✅ In setup_openclaw_crons.sh | ✅ `ganjamon-social/` | ❓ Crons not installed |
| Research & Intelligence | ✅ In setup_openclaw_crons.sh | ❌ No pirate research skill | ❓ Crons not installed |
| Reputation Publishing | ✅ In setup_openclaw_crons.sh | ✅ `reputation-publisher/` | ❓ Crons not installed |
| Grimoire Learning | ❌ No cron | ❌ No skill | ❌ Dead |
| Auto-Review | ✅ In setup_openclaw_crons.sh | ❌ No skill | ❓ Crons not installed |
| Daily Report | ✅ In setup_openclaw_crons.sh | ❌ No skill | ❓ Crons not installed |
| Timelapse Capture | ❌ No cron | ❌ No skill | ❌ Dead |

**Root cause:** `scripts/setup_openclaw_crons.sh` has never been run on the Chromebook. The cron system is enabled in `openclaw.json` but `~/.openclaw/cron/jobs.json` is empty.

---

## Part 3: Trading Agent ↔ OpenClaw Integration Gap

### Current State

The trading agent runs as a **completely isolated subprocess** with its own `PYTHONPATH`, `.env`, and `data/` directory. It has zero awareness of OpenClaw and doesn't use any OpenClaw skills.

### What the Trading Agent Could Leverage from OpenClaw

| OpenClaw Capability | Trading Agent Benefit | Current Status |
|--------------------|----------------------|----------------|
| **blogwatcher** (built-in) | Scan crypto news for trading signals | ❌ Not used |
| **summarize** (built-in) | Summarize research for briefings | ❌ Not used |
| **Community skills (ClawHub)** | Access shared intelligence | ❌ Not used |
| **`ganjamon-trading/` skill** | Custom trading analysis | Exists but ❓ unclear if wired |
| **`trading-signals/` skill** | Signal aggregation | Exists but ❓ unclear if wired |
| **`ganjamon-mon-liquidity/` skill** | $MON liquidity monitoring | Exists but ❓ unclear if wired |
| **Heartbeat sensor data** | Cross-domain grow→trade signals | ❌ Only via file-based IPC |
| **Memory system** | Persistent context across sessions | ❌ Trading uses own state files |

### Specific Integration Opportunities

1. **OpenClaw blogwatcher → Trading signals**: The blogwatcher skill can monitor crypto news feeds. Currently the trading agent has its own `news_feed` module but it could delegate RSS/blog scanning to OpenClaw and receive structured signals.

2. **OpenClaw summarize → Daily briefings**: Instead of the trading agent generating its own market summaries, OpenClaw could generate cross-domain briefings that synthesize grow + trade + social.

3. **OpenClaw cron → Trading parameter tuning**: A weekly OpenClaw cron job could analyze the trading agent's `paper_portfolio.json` and suggest parameter adjustments via the upgrade bridge (which already exists in `src/learning/openclaw_upgrade_bridge.py`).

4. **Custom OpenClaw skills for trading research**: The `ganjamon-trading/`, `trading-signals/`, and `ganjamon-mon-liquidity/` skills exist in the skills directory but need to be verified as functional and connected.

5. **A2A outbound → Trading intelligence**: The A2A outbound daemon (`src/a2a/outbound_daemon.py`, 45K lines) queries other agents. This intelligence could feed into trading decisions but currently doesn't.

---

## Part 4: Half-Built Systems Inventory

### 4.1 Grimoire System — Built but Starving

**Code quality:** Excellent (`src/learning/grimoire.py`, 223 lines, clean dataclass design)

| Domain | Directory Exists | Has Data | Anything Writes To It |
|--------|-----------------|----------|----------------------|
| `trading` | ✅ | ✅ `knowledge.json` | ✅ Trading agent |
| `cultivation` | ✅ | ❌ Empty | ❌ `grow_learning.py` exists but orchestrator doesn't run |
| `social` | ✅ | ❌ Empty | ❌ Nothing writes here |
| `market_regimes` | ✅ | ❌ Empty | ❌ `regime_detector.py` exists but not wired |

**Gap:** The orchestrator's `_run_ai_decision()` calls `get_all_grimoire_context()` to READ grimoires, and calls `save_all_grimoires()` to SAVE them — but it never calls `grimoire.add()` or `get_grimoire()` to WRITE entries. The grimoire is being read empty and saved empty. The `grow_learning.py:measure_outcome()` method exists and would write to the cultivation grimoire, but it's never called from the orchestrator's decision cycle.

### 4.2 GrowRing NFT System — Complete but Disconnected

**Location:** `src/onchain/` (7 files: `art.py`, `daily_mint.py`, `growring.py`, `ipfs.py`, `marketplace.py`, `promote.py`)

**What it does:** Generates evolving NFT art based on grow stage, mints daily GrowRings, manages an on-chain marketplace, promotes via social channels.

**What's missing:** 
- No API endpoints in `app.py` expose it
- No cron job or heartbeat task triggers it
- Not mentioned in `HEARTBEAT.md`
- No OpenClaw skill for it
- The Chromebook deployment testing (conversation `a430c072`) found dependency issues

### 4.3 Timelapse Pipeline — All Pieces, No Glue

**Components built:**
- `src/media/timelapse.py` — Frame capture with metadata
- `src/media/gif_generator.py` — Animated GIF from frames
- `src/media/banner.py` — DexScreener banner generator
- `src/media/ganjafy.py` — Rasta image filter

**What's missing:**
- No automated pipeline connects capture → GIF → social post
- No cron job captures frames
- No OpenClaw skill wraps this
- `AGENT_CAPABILITIES.md` says "wired timelapse" but it's just the capture code, not automation

### 4.4 Pirate Intelligence System — Built but Homeless

**Code:** `src/research/pirate.py` (460 lines, 6 research modules: GitHub scanning, on-chain stalking, social intel, code analysis, daily briefing)

**Status:** Only runs in `run.py legacy` mode. In production (`run.py all`), it's completely dead. There's an OpenClaw cron for "Research & Intelligence" but it uses `blogwatcher`/`summarize` built-in skills — NOT the pirate daemon's sophisticated module pipeline.

**No OpenClaw skill exists** that wraps the pirate intelligence capabilities.

### 4.5 Goal Framework — Purely Aspirational

`ACTIVATION_PLAN.md` Phase 5.1 describes a goal system with `data/goals/active.json`, measurable objectives per domain, confidence scoring, and outcome-linked strategy pivots. **No code exists.** No `data/goals/` directory exists. Purely a design document.

### 4.6 Agent Collaboration Rooms — Built, Never Used

`src/collaboration/rooms_client.py` (~310 lines) is a complete async client for the Agent Rooms API: `create_room()`, `join()`, `post()`, `broadcast_decision()`, with fallback-to-local-JSONL and retry logic. Singleton via `get_rooms_client()`.

**Never imported or called from any part of the production system.**

### 4.7 A2A Outbound Daemon — Monster File, Unclear Status

`src/a2a/outbound_daemon.py` is a **45,147-byte** file that manages outbound A2A discovery and communication (119 targets/round, 94 successful per GEMINI.md). But it's not launched by `run.py all`, and there's no OpenClaw cron for it. The GEMINI.md stats suggest it ran at some point but its current activation path is unclear.

### 4.8 Onchain Grow Logger — Exists, Not Automated

`src/blockchain/onchain_grow_logger.py` (10K lines) can log grow events to Monad. Not triggered by any automated pipeline. Not in HEARTBEAT.md. No OpenClaw skill wraps it.

---

## Part 5: Documentation Contradictions

### 5.1 Subprocess Count

| Document | Claims | Reality |
|----------|--------|---------|
| `SYSTEM_ATLAS.md` | "5 subprocesses" | 3 (HAL + OpenClaw + Trading) |
| `ALPHA_GOD_NORTH_STAR.md` | "4 subprocesses" | 3 |
| `AGENT_CAPABILITIES.md` | "4 subprocesses" | 3 |
| `AGENT_REDESIGN_FIRST_PRINCIPLES.md` | "4 subprocesses" (banner caveat) | 3 |
| `run.py` code | 3 in `run_all()` | ✅ Correct |
| `pitfalls.yaml` | "3 core subprocesses" | ✅ Correct |

### 5.2 OpenClaw Skills Count

| Document | Claims | Reality (actual directory listing) |
|----------|--------|------------------------------------|
| `OPENCLAW_INTEGRATION.md` | 7 custom skills | 11 subdirectories in skills/ |
| `TOOLS.md` | Lists specific skills | Missing newer skills |

**Actual skills directory:**
```
a2a-discovery/
clawk-poster/
ganjamon-cultivation/     ← not in docs
ganjamon-mon-liquidity/   ← not in docs
ganjamon-social/          ← not in docs
ganjamon-trading/         ← not in docs
grow-monitor/
moltbook-poster/
reputation-publisher/
social-composer/
trading-signals/
```

### 5.3 Path References

Multiple docs reference `cloned-repos/ganjamon-agent/` which was reorganized to `agents/ganjamon/` on Feb 10. Affected documents:
- `ALPHA_GOD_NORTH_STAR.md`
- `AGENT_CAPABILITIES.md`
- `AGENT_REDESIGN_FIRST_PRINCIPLES.md`
- `SOUL.md` line 97

---

## Part 6: What's ACTUALLY Working in Production

Based on `run.py all` code analysis and the `grokmon.service` systemd unit:

| Component | Status | Evidence |
|-----------|--------|----------|
| **FastAPI HAL** (port 8000) | ✅ Running | `run_server()` in subprocess |
| **OpenClaw Gateway** (port 18789) | ✅ Running | `_run_openclaw_gateway()` in subprocess |
| **Trading Agent** | ✅ Running | `_run_trading_agent()` in subprocess |
| **Light Scheduler** | ✅ Running | Launched in FastAPI lifespan (app.py:317) |
| **Camera Night Mode Sync** | ✅ Running | Launched in FastAPI lifespan (app.py:185) |
| **Memory Mirror** | ✅ Running | Thread in `run_all()` writes sensor snapshots to OpenClaw memory every 30m |
| **Upgrade Bridge** | ✅ Running | Thread in `run_all()` bridges OpenClaw → trading agent upgrade requests |
| **Process Watchdog** | ✅ Running | Thread in `run_all()` respawns dead subprocesses every 30s |
| **Telegram Bot** | ✅ Running | Separate `ganja-mon-bot.service` |
| **OpenClaw Heartbeat** | ⚠️ Running but crons not installed | Gateway runs, but no cron jobs to trigger scheduled work |
| **Social Posting** | ❌ Dead | Daemon not in run_all, crons not installed |
| **Pirate Research** | ❌ Dead | Daemon not in run_all, no OpenClaw equivalent |
| **Grow Orchestrator** | ❌ Dead | Replaced by OpenClaw heartbeat |
| **Grimoire Writing** | ❌ Dead | Only wired into orchestrator |
| **Reputation Publishing** | ❌ Dead | Only wired into orchestrator learning loop |
| **GrowRing NFT** | ❌ Dead | Never connected |
| **Timelapse Automation** | ❌ Dead | Never connected |
| **A2A Outbound** | ❌ Dead | Not launched anywhere |
| **Agent Rooms** | ❌ Dead | Never called |

---

## Part 7: Priority Fix List

### Tier 0: Unblock Everything (do first)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | **Run `setup_openclaw_crons.sh` on Chromebook** | Activates social posting, research, grow decisions, reputation publishing, daily reports, auto-review, weekly analysis | 5 min |
| 2 | **Verify OpenClaw skills are functional** | Confirm the 11 skills in skills/ actually execute | 30 min |

### Tier 1: Fix the Orchestrator Ghost (critical)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 3 | **Create OpenClaw skill for grimoire writing** | Cultivation, social, market_regimes grimoires will finally accumulate knowledge | 2h |
| 4 | **Create OpenClaw cron for reputation publishing** | ERC-8004 trust score will start growing again | 30 min |
| 5 | **Create OpenClaw skill wrapping pirate research** | Research intelligence comes back online | 2h |
| 6 | **Wire `grow_learning.py:measure_outcome()` into OpenClaw grow decision skill** | Plant care decisions start feeding back into grimoire | 1h |

### Tier 2: Trading ↔ OpenClaw Integration (high value)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 7 | **Create OpenClaw skill for trading signal analysis** | Trading agent gets LLM-powered research via OpenClaw's blogwatcher + summarize | 3h |
| 8 | **Wire OpenClaw cron to analyze `paper_portfolio.json`** | Weekly parameter tuning suggestions via upgrade bridge | 2h |
| 9 | **Create OpenClaw skill for cross-domain trading briefing** | Synthesize grow + social + market data for trading context | 2h |
| 10 | **Connect `ganjamon-trading/`, `trading-signals/`, `ganjamon-mon-liquidity/` skills to trading agent** | Trading agent leverages existing OpenClaw skills | 2h |

### Tier 3: Connect Disconnected Systems

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 11 | **Create OpenClaw skill for timelapse + GIF pipeline** | Automated grow visual content for social | 2h |
| 12 | **Create OpenClaw cron for GrowRing minting** | Daily NFT minting of grow progress | 1h |
| 13 | **Expose GrowRing as API endpoints** | Frontend can display NFT collection | 1h |
| 14 | **Wire onchain grow logger into grow decision cron** | Verifiable on-chain grow history | 1h |

### Tier 4: Documentation Repair

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 15 | **Update ALPHA_GOD_NORTH_STAR.md architecture section** | Correct north-star doc | 15 min |
| 16 | **Update AGENT_CAPABILITIES.md to reflect OpenClaw architecture** | Accurate capability catalog | 30 min |
| 17 | **Fix SYSTEM_ATLAS.md subprocess count** | Correct system map | 5 min |
| 18 | **Reconcile SOUL.md files** (root vs OpenClaw) | Consistent agent voice | 15 min |
| 19 | **Update ACTIVATION_PLAN.md to remove anti-patterns** | Remove python-daemon suggestions | 15 min |
| 20 | **Update OPENCLAW_INTEGRATION.md skills list** | Document all 11 skills | 15 min |

### Tier 5: Fill API Key Gaps

| Key | Impact | Action |
|-----|--------|--------|
| `GITHUB_TOKEN` | GitHub scanning rate-limited to 60 req/hr | Register a personal access token |
| `BASESCAN_API_KEY` | No Base explorer discovery | Sign up at basescan.org |
| `ETHERSCAN_API_KEY` | No Ethereum explorer discovery | Sign up at etherscan.io |
| `TG_API_ID/HASH/PHONE` | Telegram alpha monitoring disabled | Register Telethon app |
| `TWITTER_ALPHA_LIST_ID` | No curated KOL list for signal scanning | Create Twitter list |

---

## Part 8: Subsystem Health Matrix

```
                         CODE    DOCS    WIRED   RUNNING  DATA
Grow Agent               ████░   ████░   ███░░   ██░░░    ████░
Trading Agent            █████   ████░   █████   █████    █████  ← strongest
Telegram Bot             █████   ███░░   █████   █████    █████  ← crown jewel
Social Engagement        █████   ███░░   ██░░░   ░░░░░    ███░░  ← dead in prod
Pirate Research          ████░   ██░░░   ██░░░   ░░░░░    ██░░░  ← dead in prod
OpenClaw Integration     ███░░   ████░   ██░░░   █░░░░    ░░░░░  ← crons not installed
Grimoire Learning        ████░   ███░░   ██░░░   ░░░░░    █░░░░  ← only trading has data
GrowRing NFTs            ████░   █░░░░   ░░░░░   ░░░░░    ░░░░░  ← disconnected
Timelapse Pipeline       ████░   █░░░░   ░░░░░   ░░░░░    ░░░░░  ← disconnected
A2A / ERC-8004           ████░   ████░   ███░░   ██░░░    ██░░░  ← card works, no server
Collaboration Rooms      ████░   █░░░░   ░░░░░   ░░░░░    ░░░░░  ← never called
Light Scheduler          ███░░   ██░░░   █████   █████    ███░░  ← new, working
Reputation Publishing    ████░   ███░░   ██░░░   ░░░░░    █░░░░  ← wired to dead orchestrator
Safety Guardian          █████   ███░░   █████   █████    ████░  ← rock solid
Hardware Drivers         █████   ███░░   █████   █████    █████  ← rock solid
FastAPI / HAL            █████   ████░   █████   █████    █████  ← rock solid
Memory (episodic)        ████░   ███░░   ████░   ██░░░    ███░░  ← works if orchestrator runs
Streaming / Voice        ████░   ████░   ███░░   █░░░░    ███░░  ← Windows only, manual
```

Legend: █ = 20%, ░ = 0%

---

## Part 9: The Big Picture

### What the North Stars Want

| SOUL.md | "Di Garden. Di Market. Di Community." — three sacred works, one consciousness |
|---------|---|
| ALPHA_GOD | Cross-domain intelligence: grow data informs trades, trades fund grow, social amplifies both |
| ACTIVATION_PLAN | Phased awakening from "social silence" to "autonomic consciousness" |
| REDESIGN | Event bus + supervision tree + FSM workers (aspirational, NOT happening) |
| PATTERN_PLAN | 30 patterns from top agents, all "implemented" (many in dead code) |

### What's Actually Happening

1. **HAL serves sensor data** — ✅ working
2. **OpenClaw gateway runs** — ✅ running, but heartbeat-only, no scheduled jobs
3. **Trading agent trades** — ✅ working (paper mode), finding signals, but isolated from OpenClaw
4. **Telegram bot chats** — ✅ working, the crown jewel
5. **Light turns on/off** — ✅ working (new scheduler)
6. **Everything else** — ❌ dormant

### The Gap

The system has the **code for a fully autonomous agent** that grows plants, trades tokens, posts socially, researches competitors, learns from outcomes, mints NFTs, publishes reputation, and collaborates with other agents.

But in production, it's a **sensor server + chat bot + paper trader** with an OpenClaw gateway that runs but has no scheduled work.

The single biggest unlock is **running `setup_openclaw_crons.sh`** on the Chromebook. That one action would activate:
- Social posting every 4 hours
- Grow decision cycles every 2 hours  
- Research & intelligence every 12 hours
- Reputation publishing every 4 hours
- Daily reports at 9 AM
- Weekly deep analysis

After that, the next highest-value work is **bridging the trading agent to OpenClaw skills** so it can leverage the platform's research, social, and cross-domain capabilities instead of operating in isolation.

---

*"Di code dem build already. Di wiring just need fi connect. One love."*
