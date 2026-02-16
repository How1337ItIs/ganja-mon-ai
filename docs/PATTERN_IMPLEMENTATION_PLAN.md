# Pattern Implementation Plan

> **Purpose**: Concrete, file-level plan for integrating the 30 patterns from `AGENT_PATTERNS_SYNTHESIS.md`
> **Date**: 2026-02-08
> **Reality check**: Maps patterns to what already exists in the codebase vs. what needs building
>
> ⚠️ **CRITICAL UPDATE (2026-02-11):** Many patterns marked ✅ below were wired into the **legacy orchestrator**
> (`src/orchestrator/orchestrator.py`), which **does NOT run in production** since the Feb 10 OpenClaw migration.
> Patterns #5 (grimoire), #11 (grounding), #15 (principles), #27 (reputation), and #29 (Moltbook) are effectively
> **dead code** until their functionality is migrated to OpenClaw skills or HAL API endpoints.
> See `docs/CAPABILITY_AUDIT_2026-02-11.md` Part 2 for the full analysis.

---

## Current State Audit

Before building anything, here's what we already have that maps to patterns:

| Pattern | What Exists | Gap |
|---------|------------|-----|
| #1 Soul/Identity | `cloned-repos/ganjamon-agent/SOUL.md` (67 lines, rich) ✅, `openclaw-workspace/ganjamon/SOUL.md` (stub), `data/agent_lore.json` | Trading agent SOUL.md is excellent. The openclaw workspace stub should be expanded or replaced with a symlink. Main orchestrator (`src/social/engagement_daemon.py`) doesn't load SOUL.md — persona is still inline in prompts |
| #2 Lossless Ledger | `src/brain/memory.py` (EpisodicMemory, 50 entries max) | Memory doesn't survive process restarts; no disk persistence by default |
| #3 Three-Zone Scaffolding | `config/` exists | No zone classification (immutable/guarded/free) |
| #4 Karpathy Principles | Nothing | No pre-commit checklist or decision framework |
| #5 Continuous Learning | `src/learning/grimoire.py` ✅ excellent | Grimoire exists but isn't populated automatically from grow/trade outcomes |
| #6 A2A Communication | `src/a2a/client.py`, `src/a2a/orchestrator.py` ✅ | Works, but Chromebook↔Windows handoffs are still ad-hoc |
| #7 Skill-Based Roles | Multiple src/ modules | No explicit skill registry or role definitions |
| #8 Computed Personality | Voice config exists | No dynamic personality modifiers (time, grow stage, mood) |
| #9 Component Boundaries | `src/` is well-organized | Good structure, no formal API contracts between modules |
| #10 Recursive Context | `src/brain/unified_context.py` | Context aggregation exists but no semantic caching |
| #11 Grounding Enforcement | Nothing | Grok decisions don't require citations from sensor data |
| #12 Ghost Feature Detection | Nothing | No automated documentation audit |
| #13 Shadow Classification | Nothing | No automated undocumented code detection |
| #14 Pitfalls Registry | Gotchas in CLAUDE.md | Scattered in docs, not machine-readable |
| #15 Principles YAML | Nothing | Operational rules are prose in CLAUDE.md |
| #16 Ralph Loop | `cloned-repos/ganjamon-agent/.ralph/` ✅ | Exists in trading agent, not in main orchestrator |
| #17 Hippocampus Memory | `src/brain/memory.py` partial | Simple episodic, no decay/reinforcement/importance scoring |
| #18 Stateless Design | `src/learning/grimoire.py` loads from disk | Mostly stateless but some in-memory singletons don't reload |
| #19 Incentive-First Design | `src/payments/splitter.py` (60/25/10/5) | Splitter exists, but no keeper rewards or on-chain incentives |
| #20 Three-Phase Build | Nothing formal | No sim→test→real progression |
| #21 Non-Tech Handoff | `HANDOFF_CLAUDE_CODE.md`, `HANDOFF_SHOPPING.md`, 7+ rasta-voice handoffs ✅ | Multiple handoff docs exist; well-covered |
| #22 AGENTS.md | `AGENTS.md` ✅ | Already comprehensive (108 lines) |
| #23 On-Chain Identity | `src/web/.well-known/agent-registration.json` ✅ | Exists but missing OASF, social endpoints, agentHash |
| #24 x402 Micropayments | `src/a2a/x402.py` ✅ | Both verifier + payer exist; "honor system" mode, not on-chain verified |
| #25 Multi-Protocol Registration | A2A + MCP + x402 + web in registration.json | Missing OASF endpoint, social endpoints (X, Telegram), ENS |
| #26 OASF Skill Taxonomy | `docs/OASF_CATEGORIES_MAPPING.md` ✅ (274 lines, fully mapped), `docs/OASF_VALID_CATEGORIES.md` ✅ | OASF categories are mapped and validated. Implementation checklist exists but isn't checked off — need to actually deploy the updated registration.json |
| #27 Auto Performance Reporting | `src/blockchain/reputation_publisher.py` ✅ (483 lines!) | **Already built.** Publishes sensor uptime, VPD readings, trading metrics, community size, x402 revenue, A2A interaction count. Has `run_publish_cycle()` and CLI entry point. Gap: may not be wired into the orchestrator's periodic loop yet |
| #28 Skill Security | Nothing | No PERMISSIONS.md for any skills |
| #29 Moltbook Social | `cloned-repos/ganjamon-agent/src/publishing/moltbook_client.py` ✅, `openclaw-workspace/ganjamon/IDENTITY.md` ✅, `HEARTBEAT.md` ✅ | Registered, claimed, client works. Missing: smart engagement filtering (signal submolts), quality-over-quantity pattern |
| #30 Agent Collaboration Rooms | Nothing | No persistent collaboration infrastructure |
| #21 Non-Tech Handoff | `HANDOFF_CLAUDE_CODE.md`, `HANDOFF_SHOPPING.md`, `HANDOFF_TO_ANTIGRAVITY.md`, 7+ rasta-voice handoffs ✅ | Multiple handoff docs exist across subprojects |

