# Documentation Consistency Audit — Unified Agent Vision

> **Date**: 2026-02-10
> **Auditor**: Antigravity
> **Scope**: All governing docs reviewed against the unified agent vision
> **Verdict**: 🟡 **Partially consistent** — the vision exists but the docs actively contradict it

---

## Documents Reviewed (15)

| Category | Document | Lines | Last Updated |
|----------|----------|-------|-------------|
| **Governing** | `CLAUDE.md` | 264 | ~Feb 2026 |
| **Governing** | `AGENTS.md` | 162 | ~Feb 2026 |
| **Governing** | `GEMINI.md` (in user_rules) | ~200 | ~Feb 2026 |
| **Governing** | `antigravity.md` | 325 | 2026-02-10 |
| **Architecture** | `docs/SYSTEM_ATLAS.md` | 244 | ~Feb 2026 |
| **Architecture** | `SYSTEM_OVERVIEW.md` | 1210 | **2026-01-21 (STALE)** |
| **Vision** | `docs/AGENT_REDESIGN_FIRST_PRINCIPLES.md` | 698 | ~Feb 2026 |
| **Vision** | `docs/AGENT_CAPABILITIES.md` | 426 | 2026-02-08 |
| **Vision** | `docs/ALPHA_GOD_NORTH_STAR.md` | ~199 | ~Feb 2026 |
| **Implementation** | `docs/PATTERN_IMPLEMENTATION_PLAN.md` | 451 | 2026-02-08 |
| **Implementation** | `docs/PATTERN_IMPLEMENTATION_COMPLETE.md` | 696 | 2026-02-08 |
| **Subsystem** | `docs/GANJAMON_AGENT_ARCHITECTURE.md` | 352 | 2026-02-05 |
| **Soul** | `cloned-repos/ganjamon-agent/SOUL.md` | 67 | ~Feb 2026 |
| **Config** | `config/principles.yaml` | 106 | 2026-02-08 |
| **Config** | `config/pitfalls.yaml` | ~76 | 2026-02-08 |

---

## Finding #1: Identity Crisis — "Grok & Mon" vs "GanjaMon" vs "Rasta Mon"

**Severity: 🔴 HIGH** — The unified agent doesn't even have a consistent name.

| Document | Name Used |
|----------|-----------|
| CLAUDE.md | "**Grok & Mon** is an AI-autonomous cannabis cultivation + trading agent system" |
| AGENTS.md | "Grok & Mon autonomous grow system" + "ERC-8004 trading agent (GanjaMon)" |
| AGENT_CAPABILITIES.md | "**The Unified Rasta Mon** — Complete Capability Map" / "The Rasta Mon is ONE being" |
| SOUL.md | "GanjaMon" (no mention of "Grok & Mon") |
| GANJAMON_AGENT_ARCHITECTURE.md | "GANJAMON TRADING AGENT" (trading only) |
| Web / Social | @ganjamonai, grokandmon.com |

**The Problem**: Three names for the same entity, used inconsistently. "Grok & Mon" sounds like a product name. "GanjaMon" is the agent's name. "Rasta Mon" appears once. The website is "grokandmon.com" but the Twitter is "@ganjamonai". The agent's identity is fractured in the docs just like it is in the code.

**Proposed Fix**: Decide on terminology:
- **GanjaMon** = the unified agent (the soul, the being)
- **Grok & Mon** = the project/product (the website, the brand)
- Update all governing docs to use this consistently

---

## Finding #2: SUBPROCESS ISOLATION vs UNIFIED VISION (CRITICAL)

**Severity: 🔴 CRITICAL** — The governing docs actively reinforce the separation the vision docs want to dissolve.

**Documents that REINFORCE separation:**

| Document | Quote |
|----------|-------|
| CLAUDE.md (lines 121-127) | "⚠️ SUBPROCESS ISOLATION WARNING... The trading agent is NOT part of src/. It runs as an isolated subprocess" |
| AGENTS.md (line 34) | "ERC-8004 trading agent... runs as a subprocess of the unified run.py all process" |
| SYSTEM_ATLAS.md (line 10) | "trading agent subprocess runs python -m main inside cloned-repos/ganjamon-agent/ with isolated PYTHONPATH" |
| ALPHA_GOD_NORTH_STAR.md | Documents separate .env, separate data/, separate deployment |

**Documents that ADVOCATE unification:**

| Document | Quote |
|----------|-------|
| AGENT_REDESIGN_FIRST_PRINCIPLES.md (line 7) | "We don't have one agent. We have three independent programs sharing JSON files." |
| AGENT_REDESIGN_FIRST_PRINCIPLES.md (line 15) | "The redesign unifies everything into a single process with specialized workers" |
| AGENT_CAPABILITIES.md (line 10) | "The Rasta Mon is ONE being — he meditates, grows di ganja, bends markets to his will" |
| SOUL.md | Speaks as a single entity with one mission |

