#!/usr/bin/env bash
# ops_log.sh — Append to the operations log
#
# Usage:
#   ./scripts/ops_log.sh <event> <actor> <detail> [category] [files...]
#
# Events: deploy, service_restart, config_change, incident, fix, milestone
# Actors: antigravity, codex, claude, gemini, user, system, openclaw
# Categories: upgrade, maintenance, fix, incident, milestone, meta
#
# Examples:
#   ./scripts/ops_log.sh deploy codex "Deployed new app.py with snapshot scoring" upgrade src/api/app.py
#   ./scripts/ops_log.sh service_restart antigravity "Restart after router registration" maintenance
#   ./scripts/ops_log.sh incident system "OOM kill by earlyoom" incident
#   ./scripts/ops_log.sh milestone user "Hackathon demo ready" milestone

set -euo pipefail

EVENT="${1:?Usage: ops_log.sh <event> <actor> <detail> [category] [files...]}"
ACTOR="${2:?Missing actor (antigravity/codex/claude/gemini/user/system)}"
DETAIL="${3:?Missing detail description}"
CATEGORY="${4:-general}"
shift 4 2>/dev/null || shift 3 2>/dev/null || true

# Build files array
FILES_JSON=""
if [ $# -gt 0 ]; then
    FILES_JSON=",\"files\":["
    FIRST=true
    for f in "$@"; do
        if [ "$FIRST" = true ]; then
            FILES_JSON="${FILES_JSON}\"$f\""
            FIRST=false
        else
            FILES_JSON="${FILES_JSON},\"$f\""
        fi
    done
    FILES_JSON="${FILES_JSON}]"
fi

# Determine log path (works on both Windows and Chromebook)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPS_LOG="$PROJECT_ROOT/data/ops_log.jsonl"

mkdir -p "$(dirname "$OPS_LOG")"

TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "{\"ts\":\"$TS\",\"event\":\"$EVENT\",\"actor\":\"$ACTOR\",\"detail\":\"$DETAIL\",\"category\":\"$CATEGORY\"$FILES_JSON}" >> "$OPS_LOG"

echo "[OPS] $TS $EVENT by $ACTOR: $DETAIL"
