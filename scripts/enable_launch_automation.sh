#!/bin/bash
#
# Enable Post-Launch Automation
# ==============================
# RUN THIS AFTER TOMORROW'S LAUNCH (Jan 22, 2026)
#
# This activates:
# - Daily day counter advancement
# - Daily photo archival
# - Daily sensor data archival
# - Daily AI decision archival
# - (Optional) On-chain preservation
#
# Usage: ssh chromebook.lan "bash /home/natha/projects/sol-cannabis/scripts/enable_launch_automation.sh"

set -e

echo "🚀 Enabling Post-Launch Automation"
echo "===================================="
echo ""

# Create archive directories
mkdir -p ~/projects/sol-cannabis/archive/{photos,logs,data,onchain}
echo "✓ Created archive directories"

# Backup current crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Get existing cron (or start fresh)
crontab -l 2>/dev/null > /tmp/new_crontab.txt || echo "# Grok & Mon Automation" > /tmp/new_crontab.txt

# Add daily advancement if not present
if ! grep -q "daily_advancement.py" /tmp/new_crontab.txt; then
    cat >> /tmp/new_crontab.txt << 'EOF'

# =============================================================================
# POST-LAUNCH AUTOMATION (Activated after Jan 22, 2026 launch)
# =============================================================================

# Daily grow day advancement + archival (midnight PST = 8 AM UTC)
# This runs every day at midnight to:
# - Advance day counter (Day 1 → Day 2 → Day 3...)
# - Archive daily snapshot
# - Archive sensor data
# - Archive AI decisions
# - (Optional) Preserve on Monad blockchain
0 8 * * * cd /home/natha/projects/sol-cannabis && ./venv/bin/python scripts/daily_advancement.py >> /tmp/daily_advancement.log 2>&1

# Generate timelapse (weekly on Sundays at 3 AM)
0 11 * * 0 cd /home/natha/projects/sol-cannabis && ./venv/bin/python -c "from src.media.timelapse import generate_timelapse_gif; import asyncio; asyncio.run(generate_timelapse_gif(days=7))" >> /tmp/timelapse.log 2>&1

EOF
    echo "✓ Added post-launch cron jobs"
else
    echo "⏭ Post-launch crons already exist"
fi

# Install new crontab
crontab /tmp/new_crontab.txt
rm /tmp/new_crontab.txt

echo ""
echo "✅ Post-Launch Automation ENABLED!"
echo ""
echo "Active Automation:"
echo "  ✓ Daily day advancement (midnight PST)"
echo "  ✓ Daily photo archival"
echo "  ✓ Daily sensor archival"
echo "  ✓ Weekly timelapse generation"
echo "  ✓ Database backups (3 AM daily)"
echo "  ✓ Health monitoring (every 5 min)"
echo "  ✓ Cloudflare cache updates (every 1 min)"
echo ""
echo "Archive Location: ~/projects/sol-cannabis/archive/"
echo "  - photos/    Daily snapshots"
echo "  - data/      Sensor + AI data"
echo "  - onchain/   Blockchain records"
echo ""
echo "View current day: curl http://localhost:8000/api/grow/stage"
echo "Manual advance: curl -X POST http://localhost:8000/api/grow/advance-day -H 'Authorization: Bearer TOKEN'"
echo ""
echo "🌱 Grow will now track time automatically!"
