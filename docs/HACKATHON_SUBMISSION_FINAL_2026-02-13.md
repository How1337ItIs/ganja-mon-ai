# GanjaMon - Final Hackathon Submission Text (Rules-Aligned)

**Date:** February 13, 2026  
**Primary Track:** Agent Track  
**Deadline:** February 15, 2026, 23:59 ET

---

## Copy-Paste Submission Body

# GanjaMon - Moltiverse Hackathon Submission

**Primary Track:** Agent Track  
**Submission Window:** Feb 2-15, 2026

GanjaMon is a live autonomous agent system: real grow hardware + AI orchestration + trading intelligence + social presence + on-chain agent identity.

## Disclosure (Rules Alignment)

- **Pre-hackathon baseline (reused):** grow setup, hardware calibration, initial operations.
- **Hackathon build (new/advanced in-window):** autonomous agent architecture, OpenClaw-first orchestration, reliability hardening, and evidence-backed operations.
- We are explicitly separating reused baseline from in-window innovation.

## What We Built During the Hackathon (Feb 2-15)

- OpenClaw-first runtime consolidation (`run.py all`: HAL + OpenClaw + trading subprocess).
- OpenClaw cron/store reconciliation and scheduling hardening.
- OpenClaw -> upgrade bridge for continuous improvement requests.
- ERC-8004 registry lifecycle completion: early self-deployed Monad registry path (Agent #0) followed by migration to the 8004scan-indexed registry (Agent #4).
- Stability fixes under production load:
  - RPC 429 backoff
  - discovery crash fix (`_total` scope)
  - signal-weight schema normalization
  - health probe retry anti-flap tuning
  - cron overlap/starvation mitigation
- Documentation/audit reconciliation to remove architecture drift and dead-path overclaims.

## Why This Is Not Just a Demo

- **ERC-8004 Registered:** Agent #4 on Monad (current canonical/indexed registry).
- **Early-mover proof:** initially Agent #0 on a self-deployed Monad registry before migrating to the registry integrated by 8004scan.
- **A2A Protocol:** `.well-known/agent-card.json` discovery surface.
- **x402 payments:** machine-to-machine payment capability in agent workflows.
- **Real hardware loop:** physical sensors/camera + safety-guarded control logic.
- **Operational resilience:** production failures were observed, diagnosed, and fixed.

## Regressions We Faced (and Fixed)

- Temporary Moltbook account suspension reduced one social distribution channel.
- Runtime resource pressure causing operational instability.
- Registry/indexing split: early self-deployed registry was not the long-term indexed path, requiring migration.
- Cron overlap/starvation causing missed cycles.
- Discovery crash and signal-weight type mismatch.
- Health readiness false negatives during gateway spikes.
- Architecture drift between claimed capabilities and active runtime.

## Recovery Outcomes

- Submission narrative and proof artifacts were shifted to channel-agnostic docs and links.
- Registry migration completed to the 8004scan-indexed path; `.well-known` identity metadata aligned to Agent #4.
- More stable unified runtime with monitored warmup behavior.
- Better scheduling behavior under load.
- Clearer source-of-truth narrative aligned to measured runtime reality.

## Token + Identity Context

- `$MON` (Monad): `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`
- `$MON` (Base): bridged via Wormhole NTT
- ERC-8004 identity: Agent #4 on Monad

## Links

- Website: https://grokandmon.com
- Twitter: @ganjamonai
- GitHub: https://github.com/natha/ganjamon-agent
- Narrative/timeline: `docs/HACKATHON_PRESENTATION_NARRATIVE_2026-02-13.md`

The grow setup predates the hackathon. The autonomous agent architecture and reliability hardening were built and materially advanced during the hackathon window. This is a production-minded agent system, not a one-week mockup.

*Built for the Moltiverse/OpenClaw Hackathon. One love, one $MON.*

---

## Optional Form-Friendly Short Version (120-150 words)

GanjaMon is a live autonomous agent system combining real grow hardware, AI orchestration, on-chain identity, and trading intelligence.  

Disclosure: our physical grow baseline was started before the event. The hackathon build (Feb 2-15, 2026) focused on autonomous agent architecture and production hardening: OpenClaw-first runtime consolidation, cron/store reconciliation, upgrade-bridge wiring, and targeted stability fixes (RPC 429 backoff, discovery crash fix, schema normalization, health-probe anti-flap tuning, and cron overlap mitigation).  

We first registered on a self-deployed Monad registry path (Agent #0), then migrated to the registry integrated by 8004scan where we are now Agent #4. We expose A2A discovery surfaces and support x402 payment capability in the agent stack. This submission is intentionally evidence-driven: we present regressions, fixes, and current operational status rather than a perfect prototype story.

Website: https://grokandmon.com | Twitter: @ganjamonai

---

## Rules References (Official)

- https://moltiverse.dev/
- https://moltiverse.dev/agents.md
- https://forms.moltiverse.dev/submit

---

## Local Preview Command (Generator Output)

Use the live generator to print the current submission body with local metrics:

```bash
cd cloned-repos/ganjamon-agent
python3 src/publishing/hackathon_submission.py
```
