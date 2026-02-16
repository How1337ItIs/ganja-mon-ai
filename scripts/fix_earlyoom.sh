#!/usr/bin/env bash
# Fix earlyoom to NOT preferentially kill openclaw
# OpenClaw is now the primary orchestrator — killing it breaks the agent
#
# BEFORE: --prefer 'python3?|uvicorn|openclaw|node|chromium'
# AFTER:  --prefer 'python3?|uvicorn|node|chromium'
#
# Run on Chromebook: sudo bash fix_earlyoom.sh

set -euo pipefail

EARLYOOM_CONF="/etc/default/earlyoom"

if [ ! -f "$EARLYOOM_CONF" ]; then
    echo "ERROR: $EARLYOOM_CONF not found"
    exit 1
fi

echo "=== Current earlyoom config ==="
cat "$EARLYOOM_CONF"
echo ""

# Remove openclaw from the --prefer pattern
# Before: python3?|uvicorn|openclaw|node|chromium
# After:  python3?|uvicorn|node|chromium
if grep -q 'openclaw' "$EARLYOOM_CONF"; then
    sed -i 's/openclaw|//g' "$EARLYOOM_CONF"
    echo "[OK] Removed 'openclaw' from --prefer list"
else
    echo "[SKIP] 'openclaw' not in config"
fi

echo ""
echo "=== Updated config ==="
cat "$EARLYOOM_CONF"

echo ""
echo "=== Restarting earlyoom ==="
systemctl restart earlyoom
systemctl status earlyoom --no-pager | head -5

echo ""
echo "Done. OpenClaw will no longer be preferentially killed by earlyoom."
echo "If OOM pressure is still an issue, consider:"
echo "  - Disabling snapd: sudo systemctl stop snapd && sudo systemctl disable snapd"
echo "  - Reducing trading agent memory: set AGENT_MAX_RSS_MB in .env"
echo "  - Adding more swap: sudo fallocate -l 4G /swapfile2"
