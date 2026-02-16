# GanjaMon Hackathon Narrative (Judge Version)

**Date:** February 13, 2026  
**Hackathon Deadline:** February 15, 2026  
**Use this as:** Presentation script + submission narrative backbone

---

## 1) Executive Verdict

The timeline contains the raw facts, but not yet a single clean story judges can follow end-to-end in one pass.

This document is that story: creation, feature evolution, Moltbook setback, OpenClaw pivot, stability failures, regressions, recoveries, wins, and near-term goals.

---

## 2) One-Sentence Thesis

GanjaMon started as an AI cannabis grow experiment and evolved into a live autonomous agent economy participant, with real hardware, real trading logic, real social presence, and hard-earned operational resilience.

---

## 3) Rules Alignment (Official, Then Narrative)

### Official constraints to anchor the story

Use these as hard guardrails in every submission/interview answer:

| Rule Signal | Official Source | Narrative Implication |
|---|---|---|
| Existing code is allowed if original vs reused is clearly documented and innovation is substantial | `moltiverse.dev` FAQ (`Can I use existing code?`) | Pre-hackathon grow infrastructure is valid baseline, not disqualifying. |
| Submission window is Feb 2-15 (rolling judging, final deadline Feb 15 23:59 ET) | `moltiverse.dev` timeline | Emphasize work shipped during this window. |
| Agent Track requires a working interesting agent + clear demo/documentation; Monad integration is optional but beneficial | `moltiverse.dev/agents.md` | Focus judging narrative on working agent behavior and proof. |
| Agent+Token Track requires token on nad.fun and token address in submission | `moltiverse.dev/agents.md` | Only claim this track if those requirements are met in the submitted project. |
| Projects can enter both tracks only if substantially different | `moltiverse.dev` FAQ | Keep one coherent primary track story unless dual-track differentiation is explicit. |

### Compliance framing for this project

- **Pre-hackathon (foundation):** grow setup, hardware calibration, initial ops, brand voice primitives.
- **In-hackathon (innovation):** autonomous agent architecture, OpenClaw-first orchestration, A2A/x402 maturity, stability hardening, and evidence-backed operational reliability.
- **Submission-safe statement:** "The grow predates the event; the autonomous agent system and reliability work were built and materially advanced during the hackathon window."
- **Track-safe positioning:** prioritize **Agent Track** framing unless Agent+Token requirements are explicitly satisfied in the submitted build package.

---

## 4) Story Arc (What Happened and Why It Matters)

