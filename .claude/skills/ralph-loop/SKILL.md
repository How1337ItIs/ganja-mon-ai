---
name: ralph-loop
description: This skill should be used when the user asks to "start a ralph loop", "run autonomous development", "set up iterative AI loop", "create a self-correcting agent", or mentions "ralph wiggum technique", "long-running agent", or "autonomous coding loop".
---

# Ralph Loop Skill

Start and manage Ralph loops - autonomous AI development loops that iterate until task completion.

## What is Ralph?

Ralph is a bash loop that repeatedly feeds an AI agent a prompt until completion:

```bash
while :; do cat PROMPT.md | claude-code ; done
```

Named after Ralph Wiggum from The Simpsons - embodying "naive persistence" where the model confronts failures without sanitization until it produces correct solutions.

## Requirements Gathering

Before starting a Ralph loop, gather these requirements:

### 1. Task Definition
- What is the specific task to accomplish?
- What are the acceptance criteria?
- Can the task be verified automatically (tests, typecheck, build)?

### 2. Exit Conditions
- How will completion be detected?
- What completion promise should the agent output?
- What is the maximum iteration limit?

### 3. Verification Method
- Are there automated tests?
- Can success be verified with commands (`npm test`, `pnpm typecheck`)?
- Is manual verification required at the end?

### 4. Safety Limits
- Maximum iterations (recommended: 10-50)
- Timeout per iteration (recommended: 30-60 minutes)
- Circuit breaker (halt after 3 loops with no progress)

---

## Quick Start Patterns

### Pattern 1: Claude Code Plugin (Recommended)

Use the built-in ralph-loop plugin:

```bash
/ralph-loop "Your task description" --max-iterations 20 --completion-promise "COMPLETE"
```

The plugin's stop-hook intercepts exit attempts and feeds the same prompt back until:
- Completion promise is detected: `<promise>COMPLETE</promise>`
- Max iterations reached
- User cancels with `/cancel-ralph`

### Pattern 2: Simple Bash Loop

For external loop control:

```bash
MAX_ITERATIONS=20
for i in $(seq 1 $MAX_ITERATIONS); do
  echo "Iteration $i of $MAX_ITERATIONS"
  OUTPUT=$(claude --dangerously-skip-permissions < PROMPT.md 2>&1)

  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo "Completed at iteration $i"
    exit 0
  fi
done
```

### Pattern 3: Stop-Hook Pattern

For verification gates, configure `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "if ! npm test; then echo 'Tests failed'; exit 2; fi"
      }]
    }]
  }
}
```

Exit code 2 blocks Claude from stopping - forces continuation until tests pass.

---

## Prompt File Structure

Create a `PROMPT.md` (or `.ralph/PROMPT.md`) with:

```markdown
# Task: [Clear one-line description]

## Objective
[Detailed description of what to accomplish]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] All tests pass

## Verification Commands
Run these after each change:
- `pnpm typecheck`
- `pnpm test`
- `pnpm build`

## Completion Protocol
When ALL criteria are met:
1. Run all verification commands
2. If all pass, output: <promise>COMPLETE</promise>

## Anti-Patterns (Do NOT)
- Do not output completion promise if ANY criterion is unmet
- Do not skip verification commands
- Do not add features beyond the acceptance criteria
```

---

## Best Practices

### Context Management

- **One task per loop**: Prevents context drift
- **Fresh context per iteration**: Each loop gets clean context
- **Disk is memory**: Store state in git, files, task lists
- **Stay in smart zone**: 40-60% context utilization optimal

### Verification

- **Tests-first**: Write failing tests, implement, verify
- **Stop-hooks**: Block exit until verification passes
- **Judge pattern**: Separate agent reviews work before completion

### Safety

- **Always set max-iterations**: Prevents runaway loops
- **Circuit breaker**: Halt after no progress (3 loops with no file changes)
- **Dual-condition exit**: Require BOTH completion indicators AND explicit exit signal

### Completion Promise

The agent must output exactly:
```html
<promise>YOUR_PHRASE</promise>
```

Rules:
- ONLY output when statement is **actually true**
- Never lie to escape the loop
- Include whitespace-normalized exact match

---

## Monitoring & Debugging

### Check Progress

```bash
# Task count (if using @fix_plan.md)
grep -c "\[x\]" .ralph/@fix_plan.md   # Completed
grep -c "^\- \[ \]" .ralph/@fix_plan.md  # Remaining

# Recent logs
tail -f .ralph/logs/ralph.log

# Status JSON
cat .ralph/state/status.json
```

### Signs of Health
- Iteration times: 5-20 minutes (actual work)
- Files modified: > 0 per iteration
- Task count increasing

### Signs of Trouble
- Fast loops (<30s): Spinning/stuck
- No file changes: 3+ iterations
- Same errors repeating

### Recovery

```bash
# Reset circuit breaker
echo '{"state": "CLOSED", "no_progress_count": 0}' > .ralph/state/.circuit_breaker

# Cancel loop
/cancel-ralph  # or rm .claude/ralph-loop.local.md

# Restart with fresh context
rm .ralph/state/.session
```

---

## Multi-Ralph / Parallel Loops

For parallel development, use git worktrees:

```bash
# Create isolated worktrees
git worktree add -b feature/auth /tmp/auth-work main
git worktree add -b feature/api /tmp/api-work main

# Launch Ralph in each (separate terminals)
cd /tmp/auth-work && /ralph-loop "Implement auth" --max-iterations 20
cd /tmp/api-work && /ralph-loop "Build API" --max-iterations 20

# Merge when complete
git checkout main
git merge feature/auth
git merge feature/api

# Cleanup
git worktree remove /tmp/auth-work
git worktree remove /tmp/api-work
```

---

## Decision Framework

| Scenario | Recommended Pattern |
|----------|---------------------|
| Single well-defined task | Claude Code plugin `/ralph-loop` |
| Tasks with test suites | Stop-hook verification |
| Multiple parallel features | Git worktrees + separate loops |
| Complex multi-phase project | PRD → task queue loop |
| 24/7 autonomous operation | tmux orchestration |

---

## References

For detailed patterns, consult:
- **`references/patterns.md`** - Advanced loop patterns
- **`references/verification.md`** - Verification strategies
- **`references/troubleshooting.md`** - Common issues and fixes

For working examples, see:
- **`examples/simple-loop.sh`** - Basic bash loop
- **`examples/stop-hook-config.json`** - Stop-hook verification

---

## Checklist Before Starting

- [ ] Task is well-defined with clear acceptance criteria
- [ ] Verification commands identified (tests, typecheck, build)
- [ ] Completion promise phrase chosen
- [ ] Max iterations set (safety limit)
- [ ] Prompt file created with all sections
- [ ] Git repo initialized (Ralph needs version control)
