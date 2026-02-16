# Ralph Loop / Ralph Wiggum Methodology Reference

> "That's the beauty of Ralph - the technique is deterministically bad in an undeterministic world."
> — Geoffrey Huntley, Creator

## Overview

The Ralph Wiggum technique (or "Ralph Loop") is an iterative AI agent pattern where an LLM repeatedly processes a task, incorporating its prior outputs—including errors and failures—until predefined completion criteria are satisfied.

**Origin:** May 2025, created by Geoffrey Huntley (Australian developer, former Canva tech lead, now at Sourcegraph)

**Named after:** Ralph Wiggum from The Simpsons - the pattern is "elegantly simple yet surprisingly powerful"

## Core Philosophy

### The Fundamental Insight

Progress doesn't persist in the LLM's context window — it lives in your **files and git history**. Each iteration gets a fresh context window but reads the accumulated state from disk.

```
                    ┌─────────────────────────────────────┐
                    │         EXTERNAL MEMORY             │
                    │  (files, git history, state.json)   │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
     ┌──────────────│         FRESH LLM CONTEXT          │◄───────────┐
     │              │      (clean each iteration)         │            │
     │              └────────────────┬────────────────────┘            │
     │                               │                                  │
     │              ┌────────────────▼────────────────────┐            │
     │              │           EXECUTE TASK              │            │
     │              │   (read state, make changes)        │            │
     │              └────────────────┬────────────────────┘            │
     │                               │                                  │
     │              ┌────────────────▼────────────────────┐            │
     │              │         WRITE RESULTS               │            │
     │              │   (update files, commit git)        │            │
     │              └────────────────┬────────────────────┘            │
     │                               │                                  │
     │              ┌────────────────▼────────────────────┐            │
     │              │      CHECK COMPLETION               │────────────┘
     │              │   (verify against criteria)         │   NOT DONE
     │              └────────────────┬────────────────────┘
     │                               │ DONE
     │              ┌────────────────▼────────────────────┐
     └──────────────│            EXIT                     │
        REPEAT      │   (output final results)           │
                    └─────────────────────────────────────┘
```

### Key Principles

1. **Fresh Context Each Iteration** - No contamination from previous failures
2. **State Lives in Files** - Git history, JSON files, and logs persist between runs
3. **Completion Promise** - Clear, measurable definition of "done"
4. **Circuit Breakers** - Prevent infinite loops and runaway costs
5. **Human Feedback Loops** - Tests, linters, and validation as reinforcement

## Core Architecture

### The Original 5-Line Ralph Loop (Bash)

```bash
#!/bin/bash
# The original Ralph Wiggum loop
while true; do
    claude-code --prompt "$(cat PROMPT.md)" --continue
    if grep -q "EXIT_SIGNAL: true" response.json; then break; fi
done
```

### Production Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                             │
│  - Manages iteration count                                       │
│  - Enforces rate limits                                          │
│  - Triggers circuit breakers                                     │
│  - Evaluates completion criteria                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌───────────────────┐
│   GENERATOR   │     │    EVALUATOR    │     │     IMPROVER      │
│ Executes task │────▶│ Scores output   │────▶│ Proposes changes  │
│ with current  │     │ against rubric  │     │ based on failures │
│ prompt/config │     │                 │     │                   │
└───────────────┘     └─────────────────┘     └───────────────────┘
```

### Required Files Structure

```
project/
├── PROMPT.md           # Task instructions (read each iteration)
├── state.json          # Progress tracking, scores, iteration count
├── learnings.txt       # Append-only log of what worked/failed
├── logs/               # Execution logs per iteration
│   ├── iteration_001.log
│   ├── iteration_002.log
│   └── ...
└── output/             # Generated artifacts
```

## Completion Detection

### The Dual-Gate Pattern (frankbria/ralph-claude-code)

Exit requires BOTH conditions:
1. `completion_indicators >= 2` (heuristic patterns)
2. Explicit `EXIT_SIGNAL: true` from the agent

**Why dual-gate?** Prevents false positives where the agent reports finishing one phase while beginning another.

### Completion Indicators (Heuristics)

```python
COMPLETION_PATTERNS = [
    r"complete",
    r"finished",
    r"ready for review",
    r"all (tasks|items|tests) pass",
    r"done",
    r"EXIT_SIGNAL:\s*true"
]
```

### Verification Functions

```python
def verify_completion(state: dict) -> bool:
    """
    Check if all success criteria are met.
    Returns True only when genuinely complete.
    """
    scores = state.get("scores", {})
    thresholds = state.get("thresholds", {})

    for criterion, threshold in thresholds.items():
        if scores.get(criterion, 0) < threshold:
            return False

    return state.get("exit_signal", False)
