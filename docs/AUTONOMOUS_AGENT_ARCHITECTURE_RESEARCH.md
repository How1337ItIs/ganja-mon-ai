# Autonomous AI Agent Architecture Research Report

**Date:** February 7, 2026
**Purpose:** First-principles redesign of a multi-purpose 24/7 autonomous agent
**Scope:** Modern frameworks, production patterns, memory systems, self-improvement, observability

---

## Table of Contents

1. [Agent Architecture Patterns](#1-agent-architecture-patterns)
2. [24/7 Autonomous Operation](#2-247-autonomous-operation)
3. [Memory Systems](#3-memory-systems)
4. [Multi-Objective Agent Design](#4-multi-objective-agent-design)
5. [Self-Improvement Mechanisms](#5-self-improvement-mechanisms)
6. [Event-Driven vs Polling](#6-event-driven-vs-polling)
7. [Agent-to-Agent Communication](#7-agent-to-agent-communication)
8. [Observability](#8-observability)
9. [Framework Comparison](#9-framework-comparison)
10. [Lessons from Production Failures](#10-lessons-from-production-failures)
11. [Architectural Recommendations](#11-architectural-recommendations)

---

## 1. Agent Architecture Patterns

### 1.1 The Four Core Patterns

Modern agent architectures in 2025-2026 converge on four primary patterns:

**ReAct (Reasoning + Acting)**
- Interleaves thinking and acting in a tight loop: Think -> Act -> Observe -> Think
- Best for: dynamic tasks requiring tool use, where the path to solution is not obvious upfront
- Weakness: expensive (every step involves an LLM call), can get stuck in loops
- Use when: tasks require significant interaction with tools and dynamic adaptation

**Plan-and-Execute**
- Separates planning from execution: Plan all steps -> Execute sequentially
- Best for: multi-step processes where workflow can be reasonably determined beforehand
- Advantage: cost savings (smaller models for sub-tasks, larger for planning)
- Weakness: less adaptable to unexpected outcomes; struggles to deviate from the plan
- Use when: tasks have clear structure and predictable steps

**Hybrid Plan-ReAct** (RECOMMENDED)
- High-level planner outlines major stages, ReAct-style executor handles fine-grained adaptive execution of each stage
- Gives both strategic coherence and tactical flexibility
- This is the emerging consensus best practice for production agents

**Cognitive Architecture (SOAR/ACT-R/BDI adapted for LLMs)**
- Classical 3-stage deliberation: assertion, commitment, reconsideration
- LLMs are no longer passive knowledge engines but "cognitive controllers" combining memory, tool use, and environmental feedback
- BDI (Belief-Desire-Intention) maps well to agent goals: beliefs = world state, desires = objectives, intentions = committed plans
- Modern LLM agents represent a "third paradigm" -- pretrained LLMs as general-purpose cognitive controllers

### 1.2 Orchestration Topologies

| Topology | Description | Best For |
|----------|-------------|----------|
| **Supervisor** | Router agent dispatches to specialists, synthesizes results | Clear role boundaries, quality control |
| **Peer-to-peer** | Agents communicate directly, sharing information | Parallel processing, distributed problems |
| **Pipeline** | Sequential processing, each agent transforms output | ETL-like workflows, content pipelines |
| **Hierarchical** | Multi-level supervisors with sub-teams | Complex organizations with many agents |

### 1.3 Key Design Principles

- **Explicit plan objects**: No long-running agent without an explicit plan. Planning reduces cognitive entropy
- **Structured outputs**: Use JSON Schema constrained decoding -- reduces parsing errors by 90%, <3% overhead
- **Tool-first design**: Model the world as tools the agent can invoke, not instructions the agent must follow
- **State machines over free-form loops**: Graph-based execution (like LangGraph) prevents unbounded agent behavior

---

## 2. 24/7 Autonomous Operation

### 2.1 Durable Execution (THE Critical Pattern)

The single most important pattern for 24/7 agents is **durable execution** -- the ability to survive crashes and resume exactly where you left off.

**How it works (Temporal/DBOS pattern):**
1. Separate **deterministic workflows** (orchestration logic) from **non-deterministic activities** (LLM calls, API requests, tool invocations)
2. Every completed step is checkpointed to a persistent store (Postgres, event history)
3. On failure/restart, workflows replay from the event history, skipping already-completed steps
4. The agent resumes from the last completed step with full context

**Production validation:**
- OpenAI uses Temporal for Codex (millions of agent requests in production)
- DBOS (from creators of Postgres and Spark) provides this as a Python library with a single dependency: Postgres
- Yutori.ai runs large-scale autonomous AI on DBOS durable execution

**Implementation options:**
| Tool | Language | Dependency | Notes |
|------|----------|------------|-------|
| **Temporal** | Python, Go, Java, TS | Temporal Server cluster | Most mature, OpenAI uses it |
| **DBOS** | Python | Postgres only | Lightweight, drop-in decorators |
| **Custom** | Any | SQLite/Postgres | Roll your own with WAL pattern |

### 2.2 Circuit Breaker Pattern

Three states: **Closed** (normal) -> **Open** (failing, stop calls) -> **Half-Open** (testing recovery)

Apply to every external dependency:
- LLM API calls (rate limits, outages)
- Sensor hardware (disconnection, bad readings)
- External APIs (blockchain RPCs, social media)
- Database connections

One production system went from 99.2% to 99.87% uptime by adding circuit breakers and falling back to cached responses when the primary model failed.

### 2.3 Graceful Degradation Levels

```
Level 0: FULL       - All capabilities active
Level 1: DEGRADED   - Non-critical features disabled (social posting, analytics)
Level 2: MINIMAL    - Core functions only (sensor reading, safety controls)
Level 3: SAFE_MODE  - Safety-critical only (watering limits, hardware protection)
Level 4: OFFLINE    - Log-only mode, no actions taken
```

**Fallback chain pattern**: Cache -> Database -> API -> Defaults. Execute handlers in order until one succeeds.

**Resource-based degradation**: Monitor CPU, memory, API quotas. Auto-trigger degradation when thresholds are exceeded, auto-recover when conditions improve.

### 2.4 Watchdog & Health Checks

- Emit heartbeat signals or update a status registry at regular intervals
- If heartbeat is missed (e.g., 5 minutes when normal is 30 seconds), auto-restart or reassign task
- Separate watchdog process (systemd, supervisor) monitors the agent process
- Health endpoint that reports: last decision time, memory usage, pending tasks, error rates

### 2.5 Backpressure & Rate Limiting

**Token budget management:**
- Monthly team budgets with 50%/80%/100% spend alerts
- Rate-of-change alerts (e.g., 3x daily average)
- Per-prompt ceiling checks using official tokenizers
- Dual limiting: request-based (req/s) AND token-based (tokens/s)

**Token bucket algorithm**: Allow bursts while maintaining average rate. Pre-estimate request cost, provisionally reserve output tokens, adjust after completion.

---

## 3. Memory Systems

### 3.1 The Three Memory Types

| Type | Purpose | Implementation | Persistence |
|------|---------|----------------|-------------|
| **Working Memory** | Current context, active goals, in-progress state | LLM context window + structured state object | Session-scoped |
| **Episodic Memory** | Specific events, conversations, decisions | Vector store + metadata (timestamps, outcomes) | Long-term |
| **Semantic Memory** | General knowledge, rules, domain expertise | Knowledge graph + entity relationships | Long-term |
| **Procedural Memory** | Learned skills, routines, tool-use patterns | Code snippets, prompt templates, tool chains | Long-term |

### 3.2 State of the Art: Hybrid Architectures

The consensus in 2025-2026 is that no single storage mechanism is sufficient. The best systems combine:

**Mem0 Architecture (Production-proven):**
- Extraction phase: processes messages + historical context to create new memories
- Update phase: evaluates extracted memories against existing ones, applies merge/update/delete operations
- Graph-enhanced variant (Mem0g): stores memories as directed labeled graphs (entities as nodes, relationships as edges)
- Results: 26% improvement over OpenAI baselines, 91% lower p95 latency, 90%+ token cost savings
- Selected by AWS as exclusive memory provider for their Agent SDK

**Zep Temporal Knowledge Graph:**
- Core innovation: explicit representation of both event time (T) and ingestion time (T') for every node and edge
- Enables reasoning over retroactive data, corrections, fact invalidation
- Built on Graphiti engine: dynamically updates knowledge graph in non-lossy manner
- Results: up to 18.5% accuracy improvement, 90% latency reduction vs baselines
- Production focus: accuracy, latency, and scalability

### 3.3 Memory Consolidation

Inspired by the Ebbinghaus forgetting curve:
- Recent memories have higher retrieval priority
- Memories that are frequently accessed get reinforced
- Unused memories are progressively summarized and compressed
- Critical memories (safety events, major decisions) are pinned and never decay

### 3.4 Practical Memory Architecture

```
+-----------------+     +------------------+     +------------------+
| Working Memory  |     | Episodic Store   |     | Semantic Graph   |
| (Context Window)|<--->| (Vector DB +     |<--->| (Knowledge Graph)|
| + State Object  |     |  SQLite/Postgres)|     | (Neo4j/NetworkX) |
+-----------------+     +------------------+     +------------------+
        |                       |                        |
        +----------+------------+------------------------+
                   |
           +-------v-------+
           | Memory Manager |  <- Consolidation, decay, retrieval
           | (Background)   |     ranking, deduplication
           +---------------+
```

**Retrieval strategy**: Combine vector similarity (for semantic relevance) with recency weighting and importance scoring. The search results show that simple brute-force similarity search handles even 100k memories in milliseconds -- complex vector DB infrastructure is often overkill.

---

## 4. Multi-Objective Agent Design

### 4.1 Priority-Based Task Scheduling

For an agent with competing goals (trading, social posting, cultivation, sensor monitoring):

**Priority Queue with Dynamic Weighting:**
```
Priority = base_priority * urgency_multiplier * deadline_factor * resource_availability

Where:
- base_priority: static importance (safety > trading > social)
- urgency_multiplier: increases as deadlines approach or conditions change
- deadline_factor: hard deadlines get exponential boost
- resource_availability: suppress tasks when required resources are unavailable
```

**Safety hierarchy (non-negotiable):**
```
P0: SAFETY      - Hardware protection, watering limits, emergency shutoff
P1: MAINTENANCE - Sensor readings, health checks, data persistence
P2: OPERATIONS  - Trading execution, cultivation decisions
P3: ENGAGEMENT  - Social posting, community interaction
P4: IMPROVEMENT - Self-reflection, learning, optimization
```

### 4.2 Time-Sliced Execution

Rather than running all objectives in one monolithic loop:

```
Main Loop (every 30s):
  1. Check P0 safety conditions (always, every cycle)
  2. Read sensor data if due (P1, every 5 min)
  3. Check trading signals if due (P2, every 1-5 min depending on market)
  4. Make cultivation decisions if due (P2, every 30 min)
  5. Post to social if due (P3, every 2-6 hours)
  6. Run self-improvement if idle (P4, every 6-12 hours)
```

### 4.3 Task Preemption

Higher-priority tasks can interrupt lower-priority ones:
- P0 safety events immediately halt all other processing
- P1 sensor anomalies pause P3/P4 tasks
- P2 high-confidence trading signals can preempt P3/P4
- P3/P4 never preempt anything

### 4.4 Resource Contention Management

When multiple objectives compete for the same resource (e.g., LLM API quota):
- Reserve minimum allocation for each priority level
- Surplus goes to highest-priority active task
- Token budget enforcement per-objective (prevents one objective from starving others)
- Backoff multiplier: failed tasks get lower priority temporarily

---

## 5. Self-Improvement Mechanisms

### 5.1 Proven Patterns (from NeurIPS 2025 research)

| Mechanism | Setup Effort | Persistence | Safety Risk | Effectiveness |
|-----------|-------------|-------------|-------------|---------------|
| **Reflection loops** | Minimal | None (ephemeral) | Low | ~91% pass@1 on HumanEval |
| **Experience replay** | Low | Medium | Low | 73% -> 93% on ALFWorld |
| **Self-generated curricula** | Moderate | High | Moderate | 2x tool-use performance |
| **Self-training on verified traces** | Moderate | High | Moderate | Small models match large baselines |
| **Code-level self-modification** | High | High | High | 17-53% improvements |

### 5.2 The Practical Builder's Roadmap

**Phase 1: Reflection + Experience Replay (Start Here)**
- Agent critiques its own outputs after each decision cycle
- Store successful trajectories with context, decision, outcome, and reflection
- Retrieve relevant past experiences as in-context examples for future decisions
- This alone delivers massive gains with near-zero infrastructure cost

**Phase 2: Self-Generated Exemplars**
- Agent creates challenging scenarios for itself based on past failures
- Successful solutions become training examples
- Difficulty automatically scales with agent capability

**Phase 3: Persistent Skill Representations**
- Agent maintains a library of learned procedures (prompt templates, tool chains)
- Procedures are versioned and A/B tested
- Only improvements meeting predefined criteria are kept

**Phase 4: Gated Self-Modification**
- Agent can propose changes to its own prompts, tool definitions, or scheduling parameters
- Changes are validated against benchmark metrics before acceptance
- Conservative acceptance: only keep improvements that clear a significance threshold
- All modifications logged and reversible

### 5.3 Critical Control Mechanisms

"Don't design how agents change; design rules governing what changes are allowed."

- **External verification**: unit tests, benchmark metrics, safety constraints
- **Conservative acceptance**: only keep improvements meeting predefined criteria
- **Diversity safeguards**: curate experience to prevent narrow overfitting
- **Meta-level oversight**: modification boundaries that cannot be self-modified
- **Rollback capability**: every self-modification is reversible within a time window

---

## 6. Event-Driven vs Polling

### 6.1 The Verdict: Event-Driven Wins

The industry consensus in 2025-2026 is overwhelming: **event-driven architecture is the correct foundation for autonomous agents.**

**Why polling fails:**
- Wastes 95% of API calls (nothing changed since last poll)
- Burns through rate limits and quotas
- Never achieves true real-time responsiveness
- Scales linearly with the number of data sources (O(n) per cycle)
- Creates unnecessary load on upstream systems

**Why event-driven wins:**
- Agents respond to events asynchronously and in real-time
- Natural alignment with the agent paradigm: perceive events -> reason -> act
- Decoupled architecture: agents operate autonomously without rigid dependencies
- Scales with event volume, not poll frequency

### 6.2 The Pragmatic Hybrid

Pure event-driven is ideal but not always practical (some APIs only support polling). The recommended approach:

```
Event Sources (preferred):
  - WebSocket connections (blockchain events, price feeds)
  - Webhooks (social media notifications, API callbacks)
  - Message queues (inter-agent communication)
  - File system watchers (config changes, data updates)
  - Hardware interrupts (sensor threshold alerts)

Polling Fallbacks (when events unavailable):
  - Use exponential backoff, not fixed intervals
  - Cache results aggressively
  - Delta detection (only process changes)
  - Adaptive frequency (poll more during active periods)

Scheduling Layer (for periodic tasks):
  - Cron-like scheduler for recurring tasks (social posting, self-reflection)
  - Priority queue for on-demand tasks
  - Temporal Schedules for durable scheduled execution
```

### 6.3 Event Bus Architecture

```
+------------------+     +---------------+     +------------------+
| Event Sources    |     | Event Bus     |     | Event Handlers   |
|                  |     | (in-process   |     |                  |
| - Sensor data    |---->| queue or      |---->| - Decision engine|
| - Trading signals|     | Redis/Kafka)  |     | - Safety monitor |
| - Social mentions|     |               |     | - Memory writer  |
| - Timer events   |     | Priorities +  |     | - Action executor|
| - System health  |     | Backpressure  |     | - Logger         |
+------------------+     +---------------+     +------------------+
```

For a single-machine agent, an in-process async queue (Python asyncio.Queue or similar) is sufficient. Kafka/Redis is only needed for multi-machine or high-throughput scenarios.

---

## 7. Agent-to-Agent Communication

### 7.1 Google A2A Protocol (Industry Standard)

The Agent2Agent (A2A) protocol launched by Google in April 2025, now under the Linux Foundation with 150+ supporting organizations:

**Core concepts:**
- **Agent Card**: JSON document advertising capabilities, endpoints, authentication
- **Client/Remote model**: Client agent formulates tasks, remote agent executes them
- **Messages with Parts**: Each message contains typed content parts, enabling format negotiation
- **Built on HTTP, SSE, JSON-RPC**: Easy integration with existing stacks

**A2A v0.3 (latest):**
- gRPC support for high-performance communication
- Signed security cards
- Python SDK with client-side support

### 7.2 MCP (Model Context Protocol) -- For Tool Integration

MCP (Anthropic) and A2A (Google) are complementary:
- **MCP**: How agents connect to tools and data sources (tools, resources, prompts)
- **A2A**: How agents communicate with each other (tasks, messages, artifacts)

**MCP November 2025 spec updates:**
- OAuth 2.0 authorization flows
- Asynchronous execution support
- Enterprise-grade security (per-tool authorization, input validation, TLS)
- Gateway pattern for centralized policy enforcement
- 1,000+ open-source connectors available

### 7.3 For Internal Multi-Agent Systems

For agents within the same system (not cross-organization):

**Shared state via message passing:**
```python
# Simple internal A2A pattern
class AgentMessage:
    sender: str          # "trading_agent" | "cultivation_agent" | "social_agent"
    recipient: str       # target agent or "broadcast"
    type: str            # "signal" | "request" | "response" | "event"
    priority: int        # 0-4 (matching safety hierarchy)
    payload: dict        # structured data
    timestamp: datetime
    correlation_id: str  # for request/response tracking
```

**Shared context file** (simple, effective for co-located agents):
- Each agent writes its status/context to a shared JSON file
- Other agents read (not write) each other's context
- Unified context aggregator merges all contexts for decision-making
- This pattern already works well in practice (see unified_context.py)

---

## 8. Observability

### 8.1 The Three Pillars for AI Agents

| Pillar | What to Capture | Tools |
|--------|----------------|-------|
| **Traces** | Decision chains, tool invocations, LLM calls, reasoning steps | OpenTelemetry, LangSmith, Langfuse |
| **Metrics** | Token usage, latency, error rates, decision quality, cost | Prometheus, custom counters |
| **Logs** | Structured events with context (not just text) | Structured JSON logging, ELK |

### 8.2 OpenTelemetry for AI Agents (Emerging Standard)

OTel GenAI Semantic Conventions (v1.37+) define standard attributes:
- `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.provider.name`
- Trace spans for: agent prompt receipt, tool invocations, reasoning steps, inter-agent messages
- Sub-spans capture: prompt/response bodies, token counts, model metadata, cost

**Agent Framework Semantic Conventions (in development):**
- Tasks, Actions, Agents, Teams, Artifacts, Memory
- Standard span hierarchies for multi-step agent workflows

### 8.3 Production Observability Stack

**Tier 1 (Self-hosted, free):**
- **Langfuse** (open source, MIT, 19k+ GitHub stars): tracing, prompt management, evaluations
- Self-host with Docker, free unlimited
- Caveat: 15% overhead in multi-step workflows (vs near-zero for LangSmith)

**Tier 2 (Managed, paid):**
- **LangSmith**: Native LangGraph integration, virtually no overhead, LangGraph Studio for live debugging
- **Galileo**: Purpose-built agent reliability, Luna-2 guardrails at sub-200ms latency, 97% cost reduction in monitoring

**Tier 3 (Build your own):**
- Structured JSON logs -> SQLite/Postgres
- Custom dashboards for domain-specific metrics
- Alerting on decision quality, not just system health

### 8.4 What to Monitor for a 24/7 Autonomous Agent

```
SYSTEM HEALTH:
  - Process alive/responsive (heartbeat)
  - Memory usage, CPU, disk
  - API quota remaining (LLM, social, blockchain)
  - Error rate (rolling 5min, 1hr, 24hr)

DECISION QUALITY:
  - Decisions per hour (trend, not absolute)
  - Action distribution (are we doing the right mix of things?)
  - Confidence scores over time
  - Outcomes of past decisions (feedback loop)

COST:
  - Token usage per objective (trading vs social vs cultivation)
  - Cost per decision
  - Daily/weekly/monthly spend vs budget
  - Cost per successful outcome

SAFETY:
  - Safety constraint violations (even caught ones)
  - Time since last safety event
  - Hardware state (all actuators responding?)
  - Sensor data freshness (stale readings = danger)
```

---

## 9. Framework Comparison

### 9.1 Multi-Agent Frameworks

| Framework | Philosophy | Best For | Weakness | Maturity |
|-----------|-----------|----------|----------|----------|
| **LangGraph** | Graph-based workflows | Complex stateful workflows, production | Steep learning curve | High (LangChain backing) |
| **CrewAI** | Role-based teams | Rapid prototyping, clear role boundaries | Debugging is painful, logging broken | Medium |
| **AutoGen** | Conversational agents | Enterprise, async high-throughput | Complex setup | High (Microsoft backing) |
| **ElizaOS** | Autonomous Web3 agents | Crypto/social agents, plugin ecosystem | TypeScript only, Web3-centric | Medium (ai16z) |
| **Temporal** | Durable execution | Crash-proof long-running workflows | Infrastructure overhead | Very High (OpenAI uses it) |
| **DBOS** | Lightweight durable execution | Simple crash-proof agents | Less mature ecosystem | Medium |

### 9.2 Memory Systems

| System | Architecture | Best For | Latency | Cost |
|--------|-------------|----------|---------|------|
| **Mem0** | Vector + Graph hybrid | Production memory layer | Low (p95 optimized) | AWS partnership |
| **Zep/Graphiti** | Temporal knowledge graph | Time-aware relationships | Very low (90% reduction) | Self-hosted |
| **Simple SQLite** | Relational + JSON | Lightweight agents | Minimal | Free |
| **Chroma/Qdrant** | Pure vector store | Semantic search only | Low | Free (self-hosted) |

### 9.3 Observability

| Tool | Type | Cost | Overhead | Best For |
|------|------|------|----------|----------|
| **Langfuse** | Open source | Free (self-host) | ~15% | Budget-conscious, full control |
| **LangSmith** | Managed | Free tier, then paid | ~0% | LangGraph users, performance-critical |
| **Galileo** | Managed | Free tier | Low | Enterprise guardrails, reliability |
| **Custom OTel** | DIY | Free | Varies | Full control, existing infra |

---

## 10. Lessons from Production Failures

### 10.1 Why AI Agents Fail (Composio 2025 Report)

The three killers are not LLM quality -- they are integration issues:

1. **Dumb RAG**: Dumping everything into context without intelligent memory management. The fix: structured memory with extraction, consolidation, and selective retrieval.

2. **Brittle Connectors**: API integrations that break silently. The fix: circuit breakers, health checks, fallback chains, and retry with exponential backoff.

3. **Polling Tax**: Wasting resources polling for changes. The fix: event-driven architecture with webhooks and streaming.

### 10.2 AutoGPT/BabyAGI Lessons

- **Hallucination loops**: Agents planning and replanning without making progress. Fix: explicit plan objects with step limits and timeout-based plan abandonment.
- **Vector DB overkill**: Simple local file storage handles 100k+ memories with brute-force search in milliseconds. Don't over-engineer memory storage.
- **Model quality matters enormously**: Weaker models cause dramatically worse agent performance -- more mistakes, more loops, less coherence. Use the best model you can afford for planning; smaller models for execution.
- **Step limits are essential**: Without hard limits on reasoning steps, agents spiral into infinite loops.

### 10.3 The Demo-to-Production Gap

The gap between a working demo and a reliable production system is where projects die. Organizational failures (weak controls, unclear ownership, misplaced trust) kill more agents than technical ones.

---

## 11. Architectural Recommendations

### 11.1 Recommended Architecture for GrokMon Multi-Agent System

```
+------------------------------------------------------------------+
|                        EVENT BUS (asyncio)                        |
|  Priorities: P0 Safety > P1 Maintenance > P2 Ops > P3 Social     |
+------------------------------------------------------------------+
     |              |              |              |              |
+----v----+   +----v----+   +----v----+   +----v----+   +----v----+
| Sensor  |   | Trading |   | Cultiv. |   | Social  |   | Self-   |
| Monitor |   | Agent   |   | Agent   |   | Agent   |   | Improve |
| (P1)    |   | (P2)    |   | (P2)    |   | (P3)    |   | (P4)    |
+---------+   +---------+   +---------+   +---------+   +---------+
     |              |              |              |              |
+------------------------------------------------------------------+
|                    UNIFIED CONTEXT LAYER                          |
|  Shared state, cross-agent awareness, memory aggregation         |
+------------------------------------------------------------------+
     |              |              |
+----v----+   +----v----+   +----v----+
| Working |   | Episodic|   | Semantic|
| Memory  |   | Store   |   | Graph   |
| (State) |   | (SQLite)|   | (Graph) |
+---------+   +---------+   +---------+
     |              |              |
+------------------------------------------------------------------+
|                    DURABLE EXECUTION LAYER                        |
|  Checkpointing, crash recovery, exactly-once execution           |
+------------------------------------------------------------------+
     |
+----v----+
| Postgres|
| /SQLite |
+---------+
```

### 11.2 Specific Technology Choices

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| **Execution** | DBOS (Python + Postgres) or custom WAL | Lightweight, no infra overhead, crash-proof |
| **Event Bus** | asyncio.Queue with priority support | Single-machine, no external dependencies |
| **Memory - Episodic** | SQLite + custom similarity search | 100k memories searchable in ms, no vector DB needed |
| **Memory - Semantic** | NetworkX knowledge graph + SQLite persistence | Lightweight, no Neo4j dependency |
| **Memory - Working** | Structured Python dataclass/Pydantic model | Explicit state, serializable |
| **Observability** | Structured JSON logs + SQLite metrics + custom dashboard | Zero external dependencies |
| **LLM Integration** | Structured outputs (JSON Schema) + retry with circuit breaker | 90% fewer parsing errors |
| **Agent Communication** | Shared context files + async message queue | Already proven in unified_context.py pattern |
| **Scheduling** | Event-driven primary + cron fallback for periodic tasks | Best of both worlds |
| **Self-Improvement** | Reflection + experience replay (Phase 1-2 from roadmap) | High ROI, low risk |

### 11.3 Implementation Priority

**Phase 1: Foundation (Week 1-2)**
- [ ] Event bus with priority queue
- [ ] Durable execution layer (checkpoint/resume)
- [ ] Circuit breakers on all external calls
- [ ] Structured logging with decision traces
- [ ] Graceful degradation levels

**Phase 2: Intelligence (Week 3-4)**
- [ ] Hybrid memory system (working + episodic + semantic)
- [ ] Memory consolidation background process
- [ ] Reflection loop after each decision cycle
- [ ] Experience replay for in-context learning
- [ ] Priority-based multi-objective scheduling

**Phase 3: Resilience (Week 5-6)**
- [ ] Watchdog with auto-restart
- [ ] Health dashboard
- [ ] Token budget management per objective
- [ ] Backpressure on LLM API calls
- [ ] Adaptive polling frequencies

**Phase 4: Evolution (Week 7-8)**
- [ ] Self-generated training examples
- [ ] Gated self-modification of prompts/parameters
- [ ] A/B testing of decision strategies
- [ ] Cross-agent learning (trading insights inform cultivation, etc.)
- [ ] Performance benchmarking and regression detection

### 11.4 Anti-Patterns to Avoid

1. **Over-engineering memory**: Start with SQLite, not a vector database. You don't need Pinecone for 100k memories.
2. **Polling everything**: Convert to event-driven wherever possible. Polling should be the exception, not the rule.
3. **Monolithic agent loop**: Separate concerns into distinct agents/modules communicating via events.
4. **Unbounded reasoning**: Always set step limits, token budgets, and timeouts on LLM calls.
5. **Ignoring cost**: Track token spend per-objective from day one. Costs compound fast.
6. **No circuit breakers**: Every external call needs failure handling. One stuck API call can block everything.
7. **Free-form LLM output**: Always use structured outputs (JSON Schema). Parsing free text is fragile.
8. **Self-modification without gates**: Never let an agent modify itself without external verification.

---

## Sources

### Agent Architecture Patterns
- [Azure AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Agentic AI Design Patterns 2026 Edition](https://medium.com/@dewasheesh.rana/agentic-ai-design-patterns-2026-ed-e3a5125162c5)
- [Google Cloud: Choose a Design Pattern for Agentic AI](https://docs.google.com/architecture/choose-design-pattern-agentic-ai-system)
- [ReAct vs Plan-and-Execute Comparison](https://dev.to/jamesli/react-vs-plan-and-execute-a-practical-comparison-of-llm-agent-patterns-4gh9)
- [Cognitive Architectures for Language Agents](https://arxiv.org/pdf/2309.02427)
- [Applying Cognitive Design Patterns to General LLM Agents](https://arxiv.org/html/2505.07087v2)

### 24/7 Operation & Reliability
- [Temporal: Durable Execution for AI Agents](https://temporal.io/blog/of-course-you-can-build-dynamic-ai-agents-with-temporal)
- [DBOS: Durable Execution for Crashproof AI Agents](https://www.dbos.dev/blog/durable-execution-crashproof-ai-agents)
- [PraisonAI: Graceful Degradation Patterns](https://docs.praison.ai/docs/best-practices/graceful-degradation)
- [Galileo: AI Agent Reliability Strategies](https://galileo.ai/blog/ai-agent-reliability-strategies)
- [AI Agents in Production 2025 (Cleanlab)](https://cleanlab.ai/ai-agents-in-production-2025/)
- [Building AI That Never Goes Down (Graceful Degradation)](https://medium.com/@mota_ai/building-ai-that-never-goes-down-the-graceful-degradation-playbook-d7428dc34ca3)

### Memory Systems
- [Zep: Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1)
- [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413)
- [AWS: Persistent Memory with Mem0, ElastiCache, Neptune](https://aws.amazon.com/blogs/database/build-persistent-memory-for-agentic-ai-applications-with-mem0-open-source-amazon-elasticache-for-valkey-and-amazon-neptune-analytics/)
- [Three Types of Long-term Memory AI Agents Need](https://machinelearningmastery.com/beyond-short-term-memory-the-3-types-of-long-term-memory-ai-agents-need/)
- [ICLR 2026 Workshop: Memory for LLM-Based Agentic Systems](https://openreview.net/pdf?id=U51WxL382H)

### Self-Improvement
- [Yohei Nakajima: Better Ways to Build Self-Improving AI Agents](https://yoheinakajima.com/better-ways-to-build-self-improving-ai-agents/)
- [SAGE: Self-evolving Agents with Reflective and Memory-augmented Abilities](https://arxiv.org/html/2409.00872v2)
- [Contextual Experience Replay for Self-Improvement](https://www.semanticscholar.org/paper/204246f01e8870d7244450e5042a32c560263089)
- [MetaAgent: Self-Evolving Agent via Tool Meta-Learning](https://arxiv.org/abs/2508.00271)
- [Meta-cognitive Reflection for Efficient Self-Improvement](https://arxiv.org/html/2601.11974v1)

### Event-Driven Architecture
- [Confluent: The Future of AI Agents Is Event-Driven](https://www.confluent.io/blog/the-future-of-ai-agents-is-event-driven/)
- [AWS: Event-Driven Architecture for Serverless AI](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-serverless/event-driven-architecture.html)
- [Composio: Why AI Agent Pilots Fail in Production](https://composio.dev/blog/why-ai-agent-pilots-fail-2026-integration-roadmap)
- [Apache Kafka and Flink Power Event-Driven Agentic AI](https://www.kai-waehner.de/blog/2025/04/14/how-apache-kafka-and-flink-power-event-driven-agentic-ai-in-real-time/)

### Agent-to-Agent Communication
- [Google: Announcing the Agent2Agent Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [A2A Protocol Official Site](https://a2a-protocol.org/latest/)
- [A2A on GitHub](https://github.com/a2aproject/A2A)
- [Linux Foundation Launches A2A Protocol Project](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)
- [MCP Specification (November 2025)](https://modelcontextprotocol.io/specification/2025-11-25)

### Observability
- [OpenTelemetry: AI Agent Observability](https://opentelemetry.io/blog/2025/ai-agent-observability/)
- [OTel Semantic Conventions for GenAI Agent Spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
- [15 AI Agent Observability Tools in 2026](https://research.aimultiple.com/agentic-monitoring/)
- [Langfuse: Open Source LLM Observability](https://langfuse.com/docs/observability/overview)
- [LangSmith Observability Platform](https://www.langchain.com/langsmith/observability)

### Framework Comparisons
- [CrewAI vs LangGraph vs AutoGen (DataCamp)](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [LangGraph Multi-Agent Orchestration Guide](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/)
- [ElizaOS Documentation](https://docs.elizaos.ai)
- [Top AI Agent Frameworks 2025 (Turing)](https://www.turing.com/resources/ai-agent-frameworks)

### Production Lessons
- [AutoGPT/BabyAGI Evolution and Lessons](https://medium.com/@roseserene/agentic-ai-autogpt-babyagi-and-autonomous-llm-agents-substance-or-hype-8fa5a14ee265)
- [BabyAGI GitHub (Yohei Nakajima)](https://github.com/yoheinakajima/babyagi)
- [AI API Cost & Throughput Management Best Practices 2025](https://skywork.ai/blog/ai-api-cost-throughput-pricing-token-math-budgets-2025/)
- [Structured Output AI Reliability Guide 2025](https://www.cognitivetoday.com/2025/10/structured-output-ai-reliability/)
