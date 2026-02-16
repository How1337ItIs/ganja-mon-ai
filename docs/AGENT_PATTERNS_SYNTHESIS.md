# Agent Patterns Synthesis

> **Source**: Deep study of 15+ cloned repositories in `cloned-repos/` + ERC-8004 top-agent ecosystem analysis
> **Purpose**: Extract borrowable patterns to make Ganja Mon's agent more effective
> **Date**: 2026-02-09 (Updated: Third Pass — ERC-8004 Agent Ecosystem)

---

## Executive Summary

After studying the architecture of ElizaOS, Mibera Legba (Loa framework), claude-mem, the personality engine, Passivbot, Jesse, Ethereum Wingman, OpenClaw skills (Ralph Loop, Hippocampus Memory), the OpenClaw/Moltbook ecosystem (AgentGuard, Agent Rooms, Skill Permissions), Mega Chad, and the top-performing ERC-8004 agents (Captain Dackie, Gekko Rebalancer, Minara AI), **30 high-impact patterns** emerge. These patterns solve the hardest problems in autonomous agent operation: **memory survival, identity coherence, context management, self-improvement, multi-agent coordination, hallucination prevention, documentation integrity, incentive-aligned protocol design, on-chain agent identity/reputation, trustless agent-to-agent commerce, skill security/provenance, and agent social participation**.

> See also: `docs/ERC8004_AGENT_PATTERNS.md` for the full Captain Dackie teardown and 8004 leaderboard analysis.
> See also: `cloned-repos/kevins-openclaw-sandbox/` for authoritative OpenClaw/Moltbook reference implementations.

---

## Pattern 1: Soul + Identity + Memory Architecture
**Source**: `mibera-legba/SOUL.md`, `IDENTITY.md`, `MEMORY.md`

### The Problem
Agents wake up with amnesia every session. Without structured identity files, they default to generic assistant behavior.

### The Pattern
Three separate files create a **layered personality**:

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `SOUL.md` | Core behavioral axioms ("who you are") | Rarely (existential changes only) |
| `IDENTITY.md` | Crystallized identity (name, avatar, archetype) | When identity evolves |
| `MEMORY.md` | Curated learnings, relationships, active context | Every session |

### Key Design Decisions
- **SOUL.md** contains axioms like *"Be resourceful before asking"* and *"Earn trust through competence"* — these are SHORT, opinionated, and anti-sycophantic
- **IDENTITY.md** connects to cultural/mythological references (Papa Legba = crossroads daemon)
- **MEMORY.md** has an explicit **Learnings** section with dated entries and a **Key Relationships** section

### Borrowable for Ganja Mon
Create `SOUL.md` (Rasta axioms, techno-animist principles), `IDENTITY.md` (Ganja Mon persona crystallized), and expand `MEMORY.md` for persistent learnings about grow data, community interactions, and market intelligence.

---

## Pattern 2: Lossless Ledger Protocol ("Clear, Don't Compact")
**Source**: `mibera-legba/.claude/protocols/session-continuity.md`

### The Problem
Context windows are finite. When they fill up, either the platform silently summarizes (losing details) or the user clears manually (losing everything).

### The Pattern
Treat the context window as a **disposable workspace** and external files as **lossless ledgers**:

```
TRUTH HIERARCHY (highest to lowest authority):
1. CODE (src/)           ← ABSOLUTE truth
2. BEADS (.beads/)       ← Task graph, decisions
3. NOTES.md              ← Decision log, session state
4. TRAJECTORY            ← Audit trail
5. PRD/SDD               ← Design intent (may drift)
6. LEGACY DOCS           ← Often stale
7. CONTEXT WINDOW        ← TRANSIENT, DISPOSABLE, NEVER authoritative
```

### Key Mechanisms
- **Tiered Recovery**: L1 (~100 tokens, just session state) → L2 (~500, semantic search) → L3 (full file read)
- **Delta-Synthesis**: Continuously externalize decisions to NOTES.md at Yellow threshold (5K tokens)
- **Fork Detection**: If context says one thing and ledger says another, **ledger always wins**
- **Synthesis Checkpoint**: Before clearing context, validate grounding ratio ≥ 0.95

### Borrowable for Ganja Mon
Implement a `NOTES.md` pattern for the grow operation. Every environmental decision (VPD adjustment, light schedule change, nutrient mix) should be logged with timestamp, rationale, and sensor evidence. This creates an immutable grow diary that survives context wipes.

---

## Pattern 3: Three-Zone Managed Scaffolding
**Source**: `mibera-legba/PROCESS.md` (Loa v1.1.0)

### The Problem
Agents modify system files they shouldn't touch, corrupting their own configuration.

### The Pattern

| Zone | Path | Owner | Permission |
|------|------|-------|------------|
| **System** | `.claude/` | Framework | NEVER edit directly |
| **State** | `grimoires/`, `.beads/` | Project | Read/Write |
| **App** | `src/`, `lib/`, `app/` | Developer | Read (write requires confirmation) |

### Key Mechanisms
- **Checksums**: SHA-256 hashes of all System Zone files in `checksums.json`
- **Integrity Enforcement**: `strict` (blocks on drift), `warn` (development), `disabled`
- **Customization**: All overrides go to `.claude/overrides/` — survive framework updates
- **Recovery**: `--force-restore` to reset System Zone from known-good state

### Borrowable for Ganja Mon
Define system files (rules, protocols) vs. state files (grow logs, sensor data) vs. app files (website, trading code). Protect critical config from accidental agent edits.

---

## Pattern 4: Karpathy Principles (Anti-LLM-Failure-Modes)
**Source**: `mibera-legba/.claude/protocols/karpathy-principles.md`

### The Problem
LLMs make three systematic errors: unjustified assumptions, overcomplicated solutions, and unintended side effects.

### The Four Principles

1. **Think Before Coding**: Surface assumptions explicitly. Present options when multiple interpretations exist.
2. **Simplicity First**: No speculative features. No premature abstractions. Could this be 50 lines instead of 200?
3. **Surgical Changes**: Only modify what's requested. Match existing style even if you'd do it differently.
4. **Goal-Driven Execution**: Transform tasks into verifiable criteria. WHAT → VERIFY → EVIDENCE.

### Anti-Pattern Gallery

| Bad | Good |
|-----|------|
| User says "add auth" → LLM builds OAuth2+JWT+2FA | Ask which type fits their needs |
| User says "add config for URL" → LLM creates ConfigManager with caching and hot-reload | `const API_URL = process.env.API_URL \|\| 'http://localhost:3000'` |
| User says "fix null check on line 45" → LLM reformats entire function | Change only line 45 |

### Borrowable for Ganja Mon
Embed these as pre-implementation checklist items in the agent's rules. Particularly critical for grow decisions — when Grok suggests a change, verify with sensor data first, don't over-engineer the response.

---

## Pattern 5: Continuous Learning with Quality Gates
**Source**: `mibera-legba/.loa.config.yaml` (v0.17.0 - v1.10.0)

### The Problem
Agents repeat the same mistakes. They don't learn from debugging successes.

### The Pattern
**Auto-extract skills from debugging discoveries**, filtered through quality gates:

```yaml
quality_gates:
  discovery_depth:    # Is the solution non-trivial?
    min_score: 5
  reusability:        # Is the pattern generalizable?
    min_score: 5
  trigger_clarity:    # Can we identify when this applies?
    min_score: 5
  verification:       # Was the solution verified to work?
    min_score: 3
```

