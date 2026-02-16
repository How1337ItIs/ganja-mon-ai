# Ralph Loop Troubleshooting Guide

Common issues and fixes when running Ralph loops.

---

## Issue 1: Fast Loops with No Progress

### Symptoms
- Iterations complete in 10-30s
- No RALPH_STATUS blocks
- Same task count for multiple iterations

### Causes
- Ralph is confused or stuck
- Task is blocked but not marked as such
- Context is corrupted

### Fixes

```bash
# 1. Check what Ralph is actually saying
cat .ralph/logs/loop-001.log | tail -100

# 2. Check for real blockers
cat .ralph/@fix_plan.md | grep "^\*\*Blocked\*\*" -A5

# 3. Kill and restart with fresh context
pkill -f ralph_loop.sh
rm .ralph/state/.session
.ralph/ralph_loop.sh --timeout 60 &
```

---

## Issue 2: Circuit Breaker Opens

### Symptoms
- "Circuit breaker OPEN: No progress for 3 loops"
- Ralph halted

### Causes
- No file changes for 3+ consecutive iterations
- Same error repeated 5+ times
- Task is genuinely impossible

### Fixes

```bash
# 1. Check circuit breaker state
cat .ralph/state/.circuit_breaker

# 2. Review what Ralph was trying
tail -200 .ralph/logs/ralph.log

# 3. If legitimate blocker, mark task as blocked
# Edit .ralph/@fix_plan.md

# 4. If confusion, reset and skip
echo '{"state": "CLOSED", "no_progress_count": 0}' > .ralph/state/.circuit_breaker

# 5. Manually mark stuck task [x] if truly impossible

# 6. Restart
.ralph/ralph_loop.sh --timeout 60 &
```

---

## Issue 3: Premature EXIT_SIGNAL

### Symptoms
- Ralph exits with tasks remaining
- Completion indicators but work incomplete

### Causes
- Ralph confused blocked tasks with completed tasks
- Exit logic too permissive
- Weak completion detection

### Fixes

```bash
# 1. Check exit signals
cat .ralph/state/.exit_signals

# 2. Count remaining tasks
grep -c "^\- \[ \]" .ralph/@fix_plan.md

# 3. Reset and restart if tasks remain
echo '{"done_signals": [], "completion_indicators": []}' > .ralph/state/.exit_signals
.ralph/ralph_loop.sh --timeout 60 &
```

### Prevention

Add mandatory task count check to PROMPT.md:

```markdown
BEFORE setting EXIT_SIGNAL: true, you MUST:
1. Count uncompleted [ ] tasks: grep -c "^\- \[ \]" .ralph/@fix_plan.md
2. If count > 0, EXIT_SIGNAL MUST be false
```

---

## Issue 4: Ralph Dies Silently

### Symptoms
- No ralph processes running
- Last log entry hours old
- No exit message

### Causes
- OOM (Out of Memory)
- Timeout
- API error
- Process crash

### Fixes

```bash
# 1. Check last log entries
tail -100 .ralph/logs/ralph.log

# 2. Check system resources
free -h
df -h

# 3. Check if killed by system
dmesg | grep -i kill | tail -20

# 4. Restart with trap handler
# Add to ralph_loop.sh:
trap 'log "ERROR" "Ralph died: $?"; cleanup' EXIT ERR

# 5. Restart
.ralph/ralph_loop.sh --timeout 60 &
```

---

## Issue 5: Session Continuity Disabled

### Symptoms
- "Session continuity: false" in logs
- Context loss between iterations
- Repetitive work

### Causes
- Old Ralph instance still running
- Script cached
- Conflicting flags

### Fixes

```bash
# 1. Kill ALL Ralph instances
pkill -9 -f ralph_loop.sh
pkill -9 -f "claude.*opus"

# 2. Verify all killed
ps aux | grep ralph

# 3. Clear bash cache
hash -r

# 4. Restart
.ralph/ralph_loop.sh --timeout 60 &
```

---

## Issue 6: No RALPH_STATUS Block

### Symptoms
- "No RALPH_STATUS block found" warnings
- Can't track progress
- Exit detection unreliable

### Causes
- PROMPT.md doesn't require status blocks
- Ralph ignoring instructions
- Fast loops skipping output

### Fixes

