# Deep Study: Long-Running Agents, Ralph Loops, and Tmux Coordination

> Comprehensive analysis of autonomous AI agent patterns, ralph loops, and multi-agent orchestration systems
> Created: 2026-01-26
> Based on research across: ralph, ralph-claude-code, ralph-loop-agent, Tmux-Orchestrator, repomirror, and related documentation

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Ralph Loop Patterns](#ralph-loop-patterns)
3. [Tmux Orchestration](#tmux-orchestration)
4. [Exit Conditions & Completion Detection](#exit-conditions--completion-detection)
5. [Context Management](#context-management)
6. [Multi-Agent Coordination](#multi-agent-coordination)
7. [Backpressure & Verification](#backpressure--verification)
8. [Verification Patterns](#verification-patterns)
9. [Error Detection & Recovery](#error-detection--recovery)
10. [Workflow Patterns](#workflow-patterns)
11. [Hooks & Automation](#hooks--automation)
12. [Best Practices & Patterns](#best-practices--patterns)
13. [Implementation Examples](#implementation-examples)
14. [Key Insights & Lessons](#key-insights--lessons)

---

## Core Concepts

### What is a Ralph Loop?

**Ralph** (named after Ralph Wiggum) is fundamentally a **bash loop that re-runs an AI agent**:

```bash
while :; do cat PROMPT.md | claude-code; done
```

**Key Properties:**
- Each iteration = **fresh context window** (no memory between loops)
- Progress persists via **disk state** (git commits, files, task lists)
- Loop continues until **completion signal** or **safety limit**
- "Deterministically bad in an undeterministic world" - failures are patterns you can tune away

### The Minimal Mechanism

The purest form requires:
1. **Loop wrapper** (bash `while` loop)
2. **Prompt file** (instructions for each iteration)
3. **State persistence** (git, task files, progress logs)
4. **Exit conditions** (completion markers, max iterations, error detection)

### Core Philosophy

**"Everything is a Ralph Loop"** (Geoffrey Huntley):
- Software is "clay on the pottery wheel" - iterate until right
- **One task per loop** prevents drift
- **Operator job**: Engineer the loop, watch failures, add constraints
- **Monolithic over microservices**: One process, one repo, one loop

---

## Ralph Loop Patterns

### Pattern 1: Simple Bash Loop (ralph.sh)

**Location**: `docs/long-running-claude/repos/ralph/ralph.sh`

```bash
for i in $(seq 1 $MAX_ITERATIONS); do
  if [[ "$TOOL" == "amp" ]]; then
    OUTPUT=$(cat "$SCRIPT_DIR/prompt.md" | amp --dangerously-allow-all 2>&1)
  else
    OUTPUT=$(claude --dangerously-skip-permissions --print < "$SCRIPT_DIR/CLAUDE.md" 2>&1)
  fi
  
  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo "Ralph completed all tasks!"
    exit 0
  fi
done
```

**Characteristics:**
- Simple iteration counter
- Completion detection via `<promise>COMPLETE</promise>` marker
- Supports both Amp and Claude Code
- Progress tracked in `prd.json` and `progress.txt`

### Pattern 2: Advanced Loop with Exit Detection (ralph-claude-code)

**Location**: `docs/long-running-claude/repos/ralph-claude-code/`

**Features:**
- **Dual-condition exit gate**: Requires BOTH completion indicators AND explicit `EXIT_SIGNAL: true`
- **Circuit breaker**: Detects stuck loops (no progress, repeated errors)
- **Rate limiting**: 100 calls/hour with hourly reset
- **Session continuity**: `--continue` flag preserves context across iterations
- **Response analyzer**: Semantic understanding of Claude's output

**Exit Detection Logic:**
```bash
# Dual-condition check
if [[ $recent_completion_indicators -ge 2 ]] && [[ "$exit_signal" == "true" ]]; then
    echo "project_complete"
    return 0
fi
```

**Circuit Breaker States:**
- **CLOSED**: Normal operation
- **OPEN**: Halted after 3 loops with no file changes OR 5 loops with same errors

### Pattern 3: Programmatic Framework (ralph-loop-agent)

**Location**: `docs/long-running-claude/repos/ralph-loop-agent/`

**TypeScript framework** built on Vercel AI SDK:

```typescript
const agent = new RalphLoopAgent({
  model: 'anthropic/claude-opus-4.5',
  instructions: 'You are a helpful coding assistant.',
  stopWhen: iterationCountIs(10),
  verifyCompletion: async ({ result }) => ({
    complete: result.text.includes('DONE'),
    reason: 'Task completed successfully',
  }),
});

const { text, iterations, completionReason } = await agent.loop({
  prompt: 'Create a function that calculates fibonacci numbers',
});
```

**Architecture:**
- **Inner loop**: AI SDK tool loop (LLM ↔ tools until done)
- **Outer loop**: Ralph loop (repeat until verified complete)
- **Context manager**: Tracks changes, file context, summaries
- **Stop conditions**: Iteration count, token count, cost limits

### Pattern 4: Dual-Mode Loop (ralph-playbook)

**Location**: `docs/ralph-orchestrator-study/docs/ralph-study/ralph-playbook/files/loop.sh`

**Two modes:**
- **Plan mode**: `PROMPT_plan.md` - Exploration, planning, task identification
- **Build mode**: `PROMPT_build.md` - Implementation, execution, testing

```bash
if [ "$1" = "plan" ]; then
    PROMPT_FILE="PROMPT_plan.md"
else
    PROMPT_FILE="PROMPT_build.md"
fi

cat "$PROMPT_FILE" | claude -p \
    --dangerously-skip-permissions \
    --output-format=stream-json \
    --model opus \
    --verbose
```

**Auto-push after each iteration** to keep remote in sync.

---

## Tmux Orchestration

### Architecture: Three-Tier Hierarchy

```
┌─────────────┐
│ Orchestrator│ ← You interact here
└──────┬──────┘
       │ Monitors & coordinates
       ▼
┌─────────────┐     ┌─────────────┐
│  Project    │     │  Project    │
│  Manager 1  │     │  Manager 2  │ ← Assign tasks, enforce specs
└──────┬──────┘     └──────┬──────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│ Engineer 1  │     │ Engineer 2  │ ← Write code, fix bugs
└─────────────┘     └─────────────┘
```

**Why Separate Agents?**
- **Limited context windows**: Each agent stays focused
- **Specialized expertise**: PMs manage, engineers code
- **Parallel work**: Multiple engineers simultaneously
- **Better memory**: Smaller contexts = better recall

### Key Components

#### 1. Message Delivery System

**Script**: `send-claude-message.sh`

```bash
#!/bin/bash
WINDOW="$1"
MESSAGE="$2"

# Send as literal text (avoids quote issues)
tmux send-keys -t "$WINDOW" -l "$MESSAGE"

# Wait for UI to register
sleep 0.5

# Send Enter to submit
tmux send-keys -t "$WINDOW" Enter

# Double-check verification
sleep 0.5
LAST_LINE=$(tmux capture-pane -t "$WINDOW" -p | tail -1 | tr -d '[:space:]')
MESSAGE_END=$(echo "$MESSAGE" | tail -c 20 | tr -d '[:space:]')
if [[ "$LAST_LINE" == *"$MESSAGE_END"* ]]; then
    tmux send-keys -t "$WINDOW" Enter  # Retry
fi
```

**Why This Pattern?**
- Handles timing complexities automatically
- Prevents message submission failures
- Works with both windows and panes
- Consistent messaging across all agents

#### 2. Self-Scheduling System

**Script**: `schedule_with_note.sh`

```bash
#!/bin/bash
MINUTES=${1:-3}
NOTE=${2:-"Standard check-in"}
TARGET=${3:-"tmux-orc:0"}

# Create note file
echo "$NOTE" > next_check_note.txt

# Schedule with nohup (detached)
SECONDS=$(echo "$MINUTES * 60" | bc)
nohup bash -c "sleep $SECONDS && tmux send-keys -t $TARGET 'Time for check!' && sleep 1 && tmux send-keys -t $TARGET Enter" > /dev/null 2>&1 &
```

**Critical**: Orchestrator must know its own window to schedule correctly:
```bash
CURRENT_WINDOW=$(tmux display-message -p "#{session_name}:#{window_index}")
./schedule_with_note.sh 30 "Check PM progress" "$CURRENT_WINDOW"
```

#### 3. Session Recovery

**Automatic session logging** every 5 minutes:
```bash
watch -n 300 ./session-manager/save-sessions.sh &
```

**Session state** saved to JSON:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "sessions": [
    {
      "name": "stn",
      "working_dir": "~/Coding/spiritually-transformative-network",
      "window_count": 3,
      "windows": ["Claude-Agent", "Shell", "Dev-Server"],
      "status": "active"
    }
  ]
}
```

**Restore after crash**:
```bash
./session-manager/restore-sessions.sh
```

#### 4. Communication Protocol

**Hub-and-Spoke Model** (prevents n² complexity):
- Developers report to PM only
- PM aggregates and reports to Orchestrator
- Cross-functional communication goes through PM
- Emergency escalation directly to Orchestrator

**Message Templates:**
```
STATUS [AGENT_NAME] [TIMESTAMP]
Completed: 
- [Specific task 1]
- [Specific task 2]
Current: [What working on now]
Blocked: [Any blockers]
ETA: [Expected completion]
```

#### 5. Claude Code Hooks Integration

**Automatic notifications** via `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "PROJECT=$(basename \"$PWD\"); ~/Coding/Tmux-Orchestrator/send-claude-message.sh orc:0 \"$PROJECT: Session stopped\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_TOOL_OUTPUT\" | grep -q \"All.*tests.*pass\"; then PROJECT=$(basename \"$PWD\"); ~/Coding/Tmux-Orchestrator/send-claude-message.sh orc:0 \"$PROJECT: All tests passing!\"; fi"
          }
        ]
      }
    ]
  }
}
```

---

## Exit Conditions & Completion Detection

### Exit Condition Priority Order

1. **Circuit Breaker OPEN**
   - 3 loops with no file changes → HALT
   - 5 loops with same error → HALT
   - Human must investigate and reset

2. **All Tasks Complete**
   - All items in `@fix_plan.md` marked `[x]`
   - Ralph sets `EXIT_SIGNAL: true`
   - Loop exits with success

3. **Explicit EXIT_SIGNAL** (Dual-Condition)
   - Requires BOTH: `completion_indicators >= 2` AND `EXIT_SIGNAL: true`
   - Prevents premature exit on false positives
   - Only when Claude confirms "project fully complete"

4. **Safety Circuit Breaker**
   - Force exit after 5 consecutive completion indicators
   - Prevents infinite loops when heuristics fail

5. **Max Iterations**
   - Safety limit to prevent runaway loops
   - Default: 10 iterations (configurable)

6. **Manual Interrupt**
   - Ctrl+C during loop
   - Session preserved (can resume with `--continue`)

### Completion Detection Logic

**Dual-Condition Exit Gate:**

| completion_indicators | EXIT_SIGNAL | Result |
|----------------------|-------------|--------|
| >= 2 | `true` | **Exit** ("project_complete") |
| >= 2 | `false` | **Continue** (Claude still working) |
| >= 2 | missing | **Continue** (defaults to false) |
| < 2 | `true` | **Continue** (threshold not met) |

**Implementation:**
```bash
local claude_exit_signal="false"
if [[ -f "$RESPONSE_ANALYSIS_FILE" ]]; then
    claude_exit_signal=$(jq -r '.analysis.exit_signal // false' "$RESPONSE_ANALYSIS_FILE")
fi

if [[ $recent_completion_indicators -ge 2 ]] && [[ "$claude_exit_signal" == "true" ]]; then
    echo "project_complete"
    return 0
fi
```

### Completion Markers

**Simple marker** (ralph.sh):
```xml
<promise>COMPLETE</promise>
```

**Structured status block** (ralph-claude-code):
```markdown
## RALPH_STATUS
- STATUS: COMPLETE
- EXIT_SIGNAL: true
- REASON: All tasks completed, tests passing
```

---

## Context Management

### The Context Problem

**Challenge**: Context windows fill up quickly in long-running loops.

**Solutions:**

1. **Fresh Context Per Iteration** (Simple Ralph)
   - Each loop = new context window
   - Progress via disk state (git, files)
   - No context bloat

2. **Session Continuity** (Advanced Ralph)
   - `--continue` flag preserves context
   - Faster iterations (no re-reading codebase)
   - Auto-reset between phases or after 24 hours

3. **Context Manager** (ralph-loop-agent)
   - **Change log**: Decisions and file modifications
   - **File context**: Recently read files (LRU eviction)
   - **Summaries**: Compress older iterations
   - Keep last N iterations uncompressed

### Context Window Degradation Problem

**The Redlining Issue** (from ghuntley-redlining.md):

**Observed Behavior:**
- Claude 3.7 advertised: **200k tokens**
- Practical degradation: **~147k–152k tokens**
- When clipping occurs: **tool-call → tool-call loop starts failing**

**Performance Degradation Curve:**
```
Context Usage │ Model Performance
──────────────┼───────────────────────────────────────────
    0-20%     │ ████████████████████ Peak performance
   20-40%     │ ██████████████████   Still great
   40-60%     │ ███████████████      Noticeably worse
   60-80%     │ ██████████           Missing instructions
   80-100%    │ █████                Confused, repetitive
```

**Why Degradation Happens:**
- **Attention diffusion**: Model must attend to more content; important instructions get lost
- **Conflicting signals**: Earlier errors, corrections, abandoned approaches remain in context
- **Instruction drift**: Original prompt gets buried under tool outputs
- **Noise accumulation**: Every tool call, file read, intermediate step adds irrelevant tokens

### Context Budget Guidelines

**From ralph-playbook:**
- 200K+ tokens advertised = ~176K truly usable (accounting for degradation)
- **40-60% context utilization = "smart zone"** (optimal performance)
- **One task per loop = 100% smart zone utilization**
- Each iteration starts fresh - context is garbage collected

**Token Budget Allocation** (ralph-loop-agent pattern):
- **Change log**: 5,000 tokens (decisions and file modifications)
- **File context**: 50,000 tokens (recently read files, LRU eviction)
- **Summaries**: Variable (compressed older iterations)
- **Recent iterations**: Keep last 2-3 in full detail
- **Total working set**: ~150,000 tokens (leaves room for output)

**Best Practices:**
- **Avoid redlining**: Don't treat max tokens as safe operating point
- **Keep prompts concise**: Ballooned prompts make agents "slower and dumber"
- **One task per iteration**: Prevents context bloat
- **Use external files**: Specifications, plans, learnings stored on disk
- **Let git history carry context**: Don't re-read unchanged files
- **Fresh runs for planning**: Don't mix planning and execution in same context

---

## Multi-Agent Coordination

### Agent Types

1. **Orchestrator**: High-level oversight, cross-project coordination
2. **Project Manager**: Quality-focused team coordination, task assignment
3. **Developer**: Implementation and technical decisions
4. **QA Engineer**: Testing and verification
5. **Code Reviewer**: Security and best practices
6. **Principal Developer**: Complex implementations and architectural decisions

### Coordination Patterns

#### Pattern 1: Hub-and-Spoke

```
Orchestrator
    ↓
Project Manager
    ↓
Developers (parallel)
```

**Benefits:**
- Prevents n² message complexity
- Clear reporting hierarchy
- Scalable to many agents

#### Pattern 2: Three-Agent Pattern (ralph-loop-agent)

1. **Interviewer/Planner**: Read-only exploration → generates plan
2. **Coder**: Writes + runs commands
3. **Judge**: Verifies completion; can request changes

**This is**: "Subagents as swap space + judge as oracle"

#### Pattern 3: Quality Gate Process

```
Code Change → Code Reviewer → Test Automation → Approval
     ↓              ↓              ↓
Security Check  Coverage Check  Quality Gate
```

### Communication Best Practices

1. **No Chit-Chat**: All messages work-related
2. **Use Templates**: Reduces ambiguity
3. **Acknowledge Receipt**: Simple "ACK" for tasks
4. **Escalate Quickly**: Don't stay blocked >10 min
5. **One Topic Per Message**: Keep focused

---

## Backpressure & Verification

### What is Backpressure?

**Definition**: Automated feedback mechanisms (quality + correctness) that keep agents aligned over time.

**From moss-backpressure.md:**
> "Long-horizon agents work better when you wrap them in structure that produces automated feedback. That feedback is 'backpressure' that keeps the agent aligned over time."

### Backpressure Mechanisms

1. **Build/Test Execution**
   - Give agent Bash/CI so it can compile, read errors, self-correct
   - Typecheck, lint, tests provide immediate feedback

2. **Typed Languages + Good Errors**
   - Expressive type systems and high-quality compiler errors
   - "Free feedback" directly reusable by agents

3. **UI Feedback**
   - Tools that let agents *see* rendered output
   - Playwright/Chrome DevTools via MCP
   - Reduces human UI checking

4. **Lint/LSP Feedback**
   - Expose linters/static analysis through tools
   - Agents iterate until clean

5. **Spec-Driven Loops**
   - Auto-generate docs from schemas (e.g., OpenAPI)
   - Agent can compare intended vs produced artifacts

6. **"Pull the Slot Machine Lever Until Trusted"**
   - Fuzzing/proof assistants/logic constraints
   - Hard acceptance gates

### Why Backpressure Matters

**Ralph-style loops are cheap repetition; backpressure is what makes repetition converge:**
- Loop without gates → drift / overconfidence
- Loop with gates → gradual improvement toward "passes"

### Verification Functions

**Example from ralph-loop-agent:**
```typescript
verifyCompletion: async () => {
  const checks = await Promise.all([
    fileExists('vitest.config.ts'),
    !await fileExists('jest.config.js'),
    noFilesMatch('**/*.test.ts', /from ['"]@jest/),
    fileContains('package.json', '"vitest"'),
  ]);
  
  return { 
    complete: checks.every(Boolean),
    reason: checks.every(Boolean) ? 'Migration complete' : 'Structural checks failed'
  };
}
```

---

## Verification Patterns

### The Core Principle

**"Verification is non-negotiable"** (from claudefast-ralph-wiggum-technique):
> "Always give Claude a way to verify its work"

Without verification, agents drift, overestimate completion, and waste compute.

### Pattern 1: Tests-First Verification (Best When Possible)

**Approach**: Write tests before implementation, use test results as completion gate.

**Example:**
```bash
# In PROMPT.md
## Verification
Before marking task complete, run:
- npm test
- npm run typecheck
- npm run lint

Only set EXIT_SIGNAL: true if ALL tests pass.
```

**Benefits:**
- Objective, automated feedback
- Prevents false completion signals
- Forces correct implementation

**Limitation**: Not all tasks have testable outputs (e.g., UI changes, documentation).

### Pattern 2: Stop-Hook Validation (Claude Code)

**Mechanism** (from claudefast-ralph-wiggum-technique):
1. Claude works
2. Claude tries to stop
3. **Stop hook intercepts** and checks completion
4. If not done, feed back and continue
5. If done, allow stop

**Implementation** (`.claude/settings.json`):
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "if ! npm test; then echo 'Tests failed - blocking stop'; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

**Exit Code 2**: Blocks Claude from stopping (forces continuation).

**Benefits:**
- Automatic verification without manual intervention
- Prevents premature completion
- Can combine multiple checks (tests + lint + typecheck)

### Pattern 3: Judge Agent Verification (Independent Review)

**Pattern**: Separate agent reviews work before completion.

**Three-Agent Pattern:**
1. **Interviewer/Planner**: Read-only exploration → generates plan
2. **Coder**: Writes + runs commands
3. **Judge**: Verifies completion; can request changes

**Implementation:**
```typescript
const judge = new RalphLoopAgent({
  model: 'anthropic/claude-opus-4.5',
  instructions: 'You are a code reviewer. Verify the implementation meets requirements.',
  verifyCompletion: async ({ result }) => {
    // Judge reviews coder's work
    const review = await reviewCode(result.text);
    return {
      complete: review.approved,
      reason: review.feedback
    };
  }
});
```

**Benefits:**
- Independent verification (reduces bias)
- Can catch issues coder missed
- Provides structured feedback

**Trade-off**: Additional compute cost for judge agent.

### Pattern 4: UI Verification (Screenshot-Based)

**The Hidden Trap** (from claudefast-ralph-wiggum-technique):
> "Tests can pass while UI is broken"

**Protocol:**
1. Take screenshots of UI changes
2. Require explicit verification/renaming in later iteration
3. Only then allow completion promise

**Example:**
```markdown
## UI Verification Protocol
1. Take screenshot: `screenshot.png`
2. In next iteration, rename to `screenshot-verified.png` if UI is correct
3. Only set EXIT_SIGNAL: true after screenshot is verified
```

**Benefits:**
- Catches UI regressions tests miss
- Forces visual verification
- Prevents "tests pass, UI broken" scenarios

### Pattern 5: Spec-Driven Verification

**Approach**: Compare implementation against specification.

**From ghuntley-specs:**
- Write design/spec artifact first (durable file)
- Use agent loop to implement against that artifact
- Rely on compiler/test feedback as backpressure

**Example:**
```typescript
verifyCompletion: async () => {
  const spec = await readFile('specs/api.md');
  const implementation = await readFile('src/api.ts');
  
  // Check if implementation matches spec requirements
  const checks = [
    spec.includes('GET /users') && implementation.includes('app.get("/users"'),
    spec.includes('POST /users') && implementation.includes('app.post("/users"'),
    // ... more checks
  ];
  
  return {
    complete: checks.every(Boolean),
    reason: checks.every(Boolean) ? 'Matches spec' : 'Missing requirements'
  };
}
```

**Benefits:**
- Ensures implementation matches design
- Prevents scope creep
- Provides clear completion criteria

### Combining Verification Patterns

**Best Practice**: Use multiple verification methods:

```typescript
verifyCompletion: async () => {
  // 1. Structural checks
  const structural = await checkStructure();
  
  // 2. Test execution
  const tests = await runTests();
  
  // 3. Spec compliance
  const spec = await checkSpec();
  
  // 4. Judge review (for complex changes)
  const review = await judgeReview();
  
  return {
    complete: structural && tests && spec && review,
    reason: 'All verification checks passed'
  };
}
```

---

## Error Detection & Recovery

### Two-Stage Error Filtering

**Problem**: JSON field names like `"is_error": false` trigger false positives.

**Solution** (from ralph-claude-code):
```bash
# Stage 1: Filter out JSON field patterns
grep -v '"[^"]*error[^"]*":' "$output_file" | \
# Stage 2: Count actual error messages
grep -cE '(^Error:|^ERROR:|^error:|\]: error|Link: error|Error occurred|failed with error|[Ee]xception|Fatal|FATAL)'
```

**Benefits:**
- Eliminates false positives from JSON structure
- Accurately detects real errors
- Prevents circuit breaker false triggers

### Stuck Loop Detection

**Multi-Line Error Matching:**
```bash
# Detect errors that span multiple lines
error_count=$(grep -cE '(Error:|ERROR:|Exception|Fatal)' "$output_file" | \
              grep -v '"[^"]*error[^"]*":' | \
              wc -l)
```

**Patterns Indicating Stuck Loops:**
- Same error repeated 5+ times
- No file changes for 3+ consecutive loops
- Output length declining by >70%
- Test-only loops (no implementation)

### Circuit Breaker Pattern

**States:**
- **CLOSED**: Normal operation
- **OPEN**: Halted due to failures
- **HALF-OPEN**: Testing recovery

**Triggers:**
- **No progress**: 3 loops with no file changes
- **Repeated errors**: 5 loops with same error
- **Output decline**: >70% reduction in output length

**Recovery:**
```bash
# Manual reset after investigation
echo '{"state": "CLOSED", "no_progress_count": 0}' > .ralph/state/.circuit_breaker

# Or automatic recovery attempt
if [[ $circuit_state == "OPEN" ]] && [[ $time_since_open -gt 3600 ]]; then
  circuit_state="HALF-OPEN"  # Test recovery
fi
```

### Error Response Patterns

**Early Stopping** (from repomirror):
- Agents used `pkill` to terminate themselves when stuck
- Self-awareness of failure state
- Prevents infinite loops

**Error Classification:**
```typescript
interface ErrorClassification {
  type: 'transient' | 'permanent' | 'blocker';
  retryable: boolean;
  requiresHuman: boolean;
  suggestedAction: string;
}
```

**Recovery Strategies:**
- **Transient errors**: Retry with exponential backoff
- **Permanent errors**: Skip task, log for human review
- **Blockers**: Halt loop, escalate to human

---

## Workflow Patterns

### Pattern 1: Two-Phase Workflow (Context Hygiene)

**The Problem**: Mixing planning and execution in same context window causes:
- Instruction drift
- Context bloat
- Conflicting signals

**The Solution** (from claudefast-ralph-wiggum-technique):
- **Phase 1**: Planning/spec creation (fresh context)
- **Phase 2**: Fresh context + run loop against the plan

**Implementation:**
```bash
# Phase 1: Planning
claude -p < PROMPT_plan.md > plan.md

# Phase 2: Execution (fresh context)
claude -p < PROMPT_build.md --continue
```

**Benefits:**
- Clean separation of concerns
- No planning artifacts in execution context
- Better focus on implementation

### Pattern 2: PRD → Task Queue Loop

**The Pattern** (from snarktank-ralph):
1. Write PRD (human-readable requirements)
2. Convert to `prd.json` of small user stories
3. Loop:
   - Pick next story where `passes: false`
   - Implement it
   - Run verification (tests/typecheck)
   - If passing: mark `passes: true`, commit, log progress
4. Stop when all stories are complete

**User Story Structure:**
```json
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
```

**Benefits:**
- **Task sizing** becomes enforceable (each story = "one bite")
- Deterministic notion of what remains (`passes: false`)
- Learnings written to file (e.g., `AGENTS.md`) for future iterations

### Pattern 3: Dual-Mode Loop (Plan vs Build)

**Two Modes:**
- **Plan mode**: `PROMPT_plan.md` - Exploration, planning, task identification
- **Build mode**: `PROMPT_build.md` - Implementation, execution, testing

**Usage:**
```bash
./loop.sh plan      # Planning phase
./loop.sh build     # Implementation phase
```

**Benefits:**
- Clear mode separation
- Can switch modes based on needs
- Planning doesn't pollute execution context

### Pattern 4: Subagents as Swap Space

**The Problem** (from ghuntley-subagents):
- Single-agent loops "death spiral" when main context degrades
- Expensive exploration/reasoning burns main context

**The Solution**:
- **Main agent**: Stays focused on execution, keeps small clean working set
- **Subagents**: Do expensive exploration/reasoning/review in their own context window
- **Main agent resumes**: With concrete next steps from subagent output

**Implementation:**
```typescript
// Main agent delegates exploration to subagent
const plan = await subagent.explore(codebase);
// Main agent continues with plan (clean context)
await mainAgent.implement(plan);
```

**Benefits:**
- Prevents main context degradation
- Allows expensive operations without polluting main loop
- "Swap space" for context management

---

## Hooks & Automation

### Claude Code Hooks Lifecycle

**Available Events:**
- `PreToolUse` - Before tool execution
- `PermissionRequest` - When permission needed
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - When user submits prompt
- `Notification` - System notifications
- `Stop` - When Claude tries to stop
- `SubagentStop` - When subagent stops
- `PreCompact` - Before context compaction
- `Setup` - During initialization
- `SessionStart` - Session begins
- `SessionEnd` - Session ends

### Common Hook Patterns

#### 1. Auto-Formatting (PostToolUse)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=$(echo '$CLAUDE_TOOL_INPUT' | jq -r '.file_path'); if [[ $FILE == *.ts ]]; then prettier --write \"$FILE\"; fi"
          }
        ]
      }
    ]
  }
}
```

#### 2. File Protection (PreToolUse)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=$(echo '$CLAUDE_TOOL_INPUT' | jq -r '.file_path'); if [[ $FILE == .env ]] || [[ $FILE == .git/* ]]; then exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

**Exit Code 2**: Blocks the tool use.

#### 3. Command Logging (PreToolUse)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '$CLAUDE_TOOL_INPUT' | jq -r '.command' >> .ralph/logs/commands.log"
          }
        ]
      }
    ]
  }
}
```

#### 4. Stop-Hook Verification

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "if ! npm test; then echo 'Tests failed'; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

### Checkpointing Limitations

**Important** (from claude-code-checkpointing):
- Checkpoints persist across sessions
- **Bash-modified files are NOT tracked** by checkpointing
- Not a replacement for version control (git still matters)

**Implication**: If loop uses bash commands that modify files, can't rely on checkpoint rewind as safety net.

---

## Best Practices & Patterns

### Writing Effective Prompts

**From ghuntley-stdlib**: Most people get weak results because they:
- Use assistant like Google Search
- **Underspecify prompts** (low-level "implement XYZ please")
- Treat assistant like IDE instead of **autonomous agent**
- Don't realize you can **program LLM outcomes** (structure + feedback loops)

**Best Practices:**
1. **Be Specific**: Clear requirements lead to better results
2. **Prioritize**: Use task lists to guide focus
3. **Set Boundaries**: Define what's in/out of scope
4. **Include Examples**: Show expected inputs/outputs
5. **Keep It Short**: Ballooned prompts make agents "slower and dumber"
6. **Build Standard Library**: Create reusable patterns, constraints, workflows
7. **Program Outcomes**: Use structure + feedback loops, not just instructions

### Project Structure

**Standard Ralph structure:**
```
my-project/
├── .ralph/                 # Ralph configuration
│   ├── PROMPT.md           # Main development instructions
│   ├── @fix_plan.md        # Prioritized task list
│   ├── @AGENT.md           # Build and run instructions
│   ├── specs/              # Project specifications
│   ├── logs/               # Execution logs
│   └── status.json         # Programmatic status
└── src/                    # Source code
```

### Git Discipline

**MANDATORY FOR ALL AGENTS:**

1. **Auto-Commit Every 30 Minutes**
   ```bash
   git add -A
   git commit -m "Progress: [specific description]"
   ```

2. **Commit Before Task Switches**
   - Never leave uncommitted changes when switching context
   - Tag working versions before major changes

3. **Feature Branch Workflow**
   ```bash
   git checkout -b feature/[descriptive-name]
   # ... work ...
   git commit -m "Complete: [feature description]"
   git tag stable-[feature]-$(date +%Y%m%d-%H%M%S)
   ```

4. **Meaningful Commit Messages**
   - Bad: "fixes", "updates", "changes"
   - Good: "Add user authentication endpoints with JWT tokens"

### Task Sizing

**Right-sized stories:**
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

**Too big (split these):**
- "Build the entire dashboard"
- "Add authentication"
- "Refactor the API"

### Monitoring & Debugging

**Live Dashboard:**
```bash
ralph --monitor  # Integrated tmux monitoring
ralph-monitor    # Manual monitoring dashboard
```

**Status Checking:**
```bash
ralph --status           # JSON status output
tail -f .ralph/logs/ralph.log  # Manual log inspection
```

---

## Implementation Examples

### Example 1: Simple Ralph Loop

```bash
#!/bin/bash
MAX_ITERATIONS=10

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "Iteration $i of $MAX_ITERATIONS"
  
  OUTPUT=$(claude --dangerously-skip-permissions < PROMPT.md 2>&1)
  
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo "Completed at iteration $i"
    exit 0
  fi
  
  sleep 2
done

echo "Reached max iterations without completion"
```

### Example 2: Ralph with Exit Detection

```bash
#!/bin/bash
# Check exit conditions
check_should_exit() {
  # 1. Check all tasks complete
  if all_tasks_complete; then
    echo "all_tasks_complete"
    return 0
  fi
  
  # 2. Check EXIT_SIGNAL
  local exit_signal=$(get_exit_signal)
  local completion_indicators=$(get_completion_indicators)
  
  # 3. Dual-condition check
  if [[ $completion_indicators -ge 2 ]] && [[ "$exit_signal" == "true" ]]; then
    echo "project_complete"
    return 0
  fi
  
  return 1
}

# Main loop
while true; do
  claude --dangerously-skip-permissions < PROMPT.md
  
  EXIT_REASON=$(check_should_exit)
  if [[ -n "$EXIT_REASON" ]]; then
    echo "Exiting: $EXIT_REASON"
    break
  fi
done
```

### Example 3: Tmux Agent Communication

```bash
#!/bin/bash
# Send message to Claude agent
send_message() {
  local target="$1"
  local message="$2"
  
  tmux send-keys -t "$target" -l "$message"
  sleep 0.5
  tmux send-keys -t "$target" Enter
}

# Schedule check-in
schedule_checkin() {
  local minutes="$1"
  local note="$2"
  local target="$3"
  
  local seconds=$((minutes * 60))
  nohup bash -c "sleep $seconds && send_message '$target' '$note'" > /dev/null 2>&1 &
}

# Usage
send_message "frontend:0" "What's your progress on the login form?"
schedule_checkin 30 "Review auth implementation" "pm:0"
```

### Example 4: Programmatic Ralph Loop

```typescript
import { RalphLoopAgent, iterationCountIs } from 'ralph-loop-agent';

const agent = new RalphLoopAgent({
  model: 'anthropic/claude-opus-4.5',
  instructions: 'You are migrating a codebase from Jest to Vitest.',
  tools: { readFile, writeFile, execute },
  stopWhen: iterationCountIs(50),
  verifyCompletion: async () => {
    const checks = await Promise.all([
      fileExists('vitest.config.ts'),
      !await fileExists('jest.config.js'),
      noFilesMatch('**/*.test.ts', /from ['"]@jest/),
    ]);
    return { 
      complete: checks.every(Boolean),
      reason: checks.every(Boolean) ? 'Migration complete' : 'Checks failed'
    };
  },
});

const result = await agent.loop({
  prompt: 'Migrate all Jest tests to Vitest.',
});

console.log(`Completed in ${result.iterations} iterations`);
```

### Example 5: Stop-Hook Verification Pattern

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "if ! npm test 2>/dev/null; then echo 'Tests failed - blocking stop'; exit 2; fi"
          },
          {
            "type": "command",
            "command": "if ! npm run typecheck 2>/dev/null; then echo 'Typecheck failed - blocking stop'; exit 2; fi"
          },
          {
            "type": "command",
            "command": "if ! npm run lint 2>/dev/null; then echo 'Lint failed - blocking stop'; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

**How It Works:**
1. Claude completes work and tries to stop
2. Stop hook runs verification commands
3. If any check fails (exit code 2), Claude is blocked from stopping
4. Claude receives feedback and continues work
5. Loop repeats until all checks pass

### Example 6: Two-Phase Workflow

```bash
#!/bin/bash
# Phase 1: Planning (fresh context)
echo "=== PLANNING PHASE ==="
claude -p < PROMPT_plan.md > .ralph/plan.md

# Verify plan was created
if [ ! -f .ralph/plan.md ]; then
  echo "Planning failed"
  exit 1
fi

# Phase 2: Execution (fresh context, uses plan)
echo "=== EXECUTION PHASE ==="
cat > PROMPT_build.md << EOF
# Build Phase

Read the plan from .ralph/plan.md and implement it.

## Plan
$(cat .ralph/plan.md)

## Instructions
- Implement each task in the plan
- Run tests after each change
- Commit when tests pass
EOF

claude -p < PROMPT_build.md --continue
```

### Example 7: PRD → Task Queue Loop

```bash
#!/bin/bash
PRD_FILE="prd.json"

while true; do
  # Find next incomplete story
  NEXT_STORY=$(jq -r '.userStories[] | select(.passes == false) | .id' "$PRD_FILE" | head -1)
  
  if [ -z "$NEXT_STORY" ]; then
    echo "All stories complete!"
    break
  fi
  
  STORY=$(jq -r ".userStories[] | select(.id == \"$NEXT_STORY\")" "$PRD_FILE")
  
  # Implement story
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

## Key Insights & Lessons

### From Geoffrey Huntley

1. **"Ralph is a Bash loop"** - Keep it simple
2. **"Everything is a Ralph loop"** - Iterate until right
3. **"One task per loop"** - Prevents drift
4. **"Deterministically bad"** - Failures are patterns you can tune
5. **"Disk is memory"** - Repo carries state between iterations

### From repomirror Field Report

1. **Early stopping**: Agents used `pkill` to terminate themselves when stuck
2. **Overachieving**: After finishing, agents added features beyond scope
3. **Prompt simplicity**: Ballooned prompts made agents "slower and dumber"
4. **Operational constraints**: "Make a commit after every file edit" worked well

### From Tmux Orchestrator

1. **Message delivery timing**: 0.5s delay critical for reliable submission
2. **Session recovery**: JSON state persistence enables crash recovery
3. **Hub-and-spoke**: Prevents n² communication complexity
4. **Hook integration**: Claude Code hooks enable automatic notifications
5. **Relative paths**: Never use absolute paths for portability

### From ralph-claude-code

1. **Dual-condition exit**: Prevents premature exits
2. **Circuit breaker**: Essential for detecting stuck loops
3. **Session continuity**: Speeds up iterations but requires management
4. **Response analysis**: Semantic understanding improves exit detection
5. **Rate limiting**: Prevents API overuse

### From ralph-loop-agent

1. **Context manager**: Explicit context budgets prevent bloat
2. **Verification functions**: Programmatic completion checks
3. **Stop conditions**: Multiple safety mechanisms (iterations, tokens, cost)
4. **Three-agent pattern**: Planner → Coder → Judge works well

### From claudefast-ralph-wiggum-technique

1. **Stop-hook pattern**: Intercept stop attempts, verify before allowing
2. **Two-phase workflow**: Don't mix planning and execution
3. **UI verification trap**: Tests can pass while UI is broken
4. **Verification is non-negotiable**: Always give Claude a way to verify work

### From ghuntley-redlining

1. **Context window clipping**: Advertised 200k = ~147k-152k practical
2. **Avoid redlining**: Don't treat max tokens as safe operating point
3. **Smart zone**: 40-60% utilization for optimal performance
4. **External state**: Long-running autonomy needs disk-based state

### From ghuntley-subagents

1. **Subagents as swap space**: Burn tokens elsewhere, keep main thread clean
2. **Death spiral prevention**: Single-agent loops degrade when context fills
3. **Hierarchical pattern**: Main agent + subagents for expensive operations

### From ghuntley-specs & stdlib

1. **Spec-driven loops**: Write design first, implement against spec
2. **Standard library**: Build reusable patterns, constraints, workflows
3. **Program outcomes**: Use structure + feedback, not just instructions
4. **Underspecification problem**: Low-level prompts get weak results

### Critical Anti-Patterns

1. ❌ **Meeting Hell**: Use async updates only
2. ❌ **Endless Threads**: Max 3 exchanges, then escalate
3. ❌ **Broadcast Storms**: No "FYI to all" messages
4. ❌ **Micromanagement**: Trust agents to work
5. ❌ **Quality Shortcuts**: Never compromise standards
6. ❌ **Blind Scheduling**: Never schedule without verifying target window
7. ❌ **Absolute Paths**: Always use relative paths
8. ❌ **No Backpressure**: Always provide verification mechanisms
9. ❌ **Redlining Context**: Don't push to 80%+ utilization
10. ❌ **Mixing Planning & Execution**: Keep phases separate
11. ❌ **No Error Filtering**: Use two-stage filtering to avoid false positives
12. ❌ **Ignoring UI Verification**: Tests can pass while UI is broken

---

## Decision Framework: Choosing Your Pattern

### When to Use Simple Bash Loop

**Use when:**
- Small, well-defined tasks
- Single developer workflow
- Minimal verification needs
- Quick iterations (< 10 loops)

**Example**: Fixing lint errors, adding simple features, documentation updates

### When to Use Advanced Loop (ralph-claude-code)

**Use when:**
- Complex projects with many tasks
- Need circuit breaker protection
- Want session continuity
- Require rate limiting
- Need sophisticated exit detection

**Example**: Full feature implementation, migrations, refactoring

### When to Use Programmatic Framework (ralph-loop-agent)

**Use when:**
- Building custom agent systems
- Need explicit context management
- Want programmatic verification
- Multiple stop conditions (tokens, cost)
- TypeScript/JavaScript codebase

**Example**: Custom tooling, agent orchestration, complex workflows

### When to Use Tmux Orchestration

**Use when:**
- Multiple projects simultaneously
- Need 24/7 autonomous operation
- Complex multi-agent coordination
- Want human oversight without constant monitoring
- Need session recovery after crashes

**Example**: Managing multiple codebases, team coordination, long-running projects

### When to Use Stop-Hook Verification

**Use when:**
- Using Claude Code
- Want automatic verification gates
- Need to prevent premature completion
- Can express verification as shell commands

**Example**: Test-driven development, quality gates, deployment checks

### When to Use Two-Phase Workflow

**Use when:**
- Complex projects requiring planning
- Want clean separation of concerns
- Planning artifacts would bloat execution context
- Need to generate detailed specs first

**Example**: New feature development, architecture changes, large refactors

### When to Use PRD → Task Queue

**Use when:**
- Have existing PRD/specifications
- Want deterministic task tracking
- Need clear completion criteria
- Prefer structured user stories

**Example**: Product development, feature implementation from specs

### When to Use Subagents

**Use when:**
- Main agent context is degrading
- Need expensive exploration/reasoning
- Want independent verification
- Complex multi-step workflows

**Example**: Code review, architecture planning, complex debugging

---

## Conclusion

Long-running AI agents require:

1. **Simple loops** with clear exit conditions
2. **State persistence** via disk (git, files, task lists)
3. **Backpressure mechanisms** (tests, lint, typecheck, verification)
4. **Context management** (fresh per iteration OR explicit budgets)
5. **Multi-agent coordination** (hub-and-spoke, clear roles)
6. **Monitoring & recovery** (session state, circuit breakers, health checks)
7. **Verification patterns** (tests-first, stop-hooks, judge agents)
8. **Error detection** (two-stage filtering, stuck loop detection)
9. **Workflow separation** (planning vs execution, two-phase patterns)

### The Core Philosophy

**"You're not writing the software, you're programming the loop"**

Your role shifts from:
- ❌ Direct implementation
- ✅ Loop engineering
- ✅ Constraint design
- ✅ Failure pattern observation
- ✅ Guardrail construction

**Success Formula:**
```
Success = Iteration + Verification + Constraints + Context Hygiene
```

### The Evolution Path

1. **Start Simple**: Basic bash loop with completion markers
2. **Add Verification**: Tests, typecheck, lint as gates
3. **Add Safety**: Circuit breakers, error detection, rate limiting
4. **Add Context Management**: Fresh iterations or explicit budgets
5. **Add Coordination**: Multi-agent patterns for complex projects
6. **Add Automation**: Hooks, scheduling, session recovery

### Key Takeaways

- **"Ralph is a Bash loop"** - Keep the core simple
- **"Everything is a Ralph loop"** - Iterate until right
- **"One task per loop"** - Prevents drift
- **"Deterministically bad"** - Failures are patterns you can tune
- **"Disk is memory"** - Repo carries state between iterations
- **"Verification is non-negotiable"** - Always provide feedback mechanisms
- **"Avoid redlining"** - Stay in 40-60% context utilization
- **"Don't mix planning and execution"** - Keep phases separate

### Next Steps

1. **Choose your pattern** based on project needs (see Decision Framework above)
2. **Start with simple verification** (tests, typecheck)
3. **Add safety mechanisms** as you observe failure patterns
4. **Iterate on constraints** based on what you observe
5. **Document learnings** for future iterations

**Remember**: The loop is the product. Your job is to make it converge reliably.

---

## References

### Core Concepts
- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Everything is a Ralph Loop](https://ghuntley.com/loop/)
- [How to Build a Coding Agent](https://ghuntley.com/agent/)
- [Don't Waste Your Backpressure (Moss)](https://banay.me/dont-waste-your-backpressure/)

### Advanced Patterns
- [Ralph Wiggum Technique (Claude Fast)](https://claudefa.st/blog/guide/mechanics/ralph-wiggum-technique)
- [If You Are Redlining the LLM (Huntley)](https://ghuntley.com/redlining)
- [I Dream About AI Subagents (Huntley)](https://ghuntley.com/subagents/)
- [From Design Doc to Code: /specs (Huntley)](https://ghuntley.com/specs)
- [You Are Using Cursor AI Incorrectly: /stdlib (Huntley)](https://ghuntley.com/stdlib)

### Field Reports & Implementations
- [repomirror Field Report](https://github.com/repomirrorhq/repomirror/blob/main/repomirror.md)
- [snarktank Ralph (PRD Loop)](https://snarktank.github.io/ralph)
- [ralph-claude-code](https://github.com/frankbria/ralph-claude-code)
- [ralph-loop-agent](https://github.com/vercel-labs/ralph-loop-agent)
- [Tmux Orchestrator](docs/ralph-orchestrator-study/Tmux-Orchestrator/)

### Documentation
- [Claude Code Checkpointing](https://docs.claude.com/en/docs/claude-code/checkpointing)
- [Claude Code Hooks Guide](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [RULER Paper (Context Window Research)](https://arxiv.org/abs/2404.06654)