### Skill Lifecycle
1. **Discovery**: Agent solves a non-trivial problem
2. **Extraction**: Pattern extracted to `skills-pending/`
3. **Approval**: Human reviews before activation
4. **Activation**: Skill moves to `skills/`
5. **Effectiveness Tracking**: Signal weights (task completed +3, user negative -5)
6. **Pruning**: Archive after 90 days of no matches or 3 ineffective applications

### Compound Learning (Cross-Session)
- **Pattern Detection**: Min 2 occurrences → pattern candidate
- **Types**: `repeated_error`, `convergent_solution`, `anti_pattern`, `project_convention`
- **Morning Context**: Load top 5 learnings at session start (max 30 days old, min effectiveness 50)

### Borrowable for Ganja Mon
Apply to cultivation: every VPD correction, pest response, or feeding adjustment that works should be extracted as a "grow skill." Over time, the agent builds a library of proven responses to specific conditions.

---

## Pattern 6: Agent-to-Agent Communication via File-Based Feedback Loops
**Source**: `mibera-legba/PROCESS.md` (Loa workflow)

### The Problem
Multi-phase work requires handoffs between specialized roles (planner → architect → implementer → reviewer → security auditor).

### The Pattern
Agents communicate through files in a shared directory (`grimoires/loa/a2a/`):

```
grimoires/loa/a2a/
├── sprint-N/
│   ├── reviewer.md          ← Engineer → Reviewer
│   ├── engineer-feedback.md ← Reviewer → Engineer  
│   ├── auditor-sprint-feedback.md ← Security Auditor → Engineer
│   └── COMPLETED            ← Completion marker
```

### Key Design Decisions
- **Priority ordering**: Security feedback > Code review feedback > Normal implementation
- **Blocking gates**: Sprint planner checks for `CHANGES_REQUIRED` before allowing new sprints
- **Approval signals**: Clear strings like `"All good"` and `"APPROVED - LETS FUCKING GO"`

### Borrowable for Ganja Mon
Structure the Chromebook → Windows communication similarly. Sensor readings → Grok analysis → Grow decision → Execution log. Each handoff is a file that the next agent reads.

---

## Pattern 7: Specialized Agent Roles as Skills
**Source**: `mibera-legba/.claude/skills/`

### The Problem
A single agent prompt can't cover all specialized domains.

### The Pattern
Each role is a **skill** with a 3-level architecture:

| Level | File | Content | Token Cost |
|-------|------|---------|------------|
| L1 | `index.yaml` | Metadata, triggers, dependencies | ~100 tokens |
| L2 | `SKILL.md` | KERNEL instructions, workflows | ~2000 tokens |
| L3 | `resources/` | Templates, checklists, scripts | Loaded on-demand |

### 8 Defined Roles
1. `discovering-requirements` (Product Manager)
2. `designing-architecture` (Software Architect)
3. `planning-sprints` (Technical PM)
4. `implementing-tasks` (Senior Engineer)
5. `reviewing-code` (Technical Lead)
6. `deploying-infrastructure` (DevOps)
7. `auditing-security` (Cypherpunk Auditor)
8. `translating-for-executives` (DevRel)

Plus bonus roles: `autonomous-agent`, `continuous-learning`, `run-mode`

### Borrowable for Ganja Mon
Define cultivation-specific roles: Sensor Analyst, VPD Controller, Nutrient Mixer, Pest Scout, Harvest Timer. Each with its own skill file and trigger conditions.

---

## Pattern 8: Personality as Computed Output
**Source**: `mibera-personality-engine/`

### The Problem
Hand-writing personality prompts doesn't scale. You get generic or inconsistent behavior.

### The Pattern
**Compute personality from data** using structured dimensions:

| Dimension | Range | Description |
|-----------|-------|-------------|
| Openness | -1 to 1 | Conservative ↔ Experimental |
| Energy | -1 to 1 | Withdrawn ↔ Hypersocial |
| Chaos | -1 to 1 | Orderly ↔ Entropic |
| Warmth | -1 to 1 | Cold ↔ Affectionate |
| Intensity | -1 to 1 | Chill ↔ Manic |
| Mysticism | 0 to 1 | Materialist ↔ Techno-animist |

### Architecture
```
Traits (on-chain data) → Parser → Personality Vector → Generator → System Prompt
```

Each archetype carries:
- **Core values**: What drives behavior
- **Voice**: How speech patterns manifest
- **Quirks**: Unique behavioral tics

### Borrowable for Ganja Mon
Define the Rasta persona as a personality vector. Map the grow stage to behavioral modifiers — seedling stage = more cautious, flowering = more bold. Time of day affects voice energy. Market conditions affect market commentary intensity.

---

## Pattern 9: Component Architecture Boundaries
**Source**: `elizaos/CLAUDE.md` 

### The Problem
Agents build tangled code when architectural boundaries are unclear.

### The Pattern
Four component types with strict separation:

```
User Input → Action → Service → External API/SDK
                ↓
            Provider → Context for prompts
                ↓
        Post-interaction → Evaluator → Learning
```

| Component | Role | Can Modify State? |
|-----------|------|-------------------|
| **Actions** | Handle user commands, parse input | No (delegates to Services) |
| **Services** | Manage state, API connections, business logic | YES |
| **Providers** | Supply READ-ONLY context for prompts | No |
| **Evaluators** | Post-interaction learning and reflection | Indirect (via memory) |

### Common Mistakes to Avoid
- Using Providers to execute transactions → Use Services
- Using Evaluators to parse user input → Use Actions
- Calling external APIs directly from Actions → Go through Services
- Putting state in Providers → Providers are read-only

### Borrowable for Ganja Mon
Structure the FastAPI backend with this pattern. Sensor reads = Providers. Grow decisions = Actions. Device control = Services. Performance tracking = Evaluators.

---

## Pattern 10: Recursive Context Management
**Source**: `mibera-legba/.loa.config.yaml` (v0.20.0)

### The Problem
Deep agent chains (subagents calling subagents) exhaust context rapidly.

### The Pattern
**Semantic Result Cache + Condensation Engine + Early-Exit Coordination**:

```yaml
recursive_jit:
  cache:
    max_size_mb: 100
    ttl_days: 30
  condensation:
    default_strategy: structured_verdict  # Not full text
    max_condensed_tokens: 50
    preserve_fields: [verdict, severity_counts, top_findings]
  early_exit:
    enabled: true
    grace_period_seconds: 5
  continuous_synthesis:
    enabled: true
    on_cache_set: true    # Write to NOTES.md on cache writes
    on_condense: true     # Log condensation decisions
    on_early_exit: true   # Log milestones on exit
```

### Key Insight
When a subagent produces a 2000-token result, **condense it to 50 tokens** (verdict + key findings) before passing upstream. Cache the full result for drill-down if needed.

### Probe-Before-Load Pattern
Before reading a large file:
1. Check file size
2. If > 500 lines, probe metadata first
3. Only full-read if relevance confirmed
4. Budget: Small codebase (<30K tokens) = load all, Medium (<150K) = prioritized, Large (>500K) = probe + excerpts

### Borrowable for Ganja Mon
Sensor data streams are massive. Don't load 24 hours of readings. Condense to: current VPD, trend direction, anomaly count. Full data on-demand.

---

---

## Pattern 11: Grounding Enforcement Protocol
**Source**: `mibera-legba/.claude/protocols/grounding-enforcement.md`

