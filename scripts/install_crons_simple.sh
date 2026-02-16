#!/usr/bin/env bash
# Simplified cron installer - runs LOCALLY on Chromebook
# Avoids quoting issues when called via SSH

set -euo pipefail

AGENT="ganjamon"
TZ="America/Los_Angeles"

echo "=== Installing OpenClaw Cron Jobs ==="

# Check gateway
if ! ss -tlnp 2>/dev/null | grep -q 18789; then
  echo "[ERROR] Gateway not running on :18789"
  exit 1
fi
echo "[OK] Gateway up"

# Job 1: Grow Decision Cycle
echo "[+] Grow Decision Cycle (every 2h)"
openclaw cron add \
  --name "Grow Decision Cycle" \
  --cron "0 */2 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md section Every 2 Hours Grow Decision Cycle. curl localhost:8000/api/sensors and localhost:8000/api/grow/stage. Compare readings against VPD targets. If action needed use grow-monitor skill. Log to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 2: Moltbook Post
echo "[+] Moltbook Post (every 3h)"
openclaw cron add \
  --name "Moltbook Post" \
  --cron "0 */3 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Moltbook Post section. Check suspension status first. Use social-composer for Rasta voice content. Post to moltiversehackathon submolt. Log to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 3: Cross-Platform Social
echo "[+] Cross-Platform Social (every 4h)"
openclaw cron add \
  --name "Cross-Platform Social" \
  --cron "0 */4 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Cross-Platform Social section. Post to Twitter via tweeter, Farcaster via clawcast, Clawk via clawk-poster, Telegram via HAL API. NO hashtags NO leaf emoji. Use social-composer for Rasta voice. Log all post URLs to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 4: Reputation Publishing
echo "[+] Reputation Publishing (every 4h offset)"
openclaw cron add \
  --name "Reputation Publishing" \
  --cron "30 1,5,9,13,17,21 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Reputation Publishing section. Only publish HIGH quality signals. Check sensors and trust score first. Run python3 -m src.blockchain.reputation_publisher. Target trust score above 80 on 8004scan. Log results to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 5: Auto-Review
echo "[+] Auto-Review (every 6h)"
openclaw cron add \
  --name "Auto-Review" \
  --cron "0 0,6,12,18 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Auto-Review section. Review last 6h decisions. Check sensor trends. Analyze social engagement. Check trading P and L. Run compliance check. Detect patterns. Emit UPGRADE_REQUEST_JSON if improvements found. Log review to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 6: Research & Intelligence
echo "[+] Research and Intelligence (every 12h)"
openclaw cron add \
  --name "Research and Intelligence" \
  --cron "0 8,20 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Research section. Use blogwatcher for news scan. Use alpha-finder and crypto-whale-monitor for market intel. Use a2a-discovery for agent discovery. Check GitHub activity of target agents. Log findings to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 7: Daily Comprehensive Update
echo "[+] Daily Comprehensive Update (9 AM)"
openclaw cron add \
  --name "Daily Comprehensive Update" \
  --cron "0 9 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Daily 9 AM section. Generate comprehensive morning report covering sensors, grow decisions, trading P and L, social metrics, A2A results. Use nano-banana-pro for plant photo. Post to ALL platforms. Log to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 8: Weekly Deep Analysis
echo "[+] Weekly Deep Analysis (Mon 6 AM)"
openclaw cron add \
  --name "Weekly Deep Analysis" \
  --cron "0 6 * * 1" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "Read HEARTBEAT.md Weekly section. Run Ralph self-improvement loop. Review all memory logs from the week. Use coding-agent and ralph-loop-writer. Check clawhub for new skills. Generate weekly metrics summary. Log to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

# Job 9: Skill Library Check  
echo "[+] Skill Library Check (daily 10 AM)"
openclaw cron add \
  --name "Skill Library Check" \
  --cron "0 10 * * *" \
  --tz "$TZ" \
  --agent "$AGENT" \
  --message "List currently loaded skills. Use clawhub search for new skills matching grow trading social agents domains. Propose installation of useful skills. Log findings to memory." \
  2>&1 && echo "  OK" || echo "  SKIP"

echo ""
echo "=== Done! Verifying... ==="
openclaw cron list 2>&1 | head -50