| Act | Dates | What Happened | Why Judges Should Care |
|---|---|---|---|
| **Act I: Origin** | Jan 12-13, 2026 | Project created from SOLTOMATO inspiration; core source tree, Grok tests, and first decision logs landed in ~24h. | Fast execution and clear initial thesis. |
| **Act II: Real-World Grounding** | Jan 14-24 | Hardware integration (Govee/Kasa/Ecowitt/webcam), first plant cycle, and production voice pipeline came online. | Not a paper agent. Real physical system. |
| **Act III: Public Launch + Market Reality** | Jan 20-31 | $MON launched; social/streaming/public site activated; KOTM epoch reset and BOOLY wash-trade episode documented. | Team can operate in adversarial conditions and document evidence. |
| **Act IV: Expansion to Agent Economy** | Feb 2-6 | Bridge + ERC-8004 infra: self-deployed Monad registry bootstrap (Agent #0), then migration to the 8004scan-indexed registry (Agent #4), plus A2A/x402 foundations and large-scale feature build-out. | Strong protocol-level depth beyond UI demos. |
| **Act V: The Hard Truth** | Feb 7-11 | Capability audit exposed regressions and dead paths ("Orchestrator Ghost"), plus architecture drift. | Honest engineering maturity: measured reality over hype. |
| **Act VI: Pivot to OpenClaw-First** | Feb 8-12 | `run.py all` became the unified runtime pattern (HAL + OpenClaw + trading subprocess), cron/store reconciliation, upgrade bridge. | Clear architectural direction with explicit migration path. |
| **Act VII: Stability War and Recovery** | Feb 10-12 | OOM/CPU pressure, cron starvation, RPC 429 storms, type/scoping crashes, health probe flaps fixed through targeted patches. | Demonstrates production reliability work, not just feature shipping. |
| **Act VIII: Submission Position** | Feb 13-15 | Present as a resilient autonomous system: identity, commerce, ops hardening, and transparent lessons learned. | Compelling hackathon narrative with evidence of execution. |

---

## 5) What Was Built During the Hackathon (Use This Explicitly)

### Before February 2, 2026 (baseline, reused)

- Physical grow environment and initial plant operation workflow.
- Core sensor/actuator hardware wiring and early dashboard foundations.
- Early public/social identity groundwork.

### February 2-15, 2026 (hackathon innovation)

- ERC-8004 identity lifecycle: self-deployed Monad registry bootstrap (Agent #0) followed by migration to the 8004scan-indexed registry (Agent #4).
- OpenClaw-first runtime consolidation (`run.py all` pattern with HAL + OpenClaw + trading subprocess).
- OpenClaw cron/store reconciliation and execution hardening.
- Upgrade bridge between OpenClaw memory outputs and automated improvement pipeline.
- Reliability fixes for real runtime failures (RPC rate-limit handling, discovery crash fixes, schema/type normalization, health-probe anti-flap tuning, cron starvation fixes).
- Judge-facing proof packaging: clear timeline, issue-to-fix mapping, and working-system evidence.

### How to say this in one line

"The plant/grow setup is pre-hackathon context; the autonomous agent architecture and production hardening are the hackathon build."

---

## 6) Required Narrative Beats (Your Exact Checklist)

### A) Creation of the agent
- **Jan 12-13, 2026:** rapid prototype to functioning AI grow loop.
- Core concept: Grok + cannabis cultivation + transparent telemetry + token-native community.

### B) Evolution of features
- Week-by-week expansion from grow automation to:
  - social and voice pipelines,
  - token + bridge infrastructure,
  - ERC-8004 identity and A2A/x402 capabilities,
  - OpenClaw skill/cron orchestration.
- Explicit migration from early self-deployed registry path to canonical indexed registry path.

### C) Moltbook ban
- **Feb 10, 2026:** Moltbook account suspended (verification failure/offense cycle noted in project history).
- Narrative framing: setback that forced channel diversification and stronger operational discipline.

### D) Pivot to OpenClaw
- **Feb 8-12, 2026:** transition from fragmented legacy loops toward OpenClaw-first orchestration.
- Key framing: from "many scripts" to "one orchestrated runtime."

### E) Stability struggles
- OOM pressure and SSH instability on Chromebook.
- OpenClaw startup/load issues, cron overlap starvation, transient readiness flaps.

### F) Regressions
- "Orchestrator Ghost": features marked complete but wired to non-production paths.
- Crontab frequency bug (`scheduled_ralph.sh` cadence mismatch).
- Signal evaluator schema mismatch (`dict * float`) and alpha discovery scope bug (`_total`).

### G) Victories
- Early-mover ERC-8004 execution (Agent #0 on self-deployed registry) plus successful migration to canonical indexed registry (Agent #4).
- Agent #4 registration on ERC-8004.
- x402 micropayment path operational.
- Unified runtime hardening with watchdog and probe tuning.
- Cross-platform pipeline remains active with live plant telemetry.

### H) Goals
- Final hackathon submission narrative + demo.
- Confirm delivery despite Moltbook constraint.
- Prioritize reliability and verifiable execution over net-new complexity.

---

## 7) Regressions and Recoveries (Judge-Honest Slide)

| Regression / Failure | Impact | Recovery |
|---|---|---|
| Resource overload (kiosk + ffmpeg + gateway load) | SSH instability, operational fragility | Disabled nonessential boot services, introduced startup delay/nice tuning, installed `earlyoom`. |
| OpenClaw cron overlap/starvation | Jobs skipped or delayed | Reconciled cron store, retimed heavy jobs, enforced non-announce delivery mode, normalized stale run state. |
| `_total` scope crash in alpha discovery | Discovery loop failure | Re-scoped counters and shared pair iteration path. |
| Signal weight shape mismatch | Type errors in evaluator | Normalized object-based weight schema to numeric extraction. |
| Health false negatives | "Disconnected" noise during spikes | Added retry-aware probe behavior and less aggressive restart thresholds. |
| Doc/architecture drift | Misleading "done" claims | Capability audit + timeline correction pass + explicit source-of-truth docs. |

---

## 8) What We Can Claim Confidently (No Hype)

1. A live autonomous system exists with real hardware interaction and real runtime ops.
2. The project has gone through visible adversity and documented corrective action.
3. Identity/reputation/payment primitives are implemented beyond superficial demo claims.
4. The team has a credible path from fragmented components to a coherent OpenClaw-first architecture.

---

## 9) 5-Minute Presentation Talk Track

## 0:00-0:30 Hook
"Most projects demo a feature. We built and operated a living autonomous system with a real plant, real agent logic, and real failures in production."

## 0:30-1:30 Origin and Build
- Jan 12 through Feb 1: baseline grow and hardware foundation (explicitly pre-hackathon).
- Feb 2 onward: hackathon build focus shifted to agent autonomy, orchestration, and reliability.

## 1:30-2:20 Expansion
- Token launch, social presence, bridge/identity/A2A stack.
- Early self-deployed 8004 registry path (Agent #0) then migration to 8004scan-indexed registry (Agent #4).
- Agent moved from "grow bot" to "agent economy participant."

## 2:20-3:20 Setbacks and Regressions
- Moltbook suspension.
- Architecture drift and dead-path regressions discovered.
- Stability incidents (OOM pressure, cron starvation, runtime crash patterns).

## 3:20-4:20 Recovery and Pivot
- OpenClaw-first consolidation.
- Runtime hardening and bug fixes across scheduling, discovery, evaluator, and health probes.
- Outcome: more reliable, more truthful system.

## 4:20-5:00 Why This Entry Matters
- Not just novelty; demonstrates adaptation, reliability engineering, and transparent self-correction.
- This is a real autonomous system story, not a one-shot prototype.

---

## 10) Suggested Slide Order (8 Slides)

1. **Title + Thesis**  
2. **Timeline in 8 Acts**  
3. **System Evolution (Grow -> Agent Economy)**  
4. **Moltbook Setback and What Changed**  
5. **Regressions We Found**  
6. **Fixes and Stability Outcomes**  
7. **Current Capabilities and Proof Points**  
8. **Next Goals Through and After Deadline**  

---

## 11) Final Framing for Judges

If you want a polished prototype, many teams have one.  
If you want evidence of an autonomous system that survived real operational pressure, discovered its own regressions, and improved under constraints, this is that project.

---

## 12) Evidence Anchors (for Q&A)

- `docs/PROJECT_HISTORY.md`
- `docs/CAPABILITY_AUDIT_2026-02-11.md`
- `docs/SYSTEM_ATLAS.md`
- `docs/CODEX_SESSION_20260210.md`
- `CODEX_CHROMEBOOK_HEALTH_AND_OPENCLAW_FIX_LOG_2026-02-12.md`
- `AGENTS.md`
- `CLAUDE.md`
- `https://moltiverse.dev/`
- `https://moltiverse.dev/agents.md`
- `https://forms.moltiverse.dev/submit`