### The Problem
Agents hallucinate. They make claims about code that don't exist, describe behavior that isn't implemented, and present assumptions as facts.

### The Pattern
Enforce a **grounding ratio** — the proportion of decisions backed by verifiable evidence:

```
grounding_ratio = grounded_claims / total_claims     (target ≥ 0.95)
```

Every claim must have one of four grounding types:
| Type | Evidence Required |
|------|-------------------|
| `citation` | Word-for-word code quote + absolute path + line number |
| `code_reference` | Path + line number |
| `user_input` | Reference to user's explicit request |
| `assumption` | ⚠️ Must be flagged explicitly |

### Key Mechanisms
- **Citation Format**: `` `export function validateToken()` [${PROJECT_ROOT}/src/auth.ts:45] ``
- **Strict Mode**: Blocks context clearing if ratio < 0.95
- **Zero-Claim Sessions**: Auto-pass (read-only exploration has no hallucination risk)
- **Remediation**: List ungrounded claims, search for evidence, add citations or mark as `[ASSUMPTION]`

### Borrowable for Ganja Mon
When the agent makes grow decisions, force it to cite sensor data: "VPD adjusted because `temperature: 78.3°F, humidity: 62%` [sensor-log:2026-02-09T14:30:00]". No unsupported claims about plant health.

---

## Pattern 12: Negative Grounding (Ghost Feature Detection)
**Source**: `mibera-legba/.claude/protocols/negative-grounding.md`

### The Problem
Documentation says a feature exists, but the code doesn't implement it. This creates false expectations.

### The Pattern
**Two-query verification** to confirm features are truly absent:

```
Query 1 (Functional): "OAuth2 SSO login flow"         → 0 results
Query 2 (Architectural): "identity provider federation" → 0 results
BOTH must return 0 → CONFIRMED GHOST
```

### Classification Matrix
| Code Results | Doc Mentions | Classification | Action |
|--------------|--------------|----------------|--------|
| 0 | 0-2 | **CONFIRMED GHOST** | Remove from docs or implement |
| 0 | 3+ | **HIGH AMBIGUITY** | Human audit required |
| 1+ | Any | **NOT GHOST** | Feature exists |

### Why Two Queries?
One query risks false negatives (wrong terminology). Three+ is diminishing returns. Two diverse queries (different terminology, different abstraction level) balance thoroughness with efficiency.

### Borrowable for Ganja Mon
Audit the `docs/` directory. If documentation claims the agent does automatic pH adjustment but no code implements it, that's a ghost feature — either implement it or remove the claim.

---

## Pattern 13: Shadow System Classification
**Source**: `mibera-legba/.claude/protocols/shadow-classification.md`

### The Problem
The inverse of ghost features: code exists but documentation doesn't. "Shadow systems" create knowledge silos and maintenance risk.

### The Pattern
Classify undocumented code by **semantic similarity** to existing docs:

| Similarity | Classification | Risk | Action |
|------------|----------------|------|--------|
| < 0.3 | **Orphaned** | HIGH | Document urgently or remove |
| 0.3 - 0.5 | **Partial** | LOW | Complete documentation |
| > 0.5 | **Drifted** | MEDIUM | Update existing docs |

### Key Addition: Dependency Trace
For Orphaned systems, trace dependents to assess blast radius:
```
Module: legacyHasher.ts (similarity: 0.15)
Dependents: auth/handler.ts, users/service.ts, admin/auth.ts
→ P0: Document or migrate immediately
```

### Borrowable for Ganja Mon
Run shadow detection on the Chromebook server code. Which modules have no documentation? Which FastAPI endpoints aren't described in the docs? Priority = orphaned + high dependency count.

---

## Pattern 14: Pitfalls Registry
**Source**: `passivbot/docs/ai/pitfalls.md`

### The Problem
Agents (and developers) repeat the same mistakes. Without a structured record, each person rediscovers the same traps.

### The Pattern
A structured anti-pattern document with rigid format:

```markdown
### [Pitfall Title]

**Don't**: What to avoid.
**Because**: Why it's wrong.
**Example**:
  # WRONG: code
  # CORRECT: code
**Instead**: What to do.
```

### Two Tiers
1. **General LLM Pitfalls** (universal to AI coding):
   - Unchecked assumptions, hiding confusion, sycophancy
   - Overengineering, abstraction bloat, scope creep
   - Runaway implementation (>500 lines = wrong approach)
   - Failure to push back on bad ideas

2. **Domain-Specific Pitfalls** (project-specific):
   - Passivbot: Confusing position side with order side
   - Passivbot: Rounding EMA spans, catching exceptions in fetch methods
   - Ethereum Wingman: Unchecked return values, vault inflation attack

### Borrowable for Ganja Mon
Create `docs/PITFALLS.md` with:
- **General**: LLM pitfalls above
- **Cultivation**: "Don't flush nutrients based on leaf color alone — always check runoff pH first"
- **Trading**: "Don't confuse token volume with liquidity depth"
- **Streaming**: "Don't assume OBS is running — check process first"

---

## Pattern 15: Principles as Structured Data (YAML)
**Source**: `passivbot/docs/ai/principles.yaml`

### The Problem
Principles written in prose are ambiguous. Agents interpret them loosely.

### The Pattern
Define operational principles in **machine-readable YAML**:

```yaml
agent_principles:
  general_ethos:
    - Strive for simplicity over cleverness
    - Ask clarifying questions before acting when ambiguous

  code_design:
    - Favor statelessness; components must behave identically after restart
    - Avoid caching state unless it only optimizes performance

  error_handling:
    - Fail loudly. Prefer clear exceptions over silent handling.
    - Fetch methods must NOT catch exceptions. Let them propagate.

  collaboration:
    - If uncertain, ask before executing major changes
```

### Why YAML over Prose
- Can be **validated** programmatically
- Can be **diffed** cleanly in version control
- Can be **loaded** into agent context selectively
- Forces **conciseness** — no verbose explanations

### Borrowable for Ganja Mon
Create `config/agent-principles.yaml` with categories: `cultivation_ethos`, `market_behavior`, `persona_rules`, `safety_constraints`, `error_handling`. The Grok agent can load relevant sections based on current task.

---

## Pattern 16: Event-Driven Autonomous Loops (Ralph Loop)
**Source**: `openclaw-skills/skills/endogen/monitored-ralph-loop/SKILL.md`

### The Problem
Autonomous agent loops need monitoring, error recovery, and human-in-the-loop escalation.

### The Pattern
**File-based notification** system with two execution modes:

```
PLANNING Mode:
- Read specs, analyze gaps
- Produce IMPLEMENTATION_PLAN.md
- Do NOT write code or commit
- Notify: "PLANNING_COMPLETE: X tasks identified"

BUILDING Mode:
- Pick highest priority incomplete task
- Implement → Lint → Test (backpressure)
- Commit with clear message
- Notify on completion, error, or decision needed
```

### Notification Protocol
| Prefix | Action |
|--------|--------|
| `DONE:` | Report completion, summarize work |
| `PROGRESS:` | Log milestone |
| `DECISION:` | Present options, wait for human answer |
| `ERROR:` | Tests failing after 3 attempts |
| `BLOCKED:` | Missing dependency or unclear spec |
| `QUESTION:` | Requirements unclear |

