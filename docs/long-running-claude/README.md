# Long-Running Claude & Ralph Loops (Consolidated Reference)

This folder consolidates **Ralph loops**, **long-running agents**, and **Claude Code** autonomy docs copied from repos under `C:\Users\natha`, so sol-cannabis has a single reference set.

## What's in here

| Doc | Source repo | Description |
|-----|-------------|-------------|
| **LONG_RUNNING_AGENTS_STUDY.md** | larp-protocol | Deep study: Ralph patterns, Tmux orchestration, exit conditions, context, verification, hooks |
| **RALPH_HORDE_SWARM_RESEARCH.md** | larp-protocol | Multi-Ralph coordination: ralph-orchestrator, workmux, multi-agent-workflow-kit |
| **RALPH_QUICKSTART.md** | larp-protocol | Quick start for running Ralph (LARP-style .ralph loop) |
| **RALPH_HANDOFF.md** | larp-protocol | Handoff/babysitter guide: monitoring, circuit breaker, EXIT_SIGNAL |
| **RALPH_WIGGUM_VIDEO_SUMMARY.md** | deadhead-llm | Huntley/Horthy video: "Jeff Recipe", context as array, YOLO mode, infra isolation |
| **GRU_RALPH_REFERENCE.md** | gru | Gru CLI ralph commands, completion promises, monitoring |
| **SOURCES_INDEX.md** | (this repo) | Index of external sources (hooks, Ralph implementations, context engineering) |

## Other sol-cannabis Ralph / long-running docs

- **Main entry:** `docs/RALPH_LOOPS_AND_LONG_RUNNING_CLAUDE.md` — Short reference + links
- **Plugin scripts:** `docs/ralph-loop/` — Claude Code ralph-loop plugin (README, setup, stop-hook, commands)
- **Rasta voice:** `rasta-voice/docs/RALPH_LOOP_REFERENCE.md`, `rasta-voice/ralph_learnings.md` — Voice/persona loop learnings
- **Website:** `website-ralph-loop/docs/RALPH_RESEARCH.md` — Ralph research summary

## External repos (under ~/natha) that have more

- **larp-protocol** — `.ralph/`, `docs/long-running-claude/sources/` (20+ source snapshots), `docs/ralph-orchestrator-study/`, Tmux-Orchestrator
- **.gemini/antigravity** — `knowledge/agentic_autonomous_patterns_and_research/artifacts/` (ralph_orchestrator_v2_specification, meta_ralph_loop_specification)
- **.cursor / .claude** — `plugins/marketplaces/claude-plugins-official/plugins/ralph-loop/` (live plugin)

## Why this exists

Web pages and repos move. This copy gives sol-cannabis a **local, versioned** reference for:

- Externalizing memory into files/state
- Verification gates (tests, judges, stop-hooks)
- Circuit breakers and iteration limits
- Context hygiene (fresh runs, 40–60% utilization, one task per loop)

For full source snapshots (e.g. ghuntley-ralph-wiggum, claude-code-hooks), see **larp-protocol** `docs/long-running-claude/sources/`.
