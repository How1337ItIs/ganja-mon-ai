# Multi-Domain Agent Examples: What to Copy

**Purpose:** Curated examples across the domains we touch (orchestration, trading, social, IoT/grow, messaging, reliability) so we can copy patterns instead of inventing from scratch.

**Last updated:** 2026-02-08

---

## 1. Orchestration & Multi-Agent Coordination

### LangGraph (state graph, supervisor–worker)

- **What:** Graph-based multi-agent orchestration with typed state; only state deltas passed between nodes → lower tokens and latency (e.g. ~2.2x faster than CrewAI in some benchmarks).
- **Copy from:**
  - [LangGraph multi-agent supervisor tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/) — routing, handoffs.
  - [agent_supervisor.ipynb](https://github.com/langchain-ai/langgraph/blob/main/examples/multi_agent/agent_supervisor.ipynb) — runnable notebook.
  - [Multi-agent collaboration](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/) — network of specialists.
- **Use for:** Grow orchestrator ↔ trading/social workers; tool routing; explicit handoffs with schemas instead of free-form prose.

### SciAgent (unified multi-domain reasoning)

- **What:** Coordinator interprets domain/complexity and orchestrates worker systems (symbolic, conceptual, numerical, verification). Cross-domain (math, physics, chemistry).
- **Copy from:** [SciAgent paper (arXiv)](https://arxiv.org/html/2511.08151v1) — coordinator/worker decomposition and domain routing.
- **Use for:** Single “brain” that routes to grow vs trading vs social vs A2A based on intent and context.

### OmniNova (hierarchical automation)

- **What:** Coordinator / planner / supervisor / specialist layers; dynamic task routing by complexity; multi-layer LLM use. ~87% task completion across research, data, web.
- **Copy from:** [OmniNova (arXiv)](https://ar5iv.labs.arxiv.org/html/2503.20028) — hierarchy and routing patterns.
- **Use for:** Scaling beyond “one orchestrator + N workers” when we need planner vs executor separation.

### Supervisor–worker best practices (generic)

- **Do:** Separate context per worker, dynamic spawning by complexity, timeouts and failure handling, cache expensive ops, synthesize step with quality control.
- **Don’t:** Too many workers (diminishing returns after ~5–7), shared context between workers, skip synthesis QC. Token use can be ~15x; avoid for simple queries.
- **Copy from:** [Agentic Design – Supervisor and Workers](https://agentic-design.ai/patterns/multi-agent/supervisor-worker-pattern), [Skywork – Orchestration & Handoffs](https://skywork.ai/blog/ai-agent-orchestration-best-practices-handoffs/).

---

## 2. OpenClaw / Local-First Multi-Channel Agents

We already use OpenClaw; these are the patterns worth copying explicitly.

- **Gateway + WebSocket control plane:** Single control plane; all clients (CLI, web, headless) connect via WebSocket and declare role/scope at handshake. [Gateway Protocol](https://docs.clawd.bot/gateway/protocol).
- **Lane-based concurrency:** Main / Cron / Subagent / Nested queues with separate concurrency limits — avoids task starvation. Copy this for our “many background loops” (social, trading, grow).
- **Multichain messaging:** 29+ channels as plugins; treat platforms as interchangeable. Mirrors our Telegram + Discord + Twitter + etc.
- **Brain vs Gateway:** Brain = decision runtime; Gateway = transport/sessions. We already split “GrokBrain + API + workers” — align naming and responsibilities with this.
- **Copy from:**
  - [OpenClaw (Moltbot) guide 2026](https://sterlites.com/blog/moltbot-local-first-ai-agents-guide-2026)
  - [Building Clawdbot](https://www.mmntm.net/articles/building-clawdbot)
  - Local repo: `openclaw/` and `docs/OPENCLAW_FRAMEWORK_DEEP_DIVE.md`

---

## 3. Social & Personality (Character / Brand Voice)

### Eliza (ai16z)

- **What:** Character files (personality, platform-specific variants: all/chat/post), three loops per platform (posting, interaction, engagement), RAG memory (e.g. vector embeddings in PostgreSQL), 90+ plugins with Action/Provider/Evaluator/Service types.
- **Copy from:**
  - [elizaOS/eliza](https://github.com/elizaOS/eliza) — core framework.
  - [elizaOS/characterfile](https://github.com/elizaOS/characterfile) — character file format (JSON/TS).
  - [ElizaOS Characterfile docs](https://elizaos.github.io/eliza/docs/core/characterfile/).
- **Use for:** Rasta persona variants per platform; structured plugin types for social actions; engagement/post/interaction loop separation.

### GAME (Virtuals)

- **What:** Two-level planner: High-Level Planner (HLP) generates tasks, workers execute; workers are domain-specialized (e.g. trading, social); HLP sees personality every cycle.
- **Copy from:** Referenced in our `docs/AGENT_REDESIGN_FIRST_PRINCIPLES.md`; search for “GAME Virtuals” and “HLP” for architecture notes.
- **Use for:** Personality-in-the-loop for planner; social worker vs trading worker specialization.

---

## 4. Trading & Alpha Agents

(Already summarized in `AGENT_REDESIGN_FIRST_PRINCIPLES.md`; here as a copy list.)

- **Multi-agent deliberation:** Bull/bear debate pattern; multi-agent trading systems.
- **Signal quality:** Trust engines, scoring, validation layer (we have this in GanjaMon).
- **Regime detection:** HMM or similar for strategy adaptation (we have regime detection in learning).
- **Graduation path:** Backtest → paper → graduated live (see trading agent docs).
- **Memory:** Neo4j/vector stores for cross-session context (we use unified_context + JSON; consider vector store for semantic retrieval).
- **Copy from:** `cloned-repos/ganjamon-agent/`, `docs/GANJAMON_AGENT_ARCHITECTURE.md`, `docs/TRADING_ALPHA_AGENT_PATTERNS.md`.

---

## 5. Reliability & Production Agent Systems

### Olas / Autonolas

- **What:** FSM-based agent behavior (deterministic, auditable); composable FSM modules; distributed consensus for safety-critical ops. Powers a large share of Gnosis Chain Safe transactions.
- **Copy from:** Search “Olas Autonolas FSM agent” for whitepapers and repos.
- **Use for:** Watering/safety critical paths (e.g. dark period, kill switch) as explicit FSMs; auditability.

### General production patterns

- **Supervision trees:** Restart strategies, health monitoring (we have watchdog + supervisor in `src/core/`).
- **Circuit breakers:** On every external dependency (we have in `src/core/`).
- **Graceful degradation:** Full → Reduced → Core → Safe → Emergency tiers.
- **Event sourcing / WAL:** Crash recovery (we use SQLite WAL; ensure event bus or critical state is durable).
- **Copy from:** [Skywork – Orchestration & Handoffs](https://skywork.ai/blog/ai-agent-orchestration-best-practices-handoffs/), Temporal/Erlang/OTP-style docs for supervision and durability.

---

## 6. ERC-8004 & On-Chain Identity

- **Top 8004 agents (85–89 score):** Live MCP + A2A endpoints, health checks ~every 30 min, real A2A JSON-RPC task handling, multiple trust badges (Reputation, Staked, TEE), 25–1500+ feedback items, multi-chain registration.
- **Copy from:** `docs/ERC8004_LEADERBOARD_AGENTS_AND_REPOS.md`, `docs/8004SCAN_CRITERIA_AND_IMPROVEMENTS.md`, 8004scan leaderboard repos for A2A and MCP implementations.

---

## 7. IoT / Grow Loop (Sensors → AI → Actuators)

We have a clear pipeline (sensors → orchestrator → Grok → tools → hardware). Few open-source “grow + AI” stacks exist; the copyable parts are:

- **Event-driven sensor → decision:** Typed events, priority queues (as in our redesign). Same idea as LangGraph state deltas: only ship what’s needed.
- **Safety as explicit FSM:** Olas-style FSMs for watering, dark period, kill switch (see `src/safety/`, `WATERING_SAFEGUARDS.md`).
- **Unified context:** One context blob (sensors + market + social + inbox) for the brain — similar to “HLP sees personality every cycle” and SciAgent’s coordinator having full picture.

---

## Quick Reference Table

| Domain            | Copy from (primary)                    | What to copy |
|-------------------|----------------------------------------|--------------|
| Orchestration     | LangGraph supervisor notebook          | State graph, handoffs, tool routing |
| Multi-domain brain| SciAgent, OmniNova                     | Coordinator/worker, domain routing |
| Messaging/channels| OpenClaw docs, Gateway protocol       | Lanes, WebSocket, plugin channels |
| Social/persona    | Eliza characterfile, GAME HLP          | Character files, platform variants, personality-in-loop |
| Trading           | Our GanjaMon + first-principles doc    | Deliberation, signals, regime, graduation |
| Reliability       | Olas FSM, Skywork, supervision trees   | FSMs for safety, circuit breakers, degradation |
| ERC-8004          | Leaderboard agents, our 8004 docs      | A2A/MCP live endpoints, health, trust badges |

---

## Where This Fits in Our Repo

- **Architecture:** `docs/AGENT_REDESIGN_FIRST_PRINCIPLES.md` — target design.
- **OpenClaw:** `docs/OPENCLAW_FRAMEWORK_DEEP_DIVE.md`, `openclaw/`.
- **Trading:** `cloned-repos/ganjamon-agent/CLAUDE.md`, `docs/GANJAMON_AGENT_ARCHITECTURE.md`.
- **Capabilities:** `docs/AGENT_CAPABILITIES.md`.

When adding a new subsystem or refactoring orchestration, check this doc for a concrete example to copy before implementing from scratch.
