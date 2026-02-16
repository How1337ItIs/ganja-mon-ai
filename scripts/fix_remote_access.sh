#!/bin/bash
# fix_remote_access.sh — Run on Chromebook to fix all remote access issues
# Usage: sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan 'bash -s' < scripts/fix_remote_access.sh
#
# Or copy and run:
#   scp scripts/fix_remote_access.sh natha@chromebook.lan:/tmp/
#   ssh natha@chromebook.lan 'bash /tmp/fix_remote_access.sh'

set -e

PROJECT="/home/natha/projects/sol-cannabis"
VENV="$PROJECT/venv"
ENDPOINT="$PROJECT/cloned-repos/ganjamon-agent/endpoint"

echo "========================================="
echo "  GanjaMon Remote Access Recovery Script"
echo "  $(date)"
echo "========================================="

# Step 1: Install admin dependencies
echo ""
echo "[1/6] Installing admin dependencies..."
source "$VENV/bin/activate"
pip install --quiet python-jose[cryptography] passlib[bcrypt] python-multipart 2>&1 | tail -3
echo "  Done."

# Step 2: Deploy updated admin.py and server.py
echo ""
echo "[2/6] Checking admin module..."
if python -c "from admin import auth_router, admin_router; print('Admin module OK')" 2>/dev/null; then
    echo "  Admin module loads successfully."
else
    echo "  WARNING: Admin module failed to load. Check logs."
fi

# Step 3: Restart endpoint service
echo ""
echo "[3/6] Restarting ganjamon-endpoint service..."
systemctl --user restart ganjamon-endpoint
sleep 3
if systemctl --user is-active ganjamon-endpoint >/dev/null 2>&1; then
    echo "  ganjamon-endpoint: RUNNING"
else
    echo "  WARNING: ganjamon-endpoint failed to start"
    journalctl --user -u ganjamon-endpoint -n 10 --no-pager
fi

# Step 4: Verify admin endpoints
echo ""
echo "[4/6] Verifying admin endpoints..."
PING=$(curl -s --connect-timeout 5 http://localhost:8080/admin/ping 2>&1)
if echo "$PING" | grep -q "pong"; then
    echo "  Admin ping: OK"
else
    echo "  Admin ping: FAILED"
    echo "  Response: $PING"
    # Check diagnostics
    DIAG=$(curl -s --connect-timeout 5 http://localhost:8080/diag 2>&1)
    echo "  Diagnostics: $DIAG"
fi

# Step 5: Check/restart grokmon
echo ""
echo "[5/6] Checking grokmon service..."
if systemctl --user is-active grokmon >/dev/null 2>&1; then
    echo "  grokmon: RUNNING"
else
    echo "  grokmon: NOT RUNNING — attempting restart..."
    systemctl --user restart grokmon
    sleep 5
    if systemctl --user is-active grokmon >/dev/null 2>&1; then
        echo "  grokmon: RESTARTED OK"
    else
        echo "  grokmon: STILL FAILING"
        journalctl --user -u grokmon -n 15 --no-pager
    fi
fi

# Step 6: Check cloudflared tunnels
echo ""
echo "[6/6] Checking cloudflared tunnels..."
if pgrep -af cloudflared >/dev/null 2>&1; then
    echo "  cloudflared processes:"
    pgrep -af cloudflared | head -5
else
    echo "  WARNING: No cloudflared processes running"
fi

# Verify remote access
echo ""
echo "========================================="
echo "  Verification Summary"
echo "========================================="
echo ""

# Port 8080 (agent endpoint + admin)
if curl -s --connect-timeout 3 http://localhost:8080/health >/dev/null 2>&1; then
    echo "  Port 8080 (agent+admin): UP"
else
    echo "  Port 8080 (agent+admin): DOWN"
fi

# Port 8000 (main API)
if curl -s --connect-timeout 3 http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "  Port 8000 (main API):    UP"
else
    echo "  Port 8000 (main API):    DOWN"
fi

# SSH
if systemctl is-active ssh >/dev/null 2>&1 || systemctl is-active sshd >/dev/null 2>&1; then
    echo "  SSH:                     UP"
else
    echo "  SSH:                     DOWN"
fi

# OpenClaw version
if command -v openclaw >/dev/null 2>&1; then
    OC_VER=$(openclaw --version 2>/dev/null | head -1)
    echo "  OpenClaw:                $OC_VER"
else
    echo "  OpenClaw:                NOT FOUND"
fi

echo ""
echo "Recovery complete. Test remotely:"
echo "  curl https://agent.grokandmon.com/admin/ping"
echo "  curl https://grokandmon.com/api/admin/ping"
echo ""
