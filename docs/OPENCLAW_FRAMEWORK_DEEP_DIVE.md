# OpenClaw Framework Deep Dive

**Last Updated:** February 5, 2026
**Source:** Comprehensive analysis of `/mnt/c/Users/natha/sol-cannabis/openclaw/`

**For a single consolidated guide (concepts, skills, cron, config, CLI, integration), see [OPENCLAW_GUIDE.md](OPENCLAW_GUIDE.md).**

## Overview

OpenClaw is a **personal AI assistant framework** that runs on your own devices, combining:
- **Local-first Gateway** (control plane for sessions, channels, tools, events)
- **Embedded Pi-Mono Agent Runtime** (RPC-based AI decision engine)
- **Multi-channel Inbox** (12+ messaging surfaces)
- **Workspace-based Memory** (persistent agent identity & context)
- **Plugin/Extension System** (pluggable channels, tools, skills, hooks)

**Key Philosophy:** Single-user, always-on, feels local and fast.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw CLI & Gateway                   │
├─────────────────────────────────────────────────────────────┤
│  ├─ Gateway (WebSocket RPC server)                          │
│  ├─ Session Router (per-channel, per-user routing)          │
│  ├─ Plugin/Extension Manager                                │
│  ├─ Tool Registry (browser, canvas, exec, etc.)             │
│  └─ Config Manager (JSON5, validated schema)                │
├─────────────────────────────────────────────────────────────┤
│ Channels (12+): WhatsApp, Telegram, Slack, Discord, etc.   │
├─────────────────────────────────────────────────────────────┤
│ Embedded Pi-Mono Agent Runtime                              │
│  ├─ Tool Execution                                          │
│  ├─ Model Provider Selection                                │
│  ├─ Auth Profile Failover                                   │
│  └─ Memory/Session Management                               │
├─────────────────────────────────────────────────────────────┤
│ Agent Workspace (~/.openclaw/workspace)                      │
│  ├─ AGENTS.md (operating instructions)                      │
│  ├─ SOUL.md (persona & boundaries)                          │
│  ├─ TOOLS.md (tool conventions)                             │
│  ├─ IDENTITY.md (agent name/emoji)                          │
│  ├─ USER.md (user profile)                                  │
│  ├─ skills/ (workspace-specific skills)                     │
│  └─ memory/ (daily logs + long-term memory)                 │
├─────────────────────────────────────────────────────────────┤
│ Config (~/.openclaw/openclaw.json)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
openclaw/
├─ src/
│  ├─ agents/          # Agent runtime, auth profiles, tools
│  ├─ channels/        # Core channel implementations
│  ├─ cli/             # CLI commands & wiring
│  ├─ commands/        # CLI command handlers
│  ├─ config/          # Config schema & validation
│  ├─ gateway/         # Gateway server & session management
│  ├─ hooks/           # Hook system (boot, memory, soul-evil)
│  ├─ plugins/         # Plugin runtime & registration
│  ├─ plugin-sdk/      # Public plugin SDK exports
│  ├─ providers/       # Model providers (Anthropic, OpenAI, etc.)
│  ├─ routing/         # Message routing logic
│  ├─ sessions/        # Session storage & retrieval
│  ├─ skills/          # Skill loading & management
│  └─ telegram/discord/slack/signal/imessage/web/  # Channel impls
├─ extensions/         # Plugin channels (Discord, Telegram, Teams, Matrix, etc.)
├─ skills/             # Bundled skills (60+ skill directories)
├─ packages/           # Published packages (clawdbot, moltbot)
├─ docs/               # Mintlify documentation
├─ apps/               # Native apps (macOS, iOS, Android)
└─ ui/                 # Web dashboard & Control UI
```

---

## Supported Messaging Channels (12+)

### Built-in Channels (in `src/`)
| Channel | Library | Config Key |
|---------|---------|------------|
| Telegram | grammY | `channels.telegram` |
| Discord | discord.js | `channels.discord` |
| Slack | @slack/bolt | `channels.slack` |
| WhatsApp | Baileys (web) | `channels.whatsapp` |
| Signal | signal-cli | `channels.signal` |
| iMessage | Native (macOS/iOS) | `channels.imessage` |
| Google Chat | Chat API | `channels.googlechat` |
| WebChat | Browser | — |

### Extension Channels (in `extensions/`)
- Microsoft Teams
- Matrix
- Zalo / Zalo Personal
- BlueBubbles (iMessage relay)
- Mattermost
- Nextcloud Talk
- Line
- Nostr
- Twitch
- Tlon (Urbit)
- Voice Call (ElevenLabs)

---

## Skills System

### What Are Skills?

Skills are **instructional guides** (Markdown files with YAML frontmatter) that teach the agent how to use tools. They are **not executable code** — they're documentation that gets injected into the agent's system prompt.

### Skill Locations & Precedence

```
1. <workspace>/skills/        (highest precedence)
2. ~/.openclaw/skills/        (managed/local)
3. bundled skills/            (lowest precedence)
4. plugin-provided skills/    (via openclaw.plugin.json)
```

### Skill Format

**File:** `skills/<skill-name>/SKILL.md`

```markdown
---
name: discord
description: Use when you need to control Discord
metadata: {
  "openclaw": {
    "emoji": "🎮",
    "requires": {
      "config": ["channels.discord"],
      "bins": ["ffmpeg"],
      "env": ["DISCORD_BOT_TOKEN"]
    }
  }
}
---