```

## Circuit Breakers & Safety

### Rate Limiting

```python
RATE_LIMITS = {
    "max_iterations": 50,          # Hard stop
    "max_calls_per_hour": 100,     # API cost control
    "max_consecutive_failures": 5,  # Stuck detection
    "max_no_progress_loops": 3,     # Spin detection
}
```

### Circuit Breaker Triggers

1. **No File Changes** - 3 loops with identical file state
2. **Consecutive Errors** - 5 identical error messages
3. **API Limits** - Rate limit or budget exceeded
4. **Timeout** - Single iteration exceeds time limit

### Recovery Strategy

```python
def on_circuit_break(state: dict, reason: str):
    """Handle circuit breaker activation"""
    # 1. Log the failure
    log_failure(state, reason)

    # 2. Save state for debugging
    save_checkpoint(state)

    # 3. Options:
    #    a) Exit and alert human
    #    b) Wait and retry (half-open state)
    #    c) Spawn fresh context with reduced scope
```

## Context Window Management

### The "Gutter Ball" Problem

From Huntley's "autoregressive queens of failure":
> "If the bowling ball is in the gutter, there's no saving it."

**Solution:** Fresh context for each task. Don't try to fix a contaminated context.

### Anti-Patterns to Avoid

1. **Context Saturation** - Pushing context to maximum capacity ("redlining")
2. **Multi-Task Windows** - Mixing unrelated operations in one context
3. **Excessive Tools** - Registering too many MCPs degrades performance
4. **Memory Accumulation** - Irrelevant data from previous searches

### Best Practices

```python
# GOOD: Fresh context per iteration
for iteration in range(max_iterations):
    with fresh_context() as ctx:
        result = ctx.execute(task, state)
        state = update_state(state, result)

# BAD: Reusing contaminated context
ctx = create_context()
for iteration in range(max_iterations):
    result = ctx.execute(task, state)  # Context degrades each loop
```

## Subagent Architecture (Advanced)

### Hierarchical Decomposition

For complex tasks, spawn child agents with their own context windows:

```
┌─────────────────────────────────────┐
│         ORCHESTRATOR AGENT          │
│  (manages overall task, delegates)  │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Sub-   │ │ Sub-   │ │ Sub-   │
│ Agent  │ │ Agent  │ │ Agent  │
│   A    │ │   B    │ │   C    │
└────────┘ └────────┘ └────────┘
```

### When to Use Subagents

- Task requires multiple distinct skills
- Single context would exceed quality threshold (~147k tokens)
- Need to parallelize independent work
- Want to isolate failure domains

## Implementation Patterns

### Pattern 1: Simple Bash Loop

```bash
#!/bin/bash
MAX_ITER=50
ITER=0

while [ $ITER -lt $MAX_ITER ]; do
    ITER=$((ITER + 1))
    echo "=== Iteration $ITER ===" | tee -a logs/ralph.log

    # Execute with fresh context
    claude-code "$(cat PROMPT.md)" > output/iter_${ITER}.json 2>&1

    # Check for completion
    if jq -e '.exit_signal == true' output/iter_${ITER}.json > /dev/null; then
        echo "COMPLETE at iteration $ITER"
        break
    fi

    # Check for stuck loop (no changes)
    if [ $ITER -gt 1 ]; then
        if diff -q output/iter_$((ITER-1)).json output/iter_${ITER}.json > /dev/null; then
            echo "WARNING: No progress detected"
            STUCK=$((STUCK + 1))
            [ $STUCK -ge 3 ] && { echo "CIRCUIT BREAK: Stuck loop"; exit 1; }
        else
            STUCK=0
        fi
    fi
