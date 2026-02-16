# OpenClaw Integration — GanjaMon

**Last Updated:** February 11, 2026
**Status:** LIVE ✅ on Chromebook (gateway running, heartbeat active)

**For a thorough conceptual and reference guide to OpenClaw (architecture, skills, cron, config, CLI), see [OPENCLAW_GUIDE.md](OPENCLAW_GUIDE.md).**

## Architecture

OpenClaw is the **primary AI orchestrator**. Python is demoted to a Hardware Abstraction Layer (HAL).

```
┌──────────────────────────────────────────────────────────────┐
│  OpenClaw Gateway (PRIMARY ORCHESTRATOR)                     │
│  Port 18789 — heartbeat-driven autonomous agent              │
│                                                              │
│  16 built-in skills + 14 community skills + 13 custom skills│
│  + lobster extension (approval-gated pipelines)              │
│                                                              │
│  Agents: ganjamon (primary), moltbook-observer (read-only)   │
│  Memory: daily logs + MEMORY.md + vector search              │
├──────────────────────────────────────────────────────────────┤
│  Python HAL (HARDWARE + EXECUTION LAYER)                     │
│  FastAPI :8000 — sensors, actuators, safety, trading         │
├──────────────────────────────────────────────────────────────┤
│  GanjaMonAgent (TRADING SUBPROCESS)                          │
│  Isolated PYTHONPATH — agents/ganjamon/                      │
└──────────────────────────────────────────────────────────────┘
```

## Process Model

```bash
python run.py all          # NEW: HAL + OpenClaw + Trading (3 subprocesses)
python run.py legacy       # OLD: HAL + Orchestrator + Social + Research + Trading
python run.py openclaw     # Just the OpenClaw gateway
python run.py server       # Just the HAL (FastAPI)
```

## Conflict Avoidance (CRITICAL)

- The legacy `ganjamon-agent.service` (runs `python -m src.main` in `cloned-repos/ganjamon-agent/`) must be **stopped** or it will fight the `run.py all` trading subprocess and create respawn / PID-lock loops:
  - `systemctl --user stop ganjamon-agent.service`
  - `systemctl --user disable ganjamon-agent.service`
- Do not leave a manually-started gateway (`nohup openclaw gateway run ...`) running alongside `grokmon.service` unless you intentionally want to bypass `run.py`'s lifecycle management (port/lock conflicts otherwise).

### `run.py all` (Default)

| Subprocess | Process | Port | Role |
|-----------|---------|------|------|
| FastAPI server | Main process spawns | :8000 | Hardware HAL — sensors, actuators, SafetyGuardian, admin API |
| OpenClaw gateway | `openclaw gateway run` | :18789 | Primary AI brain — heartbeat, skills, social, decisions |
| GanjaMonAgent | `python -m main` | — | Trading execution — signals, portfolio, P&L |

**Fallback:** If `openclaw` binary is not found or config is missing, the OpenClaw subprocess automatically falls back to the legacy orchestrator.

**Watchdog:** A background thread respawns OpenClaw gateway or trading agent if either crashes (checks every 30s).

## Workspace Files

All workspace files live at `openclaw-workspace/ganjamon/`:

| File | Purpose |
|------|---------|
| `SOUL.md` | Rasta personality — Bob Marley meets Cheech & Chong, Jamaican patois, mission statement |
| `HEARTBEAT.md` | Full autonomous loop — 30m sensor checks through weekly Ralph loops |
| `TOOLS.md` | Complete skill manifest — 37 skills + HAL API endpoints |
| `AGENTS.md` | Operating rules — skill-first architecture, safety, A2A protocol, social posting rules |
| `IDENTITY.md` | Agent UUID, Moltbook profile, ERC-8004 registration |
| `PERMISSIONS.md` | Filesystem, network, env, shell permissions |

Config at `openclaw-workspace/config/openclaw.json`.

## Heartbeat Schedule

The OpenClaw heartbeat fires every 30 minutes. The `HEARTBEAT.md` defines a layered schedule:

| Interval | Action |
|----------|--------|
| 30 min | Sensor read via HAL, Moltbook heartbeat.md check, Clawk engagement |
| 2 hours | Full grow decision cycle (sensors → AI reasoning → actuator commands) |
| 3 hours | Moltbook post (fetch heartbeat.md first, handle verification challenges) |
| 4 hours | Cross-platform social (Twitter, Farcaster, Clawk, Telegram) + reputation publishing |
| 6 hours | Auto-review via `oracle` skill (compliance, patterns, optimization) |
| 12 hours | Research via `blogwatcher` + `summarize` + `alpha-finder` + A2A discovery |
| Daily 9AM | Comprehensive update with `nano-banana-pro` image across all platforms |
| Weekly | Ralph loop self-improvement via `coding-agent` + `ralph-loop-writer` |