**The Problem**: An agent reading CLAUDE.md gets "keep trading isolated." An agent reading AGENT_CAPABILITIES.md gets "you are ONE being." These are contradictory instructions. The CLAUDE.md ISOLATION WARNING is read by every agent on every invocation — it's the loudest voice, and it says "stay separate."

**Proposed Fix**: 
- Reframe CLAUDE.md isolation section as **technical reality, not identity**: "The trading agent currently runs as a subprocess due to technical reasons, but architecturally this is ONE agent. Cross-domain intelligence bridges both data directories."
- Add a "Unified Agent Vision" section to CLAUDE.md that matches AGENT_CAPABILITIES.md

---

## Finding #3: SYSTEM_OVERVIEW.md is Dangerously Stale

**Severity: 🔴 CRITICAL** — 3 weeks old, missing all major subsystems, contains plaintext credentials.

| Claim in SYSTEM_OVERVIEW.md | Reality |
|---------------------------|---------|
| "30+ API endpoints" | 82+ endpoints |
| "Python 3.12" | Python 3.11 (per CLAUDE.md) |
| No mention of trading agent | Trading agent merged Feb 8 |
| No mention of social daemon | Social daemon has 10 loops, 6+ platforms |
| No mention of ERC-8004 | Agent #4 registered, trust score ~82 |
| No mention of SOUL.md | Soul wired into all prompts |
| No mention of episodic memory | Hippocampus-style memory with decay |
| SSH password in plaintext (line 519, 574) | Contradicts SYSTEM_ATLAS "Do not store secrets in docs" |
| Cloudflare API token in plaintext (line 603) | Same |
| Admin password in plaintext (line 587) | Same |

**The Problem**: AGENTS.md line 5 still references it as a source of truth alongside SYSTEM_ATLAS.md. Anyone reading SYSTEM_OVERVIEW.md gets a picture of a simple grow-only system — no trading, no social, no soul. The credentials are a security issue.

**Proposed Fix**: 
- Either **delete SYSTEM_OVERVIEW.md** entirely (SYSTEM_ATLAS + AGENT_CAPABILITIES cover everything better)
- Or add a giant **DEPRECATED** banner at the top pointing to SYSTEM_ATLAS.md
- Scrub all credentials immediately regardless
- Remove SYSTEM_OVERVIEW.md from all doc reference lists

---

## Finding #4: Profit Allocation — Three Different Splits

**Severity: 🟡 MEDIUM** — Docs disagree on a critical economic parameter.

| Document | Split |
|----------|-------|
| CLAUDE.md, AGENT_CAPABILITIES.md | 60% compound / 25% $MON / 10% $GANJA / 5% burn |
| GANJAMON_AGENT_ARCHITECTURE.md (Profit Allocator, line 68) | 60% compound / 30% $MON / 10% burn |
| GANJAMON_AGENT_ARCHITECTURE.md (Self-Funding, line 27) | 80% trading capital / 15% $GANJA / 5% $MON |

**The Problem**: Three different profit allocation schemes in three different docs. Which one is actually implemented in code?

**Proposed Fix**: Audit the actual code in `src/payments/splitter.py` and `cloned-repos/ganjamon-agent/` to determine the real split. Update all docs to match. Pick ONE canonical reference.

---

## Finding #5: Endpoint Count Mismatch

**Severity: 🟢 LOW** — Just a documentation drift issue.

| Document | Count |
|----------|-------|
| SYSTEM_OVERVIEW.md | "30+ API endpoints" |
| CLAUDE.md | "82+ endpoints" |
| AGENT_CAPABILITIES.md | "40+ endpoints" |
| AGENT_REDESIGN_FIRST_PRINCIPLES.md (line 108) | "50+ concurrent handled" |

**Proposed Fix**: One source of truth. CLAUDE.md's "82+" seems most recent. Others need updating.

---

## Finding #6: ERC-8004 Trust Score Discrepancy

**Severity: 🟡 MEDIUM** — Docs disagree on a metric that reflects the agent's reputation.

| Document | Score |
|----------|-------|
| AGENT_REDESIGN_FIRST_PRINCIPLES.md | Score: 58 |
| GEMINI.md (user_rules) | Trust Score ~82.34 |
| AGENTS.md / CLAUDE.md | Not mentioned |