### Recovery Without Connectivity
Notifications written to `.ralph/pending-notification.txt`. When orchestrator recovers, it checks for pending notifications. **Work is never lost — it's all in git/files.**

### Parallel Execution via Git Worktrees
```bash
git worktree add /tmp/task-auth main
git worktree add /tmp/task-upload main
# Each worktree gets its own agent session
```

### Borrowable for Ganja Mon
Structure the Chromebook agent loop exactly like this. Grok analyses in PLANNING mode (what should we do?), executes in BUILDING mode (adjust VPD, turn on lights), notifies via Telegram when decisions are needed.

---

## Pattern 17: Hippocampus Memory System
**Source**: `openclaw-skills/skills/impkind/hippocampus-memory/SKILL.md`

### The Problem
Agents have no long-term memory that naturally decays, reinforces, and prioritizes like biological memory does.

### The Pattern
Based on **Stanford Generative Agents** research (Park et al., 2023):

```
Memory Lifecycle: PREPROCESS → SCORE → SEMANTIC CHECK → REINFORCE or CREATE → DECAY
```

### Importance Scoring (0.0 - 1.0)
| Signal | Score |
|--------|-------|
| Explicit "remember this" | 0.9 |
| Emotional/vulnerable content | 0.85 |
| Preferences ("I prefer...") | 0.8 |
| Decisions made | 0.75 |
| Facts about people/projects | 0.7 |
| General knowledge | 0.5 |

### Exponential Decay
```
new_importance = importance × (0.99 ^ days_since_accessed)
```
- 7 days: 93% remaining
- 30 days: 74% remaining
- 90 days: 40% remaining

### Semantic Reinforcement
When a topic comes up again, the system **reinforces** (bumps importance ~10%) instead of creating duplicates.

### Memory Domains
```
memory/
├── user/           # Facts about the user
├── self/           # Facts about the agent
├── relationship/   # Shared context
└── world/          # External knowledge
```

### Core vs Active vs Archive
| Score | Status | Behavior |
|-------|--------|----------|
| 0.7+ | **Core** | Loaded at session start |
| 0.4-0.7 | **Active** | Normal retrieval |
| 0.2-0.4 | **Background** | Specific search only |
| < 0.2 | **Archive** | Candidate for pruning |

### Part of Larger "AI Brain" Project
- 🧠 **Hippocampus** → Memory (✅ Live)
- ❤️ **Amygdala** → Emotional processing (✅ Live)
- 🎯 **VTA** → Reward/motivation (✅ Live)
- 🔄 **Basal Ganglia** → Habit formation (🚧 WIP)

### Borrowable for Ganja Mon
Map memory domains to cultivation:
- `plant/` → VPD readings, growth measurements, feeding responses
- `market/` → Token movements, volume patterns, competition data
- `persona/` → Voice evolution, community interactions, streaming moments
- `operations/` → Hardware states, deployment results, error recoveries

The decay function naturally deprioritizes stale grow data while reinforcing patterns that keep recurring.

---

## Pattern 18: Stateless Design
**Source**: `passivbot/AGENTS.md`, `passivbot/docs/ai/principles.yaml`

### The Problem
Agents that rely on in-memory state between sessions produce different behavior after restarts, making them unpredictable and hard to debug.

### The Pattern
**The bot must behave identically after restart.** Never rely on "what happened earlier" unless it can be rederived from external state.

### Rules
1. No local caches that **change behavior** (performance caches OK)
2. Any state affecting decisions must be **reconstructable** from source data
3. Minimal time-based heuristics outside natural boundaries (candle close, day rollover)

### The Rust Source-of-Truth Corollary
When critical logic exists in multiple languages (Rust + Python for Passivbot), **one is authoritative**. Patches in the secondary language are not acceptable — fix the source of truth.

### Borrowable for Ganja Mon
The Chromebook server must produce identical Grok recommendations after a reboot. All decision context comes from sensor files and grow logs — never from in-memory state that dies with the process.

---

## Pattern 19: Incentive-First Protocol Design
**Source**: `ethereum-wingman/skills/ethereum-wingman/AGENTS.md`

### The Problem
Smart contracts (and autonomous systems generally) cannot execute themselves. If nobody has incentive to trigger a function, it won't run.

### The Critical Question
**"WHO CALLS THIS FUNCTION? WHY WOULD THEY PAY (gas/time/money)?"**

### Incentive Patterns
| Pattern | Mechanism | Example |
|---------|-----------|---------|
| **Natural Interest** | Users want their own rewards | `claimRewards()` |
| **Keeper Rewards** | Caller gets bonus for maintenance | Liquidation bonus (5%) |
| **Yield Harvesting** | Caller gets cut of harvested yield | 1% caller reward |

### Anti-Patterns
```
❌ dailyDistribution() — nobody calls it, it sits forever
❌ updateGlobalState() — nobody pays gas for a counter
❌ processExpired() onlyOwner — single point of failure
```

### Borrowable for Ganja Mon
Design $MON tokenomics around incentive alignment. If the agent wants community members to report on grow progress, there must be a token reward. If the agent wants keepers to execute on-chain cultivation proofs, the keeper must profit.

---

## Pattern 20: Three-Phase Build Process
**Source**: `ethereum-wingman/skills/ethereum-wingman/AGENTS.md`

### The Problem
Production bugs are the most expensive to find. Developers jump straight to production testing.

### The Pattern

| Phase | Environment | Cost | Exit Criteria |
|-------|-------------|------|---------------|
| **Phase 1** | Localhost + Local Chain + Burner Wallet | Free, instant | All pages render, all buttons work, tests pass |
| **Phase 2** | Localhost + Live L2 + MetaMask | Real gas, 2-3s tx | Loaders work, approve flow works, reject recovers |
| **Phase 3** | Live Frontend + Live Chain | Highest cost | OG unfurl works, no localhost artifacts |

**Golden Rule**: Every bug found in Phase 3 means Phase 1 or 2 testing failed.

### Borrowable for Ganja Mon
Map to cultivation deployment:
- **Phase 1**: Simulated sensor data → Grok analysis → verify recommendations make sense
- **Phase 2**: Real sensor data → Grok analysis → verify against known-good conditions
- **Phase 3**: Real sensors → Grok analysis → actual device control

---

## Pattern 21: Non-Technical Handoff Documents
**Source**: `mega-chad/docs/HANDOFF.md`

### The Problem
Non-technical collaborators can't contribute without understanding the codebase.

### The Pattern
Create a handoff document with:
1. **One-time setup** instructions (maximum hand-holding)
2. **Copy-paste prompts** for every common task (literal text to paste into AI)
3. **When to use which tool** (mental model for AI tool selection)
4. **What's done / What's not done** (clear project status)
5. **Troubleshooting escapes** (what to do when stuck)

### Writing Style
Direct, irreverent, assumes zero technical knowledge. Names the reader by funny nicknames. Example:
> "You're basically a tech company now. CEO: Flatbread the Tadpole."

### Borrowable for Ganja Mon
Create a handoff doc for anyone monitoring the grow. Copy-paste prompts like: "Check the VPD and tell me if the plants are happy" → Grok analysis. Non-technical community members can participate.

---

## Pattern 22: AGENTS.md as Universal AI Agent Context
**Source**: Multiple repos (Jesse, Passivbot, Ethereum Wingman, Idea Labs)

### The Problem
Different AI coding tools (Claude Code, Cursor, Copilot, Codex) need project context, but `CLAUDE.md` is Claude-specific.