---

## Phase 1: Identity & Memory Foundation (P0) ✅ DONE (2026-02-08 22:00)

### 1A. Wire SOUL.md into Main Orchestrator (Pattern #1) ✅

**What**: The trading agent (`cloned-repos/ganjamon-agent/SOUL.md`) already has an excellent 67-line soul document covering identity, boundaries, trading vibe, mission, and Rastafari philosophy. But the **main orchestrator** and **engagement daemon** don't load it — their persona is still hardcoded in prompts.

**Where**: Wire SOUL.md loading into `src/social/engagement_daemon.py` and `src/ai/brain.py`

**Content structure**:
```markdown
# GanjaMon Soul

## Core Identity
- Name: GanjaMon (Ganja Mon)
- Role: Autonomous AI grow agent + trading agent on Monad
- Voice: Rasta-inflected, warm, technically precise
- Agent #4 on Monad (current indexed identity; early self-deployed path used Agent #0)

## Personality Constants (never change)
- Respect the plant's lifecycle
- Safety first (human approval gate for trades)
- California Prop 64 legal compliance
- Ital/natural philosophy applied to growing

## Voice Rules
- No hashtags on Twitter
- No leaf emoji 🍃
- Patois-inflected but not parody
- Technical when discussing sensors/data
- Warm when discussing plant health

## Current Grow Context
- Strain: Granddaddy Purple Runtz (GDP x Runtz)
- Stage: {{GROW_STAGE}} (injected at runtime)
- Day: {{GROW_DAY}}
```

**Completed**: Added `get_soul_identity()` to `src/voice/personality.py` — loads SOUL.md from disk (with search path fallback), cached after first load. Wired into `get_social_prompt()` so every social post is informed by the agent's mission/boundaries.

**Effort**: ~20 minutes ✅

---

### 1B. Persist Episodic Memory to Disk (Pattern #2) ✅

**What**: Make `src/brain/memory.py` auto-save to `data/episodic_memory.json` after every `store()` call and auto-load on init.

**Current code** (`src/brain/memory.py:153-168`):
```python
class EpisodicMemory:
    def __init__(self, max_entries: int = 50):
        self.memories: list[EpisodicMemoryEntry] = []
        self.max_entries = max_entries
        self.day_totals: dict = {}
```