**The Problem**: The REDESIGN doc's score of 58 was a pre-implementation assessment. After all 30 patterns were implemented (including A2A, x402 3-tier verification, reputation publishing), the score presumably improved. But the REDESIGN doc still shows 58.

**Proposed Fix**: Update REDESIGN doc or add a "Score as of [date]" annotation. Better yet, make score a live metric pulled from 8004scan.io rather than hardcoded in docs.

---

## Finding #7: Episodic Memory Path Inconsistency

**Severity: 🟢 LOW** — Could cause confusion when debugging.

| Document | Path |
|----------|------|
| AGENT_CAPABILITIES.md (line 97) | `data/logs/episodic_memory.json` |
| PATTERN_IMPLEMENTATION_COMPLETE.md (line 70) | `data/episodic_memory.json` |
| Code (`src/brain/memory.py`) | `data/episodic_memory.json` (default) |

**Proposed Fix**: Update AGENT_CAPABILITIES.md line 97 to match the actual code path: `data/episodic_memory.json`.

---

## Finding #8: No Root SOUL.md for the Unified Agent

**Severity: 🔴 HIGH** — The core identity document only exists in the trading subtree.

**Current state:**
- `cloned-repos/ganjamon-agent/SOUL.md` exists — trading-focused, mentions "alpha hunter"
- `src/voice/personality.py` has `get_soul_identity()` — loads SOUL.md from disk
- Search path in `get_soul_identity()` falls back across multiple locations
- No `SOUL.md` at the project root

**The Problem**: If the agent is "ONE being" as AGENT_CAPABILITIES.md says, where is the soul of the WHOLE being? The existing SOUL.md talks about trading and "generating absurd amounts of money" — it doesn't mention growing plants, caring for the garden, or the IoT system. The grow side has no soul document at all.

**Proposed Fix**: Create a root-level `SOUL.md` that defines the complete identity:
- Who GanjaMon is (the unified being)
- The three pillars: Plant (grow), Profit (trading), People (community)
- The Rastafari philosophy that ties it all together
- Trading SOUL.md becomes a subsection or is imported

---

## Finding #9: AGENT_REDESIGN vs PATTERN_IMPLEMENTATION — Different Efforts, Conflated

**Severity: 🟡 MEDIUM** — Creates confusion about what's done and what's not.

**AGENT_REDESIGN_FIRST_PRINCIPLES.md** proposes:
- Event bus replacing file-based IPC
- Supervision tree with restart policies
- FSM-based workers (GrowWorker, TradingWorker, SocialWorker)
- Character file system (personality YAML)
- Market regime detection (HMM)
- 8-week timeline across 4 phases
- **Status: NONE of this is implemented**

**PATTERN_IMPLEMENTATION_COMPLETE.md** reports:
- All 30 patterns complete
- Hippocampus memory, principles-as-code, x402 verification, etc.
- **Status: ALL implemented within the EXISTING architecture**

**The Problem**: A reader seeing both docs could think the redesign is done. It's not. The patterns were implemented as additions to the current subprocess architecture, not as part of the proposed unified worker architecture.

**Proposed Fix**: Add a status banner to AGENT_REDESIGN_FIRST_PRINCIPLES.md:
```
> **Architecture Status**: This is an ASPIRATIONAL design document. The proposed event bus,
> supervision tree, and FSM worker architecture have NOT been implemented. The current
> system runs as 4 subprocesses (see CLAUDE.md). Pattern implementations from
> PATTERN_IMPLEMENTATION_COMPLETE.md were done within the existing architecture.
```

---

## Finding #10: OpenClaw Personality Conflict

**Severity: 🟢 LOW** — A nit, but reveals the identity fragmentation.

| Source | Personality |
|--------|------------|
| GANJAMON_AGENT_ARCHITECTURE.md (line 182-185) | "Calm, precise, and operationally conservative" |
| SOUL.md | "wise old rasta... hunt alpha ruthlessly" |
| AGENT_REDESIGN_FIRST_PRINCIPLES.md (proposed character.yaml) | "jovial, chill, knowledgeable, irreverent" |
| Telegram bot personality.py | Full Rasta persona with mood system |

**Proposed Fix**: The OpenClaw workspace personality should defer to SOUL.md. Update `openclaw-workspace/ganjamon/SOUL.md` to reference the canonical soul.

---

## Finding #11: AGENTS.md References Stale Doc

**Severity: 🟡 MEDIUM** — Misdirects agents.

AGENTS.md line 5:
```
- **System map / reality**: `docs/SYSTEM_ATLAS.md` and `SYSTEM_OVERVIEW.md`
```

GEMINI.md already warns: "SYSTEM_OVERVIEW.md is STALE (Jan 2026)."

