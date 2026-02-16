# Ralph Loop Patterns Reference

Detailed patterns for different Ralph loop scenarios.

---

## Pattern 1: PRD → Task Queue Loop

Convert product requirements into atomic tasks, iterate until all complete.

### Structure

```
.ralph/
├── PROMPT.md           # Main instructions
├── @fix_plan.md        # Task list with checkboxes
├── prd.json            # Structured user stories
└── learnings/          # Accumulated knowledge
```

### Task Queue Format (`prd.json`)

```json
{
  "userStories": [
    {
      "id": "US-001",
      "title": "Add priority field to database",
      "acceptanceCriteria": [
        "Add priority column to tasks table",
        "Generate and run migration",
        "Typecheck passes"
      ],
      "passes": false
    }
  ]
}
```

### Loop Logic

```bash
#!/bin/bash
PRD_FILE="prd.json"

while true; do
  NEXT_STORY=$(jq -r '.userStories[] | select(.passes == false) | .id' "$PRD_FILE" | head -1)

  if [ -z "$NEXT_STORY" ]; then
    echo "All stories complete!"
    break
  fi

  STORY=$(jq -r ".userStories[] | select(.id == \"$NEXT_STORY\")" "$PRD_FILE")

  claude -p << EOF
Implement user story: $NEXT_STORY

$STORY

After implementation:
1. Run tests
2. Run typecheck
3. If both pass, mark story as complete in prd.json
EOF

  # Check if story was marked complete
  PASSES=$(jq -r ".userStories[] | select(.id == \"$NEXT_STORY\") | .passes" "$PRD_FILE")

  if [ "$PASSES" == "true" ]; then
    echo "Story $NEXT_STORY completed"
    git add -A
    git commit -m "feat: $NEXT_STORY - $(echo "$STORY" | jq -r '.title')"
  fi
done
```

---

## Pattern 2: Two-Phase Workflow

Separate planning and execution into distinct context windows.

### Phase 1: Planning (Fresh Context)

```bash
claude -p < PROMPT_plan.md > .ralph/plan.md
```

**PROMPT_plan.md:**
```markdown
# Planning Phase

Analyze the codebase and create a detailed implementation plan.

## Deliverable
Write the plan to `.ralph/plan.md` with:
- Ordered list of implementation steps
- Files to modify
- Tests to write
- Verification commands

## Constraints
- Read-only exploration
- Do not modify any files
- Output only the plan document
```

### Phase 2: Execution (Fresh Context)

```bash
claude -p < PROMPT_build.md --continue
```

**PROMPT_build.md:**
```markdown
# Build Phase

Read the plan from `.ralph/plan.md` and implement it.

## Plan
$(cat .ralph/plan.md)

## Instructions
- Implement each step in order
- Run tests after each change
- Commit when tests pass
- Output <promise>COMPLETE</promise> when done
```

---

## Pattern 3: Dual-Condition Exit Gate

Prevent premature exits with compound conditions.

### Exit Detection Logic

```bash
check_should_exit() {
  local exit_signal=$(jq -r '.exit_signal // false' .ralph/state/response.json)
  local completion_indicators=$(jq -r '.completion_indicators' .ralph/state/response.json)
  local remaining_tasks=$(grep -c "^\- \[ \]" .ralph/@fix_plan.md)

  # Dual condition: BOTH must be true
  if [[ "$completion_indicators" -ge 2 ]] && \
     [[ "$exit_signal" == "true" ]] && \
     [[ "$remaining_tasks" -eq 0 ]]; then
    echo "project_complete"
    return 0
  fi

  return 1
}
```

### RALPH_STATUS Block

Require structured status in every response:

```markdown
---RALPH_STATUS---
PHASE: 3
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: 1
FILES_MODIFIED: 5
TESTS_STATUS: PASSING | FAILING | NOT_RUN
EXIT_SIGNAL: false
CURRENT_TASK: P3-T3 - Generate personas
RECOMMENDATION: Continue to P3-T4
---END_RALPH_STATUS---
```

---

## Pattern 4: Circuit Breaker

Halt loops that aren't making progress.

### States

- **CLOSED**: Normal operation
- **OPEN**: Halted due to failures
- **HALF-OPEN**: Testing recovery

### Triggers

