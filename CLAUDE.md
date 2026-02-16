# CLAUDE.md

## Core Policies

@.claude/rules/autonomy.md
@.claude/rules/browser-testing.md
@.claude/rules/streaming.md
@.claude/rules/twitter.md
@.claude/rules/theft.md
@.claude/rules/skills.md

## Project Overview

**Grok & Mon** is an AI-autonomous cannabis cultivation + trading agent system combining:
- **Grok AI** (xAI) for autonomous plant management decisions
- **GanjaMon Trading Agent** - Omniscient multi-chain alpha hunting agent (Moltiverse/OpenClaw hackathon, deadline Feb 15 2026)
- **Monad blockchain** for the $MON token (EVM-compatible)
- **IoT hardware** (Chromebook controller, Govee sensors, Kasa/Ecowitt)
- **Rasta Voice AI** for streaming personality and brand voice
- **OpenClaw** - Multichain AI agent framework (12+ messaging channels)

Legal: California Prop 64 (6 plants max personal cultivation).

## Architecture Strategy: OpenClaw-First (CRITICAL)

**OpenClaw is the primary AI orchestrator. Python is demoted to a Hardware Abstraction Layer (HAL).**

When building new capabilities, follow this preference hierarchy:
1. **OpenClaw built-in skill** (e.g., `gemini`, `oracle`, `blogwatcher`) — already maintained, tested, framework-native
2. **Community skill via ClawHub** (e.g., `alpha-finder`, `tweeter`, `ralph-loop-writer`) — install, configure, done
3. **Custom OpenClaw skill** in `openclaw-workspace/ganjamon/skills/` — our own, portable, follows framework conventions
4. **Python `src/` code** — ONLY for hardware drivers, HAL API endpoints, and things that genuinely can't be skills

**When to use Python instead:** Hardware I/O, FastAPI endpoints, safety guardrails, database operations, low-level integrations. Anything with `import sensor` or `import subprocess` for device control.

**When to use OpenClaw skills:** Social posting, content generation, research, trading signals, self-improvement, monitoring, A2A interactions, email triage — any capability that's primarily "call an API or LLM and do something with the result."

### ❌ Anti-Pattern: Python Daemons
**NEVER** add social posting, research, or scheduled tasks as Python subprocesses in `run.py`. Use **OpenClaw cron jobs** instead (canonical schedule is reconciled into the active cron store). The gateway handles all scheduling internally. See `scripts/setup_openclaw_crons.sh` and `scripts/reconcile_openclaw_cron_store.py`.

### Scheduling via OpenClaw Cron
- `openclaw-workspace/ganjamon/HEARTBEAT.md` defines the complete autonomous loop
- Heartbeat (every 30m) handles sensor checks + Moltbook/Clawk
- **Cron jobs** handle social posting (4h), research (12h), daily reports (9AM), self-improvement (weekly)
- Cron runs inside the gateway process — no additional Python subprocesses needed
- Full cron docs: `openclaw/docs/automation/cron-jobs.md`

**Full reference:** `docs/OPENCLAW_INTEGRATION.md` — skills manifest, heartbeat schedule, HAL API, deployment, migration table.

## System Architecture (CRITICAL)

**THREE machines:**

| Machine | Location | Role |
|---------|----------|------|
| **Windows Laptop** | `C:\Users\natha\sol-cannabis` | Development, streaming, Rasta voice |
| **Chromebook Server** | `natha@chromebook.lan` | Plant ops, unified agent (grow + trading + social + FastAPI) |
| **Raspberry Pi Zero 2 W** | `midaswhale@192.168.125.222` | Rasta megaphone (Deepgram STT -> Groq LLM -> ElevenLabs TTS) |

- Rasta voice pipeline typically runs on Windows (`rasta-voice/`), but the streaming agent may need it on other hosts as needed.
- Pi details: See `raspberry-pi/` directory and `memory/raspberry_pi.md`

## Development Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run everything (FastAPI server + AI orchestrator)
python run.py all          # or: ./run.sh --hw

# Run components individually
python run.py server       # FastAPI on :8000
python run.py orchestrator # Sensor polling + AI decisions

