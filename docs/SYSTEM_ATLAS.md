# Grok & Mon System Atlas

## Scope
This document is the deep-dive map of the **core Grok & Mon system** (plant ops, web/API, social, hardware, MCP tools, and deployment). Subrepos and large cloned stacks are documented in `docs/SYSTEM_ATLAS_SUBREPOS.md`.

## Reality Check (What Is Live)
- Production system is described as **LIVE** in `SYSTEM_OVERVIEW.md`.
- Two-machine setup is **required** (Windows for dev/streaming/voice; Chromebook for plant ops). See `CLAUDE.md`.
- **Unified agent** (2026-02-11): `run.py all` launches **3 subprocesses** — FastAPI (HAL), OpenClaw gateway (primary AI orchestrator), trading agent. Plus 3 helper threads (memory mirror, upgrade bridge, watchdog). One service (`grokmon.service`), one heartbeat. `ganjamon-agent.service` is DISABLED (merged). Grow orchestrator, social posting, and research are replaced by OpenClaw heartbeat + cron jobs (see `scripts/setup_openclaw_crons.sh`). Social/pirate Python daemons are **legacy** and do NOT run in `run.py all` mode.
- **OpenClaw startup delay** (2026-02-10): OpenClaw waits `OPENCLAW_START_DELAY_SECONDS` (default 60s) after HAL+trading start, and runs at nice +10 (`OPENCLAW_NICE`), to prevent boot-time CPU saturation that kills SSH.
- **Resource hardening** (2026-02-10): `kiosk.service` (Chrome HUD) and `retake-stream.service` (ffmpeg RTMP) are **DISABLED** on boot. Together they consumed 1.2 GB + 100% CPU on a 3.7 GB machine. Website plant cam still works via `/api/webcam/latest` (no ffmpeg needed). `earlyoom` installed to prevent OOM freezes.
- **Codebase reorganization** (2026-02-10): Root cleaned from 316→24 files. Trading agent promoted from `cloned-repos/ganjamon-agent/` → `agents/ganjamon/`. Farcaster agent from `cloned-repos/farcaster-agent/` → `agents/farcaster/`. Centralized path module at `src/core/paths.py`. Chromebook deployed with symlinks preserving production data.
- **IMPORTANT**: The trading agent subprocess runs `python -m main` inside `agents/ganjamon/` with **isolated PYTHONPATH**. It has its own `.env`, its own `data/` directory, and its own dependencies. `deploy.sh` does NOT deploy it. Use `deploy_agent.sh` instead (see Deployment section below).

## Framework Strategy: OpenClaw-First

**Target architecture:** All AI-driven capabilities run as OpenClaw skills. Python `src/` serves as the Hardware Abstraction Layer (HAL) — hardware I/O, FastAPI endpoints, safety guardrails, database ops.

| Domain | Status | Where |
|--------|--------|-------|
| Grow orchestration | ✅ Migrated | OpenClaw heartbeat + `HEARTBEAT.md` |
| Social posting | ✅ Migrated | `moltbook-poster`, `clawk-poster`, `tweeter`, `clawcast` skills |
| Content generation | ✅ Migrated | `gemini` + `social-composer` + `nano-banana-pro` skills |
| Research | ✅ Migrated | `blogwatcher` + `summarize` + `alpha-finder` skills |
| Email | ✅ Migrated | `himalaya` skill |
| Self-improvement | ✅ Migrated | `coding-agent` + `ralph-loop-writer` skills |
| Trading signals | ✅ Skill exists | `trading-signals` + `ganjamon-trading` custom skills |
| A2A / reputation | ✅ Skill exists | `a2a-discovery` + `reputation-publisher` custom skills |
| Hardware I/O | ⬜ Stays Python | `src/hardware/` (sensors, actuators, camera) |
| FastAPI / Admin API | ⬜ Stays Python | `src/api/` (82+ endpoints) |
| Safety guardrails | ⬜ Stays Python | `src/safety/guardian.py` |
| Database ops | ⬜ Stays Python | `src/db/` |

