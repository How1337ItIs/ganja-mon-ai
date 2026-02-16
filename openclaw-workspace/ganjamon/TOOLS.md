# TOOLS.md — GanjaMon Skill & Tool Manifest

## Built-in OpenClaw Skills (16 active)

### Content & Intelligence
| Skill | Command | Use Case |
|-------|---------|----------|
| `gemini` | `gemini "prompt"` | Quick Q&A, content ganjafy, Rasta voice generation |
| `nano-banana-pro` | `uv run nano-banana-pro.py --prompt "..."` | Gemini 3 Pro image gen/edit, plant photos, memes |
| `oracle` | `oracle --prompt "..." --files file1 file2` | GPT-5.2 Pro deep think, multi-file review, strategy |
| `summarize` | `summarize <url>` | Summarize articles, PDFs, YouTube for research |
| `blogwatcher` | `blogwatcher scan --config feeds.yaml` | Monitor RSS/Atom feeds for crypto/cannabis news |
| `weather` | `weather "Los Angeles"` | Outdoor conditions affecting grow environment |

### Development & Ops
| Skill | Command | Use Case |
|-------|---------|----------|
| `github` | `gh issue list`, `gh pr view` | Issue triage, PR monitoring, CI checks |
| `coding-agent` | `coding-agent run "task"` | Background PTY for Ralph loops, automated fixes |
| `skill-creator` | `skill-creator init`, `skill-creator validate` | Create new skills, self-evolving agent |
| `clawhub` | `clawhub search`, `clawhub install`, `clawhub publish` | Skill marketplace, install/publish community skills |
| `model-usage` | `model-usage report` | Track per-model API costs across providers |
| `tmux` | `tmux new -s session`, `tmux send-keys` | Manage background processes on Chromebook |
| `session-logs` | `session-logs search "query"` | Search session JSONL history, audit trail |

### Communication
| Skill | Command | Use Case |
|-------|---------|----------|
| `discord` | `discord send #channel "message"` | Grow alerts, trading signals, community |
| `himalaya` | `himalaya list`, `himalaya read`, `himalaya write` | agent@grokandmon.com email (IMAP/SMTP) |
| `canvas` | `canvas render dashboard.html` | Live grow dashboard on phone/tablet |

### Workflow
| Skill | Command | Use Case |
|-------|---------|----------|
| `lobster` (extension) | Pipeline syntax below | Multi-step approval pipelines for safety |

#### Lobster Pipeline Examples
```
# Watering approval gate
grow-monitor.check-moisture | approve --prompt "Water? Soil at {moisture}%" | grow-monitor.water

# Trade execution pipeline
trading-signals.scan | approve --prompt "Execute trade?" | trading-signals.execute

# Email triage
himalaya.list --folder INBOX | approve --prompt "Reply to these?" | himalaya.reply
```

## Community Skills (14 installed via ClawHub)

### Token & Trading
| Skill | Author | Use Case |
|-------|--------|----------|
| `nadfun-token-creation` | therealharpaljadeja | Launch $GANJA token on nad.fun |
| `x402` | 0xterrybit | x402 micropayment protocol |
| `polymarket-hyperliquid-trading` | zaycv | Polymarket + Hyperliquid integration |
| `unifai-trading-suite` | zbruceli | Unified trading: Polymarket, Kalshi, social signals |
| `alpha-finder` | tzannetosgiannis | Alpha hunting across social + on-chain |
| `crypto-whale-monitor` | waleolapo | Whale wallet tracking |
| `crypto-self-learning` | totaleasy | Autonomous trading self-improvement |

### Social
| Skill | Author | Use Case |
|-------|--------|----------|
| `clawcast` | tezatezaz | Farcaster casting |
| `tweeter` | trymoinai-create | Twitter/X posting |
| `moltbook-2` | zaki9501 | Moltbook posting |
| `moltbook-daily-digest` | wangfugui1799 | Moltbook feed summarization |

### Agent Intelligence
| Skill | Author | Use Case |
|-------|--------|----------|
| `ralph-loop-writer` | walkamolee | Structured self-improvement loops |
| `session-memory` | swaylq | Persistent session memory |
| `crypto-hackathon` | swairshah | Hackathon utilities |

## Custom Skills (7)

