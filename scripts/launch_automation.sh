#!/bin/bash
#
# Launch Day Automation Setup
# ============================
# Run this AFTER launch tomorrow to activate:
# - Daily day counter advancement
# - Photo archival
# - Log preservation
# - On-chain data (optional)
#
# Usage: bash scripts/launch_automation.sh

echo "🚀 Setting up post-launch automation..."
echo ""

# Create archive directories
mkdir -p ~/projects/sol-cannabis/archive/{photos,logs,data,onchain}
echo "✓ Created archive directories"

# Get current crontab
crontab -l 2>/dev/null > /tmp/crontab.tmp || echo "# Grok & Mon Cron Jobs" > /tmp/crontab.tmp

# Add daily advancement (midnight PST = 8 AM UTC)
if ! grep -q "daily_advancement.py" /tmp/crontab.tmp; then
    echo "" >> /tmp/crontab.tmp
    echo "# Daily grow day advancement + archival (midnight PST)" >> /tmp/crontab.tmp
    echo "0 8 * * * cd /home/natha/projects/sol-cannabis && ./venv/bin/python scripts/daily_advancement.py >> /tmp/daily_advancement.log 2>&1" >> /tmp/crontab.tmp
    echo "✓ Added daily advancement cron"
else
    echo "⏭ Daily advancement cron already exists"
fi

# Install crontab
crontab /tmp/crontab.tmp
rm /tmp/crontab.tmp

echo ""
echo "✅ Automation activated!"
echo ""
echo "What will happen daily at midnight PST:"
echo "  1. Grow day advances (Day 1 → Day 2 → Day 3...)"
echo "  2. Daily snapshot archived to archive/photos/"
echo "  3. Sensor data archived to archive/data/"
echo "  4. AI decisions archived to archive/data/"
echo "  5. (Optional) IPFS hash stored on Monad"
echo ""
echo "Manual commands:"
echo "  - View archives: ls -lh archive/photos/"
echo "  - Test advancement: python scripts/daily_advancement.py"
echo "  - Check logs: tail /tmp/daily_advancement.log"
echo ""
echo "🌱 Ready for autonomous time tracking!"
