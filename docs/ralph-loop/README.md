# Ralph Loop Plugin (Reference Copy)

Implementation of the Ralph Wiggum technique for iterative, self-referential AI development loops in Claude Code.

**Source:** Claude/Cursor plugin marketplace (`claude-plugins-official/ralph-loop`). This is a reference copy for use in this repo.

## What is Ralph Loop?

Ralph Loop is a development methodology based on continuous AI agent loops. As Geoffrey Huntley describes it: **"Ralph is a Bash loop"** - a simple `while true` that repeatedly feeds an AI agent a prompt file, allowing it to iteratively improve its work until completion.

This technique is inspired by the Ralph Wiggum coding technique (named after the character from The Simpsons), embodying the philosophy of persistent iteration despite setbacks.

### Core Concept

This plugin implements Ralph using a **Stop hook** that intercepts Claude's exit attempts:

```bash
# You run ONCE:
/ralph-loop "Your task description" --completion-promise "DONE"

# Then Claude Code automatically:
# 1. Works on the task
# 2. Tries to exit
# 3. Stop hook blocks exit
# 4. Stop hook feeds the SAME prompt back
# 5. Repeat until completion
```

The loop happens **inside your current session** - you don't need external bash loops. The Stop hook in `stop-hook.sh` creates the self-referential feedback loop by blocking normal session exit.

## Commands

- **/ralph-loop** — Start a Ralph loop: `/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"`
- **/cancel-ralph** — Cancel the active Ralph loop (removes `.claude/ralph-loop.local.md`).

## Files in This Reference

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `setup-ralph-loop.sh` | Creates `.claude/ralph-loop.local.md` state file |
| `stop-hook.sh` | Stop hook: blocks exit, feeds prompt back |
| `commands/` | Slash-command definitions (ralph-loop, cancel-ralph, help) |
| `plugin.json` | Plugin metadata |
| `hooks.json` | Hook registration (Stop → stop-hook.sh) |

## Learn More

- Main doc in this repo: `docs/RALPH_LOOPS_AND_LONG_RUNNING_CLAUDE.md`
- Original technique: https://ghuntley.com/ralph/
- Ralph Orchestrator: https://github.com/mikeyobrien/ralph-orchestrator