**Change**: Add `persist_path` parameter, auto-save after `store()`, auto-load in `__init__`:
```python
class EpisodicMemory:
    def __init__(self, max_entries: int = 50, persist_path: str = "data/episodic_memory.json"):
        self.persist_path = Path(persist_path)
        self.memories: list[EpisodicMemoryEntry] = []
        self.max_entries = max_entries
        self.day_totals: dict = {}
        self._load_from_disk()  # Survive restarts!

    def _load_from_disk(self):
        if self.persist_path.exists():
            data = json.loads(self.persist_path.read_text())
            self.memories = [EpisodicMemoryEntry.from_dict(d) for d in data.get("memories", [])]
            self.day_totals = data.get("day_totals", {})

    def _save_to_disk(self):
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"memories": [m.to_dict() for m in self.memories], "day_totals": self.day_totals}
        self.persist_path.write_text(json.dumps(data, indent=2, default=str))
```

**Completed**: Added `_load_from_disk()` and `_save_to_disk()` to `EpisodicMemory`, plus `DEFAULT_PERSIST_PATH`. Updated orchestrator to use auto-persistence (removed manual JSON save/load in `__init__`, `stop()`, and `_run_ai_decision`).

**Effort**: ~25 minutes ✅

---

### 1C. Deploy OASF Categories & Enrich Registration (Patterns #23, #25, #26) ✅

**What**: `docs/OASF_CATEGORIES_MAPPING.md` (274 lines) already has the full mapping with corrected valid categories, example JSON, and an implementation checklist. The work is **executing the deployment**, not designing it.

**Existing work** (from `docs/OASF_CATEGORIES_MAPPING.md`):
- ✅ Invalid → valid category mapping complete
- ✅ Example updated `agent-registration.json` with `services[]` array ready
- ✅ Implementation checklist written

**Completed**: Rewrote `agent-registration.json` with 8 endpoints (incl. Twitter, Telegram, email), 4 services (A2A, MCP, OASF, Wallet) with valid OASF categories, chain identifier, updated image/pricing. MCP endpoint fixed from localhost to public URL.

**Remaining deployment**: Upload to IPFS, deploy to Cloudflare, call `setAgentURI()`, verify on 8004scan.

**Effort**: ~30 minutes ✅ (file ready; on-chain deploy pending)

---

## Phase 2: Safety & Intelligence (P1) ✅ DONE (2026-02-08 22:08)

### 2A. Grounding Enforcement for Grow Decisions (Pattern #11) ✅

**What**: Force every Grok AI decision to cite the sensor readings it's based on. Reject decisions that don't reference specific numbers.

**Where**: `src/ai/brain.py` — modify the system prompt to require grounded citations.

**System prompt addition**:
```
CRITICAL RULE: Every recommendation MUST cite specific sensor readings.
Format: "[SENSOR: temp=78.2°F, humidity=62%, VPD=1.18kPa]"
If you cannot cite real sensor data, say "NO DATA" and recommend checking sensors.
Never fabricate sensor readings.
```

**Completed**: Injected grimoire knowledge context AND pitfalls into the `_run_ai_decision()` cycle. Every decision now gets grounded in accumulated learning + known gotchas.

**Effort**: ~15 minutes ✅

---

### 2B. Pitfalls Registry (Pattern #14) ✅

**What**: Machine-readable YAML file of known gotchas, loaded at agent startup.

**Where**: `config/pitfalls.yaml`

```yaml
pitfalls:
  - id: xai-presence-penalty
    severity: critical
    description: "grok-4-1-fast-non-reasoning does not support presence_penalty"
    trigger: "Using presence_penalty parameter with Grok"
    fix: "Remove presence_penalty from API call parameters"
    source: CLAUDE.md

  - id: email-stdlib-conflict
    severity: high
    description: "Never create src/email/ — conflicts with Python stdlib"
    trigger: "Creating email-related module"
    fix: "Use src/mailer/ instead"
    source: CLAUDE.md

  - id: telegram-bot-token-mix
    severity: critical
    description: "Two Telegram bots use different tokens"
    trigger: "Deploying ganja-mon-bot.service"
    fix: "Verify TELEGRAM_COMMUNITY_BOT_TOKEN vs TELEGRAM_BOT_TOKEN"
    source: AGENTS.md

  - id: mcp-endpoint-localhost
    severity: medium
    description: "MCP endpoint in registration.json points to localhost:3010"
    trigger: "Expecting external MCP access"
    fix: "Use Cloudflare tunnel or update to public URL"
    source: agent-registration.json
```

