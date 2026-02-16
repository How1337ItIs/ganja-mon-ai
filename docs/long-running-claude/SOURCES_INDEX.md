# Long-Running Claude — Sources Index

Index of external sources for Ralph loops, long-running agents, and Claude Code harness. Full snapshots live in **larp-protocol** `docs/long-running-claude/sources/` (one file per source).

## Claude Code official (hooks / automation)

- **claude-code-hooks.md** — Hook lifecycle, events, I/O, decision control
- **claude-code-hooks-guide.md** — Examples: formatting, file protection
- **claude-code-cli-reference.md** — `--continue`/`--resume`, print mode, budgets, subagents
- **claude-code-settings.md** — Settings scopes, hooks config locations, env vars
- **claude-code-checkpointing.md** — Rewind/checkpoints limitations
- **claude-code-headless-agent-sdk.md** — `claude -p` programmatic usage, structured output
- **claude-code-subagents.md** — Subagents: scope, permissions, hooks
- **claude-code-mcp.md** — MCP servers, scopes, tool search
- **claude-agent-sdk-todo-tracking.md** — SDK todo tracking as task ledger

## Ralph loop implementations (community)

- **ralph-claude-code-frankbria.md** — Bash orchestrator, state files, circuit breaker, exit detection
- **snarktank-ralph-prd-loop.md** — PRD → task queue loop
- **vercel-ralph-loop-agent.md** — Programmatic loop, context budgets, judge pattern
- **repomirror-while-loop-field-report.md** — YC hackathon: “agent in a while loop”

## Context / failure modes (Huntley & others)

- **ghuntley-how-to-build-a-coding-agent.md** — “agent = loop + tools”, harness prompts
- **ghuntley-gutter-context.md** — Single-task contexts; “gutter ball” failure
- **ghuntley-subagents.md** — Subagents as “swap space” to avoid main-context death spiral
- **claudefast-ralph-wiggum-technique.md** — Stop hooks, completion promises, verification
- **ghuntley-ralph-wiggum.md** — Minimal Ralph (fresh context + disk state)
- **ghuntley-everything-is-a-ralph-loop.md** — “Monolithic, one task per loop”
- **ghuntley-redlining.md** — Real vs advertised context window; tool-loop failure near limit
- **moss-backpressure.md** — Backpressure for long-horizon convergence
- **ghuntley-backpressure.md** — Huntley framing + pre-commit as backpressure
- **ghuntley-stdlib.md** — /stdlib: underspecification + “program outcomes”
- **ghuntley-specs.md** — /specs: specs + compiler feedback

## Cloned repos (larp-protocol `docs/long-running-claude/repos/`)

- **repomirror** — Harness + prompts for “sync-forever” loops
- **ralph-claude-code** — Frank Bria’s Bash orchestrator
- **ralph-loop-agent** — Vercel Labs programmatic loop
- **ralph** — Snarktank PRD/task-queue loop
- **how-to-ralph-wiggum** — Community playbook
- **how-to-build-a-coding-agent** — Huntley workshop repo
- **loom** — Huntley “Weaving Loom” (research)
- **cursed** — Huntley long-running loop artifact (compiler + specs)
- **ralph-orchestrator** — mikeyobrien Rust orchestrator (hats, worktrees)

## Primary URLs

- [ghuntley.com/ralph](https://ghuntley.com/ralph/)
- [ghuntley.com/loop](https://ghuntley.com/loop/)
- [ghuntley.com/agent](https://ghuntley.com/agent/)
- [github.com/mikeyobrien/ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)
- [github.com/frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code)
- [github.com/vercel-labs/ralph-loop-agent](https://github.com/vercel-labs/ralph-loop-agent)
