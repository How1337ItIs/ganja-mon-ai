#!/bin/bash

# Simple Ralph Loop
# Usage: ./simple-loop.sh [max_iterations] [completion_promise]
#
# Example:
#   ./simple-loop.sh 20 "COMPLETE"

set -euo pipefail

# Configuration
MAX_ITERATIONS=${1:-20}
COMPLETION_PROMISE=${2:-"COMPLETE"}
PROMPT_FILE="${PROMPT_FILE:-PROMPT.md}"
LOG_DIR="${LOG_DIR:-.ralph/logs}"

# Create log directory
mkdir -p "$LOG_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
  local level=$1
  local msg=$2
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo -e "[$timestamp] [$level] $msg"
  echo "[$timestamp] [$level] $msg" >> "$LOG_DIR/ralph.log"
}

# Check prompt file exists
if [[ ! -f "$PROMPT_FILE" ]]; then
  log "ERROR" "Prompt file not found: $PROMPT_FILE"
  exit 1
fi

log "INFO" "Starting Ralph loop"
log "INFO" "Max iterations: $MAX_ITERATIONS"
log "INFO" "Completion promise: $COMPLETION_PROMISE"
log "INFO" "Prompt file: $PROMPT_FILE"

for i in $(seq 1 $MAX_ITERATIONS); do
  log "INFO" "=== Iteration $i of $MAX_ITERATIONS ==="

  START_TIME=$(date +%s)

  # Run Claude with prompt
  OUTPUT=$(claude --dangerously-skip-permissions --print < "$PROMPT_FILE" 2>&1) || true

  END_TIME=$(date +%s)
  DURATION=$((END_TIME - START_TIME))

  # Save iteration output
  echo "$OUTPUT" > "$LOG_DIR/loop-$(printf '%03d' $i).log"

  log "INFO" "Iteration completed in ${DURATION}s"

  # Check for completion promise
  if echo "$OUTPUT" | grep -q "<promise>$COMPLETION_PROMISE</promise>"; then
    log "INFO" "${GREEN}Detected <promise>$COMPLETION_PROMISE</promise>${NC}"
    log "INFO" "Ralph loop completed successfully at iteration $i"
    exit 0
  fi

  # Check for errors
  if echo "$OUTPUT" | grep -qE "(Error:|ERROR:|Fatal|FATAL)"; then
    ERROR_COUNT=$((ERROR_COUNT + 1))
    log "WARN" "${YELLOW}Errors detected in output${NC}"
  else
    ERROR_COUNT=0
  fi

  # Circuit breaker: 5 consecutive errors
  if [[ ${ERROR_COUNT:-0} -ge 5 ]]; then
    log "ERROR" "${RED}Circuit breaker: 5 consecutive errors${NC}"
    exit 1
  fi

  # Brief pause between iterations
  sleep 2
done

log "WARN" "${YELLOW}Max iterations ($MAX_ITERATIONS) reached without completion${NC}"
exit 1
