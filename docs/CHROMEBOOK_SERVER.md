# Chromebook Server Reference

The production server runs on a Chromebook booted from external drive (Ubuntu 24.04).

## Quick Access

```bash
# SSH (when local network is working)
ssh natha@chromebook.lan

# Public Dashboard (via Cloudflare Tunnel - always works)
https://grokandmon.com

# API Health Check
curl https://grokandmon.com/api/health
```

## 🚨 Persistent Access (When SSH is Down)

The Chromebook has a **Cloudflare Tunnel** running that provides access even when SSH fails.

### Quick Health Check (No Auth)
```bash
curl https://grokandmon.com/api/admin/ping
# Returns: {"status":"pong","timestamp":"...","server":"chromebook"}

curl https://agent.grokandmon.com/admin/ping
# Returns: {"status":"pong","server":"ganjamon-agent-endpoint","port":8080}
```

### Full Admin Access (Auth Required)

```bash
# Main tunnel auth (grokandmon.com) uses ADMIN_JWT_PASSWORD
MAIN_TOKEN=$(curl -s -X POST "https://grokandmon.com/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=$ADMIN_JWT_PASSWORD" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Agent tunnel auth (agent.grokandmon.com) uses ADMIN_PASSWORD
AGENT_TOKEN=$(curl -s -X POST "https://agent.grokandmon.com/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=$ADMIN_PASSWORD" \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# System info (main tunnel)
curl -s -H "Authorization: Bearer $MAIN_TOKEN" https://grokandmon.com/api/admin/system-info

# Service list (agent tunnel)
curl -s -H "Authorization: Bearer $AGENT_TOKEN" https://agent.grokandmon.com/admin/services

# Restart service (agent tunnel)
curl -s -X POST -H "Authorization: Bearer $AGENT_TOKEN" \
  https://agent.grokandmon.com/admin/restart-service/grokmon

# Execute shell command (agent tunnel)
curl -s -X POST -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "uptime", "timeout": 30}' \
  https://agent.grokandmon.com/admin/exec

# REBOOT via main tunnel (last resort - requires confirm=True)
curl -s -X POST -H "Authorization: Bearer $MAIN_TOKEN" \
  "https://grokandmon.com/api/admin/reboot?confirm=True&delay_seconds=10"
```

### Off-LAN Shortcut

Use the wrapper script from repo root:

```bash
scripts/chromebook_remote_admin.sh ping
scripts/chromebook_remote_admin.sh status
scripts/chromebook_remote_admin.sh exec "hostname && date -Is"
scripts/chromebook_remote_admin.sh restart grokmon
```

### Admin API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/admin/ping` | GET | No | Quick health check |
| `/api/admin/system-info` | GET | Yes | Uptime, memory, disk, CPU temp |
| `/api/admin/services` | GET | Yes | Status of all services |
| `/api/admin/logs/{service}` | GET | Yes | View service logs |
| `/api/admin/restart-service/{service}` | POST | Yes | Restart a service |
| `/api/admin/exec` | POST | Yes | Execute shell command |
| `/api/admin/reboot` | POST | Yes | Reboot (needs confirm=True) |

See `docs/CLOUDFLARE_TUNNEL_SETUP.md` for full tunnel documentation.

## Credentials

> **SECURITY NOTE:** Never store credentials in documentation.

| Service | Username | Password Location |
|---------|----------|-------------------|
| SSH/sudo | natha | See `~/.ssh_password` on Windows host |
| Main tunnel admin (`/api/auth/token`) | admin | `ADMIN_JWT_PASSWORD` in `.env` |
| Agent tunnel admin (`/auth/token`) | admin | `ADMIN_PASSWORD` in `.env` |

```bash
# SSH password stored securely at:
# Windows: C:\Users\natha\.ssh_password
# To view: cat /mnt/c/Users/natha/.ssh_password

# Tunnel admin passwords set via environment
export ADMIN_JWT_PASSWORD="main-tunnel-password"
export ADMIN_PASSWORD="agent-tunnel-password"
```

## Webcam Troubleshooting

### Tiny white dot / blank feed (342 bytes or less)