done
```

### Pattern 2: Python with Evaluation

```python
import json
from pathlib import Path
from typing import Callable

class RalphLoop:
    def __init__(
        self,
        generator: Callable,
        evaluator: Callable,
        improver: Callable,
        max_iterations: int = 50,
        state_file: Path = Path("state.json")
    ):
        self.generator = generator
        self.evaluator = evaluator
        self.improver = improver
        self.max_iterations = max_iterations
        self.state_file = state_file

    def load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"iteration": 0, "scores": {}, "history": []}

    def save_state(self, state: dict):
        self.state_file.write_text(json.dumps(state, indent=2))

    def run(self) -> dict:
        state = self.load_state()

        while state["iteration"] < self.max_iterations:
            state["iteration"] += 1
            print(f"\n{'='*60}")
            print(f"ITERATION {state['iteration']}")
            print('='*60)

            # 1. Generate output with fresh context
            output = self.generator(state)

            # 2. Evaluate against criteria
            scores, feedback = self.evaluator(output, state)
            state["scores"] = scores
            state["history"].append({
                "iteration": state["iteration"],
                "scores": scores,
                "feedback": feedback
            })

            # 3. Check completion
            if self.is_complete(scores):
                print("COMPLETION CRITERIA MET!")
                state["exit_signal"] = True
                break

            # 4. Generate improvements
            improvements = self.improver(feedback, state)
            state["pending_improvements"] = improvements

            # 5. Save state for next iteration
            self.save_state(state)

        return state

    def is_complete(self, scores: dict) -> bool:
        thresholds = {
            "naturalness": 8,
            "warmth": 8,
            "humor": 7,
            "flow": 8,
            "consistency": 8
        }
        return all(scores.get(k, 0) >= v for k, v in thresholds.items())
```

### Pattern 3: Task Queue (PRD-Based)

From snarktank/ralph:

```python
# prd.json structure
{
    "stories": [
        {"id": 1, "description": "...", "passes": false},
        {"id": 2, "description": "...", "passes": false},
        {"id": 3, "description": "...", "passes": true}
    ]
}

def select_next_task(prd: dict) -> dict:
    """Select highest-priority incomplete story"""
    for story in prd["stories"]:
        if not story["passes"]:
            return story
    return None  # All complete

def mark_complete(prd: dict, story_id: int):
    """Mark story as passing after verification"""
    for story in prd["stories"]:
        if story["id"] == story_id:
            story["passes"] = True
            break
```

## Real-World Results

### Notable Successes

1. **Cursed Programming Language** - Huntley ran a loop for 3 months, producing a complete language with compiler, stdlib, and editor support

2. **$50K Contract for $297** - Developer completed a complex contract using Ralph Loop, arbitraging human rates vs. API costs

3. **Flexbox Implementation** - Complete CSS flexbox layout algorithm in 3 hours (vs. 2 weeks manually in 2015)

## References

### Primary Sources

- [ghuntley.com/agent](https://ghuntley.com/agent/) - "How to Build a Coding Agent" workshop
- [ghuntley.com/gutter](https://ghuntley.com/gutter/) - Context window management
- [ghuntley.com/subagents](https://ghuntley.com/subagents/) - Hierarchical agent design

### Community Implementations

- [github.com/frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) - Full-featured Claude Code integration
- [github.com/snarktank/ralph](https://github.com/snarktank/ralph) - PRD-based task queue approach
- [github.com/vercel-labs/ralph-loop-agent](https://github.com/vercel-labs/ralph-loop-agent) - Vercel AI SDK integration

### Articles

- [VentureBeat: How Ralph Wiggum went from The Simpsons to AI](https://venturebeat.com/technology/how-ralph-wiggum-went-from-the-simpsons-to-the-biggest-name-in-ai-right-now)
- [DEV.to: 2026 - The year of the Ralph Loop Agent](https://dev.to/alexandergekov/2026-the-year-of-the-ralph-loop-agent-1gkj)
- [Alibaba Cloud: From ReAct to Ralph Loop](https://www.alibabacloud.com/blog/from-react-to-ralph-loop-a-continuous-iteration-paradigm-for-ai-agents_602799)

---

*Last updated: 2026-01-19*
