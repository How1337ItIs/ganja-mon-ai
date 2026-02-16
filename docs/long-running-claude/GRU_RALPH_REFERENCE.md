# Gru Ralph Loops Reference

> **Source:** gru repo `gru/docs/ralph.md`  
> Gru integrates Ralph Wiggum as CLI commands for autonomous, long-running development cycles.

## Philosophy

**Iteration > Perfection.** Ralph in Gru lets agents refine work over multiple attempts rather than aiming for one-shot perfection.

## Quick Start

```bash
# Basic usage
gru ralph "Build a REST API with user authentication"

# With completion detection
gru ralph "Add tests until coverage > 90%" --completion-promise "COVERAGE_MET"

# Custom iterations
gru ralph "Refactor this codebase" --max-iterations 30

# Named loop for tracking
gru ralph "Optimize performance" --name perf-optimizer
```

## How It Works

1. **Initial task** — Agent gets the task + Ralph loop instructions.
2. **Execution** — Works autonomously (no approval prompts).
3. **Iteration check** — On “complete”: if completion promise found → end; if max iterations → end; else spawn next iteration with context.
4. **Context preservation** — Next iteration gets summary of previous work.
5. **Progressive refinement** — Agent builds on prior attempts.

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-iterations` | Max iterations | 20 |
| `--completion-promise` | String that signals completion | None |
| `--name` | Custom loop name | ralph-[id] |
| `--model` | AI model | Default |
| `--priority` | high / normal / low | normal |

## Best Use Cases

**Ideal for:** Large refactors, test coverage, batch operations, greenfield with clear requirements, docs, code cleanup.

**Not for:** Production debugging, one-shot tasks, unclear success criteria, time-sensitive work.

## Completion Promises

Exact string matching. Agent must output the exact string (e.g. `TESTS_COMPLETE`), not a variation.

## Monitoring

```bash
gru status <agent-id>
gru logs <agent-id>
gru cancel-ralph <agent-id>
```

## Safety

- Iteration limits, cancellation, unsupervised-only execution, status tracking, cleanup on completion/cancel.