| Skill | Directory | Purpose |
|-------|-----------|---------|
| `moltbook-poster` | `skills/moltbook-poster/` | Moltbook posting + verification challenge handling |
| `clawk-poster` | `skills/clawk-poster/` | Clawk posting + 5:1 engagement rule |
| `grow-monitor` | `skills/grow-monitor/` | Sensor reads + actuator control via HAL API |
| `trading-signals` | `skills/trading-signals/` | Portfolio status + market research |
| `a2a-discovery` | `skills/a2a-discovery/` | ERC-8004 agent discovery + A2A JSON-RPC |
| `social-composer` | `skills/social-composer/` | Rasta-voice content gen with gemini + nano-banana-pro |
| `reputation-publisher` | `skills/reputation-publisher/` | On-chain ERC-8004 reputation signals |

## Python HAL API (Hardware Abstraction Layer)

The FastAPI server at `http://localhost:8000` provides all hardware interaction. OpenClaw skills call these endpoints — they never touch hardware directly.

### Exec Host Safety (Critical)
When using OpenClaw `exec` tool calls, do not set `host=node` or `host=gateway` for normal ops.
Use default sandbox execution (omit `host`) or explicitly set `host="sandbox"` to avoid host-routing failures.

### Sensor Endpoints (Read-Only)
```
GET  /api/sensors                    → Current temp, humidity, VPD, soil moisture, CO2
GET  /api/sensors/history?hours=N    → Historical sensor data
GET  /api/grow/stage                 → Current growth stage + targets
GET  /api/grow/history?hours=N       → Grow decision history
GET  /api/health                     → System health check
```

### Actuator Endpoints (Write — SafetyGuardian enforced)
```
POST /api/actuator/control           → {"device": "water_pump|co2_injector", "action": "on|off", "duration": N}
GET  /api/actuator/status            → Current device states
GET  /api/safety/status              → SafetyGuardian state (watering cooldown, dark period)
```

### Trading Endpoints
```
GET  /api/trading/portfolio          → Current positions + P&L
GET  /api/trading/signals            → Latest alpha signals
POST /api/trading/execute            → Execute trade (requires approval gate)
GET  /api/trading/history            → Trade execution history
```

### Social Endpoints
```
POST /api/social/post                → {"text": "...", "include_image": false} (Twitter text post)
POST /api/social/tweet-with-image    → {"text": "..."} (Twitter post + current webcam image)
GET  /api/social/search?q=...        → Find QT targets with engagement + media URLs
POST /api/social/quote               → {"tweet_id": "...", "text": "..."} (text-only QT)
POST /api/social/quote-with-image    → multipart form: tweet_id, text, image file
GET  /api/social/mentions            → Recent mentions for reply cycle
POST /api/social/reply               → {"tweet_id": "...", "text": "..."} (reply to mention)
GET  /api/social/preview             → Dry-run generated social text preview
```

### Blockchain Endpoints
```
POST /api/blockchain/publish-reputation  → {"signals": N} — publish ERC-8004 on-chain signals
GET  /api/blockchain/trust-score         → Current 8004scan trust score
GET  /api/blockchain/agent-info          → Agent #4 on Monad details
```

### Admin Endpoints
```
GET  /api/admin/ping                 → Health check (no auth)
GET  /api/admin/system-info          → CPU, memory, disk, uptime
GET  /api/admin/services             → systemd service statuses
POST /api/admin/restart-service/{name} → Restart a service
POST /api/admin/exec                 → {"command": "..."} — run shell command
GET  /api/admin/logs/{name}?lines=N  → Service logs
```

## Tool Priority

1. **Built-in OpenClaw skills first** — they're tested, maintained, and part of the framework
2. **Community skills second** — installed via ClawHub, vetted by community
3. **Custom skills third** — our domain-specific implementations
4. **HAL API direct calls last** — only when no skill wraps the functionality

## Environment Variables Required

Skills need these in their environment (configured in `openclaw.json`):
```
MOLTBOOK_API_KEY          — Moltbook posting
CLAWK_API_KEY             — Clawk posting
GEMINI_API_KEY            — Gemini CLI + nano-banana-pro
OPENAI_API_KEY            — Oracle (GPT-5.2 Pro)
GITHUB_TOKEN              — GitHub CLI
DISCORD_BOT_TOKEN         — Discord bot
TELEGRAM_BOT_TOKEN        — Telegram posting
FARCASTER_MNEMONIC        — Farcaster signing
RESEND_API_KEY            — Email sending
PRIVATE_KEY               — Blockchain signing (Monad)
NEYNAR_API_KEY            — Farcaster hub API
HAL_BASE_URL              — http://localhost:8000 (Python HAL)
```
