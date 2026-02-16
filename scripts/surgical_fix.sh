#!/bin/bash
# Surgical Fix Loop — Invokes Claude Code ONLY when real bugs are detected.
#
# Reads data/health_report.json (written by agent_doctor.py).
# If no CRITICAL/HIGH bugs → exits immediately (zero Claude Code cost).
# If bugs found → invokes Claude Code with a focused surgical prompt.
#
# Cron: 0 */12 * * * cd /home/natha/projects/sol-cannabis && scripts/surgical_fix.sh
#
set -euo pipefail

PROJECT_DIR="/home/natha/projects/sol-cannabis"
REPORT="$PROJECT_DIR/data/health_report.json"
LOG_DIR="$PROJECT_DIR/data/logs"
FIX_LOG="$LOG_DIR/surgical_fix.log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$FIX_LOG"
}

# --- Step 1: Run health check first ---
log "Running agent_doctor.py..."
cd "$PROJECT_DIR"
venv/bin/python scripts/agent_doctor.py >> "$FIX_LOG" 2>&1 || true

# --- Step 2: Check if report exists ---
if [ ! -f "$REPORT" ]; then
    log "No health report found. Exiting."
    exit 0
fi

# --- Step 3: Check severity ---
CRITICAL=$(python3 -c "import json; d=json.load(open('$REPORT')); print(d.get('critical', 0))")
HIGH=$(python3 -c "import json; d=json.load(open('$REPORT')); print(d.get('high', 0))")
OVERALL=$(python3 -c "import json; d=json.load(open('$REPORT')); print(d.get('overall', 'UNKNOWN'))")

log "Health: $OVERALL (${CRITICAL}C, ${HIGH}H)"

if [ "$CRITICAL" -eq 0 ] && [ "$HIGH" -eq 0 ]; then
    log "No critical/high bugs. Skipping Claude Code invocation. Credits saved."
    exit 0
fi

# --- Step 4: Build surgical prompt ---
BUGS=$(python3 -c "
import json
d = json.load(open('$REPORT'))
lines = []
for b in d.get('bugs', []):
    if b['severity'] in ('CRITICAL', 'HIGH'):
        loc = ''
        if b.get('file'):
            loc = f\" in {b['file']}\"+( f\":{b['line']}\" if b.get('line') else '')
        lines.append(f\"- [{b['severity']}] {b['name']}{loc}: {b['detail'][:150]}\")
print(chr(10).join(lines))
")

PROMPT="You are a surgical bug fixer for the GanjaMon unified agent system.
The health monitor detected these bugs:

$BUGS

INSTRUCTIONS:
1. Fix ONLY the bugs listed above. Do NOT explore, research, or add features.
2. For each bug: read the file, make the minimal fix, verify it compiles/imports.
3. After fixing, deploy changed files to the Chromebook:
   sshpass -p \"\$SSH_PASSWORD\" scp <file> natha@chromebook.lan:/home/natha/projects/sol-cannabis/<file>
4. Restart the service: sshpass -p \"\$SSH_PASSWORD\" ssh natha@chromebook.lan \"systemctl --user restart grokmon\"
5. Wait 10 seconds, then run: python scripts/agent_doctor.py --json
6. Verify the bugs are resolved.

Working directory: $PROJECT_DIR
SSH password is in .env as SSH_PASSWORD.
Do NOT make any changes beyond fixing these specific bugs."

# --- Step 5: Check if Claude Code is available ---
if ! command -v claude &> /dev/null; then
    log "ERROR: claude command not found. Cannot invoke surgical fix."
    log "Bugs requiring attention:"
    echo "$BUGS" >> "$FIX_LOG"
    exit 1
fi

# --- Step 6: Invoke Claude Code ---
log "Invoking Claude Code for ${CRITICAL}C + ${HIGH}H bugs..."

# Use --dangerously-skip-permissions for autonomous operation
# Limit to 30 minutes max
timeout 1800 claude --dangerously-skip-permissions --print "$PROMPT" >> "$FIX_LOG" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "Surgical fix completed successfully."
elif [ $EXIT_CODE -eq 124 ]; then
    log "Surgical fix timed out after 30 minutes."
else
    log "Surgical fix exited with code $EXIT_CODE."
fi

# --- Step 7: Re-run health check to verify ---
log "Re-running health check to verify fixes..."
venv/bin/python scripts/agent_doctor.py >> "$FIX_LOG" 2>&1 || true

NEW_OVERALL=$(python3 -c "import json; d=json.load(open('$REPORT')); print(d.get('overall', 'UNKNOWN'))")
log "Post-fix health: $NEW_OVERALL"

exit 0