# Discord Actions

Use the `discord` tool to:
- Send messages
- React to messages
- Manage threads & pins

## Send a message

\`\`\`json
{
  "action": "sendMessage",
  "to": "channel:123",
  "content": "Hello from OpenClaw"
}
\`\`\`
```

### Skill Gating

Metadata gates determine when a skill loads:
- `bins` - Binary must exist on PATH
- `anyBins` - At least one must exist
- `env` - Env var or config must exist
- `config` - Config path must be truthy
- `os` - Platform restriction (darwin, linux)

---

## Agent Workspace Files

The agent workspace contains **six core memory files** that define personality and behavior:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Operating instructions, rules, memory usage |
| `SOUL.md` | Persona, tone, boundaries |
| `USER.md` | User profile, preferred address |
| `IDENTITY.md` | Agent name, vibe, emoji |
| `TOOLS.md` | Tool conventions & usage notes |
| `HEARTBEAT.md` | Lightweight checklist (keep short) |
| `BOOTSTRAP.md` | One-time initialization ritual |
| `memory/YYYY-MM-DD.md` | Daily memory log |
| `MEMORY.md` | Long-term curated memory |

**Injection Logic:**
- All non-missing bootstrap files are concatenated and prepended to the system prompt
- Large files are truncated (default: 20KB per file)
- `openclaw setup` creates safe defaults

---

## Plugin System

### Plugin SDK (`openclaw/plugin-sdk`)

```typescript
export type OpenClawPluginApi = {
  runtime: PluginRuntime;
  registerChannel: (reg: OpenClawPluginChannelRegistration) => void;
  registerTool: (options: OpenClawPluginToolOptions) => void;
  registerHook: (options: OpenClawPluginHookOptions) => void;
  registerProvider: (provider: ProviderAuthHandler) => void;
};
```

### Plugin Manifest (`openclaw.plugin.json`)

```json
{
  "id": "telegram",
  "channels": ["telegram"],
  "skills": ["./skills"],
  "configSchema": { "type": "object" }
}
```

### Creating a Plugin

```typescript
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

const plugin = {
  id: "myplugin",
  name: "My Plugin",
  register(api: OpenClawPluginApi) {
    api.registerChannel({ plugin: myChannelPlugin });
    api.registerTool({ name: "mytool", factory: myToolFactory });
    api.registerHook({ entry: { name: "my-hook", handler: myHook }, register: true });
  },
};

export default plugin;
```

---

## Hooks System

Hooks are **event-driven handlers** that run on specific Gateway or agent events.

### Hook Events
- `gateway:startup` / `gateway:shutdown`
- `agent:bootstrap` / `agent:after-turn`
- `message:route`
- `cron:{schedule}`

### Bundled Hooks
- `boot-md` - Run BOOT.md checklist on restart
- `session-memory` - Auto-flush memory after session
- `soul-evil` - Swap SOUL.md with SOUL_EVIL.md (alt persona)
- `command-logger` - Log messages to workspace

---

## CLI Commands