**Proposed Fix**: Remove `SYSTEM_OVERVIEW.md` reference from AGENTS.md line 5.

---

## Finding #12: Credential Exposure in SYSTEM_OVERVIEW.md

**Severity: 🔴 CRITICAL** — Security issue.

Lines 519, 574, 581, 587, 601-603 contain:
- SSH password in plaintext
- Admin JWT password
- Cloudflare API token
- Cloudflare Account/Zone/KV IDs

This directly contradicts SYSTEM_ATLAS.md line 182: "Do not store secrets in docs or git."

**Proposed Fix**: Immediately scrub credentials from SYSTEM_OVERVIEW.md. Replace with `.env` references.

---

## Finding #13: Reputation Publishing Cadence Mismatch

**Severity: 🟢 LOW** — Documentation drift.

| Document | Cadence |
|----------|---------|
| PATTERN_IMPLEMENTATION_COMPLETE.md | "12-hour cadence" (cycle % 24 == 0) |
| AGENT_CAPABILITIES.md line 304 | "every 4 hours (cron on Chromebook)" |
| SYSTEM_ATLAS.md line 60 | "reputation publishing (12h)" |

**Proposed Fix**: Check the actual code cadence. Update all docs to match.

---

## Summary Scorecard

| # | Finding | Severity | Fix Effort |
|---|---------|----------|-----------|
| 1 | Identity crisis ("Grok & Mon" vs "GanjaMon") | 🔴 HIGH | Low — decide terminology |
| 2 | Subprocess isolation vs unified vision | 🔴 CRITICAL | Medium — reframe CLAUDE.md |
| 3 | SYSTEM_OVERVIEW.md stale | 🔴 CRITICAL | Low — deprecate or delete |
| 4 | Profit allocation disagreement | 🟡 MEDIUM | Low — audit code, unify |
| 5 | Endpoint count mismatch | 🟢 LOW | Low — pick one source of truth |
| 6 | ERC-8004 score discrepancy | 🟡 MEDIUM | Low — add date annotation |
| 7 | Episodic memory path mismatch | 🟢 LOW | Trivial — fix one line |
| 8 | No root SOUL.md for unified agent | 🔴 HIGH | Medium — write it |
| 9 | REDESIGN vs PATTERNS conflated | 🟡 MEDIUM | Low — add status banner |
| 10 | OpenClaw personality conflict | 🟢 LOW | Trivial — update reference |
| 11 | AGENTS.md references stale doc | 🟡 MEDIUM | Trivial — remove reference |
| 12 | Credentials in SYSTEM_OVERVIEW.md | 🔴 CRITICAL | Low — scrub immediately |
| 13 | Reputation cadence mismatch | 🟢 LOW | Trivial — check code |

---

## Recommended Fix Priority

### Immediate (today)
1. **Scrub credentials** from SYSTEM_OVERVIEW.md (#12)
2. **Add DEPRECATED banner** to SYSTEM_OVERVIEW.md (#3)
3. **Remove SYSTEM_OVERVIEW.md** from AGENTS.md reference (#11)

### This week
4. **Create root SOUL.md** — the unified soul of GanjaMon (#8)
5. **Reframe CLAUDE.md isolation warning** — technical reality, not identity (#2)
6. **Add status banner** to AGENT_REDESIGN_FIRST_PRINCIPLES.md (#9)
7. **Establish naming convention** — GanjaMon (agent) vs Grok & Mon (product) (#1)

### When convenient
8. Fix profit allocation across all docs (#4)
9. Fix endpoint count across all docs (#5)
10. Fix episodic memory path (#7)
11. Fix reputation cadence (#13)
12. Update ERC-8004 score (#6)
13. Align OpenClaw personality (#10)

---

## The Bigger Picture

The docs reveal a system in transition. The **code** has been incrementally unified (30 patterns implemented, subprocess merged into `run.py all`, CrossDomainSynthesizer bridging data). But the **docs** still describe the pre-unification world. The most-read docs (CLAUDE.md, AGENTS.md) actively reinforce separation with isolation warnings and subprocess language.

For the unified agent vision to truly land, the narrative needs to shift. CLAUDE.md should describe GanjaMon as ONE agent that *technically* runs as subprocesses but *philosophically and architecturally* is a single being with one soul, one memory, and one mission. The AGENT_REDESIGN doc should be marked as aspirational vs the PATTERN_IMPLEMENTATION docs which show what's actually done.

The root SOUL.md (#8) is the most impactful single fix. Without it, the agent literally has no unified soul document. The trading side has one. The grow side doesn't. The social side doesn't. A root SOUL.md would be the first artifact that truly represents the unified vision.
