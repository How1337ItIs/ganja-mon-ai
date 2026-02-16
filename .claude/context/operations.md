# Operations & Deployment

## SSH Access

Password in `.env` as `$SSH_PASSWORD` (also stored at `/mnt/c/Users/natha/.ssh_password` on WSL; Windows: `C:\Users\natha\.ssh_password`). **The same password is used for `sudo` on the Chromebook** when running privileged commands over SSH.

**CRITICAL:** Always use `natha@chromebook.lan` (not just `chromebook.lan`)

### Quoting Reality (Don’t Fight It)
- WSL `sshpass ... "..."` can safely use heredocs and multi-line commands.
- PowerShell `powershell.exe -Command "ssh ... '...'"` is a 3-shell quoting trap; avoid inlining anything complex.
- For PowerShell SSH, default to the script-pipe pattern in `docs/SSH_QUOTING_PLAYBOOK.md` (and `memory/chromebook_access.md`).

### Common Commands

```bash
# Deploy file to Chromebook
sshpass -p "$SSH_PASSWORD" scp file.py natha@chromebook.lan:/home/natha/projects/sol-cannabis/file.py

# Restart grokmon service
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user restart grokmon"

# Check logs
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "journalctl --user -u grokmon -n 50 --no-pager"

# Capture plant image
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "curl -s http://localhost:8000/api/webcam/latest -o /tmp/plant.jpg"
sshpass -p "$SSH_PASSWORD" scp natha@chromebook.lan:/tmp/plant.jpg /tmp/plant.jpg
```

## Cloudflare Pages Deployment

**IMPORTANT:** Use Cloudflare Pages for all web hosting, NOT GitHub Pages.

### Credentials

Located in `.env.wrangler`:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

```bash
source .env.wrangler && export CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
```

### Deploy Commands

```bash
# Deploy mon-bridge
cd mon-bridge
source ../.env.wrangler && export CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
npx wrangler pages deploy . --project-name=mon-bridge

# Deploy main site
cd pages-deploy
npx wrangler pages deploy . --project-name=grokandmon
```

### Current Deployments

| Project | URL | Source |
|---------|-----|--------|
| grokandmon | https://grokandmon.com | `pages-deploy/` |
| mon-bridge | https://mon-bridge.pages.dev | `mon-bridge/` |

## Retake.tv Streaming

**Agent:** ganjamonai
**Stream URL:** https://retake.tv/ganjamonai

### Credentials Location

| Location | Path |
|----------|------|
| **Windows** | `C:\Users\natha\.config\retake\credentials.json` |
| **Chromebook** | `~/.config/retake/credentials.json` |
| **.env vars** | `RETAKE_ACCESS_TOKEN`, `RETAKE_USER_DB_ID`, `RETAKE_AGENT_ID` |

### Stream Commands

```bash
# Start stream on Chromebook
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "cd ~/projects/sol-cannabis && source venv/bin/activate && python src/streaming/retake_lite.py start"

# Stop stream
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "cd ~/projects/sol-cannabis && source venv/bin/activate && python src/streaming/retake_lite.py stop"

# Check status
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "cd ~/projects/sol-cannabis && source venv/bin/activate && python src/streaming/retake_lite.py status"

# Enable 24/7 service
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user enable --now retake-stream"
```

## OpenClaw Reliability Checks (Chromebook)

Use this sequence after any OpenClaw model/cron change:

```bash
# 1) Read live config (do NOT assume handoff edits are already applied)
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "sed -n '1,220p' /home/natha/.openclaw/openclaw.json"

# 2) Confirm gateway reachability
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "curl -fsS --max-time 3 http://127.0.0.1:18789/__openclaw__/canvas/ >/dev/null && echo ok || echo fail"

# 3) Inspect cron stores (active + legacy)
# Active store is driven by `openclaw-workspace/config/openclaw.json` ("cron.store").
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "ls -la /home/natha/projects/sol-cannabis/openclaw-workspace/cron && sed -n '1,260p' /home/natha/projects/sol-cannabis/openclaw-workspace/cron/cron.json 2>/dev/null"
# Legacy (may exist but be stale)
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "ls -la /home/natha/.openclaw/cron && sed -n '1,200p' /home/natha/.openclaw/cron/cron.json 2>/dev/null && sed -n '1,200p' /home/natha/.openclaw/cron/jobs.json 2>/dev/null"

# 4) If jobs aren't running, inspect gateway errors
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "tail -n 120 /home/natha/projects/sol-cannabis/logs/openclaw.log | rg -i 'gateway timeout|gateway closed|cron'"
```

Notes:
- `scripts/setup_openclaw_crons.sh` output alone is insufficient; verify jobs exist in the active cron store file and watch `jobs[].state.lastRunAtMs` advance over time.
- `/api/health` may be healthy even while OpenClaw CLI commands time out on the websocket gateway.

## Watering Audit Query

`action_logs.action_type='WATER'` includes observation rows. Use this query for real pump events:

```bash
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "python3 - <<'PY'
import sqlite3
con=sqlite3.connect('/home/natha/projects/sol-cannabis/data/grokmon.db')
rows=con.execute(\"\"\"
SELECT timestamp, reason
FROM action_logs
WHERE lower(reason) LIKE 'dispensed %ml of water%'
ORDER BY timestamp DESC
LIMIT 20
\"\"\").fetchall()
print(*rows, sep='\\n')
PY"
```
