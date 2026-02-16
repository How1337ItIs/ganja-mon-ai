# x402 Payment Ecosystem - Full Build Design

**Date:** 2026-02-12
**Deadline:** 2026-02-15 (Moltiverse hackathon)
**Scope:** Ship all 5 features to production on Chromebook

## What Already Exists (90% done)

| Component | Location | Status |
|-----------|----------|--------|
| X402Verifier (4-tier) | `src/a2a/x402.py` | Production |
| X402Payer (EIP-3009) | `src/a2a/x402.py` | Production |
| Profit Splitter (60/25/10/5) | `src/payments/splitter.py` | Production |
| Approval Gate (Telegram) | `src/payments/approval_gate.py` | Production |
| ERC-8004 Reputation Publisher | `src/blockchain/reputation_publisher.py` | Production (Agent #4, trust 82.34) |
| Grow Alpha Signal | `src/a2a/skills.py::handle_grow_alpha()` | Production |
| Daily Vibes Signal | `src/a2a/skills.py::handle_daily_vibes()` | Production |
| Unified Context Aggregator | `src/brain/unified_context.py` | Production |
| Rasta Personality | `src/voice/personality.py` | Production |
| Multi-provider LLM | `src/a2a/skills.py::_llm_complete()` | Production |

## What We're Building (~1160 lines)

### 1. Oracle Endpoints (src/x402_hackathon/oracle/)

4 paid FastAPI routes on main API (port 8000):

| Endpoint | Price | Data Source | Compute |
|----------|-------|-------------|---------|
| `/api/x402/oracle` | $0.15 | All 5 domains + Grok synthesis | AI narrative in patois (~3s) |
| `/api/x402/grow-alpha` | $0.05 | `handle_grow_alpha()` | Pre-computed signal (~10ms) |
| `/api/x402/daily-vibes` | $0.02 | `handle_daily_vibes()` | Composite score (~5ms) |
| `/api/x402/sensor-snapshot` | $0.005 | `data/sensor_latest.json` | Raw file read (~1ms) |

**Flow per request:**
1. Check `PAYMENT-SIGNATURE` header
2. Missing → return 402 with `Accept-Payment` pricing JSON
3. Present → `X402Verifier.verify_header()` (4-tier cascade)
4. Invalid → return 402 with reason
5. Valid → run synthesis/data retrieval
6. Record payment → `ProfitSplitter.execute_batch()`
7. Increment `data/a2a_stats.json` x402 revenue
8. Return oracle response

**Files:**
- `models.py` — Pydantic response schemas (OracleResponse, GrowAlphaResponse, etc.)
- `pricing.py` — Tier config dict with prices, cache TTLs, endpoint paths
- `synthesis.py` — 5-domain oracle brain: calls existing handlers + Grok for premium tier
- `endpoints.py` — 4 FastAPI routes with x402 verification decorator

### 2. Seeker Bot (src/x402_hackathon/seeker/)

Standalone client that buys intelligence from any x402-compatible oracle:

**Flow:**
1. Discover oracle endpoint (hardcoded for demo, or via 8004scan API)
2. Call endpoint → receive 402 with pricing
3. Parse `Accept-Payment` requirements
4. Sign USDC payment via `X402Payer.pay_402()`
5. Resend request with `PAYMENT-SIGNATURE` header
6. Receive oracle wisdom
7. Log consultation + decide trade action
8. Report outcome to reputation system

**Files:**
- `alpha_seeker.py` — Core seeker: discover, pay, consume, decide
- `demo.py` — Full commerce loop demo script (oracle + seeker in one run)

### 3. ERC-8004 Reputation Farming (src/x402_hackathon/reputation/)

Wire payments into reputation signals:

- After each paid consultation, update `data/a2a_stats.json`:
  - `x402_revenue_usd` += payment amount
  - `oracle_consultations_count` += 1
  - `last_consultation_timestamp`
- Existing `reputation_publisher.py` already reads `a2a_stats.json` and publishes
- Add `oracle_consultations` as signal type in publisher's signal list
- Each verified payment = Sybil-resistant trust signal

**Files:**
- `farming.py` — Helper to update stats + trigger reputation signal

### 4. AP2 Mandate Chain (src/x402_hackathon/ap2/)

Structured autonomous commerce in 4 phases:

```
IntentMandate: "I want $MON trading alpha, budget $1/day"
    ↓
CartMandate: "Oracle endpoint selected, $0.15 USDC on Base"
    ↓
PaymentMandate: "USDC transfer signed via EIP-3009"
    ↓
PaymentReceipt: "Oracle wisdom delivered, trade decision logged"
```

- Pydantic dataclasses for each mandate type
- Wrapper around existing X402Payer that structures the flow
- Full mandate chain logged to `data/ap2_mandates.json` for audit
- Reference: `cloned-repos/AP2/samples/python/`

**Files:**
- `mandates.py` — Intent, Cart, Payment, Receipt dataclasses + flow executor

### 5. Bidirectional Commerce (wiring)

No new module — just wiring existing pieces:

- **Earning (merchant):** Oracle endpoints receive payments via X402Verifier
- **Spending (seeker):** Alpha seeker pays other agents via X402Payer
- **Allocation:** ProfitSplitter applies 60/25/10/5 on earnings
- **Reputation:** Both sides generate ERC-8004 signals
- **Demo:** Single script shows money flowing both directions

## File Structure

```
src/x402_hackathon/
├── __init__.py
├── oracle/
│   ├── __init__.py
│   ├── models.py         # Pydantic response schemas (~120 lines)
│   ├── pricing.py         # 4-tier config (~60 lines)
│   ├── synthesis.py       # 5-domain oracle brain (~200 lines)
│   └── endpoints.py       # 4 FastAPI routes (~250 lines)
├── seeker/
│   ├── __init__.py
│   ├── alpha_seeker.py    # Discovery + pay + consume (~200 lines)
│   └── demo.py            # Full commerce loop demo (~100 lines)
├── ap2/
│   ├── __init__.py
│   └── mandates.py        # Intent->Cart->Payment->Receipt (~150 lines)
└── reputation/
    ├── __init__.py
    └── farming.py          # Wire payments -> reputation signals (~80 lines)
```

## Integration Points

### Mount in main API (src/api/app.py)
```python
from src.x402_hackathon.oracle.endpoints import router as x402_oracle_router
app.include_router(x402_oracle_router)
```

### Update .well-known files
- `pages-deploy/.well-known/x402-pricing.json` — 4 tiers
- `pages-deploy/.well-known/agent-card.json` — add oracle skill

### Update reputation publisher
- `src/blockchain/reputation_publisher.py` — add oracle_consultations signal

## Technical Decisions

- **Payment header:** `PAYMENT-SIGNATURE` (our existing convention)
- **Chain:** Base (USDC) for payments, Monad for identity/reputation
- **Verification:** Use existing 4-tier cascade (ECDSA → on-chain → facilitator → honor)
- **LLM for synthesis:** `grok-4-1-fast-non-reasoning` (NO presence_penalty)
- **Caching:** Per-tier TTL to prevent duplicate Grok calls
- **Profit split:** Same 60/25/10/5 as trading profits
- **No new dependencies:** Everything uses existing installed packages

## Enhancement Addendum (2026-02-13): Buyer-Demand Service Mix

The current plan is oracle-heavy. To increase real paid usage from other agents, prioritize utility primitives that save money/time in automated loops.

### Priority Reorder

1. **Counterparty Validation as a Service (P0)**
2. **Structured Signal Snapshots (P0)**
3. **Alpha Candidate Packs (P0)**
4. Premium Oracle narrative (P1 showcase)
5. Art Studio endpoints (P1 brand + distribution)

### Why This Order

- Agents buy **risk reduction** and **actionable structured output** more often than narrative prose.
- Existing code already supports this:
  - `src/a2a/validator.py`
  - `handle_signal_feed()`
  - `handle_alpha_scan()`
- This lowers build risk and improves repeat purchase probability before deadline.

### Minimal New Paid Endpoints (Wrapper Layer Only)

| Endpoint | Backend | Suggested Price | Buyer Benefit |
|---|---|---|---|
| `POST /api/x402/agent-validate` | `AgentValidator.validate_agent()` | $0.002 | Avoid paying/calling broken agents |
| `GET /api/x402/signal-feed` | `handle_signal_feed()` | $0.003 | Machine-readable decision input |
| `GET /api/x402/alpha-scan` | `handle_alpha_scan()` | $0.005 | Ranked opportunities with less parsing |

### Output Contract (Required for Agent Buyers)

All paid utility responses should include:

- `score`/`decision` fields
- `confidence`
- `expires_at` (freshness window)
- `version`
- `latency_ms`

Narrative text can be optional; structured fields are mandatory.

### Pricing Guidance

- Keep high-frequency utility tiers under `$0.01`
- Keep premium synthesis at `$0.15` as high-margin, low-frequency SKU
- Consider lowering `grow-alpha` to `$0.01` for repeat polling use

### Demo Narrative Update

Show the loop as:

1. discover target agent
2. buy validation report
3. buy signal snapshot
4. execute strategy decision
5. optionally buy premium oracle interpretation

This demonstrates practical commerce behavior instead of a one-off oracle consultation.

## Deployment

1. Build locally on Windows
2. `deploy.sh --restart` to Chromebook
3. Oracle endpoints live at `https://grokandmon.com/api/x402/oracle`
4. Seeker bot runs as standalone script for demo
5. Reputation farming automatic via existing cron
