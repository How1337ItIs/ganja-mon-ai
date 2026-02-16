# Autonomy & Automation Policy

**CRITICAL**: Be maximally helpful and autonomous. DO NOT ask the user to do things you can do yourself.

## Core Principles

1. **Do it yourself** - If you can execute a task (SSH, install packages, restart services, deploy code), DO IT
2. **Automate everything** - Always suggest and implement automation opportunities
3. **Proactive problem-solving** - When you identify an issue, fix it immediately
4. **No hand-holding** - Don't provide instructions for the user when you can execute directly
5. **Verify live state after changes** - Never trust script output alone; always read back configs/state from the target system

## Examples

- BAD: "Run this command on the Chromebook: `pip install tweepy`"
- GOOD: "Installing tweepy on Chromebook..." `sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "pip install tweepy"`

- BAD: "You should restart the service with systemctl"
- GOOD: "Restarting service..." `sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user restart grokmon"`

- BAD: "Would you like me to...?"
- GOOD: "Doing X..." [executes immediately]

## When NOT to be autonomous

- User explicitly asks for advice/explanation only
- Destructive operations without clear intent (deleting data, force pushing to main, etc.)
- Ambiguous requirements where user input is genuinely needed

## Chromebook Connection Hierarchy (MANDATORY FALLBACK CHAIN)

**CRITICAL RULE:** When connecting to the Chromebook, you MUST attempt ALL methods in order before giving up. If Method 1 fails, IMMEDIATELY try Method 2. Do NOT stop at the first failure.

**NEVER ask the user how to connect. NEVER search for this. Always have it ready.**

### Method 1: SSH (LAN) - PRIMARY
```bash
source /mnt/c/Users/natha/sol-cannabis/.env
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "command"
# Fallback IP: natha@192.168.125.128
sshpass -p "$SSH_PASSWORD" scp file.py natha@chromebook.lan:/home/natha/projects/sol-cannabis/file.py
```
- **CRITICAL:** Always use `natha@` prefix — WSL defaults to `wombatinux` which fails

### Method 2: Cloudflare Tunnel Admin API - FALLBACK (MUST USE WHEN SSH FAILS)

**MANDATORY:** If SSH fails for ANY reason (timeout, connection refused, permission denied, broken pipe), you MUST immediately attempt this method before reporting failure to the user.
```bash
source /mnt/c/Users/natha/sol-cannabis/.env
# No-auth health check
curl -s https://grokandmon.com/api/admin/ping
# Get JWT
TOKEN=$(curl -s -X POST "https://grokandmon.com/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=$ADMIN_PASSWORD" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
# Authenticated commands
curl -s -H "Authorization: Bearer $TOKEN" https://grokandmon.com/api/admin/system-info
curl -s -X POST -H "Authorization: Bearer $TOKEN" https://grokandmon.com/api/admin/restart-service/grokmon
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"command": "uptime"}' https://grokandmon.com/api/admin/exec
```
Available endpoints: `/ping`, `/system-info`, `/services`, `/logs/{name}?lines=50`, `/restart-service/{name}`, `/exec`, `/reboot?confirm=True`

### Method 3: Both fail = Chromebook genuinely offline
- SSH "No route to host" + Tunnel Error 1033 = powered off or network disconnected
- Inform user, wait for physical intervention

### Error diagnosis & Mandatory Responses
| Error | Meaning | What Claude MUST Do |
|-------|---------|---------------------|
| SSH "No route to host" | Not on LAN | IMMEDIATELY try tunnel API (Method 2) |
| SSH "Permission denied" | Auth issue or rate limit | IMMEDIATELY try tunnel API (Method 2) |
| SSH "Connection refused" | sshd down | IMMEDIATELY try tunnel API → restart ssh service |
| SSH "Broken pipe" | Connection interrupted | IMMEDIATELY try tunnel API (Method 2) |
| SSH exit code 255 | Any SSH failure | IMMEDIATELY try tunnel API (Method 2) |
| Tunnel 502 | FastAPI crashed | Try tunnel → restart grokmon, then report if still failing |
| Tunnel 1033 | cloudflared not running | Chromebook genuinely offline - report to user |
| Both SSH AND Tunnel fail | Chromebook offline | NOW you can inform user |

**ENFORCEMENT:** If you encounter an SSH error and do NOT immediately attempt the tunnel API fallback, you have violated this rule.

## Mandatory Readback Verification

After any remote change (config edits, cron setup, service restarts), you MUST verify with objective readbacks:

- Config changes: re-open the exact file you edited on Chromebook and confirm expected values are present.
- Service restarts: check `systemctl --user status` and a functional health probe (`/api/health` and/or target port).
- OpenClaw cron/model changes: inspect the active store under `openclaw-workspace/cron/cron.json` and watch `jobs[].state.lastRunAtMs` advance over time (legacy `/home/natha/.openclaw/cron/` files may be stale; CLI commands may hang).
- Watering checks: do not assume `action_type='WATER'` means irrigation; verify rows where reason is `Dispensed <n>ml of water`.

Do not report success until these readbacks pass.

## Remote Agent Execution

- If SSH proves difficult or limited, you can run a Claude Code agent directly on the Chromebook
- The Chromebook has full Ubuntu 24.04 environment with Python, Node.js, etc.
- Remote agents can handle tasks requiring local system access, complex multi-step operations, or when SSH authentication is problematic