**Preference hierarchy for new features:** OpenClaw built-in skill > Community skill (ClawHub) > Custom skill > Python `src/` code.
**Full reference:** `docs/OPENCLAW_INTEGRATION.md`

## Machines & Roles (Critical)
- **Windows laptop** (`C:\Users\natha\sol-cannabis`): development, streaming, Rasta voice pipeline.
- **Chromebook server** (`natha@chromebook.lan`): plant ops, sensors, FastAPI, orchestrator, webcams.
- **Rule:** Rasta voice runs **only on Windows** (`rasta-voice/`). Do not deploy it to Chromebook.

### Chromebook Path Mapping (CRITICAL)

| Component | Windows Path | Chromebook Path | Notes |
|-----------|-------------|----------------|-------|
| **Project root** | `C:\Users\natha\sol-cannabis` | `/home/natha/projects/sol-cannabis` | |
| **Grow system** | `sol-cannabis\src\` | `.../src/` | |
| **Trading agent** | `sol-cannabis\agents\ganjamon\` | `.../agents/ganjamon/` | **NEW** (was `cloned-repos/ganjamon-agent/`) |
| **Trading agent data** | `agents\ganjamon\data\` | `.../agents/ganjamon/data/` | Chromebook: symlink → `cloned-repos/ganjamon-agent/data/` |
| **Farcaster agent** | `sol-cannabis\agents\farcaster\` | `.../agents/farcaster/` | **NEW** (was `cloned-repos/farcaster-agent/`) |
| **Grow data** | `sol-cannabis\data\` | `.../data/` | |
| **Ralph loop** | `agents\ganjamon\.ralph\` | `.../agents/ganjamon/.ralph/` | Chromebook: symlink → `cloned-repos/ganjamon-agent/.ralph/` |
| **Centralized paths** | `sol-cannabis\src\core\paths.py` | `.../src/core/paths.py` | Import: `from src.core.paths import PROJECT_ROOT, AGENT_DIR` |

> ⚠️ **Common mistake**: The Chromebook path is `/home/natha/projects/sol-cannabis/`, NOT `/home/natha/sol-cannabis/`. The old `/home/natha/projects/ganjamon-agent/` is a legacy personality-only directory — do NOT deploy there.
>
> ⚠️ **Post-reorg**: On the Chromebook, `agents/ganjamon/{data,.env,src,venv,main,.ralph}` are symlinks to `cloned-repos/ganjamon-agent/` to preserve production state. The `cloned-repos/` originals are kept as the canonical data source.

## Runtime Entry Points
- `run.py`
  - `python run.py all` — **Production mode**: launches 3 subprocesses (FastAPI HAL, OpenClaw gateway, trading agent) + helper threads (memory mirror, upgrade bridge, watchdog). Social posting, research, and all scheduled activities run through **OpenClaw cron jobs** inside the gateway — NOT as Python daemons.
  - `python run.py server` — FastAPI only.
  - `python run.py orchestrator` — Grow orchestrator only.
- `run.sh`
  - Legacy convenience wrapper for archived `src.brain.agent_legacy` with mock or hardware modes.
- `systemd/grokmon.service`
  - User service for Chromebook (`ExecStart=... python run.py all`). Unified agent.
- `systemd/ganja-mon-bot.service`
  - Telegram community bot (separate service, stays independent).
- `systemd/kiosk.service`
  - Chrome kiosk showing HUD on local display. **DISABLED** (2026-02-10) — saves 1.1 GB RAM + 67% CPU. HUD accessible remotely via browser.
- `systemd/retake-stream.service`
  - ffmpeg RTMP stream to RetakeTV. **DISABLED** (2026-02-10) — saves 104 MB + 31% CPU. Only needed when live streaming; website cam uses `/api/webcam/latest` directly.
- `docker-compose.yml`
  - Optional containerized stack: EMQX MQTT, FastAPI backend, optional frontend, optional InfluxDB+Grafana.

## High-Level Architecture
- **Edge:** Cloudflare DNS, Bot Fight Mode, Worker caching, A2A/MCP endpoints.
- **Server:** FastAPI + SQLite + hardware drivers (82+ endpoints).
- **Unified Agent:** 3 subprocesses — FastAPI (HAL), OpenClaw gateway (primary orchestrator), trading agent. Social, research, and all scheduled activities are **OpenClaw cron jobs** (not Python daemons). Helper threads: memory mirror, upgrade bridge, proc watchdog.
- **Grow:** Grok AI decision loop + 14 tools + SafetyGuardian + hippocampus memory (importance/decay/reinforcement) + grimoire + pitfalls + principles + auto-review. Code: `src/orchestrator/orchestrator.py`.
- **Trading:** 33 signal source modules, multi-chain execution, 38 learning modules, profit allocation. Code: `agents/ganjamon/src/`. Runs in **isolated subprocess** with own PYTHONPATH.
- **Social:** Engagement daemon (10 loops, 6+ platforms), anti-robot humanization, scheduler. Code: `src/social/`.
- **Frontend:** static HTML/CSS/JS (`src/web/`, `pages-deploy/`).
- **Token/chain:** Monad + LFJ Token Mill + ERC-8004 Agent #4 + Wormhole NTT bridge.

## Core Modules (src/)

### `src/orchestrator/`
- **Package** (2026-02-10 reorg): `orchestrator.py` and `orchestrator_resilient.py` moved from loose `src/` files into `src/orchestrator/` package.
- `__init__.py` re-exports `GrokMonOrchestrator` for backward compatibility.
- Main control loop: polls sensors, logs to DB, runs Grok decisions on a schedule, executes actions through safety guardrails.
- Initializes hardware hubs (Govee, Kasa, Tapo, Ecowitt), webcam, safety guardian, tool executor, and Grok brain.
- Learning loop (~30min cadence): grimoire saves (3h), grow pattern extraction (6h), reputation publishing (12h).

### `src/core/paths.py`
- **Centralized path module** (2026-02-10): single source of truth for all directory paths.
- Exports: `PROJECT_ROOT`, `SRC_DIR`, `DATA_DIR`, `AGENT_DIR`, `TRADING_AGENT_DIR`, `TRADING_DATA`, `FARCASTER_AGENT_DIR`, `OPENCLAW_DIR`, `SCRIPTS_DIR`, `CONFIG_DIR`, `DOCS_DIR`.
- Supports `GROKMON_ROOT` env var override for non-standard installations.

### `src/brain/`
- `agent_legacy.py`: **ARCHIVED** (2026-02-08). Was `agent.py`. Legacy standalone Grok decision loop. Not used in production.
- `memory.py`: Hippocampus-style episodic memory — importance auto-scoring (0.4-0.9 based on action type), exponential decay (`(1-0.01)^hours`), access-based reinforcement, smart trimming (importance > recency). Persists to `data/episodic_memory.json`.
- `unified_context.py`: cross-system awareness aggregator (wired into orchestrator).
- `prompts/system_prompt.md`: primary system prompt for Grok.

### `src/ai/`
- Grok brain + vision analysis integration (see `src/ai` module usage in orchestrator and API).

### `src/api/`
- `app.py`: FastAPI app and endpoints. Uses hardware hubs or mock fallbacks. Includes camera retry logic and night mode syncing.
- `auth.py`: JWT auth and admin gating.
- `transparency.py`: audit/transparency logging hooks (imported by the agent when available).

### `src/hardware/`
- Govee sensors (`govee.py`), Kasa/Tapo actuators (`kasa.py`, `tapo.py`), Ecowitt soil (`ecowitt.py`).
- `webcam.py`: USB and IP camera handling, night vision mode.
- `soil_sensor.py`: ESP32 soil hub integration.
- `mock.py`: mock sensor/actuator implementations.

### `src/cultivation/`
- VPD calculations, growth stage parameters, and stage logic.

### `src/db/`
- SQLite schema, repository layer, initialization, setpoints.
- Data logged from sensors, AI decisions, and device states.

### `src/mcp/`
- `tools.py`: Model Context Protocol tool schemas and handlers for grow control.
- Includes validation, setpoint comparisons, MQTT publishes when available.

### `src/learning/openclaw_upgrade_bridge.py`
- **OpenClaw → Ralph bridge** (2026-02-10): deterministic daemon thread that scans OpenClaw memory files for `UPGRADE_REQUEST_JSON: {...}` lines and feeds them into `agents/ganjamon/data/upgrade_requests.json` via `UpgradeSystem`.
- Offset-based scanning (never reprocesses old lines), no LLM calls.
- State persisted in `data/openclaw_upgrade_bridge_state.json`.

### `src/social/`
- Engagement daemon (`engagement_daemon.py`): 10 concurrent loops across 6+ platforms. Launches as subprocess in `run_all()` alongside OpenClaw — handles actual platform API calls while OpenClaw handles high-level orchestration.
- Twitter client (`twitter.py`) + xAI helper (`xai_native.py`).
- Social manager and scheduler (`manager.py`, `scheduler.py`).
- Anti-robot humanization (`anti_robot.py`): jitter, frequency modulation, organic closers.
- Social tracker (`../learning/social_tracker.py`): per-platform engagement metrics.

### `src/telegram/`
- Telegram bot, persona, and community knowledge integration.

### `src/notifications/`
- Alert routing to Telegram/Discord/webhooks and other channels.

### `src/web/`
- Static pages (`index.html`, `dashboard.html`, `bridge.html`, etc.).
- Assets (logos/banners), playlist and skins.

### `src/media/`
- Timelapse and media generation utilities.

### `src/mqtt/`
- MQTT topics and service layer (used by MCP and optional infra).

### `src/payments/`
- Profit splitter (`splitter.py`): 60/25/10/5 allocation with batch API.
- Approval gate (`approval_gate.py`): Telegram approval for large amounts.

### `src/review/`
- Auto-review engine (`engine.py`): compliance grading every ~6h.
- Analyzers (`analyzers.py`): compliance, decision quality, patterns, optimization.
- Visual analyzer (`visual.py`): Grok vision plant health audits.

### `src/mailer/`
- Email client (`client.py`): outbound via Resend API (agent@grokandmon.com).
- Inbox handler (`inbox.py`): webhook for inbound email classification + auto-reply.

### `src/core/`
- Events (`events.py`): async event bus for cross-module communication.
- Circuit breakers (`circuit_breaker.py`): fault tolerance for hardware/API calls.
- Watchdog (`watchdog.py`): component heartbeat monitoring.
- Supervisor (`supervisor.py`): task restart policies.
- Health (`health.py`): `/api/health` and `/api/ready` endpoints.

### `src/analytics/`
- Stability calculator (`stability.py`): sensor stability scoring from DB data.

### `src/collaboration/`
- `rooms_client.py`: Async Python client for OpenClaw Agent Rooms API (room CRUD, messaging, tasks).
- `broadcast_decision()`: formats AI grow decisions for room broadcasting.
- Graceful fallback to local JSONL (`data/rooms_fallback/`) when server is unreachable.
- Singleton via `get_rooms_client()`.

### `src/voice/`
- `manager.py`: Rasta voice pipeline manager (Windows only).
- `personality.py`: `get_soul_identity()` loads SOUL.md for AI persona injection.

## Data & Storage

**TWO data directories** (cross-domain intelligence reads both):

| Directory | Written By | Key Files |
|-----------|-----------|----------|
| `sol-cannabis/data/` | Orchestrator, social daemon, API | `grokmon.db`, `last_sensors.json`, `engagement_state.json`, `farcaster_state.json`, `episodic_memory.json` |
| `agents/ganjamon/data/` | Trading agent subprocess | `paper_portfolio.json`, `unified_brain_state.json`, `observations.json`, `experience.db`, `macro_state.json` |

> On Chromebook, `agents/ganjamon/data/` is a symlink to the canonical `cloned-repos/ganjamon-agent/data/`.

- `config/` contains `principles.yaml` (15 agent constraints, 11 hard/4 soft), `pitfalls.yaml` (10 machine-readable gotchas), `hardware.yaml`, and grow profiles.
- `output/` used by image pipelines and exports.
- Logs are written to JSONL and persisted memory files.

## Hardware Topology (Summarized)
- Govee sensors: temp/humidity, CO2, humidifier control.
- Kasa smart plugs: exhaust, circulation, pump, CO2 solenoid.
- Tapo plug: grow light power.
- Ecowitt GW1100 + WH51 probes for soil moisture.
- USB webcam + optional IP camera.

## Web + Edge
- `cloudflare/workers/`: Cloudflare Worker scripts (moved from root 2026-02-10).
- `cloudflare/*.toml`: Cloudflare worker deployment configs (moved from root 2026-02-10).
- `pages-deploy/`: static site deployment build outputs.

## Security & Safety
- Edge security (Cloudflare) + app-layer rate limiting and sanitization in FastAPI.
- `src/safety/guardian.py` enforces guardrails on actions.
- `SECURITY_HARDENING*.md` documents hardening steps.
- **Do not store secrets in docs or git.** Use `.env` and local secure storage.

## Token & Chain
- `src/blockchain/monad.py` integrates DexScreener + SocialScan for $MON token metrics.
- NTT bridge status in `ntt-deployment/DEPLOYMENT_STATUS.md`.

## Ops & Runbooks
- `SYSTEM_OVERVIEW.md`: production architecture and API list.
- `CHROMEBOOK_SERVER.md`: server ops and troubleshooting (avoid copying credentials).
- `STREAMING_OBS_SETUP.md`, `OBS_*` docs: OBS and streaming setup.
- `MCP_*` docs: MCP deployment and verification.

## Deployment & Sync

### Grow System (src/)
- `deploy.sh [--restart|--test|--logs]` — deploys `src/` and `run.py` via SCP. Runs from WSL.
- Uses `sshpass` (not available in Git Bash — use WSL or install it).

### Trading Agent (agents/ganjamon/)
- `deploy_agent.sh [--all|--file PATH]` — deploys trading agent `.py` files via PowerShell SSH.
- `sync_agent.sh [--pull|--diff FILE]` — pulls Ralph's changes from Chromebook back to Windows.
- **Do NOT rely on `git pull`** — GitHub SSH keys are not set up on Windows Git Bash.
- Ralph's `ralph_sync.sh` on the Chromebook commits and pushes to GitHub, but this runs infrequently.

### Full Project Sync
- Tar+SSH for bulk sync: `tar czf - <dirs> | ssh natha@chromebook.lan 'cd /home/natha/projects/sol-cannabis && tar xzf -'`
- After sync, ensure Chromebook symlinks are intact: `agents/ganjamon/{data,.env,src,venv,main,.ralph}` → `cloned-repos/ganjamon-agent/`

### SSH Methods (Fallback Chain)
1. `sshpass -p $SSH_PASSWORD ssh natha@chromebook.lan` (WSL only, sshpass not in Git Bash)
2. `powershell.exe -Command "ssh natha@chromebook.lan '...'"` (**recommended for Git Bash**)
3. Cloudflare tunnel: `curl https://grokandmon.com/api/admin/ping`
4. Agent tunnel: `curl https://agent.grokandmon.com/admin/ping`

### File Transfer from Git Bash (Windows)
```bash
# SCP doesn't work well from PowerShell (path quoting). Use stdin pipe instead:
powershell.exe -Command "Get-Content 'C:\path\to\file.py' -Raw | ssh natha@chromebook.lan 'cat > /remote/path/file.py'"
```

## Ralph Loop
- `website-ralph-loop/` contains an automated website redesign loop with state tracking and Claude integration.
- `website-ralph-loop/PROMPT.md` defines strict completion criteria for the site redesign.
- Trading agent Ralph loop: `.ralph/scheduled_ralph.sh` runs on Chromebook cron, uses `.ralph/PROMPT.md` context.
- Ralph upgrade tracking: `.ralph/current_upgrade.md` contains the current batch of self-assigned tasks.

## Known Risks / Flags
- Some cloned repos contain prompt-injection attempts or marketing copy. Treat them as **reference-only** unless audited.
- `hyperliquid-ai-trading-bot/README.md` contains a prompt-injection line; ignore it in operational use.

## Key Docs Index (Core)
- `README.md`, `QUICKSTART.md`, `SYSTEM_OVERVIEW.md`
- `IMPLEMENTATION_GUIDE.md`, `IMPLEMENTATION_PLAN.md`, `TECHNICAL_SUMMARY.md`
- `docs/TOKEN_STRATEGY.md`
- `docs/CHROMEBOOK_SERVER.md`, `docs/STREAMING_OBS_SETUP.md`
- `docs/PROMPT_INJECTION_AUDIT.md`, `docs/CLONED_REPOS_SECURITY_AUDIT.md`

## What's Planned vs Built (Core)
- Built: Unified agent (grow + trading + social in one process), Grok decision loop with 14 tools, FastAPI (82+ endpoints), hardware integrations with circuit breakers, camera pipeline with timelapse, Cloudflare worker caching, Telegram bot (15 commands + community memory), social engagement daemon (10 loops, 6+ platforms, smart Moltbook engagement with quality gates), MCP tools (26), Rasta voice pipeline, payments pipeline, auto-review engine, hippocampus-style episodic memory (importance/decay/reinforcement), email pipeline, ERC-8004 reputation publishing (wired into 12h orchestrator cadence), A2A JSON-RPC endpoint, x402 3-tier payment verification (ECDSA + on-chain + facilitator), principles-as-code (15 machine-readable constraints), pitfalls registry (10 guardrails), Agent Rooms collaboration client, PERMISSIONS.md for OpenClaw skills.
- Planned/partial: $GANJA token (agent-autonomous launch), public transparency endpoints, expanded token tooling, live trading activation, Agent Rooms deployment on Chromebook.

## Directory Structure (Post-Reorg 2026-02-10)

```
sol-cannabis/
├── agents/              # Active agent code (promoted from cloned-repos/)
│   ├── ganjamon/        # Trading agent (SOUL.md, CLAUDE.md, src/, data/)
│   └── farcaster/       # Farcaster posting agent
├── src/                 # Core Python codebase (HAL)
│   ├── core/            # paths.py, events, circuit breakers, health
│   ├── orchestrator/    # Main grow agent loop (package)
│   ├── ai/              # Grok brain + tools
│   ├── api/             # FastAPI (82+ endpoints)
│   ├── hardware/        # Sensor/actuator drivers
│   ├── telegram/        # Telegram bot
│   └── ...              # social, learning, blockchain, etc.
├── openclaw-workspace/  # OpenClaw config, skills, identity
├── openclaw/            # OpenClaw framework (upstream)
├── cloned-repos/        # Reference repos (40+, security audited)
├── scripts/             # Organized utility scripts
│   ├── obs/             # OBS scene switching
│   ├── telegram/        # Telegram utilities
│   ├── twitter/         # Twitter posting
│   ├── hardware/        # Hardware test scripts
│   └── test/            # Test/debug scripts
├── cloudflare/          # Worker scripts + wrangler configs
├── assets/screenshots/  # Historical screenshots
├── docs/                # Documentation (organized by topic)
├── config/              # principles.yaml, pitfalls.yaml, hardware.yaml
├── data/                # Grow data, sensors, engagement state
├── pages-deploy/        # Cloudflare Pages static site
└── rasta-voice/         # Rasta voice pipeline (Windows only)
```

## References to Subprojects
See `docs/SYSTEM_ATLAS_SUBREPOS.md` for:
- OpenClaw, openclaw-trading-assistant, ganjamon-agent
- Polymarket/DEX scrapers, trading bots, pumpfun/monad snipers
- Research and competitor repos used as references
