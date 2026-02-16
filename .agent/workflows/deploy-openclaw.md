---
description: Deploy OpenClaw Gateway to Chromebook and manage the agent
---

# OpenClaw Gateway Deployment

## Prerequisites
- OpenClaw installed on Chromebook (`sudo npm install -g openclaw@latest`)
- Node.js v22+ available
- `~/.openclaw/` directory exists
- Systemd service `openclaw-gateway.service` is **DISABLED** (run.py manages gateway)

## Deploy Config + Restart

// turbo-all

1. Deploy the config from Windows to Chromebook:
```bash
powershell.exe -Command "Get-Content 'c:\Users\natha\sol-cannabis\openclaw-workspace\config\openclaw.json' -Raw | ssh natha@chromebook.lan 'cat > ~/.openclaw/openclaw.json && echo DEPLOYED'"
```

2. Kill any existing OpenClaw processes:
```bash
powershell.exe -Command "ssh natha@chromebook.lan 'pkill -9 -f openclaw 2>/dev/null; sleep 2; fuser -k 18789/tcp 2>/dev/null; echo KILLED'"
```

3. If `grokmon.service` is running, stop it before a manual gateway start (otherwise `run.py all` will also try to manage the gateway):
```bash
powershell.exe -Command "ssh natha@chromebook.lan 'systemctl --user stop grokmon && echo GROKMON_STOPPED'"
```

4. Start the gateway (manual mode):
```bash
powershell.exe -Command "ssh natha@chromebook.lan 'cd /home/natha/projects/sol-cannabis/openclaw-workspace && nohup openclaw gateway run --bind loopback --port 18789 --force > /tmp/openclaw-gateway.log 2>&1 & sleep 1 && echo STARTED'"
```

5. Verify (wait 10s for startup):
```bash
powershell.exe -Command "Start-Sleep -Seconds 10; ssh natha@chromebook.lan 'ss -tlnp | grep 18789 && echo PORT_OK || echo PORT_MISSING'"
```

Expected output should show `LISTEN ... 18789 ... openclaw-gatewa`.

## Full System Restart (via run.py)

To restart the entire stack (HAL + OpenClaw + Trading Agent):

1. Kill everything:
```bash
powershell.exe -Command "ssh natha@chromebook.lan 'pkill -9 -f openclaw 2>/dev/null; pkill -f run.py 2>/dev/null; pkill -f uvicorn 2>/dev/null; sleep 3; fuser -k 8000/tcp 18789/tcp 2>/dev/null; echo KILLED'"
```

2. Deploy updated run.py (if changed locally):
```bash
powershell.exe -Command "Get-Content 'C:\Users\natha\sol-cannabis\run.py' -Raw | ssh natha@chromebook.lan 'cat > /home/natha/projects/sol-cannabis/run.py'"
```

3. Start run.py all:
```bash
powershell.exe -Command "ssh natha@chromebook.lan 'cd /home/natha/projects/sol-cannabis && source venv/bin/activate && nohup python3 run.py all > /tmp/grokmon_startup.log 2>&1 & sleep 1 && echo STARTED'"
```

4. Verify (wait 30s):
```bash
powershell.exe -Command "Start-Sleep -Seconds 30; ssh natha@chromebook.lan 'ss -tlnp | grep -c 18789; ss -tlnp | grep -c 8000'"
```

Both should output `1` or more.

## ⚠️ CRITICAL: CLI Syntax

```bash
# CORRECT — direct gateway start
openclaw gateway run --bind loopback --port 18789 --force

# WRONG — --config flag does NOT exist!
openclaw gateway run --config /path/to/config.json   # ❌ FATAL ERROR

# WRONG — systemd commands (service is disabled)
openclaw gateway start     # ❌ Won't work
openclaw gateway restart   # ❌ Won't work
```

OpenClaw ALWAYS reads config from `~/.openclaw/openclaw.json`. There is no way to specify a different config via CLI.

## ⚠️ Config Rules (v2026.2.9)

Before deploying config, verify:
- **NO** top-level `identity` key (must be inside `agents.list[].identity`)
- **NO** `gateway.auth` section when using `bind: "loopback"` (avoids `MissingEnvVarError`)
- **ALL paths are absolute** (no `../ganjamon`, use `/home/natha/projects/...`)
- **ALL `${VAR}` references** have corresponding env vars set (unresolved = fatal crash)

## Deploy Skills

To deploy updated skills from Windows:
```bash
powershell.exe -Command "Get-Content 'c:\Users\natha\sol-cannabis\openclaw-workspace\ganjamon\skills\<skill>\SKILL.md' -Raw | ssh natha@chromebook.lan 'cat > ~/projects/sol-cannabis/openclaw-workspace/ganjamon/skills/<skill>/SKILL.md'"
```

## Architecture

```
[Telegram] ──→ [OpenClaw Gateway :18789] ──→ [GanjaMon Agent]
                      │                          │
                      ├── Canvas UI (:18792)      ├─→ SOUL.md (identity)
                      ├── Heartbeat (30m)         ├─→ HEARTBEAT.md (cron loop)
                      ├── Cron engine             ├─→ Skills (16 bundled + custom)
                      └── Bonjour/mDNS            └─→ HAL API :8000 (sensors/actuators)
```

## Config Locations

| Location | Path | Purpose |
|----------|------|---------|
| Windows (source) | `openclaw-workspace/config/openclaw.json` | Edit here |
| Chromebook (deployed) | `~/.openclaw/openclaw.json` | OpenClaw reads this |
| Chromebook (workspace) | `~/projects/sol-cannabis/openclaw-workspace/` | Agent workspaces |

## Health Checks

```bash
# Port listening?
ssh natha@chromebook.lan 'ss -tlnp | grep 18789'

# Process running?
ssh natha@chromebook.lan 'ps aux | grep openclaw | grep -v grep'

# Recent log entries
ssh natha@chromebook.lan 'tail -5 /home/natha/projects/sol-cannabis/openclaw-workspace/logs/openclaw.log'

# HAL server healthy?
ssh natha@chromebook.lan 'curl -s http://localhost:8000/api/health'
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `error: unknown option '--config'` | Remove `--config`. Use file copy to `~/.openclaw/openclaw.json` |
| `MissingEnvVarError: OPENCLAW_GATEWAY_TOKEN` | Remove `gateway.auth` section from config |
| `Config invalid - identity was moved` | Move `identity` from top-level into `agents.list[0].identity` |
| Port 18789 not listening | Kill stale processes: `pkill -9 -f openclaw; fuser -k 18789/tcp` |
| `Pairing required` | Use `bind: "loopback"` instead of `bind: "lan"` |
| Telegram conflict | Stop other bot instances polling same token |
| OOM | Gateway uses ~370MB. Chromebook has 4GB. Monitor with `free -h` |
| OpenClaw + systemd conflict | Disable systemd: `systemctl --user disable openclaw-gateway.service` |
