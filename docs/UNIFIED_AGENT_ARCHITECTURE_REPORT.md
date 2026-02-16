# Grok & Mon: Unified Agent Architecture Report

**Date:** 2026-02-09  
**Scope:** How the system functions as a single “unified agent” (grow + trading + social + API), where unification succeeds, and where it falls short.

---

## 1. Executive Summary

Grok & Mon is designed as **one agent** (Mon) that tends the plant, trades, posts, and communicates. Unification is achieved through **shared context**, **cross-system control**, **a shared task list**, and **unified narrative output**—not through a single process or a single LLM. The architecture is more cohesive than a naive “four subprocesses” view suggests: one brain (the grow orchestrator’s Grok) receives full situational awareness; trading can trigger grow AI; social posts blend plant, trading, and $MON in one voice; and a single task list drives both the grow brain and the engagement daemon. Gaps remain: two codebases/processes, two decision loops, and no shared episodic memory.

---

## 2. Runtime and Process Layout

| Component        | Process        | Entry / Role |
|-----------------|----------------|--------------|
| FastAPI server  | Subprocess     | REST + WebSocket, health, grow/trading APIs |
| Orchestrator    | Main process   | Sensor polling, Grok AI decisions, hardware |
| Social daemon   | Subprocess     | Engagement loops, task execution, posting |
| Trading agent   | Subprocess     | GanjaMon in `cloned-repos/ganjamon-agent/` |

- **Single launcher:** `python3 run.py all` starts all four; on Chromebook, one systemd unit (`grokmon.service`) runs them with a crash watchdog that respawns social and trading.
- **Communication:** File-based (JSON/JSONL under `data/`, trading under `cloned-repos/ganjamon-agent/data/`) and HTTP (trading → FastAPI for plant snapshot and control).

---

## 3. Where Unification Is Achieved

### 3.1 Single “Cross-System Awareness” Into One Brain

The **grow orchestrator** is the only component that calls Grok for **grow** decisions. Every decision cycle, it builds a **unified context** string and injects it into the same prompt that decides watering, lights, and environment.

**Unified context includes:**

- **Trading:** Portfolio, PnL, research cycles, domains, signals, paper vs live.
- **Social:** Posts per channel (24h), replies, Farcaster metrics, engagement health.
- **Email:** Sent/limit, inbox/outbox, follow-ups; prompt tells the brain to use `queue_email` when needed.
- **Community:** Trade suggestions from Telegram (username, type, token, chain, text).
- **Agent tasks:** Pending todos from `data/agent_tasks.json` with priority and `tool_hint`; explicit “ACT ON THESE” and instructions to use `queue_email` or `log_observation` (and urgency for critical/hackathon tasks).
- **Historical review:** External review agent output (e.g. `data/historical_review.json`).
- **Agent lore:** Short narrative snippets for personality.

**Implementation:** `src/brain/unified_context.py` → `UnifiedContextAggregator.format_unified_context()`; called from `src/orchestrator.py` before `brain.decide()`.

So **one decision loop** (grow) has **full situational awareness** across trading, social, email, community, and tasks. That is a deliberate unification of **context** into one brain.

### 3.2 Trading → Grow: Control, Not Just Read

The trading agent does not only **read** plant state:

- **GrokMonClient** (`cloned-repos/ganjamon-agent/src/clients/grokmon.py`) exposes:
  - `fetch_snapshot()` — stage, AI latest, sensors, plant progress.
  - `trigger_ai_decision()` — POST `/api/ai/trigger` to force an immediate grow decision cycle.
  - `set_schedule()`, `advance_day()` — photoperiod and grow-day control.

- **PlantMaster** (`cloned-repos/ganjamon-agent/src/intelligence/plant_master.py`) runs in the trading process and:
  - Fetches plant status on an interval.
  - Correlates with trading (e.g. recent profits). If profits are high and plant health is not “good,” it calls **`await self.client.trigger_ai_decision()`** so the grow side runs an extra AI cycle.

So there is a real **trading → grow** action path: trading can request more grow attention when it “matters” (e.g. after good PnL).

### 3.3 Shared Task List: One Todo, Two Executors

- **`data/agent_tasks.json`** is the shared task list (priority, title, description, `tool_hint`).
- **Grow brain** sees these in unified context and is instructed to act via `queue_email` or `log_observation` (and to prioritize critical/hackathon tasks).
- **Engagement daemon** (`src/social/engagement_daemon.py`) reads the same file and runs a **task-exec** loop: e.g. post to Moltbook, queue Telegram message, defer `queue_email` tasks to the mailer, run subagent for research tasks.

So **one task list** drives both the grow brain (via tools) and the engagement daemon (via task execution). That unifies **work** across subsystems.

### 3.4 Grow Brain Can Drive Email

- The grow brain has a **`queue_email`** tool (`src/ai/tools.py`) that calls the mailer. So **grow → email** is wired.
- Unified context describes email state and tells the brain to use `queue_email` for outreach and tasks. One brain can initiate outbound communication on behalf of the agent.

### 3.5 Social Output Is Explicitly Multi-Domain

- **SocialBroadcaster** (in the trading agent) is given **`get_plant_snapshot`** and uses it in every short and long post.
- Short-cycle rotation is **`["trading", "mon", "plant", "introspection"]`** — plant is a first-class dimension.
- Long “GanjaMon Ops Report” is one document: **Trading activity (alpha-safe) + $MON focus + Mon the plant** (stage, day, latest Grok note). One narrative, one voice (Rasta), one report.

So **social output** is deliberately unified: trading + token + grow in a single post, not separate channels.

### 3.6 Single Identity (Mon) Across Domains