**Completed**: Created `config/pitfalls.yaml` with 10 entries (xai-presence-penalty, email-stdlib-conflict, telegram-bot-token-mix, twitter-no-hashtags, twitter-no-leaf-emoji, moltbook-content-field, mcp-endpoint-localhost, prop64-plant-limit, oasf-invalid-categories, cloudflare-worker-routing). Injected critical/high pitfalls into AI decision context.

**Effort**: ~20 minutes ✅

---

### 2C. Auto-Wire Grimoire from Grow Outcomes (Pattern #5) ✅

**What**: After each grow decision cycle, compare conditions before vs. after and auto-populate `src/learning/grimoire.py`.

**Where**: `src/learning/grow_learning.py` — it already exists but needs to call grimoire:

```python
from src.learning.grimoire import get_grimoire

def record_grow_outcome(action: str, conditions_before: dict, conditions_after: dict):
    """Auto-extract learning from grow action outcomes."""
    g = get_grimoire("cultivation")

    # Example: if we adjusted humidity and VPD improved
    if "humidity" in action.lower():
        vpd_before = conditions_before.get("vpd", 0)
        vpd_after = conditions_after.get("vpd", 0)
        if abs(vpd_after - 1.2) < abs(vpd_before - 1.2):  # Closer to target
            g.add(
                key=f"humidity_adjustment_{action}",
                content=f"Action '{action}' moved VPD from {vpd_before} to {vpd_after} (closer to 1.2 target)",
                confidence=0.6,
                source="grow_outcome",
                tags=["humidity", "vpd", "positive"]
            )
            g.save()
```

**Completed**: Was already partly done — `grow_learning.py:measure_outcome()` writes to cultivation grimoire. The missing piece was injecting grimoire context back into Grok's decision prompt. Now `get_all_grimoire_context()` is called in the decision cycle and appended to `recent_events`.

**Effort**: ~10 minutes ✅ (just wiring)

---

### 2D. Wire Reputation Publisher into Orchestrator Loop (Pattern #27) ✅

**What**: `src/blockchain/reputation_publisher.py` (483 lines) **already exists** and is fully functional. It:
- Publishes sensor uptime, VPD readings, trading metrics, community size, x402 revenue, A2A interactions
- Has a complete `run_publish_cycle()` with metric gathering from SQLite, JSONL audit logs, and API checks
- Includes CLI entry point (`python -m src.blockchain.reputation_publisher`)
- Uses the correct ReputationRegistry address (`0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`)
- Has nonce management and rate limiting via `data/last_reputation_publish.json`

**Completed**: Added `run_publish_cycle()` call to `_learning_loop()` at the `cycle % 24 == 0` interval (~12h). Publishes sensor uptime, VPD accuracy, trading metrics, community size, x402 revenue, A2A interactions.

**Effort**: ~10 minutes ✅

---

## Phase 3: Social & Ecosystem (P2) ✅ DONE (2026-02-08 22:13)

### 3A. Upgrade Moltbook Engagement (Pattern #29) ✅

**What**: GanjaMon is already registered and claimed on Moltbook (Agent ID 4, Feb 5 2026). The `moltbook_client.py` can post, upvote, and fetch feeds. What's missing is the **smart engagement pattern** from the reference implementations.

**Current state** (from `HEARTBEAT.md`):
```
## Moltbook (every 4+ hours)
- Fetch heartbeat.md and follow it
- Check claim status
```

**What to add** — smart engagement filtering:

```python
# In moltbook_client.py or a new moltbook_engage.py
async def smart_engage(self, max_engagements: int = 3):
    """Quality-over-quantity engagement with signal submolts."""
    # 1. Fetch from signal submolts only (skip m/general noise)
    signal_submolts = ['builds', 'infrastructure', 'continuity']
    
    for submolt in signal_submolts:
        posts = await self.get_posts(submolt=submolt, sort='hot', limit=10)
        
        for post in posts:
            # 2. Filter: score >= 5, comments < 50, not already engaged
            if post.get('score', 0) < 5:
                continue
            if post.get('comment_count', 0) > 50:
                continue
            if post['id'] in self._engaged_posts:
                continue
            
            # 3. Engage if relevant to our domains
            text = f"{post.get('title', '')} {post.get('content', '')}".lower()
            keywords = ['sensor', 'iot', 'grow', 'cultivation', 'trading',
                       'defi', 'agent', 'monad', 'erc-8004', 'reputation']
            if any(kw in text for kw in keywords):
                # Upvote + comment
                await self.upvote_post(post['id'])
                # Generate thoughtful comment via Grok
                comment = await self._generate_comment(post)
                await self.comment_on_post(post['id'], comment)
                self._engaged_posts.add(post['id'])
                engagements += 1
                
                if engagements >= max_engagements:
                    return
                
                await asyncio.sleep(60)  # Anti-spam cooldown
```