**Cause:** Race condition at startup - both orchestrator and web server try to open camera simultaneously. The server loses and falls back to MockCameraHub (tiny placeholder image).

**Root Cause (Jan 26, 2026):**
- `run.py all` starts orchestrator (main process) AND web server (subprocess)
- Both try to open `/dev/video2` at startup
- Orchestrator grabs camera first for test capture
- Server's ContinuousWebcam fails to open → falls back to mock
- Fix: Added retry logic (5 attempts, 2sec delay) in `app.py` camera init

**Symptoms:**
- Webcam shows tiny white dot instead of plant
- `/api/webcam/latest` returns ~342 bytes (should be 20-200KB)
- Logs show: `[!] ContinuousWebcam failed to start, using mock`

**Fix:**
```bash
# Usually just restart - retry logic should handle it now
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user restart grokmon"

# If still failing, check logs for camera errors:
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "journalctl --user -u grokmon -n 50 | grep -i camera"
```

### Capturing Webcam Images

**Working method:** Use the `/api/webcam/latest` endpoint (instant response from buffer)
```bash
# Capture image
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "curl -s http://localhost:8000/api/webcam/latest -o /tmp/plant.jpg"

# Copy to local
sshpass -p "$SSH_PASSWORD" scp natha@chromebook.lan:/tmp/plant.jpg /tmp/plant.jpg
```

### Camera Brightness Adjustment

When light intensity changes (100% → 50%), camera settings need adjustment:
- Normal mode (lights on): `brightness=60, contrast=55, gain=50, sat=70, exposure=25, WB=4600K` (calibrated Feb 11 2026 for grow light ~4000K spectrum)
- Night vision (lights off): `brightness=255, gain=255, exposure=1000` (max everything)
- Settings configured in `src/hardware/webcam.py:341-350`

**Prevention:** Night vision mode is enabled by default (`night_mode=True` in app.py). This:
- Auto-switches camera to high-gain/long-exposure during dark periods (inverse of light schedule)
- Applies software brightening (gamma correction + green tint)
- Switches back to normal settings when lights turn on
- Provides visible feed 24/7 (though dark period will be grainy/noisy)

**Normal frame size:** 20-50KB (daytime), 100-200KB (night vision with high gain)

## Connected Hardware

**Govee Devices (Cloud API via GOVEE_API_KEY)**
| Device | Model | Function |
|--------|-------|----------|
| WiFi Thermometer | H5179 | Temperature & Humidity |
| Smart CO2 Monitor | H5140 | CO2 PPM readings |
| Smart Humidifier 2 | H7145 | Humidity control (on/off) |

**Kasa Smart Plugs (Local Network)**
| Plug | IP |
|------|-----|
| Plug 1 | 192.168.125.181 |
| Plug 2 | 192.168.125.129 |
| Plug 3 | 192.168.125.203 |
| Plug 4 | 192.168.125.133 |

## Server Auto-Start

Server runs via systemd user service. After reboot:
- SSH available immediately via `chromebook.lan`
- API server (HAL) starts automatically on port 8000
- Trading agent starts automatically on port 8001
- OpenClaw gateway starts after 60s delay on port 18789 (configurable via `OPENCLAW_START_DELAY_SECONDS`)
- All Govee/Kasa devices auto-connect
- `earlyoom` monitors memory and kills runaway processes before OOM freeze

**DISABLED on boot (2026-02-10):**
- `kiosk.service` — Chrome HUD display (1.1 GB + 67% CPU). HUD accessible remotely via browser. Enable manually: `systemctl --user start kiosk.service`
- `retake-stream.service` — ffmpeg RTMP to RetakeTV (104 MB + 31% CPU). Only needed when live streaming. Enable manually: `systemctl --user start retake-stream.service`
- **Rationale:** Chromebook has 3.7 GB RAM. Kiosk + ffmpeg consumed 1.2 GB + 100% CPU, causing SSH resets and OOM reboots.

## Sleep Prevention

Chromebook is configured to NEVER sleep via `/etc/systemd/logind.conf.d/no-sleep.conf`:
```
[Login]
IdleAction=ignore
HandleLidSwitch=ignore
HandleSuspendKey=ignore
```
If camera/connection goes black, check that sleep hasn't been re-enabled. Reconfigure with:
```bash
# You will be prompted for password
ssh -tt chromebook.lan "sudo systemctl restart systemd-logind"
```