Add mandatory requirement to PROMPT.md:

```markdown
## MANDATORY: Status Block

EVERY response MUST end with:

---RALPH_STATUS---
PHASE: [number]
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: [number]
FILES_MODIFIED: [number]
TESTS_STATUS: PASSING | FAILING | NOT_RUN
EXIT_SIGNAL: false
CURRENT_TASK: [description]
RECOMMENDATION: [next action]
---END_RALPH_STATUS---

If 3 consecutive responses lack this block, the loop will skip the current task.
```

---

## Issue 7: Context Window Degradation

### Symptoms
- Model becomes confused
- Instructions missed
- Repetitive suggestions
- Quality declining

### Causes
- Context approaching limit (>80%)
- Too much history in context
- Mixed planning and execution

### Fixes

```bash
# 1. Reset to fresh context
rm .ralph/state/.session

# 2. Use two-phase workflow
# Phase 1: Planning (fresh context)
claude -p < PROMPT_plan.md > .ralph/plan.md

# Phase 2: Execution (fresh context)
claude -p < PROMPT_build.md

# 3. Store state on disk, not in context
# Use @fix_plan.md, learnings files, git commits
```

---

## Issue 8: API Rate Limiting

### Symptoms
- "Rate limit exceeded" errors
- Slow iterations
- API timeouts

### Causes
- Too many parallel requests
- Short iteration times
- Shared API key across projects

### Fixes

```bash
# 1. Add rate limiting to loop
sleep 30  # Between iterations

# 2. Use exponential backoff
retry_count=0
while ! claude -p < PROMPT.md; do
  retry_count=$((retry_count + 1))
  sleep $((2 ** retry_count))
  if [ $retry_count -gt 5 ]; then
    echo "Max retries exceeded"
    exit 1
  fi
done

# 3. Limit parallel loops
MAX_CONCURRENT=3
```

---

## Issue 9: Git Conflicts in Worktrees

### Symptoms
- Merge conflicts when combining work
- Worktree branch diverged
- Conflicting changes

### Causes
- Multiple loops editing same files
- Base branch updated
- Incomplete merges

### Fixes

```bash
# 1. Update base before creating worktrees
git checkout main && git pull

# 2. Create worktrees from clean main
git worktree add -b feature/x /tmp/x main

# 3. Rebase before merge
cd /tmp/x
git fetch origin
git rebase origin/main

# 4. Use merge-ralph for AI conflict resolution
# (if using ralph-orchestrator)
```

---

## Issue 10: Completion Promise Not Detected

### Symptoms
- Ralph outputs completion promise
- Loop doesn't detect it
- Continues beyond completion

### Causes
- Whitespace mismatch
- Promise in wrong format
- Extraction regex failed

### Fixes

```bash
# Check promise format (must be exact)
# Correct:
<promise>COMPLETE</promise>

# Wrong:
<promise> COMPLETE </promise>  # Extra spaces
<promise>complete</promise>    # Wrong case
<Promise>COMPLETE</Promise>    # Wrong tag case

# Verify detection regex in stop-hook
grep -o '<promise>.*</promise>' output.log
```

---

## Diagnostic Commands Quick Reference

```bash
# Check Ralph status
ps aux | grep ralph

# View recent logs
tail -50 .ralph/logs/ralph.log

# Count completed tasks
grep -c "\[x\]" .ralph/@fix_plan.md

# Count remaining tasks
grep -c "^\- \[ \]" .ralph/@fix_plan.md

# Check circuit breaker
cat .ralph/state/.circuit_breaker

# Check exit signals
cat .ralph/state/.exit_signals

# View latest iteration
ls -lt .ralph/logs/loop-*.log | head -1 | awk '{print $NF}' | xargs cat

# Kill all Ralph processes
pkill -9 -f ralph_loop.sh

# Reset all state
rm -rf .ralph/state/*
```

---

## When to Escalate to Human

### Immediate
- Ralph stuck >2 hours
- Circuit breaker won't reset
- Disk full / OOM
- Critical file corruption

### Can Wait
- Legitimate blocked tasks
- Slow but progressing
- Individual task failures (if skipping and continuing)
- Minor log errors

### User Action Required
Tasks that genuinely need human input:
- API key configuration
- External account setup
- Production deployment approval
- Architecture decisions