```bash
# No progress detection
if [[ $no_progress_count -ge 3 ]]; then
  echo '{"state": "OPEN", "reason": "No file changes for 3 loops"}' > .circuit_breaker
  exit 1
fi

# Repeated errors
if [[ $same_error_count -ge 5 ]]; then
  echo '{"state": "OPEN", "reason": "Same error 5 times"}' > .circuit_breaker
  exit 1
fi
```

### Recovery

```bash
# Manual reset after investigation
echo '{"state": "CLOSED", "no_progress_count": 0}' > .ralph/state/.circuit_breaker

# Automatic recovery attempt (after 1 hour)
if [[ $circuit_state == "OPEN" ]] && [[ $time_since_open -gt 3600 ]]; then
  echo '{"state": "HALF-OPEN"}' > .ralph/state/.circuit_breaker
fi
```

---

## Pattern 5: Subagents as Swap Space

Prevent main context degradation with subagent delegation.

### Problem

Single-agent loops "death spiral" when context fills with exploration/debugging artifacts.

### Solution

```
Main Agent (clean, focused)
    ↓ delegates expensive work
Subagent (exploration/review)
    ↓ returns concrete results
Main Agent resumes with clean context
```

### Implementation

```typescript
// Main agent delegates exploration
const plan = await subagent.explore(codebase);

// Main agent continues with plan (clean context)
await mainAgent.implement(plan);
```

### When to Use

- Complex debugging that requires reading many files
- Architecture planning with extensive exploration
- Code review that touches many modules
- Expensive reasoning that would pollute main context

---

## Pattern 6: Judge Agent Verification

Independent agent reviews work before completion.

### Three-Agent Pattern

1. **Planner**: Read-only exploration → generates plan
2. **Coder**: Writes code, runs commands
3. **Judge**: Verifies completion, can request changes

### Implementation

```typescript
const judge = new Agent({
  instructions: 'You are a code reviewer. Verify implementation meets requirements.',
  verifyCompletion: async ({ result }) => {
    const tests = await runTests();
    const typecheck = await runTypecheck();
    const review = await reviewCode(result);

    return {
      complete: tests.pass && typecheck.pass && review.approved,
      reason: review.feedback
    };
  }
});
```

---

## Pattern 7: Tmux Orchestration

Coordinate multiple agents across tmux sessions.

### Hub-and-Spoke Architecture

```
┌─────────────┐
│ Orchestrator│ ← Monitor & coordinate
└──────┬──────┘
       ↓
┌─────────────┐     ┌─────────────┐
│  Project    │     │  Project    │
│  Manager 1  │     │  Manager 2  │
└──────┬──────┘     └──────┬──────┘
       ↓                   ↓
┌─────────────┐     ┌─────────────┐
│ Engineer 1  │     │ Engineer 2  │
└─────────────┘     └─────────────┘
```

### Message Delivery

```bash
send_message() {
  local target="$1"
  local message="$2"

  tmux send-keys -t "$target" -l "$message"
  sleep 0.5
  tmux send-keys -t "$target" Enter
}

send_message "frontend:0" "Implement the login form"
```

### Session Recovery

Save session state to JSON for crash recovery:

```json
{
  "timestamp": "2026-01-01T12:00:00Z",
  "sessions": [
    {
      "name": "project-a",
      "working_dir": "~/Projects/a",
      "window_count": 3,
      "status": "active"
    }
  ]
}
```

---

## Context Budget Guidelines

### Token Allocation

| Context Section | Budget |
|-----------------|--------|
| System prompt   | ~16k overhead |
| Change log      | 5,000 tokens |
| File context    | 50,000 tokens (LRU eviction) |
| Summaries       | Variable (compressed history) |
| Recent iterations | Last 2-3 in full |
| **Total working set** | ~150,000 tokens |

### Smart Zone

```
Context Usage │ Performance
──────────────┼─────────────────────
    0-20%     │ Peak performance
   20-40%     │ Still great
   40-60%     │ SMART ZONE ✓
   60-80%     │ Missing instructions
   80-100%    │ Confused, repetitive
```

### Avoiding Redlining

- 200K tokens advertised = ~147-152K practical
- One task per loop = 100% smart zone utilization
- Fresh runs for planning (don't mix with execution)
- External files for specs, plans, learnings