# Quick run modes
./run.sh --once            # Single decision cycle (mock sensors)
./run.sh --hw --once       # Single cycle with real hardware
./run.sh --hw --interval 15  # Custom interval (minutes)

# Test hardware individually
python -m src.hardware.kasa    # Discover Kasa smart plugs
python -m src.hardware.govee   # Test Govee temp/humidity sensor
python -m src.hardware.webcam  # Test webcam capture

# API server standalone
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Deploy website to Cloudflare Pages
source .env.wrangler && export CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
npx wrangler pages deploy pages-deploy/ --project-name=grokandmon

# Docker
docker build -t grokmon .
docker run -p 8000:8000 --env-file .env grokmon
```

## Source Code Architecture

The `src/` package is the core Python codebase (Python 3.11, FastAPI + asyncio). `PYTHONPATH` must include the project root.

| Module | Purpose | Key Entry |
|--------|---------|-----------|
| `src/orchestrator/` | Main grow agent loop — sensors, AI decisions, safety, learning | Production entry point (via `run.py all`) |
| `src/ai/` | Grok AI brain + vision analysis + 14 grow tools | `brain.py` (GrokBrain), `tools.py` (ToolExecutor) |
| `src/brain/` | Legacy agent (archived) + episodic memory + unified context | `agent_legacy.py` (archived), `memory.py`, `unified_context.py` |
| `src/core/` | Infrastructure — **paths.py** (centralized), events, circuit breakers, watchdog, supervisor, health | Shared by all subsystems |
| `src/api/` | FastAPI server — REST + WebSocket endpoints for dashboard | `app.py` (82+ endpoints, health, webhooks) |
| `src/hardware/` | Sensor/actuator drivers — Govee, Kasa, Ecowitt, Tapo, webcam | Each device has its own module |
| `src/social/` | Multi-platform posting — engagement daemon, scheduler, anti-robot | `engagement_daemon.py` (6+ platforms, 10 loops) |
| `src/telegram/` | Telegram bot (@MonGardenBot) — Rasta personality, community | `bot.py` (separate service) |
| `src/payments/` | Profit splitting (60/25/10/5) + approval gate | `splitter.py`, `approval_gate.py` |
| `src/review/` | Auto-review engine — compliance, patterns, visual analysis | `engine.py`, `analyzers.py`, `visual.py` |
| `src/learning/` | Cross-domain learning — grimoire, grow learning, regime detection, **OpenClaw→Ralph upgrade bridge** | `grow_learning.py`, `compound_learning.py`, `openclaw_upgrade_bridge.py` |
| `src/streaming/` | Retake.tv streaming + Rasta TTS | `retake_lite.py`, `rasta_tts.py` |
| `src/blockchain/` | Monad/EVM integration, ERC-8004 reputation publishing, on-chain grow logging | `monad.py`, `reputation_publisher.py`, `onchain_grow_logger.py` |
| `src/cultivation/` | Growth stage params, VPD calculations | Cannabis-specific environmental targets |
| `src/mailer/` | Email via agent@grokandmon.com — outbound + inbound webhook | `client.py`, `inbox.py` |
| `src/mcp/` | MCP tool definitions for hardware control | `tools.py` (26 tools) |
| `src/db/` | SQLAlchemy + SQLite data persistence | `data/grow_data.db` |
| `src/safety/` | SafetyGuardian — watering safeguards, dark period, kill switch | `guardian.py` |
| `src/media/` | Timelapse capture, GIF generator, DexScreener banners | `timelapse.py`, `gif_generator.py` |
| `src/analytics/` | Sensor stability scoring | `stability.py` |
| `src/mqtt/` | IoT expansion — publish/subscribe with graceful degradation | `service.py` |
| `src/voice/` | Rasta voice pipeline manager (Windows only) + `get_soul_identity()` for persona loading | `manager.py`, `personality.py` |
| `src/collaboration/` | Agent Rooms client — room messaging, tasks, fallback IPC for multi-agent coordination | `rooms_client.py` |
| `src/notifications/` | Alert routing — Discord, Telegram, generic notifier | `alerts.py`, `discord.py`, `notifier.py` |
| `src/scheduling/` | Light schedule / photoperiod management | `photoperiod.py` |
| `src/web/` | Web frontend — dashboards, HUD, bridge UI, swap UI | HTML/CSS/JS in subdirectories |
| `src/tools/` | Web search, subagent executor, shared tool utilities | `web_search.py`, `subagent.py` |

**Data flow:** Sensors -> `orchestrator.py` -> `src/ai/brain.py` -> Grok API (xAI) -> action decisions -> `hardware/` actuators -> `db/` logging -> `api/` dashboard

**Cross-system awareness:** `brain/unified_context.py` aggregates read-only data from the trading agent (`agents/ganjamon/data/`), engagement daemon (`data/engagement_*.json`), email inbox, community suggestions, and historical reviews into a unified context block injected into every Grok decision prompt. This gives the AI brain full situational awareness across all subsystems without coupling them.

**AI Decision Context (injected every 2h):** Sensor data + episodic memory (with hippocampus-style importance/decay) + grimoire learnings (confidence ≥ 0.4) + pitfalls (`config/pitfalls.yaml`, critical/high) + hard principles (`config/principles.yaml`, 11 rules) + unified trading/social context.

**Config files:**
- `config/principles.yaml` — 15 machine-readable agent principles (11 hard, 4 soft)
- `config/pitfalls.yaml` — 10 machine-readable gotchas/guardrails
- `config/hardware.yaml` — Device mapping
- `.env` — Secrets/API keys

**Unified process:** `run.py all` launches 3 subprocesses: FastAPI (HAL), OpenClaw gateway (primary orchestrator, 60s delayed start, nice +10), and GanjaMonAgent (trading). Helper threads: memory mirror (30min sensor snapshots), upgrade bridge (OpenClaw→Ralph), proc watchdog. One service (`grokmon.service`), one heartbeat.

## Webcam Settings (Logitech C270 @ /dev/video2)

Calibrated Feb 15 2026. Key insight: **auto WB + low saturation** is the only combo that avoids persistent yellow cast under grow LEDs. Manual WB at any temperature (2500K-5500K) produced yellow.

| Setting | Value | Notes |
|---------|-------|-------|
| brightness | 45 | Low — prevents washout under bright LED |
| contrast | 50 | Above default — adds depth |
| saturation | **20** | Critical — prevents warm LED color amplification |
| gain | 8 | Low — LED provides enough light |
| sharpness | 50 | Moderate — avoids halo artifacts |
| auto_exposure | 1 | Manual mode |
| exposure_time_absolute | 25 | Short — prevents washout |
| backlight_compensation | 0 | Off |
| white_balance_automatic | **1** | Auto — adapts to LED spectrum |

`_enforce_white_balance()` runs periodically to keep auto WB enabled.

## Recent Ops Lessons (2026-02-11)

- **Do not trust handoff state without readback.** On Chromebook, always inspect `/home/natha/.openclaw/openclaw.json` directly before assuming model or fallback changes are live.
- **Cron setup requires hard verification.** `scripts/setup_openclaw_crons.sh` output alone is not proof; confirm by inspecting the active store `openclaw-workspace/cron/cron.json` and watching `jobs[].state.lastRunAtMs` advance over time (legacy `~/.openclaw/cron/*.json` may be stale).
- **When OpenClaw CLI hangs, separate gateway vs API health.**
  - `/api/health` can still be healthy while `openclaw cron list` times out at websocket gateway.
  - Probe `http://127.0.0.1:18789/__openclaw__/canvas/` and check `logs/openclaw.log` for `gateway timeout after 30000ms`.
- **OpenClaw CLI version mismatch matters.** Chromebook is on `OpenClaw 2026.2.9`; `openclaw cron run` supports `--timeout` and `--due`, but not `--force`. Use extended timeout for manual isolated runs (`openclaw cron run <id> --timeout 180000`).
- **Watering audit query discipline.** `action_logs` contains many `WATER` observation rows; real pump events are rows with reasons like `Dispensed 50ml of water...`.
- **Grok's Wisdom must be user-facing.** `/api/ai/latest` should not expose raw `AUTOPILOT (gentle_daily_watering)` log blobs; translate them into patois guidance about what happened and next plant action, and keep `mon_day` aligned with current grow day.
- **Timezone safety in trading agent.** Keep `datetime` values timezone-aware in `agents/ganjamon/src/main.py` (`datetime.now(timezone.utc)`) to prevent crash loops and naive/aware subtraction errors.
- **Tunnel admin credential split is real.** `https://grokandmon.com/api/auth/token` expects `ADMIN_JWT_PASSWORD`, while `https://agent.grokandmon.com/auth/token` expects `ADMIN_PASSWORD` (set in `.env`).
- **Travel/off-LAN control path is operational.** Use `scripts/chromebook_remote_admin.sh` (`ping|status|exec|restart`) instead of ad-hoc curl/urllib for reliable remote administration.
- **Alpha discovery can silently stall on branch-scope bugs.** Keep deployer counters and pair iteration shared across provider branches in `signals/alpha_discovery.py`; otherwise `_total` can be unbound and the loop sleeps for 2h after one exception.
- **Signal weight files are object-shaped, not scalar-only.** `signal_weights.json` may store `{weight, ...}` objects per source. Always normalize to numeric `weight` before multiplying.
- **On-chain polling needs circuit-breakers.** Ethereum RPC 429s can flood logs and burn CPU. Keep chain-level backoff and throttled rate-limit logging in `intelligence/onchain_awareness.py`.
- **x402 payer should auto-disable without key.** If `MONAD_PRIVATE_KEY` is unset, do not keep attempting paid outbound calls; this can spam `x402: No private key configured` and burn cycles. Keep payer disabled unless key is present (`X402_PAYER_ENABLED` supports `auto|true|false`).
- **Cron delivery can hurt gateway responsiveness.** Announce-style cron delivery has triggered `Subagent announce failed: gateway timeout` under load; default autonomous cron jobs to `delivery.mode=none`.
- **Cron overlap can silently skip jobs.** With catch-up suppression enabled, if one isolated cron run occupies the lane, nearby due jobs can jump to their next slot without running. Stagger heavy schedules (do not stack within a few minutes).
- **When changing cron expressions, reset schedule state.** Preserve history (`lastRunAtMs`) but clear/recompute `nextRunAtMs` so jobs don't remain pinned to old times.
- **`/api/health` should retry OpenClaw probes.** Single-shot checks can false-negative during short gateway stalls. Keep retry-based probing (`OPENCLAW_HEALTH_PROBE_RETRIES`) for readiness accuracy.
- **Dashboard social feed should be normalized.** For live demos/debugging, combine `engagement_log.jsonl` + trading `social_post_log.jsonl` and normalize to consistent fields (`timestamp/platform/post_type/content`) so recent activity doesn’t look empty or null.
- **Cheap-by-default model split is required.** Keep routine cron loops on `openrouter/moonshotai/kimi-k2.5`; reserve `kimi-k2-thinking` for low-frequency deep analysis/reflection jobs.

**⚠️ TRADING AGENT RUNTIME NOTE (Read Before Editing Trading Code):**
GanjaMon is **ONE agent** with one soul and one mission — but the trading subsystem currently runs as a separate subprocess for technical reasons:
- **Code:** `agents/ganjamon/src/` (separate PYTHONPATH)
- **Config:** `agents/ganjamon/.env` (separate from root `.env`)
- **Data:** `agents/ganjamon/data/` (separate from `sol-cannabis/data/`)
- **Entry:** `python -m main` with `cwd=agents/ganjamon/`
- **Deployment:** `deploy.sh` does NOT deploy it. Use `deploy_agent.sh` instead.
- **Sync:** `sync_agent.sh --pull` pulls Ralph's Chromebook changes back to Windows.

Cross-domain intelligence bridges both data directories via `brain/unified_context.py` and `CrossDomainSynthesizer`. SOUL.md is loaded by both sides. The agent learns from grows and applies it to trades, and vice versa.

**Chromebook path:** `/home/natha/projects/sol-cannabis/agents/ganjamon/` (symlinks to `cloned-repos/ganjamon-agent/` for data, src, venv)
> ⚠️ NOT `/home/natha/sol-cannabis/...` — that path doesn't exist. The old `/home/natha/projects/ganjamon-agent/` is legacy personality files only.

**Two data directories exist:**
| `sol-cannabis/data/` | Grow sensors, engagement state, episodic memory, SQLite DB |
| `agents/ganjamon/data/` | Paper portfolio, brain state, observations, experience DB |
Cross-domain intelligence must read from BOTH directories.

**Services on Chromebook:**
- `grokmon.service` — **UNIFIED agent** (HAL + OpenClaw + trading). ENABLED.
- `ganja-mon-bot.service` — Telegram community bot (@MonGardenBot). ENABLED.
- `ganjamon-agent.service` — DISABLED (merged into grokmon 2026-02-08).
- `kiosk.service` — Chrome HUD kiosk. **DISABLED** (2026-02-10, saves 1.1 GB + 67% CPU). Start manually when needed.
- `retake-stream.service` — ffmpeg RTMP to RetakeTV. **DISABLED** (2026-02-10, saves 104 MB + 31% CPU). Start manually for live streams.

**Entrypoints:** `run.py` (Python) or `run.sh` (bash wrapper for legacy agent). Chromebook runs via systemd: `systemd/grokmon.service` -> `python run.py all`.

**Config:** `.env` for secrets/API keys (see `.env.example`), `config/hardware.yaml` for device mapping.

## Sync Workflow (Chromebook <-> Windows)

**Grow system (src/):**
- Deploy Windows → Chromebook: `deploy.sh [--restart]` (WSL, uses sshpass)

**Trading agent (agents/ganjamon/):**
- Deploy Windows → Chromebook: `deploy_agent.sh [--all|--file PATH]` (Git Bash, uses PowerShell SSH)
- Sync Chromebook → Windows: `sync_agent.sh [--pull|--diff FILE]` (Git Bash, uses PowerShell SSH)
- ⚠️ `sync_from_ralph.sh` and `ralph_sync.sh` use `git fetch/push` which requires GitHub SSH keys — these are set up on the Chromebook but NOT on Windows Git Bash.

**SSH from Git Bash (Windows):**
- `sshpass` is NOT available in Git Bash. Use PowerShell SSH instead:
  ```bash
  powershell.exe -Command "ssh natha@chromebook.lan 'command here'"
  ```
- File transfer: prefer stdin piping (more reliable than `scp` across Git Bash/PowerShell path + quoting edge cases):
  ```bash
  powershell.exe -Command "Get-Content 'C:\path\file.py' -Raw | ssh natha@chromebook.lan 'cat > /remote/path/file.py'"
  ```
  For complex remote commands, do not inline quoting-heavy one-liners; use the script-pipe pattern in `docs/SSH_QUOTING_PLAYBOOK.md`.

## Multi-Agent Orchestration

Multiple AI agents work on this codebase:
- **Claude Code** (this) - Primary development agent (WSL, `sshpass`, `--dangerously-skip-permissions`)
- **Antigravity IDE** - Visual IDE agent with browser testing, image gen, rich tooling (see `antigravity.md`)
- **Gemini CLI** - Parallel agent (see `GEMINI.md`)
- **Codex CLI** - Repository scaffolding and bulk operations (see `AGENTS.md`)

All agents follow the same shared rules (`.claude/rules/*.md`) via their respective instruction files.
All agents share the `memory/` directory for cross-agent knowledge.

## Current Grow

| Field | Value |
|-------|-------|
| **Strain** | Granddaddy Purple Runtz (GDP x Runtz) |
| **Stage** | Veg (Feb 2026) |
| **Harvest** | Late April / Early May 2026 |

## On-Demand Reference (read when needed, NOT always loaded)

These files contain detailed reference data. Read them when working on the relevant subsystem:

| File | When to read |
|------|-------------|
| `.claude/context/token.md` | Working on $MON token, bridge, or contracts |
| `.claude/context/telegram.md` | Working on Telegram bots or community |
| `.claude/context/farcaster.md` | Working on Farcaster posting or account |
| `.claude/context/operations.md` | Deploying, SSH, streaming, Cloudflare |
| `.claude/context/hardware.md` | Working on sensors, actuators, xAI API |
| `docs/WORMHOLE_NTT_RULES.md` | Debugging Wormhole NTT bridge issues |

## GanjaMon Trading Agent

The primary trading agent lives at `agents/ganjamon/` with its own comprehensive `CLAUDE.md`.

### CRITICAL: $MON vs Trading Assets

**$MON (Ganja Mon)** is OUR token - the one we're bolstering with trading profits:
- Monad: `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`
- Base: `0xE390612D7997B538971457cfF29aB4286cE97BE2`

**The agent trades ANY asset with alpha** - chain/asset agnostic for generating profits.

**Profit allocation:** 60% compound -> 25% buy $MON -> 10% buy $GANJA -> 5% burn

**Key subsystems:** Signal aggregation, validation layer, execution engine (nad.fun, Token Mill, Hyperliquid, Polymarket), self-funding flywheel, profit allocator.

**Related infrastructure:** `openclaw/`, `openclaw-workspace/`, `openclaw-trading-assistant/`, `hyperliquid-trading-bot/`, `hyperliquid-ai-trading-bot/`, `cloned-repos/` (40+ repos, security audited).

## Social / Branding

- **Website:** https://grokandmon.com
- **Twitter/X:** @ganjamonai
- **Telegram:** https://t.me/ganjamonai
- **Token:** $MON on Monad

## Subdirectory CLAUDE.md Files

- `rasta-voice/CLAUDE.md` - Voice pipeline, audio, OBS
- `irie-milady/CLAUDE.md` - NFT generation
- `agents/ganjamon/CLAUDE.md` - GanjaMon trading agent (primary)
- `openclaw/CLAUDE.md` - OpenClaw framework dev guidelines
- `hyperliquid-trading-bot/CLAUDE.md` - Hyperliquid grid bot

## Reference Docs

### Deep Dive Documentation

| Doc | Topic |
|-----|-------|
| `docs/OPENCLAW_FRAMEWORK_DEEP_DIVE.md` | Complete OpenClaw architecture |
| `docs/ERC8004_DEEP_DIVE.md` | ERC-8004 standard, registries, trust models |
| `docs/MOLTBOOK_HACKATHON_GUIDE.md` | Hackathon guide, submission requirements |
| `docs/GANJAMON_AGENT_ARCHITECTURE.md` | Trading agent signals, execution, self-improvement |
| `docs/AGENT_CAPABILITIES.md` | Unified agent capabilities, all tools/endpoints |
| `docs/AGENT_REDESIGN_FIRST_PRINCIPLES.md` | Architecture redesign, 10-agent research |
| `docs/MULTI_DOMAIN_AGENT_EXAMPLES.md` | Copyable examples: orchestration, social, trading, OpenClaw, reliability |
| `docs/AGENT_PATTERNS_SYNTHESIS.md` | 30 borrowable patterns from 15+ agent repos |
| `docs/PATTERN_IMPLEMENTATION_PLAN.md` | Phase 1-4 implementation plan (all complete) |
| `docs/PATTERN_IMPLEMENTATION_COMPLETE.md` | Comprehensive record of all 30 patterns implemented |

### Infrastructure & Operations

| Doc | Topic |
|-----|-------|
| `docs/CHROMEBOOK_SERVER.md` | Server setup, deployment, tunnel access |
| `docs/CLOUDFLARE_TUNNEL_SETUP.md` | Remote admin API |
| `docs/CULTIVATION_REFERENCE.md` | VPD targets, strain info |
| `docs/SYSTEM_ATLAS.md` | Full system map |
| `docs/WORMHOLE_NTT_RULES.md` | Wormhole NTT bridge debugging rules |
| `docs/NTT_DEPLOYMENT_LESSONS.md` | Bridge deployment lessons |
| `docs/RALPH_LOOPS_AND_LONG_RUNNING_CLAUDE.md` | Iterative AI loops |
| `WATERING_SAFEGUARDS.md` | AI watering safety constraints |
| `AGENTS.md` | Repo guidelines for Codex/other agents |
| `GEMINI.md` | Parallel instruction set for Gemini |