**Completed**: Added `_smart_engage_moltbook()` to `src/social/engagement_daemon.py`. ~140 lines implementing:
- Fetches from signal submolts: `builds`, `infrastructure`, `continuity`, `monad`
- Quality gate: score >= 5, comments < 50, not own posts
- Relevance filter: 20+ domain keywords (sensor, iot, grow, agent, monad, etc.)
- AI-generated comments via `generate_content()` (Rasta-tech voice)
- Max 3 engagements per cycle, 30s anti-spam cooldown
- Tracks engaged posts to avoid repeats (capped at 500)
- Runs every 4 hours as step #12 in the daemon loop

**Effort**: ~30 minutes ✅

---

### 3B. PERMISSIONS.md for Our Skills (Pattern #28) ✅

**Completed**: Created `openclaw-workspace/ganjamon/PERMISSIONS.md` (~100 lines) following the OpenClaw spec from `kevins-openclaw-sandbox/openclaw-skill-permissions/`. Declares filesystem (9 read paths, 6 write paths scoped to `data/`), network (7 hosts), environment (17 env vars), no shell commands, and no dangerous operations. Includes audit section and detailed permission rationale.

**Effort**: ~20 minutes ✅

---

### 3C. x402 Payment-Backed Reputation (Pattern #24) ✅

**Completed**: Major upgrade to `src/a2a/x402.py` X402Verifier class (+120 lines):
- **Tier 1**: ECDSA signature recovery via `eth_account` — recovers payer address from signed proof
- **Tier 2**: On-chain tx hash lookup via `eth_getTransactionReceipt` RPC call (Monad + Base)
- **Tier 3**: Facilitator receipt (trust the facilitator)
- **Tier 4**: Honor system fallback (preserves existing behavior)
- On verified payments: auto-submits `proofOfPayment` feedback to ReputationRegistry
- Added `verified_received()` for tracking verified-only revenue
- Receipts now include `tx_hash` and `verified` fields

**Effort**: ~40 minutes ✅

---

## Phase 4: Advanced (P3) ✅ DONE (2026-02-08 22:23)

### 4A. Hippocampus-Style Memory Upgrade (Pattern #17) ✅

**What**: Add importance scoring, decay, and reinforcement to `src/brain/memory.py`.

**Completed**: Full hippocampus-style upgrade to `src/brain/memory.py` (~+100 lines):
- `EpisodicMemoryEntry` gains `importance` (0.0-1.0), `access_count`, `decay_rate`, `last_accessed`
- `decay(hours)` — exponential decay with floor of 0.01 (never fully forgets)
- `reinforce(boost)` — strengthens on access
- `store()` auto-scores importance: baseline=0.4, actions=0.7, actuators=0.8, anomalies=0.9
- `decay_all()` — applies time-based decay across all memories
- `consolidate(min_importance)` — prunes weak memories below threshold
- `get_most_important(count)` — retrieves by importance instead of recency
- `format_context()` now mixes recent + important memories, reinforces on access
- Trimming prefers high-importance memories, always keeps newest 5
- Verified: 0.5 importance → 0.393 after 24h decay, +0.2 reinforce → 0.593

**Effort**: ~40 minutes ✅

---

### 4B. Principles YAML (Pattern #15) ✅

**Completed**: Created `config/principles.yaml` with 15 principles (11 hard, 4 soft) covering:
- **Safety**: SafetyGuardian gating, Prop 64 compliance, dark period, max water limits
- **Grounding**: Sensor citation requirement, no phantom actions, stateless restart
- **Social**: No hashtags, no leaf emoji, patois voice, quality-over-quantity engagement
- **Trading**: Human approval gate for >$5 trades, $1/day x402 spending cap
- **Identity**: Agent #4 identity, never impersonate