## Service Commands

```bash
systemctl --user status grokmon    # Check status
systemctl --user restart grokmon   # Restart
journalctl --user -u grokmon -f    # View logs
```

**Service Mode:** `run.py all` runs 3 subprocesses:
- **FastAPI (HAL):** Port 8000, serves website + API + sensor data
- **OpenClaw Gateway:** Port 18789, primary AI orchestrator (heartbeat-driven, replaces legacy orchestrator). Starts after 60s delay, runs at nice +10.
- **Trading Agent:** Port 8001, GanjaMonAgent isolated subprocess

**Helper Threads (inside run.py):**
- **Memory Mirror:** Writes sensor snapshots to `openclaw-workspace/ganjamon/memory/YYYY-MM-DD.md` every 30min
- **Upgrade Bridge:** Scans OpenClaw memory for `UPGRADE_REQUEST_JSON:` lines → feeds into `upgrade_requests.json`
- **Proc Watchdog:** Respawns OpenClaw/trading if they die

### Relevant Environment Variables

- `OPENCLAW_START_DELAY_SECONDS` — Delay before starting OpenClaw (default: 60)
- `OPENCLAW_NICE` — Nice value for OpenClaw process (default: 10)
- `OPENCLAW_UPGRADE_BRIDGE_POLL_SECONDS` — How often bridge scans memory (default: 60)

## Remote Deployment from Windows

```bash
# CORRECT - specify username natha@chromebook.lan
sshpass -p "$SSH_PASSWORD" scp /c/Users/natha/sol-cannabis/src/path/to/file.py natha@chromebook.lan:/home/natha/projects/sol-cannabis/src/path/to/file.py

# Restart service
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user restart grokmon"

# Check status
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user status grokmon --no-pager"

# Check logs
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "journalctl --user -u grokmon -n 50 --no-pager"

# Test API
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "curl -s http://localhost:8000/api/health"

# Capture webcam image (working method)
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "curl -s http://localhost:8000/api/webcam/latest -o /tmp/plant.jpg"
sshpass -p "$SSH_PASSWORD" scp natha@chromebook.lan:/tmp/plant.jpg /tmp/plant.jpg
```

## File Locations

| Component | Windows | Chromebook |
|-----------|---------|------------|
| **Project root** | `C:\Users\natha\sol-cannabis` | `/home/natha/projects/sol-cannabis` |
| **Grow system** | `src/` | `/home/natha/projects/sol-cannabis/src/` |
| **Trading agent** | `cloned-repos/ganjamon-agent/` | `/home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent/` |
| **Trading agent data** | `cloned-repos/ganjamon-agent/data/` | `.../cloned-repos/ganjamon-agent/data/` |
| **Ralph loop** | `cloned-repos/ganjamon-agent/.ralph/` | `.../cloned-repos/ganjamon-agent/.ralph/` |

> ⚠️ **Path trap:** `/home/natha/projects/ganjamon-agent/` exists but is a LEGACY directory with only personality files (SOUL.md, IDENTITY.md). The real trading agent code lives under `sol-cannabis/cloned-repos/ganjamon-agent/`.

## Trading Agent Deployment

```bash
# From Windows (Git Bash), deploy changed files:
./deploy_agent.sh

# Deploy ALL Python files:
./deploy_agent.sh --all

# Deploy a single file:
./deploy_agent.sh --file src/intelligence/alpha_distiller.py

# Pull Ralph's changes FROM Chromebook:
./sync_agent.sh --pull

# See what changed on Chromebook:
./sync_agent.sh
```

**Manual single-file deploy (when scripts aren't available):**
```bash
# Upload via PowerShell stdin pipe (avoids SCP quoting issues):
powershell.exe -Command "Get-Content 'C:\Users\natha\sol-cannabis\cloned-repos\ganjamon-agent\src\intelligence\alpha_distiller.py' -Raw | ssh natha@chromebook.lan 'cat > /home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent/src/intelligence/alpha_distiller.py'"
```

See `CHROMEBOOK_SETUP.md` for full documentation.
