# Ralph Loops and Long-Running Claude

Reference for **Ralph Loop** (iterative AI development loops) and **long-running Claude** context tips. Sourced from the official Claude/Cursor ralph-loop plugin and automation recommender docs.

---

## Ralph Loop

### What Is Ralph Loop?

**Ralph Loop** implements the **Ralph Wiggum technique**: an iterative development methodology based on continuous AI agent loops, pioneered by Geoffrey Huntley. In his words: **"Ralph is a Bash loop"** — a `while true` that repeatedly feeds an AI agent a prompt file so it can iteratively improve until completion.

- **Origin:** [ghuntley.com/ralph/](https://ghuntley.com/ralph/)
- **Ralph Orchestrator:** [github.com/mikeyobrien/ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)

### How It Works (Claude Code Plugin)

The plugin uses a **Stop hook** that intercepts Claude’s exit:

1. You run once: `/ralph-loop "Your task" --completion-promise "DONE"`
2. Claude works on the task.
3. When Claude tries to exit, the stop hook runs.
4. The hook either allows exit (completion promise detected or max iterations) or **blocks** and feeds the **same prompt** back.
5. Claude sees its previous work in files and continues. Loop repeats until completion or limit.

The loop runs **inside one session**; no external bash loop is required. State is stored in `.claude/ralph-loop.local.md`.

### Commands (Claude Code)

| Command | Description |
|--------|-------------|
| `/ralph-loop "<prompt>" [OPTIONS]` | Start a Ralph loop in the current session. |
| `/cancel-ralph` | Cancel the active loop (removes `.claude/ralph-loop.local.md`). |

**Options:**

- `--max-iterations <n>` — Stop after N iterations (default: unlimited). **Always set a safety limit.**
- `--completion-promise "<text>"` — Phrase that signals completion (exact match inside `<promise>` tags).

**Examples:**

```bash
/ralph-loop "Refactor the cache layer" --max-iterations 20
/ralph-loop "Add tests" --completion-promise "TESTS COMPLETE"
/ralph-loop "Build a REST API for todos. CRUD, validation, tests. Output <promise>COMPLETE</promise> when done." --completion-promise "COMPLETE" --max-iterations 50
```

### Completion Promise

To finish the loop, Claude must output:

```html
<promise>YOUR_PHRASE</promise>
```

The stop hook looks for this tag. Without a completion promise (or `--max-iterations`), the loop can run indefinitely.

**Rule:** Only output the promise when the statement is **actually true**. Do not output a false promise to exit.

### Prompt Best Practices

1. **Clear completion criteria** — e.g. “All CRUD endpoints working, tests passing, output &lt;promise&gt;COMPLETE&lt;/promise&gt;.”
2. **Incremental goals** — Break into phases with testable steps.
3. **Self-correction** — e.g. “Follow TDD: write failing tests, implement, run tests, fix, repeat until green.”
4. **Escape hatch** — Use `--max-iterations` (e.g. 20) so impossible or stuck tasks don’t run forever.

### When to Use Ralph

**Good for:**

- Well-defined tasks with clear success criteria
- Iterative refinement (e.g. getting tests to pass)
- Greenfield work where you can let it run
- Tasks with automatic checks (tests, linters)

**Not good for:**

- Tasks needing human judgment or design decisions
- One-off operations
- Unclear success criteria
- Production debugging (prefer targeted debugging)

### Cursor vs Claude Code

- **Claude Code** has native ralph-loop plugin support (stop hook, same prompt re-fed).
- **Cursor** does not support long Ralph-style loops natively; there are workarounds (e.g. [cursor-ralph](https://github.com/hexsprite/cursor-ralph) on macOS using `osascript` to work around the 5-iteration stop hook limit).
- For long-running autonomous loops, Claude Code or tools like Aider are better suited than Cursor.

---

## Long-Running Claude / Context

### Memory and Context

For **long-running projects** and **multi-session work**:

- **Memory MCP** — Use for persistent context: “Remember context”, “User preferences”, “Learning patterns.” Lets Claude retain project context, decisions, and patterns across conversations.
- **Project rules and docs** — Keep `CLAUDE.md`, `.claude/rules/`, and key docs up to date so each session (and each Ralph iteration) has clear constraints and background.

### Hooks: Avoid Long-Running Logic

From the plugin-dev hook guidelines:

- **Do not** run long-running logic inside hooks (e.g. `sleep 120` or heavy work). Hooks should be fast or they can timeout and block the workflow.
- **Ralph’s stop hook** is fast: it reads state, checks transcript for `<promise>`, and either exits or returns a block + prompt. No heavy computation.

### Summary Table

| Topic | Recommendation |
|-------|-----------------|
| Ralph Loop | Use in Claude Code with `/ralph-loop`, always set `--max-iterations`, use `<promise>` for completion. |
| Long-running context | Use Memory MCP and good project docs/rules. |
| Hooks | Keep them short; no long-running operations. |
| Cursor long runs | Prefer Claude Code or Aider for overnight/autonomous Ralph-style loops. |

---

## GanjaMon Two-Loop Architecture (V2)

GanjaMon runs **two separate Ralph loops**, both calling Claude Code, with different cadences and budgets:

### Surgical Ralph (Triage Loop)

| Property | Value |
|----------|-------|
| **Fires** | Every 2-4 hours (cron or agent-triggered) |
| **Token budget** | Low (~50k per Claude call) |
| **Mission** | Keep the agent running — fix broken modules, missing keys, crashed imports |
| **Prompt** | `.ralph/PROMPT.md` — diagnosis-first, reads health_status.json |
| **Runner** | `.ralph/run-loop.sh` (standalone) or `.ralph/scheduled_ralph.sh` (cron) |
| **Code trigger** | `unified_brain.trigger_ralph_loop()` — fires on upgrade requests |
| **Circuit breaker** | Stops after 5 consecutive failures, exponential backoff |
| **Completion promise** | `<promise>RESEARCH COMPLETE</promise>` |

**Flow:** HealthMonitor detects failure → generates upgrade request → Surgical Ralph reads health_status.json → diagnoses → fixes → verifies compilation → marks deployed.

### Evolutionary Ralph (Growth Loop)

| Property | Value |
|----------|-------|
| **Fires** | Once per day (or on-demand) |
| **Token budget** | High (~200k per Claude call) |
| **Mission** | Make the agent smarter — implement research, distill lessons, adopt patterns |
| **Prompt** | `.ralph/EVOLUTIONARY_PROMPT.md` — reads experience DBs, research logs |
| **Runner** | `.ralph/evolutionary_loop.sh` |
| **Code trigger** | `unified_brain.trigger_evolutionary_ralph()` — daily, health-gated |
| **Pre-flight gate** | Skips if >30% components failing (let Surgical stabilize first) |
| **Completion promise** | `<promise>EVOLUTION COMPLETE</promise>` |

**Flow:** Agent accumulates experience/research → Evolutionary Ralph reads learning state → identifies highest-value capability expansion → implements from cloned-repos or novel → verifies → wires into brain/health/experience.

### How They Interact

```
                   ┌─────────────────┐
                   │  HealthMonitor   │
                   │  (always running)│
                   └────────┬────────┘
                            │ failures
                            ▼
               ┌────────────────────────┐
               │  data/health_status.json│
               │  data/upgrade_requests  │
               └──────┬─────────┬───────┘
                      │         │
            ┌─────────▼──┐  ┌──▼──────────┐
            │  Surgical   │  │ Evolutionary │
            │  Ralph      │  │ Ralph        │
            │  (2-4h)     │  │ (daily)      │
            │  Quick fixes│  │ Growth       │
            └─────────────┘  └──────────────┘
                      │         │
                      ▼         ▼
            Both call: claude --dangerously-skip-permissions --print
```

### Crontab Setup (Chromebook)

```crontab
# Surgical Ralph — every 4 hours
0 */4 * * * /home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent/.ralph/scheduled_ralph.sh

# Evolutionary Ralph — daily at 3am
0 3 * * * /home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent/.ralph/evolutionary_loop.sh
```

---

## Full Index: Ralph & Long-Running Claude in This Repo

Content copied from **larp-protocol**, **gru**, **deadhead-llm**, **.cursor/.claude** plugins, and sol-cannabis’s own subprojects.

### docs/long-running-claude/ (consolidated reference)

| Doc | Description |
|-----|-------------|
| **README.md** | Index of this folder and pointers to other repos |
| **LONG_RUNNING_AGENTS_STUDY.md** | Deep study: Ralph patterns, Tmux, exit conditions, context, verification, hooks (from larp-protocol) |
| **RALPH_HORDE_SWARM_RESEARCH.md** | Multi-Ralph: ralph-orchestrator, workmux, multi-agent-workflow-kit (from larp-protocol) |
| **RALPH_QUICKSTART.md** | Quick start for .ralph-style loop (from larp-protocol) |
| **RALPH_HANDOFF.md** | Babysitter/monitoring guide, circuit breaker, EXIT_SIGNAL (from larp-protocol) |
| **RALPH_WIGGUM_VIDEO_SUMMARY.md** | Huntley/Horthy video: “Jeff Recipe”, context as array, YOLO (from deadhead-llm) |
| **GRU_RALPH_REFERENCE.md** | Gru CLI ralph commands (from gru) |
| **SOURCES_INDEX.md** | Index of external sources (hooks, Ralph implementations, context engineering) |

### docs/ralph-loop/ (Claude Code plugin reference)

- **README** — Plugin overview.
- **Commands** — `ralph-loop`, `cancel-ralph`, `help`.
- **Scripts** — `setup-ralph-loop.sh`, `stop-hook.sh`.
- **Plugin metadata** — `plugin.json`, `hooks.json`.

### In this repo (other Ralph / long-running docs)

- **rasta-voice/docs/RALPH_LOOP_REFERENCE.md** — Ralph methodology for voice pipeline.
- **rasta-voice/ralph_learnings.md** — Persona/variety loop learnings.
- **website-ralph-loop/docs/RALPH_RESEARCH.md** — Ralph research summary.

### Other local repos (under ~/natha) with more

- **larp-protocol** — `docs/long-running-claude/sources/` (20+ source snapshots), `.ralph/`, ralph-orchestrator-study.
- **.gemini/antigravity** — `knowledge/.../artifacts/` (ralph_orchestrator_v2_specification, meta_ralph_loop_specification).
- **.cursor / .claude** — `plugins/.../ralph-loop/` (live Claude Code plugin).