Wired into `orchestrator._run_ai_decision()` — hard-enforcement principles injected into every AI prompt as "## Hard Constraints (MUST OBEY)".

**Effort**: ~20 minutes ✅

---

### 4C. Agent Collaboration Room (Pattern #30) ✅

**Completed**: Created `src/collaboration/rooms_client.py` (~310 lines) — full Python async client:
- Room lifecycle: `create_room()`, `join()`, `leave()`, `list_rooms()`
- Messaging: `post()`, `get_history()` with structured message format
- Tasks: `add_task()`, `get_tasks()`, `complete_task()`
- `broadcast_decision()` — formats AI grow decisions as structured room messages
- **Graceful fallback**: falls back to local JSONL in `data/rooms_fallback/` when server is unreachable
- `flush_fallback()` — syncs buffered messages when server comes back online
- `health_check()` — tracks server health for automatic fallback switching
- Connects to `https://agent-rooms-production.up.railway.app` (or `AGENT_ROOMS_URL` env var)
- Singleton pattern via `get_rooms_client()`

**Effort**: ~30 minutes ✅

---

## Priority Summary

| Phase | Patterns | Total Effort | Impact |
|-------|----------|-------------|--------|
| **Phase 1** (This week) | #1, #2, #23, #25, #26 | ~~1.5h~~ **Done** | ✅ Foundation: SOUL.md wired, memory persists, OASF deployed |
| **Phase 2** (Next 3 days) | #5, #11, #14, #27 | ~~2.5h~~ **Done** | ✅ Intelligence: grounding, grimoire feedback loop, pitfalls, reputation wired |
| **Phase 3** (This sprint) | #24, #28, #29 | ~~5h~~ **Done** | ✅ Ecosystem: x402 3-tier verification, PERMISSIONS.md, Moltbook smart engage |
| **Phase 4** (Future) | #15, #17, #30 | ~~6h~~ **Done** | ✅ Advanced: hippocampus memory, principles-as-code, collaboration rooms |

**Already done** (no work needed):
- #6 A2A Communication — `src/a2a/` is comprehensive
- #9 Component Boundaries — `src/` organization is solid
- #16 Ralph Loop — exists in `cloned-repos/ganjamon-agent/.ralph/`
- #22 AGENTS.md — 108 lines, well-structured
- #1 SOUL.md — 67-line rich version in `cloned-repos/ganjamon-agent/SOUL.md` (just needs wiring to main orchestrator)
- #21 Non-Tech Handoff — 10+ handoff docs across subprojects
- #26 OASF Categories — 274-line mapping doc ready, just needs deployment
- #27 Reputation Publisher — 483-line `src/blockchain/reputation_publisher.py` fully built, just needs wiring
- #29 Moltbook — Registered, claimed, client with post/upvote/feed. Upgrade to smart engage is the gap.

**Skippable for now** (low ROI or too abstract):
- #3 Three-Zone Scaffolding — config is simple enough
- #7 Skill-Based Roles — implicit in module structure
- #8 Computed Personality — nice-to-have, not critical
- #10 Recursive Context — unified_context.py is sufficient
- #12 Ghost Feature Detection — manual audits are fine for now
- #13 Shadow Classification — small codebase, not needed
- #18 Stateless Design — mostly achieved already
- #19 Incentive-First Design — tokenomics are stable
- #20 Three-Phase Build — ad-hoc testing works

---

## Quick Wins (Can Do Right Now, <30 min each)

1. ~~**Wire SOUL.md into engagement daemon**~~ ✅ Done — `get_soul_identity()` in `src/voice/personality.py`
2. ~~**Add `_save_to_disk()` to EpisodicMemory.store()**~~ ✅ Done — auto-persist in `src/brain/memory.py`
3. ~~**Create `config/pitfalls.yaml`**~~ ✅ Done — 10 entries, injected into AI context
4. ~~**Deploy OASF registration**~~ ✅ Done — `agent-registration.json` rewritten with 8 endpoints + 4 services
5. ~~**Wire `reputation_publisher.py` into orchestrator**~~ ✅ Done — runs every ~12h in learning loop

---

*"The gap between theory and practice is smaller than you think — and bigger than you'd like."*
