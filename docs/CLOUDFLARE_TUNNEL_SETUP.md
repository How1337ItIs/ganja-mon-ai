# Cloudflare Tunnel Setup for Chromebook

This guide documents the **persistent, always-on** connection to the Chromebook server via Cloudflare Tunnel.

## Current Status ✅

The tunnel is **already configured and running**:

| Component | Status | Details |
|-----------|--------|---------|
| **Tunnel Name** | `ganjamonai` | Running as systemd service |
| **Public URL** | https://grokandmon.com | Routes to FastAPI :8000 |
| **Uptime** | 5+ hours | Auto-restarts on failure |

## Architecture

```
Windows Laptop                     Cloudflare                    Chromebook
     │                                 │                              │
     ├── Browser/curl ─────────────────┼── https://grokandmon.com ────► FastAPI :8000
     │                                 │                              │
     └── Admin API ────────────────────┼── https://grokandmon.com/api/admin/* ──► System Control
                                       │                              │
                                 (Zero Trust)                    (outbound only)
```

## Admin API Endpoints

When SSH is down, use these authenticated API endpoints for full remote control:

### Authentication

```bash
# Get JWT token
TOKEN=$(curl -s -X POST "https://grokandmon.com/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=YOUR_ADMIN_PASSWORD" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### System Control

```bash
# Ping (no auth required)
curl -s https://grokandmon.com/api/admin/ping

# System info (auth required)
curl -s -H "Authorization: Bearer $TOKEN" https://grokandmon.com/api/admin/system-info

# List service statuses
curl -s -H "Authorization: Bearer $TOKEN" https://grokandmon.com/api/admin/services

# Get logs for a service
curl -s -H "Authorization: Bearer $TOKEN" "https://grokandmon.com/api/admin/logs/grokmon?lines=50"

# Restart a service
curl -s -X POST -H "Authorization: Bearer $TOKEN" https://grokandmon.com/api/admin/restart-service/grokmon

# Execute shell command
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "uptime", "timeout": 30}' \
  https://grokandmon.com/api/admin/exec

# REBOOT (requires confirm=True)
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "https://grokandmon.com/api/admin/reboot?confirm=True&delay_seconds=5"
```

### Available Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/admin/ping` | GET | No | Health check |
| `/api/admin/system-info` | GET | Yes | Uptime, memory, disk, temp |
| `/api/admin/services` | GET | Yes | List all service statuses |
| `/api/admin/service-status/{name}` | GET | Yes | Status of specific service |
| `/api/admin/restart-service/{name}` | POST | Yes | Restart a service |
| `/api/admin/logs/{name}` | GET | Yes | View service logs |
| `/api/admin/exec` | POST | Yes | Execute shell command |
| `/api/admin/reboot` | POST | Yes | Reboot system (needs confirm=True) |

### Allowed Services for Restart

- `grokmon` - Main application
- `cloudflared` - Tunnel connector
- `ssh` - SSH daemon

## Shell Execution Safety

The `/api/admin/exec` endpoint has safety features:

**Blocked Patterns:**
- `rm -rf`, `mkfs`, `dd if=`, `chmod 777 /`
- Pipe to shell (`curl | sh`, `wget | sh`)
- Fork bombs

**Safe Quick Commands:**
```bash
# These run without full shell analysis
uptime, df -h, free -h, ps aux, top -bn1
ip addr, whoami, date, pwd, ls -la
```

## Tunnel Management

```bash
# View tunnel status on Chromebook
ssh natha@chromebook.lan "systemctl status cloudflared"

# Restart tunnel (if SSH works)
ssh natha@chromebook.lan "sudo systemctl restart cloudflared"

# View tunnel in Cloudflare Dashboard
https://one.dash.cloudflare.com/ → Networks → Connectors
```

## When to Use What

| Situation | Solution |
|-----------|----------|
| SSH working, quick command | Use SSH directly |
| SSH flaky, need to restart service | Use `/api/admin/restart-service/grokmon` |
| SSH completely dead, need reboot | Use `/api/admin/reboot?confirm=True` |
| SSH dead, need to run commands | Use `/api/admin/exec` |
| Need to check if server is alive | Use `/api/admin/ping` |

## Troubleshooting

### Tunnel shows 502 Bad Gateway

1. Check if FastAPI is running: `curl https://grokandmon.com/api/health`
2. If not responding, the service might have crashed
3. The tunnel itself can't restart the service - you need SSH or wait for systemd auto-restart

### Can't authenticate

1. Check ADMIN_PASSWORD in `/home/natha/projects/sol-cannabis/.env`
2. Verify token isn't expired (default: 60 minutes)
3. Get a fresh token with the auth endpoint

### Reboot endpoint not working

1. Make sure `confirm=True` is in the query string
2. The sudo command requires passwordless sudo for the `reboot` command
3. Add to sudoers: `natha ALL=(ALL) NOPASSWD: /sbin/reboot`

## Files

| File | Location |
|------|----------|
| Tunnel service | `/etc/systemd/system/cloudflared.service` |
| Admin API | `src/api/admin.py` |
| Credentials | In Cloudflare Zero Trust Dashboard |