## Skills (37 Total)

### Built-in Skills (16)

| Skill | Use Case |
|-------|----------|
| `gemini` | Quick Q&A, content ganjafy, Rasta voice generation |
| `nano-banana-pro` | Gemini 3 Pro image gen/edit — plant photos, memes, daily updates |
| `oracle` | GPT-5.2 Pro deep think — multi-file review, strategy, auto-review |
| `summarize` | Summarize articles, PDFs, YouTube for market research |
| `blogwatcher` | RSS/Atom feed monitoring for crypto/cannabis news |
| `weather` | Outdoor conditions affecting grow environment |
| `github` | Issue triage (#125 appeal), PR monitoring, CI checks |
| `coding-agent` | Background PTY for Ralph loops, automated fixes |
| `skill-creator` | Create new skills when patterns emerge (self-evolving) |
| `clawhub` | Skill marketplace — install/publish community skills |
| `model-usage` | Track per-model API costs across providers |
| `tmux` | Manage background processes on Chromebook |
| `session-logs` | Search session JSONL history, audit trail |
| `discord` | Grow alerts, trading signals, community engagement |
| `himalaya` | agent@grokandmon.com email (IMAP/SMTP) |
| `canvas` | Live grow dashboard on phone/tablet |

### Community Skills (14, via ClawHub)

| Skill | Author | Use Case |
|-------|--------|----------|
| `nadfun-token-creation` | therealharpaljadeja | Launch $GANJA token on nad.fun |
| `x402` | 0xterrybit | x402 micropayment protocol |
| `polymarket-hyperliquid-trading` | zaycv | Polymarket + Hyperliquid trading |
| `unifai-trading-suite` | zbruceli | Unified trading: Polymarket, Kalshi, social signals |
| `alpha-finder` | tzannetosgiannis | Alpha hunting across social + on-chain |
| `crypto-whale-monitor` | waleolapo | Whale wallet tracking |
| `crypto-self-learning` | totaleasy | Autonomous trading self-improvement |
| `clawcast` | tezatezaz | Farcaster casting |
| `tweeter` | trymoinai-create | Twitter/X posting |
| `moltbook-2` | zaki9501 | Moltbook posting |
| `moltbook-daily-digest` | wangfugui1799 | Moltbook feed summarization |
| `ralph-loop-writer` | walkamolee | Structured self-improvement loops |
| `session-memory` | swaylq | Persistent session memory |
| `crypto-hackathon` | swairshah | Hackathon utilities |

### Custom Skills (13)

| Skill | Purpose |
|-------|---------|
| `moltbook-poster` | Moltbook posting + verification challenge handling + rate limiting |
| `clawk-poster` | Clawk posting with 5:1 engagement rule enforcement |
| `grow-monitor` | Sensor reads + actuator control via HAL API (SafetyGuardian enforced) |
| `trading-signals` | Portfolio monitoring + alpha aggregation + trade announcements |
| `a2a-discovery` | ERC-8004 agent discovery + A2A JSON-RPC + x402 payments |
| `social-composer` | Rasta-voice content generation with `gemini` + `nano-banana-pro` |
| `reputation-publisher` | On-chain ERC-8004 reputation signal publishing |
| `ganjamon-cultivation` | Cultivation domain intelligence + grimoire writing |
| `ganjamon-mon-liquidity` | $MON liquidity monitoring across chains |
| `ganjamon-social` | Cross-platform social posting strategy |
| `ganjamon-trading` | Trading intelligence + cross-domain synthesis |
| `pirate-intelligence` | Competitive intel: GitHub scanning, on-chain stalking, code analysis |
| `grimoire-writer` | Write learnings to domain grimoires from decision outcomes |

### Extension

| Extension | Purpose |
|-----------|---------|
| `lobster` | Multi-step approval pipelines for irreversible actions (watering, trading, posting) |

## HAL API Endpoints

The FastAPI server at `localhost:8000` is the hardware interface. OpenClaw skills call these — they never touch hardware directly.

### Sensor (Read-Only)
```
GET  /api/sensors              → Current temp, humidity, VPD, soil moisture, CO2
GET  /api/sensors/history      → Historical data (?hours=N)
GET  /api/grow/stage           → Growth stage + VPD targets
GET  /api/grow/history         → Decision history
GET  /api/health               → System health
```

### Actuator (Write — SafetyGuardian enforced)
```
POST /api/actuator/control     → {"device": "water_pump|co2_injector", "action": "on|off", "duration": N}
GET  /api/actuator/status      → Device states
GET  /api/safety/status        → Watering cooldown, dark period, kill switch
```

### Trading
```
GET  /api/trading/portfolio    → Positions + P&L
GET  /api/trading/signals      → Alpha signals
POST /api/trading/execute      → Execute trade (requires lobster approval)
GET  /api/trading/history      → Trade history
```

### Social
```
POST /api/social/post          → {"platform": "...", "content": "...", "image_url": "..."}
GET  /api/social/metrics       → Engagement metrics
GET  /api/social/mentions      → Unread mentions
```

### Blockchain
```
POST /api/blockchain/publish-reputation → Publish ERC-8004 signals
GET  /api/blockchain/trust-score       → 8004scan trust score
GET  /api/blockchain/agent-info        → Agent #4 on Monad
```

### Admin
```
GET  /api/admin/ping           → Health (no auth)
GET  /api/admin/system-info    → CPU, memory, disk
POST /api/admin/restart-service/{name}
POST /api/admin/exec           → {"command": "..."}
GET  /api/admin/logs/{name}    → Service logs (?lines=N)
```

## Lobster Pipelines

Safety-critical actions use `lobster` approval gates:

```
# Watering
grow-monitor.check-moisture | approve --prompt "Water? Soil at {moisture}%" | grow-monitor.water

# Trading
trading-signals.scan | approve --prompt "Execute trade?" | trading-signals.execute

# Email triage
himalaya.list --folder INBOX | approve --prompt "Reply to these?" | himalaya.reply
```

## OpenClaw Config (openclaw.json)

Key configuration:

| Field | Value |
|-------|-------|
| Primary model | `x-ai/grok-3-mini` |
| Fallback models | `anthropic/claude-sonnet-4-5`, `google/gemini-2.5-flash` |
| Heartbeat interval | 30 minutes |
| Active hours | 06:00 - 23:00 (America/Los_Angeles) |
| Gateway port | 18789 |
| Built-in skills | 16 enabled |
| Agents | `ganjamon` (default), `moltbook-observer` |
| Channels | Telegram (group -1003584948806), Discord |
| Extensions | `lobster` (approval pipelines) |
| Cron | Enabled, max 2 concurrent |

### Claude Max Subscription Auth (DORMANT)

**Status:** Configured as fallback, **no auth credentials deployed** — completely inert until activated.

`anthropic/claude-sonnet-4-5` is in the fallback chain but OpenClaw silently skips it (no `ANTHROPIC_API_KEY` or setup-token on the Chromebook). This is intentional — it avoids burning Claude Max quota.

**To activate (when quota resets):**
```bash
# From Git Bash on Windows:
bash scripts/activate_claude_max.sh              # Add auth (keeps as fallback)
bash scripts/activate_claude_max.sh --primary    # Promote to primary model
bash scripts/activate_claude_max.sh --status     # Check current auth
bash scripts/activate_claude_max.sh --deactivate # Remove from fallback chain
```

**How it works:** `claude setup-token` generates a long-lived token from your Claude Code Max subscription. The script deploys it to the Chromebook's OpenClaw auth profiles. The token doesn't auto-refresh — re-run the script when it expires.

**⚠️ Note:** Anthropic's ToS may not endorse subscription auth for autonomous agent workloads. For production, API keys are safer. Prompt caching is also not available with subscription auth.

## Deployment

### Chromebook Paths
```
/home/natha/projects/sol-cannabis/openclaw-workspace/           → Workspace root
/home/natha/projects/sol-cannabis/openclaw-workspace/config/    → Config source
/home/natha/projects/sol-cannabis/openclaw-workspace/ganjamon/  → Primary agent
/home/natha/projects/sol-cannabis/openclaw-workspace/logs/      → Gateway logs
/home/natha/.openclaw/openclaw.json                            → Config (OpenClaw reads this)
/usr/lib/node_modules/openclaw/                                → Binary (v2026.2.9)
```

### ⚠️ CLI Syntax (CRITICAL — Read This)

```bash
# CORRECT — start gateway
openclaw gateway run --bind loopback --port 18789 --force

# WRONG — --config flag does NOT exist!
openclaw gateway run --config /path/to/config.json   # ❌ FATAL ERROR

# WRONG — systemd service is DISABLED (run.py manages gateway)
openclaw gateway start                                # ❌ Won't work
openclaw gateway restart                              # ❌ Won't work
```

OpenClaw ALWAYS reads config from `~/.openclaw/openclaw.json`. There is no CLI flag to override.

### Deploy Commands
```bash
# Deploy config (use stdin pipe — SCP doesn't work from Git Bash)
powershell.exe -Command "Get-Content 'openclaw-workspace/config/openclaw.json' -Raw | ssh natha@chromebook.lan 'cat > ~/.openclaw/openclaw.json'"

# Deploy run.py
powershell.exe -Command "Get-Content 'run.py' -Raw | ssh natha@chromebook.lan 'cat > /home/natha/projects/sol-cannabis/run.py'"

# Kill + restart (run.py manages all subprocesses)
powershell.exe -Command "ssh natha@chromebook.lan 'pkill -9 -f openclaw; pkill -f run.py; sleep 3; cd /home/natha/projects/sol-cannabis && source venv/bin/activate && nohup python3 run.py all > /tmp/grokmon_startup.log 2>&1 &'"

# Verify (wait 15s)
powershell.exe -Command "Start-Sleep 15; ssh natha@chromebook.lan 'ss -tlnp | grep 18789'"
```

### Config Rules (v2026.2.9)

Before deploying config, verify:
- **NO** top-level `identity` key (must be inside `agents.list[].identity`)
- **NO** `gateway.auth` section when using `bind: "loopback"`
- **ALL paths are absolute** (no relative `../ganjamon`)
- **ALL `${VAR}` references** have env vars set (missing = fatal crash)

### Install Community Skills (on Chromebook)
```bash
cd /home/natha/projects/sol-cannabis/openclaw-workspace/ganjamon
export PATH=$PATH:/home/natha/.npm-global/bin
clawhub install nadfun-token-creation
clawhub install x402
clawhub install clawcast
clawhub install tweeter
clawhub install alpha-finder
clawhub install crypto-whale-monitor
clawhub install ralph-loop-writer
clawhub install moltbook-2
clawhub install session-memory
clawhub install polymarket-hyperliquid-trading
clawhub install unifai-trading-suite
clawhub install crypto-self-learning
clawhub install moltbook-daily-digest
clawhub install crypto-hackathon
```

Or copy from local clone: `cp -r cloned-repos/openclaw-skills/skills/<name>/ openclaw-workspace/ganjamon/skills/`

## Moltbook Suspension Appeal

- **GitHub Issue:** [moltbook/api#125](https://github.com/moltbook/api/issues/125)
- **Reason:** Failed AI verification challenge (offense #2) + raw HTTP instead of OpenClaw skills
- **Fix:** Full OpenClaw migration, `moltbook-poster` skill with verification challenge handler
- **Status:** Appeal comment posted 2026-02-09 with migration details

## Migration from Legacy

| What | Before (Legacy) | After (OpenClaw) |
|------|-----------------|-------------------|
| Orchestrator | `src/orchestrator.py` (Python asyncio) | OpenClaw heartbeat + HEARTBEAT.md |
| Social posting | `src/social/engagement_daemon.py` | OpenClaw skills (moltbook-poster, clawk-poster, tweeter, clawcast) |
| Content gen | Direct Grok API calls | `gemini` + `social-composer` skills |
| Image gen | N/A | `nano-banana-pro` skill (Gemini 3 Pro) |
| Research | `src/research/pirate.py` | `blogwatcher` + `summarize` + `alpha-finder` skills |
| Email | `src/mailer/client.py` (Resend) | `himalaya` skill (IMAP/SMTP) |
| Self-improvement | Manual Ralph loops | `coding-agent` + `ralph-loop-writer` skills |
| Process count | 4 subprocesses | 3 subprocesses |

Legacy mode is preserved via `python run.py legacy` for fallback.

## Incident Record: Feb 10, 2026 — Gateway Crash Loop

**Duration:** ~12 hours (overnight respawn loop)

**Symptoms:**
- OpenClaw gateway crashing in rapid respawn loop
- Port 18789 never listening
- `[WARN] OpenClaw gateway died — respawning...` in startup log
- CPU spike from crash → respawn → crash cycle

**Root Causes (3):**

| # | Bug | Fix |
|---|-----|-----|
| 1 | `run.py` used `--config` flag which doesn't exist in OpenClaw CLI | Changed to `--bind loopback --port 18789 --force`; added config sync via `shutil.copy2()` to `~/.openclaw/` |
| 2 | `gateway.auth.token` referenced `${OPENCLAW_GATEWAY_TOKEN}` which wasn't set in shell env | Removed `gateway.auth` section (loopback doesn't need auth) |
| 3 | Top-level `identity` key deprecated in v2026.2.9 | Migrated into `agents.list[0].identity` |

**Additional fixes:**
- Disabled conflicting `openclaw-gateway.service` systemd unit
- Created missing directories: `logs/`, `ganjamon/memory/`, `cron/`
- Converted relative paths to absolute in config
- Added auto-sync of workspace config → `~/.openclaw/` in `run.py`

**Documented in:** `memory/openclaw_gateway.md`, `config/pitfalls.yaml`
