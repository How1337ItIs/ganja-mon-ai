# OpenClaw — Thorough Guide

**Last Updated:** February 12, 2026  
**Sources:** Cloned repo `openclaw/`, `openclaw-workspace/`, project docs, and official OpenClaw documentation.

This guide combines research from the in-repo OpenClaw clone and the web into a single reference for understanding, configuring, and extending OpenClaw in the Grok & Mon stack.

---

## Table of Contents

1. [What Is OpenClaw?](#1-what-is-openclaw)
2. [Architecture Overview](#2-architecture-overview)
3. [Repository Structure (Cloned Repo)](#3-repository-structure-cloned-repo)
4. [Agent Workspace & Memory](#4-agent-workspace--memory)
5. [Skills System](#5-skills-system)
6. [Scheduling: Heartbeat vs Cron](#6-scheduling-heartbeat-vs-cron)
7. [Gateway: Run, Config, and CLI](#7-gateway-run-config-and-cli)
8. [Configuration Reference](#8-configuration-reference)
9. [Channels & Multi-Agent](#9-channels--multi-agent)
10. [Integration in This Project](#10-integration-in-this-project)
11. [Tools System](#11-tools-system)
12. [Agent Loop & Lifecycle](#12-agent-loop--lifecycle)
13. [Hooks](#13-hooks)
14. [Plugins & Extensions](#14-plugins--extensions)
15. [Security & Model Failover](#15-security--model-failover)
16. [Troubleshooting](#16-troubleshooting)
17. [Official Docs & Resources](#17-official-docs--resources)

---

## 1. What Is OpenClaw?

**OpenClaw** is an **open-source personal AI assistant framework** that you run on your own devices. It is:

- **Local-first**: A single Gateway (control plane) runs on your machine or server; you own the process and data.
- **Multi-channel**: One assistant can answer on WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, BlueBubbles, Microsoft Teams, Matrix, Zalo, WebChat, and more (including extensions).
- **Model-agnostic**: Supports Anthropic (Claude), OpenAI (GPT), Google (Gemini), xAI (Grok), OpenRouter, and others via a unified config; primary + fallback models per agent.
- **Skill-based**: Capabilities are added via **skills**—instructional Markdown (SKILL.md) that teach the agent how to use tools—not only by writing code.
- **Single-user by design**: Optimized for “my assistant, always on, feels local and fast.”

Key philosophy: the **Gateway is the control plane**; the product is the assistant. OpenClaw was built for **Molty** (space lobster AI) by Peter Steinberger and the community. License: MIT.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Clients: WhatsApp / Telegram / Slack / Discord / … / WebChat   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Gateway (control plane)                                         │
│  • WebSocket: ws://127.0.0.1:18789 (default)                      │
│  • HTTP on same port: Control UI, webhooks, OpenAI-compat API   │
│  • Sessions, presence, config, cron, channel routing             │
├─────────────────────────────────────────────────────────────────┤
│  Pi agent runtime (RPC) — tool execution, model selection,       │
│  auth failover, memory/session management                        │
├─────────────────────────────────────────────────────────────────┤
│  Agent workspace (~/.openclaw/workspace or per-agent path)        │
│  • AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, HEARTBEAT.md       │
│  • memory/ (daily logs, MEMORY.md)                               │
│  • skills/ (workspace-specific skills)                            │
└─────────────────────────────────────────────────────────────────┘
```

- **Gateway**: Always-on process; owns channel connections (e.g. Baileys for WhatsApp, grammY for Telegram) and the WebSocket control plane. Exits non-zero on fatal errors so a supervisor can restart it.
- **Config**: Read from `~/.openclaw/openclaw.json` (or `OPENCLAW_CONFIG_PATH`). There is **no** `--config` CLI flag to override; OpenClaw always uses that path.
- **Canvas**: Optional file server (default port 18793) for A2UI/visual workspace; can be disabled.

---

## 3. Repository Structure (Cloned Repo)

In this project, OpenClaw lives in two places:

### `openclaw/` (framework clone)

| Path | Purpose |
|------|---------|
| `src/` | TypeScript source: `agents/`, `channels/`, `cli/`, `config/`, `gateway/`, `cron/`, `skills/`, etc. |
| `docs/` | Mintlify-style docs (automation, channels, CLI, gateway, tools, concepts) |
| `skills/` | **Bundled skills** (e.g. gemini, discord, blogwatcher, summarize, oracle, nano-banana-pro) |
| `extensions/` | Plugin channels (Teams, Matrix, Line, etc.) |
| `packages/` | clawdbot, moltbot |
| `apps/` | Native apps (macOS, iOS, Android) |
| `openclaw.mjs` / `package.json` | Entry and build |

### `openclaw-workspace/` (this project’s workspace)

| Path | Purpose |
|------|---------|
| `config/openclaw.json` | **Source** config (deployed to `~/.openclaw/openclaw.json` on Chromebook) |
| `cron/cron.json` | Cron job store when `cron.store` points here (canonical schedule) |
| `ganjamon/` | Primary agent: SOUL.md, HEARTBEAT.md, TOOLS.md, AGENTS.md, IDENTITY.md, PERMISSIONS.md |
| `ganjamon/skills/` | **Custom skills** (moltbook-poster, grow-monitor, a2a-discovery, etc.) |
| `moltbook-observer/` | Secondary read-only agent |

**Critical:** OpenClaw **always** reads config from `~/.openclaw/openclaw.json`. Deploy `openclaw-workspace/config/openclaw.json` there (e.g. via stdin pipe to `cat > ~/.openclaw/openclaw.json`).

---

## 4. Agent Workspace & Memory

Each agent has a **workspace** directory. These files define identity and behavior and are injected into the system prompt (with size limits):

| File | Purpose |
|------|---------|
| `AGENTS.md` | Operating instructions, rules, memory usage |
| `SOUL.md` | Persona, tone, boundaries |
| `USER.md` | User profile (optional) |
| `IDENTITY.md` | Agent name, theme, emoji |
| `TOOLS.md` | Tool conventions and usage notes |
| `HEARTBEAT.md` | Checklist for heartbeat runs—**follow strictly**; agent reads this every heartbeat |
| `BOOTSTRAP.md` | One-time setup (optional) |
| `memory/YYYY-MM-DD.md` | Daily memory log |
| `MEMORY.md` | Long-term curated memory |

Injection: non-missing files are concatenated and prepended to the system prompt; large files are truncated (default ~20KB per file). Session snapshot: skills are fixed when a session starts and can hot-reload if the skills watcher is enabled.

---

## 5. Skills System

### What skills are

Skills are **instructional guides** for the LLM: a directory with a `SKILL.md` file (YAML frontmatter + Markdown). They are **not** executable code—they teach the agent how to use existing tools (bash, browser, HTTP, etc.) or document custom tool contracts.

### Skill locations and precedence

1. **Workspace skills**: `<workspace>/skills/` (highest)
2. **Managed/local**: `~/.openclaw/skills/`
3. **Bundled**: Shipped with the install (lowest)
4. **Extra dirs**: `skills.load.extraDirs` in config (lowest)
5. **Plugin skills**: From `openclaw.plugin.json` (when plugin enabled)

Name conflict: workspace overrides managed, managed overrides bundled.

### SKILL.md format (AgentSkills-compatible)

Minimum frontmatter:

```markdown
---
name: my-skill
description: One-line description for the agent.
---
```

Optional metadata (single-line JSON):

```markdown
---
name: nano-banana-pro
description: Generate or edit images via Gemini 3 Pro
metadata:
  {
    "openclaw": {
      "emoji": "🍌",
      "requires": { "bins": ["uv"], "env": ["GEMINI_API_KEY"], "config": ["browser.enabled"] },
      "primaryEnv": "GEMINI_API_KEY"
    }
  }
---

# Skill title

Instructions for when and how to use tools...
```

### Gating (load-time filters)

Skills are **filtered at load time** via `metadata.openclaw`:

| Field | Meaning |
|-------|---------|
| `requires.bins` | Each binary must exist on PATH |
| `requires.anyBins` | At least one must exist |
| `requires.env` | Env var or config must exist |
| `requires.config` | Config path(s) must be truthy |
| `requires.os` | e.g. `["darwin","linux"]` |
| `always: true` | Skip other gates; always include |

If gating fails, the skill is **not** injected into the prompt. Use `openclaw skills check --json` to see eligible vs missing.

### Config overrides (`openclaw.json`)

```json5
{
  "skills": {
    "entries": {
      "nano-banana-pro": {
        "enabled": true,
        "apiKey": "GEMINI_KEY",
        "env": { "GEMINI_API_KEY": "..." },
        "config": { "model": "nano-pro" }
      },
      "peekaboo": { "enabled": false }
    },
    "allowBundled": ["gemini", "oracle", ...]  // only these bundled skills load
  }
}
```

- `enabled: false` disables the skill.
- `env` is injected only if the variable is not already set.
- `allowBundled`: when set, **only** listed bundled skills are eligible (workspace/managed unchanged).

### ClawHub (skill registry)

- **Browse/install**: https://clawhub.com  
- **Install into workspace**: `clawhub install <skill-slug>`  
- **Update all**: `clawhub update --all`  
- **Sync/publish**: `clawhub sync --all`

Default install target is `./skills` under cwd or the configured workspace.

### Creating a custom skill

1. Create directory: `<workspace>/skills/<skill-name>/`
2. Add `SKILL.md` with frontmatter (`name`, `description`) and instructions.
3. Optionally add scripts in the same directory; reference with `{baseDir}` in the skill text.
4. Restart gateway or rely on skills watcher; new sessions will see the skill.

Keep instructions concise and tool-focused; avoid arbitrary command injection from user input.

**Token impact:** Eligible skills are injected as a compact XML list into the system prompt. Per-skill overhead is roughly ~97 characters plus name/description/location length; base overhead ~195 characters when at least one skill is present. Session snapshot is taken when the session starts; skills watcher can hot-reload on file changes.

---

## 6. Scheduling: Heartbeat vs Cron

### Heartbeat

- **What**: Periodic agent turns in the **main** session. The agent receives a fixed prompt (e.g. “Read HEARTBEAT.md and follow it strictly…”).
- **When**: Interval set by `agents.defaults.heartbeat.every` (e.g. `30m`, `2h`). Can restrict to `activeHours` (local timezone).
- **Response contract**: Reply `HEARTBEAT_OK` when nothing needs attention; otherwise return alert/actions. OpenClaw can strip/drop the ack.
- **Use case**: General “check in” loop—sensors, inbox, reminders, HEARTBEAT.md checklist. In this project, HEARTBEAT.md defines the full autonomous loop (sensor check, grow decisions, social, research, etc.).

### Cron

- **What**: Gateway’s built-in scheduler. Jobs persist (e.g. `~/.openclaw/cron/jobs.json` or `cron.store` path); run inside the Gateway process.
- **Two execution styles**:
  - **Main session** (`sessionTarget: "main"`): Enqueue a **system event**; runs on next heartbeat (or immediately with `wakeMode: "now"`).
  - **Isolated** (`sessionTarget: "isolated"`): Dedicated agent turn in session `cron:<jobId>`; optional delivery to a channel.
- **Schedules**: One-shot (`at`), interval (`every`), or cron expression (`cron` + optional IANA timezone).

**When to use which (decision guide):**

| Use case | Prefer | Reason |
|----------|--------|--------|
| Check inbox / sensors every N min | Heartbeat | Batches with other checks, context-aware |
| Send daily report at 9:00 sharp | Cron (isolated) | Exact timing, optional delivery to channel |
| Monitor calendar / reminders | Heartbeat | Fits periodic awareness |
| Weekly deep analysis | Cron (isolated) | Standalone; can use different model/thinking |
| Remind me in 20 minutes | Cron (main, `--at`) | One-shot, precise |
| Background health check | Heartbeat | Piggybacks on existing cycle |

- **Heartbeat**: Recurring “main context” loop (same session, same HEARTBEAT.md). Batch multiple checks in one turn to reduce API cost.
- **Cron**: One-off reminders, time-bound tasks, or isolated jobs that should not clutter main chat (e.g. “daily digest to Telegram”). Use **isolated** when you want a clean session, model override, or direct delivery; use **main** + system event when you want the next heartbeat to see the event in full context.

**Lobster (approval pipelines):** For **multi-step workflows with explicit approvals** (e.g. “water plant only after I approve”), use the **lobster** extension. Heartbeat/cron decide *when* a run happens; Lobster defines *what steps* run and where to pause for approval. The agent invokes the Lobster tool with a pipeline spec; if the pipeline pauses, it returns a `resumeToken` so you can approve and resume without re-running earlier steps. Enable via `plugins.entries.lobster.enabled` and allow the tool (e.g. `tools.alsoAllow: ["lobster"]`). See `openclaw/docs/tools/lobster.md`.

### Cron CLI examples

```bash
# One-shot reminder (main session, wake now)
openclaw cron add --name "Reminder" --at "2026-02-01T16:00:00Z" \
  --session main --system-event "Reminder: check X" --wake now --delete-after-run

# Recurring isolated job with delivery
openclaw cron add --name "Morning brief" --cron "0 7 * * *" --tz "America/Los_Angeles" \
  --session isolated --message "Summarize overnight." --deliver --channel telegram --to "-1003584948806"

# List / run / history
openclaw cron list
openclaw cron run <jobId> --force
openclaw cron runs --id <jobId> --limit 50
```

**Store location**: Default `~/.openclaw/cron/jobs.json`. This project sets `cron.store` to `cron/cron.json` (relative to workspace root), so the canonical store is `openclaw-workspace/cron/cron.json`. The **active store** is the one in config—verify there, not only `~/.openclaw/cron/`.

---

## 7. Gateway: Run, Config, and CLI

### How to run

```bash
openclaw gateway run --bind loopback --port 18789 --force
# or
openclaw gateway --port 18789 --verbose
```

- **Port precedence**: `--port` > `OPENCLAW_GATEWAY_PORT` > `gateway.port` in config > default `18789`.
- **Bind**: `loopback` (127.0.0.1) is typical; avoid `0.0.0.0` without auth.
- **`--force`**: Kill existing listeners on the port, then start (useful when port is stuck).
- **`--verbose`**: Mirror debug logs to stdio.

### Critical CLI gotchas

- **No `--config` flag**: OpenClaw **always** reads `~/.openclaw/openclaw.json`. You cannot pass a config path. Deploy by copying/syncing the file to that path.
- **No `openclaw gateway start`/`restart`**: Those are for a separate daemon/service. When the gateway is managed by `run.py all`, start/stop is via the parent process.
- **Config hot reload**: Gateway watches the config file; `gateway.reload.mode` (e.g. `hybrid`) applies safe changes without full restart; critical changes may trigger in-process restart (SIGUSR1).
- **Project caveat (`run.py all`)**: avoid routine `openclaw gateway run --force` in this stack; forcing listeners can create duplicate/flapping gateway behavior when the Python supervisor already owns lifecycle.

### Config rules (v2026.2.9 and similar)

- No top-level `identity`; use `agents.list[].identity`.
- When using `bind: "loopback"`, omit or adjust `gateway.auth` if you don’t need token auth.
- Use **absolute paths** for workspaces and cron store (no relative `../ganjamon`).
- All `${VAR}` in config must have corresponding env vars set on the host, or the gateway can crash.

---

## 8. Configuration Reference

Key sections in `~/.openclaw/openclaw.json`:

| Section | Purpose |
|--------|---------|
| `agents.defaults` | Workspace, model (primary + fallbacks), heartbeat, timeout, timezone |
| `agents.list[]` | Per-agent id, workspace, heartbeat overrides, identity |
| `channels` | Telegram, Discord, Slack, etc.: tokens, allowlists, groups |
| `gateway` | port, bind, controlUi, reload |
| `skills` | entries (per-skill enabled/env/config), allowBundled, load.extraDirs, load.watch |
| `cron` | enabled, store, maxConcurrentRuns |
| `tools` | allow/deny lists, exec timeouts |
| `plugins.entries` | telegram, discord, lobster, memory-core, etc. |
| `env.vars` | Key-value env injected into agent runs (or use shellEnv) |

Example minimal agent + heartbeat:

```json5
{
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      "model": { "primary": "anthropic/claude-sonnet-4-20250514", "fallbacks": [] },
      "heartbeat": { "every": "30m", "target": "last" }
    },
    "list": [{ "id": "main", "default": true, "workspace": "~/.openclaw/workspace" }]
  }
}
```

---

## 9. Channels & Multi-Agent

### Channels

OpenClaw supports many messaging channels (built-in and extensions). Each has its own config block (e.g. `channels.telegram`, `channels.discord`). Common settings:

- **Telegram**: `botToken` (or `TELEGRAM_BOT_TOKEN`), `groups`, `allowFrom`, `groupPolicy`, `requireMention`.
- **Discord**: `token`, `guildIds`, `dm.allowFrom`.
- **Slack**: `botToken`, `appToken`.

Security: Default DM policy is often “pairing” (unknown users get a pairing code). Use `openclaw doctor` to check risky policies.

### Multi-agent

You can run **multiple agents** from one Gateway:

- Each agent has its own **workspace** (files, memory, skills).
- Each has its own **sessions** and chat history.
- **Routing**: Map channels/peers to agent IDs (e.g. WhatsApp → personal, Slack → work).
- **Cron**: Jobs can target a specific agent via `agentId`.

Useful for: separate personal vs work assistants, or different models per agent (e.g. fast model for chat, slow “thinking” model for deep tasks).

---

## 10. Integration in This Project

- **OpenClaw as primary orchestrator**: Python is the HAL (Hardware Abstraction Layer). OpenClaw runs the heartbeat and skills; skills call the FastAPI HAL at `http://localhost:8000` for sensors, actuators, trading, social, and blockchain.
- **Process model**: `python run.py all` starts FastAPI (HAL), OpenClaw gateway (e.g. 60s delayed, nice +10), and the GanjaMon trading subprocess. A watchdog respawns the gateway or trading process if they crash.
- **Workspace**: `openclaw-workspace/ganjamon/` (SOUL.md, HEARTBEAT.md, TOOLS.md, custom skills). Config: `openclaw-workspace/config/openclaw.json` → deploy to `~/.openclaw/openclaw.json` on Chromebook.
- **Cron store**: `openclaw-workspace/cron/cron.json` when `cron.store` is set to `cron/cron.json` (relative to workspace or configured base). This is the **source of truth** for scheduled jobs; `openclaw cron list` can lag—inspect the store file to verify.
- **Deploy**: Sync config via stdin pipe to `cat > ~/.openclaw/openclaw.json`; start/restart via `run.py` (no standalone `openclaw gateway start`). See `docs/OPENCLAW_INTEGRATION.md` for exact commands and incident notes.

### Off-LAN Chromebook Admin (Project-Specific)

When traveling/off local network, remote admin works via Cloudflare tunnels:

- Main tunnel: `https://grokandmon.com` (HAL on `:8000`)
  - Auth endpoint: `POST /api/auth/token`
  - Credential: `ADMIN_JWT_PASSWORD`
- Agent tunnel: `https://agent.grokandmon.com` (admin endpoint on `:8080`)
  - Auth endpoint: `POST /auth/token`
  - Credential: `ADMIN_PASSWORD` (set in `.env`)

Quick checks:

```bash
curl -s https://grokandmon.com/api/admin/ping
curl -s https://agent.grokandmon.com/admin/ping
```

Recommended helper:

```bash
scripts/chromebook_remote_admin.sh ping
scripts/chromebook_remote_admin.sh status
scripts/chromebook_remote_admin.sh exec "hostname && date -Is"
```

---

## 11. Tools System

OpenClaw exposes **first-class agent tools** (browser, canvas, nodes, cron, exec, sessions, message, etc.). The agent sees both a human-readable list in the system prompt and structured tool schemas sent to the model API.

### Allow / deny

- **Global**: `tools.allow` and `tools.deny` in `openclaw.json` (deny wins). Case-insensitive; `*` wildcards supported.
- **Per-agent**: `agents.list[].tools.profile`, `agents.list[].tools.allow`, `agents.list[].tools.deny`.
- **By provider**: `tools.byProvider["provider/model"]` can narrow the tool set for specific models (e.g. minimal tools for a flaky endpoint).

### Tool profiles (base allowlist)

| Profile | Tools included |
|---------|----------------|
| `minimal` | `session_status` only |
| `coding` | `group:fs`, `group:runtime`, `group:sessions`, `group:memory`, `image` |
| `messaging` | `group:messaging`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status` |
| `full` | No restriction (default when unset) |

### Tool groups (shorthands)

Use in `tools.allow` / `tools.deny`:

- `group:runtime` → `exec`, `bash`, `process`
- `group:fs` → `read`, `write`, `edit`, `apply_patch`
- `group:sessions` → `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `session_status`
- `group:memory` → `memory_search`, `memory_get`
- `group:web` → `web_search`, `web_fetch`
- `group:ui` → `browser`, `canvas`
- `group:automation` → `cron`, `gateway`
- `group:messaging` → `message`
- `group:nodes` → `nodes`
- `group:openclaw` → all built-in OpenClaw tools (excludes provider plugins)

### Key tools (summary)

- **exec / process**: Run shell commands; background with `yieldMs`/`background`; manage via `process` (list, poll, log, kill). Timeout, elevated mode, and host (sandbox/gateway/node) configurable.
- **browser**: OpenClaw-managed Chrome/Chromium; snapshot (aria/ai), act (click/type), screenshot, navigate. Profile support; can target node for remote browser.
- **canvas**: Present, A2UI push/reset, snapshot; uses `node.invoke` when a node is connected.
- **nodes**: Discover paired nodes; notify, run (macOS `system.run`), camera_snap, screen_record, location_get.
- **message**: Send/react/read/edit/delete across Discord, Slack, Telegram, WhatsApp, etc.; channel-specific actions (polls, threads, pins).
- **cron**: status, list, add, update, remove, run, runs, wake (system event + optional immediate heartbeat).
- **gateway**: restart (SIGUSR1), config.get/apply/patch, update.run (when enabled).
- **sessions_list / sessions_history / sessions_send / sessions_spawn**: Cross-session messaging and sub-agent runs; reply-back ping-pong and announce step configurable.

Plugins can register additional tools (e.g. **lobster** for approval pipelines, **llm-task** for structured LLM steps in workflows). See `openclaw/docs/tools/index.md` for full inventory and parameters.

---

## 12. Agent Loop & Lifecycle

The **agent loop** is the full run: intake → context assembly → model inference → tool execution → streaming → persistence. One run per session at a time; queueing keeps session state consistent.

### Entry points

- **Gateway RPC**: `agent` (returns `runId` immediately), `agent.wait` (waits for lifecycle end/error).
- **CLI**: `openclaw agent --message "..."`.

### Flow (high-level)

1. Validate params, resolve session (sessionKey/sessionId), persist session metadata.
2. Resolve model + thinking/verbose defaults; load skills snapshot.
3. **runEmbeddedPiAgent**: serialize runs via per-session (and optional global) queue; build pi session; subscribe to pi events; enforce timeout (abort if exceeded).
4. Stream events: `lifecycle` (phase start/end/error), `assistant` (deltas), `tool` (tool start/update/end).
5. Reply shaping: assistant text, optional reasoning, inline tool summaries; `NO_REPLY` filtered; messaging duplicates removed.

### Queueing

Runs are **serialized per session key** (and optionally global lane). Prevents tool/session races and keeps history consistent. Channels can use queue modes (collect/steer/followup) that feed this lane.

### Hooks (where you can intercept)

- **Gateway hooks**: `agent:bootstrap` (before system prompt finalized; can mutate bootstrap files), command hooks (`/new`, `/reset`, `/stop`).
- **Plugin hooks**: `before_agent_start`, `agent_end`, `before_compaction`/`after_compaction`, `before_tool_call`/`after_tool_call`, `tool_result_persist`, `message_received`/`message_sending`/`message_sent`, `session_start`/`session_end`, `gateway_start`/`gateway_stop`.

### Timeouts

- **agent.wait**: default 30s (wait only); `timeoutMs` overrides.
- **Agent runtime**: `agents.defaults.timeoutSeconds` (default 600s); enforced in runEmbeddedPiAgent.

See `openclaw/docs/concepts/agent-loop.md` for full lifecycle and event streams.

---

## 13. Hooks

Hooks are **event-driven handlers** that run when agent commands or lifecycle events fire (e.g. `/new`, `/reset`, gateway startup). They are discovered from directories and enabled via config or CLI—similar to skills.

### Discovery (precedence)

1. **Workspace hooks**: `<workspace>/hooks/` (per-agent, highest).
2. **Managed hooks**: `~/.openclaw/hooks/` (shared).
3. **Bundled hooks**: shipped with OpenClaw (e.g. in `dist/hooks/bundled/`).

Each hook is a directory with `HOOK.md` (metadata + docs) and `handler.ts` (or `index.ts`). Hook packs can be npm packages that export multiple hooks via `openclaw.hooks` in `package.json`.

### HOOK.md format

YAML frontmatter plus Markdown. In `metadata.openclaw`: `events` (e.g. `["command:new", "command:reset"]`), `emoji`, `requires` (bins, env, config, os), `export` (handler name).

### Event types

- **Command**: `command`, `command:new`, `command:reset`, `command:stop`
- **Agent**: `agent:bootstrap` (before bootstrap files injected)
- **Gateway**: `gateway:startup`

### Bundled hooks (examples)

- **session-memory**: Saves session context to workspace `memory/YYYY-MM-DD-slug.md` on `/new`.
- **command-logger**: Logs command events to `~/.openclaw/logs/commands.log` (JSONL).
- **soul-evil**: Swaps SOUL.md with SOUL_EVIL.md (purge window or random chance).
- **boot-md**: Runs `BOOT.md` on gateway start (after channels start).

### Config

```json5
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "session-memory": { "enabled": true },
        "command-logger": { "enabled": false }
      }
    }
  }
}
```

CLI: `openclaw hooks list`, `openclaw hooks enable/disable <name>`, `openclaw hooks check`, `openclaw hooks info <name>`. See `openclaw/docs/hooks.md` for handler API and troubleshooting.

---

## 14. Plugins & Extensions

Plugins are **TypeScript modules** that extend OpenClaw with extra channels, tools, CLI commands, Gateway RPC, and skills. They run in-process with the Gateway (trusted code).

### What plugins can register

- Channels (e.g. Microsoft Teams, Matrix, Nostr, Zalo)
- Agent tools
- CLI commands
- Gateway RPC methods and HTTP handlers
- Skills (directories listed in plugin manifest)
- Auto-reply commands (no AI invocation)
- Background services

### Discovery

1. `plugins.load.paths` (config)
2. Workspace: `<workspace>/.openclaw/extensions/*.ts` or `*/index.ts`
3. npm: `@openclaw/*` and other configured packages

### Manifest (openclaw.plugin.json)

Plugin declares `id`, `channels`, `skills`, `configSchema`, etc. Config validation uses the manifest and JSON Schema; plugin code is not executed at config load time.

### Install (example)

```bash
openclaw plugins list
openclaw plugins install @openclaw/voice-call
```

Then configure under `plugins.entries.<id>.enabled` and optional `config`. Official plugins include Microsoft Teams (`@openclaw/msteams`), Voice Call, Matrix, Nostr, Zalo, memory-core/memory-lancedb, and provider-auth plugins (e.g. google-antigravity-auth). See `openclaw/docs/plugin.md` and `openclaw/docs/plugins/agent-tools.md` for authoring tools.

---

## 15. Security & Model Failover

### Security

- **Audit**: Run `openclaw security audit` (and `--deep`, `--fix`) to flag open DM/group policies, auth exposure, browser control exposure, permissions. `--fix` can tighten group policies and file permissions.
- **Credential storage**: WhatsApp creds, pairing allowlists, model auth profiles live under `~/.openclaw/credentials/` and `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`. Keep these dirs and config (`~/.openclaw`) not world-readable (e.g. 700/600).
- **DM policy**: Default is often “pairing” (unknown users get a pairing code). Use `openclaw doctor` to surface risky policies; avoid `dmPolicy="open"` with `"*"` allowlist unless intentional.
- **Sandboxing**: Non-main sessions (e.g. groups) can run in per-session Docker sandboxes (`agents.defaults.sandbox.mode: "non-main"`). Tool allowlists and denylists apply inside the sandbox.
- **Control UI**: Prefer HTTPS or localhost; `gateway.controlUi.allowInsecureAuth` and `dangerouslyDisableDeviceAuth` are security downgrades.

### Model failover

OpenClaw handles failures in two stages:

1. **Auth profile rotation** within the current provider (round-robin by type and usage; cooldowns move failed profiles to end).
2. **Model fallback** to the next model in `agents.defaults.model.fallbacks`.

Auth profiles (API keys and OAuth) live in `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`. Session stickiness: the chosen profile is pinned per session until reset, compaction, or cooldown. Rate limits and errors can trigger cooldowns; user-pinned profiles (e.g. via `/model …@profileId`) stay locked and only model fallback applies. See `openclaw/docs/concepts/model-failover.md` for cooldown rules and provider behavior.

### Doctor

`openclaw doctor` runs health checks, config migrations, and repair steps (skills status, auth health, permissions, gateway port, security warnings). Use `--yes` / `--repair` / `--non-interactive` for automation. Run after config or env changes.

---

## 16. Troubleshooting

### First checks

```bash
openclaw status
openclaw status --all
openclaw gateway probe
openclaw logs --follow
openclaw doctor
```

### Cron “nothing runs”

- Cron is **inside the Gateway**; ensure the Gateway is running continuously.
- If cron runs are healthy but gateway responsiveness drops with errors like `Subagent announce failed: gateway timeout`, switch cron job delivery to non-announcing (`delivery.mode = "none"` in the active cron store) so long isolated runs do not block delivery lanes.
- If a heavy isolated job runs across the next job's due time, OpenClaw can skip the missed slot and move that job to its next future schedule (when catch-up suppression is in effect). Stagger heavy jobs (for example >=20 min apart) to avoid silent skips.
- Verify `cron.enabled` is true and `OPENCLAW_SKIP_CRON` is not set.
- Confirm **store path**: if `cron.store` is set (e.g. `cron/cron.json`), the active store is that path (relative to config or workspace); jobs in `~/.openclaw/cron/jobs.json` may be ignored.
- For cron schedules: check timezone (`--tz`) vs host timezone; ensure `enabled: true` on the job.

### Gateway crash loop / won’t start

- **No `--config` flag**: OpenClaw always reads `~/.openclaw/openclaw.json`. Wrong path or missing file → fail. Deploy config to that path.
- **Invalid config**: Top-level `identity` deprecated (use `agents.list[].identity`); `gateway.auth.token` referencing missing `${OPENCLAW_GATEWAY_TOKEN}` can crash; remove auth section when using `bind: "loopback"` if you don’t set the var.
- **Relative paths**: Use absolute paths for workspaces and cron store; `${VAR}` must be set in the environment.
- **Port in use**: Use `openclaw gateway run --force` to kill listeners on the port, then start.

### “openclaw: command not found”

Node/npm PATH issue. Ensure `openclaw` (or npx openclaw) is on PATH after install; check Node version (≥22).

### Model / auth failures

- Run `openclaw doctor` for auth profile and cooldown status.
- Check `agents.defaults.model.primary` and `fallbacks`; ensure API keys or OAuth are set for the chosen provider.
- If `/model` says “model not allowed”, check `agents.defaults.models` allowlist (if set) and add the model or clear it.

### Skills not loading

- `openclaw skills check --json` shows eligible vs missing (bins, env, config).
- If using `allowBundled`, only listed bundled skills load; workspace/managed skills unaffected.
- Session snapshot: skills are fixed at session start; restart session or rely on skills watcher for file changes.

See `openclaw/docs/help/troubleshooting.md` and `openclaw/docs/gateway/troubleshooting.md` for more.

---

## 17. Official Docs & Resources

| Resource | URL |
|----------|-----|
| **Website** | https://openclaw.ai |
| **Docs (primary)** | https://docs.openclaw.ai |
| **Getting started** | https://docs.openclaw.ai/start/getting-started |
| **Wizard** | https://docs.openclaw.ai/start/wizard |
| **Gateway runbook** | https://docs.openclaw.ai/gateway |
| **Full configuration** | https://docs.openclaw.ai/gateway/configuration |
| **Skills** | https://docs.openclaw.ai/tools/skills |
| **Cron & heartbeat** | https://www.getopenclaw.ai/help/cron-heartbeat-automation |
| **ClawHub** | https://clawhub.com |
| **Discord** | https://discord.gg/clawd |
| **GitHub** | https://github.com/openclaw/openclaw |
| **DeepWiki** | https://deepwiki.com/openclaw/openclaw |

### In-repo references

- **Integration & deployment**: `docs/OPENCLAW_INTEGRATION.md`
- **Framework deep dive (code-level)**: `docs/OPENCLAW_FRAMEWORK_DEEP_DIVE.md`
- **Cloned framework docs**: `openclaw/docs/` (automation, channels, cli, gateway, tools, concepts, hooks, plugin, security)
- **Workspace agent**: `openclaw-workspace/ganjamon/` (HEARTBEAT.md, TOOLS.md, skills)
- **Agent loop**: `openclaw/docs/concepts/agent-loop.md`
- **Cron vs heartbeat**: `openclaw/docs/automation/cron-vs-heartbeat.md`
- **Model failover**: `openclaw/docs/concepts/model-failover.md`
- **Hooks**: `openclaw/docs/hooks.md`
- **Plugins**: `openclaw/docs/plugin.md`
- **Security**: `openclaw/docs/gateway/security/index.md`
- **Doctor**: `openclaw/docs/gateway/doctor.md`
- **Troubleshooting**: `openclaw/docs/help/troubleshooting.md`, `openclaw/docs/gateway/troubleshooting.md`

---

*This guide was assembled and expanded from the cloned OpenClaw repo, openclaw-workspace, project documentation, and official OpenClaw documentation (February 2026). Sections 11–16 added via deeper research and sequential thinking.*