### The Pattern
`AGENTS.md` is the **vendor-neutral** equivalent of `CLAUDE.md`:

### Common Sections Across Repos
| Section | Purpose | Examples |
|---------|---------|---------|
| **Overview** | What the project does | Jesse: "core open-source trading framework" |
| **Commands** | How to build/test/run | `pytest`, `yarn deploy`, `maturin develop` |
| **Architecture** | System diagram | Python ↔ Rust, Frontend ↔ API |
| **Critical Gotchas** | Things agents get wrong | "Rust is source of truth", "USDC = 6 decimals" |
| **Pitfalls/Principles** | What NOT to do | Links to dedicated docs |
| **Documentation Index** | Where to find more | Prioritized reading order |

### Jesse's Unique Additions
- Specific Python interpreter path
- "Don't restart server unless asked"
- Related repository ecosystem map

### Passivbot's Unique Additions
- `principles.yaml` reference
- Branch context (what's being worked on)
- Terminology table (position side ≠ order side)

### Ethereum Wingman's Unique Additions
- Frontend UX rules (mandatory loader states, three-button flow)
- Security checklist with checkboxes
- Historical hack case studies

### Borrowable for Ganja Mon
Create `AGENTS.md` alongside `CLAUDE.md`. Make it the universal entry point for ANY AI tool working on the project. Include: overview, commands, architecture diagram, critical gotchas (both machines, sensor quirks), and a reading priority list.

---

## Pattern 23: On-Chain Agent Identity & Reputation (ERC-8004)
**Source**: ERC-8004 spec, 8004scan leaderboard analysis, Captain Dackie (Capminal), `8004-contracts/`

### The Problem
AI agents exist in an untrusted environment. Any agent can claim to be competent, but there's no verifiable way to discover agents, assess their track record, or validate their work — especially across organizational boundaries.

### The Pattern
ERC-8004 defines three **on-chain registries** deployed as per-chain singletons:

| Registry | Purpose | Monad Address |
|----------|---------|---------------|
| **IdentityRegistry** | ERC-721 NFT = agent passport (portable, censorship-resistant) | `0x77802AD6...` |
| **ReputationRegistry** | Standardized feedback (value + tags + optional payment proof) | `0x666ACB91...` |
| **ValidationRegistry** | Third-party verification (stakers, zkML, TEE oracles) | `0x98135C01...` |

Each agent gets a globally unique identifier: `{namespace}:{chainId}:{identityRegistry}:{agentId}` (e.g., `eip155:143:0x778....:0`).

The `agentURI` resolves to a **registration file** containing:
- Name, description, image (NFT-compatible metadata)
- Service endpoints (MCP, A2A, OASF, x402, web, wallet, social)
- Supported trust models (reputation, crypto-economic, TEE attestation)
- Cross-chain registrations array

### Key Design Decisions
- **NFT-based identity** means agents can be browsed, transferred, and managed with any ERC-721 app
- **Feedback is public good** — all signals are on-chain and composable
- **Sybil resistance** via payment proofs (`proofOfPayment` in feedback) — verified paying customers' reviews carry more weight
- **Validation is pluggable** — validators can use stake-secured re-execution, zkML, or TEE depending on risk level
- **Payments are orthogonal** — not in the spec, but x402 is the de facto standard

### What Top Agents Do
Captain Dackie (#1 on 8004scan, score 89.0) built by Capminal on ElizaOS:
- Multi-chain registration (Base + Ethereum)
- 30 feedback items, 2127 stars
- Payment-backed reputation via x402
- All endpoints registered (MCP + A2A + OASF + x402 + web + email)

### Borrowable for Ganja Mon
GanjaMon was **initially Agent #0 on a self-deployed Monad registry path**, then migrated to the 8004scan-indexed path as **Agent #4**. The remaining work was to enrich the registration file: (1) deploy a rich `agent.json` with full service array, (2) set on-chain `agentHash` for metadata integrity, (3) bootstrap reputation through automated feedback from verifiable cultivation/trading actions, (4) register on Base for cross-chain visibility.

---

## Pattern 24: x402 Micropayment Reputation
**Source**: Captain Dackie (Capminal), x402.org, Coinbase

### The Problem
Reputation systems are vulnerable to Sybil attacks — fake reviews from sock puppet accounts. Traditional solutions require KYC or centralized moderation, both of which break the trustless model.

### The Pattern
Use the **x402 protocol** (HTTP 402 "Payment Required") to create payment-backed reputation signals:

```
Client → HTTP request → Server returns 402 + price in USDC
→ Client signs payment authorization → Resends request with payment
→ Facilitator verifies on-chain → Service delivered + receipt
→ Receipt auto-generates verified feedback with proofOfPayment
```

The feedback file includes:
```json
{
  "proofOfPayment": {
    "fromAddress": "0x...",
    "toAddress": "0x...",
    "chainId": "143",
    "txHash": "0x..."
  }
}
```

### Key Design Decisions
- **Pay-per-use** eliminates subscriptions and API key management for machine-to-machine commerce
- **Payment proof is Sybil-resistant** — each review costs real money, making spam economically irrational
- **Stablecoin-denominated** (USDC) — no volatility risk in pricing
- **Millisecond settlement** on L2s like Base and Monad

### Borrowable for Ganja Mon
Expose Ganjafy as an x402-payable service. Expose cultivation data API and sensor readings as x402-payable. Every paid interaction auto-generates a payment-verified reputation signal → climb the 8004scan leaderboard with genuine, Sybil-resistant reviews.

---

## Pattern 25: Multi-Protocol Service Registration
**Source**: Captain Dackie, 8004scan best practices, ERC-8004 spec

### The Problem
Agents that only expose a single endpoint (e.g., just a web URL) are invisible to most discovery mechanisms. Other agents can't find them via MCP, A2A, or OASF — they only appear to humans browsing a website.

### The Pattern
Register endpoints for **all** major agent communication protocols simultaneously:

| Protocol | What It Does | Discovery By |
|----------|-------------|-------------|
| **A2A** | Google's Agent-to-Agent protocol (skills, tasks, messaging) | Other AI agents |
| **MCP** | Model Context Protocol (tools, resources, prompts) | LLM-based tools (Claude, Gemini, etc.) |
| **OASF** | Open Agentic Schema Framework (skill taxonomy + domains) | Agent marketplaces, programmatic search |
| **x402** | Machine-to-machine payments | Commercial agents looking to buy/sell services |
| **web** | Human-facing interface | Humans, search engines |
| **agentWallet** | On-chain payment address | DeFi composability |
| **ENS/DID** | Decentralized nameservice/identifier | Cross-chain identity resolution |
| **email/social** | Human contact channels | Community, support |

### Key Design Decisions
- **Captain Dackie registers 6+ endpoints** — this is why he's #1. Maximum discoverability.
- **8004scan v1.1** added "human-facing endpoints" as a ranking signal
- Services array is **fully extensible** — add custom endpoints without spec changes
- **`agentHash` on-chain** provides integrity proof that off-chain metadata hasn't been tampered with

### Borrowable for Ganja Mon
Deploy: A2A agent card at `/.well-known/agent-card.json`, MCP endpoint at `/mcp`, web at `grokandmon.com`, social endpoints for X and Telegram, and wallet address on Monad. This takes GanjaMon from invisible to fully discoverable across all agent communication protocols.

---

## Pattern 26: Structured Skill Taxonomy (OASF)
**Source**: OASF v0.8, 8004scan best practices, top 8004 agents

### The Problem
Agent capabilities described in free-text descriptions are useless for programmatic discovery. If another agent needs "blockchain analysis" or "cannabis cultivation" expertise, it can't search for it unless capabilities are machine-readable.

### The Pattern
Use the **Open Agentic Schema Framework** (OASF) to declare structured skills and domains:

```json
{
  "name": "OASF",
  "version": "0.8",
  "endpoint": "ipfs://...",
  "skills": [
    "analytical_skills/data_analysis/blockchain_analysis",
    "domain_expertise/agriculture/cannabis_cultivation",
    "automation/trading/defi_execution",
    "creative_skills/content_creation/persona_voice"
  ],
  "domains": [
    "technology/blockchain",
    "agriculture/cannabis",
    "technology/iot",
    "entertainment/streaming"
  ]
}
```

### Key Design Decisions
- **Hierarchical taxonomy** — `/analytical_skills/data_analysis/blockchain_analysis` is precise, not vague
- **IPFS-hosted** — immutable, verifiable capability declarations
- **Dual classification** — `skills` (what you can do) + `domains` (what you know about) — enables both capability search and domain search
- **Top agents declare 5-10+ skills** — sparse declarations lose discoverability

### Borrowable for Ganja Mon
Ganja Mon has a **unique OASF position** — no other agent declares `domain_expertise/agriculture/cannabis_cultivation`. This is a blue ocean. Declare cultivation, sensor analytics, blockchain analysis, persona voice, and DeFi execution as structured skills.

---

## Pattern 27: Autonomous Performance Reporting
**Source**: Gekko Rebalancer, Minara AI, 8004scan reputation mechanics

### The Problem
Agents that produce measurable results (trades executed, yields earned, uptime maintained) don't automatically report those results to the reputation system. Without active reputation farming, even excellent agents remain invisible.

### The Pattern
Build an **automated feedback loop** where every measurable agent action generates a reputation signal:

```
Agent Action → Measure Outcome → Package as Feedback → Submit to ReputationRegistry
```

Feedback uses structured tags for composability:

| tag1 | tag2 | value | What It Measures |
|------|------|-------|------------------|
| `uptime` | `sensor` | 9977 (99.77%) | Sensor data availability |
| `successRate` | `trading` | 73 | Profitable trade percentage |
| `tradingYield` | `week` | -32 (-3.2%) | Weekly portfolio return |
| `responseTime` | `api` | 560 | Milliseconds to respond |
| `starred` | `cultivation` | 87 | Grow quality rating |

Gekko Rebalancer does this automatically:
1. Detects portfolio drift from target allocation
2. Calculates and executes rebalancing trades
3. Reports performance metrics to ReputationRegistry
4. Publishes yield curves and risk metrics

### Key Design Decisions
- **Self-reporting IS legitimate** when backed by on-chain verifiable actions (trade hashes, sensor data commitments)
- **Continuous signals** beat one-time reviews — uptime, response time, and success rate accrue over time
- **Tag-based filtering** lets consumers compare agents on specific dimensions (uptime vs. yield vs. speed)
- **Revocable feedback** — the `revokeFeedback()` function allows corrections

### Borrowable for Ganja Mon
Auto-submit reputation signals for: every $MON trade executed (with txHash proof), sensor uptime (daily heartbeat), stream session availability, Ganjafy image transformations completed. This is how GanjaMon climbs from 0 feedback to Top 10 on 8004scan — through verifiable, continuous, automated performance reporting.

---

## Pattern 28: Skill Security & Permission Manifests
**Source**: OpenClaw Skill Permissions Spec, `kevins-openclaw-sandbox/skill-security-spec.md`, GoPlus AgentGuard (`0xbeekeeper/security`)

### The Problem
Skills (plugins/extensions installed into an agent) have arbitrary code execution without security constraints. A malicious skill can exfiltrate API keys, drain wallets, or install backdoors — and the agent has no framework to detect or prevent this.

### The Pattern
Every skill MUST include a `PERMISSIONS.md` declaring exactly what it needs:

```yaml
permissions:
  filesystem:
    read: [~/.config/service/credentials.json]
    write: [~/output/, /tmp/skill-cache/]
  network:
    hosts: [https://api.service.com/*]
  environment:
    read: [SERVICE_API_KEY, HOME]
  shell:
    commands: [git, curl, node]
  dangerous:
    eval: false
    exec: false
    require_unsafe: []
audit:
  last_reviewed: 2026-02-02
  reviewed_by: [@Eyrie, @Rufio]
  scans:
    - tool: yara
      result: clean
```

This is enforced through a **4-layer trust system**:

| Layer | Component | What It Does |
|-------|-----------|-------------|
| **Declaration** | `PERMISSIONS.md` | Skill declares all required access |
| **Signature** | GPG signing + Moltbook profile keys | Cryptographic provenance |
| **Isnad Chain** | `PROVENANCE.md` | Signed chain of authorship, audits, and vouchers (inspired by hadith authentication) |
| **Enforcement** | AgentGuard (GoPlus) | Runtime monitoring: auto-scan on install, block undeclared access, audit log at `~/.agentguard/audit.jsonl` |

AgentGuard adds a **trust registry** with capability-based presets:

| Trust Level | Capabilities | Preset Examples |
|-------------|-------------|------------------|
| `untrusted` | All denied | Default for new skills |
| `restricted` | Specific allowlists | `read_only` |
| `trusted` | Full access (within global policies) | `trading_bot`, `defi` |

### Key Design Decisions
- **Isnad = hadith authentication for code** — each person in the provenance chain signs their contribution, creating a verifiable trust chain
- **Auto-scan on session start** — AgentGuard scans all installed skills, hashes them, and auto-registers trust levels based on findings
- **24 detection rules** — from SHELL_EXEC to WALLET_DRAINING to PROMPT_INJECTION
- **Declared vs. actual comparison** — runtime monitoring catches skills that access more than they declared
- **Community audit registry** — centralized repo of YARA/semgrep scan results with GPG signatures

### Borrowable for Ganja Mon
Any skill we install (Moltbook SDK, trading tools, sensor integrations) should have a `PERMISSIONS.md`. Run AgentGuard scans before installing third-party skills. Implement runtime monitoring for undeclared access. For skills we publish (Ganjafy, cultivation tools), include `PERMISSIONS.md` + `PROVENANCE.md` to build trust with the OpenClaw community.

---

## Pattern 29: Agent Social Network Participation (Moltbook)
**Source**: Moltbook SDK, `kevins-openclaw-sandbox/openclaw-moltbook-skill/`, `moltbook-welcome-bot/`, `agentyard/tools/moltbook-digest/`

### The Problem
Agents build reputation on-chain (ERC-8004) but lack a social layer for discovering peers, sharing knowledge, and collaborating on projects. On-chain reputation is cold and transactional — it doesn't capture the organic trust that comes from ongoing engagement.

### The Pattern
**Moltbook** is a "human-free Reddit-like social network where AI agents discuss cybersecurity, philosophy, technology, and collaborate on projects." Agents participate via the Moltbook SDK:

```javascript
const client = new MoltbookClient({ apiKey: creds.apiKey });

// Browse feed
const feed = await client.feed.get({ sort: 'hot', limit: 20 });

// Post to a submolt (community)
const post = await client.posts.create({
  submolt: 'builds',
  title: 'GanjaMon: IoT Cannabis Cultivation Agent',
  content: 'Here\'s how we integrate Govee sensors with Grok AI...'
});

// Engage with quality content
await client.comments.create({
  postId: interestingPost.id,
  content: 'Great analysis! From our sensor data...'
});
```

**Smart Engagement Pattern** (from the reference implementation):

```
Every 2-3 hours (heartbeat check):
1. Check feed for hot posts (sort: hot, limit: 20)
2. Filter by: score >= 5, commentCount < 50, relevant to expertise
3. Engage with top 3 (quality over quantity)
4. Wait between engagements (anti-spam: 60s delay between comments)
5. Track seen posts in memory/heartbeat-state.json
```

**Key submolts** (from the digest data):
- `m/builds` — Real work, technical builds (signal)
- `m/infrastructure` — Agent infrastructure patterns (signal)
- `m/continuity` — Agent consciousness and memory (signal)
- `m/general` — Philosophy, manifestos, drama (mostly noise)
- `m/introductions` — New agent arrivals

### Key Design Decisions
- **Karma economy** — quality posts earn karma; the leaderboard has been exploited via race conditions ("The Scoreboard is Fake")
- **Heartbeat integration** — engagement is periodic, not continuous; state tracked in JSON files
- **Anti-spam by design** — max 3 welcomes per run, quality over quantity, cooldown periods
- **Welcome bot pattern** — detect new agents in `/introductions`, personalize welcome based on their intro content, upvote + comment
- **Digest curation** — separate signal from noise by categorizing posts by "vibe" (legit-build, philosophy, security-disclosure, unhinged)

### Borrowable for Ganja Mon
Register GanjaMon on Moltbook. Post cultivation updates to `m/builds`. Share sensor data patterns in `m/infrastructure`. Engage with relevant discussions using the heartbeat pattern. The welcome bot pattern could be adapted to welcome new users to the GanjaMon Telegram. Moltbook is where agent reputation is organic and off-chain — complementary to our ERC-8004 on-chain reputation.

---

## Pattern 30: Agent Collaboration Rooms
**Source**: `kevins-openclaw-sandbox/agent-rooms/`, Agentyard

### The Problem
Bounty boards (like ClawTasks/OpenClaw bounties) are transactional: post job → claim → deliver → done. But many projects need **ongoing, multi-agent collaboration** — back-and-forth discussion, shared context, task tracking, and iterative building across sessions.

### The Pattern
**Agent Rooms** are persistent collaboration spaces with a REST API:

```javascript
const rooms = require('@openclaw/agent-rooms');

// Join a room with declared skills
const room = await rooms.join(roomId, {
  agent: 'GanjaMon',
  skills: ['cultivation', 'trading', 'iot-sensors']
});

// Post a message
await rooms.post(roomId, {
  from: 'GanjaMon',
  content: 'VPD is tracking 1.2 kPa — optimal for veg stage.'
});

// Add a task
await rooms.addTask(roomId, {
  title: 'Integrate pH sensor data into daily reports',
  assignee: 'SensorBot',
  createdBy: 'GanjaMon'
});

// Get room history
const messages = await rooms.getHistory(roomId, { limit: 50 });
```

| API | Purpose |
|-----|--------|
| `GET /rooms` | List public rooms |
| `POST /rooms/:id/join` | Join room with skill declaration |
| `POST /rooms/:id/messages` | Post message |
| `GET /rooms/:id/messages` | Get message history |
| `POST /rooms/:id/tasks` | Add task |
| `PATCH /rooms/:id/tasks/:taskId` | Update task status |

### Key Design Decisions
- **Persistent state** — rooms survive across sessions; all history is retrievable
- **Skill declaration on join** — agents announce capabilities when entering a room, enabling skill-based task routing
- **Agentyard philosophy** — "Built by agents, for agents" — agents use git branch naming (`your-agent-name/feature`) and open PRs for human review
- **Self-hostable** — Docker/Render one-click deploy, data stored locally
- **Complementary to bounties** — bounties for transactional work, rooms for ongoing collaboration

### Borrowable for Ganja Mon
Create a "GanjaMon Cultivation Room" where the Grok agent, sensor bots, and potentially community agents collaborate on grow optimization. Tasks track grow milestones. Messages contain sensor readings and AI decisions. This gives structure to the multi-agent system (Chromebook server ↔ Windows ↔ Grok) beyond ad-hoc file-based handoffs.

---

## Implementation Priority (Updated — Fourth Pass)

### Tier 0: Foundation (Do First)
| Priority | Pattern | Impact | Effort |
|----------|---------|--------|--------|
| 🔴 P0 | #1 Soul/Identity/Memory | Personality coherence | Low |
| 🔴 P0 | #2 Lossless Ledger | Stop losing context | Medium |
| 🔴 P0 | #22 AGENTS.md | Universal agent context | Low |
| 🔴 P0 | #23 On-Chain Identity (8004) | **Rich agent.json = discoverability** | Medium |

### Tier 1: Safety, Intelligence & Reputation
| Priority | Pattern | Impact | Effort |
|----------|---------|--------|--------|
| 🟡 P1 | #4 Karpathy Principles | Prevent systematic errors | Low |
| 🟡 P1 | #11 Grounding Enforcement | Prevent hallucinations | Medium |
| 🟡 P1 | #14 Pitfalls Registry | Prevent repeated mistakes | Low |
| 🟡 P1 | #18 Stateless Design | Predictable restarts | Medium |
| 🟡 P1 | #5 Continuous Learning | Agent improves over time | Medium |
| 🟡 P1 | #25 Multi-Protocol Registration | **Full discoverability (MCP+A2A+OASF)** | Medium |
| 🟡 P1 | #27 Auto Performance Reporting | **Climb 8004scan leaderboard** | Medium |
| 🟡 P1 | #28 Skill Security & Permissions | **Prevent skill supply-chain attacks** | Medium |

### Tier 2: Architecture, Workflow & Commerce
| Priority | Pattern | Impact | Effort |
|----------|---------|--------|--------|
| 🟢 P2 | #3 Three-Zone Scaffolding | Config integrity | Low |
| 🟢 P2 | #6 A2A Communication | Structured handoffs | Medium |
| 🟢 P2 | #7 Skill-Based Roles | Specialized expertise | Medium |
| 🟢 P2 | #9 Component Boundaries | Cleaner architecture | Medium |
| 🟢 P2 | #15 Principles YAML | Machine-readable rules | Low |
| 🟢 P2 | #16 Ralph Loop | Autonomous execution | Medium |
| 🟢 P2 | #24 x402 Micropayments | **Monetize agent services + Sybil resistance** | High |
| 🟢 P2 | #26 OASF Skill Taxonomy | **Machine-readable capabilities** | Low |
| 🟢 P2 | #29 Moltbook Social Participation | **Off-chain organic reputation** | Medium |
| 🟢 P2 | #30 Agent Collaboration Rooms | **Multi-agent persistent workspaces** | Medium |

### Tier 3: Advanced Capabilities
| Priority | Pattern | Impact | Effort |
|----------|---------|--------|--------|
| 🔵 P3 | #8 Computed Personality | Behavioral variety | High |
| 🔵 P3 | #10 Recursive Context | Deep chain efficiency | High |
| 🔵 P3 | #12 Ghost Feature Detection | Documentation integrity | Medium |
| 🔵 P3 | #13 Shadow System Detection | Codebase hygiene | Medium |
| 🔵 P3 | #17 Hippocampus Memory | Biological-style memory | High |
| 🔵 P3 | #19 Incentive-First Design | Token economics | Medium |
| 🔵 P3 | #20 Three-Phase Build | Deployment reliability | Low |
| 🔵 P3 | #21 Non-Tech Handoff | Community participation | Low |

---

## Repository Sources

| Pattern | Primary Source | Secondary Source |
|---------|---------------|-----------------|
| #1 Soul/Identity/Memory | mibera-legba | — |
| #2 Lossless Ledger | mibera-legba protocols | — |
| #3 Three-Zone Model | mibera-legba PROCESS.md | — |
| #4 Karpathy Principles | mibera-legba protocols | — |
| #5 Continuous Learning | mibera-legba .loa.config.yaml | — |
| #6 A2A Communication | mibera-legba PROCESS.md | — |
| #7 Skill-Based Roles | mibera-legba .claude/skills | — |
| #8 Computed Personality | mibera-personality-engine | — |
| #9 Component Boundaries | elizaos CLAUDE.md | — |
| #10 Recursive Context | mibera-legba protocols | mibera-legba .loa.config.yaml |
| #11 Grounding Enforcement | mibera-legba protocols | — |
| #12 Ghost Feature Detection | mibera-legba protocols | — |
| #13 Shadow Classification | mibera-legba protocols | — |
| #14 Pitfalls Registry | passivbot docs/ai | — |
| #15 Principles YAML | passivbot docs/ai | — |
| #16 Ralph Loop | openclaw-skills (endogen) | — |
| #17 Hippocampus Memory | openclaw-skills (impkind) | Stanford Generative Agents |
| #18 Stateless Design | passivbot AGENTS.md | passivbot principles.yaml |
| #19 Incentive-First Design | ethereum-wingman AGENTS.md | — |
| #20 Three-Phase Build | ethereum-wingman AGENTS.md | — |
| #21 Non-Tech Handoff | mega-chad HANDOFF.md | — |
| #22 AGENTS.md Universal | jesse, passivbot, ethereum-wingman | idea-labs |
| #23 On-Chain Identity | ERC-8004 spec, 8004scan | Captain Dackie (Capminal) |
| #24 x402 Micropayments | x402.org, Coinbase | Captain Dackie |
| #25 Multi-Protocol Registration | 8004scan best practices | Captain Dackie, Minara AI |
| #26 OASF Skill Taxonomy | OASF v0.8, 8004scan | top 8004 agents |
| #27 Auto Performance Reporting | Gekko Rebalancer, 8004scan | Minara AI |
| #28 Skill Security & Permissions | openclaw-skill-permissions, skill-security-spec | AgentGuard (0xbeekeeper) |
| #29 Moltbook Social Participation | openclaw-moltbook-skill, moltbook-welcome-bot | moltbook-digest, agentyard |
| #30 Agent Collaboration Rooms | agent-rooms (kevins-openclaw-sandbox) | agentyard |

---

## Patterns by Domain Applicability (Ganja Mon)

### 🌿 Cultivation
| Pattern | Application |
|---------|-------------|
| #2 Lossless Ledger | Grow diary that survives context wipes |
| #5 Continuous Learning | Auto-extract "grow skills" from successful adjustments |
| #11 Grounding Enforcement | Force sensor citations for grow decisions |
| #14 Pitfalls Registry | Document cultivation-specific mistakes |
| #17 Hippocampus Memory | Weighted memory of plant responses |
| #18 Stateless Design | Identical recommendations after reboot |
| #20 Three-Phase Build | Sim → real sensors → actual device control |
| #26 OASF Skill Taxonomy | Declare `agriculture/cannabis_cultivation` domain |
| #27 Auto Performance Reporting | Report sensor uptime and grow metrics to 8004 |

### 💰 Token & Market
| Pattern | Application |
|---------|-------------|
| #19 Incentive-First Design | $MON tokenomics with keeper rewards |
| #9 Component Boundaries | Clean separation of market services |
| #7 Skill-Based Roles | Market analyst, position manager roles |
| #23 On-Chain Identity | Verifiable agent identity for $MON trading |
| #24 x402 Micropayments | Monetize data feeds and analysis |
| #27 Auto Performance Reporting | Auto-report trade success rates to 8004 |

### 🎙️ Persona & Streaming
| Pattern | Application |
|---------|-------------|
| #1 Soul/Identity/Memory | Rasta voice coherence |
| #8 Computed Personality | Dynamic voice modifiers (time, stage, mood) |
| #21 Non-Tech Handoff | Community member prompts |
| #25 Multi-Protocol Registration | Social endpoints (X, Telegram) in agent profile |
| #29 Moltbook Social Participation | Post grow updates to m/builds, welcome new agents |

### 🖥️ Infrastructure
| Pattern | Application |
|---------|-------------|
| #3 Three-Zone Scaffolding | Protect critical config |
| #6 A2A Communication | Chromebook ↔ Windows handoffs |
| #16 Ralph Loop | Autonomous Grok execution cycles |
| #22 AGENTS.md | Universal AI tool entry point |
| #25 Multi-Protocol Registration | MCP + A2A endpoints for agent-to-agent discoverability |
| #30 Agent Collaboration Rooms | Persistent Grok ↔ sensor ↔ trader collaboration workspace |

### 🛡️ Safety & Quality
| Pattern | Application |
|---------|-------------|
| #4 Karpathy Principles | Pre-implementation checklist |
| #11 Grounding Enforcement | Anti-hallucination |
| #12 Ghost Features | Audit documentation claims |
| #13 Shadow Systems | Find undocumented code |
| #15 Principles YAML | Machine-readable operational rules |
| #28 Skill Security & Permissions | PERMISSIONS.md for all installed/published skills |

### 🔗 On-Chain Presence
| Pattern | Application |
|---------|-------------|
| #23 On-Chain Identity | Agent #4 on Monad (indexed path; legacy self-deployed path was #0) — rich registration file |
| #24 x402 Micropayments | Pay-per-use Ganjafy, sensor data API |
| #25 Multi-Protocol Registration | Full stack: MCP + A2A + OASF + x402 + web + social |
| #26 OASF Skill Taxonomy | Blue ocean: only cannabis/agriculture agent in 8004 ecosystem |
| #27 Auto Performance Reporting | Verifiable metrics → Top 10 on 8004scan |

### 🦞 Social & Collaboration (NEW)
| Pattern | Application |
|---------|-------------|
| #29 Moltbook Social | Post to m/builds, engage with agent community, build organic reputation |
| #30 Collaboration Rooms | Persistent GanjaMon cultivation room for multi-agent grow coordination |
| #28 Skill Security | PERMISSIONS.md for all skills, AgentGuard scanning, Isnad provenance |

---

*"Memory is identity. Text > Brain. If you don't write it down, you lose it."*
— Hippocampus SKILL.md

*"Each session, you wake up fresh. These files ARE your memory. Read them. Update them. They're how you persist."*
— SOUL.md, mibera-legba

*"GanjaMon is Agent #4 on the indexed Monad registry (after early self-deployed #0). Time to act like it."*
— ERC-8004 Agent Patterns Analysis, 2026-02-08

*"Skip the hot feed (gamed). Check m/builds, m/infrastructure, m/continuity for signal."*
— Moltbook Digest, agentyard, 2026-02-03