| Command | Purpose |
|---------|---------|
| `openclaw onboard` | Interactive setup wizard |
| `openclaw gateway` | Start WebSocket control plane |
| `openclaw agent --message "..."` | Run agent directly |
| `openclaw message send` | Send message to channel |
| `openclaw channels status` | Show channel status |
| `openclaw config set` | Update config |
| `openclaw doctor` | Diagnose issues |
| `clawhub install <skill>` | Install skill |
| `clawhub update --all` | Update all skills |

---

## Tools & Capabilities

### Tool Groups
| Group | Tools | Purpose |
|-------|-------|---------|
| Filesystem | read, write, edit, apply_patch | File operations |
| Runtime | exec, bash, process | Command execution |
| Sessions | sessions_list, sessions_history | Session navigation |
| Memory | memory_search, memory_get, memory_flush | Agent memory |
| Browser | browser (Playwright) | Web automation |
| Canvas | canvas (A2UI) | Interactive UI |
| Web | web_search, web_fetch | Internet access |
| Messaging | Channel-specific | Discord, Slack, etc. |
| Cron | cron_register | Schedule tasks |

### Tool Profiles
- `minimal` → session_status only
- `coding` → fs, runtime, sessions, memory, image
- `messaging` → messaging, sessions
- `full` → all tools

---

## Configuration (`~/.openclaw/openclaw.json`)

```json5
{
  agents: {
    defaults: { workspace: "~/.openclaw/workspace" },
    list: [
      { id: "main", workspace: "~/.openclaw/workspace", model: "anthropic/claude-opus-4-5" }
    ]
  },
  channels: {
    telegram: { allowFrom: ["+15555550123"] },
    discord: { guildIds: ["123456789"] }
  },
  tools: {
    profile: "coding",
    allow: ["browser"],
    deny: ["exec"]
  },
  skills: {
    load: { extraDirs: ["~/my-skills"] }
  }
}
```

---

## Integration with GanjaMon

### Creating a Trading Skill

**File:** `~/.openclaw/workspace/skills/ganjamon-trading/SKILL.md`

```markdown
---
name: ganjamon-trading
description: Trading operations for $MON token
metadata: {
  "openclaw": {
    "emoji": "🍃",
    "requires": { "env": ["MON_TRADING_API_KEY"] }
  }
}
---

# GanjaMon Trading

Use the `ganjamon_trade` tool to execute trading strategies:

## Check Price
\`\`\`json
{ "action": "get_price", "token": "MON", "chain": "monad" }
\`\`\`

## Execute Trade
\`\`\`json
{ "action": "swap", "fromToken": "USDC", "toToken": "MON", "amount": "1000" }
\`\`\`
```

### Building a Trading Plugin

```typescript
api.registerTool({
  name: "ganjamon_trade",
  factory: (ctx) => ({
    name: "ganjamon_trade",
    description: "Execute $MON trading strategies",
    inputSchema: {
      type: "object",
      properties: {
        action: { type: "string", enum: ["swap", "get_price", "liquidity_check"] },
        fromToken: { type: "string" },
        toToken: { type: "string" },
        amount: { type: "string" },
        chain: { type: "string" },
      },
    },
    async execute(params) {
      const result = await callGanjaMonTradingAPI(params);
      return { success: true, data: result };
    },
  }),
});
```

---

## Key Learnings

1. **Skills are documentation, not code** - They teach agents via system prompt injection
2. **Workspace files define identity** - SOUL.md, AGENTS.md, IDENTITY.md shape behavior
3. **Plugins register at runtime** - Channels, tools, hooks all use the same SDK
4. **12+ messaging channels** - Telegram, Discord, WhatsApp, Signal, iMessage, Teams, etc.
5. **Memory is file-based** - Daily logs in `memory/YYYY-MM-DD.md`, long-term in `MEMORY.md`
6. **Hooks enable automation** - Run code on startup, after turns, on cron schedules
7. **Tool profiles control access** - Allowlists/denylists for security
8. **ClawHub is the skill marketplace** - Install, update, sync skills

---

## References

- OpenClaw Docs: https://docs.clawd.bot
- ClawHub (Skill Marketplace): https://clawhub.com
- Repository: `/mnt/c/Users/natha/sol-cannabis/openclaw/`