- **PlantMaster** is documented as the “Master Agent” overseeing both markets and the physical plant.
- Trading persona and social copy use plant snapshot so they can say “Mon is in veg, day 42” and “Grok stays on it.” One character (Mon) is maintained across grow, trading, and social, even though the codebases are separate.

---

## 4. Where Unification Falls Short

### 4.1 Separate Processes and Codebases

- Four OS processes; no shared in-process state. Coordination is via files and HTTP.
- Trading agent lives in **`cloned-repos/ganjamon-agent/`** with its own `PYTHONPATH` and entrypoint (`python -m main`). So “unified” is at the **orchestration** level (one `run.py all`, one service), not at the **module** level.

### 4.2 Two Decision “Brains”

- **Grow:** `src/ai/brain.py` (Grok) in the orchestrator — watering, lights, environment, tools.
- **Trading:** Inside `ganjamon-agent` — its own loops, signals, execution, risk.

There is **no single LLM call** that can both “water the plant” and “take this trade.” Two decision loops each get **context** about the other but do not share one policy or one reasoning pass.

### 4.3 Context Flow Is Asymmetric

- **Grow → trading:** Trading **pulls** plant snapshot from the API on an interval. Grow does not push.
- **Trading/social → grow:** Grow **reads** their output from disk (unified context). Trading and social do not receive a structured feed of grow decisions or a shared “agent state”; they write, grow reads.

So there is no single, bidirectional “agent state” that all subsystems read and write.

### 4.4 Episodic Memory Is Grow-Side Only

- **Episodic memory** (`src/brain/memory.py`, persisted to `data/episodic_memory.json`) is used by the orchestrator (and legacy agent). It stores grow events (conditions, watering, observations).
- The trading agent has its own memory/observation journal. There is **no shared** episodic store that both “watered today” and “closed a trade today” write into for one agent narrative.

### 4.5 Social as Output-Only in the Loop

- The engagement daemon **writes** files the grow brain reads (engagement log, state). It **reads** the shared task list and executes by hint.
- It does **not** receive explicit “today’s theme” or “emphasize $MON” directives from the grow brain or trading; it composes from status, plant snapshot, and task hints. So social is an output arm fed by shared state and tasks, not an equal participant in one shared decision step.

### 4.6 log_observation and “Social Pickup”

- Unified context tells the grow brain: “If a task needs a social post, describe it in log_observation so the engagement daemon picks it up.”
- ~~The **grow** `log_observation` tool (`src/ai/tools.py`) was a stub~~ **FIXED (2026-02-09)**: Now persists to `EpisodicMemory` DB + writes to shared event log (`data/unified_event_log.jsonl`).
- ~~The engagement daemon couldn't read observations~~ **FIXED**: Engagement daemon reads `_get_event_log_context()` from the shared event log and injects it into social post generation.
- ~~The prompt told the brain to "describe in log_observation so engagement picks it up"~~ **FIXED**: Prompt now tells the brain to use `create_task` with appropriate `tool_hint` values.

---

## 5. Summary Table

| Dimension            | Unified? | Mechanism |
|----------------------|----------|-----------|
| Context into one brain | Yes     | UnifiedContextAggregator → grow Grok prompt |
| Trading → grow action | Yes     | PlantMaster + GrokMonClient.trigger_ai_decision() |
| Shared task list      | Yes     | agent_tasks.json → grow tools + engagement task-exec |
| Dynamic task creation | Yes     | `create_task` tool → agent_tasks.json → engagement daemon |
| Grow → email          | Yes     | queue_email tool + mailer |
| Social narrative      | Yes     | SocialBroadcaster with plant_snapshot, one report |
| Shared event log      | Yes     | unified_event_log.jsonl — grow, trading, social all write/read |
| Observation persistence | Yes   | log_observation → EpisodicMemory DB + event log |
| Single process        | No      | Four processes (intentional — safety/isolation) |
| Single codebase       | No      | sol-cannabis src/ + ganjamon-agent (intentional) |
| Single decision loop  | No      | Grow Grok vs trading's own loops (intentional — domain safety) |

---

## 6. What "Unified Agent" Means (Documented Contract)

**Mon is one agent** experienced through multiple processes. The unification contract is:

1. **One context blob** — UnifiedContextAggregator gathers all subsystem state into one prompt
2. **One shared event log** — `data/unified_event_log.jsonl` provides a "Mon's Day" narrative across grow, trading, and social
3. **One task list** — `data/agent_tasks.json` drives both grow brain (via tools) and engagement daemon (via task-exec)
4. **Dynamic task creation** — The grow brain can create tasks (`create_task` tool) for the engagement daemon to execute
5. **Trading → grow control** — PlantMaster can trigger AI decisions and adjust schedules
6. **Grow → email** — `queue_email` tool drives outbound communication
7. **Unified social voice** — All platforms use Rasta personality with grow+trading+token context

**Two processes and two brains are intentional** for safety and separation of concerns:
- Grow decisions must never be blocked by trading failures
- Trading risk management must be independent of grow loops
- Social posting should survive either subsystem crashing

---

## 7. Remaining Gaps (Accepted)

- **No shared episodic memory** — Grow has hippocampus-style memory; trading has its own journal. The shared event log bridges this but doesn't replace per-domain memory.
- **Context flow is still mostly read-only** — Trading reads grow API; grow reads trading files. The event log adds a bidirectional narrative but not bidirectional control.
- **Agent tasks are mostly human-authored** — The `create_task` tool enables dynamic creation, but the initial task list is still manually seeded.

These are acceptable trade-offs for a system that prioritizes reliability and safety over tight coupling.

---

*Report generated from codebase review. Updated 2026-02-09 after fixing broken paths (log_observation, create_task, shared event log).*
