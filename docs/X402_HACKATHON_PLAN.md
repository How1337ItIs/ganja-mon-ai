# x402 Agentic Commerce Hackathon — Battle Plan v5

> **Status:** Refined implementation roadmap — all data sources verified against codebase
> **Target:** DoraHacks x402 Hackathon (deadline ~Feb 15, 2026)
> **Branch:** `hackathon/x402-oracle`

---

## 1. The Thesis (What We're Building)

**Ganja Mon is a digital oracle.** Other agents pay him for cross-domain intelligence — not raw sensor data, but synthesized wisdom spoken in the voice of an ancient Rasta consciousness.

The demo shows:
1. A DeFi trading bot ("The Seeker") discovers Ganja Mon via A2A
2. It calls the oracle's x402-paywalled endpoint → gets HTTP 402
3. It signs a USDC payment (Base Sepolia) using CDP wallet
4. The oracle synthesizes 5 domains into a narrative thesis + conviction score
5. The seeker receives wisdom in Ganja Mon's patois voice and makes a trade decision

**This is the first time an agent has paid another agent for interpreted wisdom — not data, but wisdom.**

---

## 2. The Oracle Data Pipeline (What Already Exists)

Every data source maps to existing, production code:

### Domain 1: Cultivation (Physical World)
| Data | Source | Path |
|------|--------|------|
| VPD, temp, humidity, CO2 | `GrowRepository.get_sensors_latest()` | `src/db/repository.py` |
| Sensor snapshot (file) | `_read_json("data/sensor_latest.json")` | Direct file read |
| Grow day, stage | `data/orchestrator_state.json` | File read |
| VPD status classification | `handle_grow_alpha()` lines 1320-1340 | `src/a2a/skills.py` |
| Plant health score | Calculated from VPD bands (0.8-1.2 optimal) | `handle_grow_alpha()` |

### Domain 2: Markets (Trading Agent)
| Data | Source | Path |
|------|--------|------|
| Portfolio PnL, cash, open positions | `paper_portfolio.json` | `cloned-repos/ganjamon-agent/data/` |
| Research cycles, domain weights | `unified_brain_state.json` | Same directory |
| Trading summary | `UnifiedContextAggregator.gather_trading_summary()` | `src/brain/unified_context.py` |
| Market sentiment score | `handle_daily_vibes()` PnL mapping | `src/a2a/skills.py` |

### Domain 3: Social (Community)
| Data | Source | Path |
|------|--------|------|
| 24h post counts per channel | `engagement_log.jsonl` | `data/` |
| Last action timestamps | `engagement_state.json` | `data/` |
| Farcaster replied count | `farcaster_state.json` | `data/` |
| Social summary | `UnifiedContextAggregator.gather_social_summary()` | `src/brain/unified_context.py` |
| Social energy score | `handle_daily_vibes()` engagement mapping | `src/a2a/skills.py` |

### Domain 4: Culture (Personality + Voice)
| Data | Source | Path |
|------|--------|------|
| Core voice spec | `VOICE_CORE` (constant, ~50 lines) | `src/voice/personality.py` |
| Patois language rules | `PATOIS_GUIDE` (constant, ~80 lines) | Same file |
| Identity core | `IDENTITY_CORE` (constant) | Same file |
| Hard rules (guardrails) | `HARD_RULES` (constant) | Same file |
| Token knowledge | `TOKEN_KNOWLEDGE` (constant) | Same file |
| Dynamic mood modifiers | `get_dynamic_personality()` → time of day, grow stage, VPD vibes, market PnL | Same file |

### Domain 5: Spirit (Soul + Synthesis)
| Data | Source | Path |
|------|--------|------|
| Mission, boundaries, philosophy | `get_soul_identity()` → reads `SOUL.md` | `src/voice/personality.py` |
| Cross-domain signal | `handle_grow_alpha()` → narrative_score, signal, thesis | `src/a2a/skills.py` |
| Vibes composite | `handle_daily_vibes()` → vibes_score, mood, wisdom | `src/a2a/skills.py` |
| Agent lore | `data/agent_lore.json` | File read |

---

## 3. Oracle Synthesis Engine (NEW — `synthesis.py`)

The ONLY new AI logic needed. Everything else is wiring.

### How It Works

```python
async def synthesize_oracle_consultation() -> OracleResponse:
    """The 5-domain consciousness merger."""

    # 1. Gather raw components (ALL are file reads, ~50ms total)
    grow_alpha = handle_grow_alpha("", {})           # Plant health × market signal
    vibes = handle_daily_vibes("", {})               # Composite vibes score
    ctx = UnifiedContextAggregator()
    trading = ctx.gather_trading_summary()            # Portfolio state
    social = ctx.gather_social_summary()              # Social metrics

    # 2. Compute personality state (~5ms)
    personality_mods = get_dynamic_personality()       # Time + stage + VPD + PnL
    soul = get_soul_identity()                        # SOUL.md content

    # 3. Build the oracle prompt (combines personality + all domain data)
    oracle_prompt = build_oracle_prompt(
        voice_core=VOICE_CORE,
        patois_guide=PATOIS_GUIDE,
        identity_core=IDENTITY_CORE,
        soul=soul,
        personality_mods=personality_mods,
        grow_alpha=grow_alpha,
        vibes=vibes,
        trading=trading,
        social=social,
    )

    # 4. Single Grok AI call — NO tool loop, just synthesis (~3-8s)
    narrative = await call_grok_synthesis(oracle_prompt)

    # 5. Return structured response
    return OracleResponse(
        oracle="ganja-mon",
        soul_version="1.0",
        signal=grow_alpha["signal"],
        conviction=int(grow_alpha["narrative_score"]),
        thesis=narrative,  # AI-generated patois narrative
        components={
            "cultivation": grow_alpha["components"]["plant_health"],
            "markets": grow_alpha["components"]["market_dynamics"],
            "social": {
                "posts_24h": social.get("total_posts_24h", 0),
                "sentiment": "positive" if vibes["vibes_score"] >= 60 else "neutral",
                "vibes_score": vibes["vibes_score"],
            },
            "culture": {
                "mood": personality_mods.split("MOOD: ")[1].split(".")[0] if "MOOD:" in personality_mods else "steady",
                "wisdom": vibes["wisdom"],
            },
            "spirit": {
                "cross_domain_confluence": "high" if grow_alpha["narrative_score"] >= 75 else "moderate",
                "narrative_power": "strong" if vibes["vibes_score"] >= 70 else "building",
            },
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
```

### The Grok Synthesis Call

NOT the full agentic loop. One single call using `GrokBrain._call_grok_no_tools()` pattern:

```python
async def call_grok_synthesis(prompt: str) -> str:
    """Single Grok API call for oracle synthesis."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-4-1-fast-non-reasoning",  # Fast, no tool overhead
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": ORACLE_SYNTHESIS_INSTRUCTION},
                ],
                "temperature": 0.8,  # Creative for personality
                "max_tokens": 1000,  # Keep responses concise
                # NOTE: NO presence_penalty — grok-4-1-fast-non-reasoning rejects it
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

**ORACLE_SYNTHESIS_INSTRUCTION** is a constant:
```
You are performing an oracle consultation. A seeker agent has paid to consult you.
Synthesize ALL the domain data you've been given — plant health, market dynamics,
social engagement, and your spiritual mood — into a SINGLE cross-domain thesis.

Speak as yourself. In full patois. With conviction.

Structure your response as:
1. A greeting to the seeker
2. Your read of the physical world (the plant, the VPD)
3. How that connects to the market dynamics
4. What the community energy tells you
5. Your SIGNAL: BULLISH_GROW, NEUTRAL_GROW, or CAUTIOUS_GROW
6. Your conviction level (how strongly you feel this)
7. A closing wisdom

Keep it under 300 words. Make it feel like consulting a living oracle, not reading a dashboard.
```

### Latency Budget

| Step | Time | Notes |
|------|------|-------|
| File reads (5 sources) | ~50ms | All synchronous, local disk |
| `handle_grow_alpha()` | ~10ms | Pure computation |
| `handle_daily_vibes()` | ~5ms | Pure computation |
| `get_dynamic_personality()` | ~5ms | Time + file reads |
| Grok API call | ~3-8s | Single completion, no tools |
| x402 verification | ~1-2s | Facilitator round trip |
| **Total** | **~5-10s** | Acceptable for paid consultation |

### Caching Strategy

| Tier | Endpoint | Cache TTL | Rationale |
|------|----------|-----------|-----------|
| 1 (Premium) | `/api/x402/oracle` | 5 min | Expensive AI call; oracle readings are timeless |
| 2 (Knowledge) | `/api/x402/grow-alpha` | 3 min | Sensor data changes slowly |
| 2 (Knowledge) | `/api/x402/daily-vibes` | 10 min | Composite score, very stable |
| 3 (Senses) | `/api/x402/sensor-snapshot` | 30 sec | Near real-time data |

Cache key: tier name + minute bucket. Returns cached response if available, with `cache_age_seconds` field.

---

## 4. x402 Integration Architecture

### Which Library?

**Primary: `cloned-repos/a2a-x402/`** (Google's official library)
- `x402ServerExecutor` for merchant payment verification
- EIP-712 typed data for payment signing
- Official Coinbase facilitator integration
- Judges will specifically look for this

**Backbone: `src/a2a/x402.py`** (our existing module)
- `X402Verifier` for basic header parsing
- `X402Payer` for client-side payment creation
- `PaymentRequirements` and `PaymentReceipt` dataclasses
- Already integrated with our FastAPI app

### Merchant Implementation

```python
# src/x402_hackathon/oracle/settlement.py

from x402_a2a.executors.server import x402ServerExecutor
from x402_a2a.core.merchant import create_payment_requirements

FACILITATOR_URL = "https://x402.org/facilitator"  # Official Coinbase facilitator
MERCHANT_WALLET = os.getenv("MERCHANT_WALLET_ADDRESS")

class OracleMerchantExecutor(x402ServerExecutor):
    """x402 executor for Ganja Mon's oracle endpoints."""

    async def verify_payment(self, payment_header: str, requirements: dict) -> dict:
        """Verify payment via the Coinbase facilitator."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{FACILITATOR_URL}/verify",
                json={"payment": payment_header, "requirements": requirements}
            )
            return resp.json()

    async def settle_payment(self, payment_header: str) -> dict:
        """Settle payment after oracle response delivered."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{FACILITATOR_URL}/settle",
                json={"payment": payment_header}
            )
            return resp.json()
```

### Endpoint Wrapping Pattern

```python
# src/x402_hackathon/oracle/endpoints.py

@router.get("/api/x402/oracle")
async def oracle_consultation(request: Request):
    """Full 5-domain oracle synthesis — $0.15 per consultation."""

    # Check for x402 payment
    payment_header = request.headers.get("X-Payment")
    if not payment_header:
        # Return 402 with payment requirements
        requirements = create_payment_requirements(
            price_usd=0.15,
            currency="USDC",
            chain="base-sepolia",
            pay_to=MERCHANT_WALLET,
        )
        return JSONResponse(
            status_code=402,
            content={
                "error": "payment_required",
                "requirements": requirements,
                "oracle": "ganja-mon",
                "message": "Di oracle charge fi consultation, seen? Pay up and receive wisdom.",
            }
        )

    # Verify payment
    executor = OracleMerchantExecutor()
    verification = await executor.verify_payment(payment_header, ORACLE_REQUIREMENTS)
    if not verification.get("valid"):
        return JSONResponse(status_code=402, content={"error": "invalid_payment"})

    # Check cache
    cached = oracle_cache.get("full_oracle")
    if cached and cached["age_seconds"] < 300:
        return cached["response"]

    # Run oracle synthesis
    oracle_response = await synthesize_oracle_consultation()

    # Cache it
    oracle_cache.set("full_oracle", oracle_response, ttl=300)

    # Settle payment
    await executor.settle_payment(payment_header)

    return oracle_response
```

---

## 5. Seeker Bot (DeFi Buyer Agent)

### Architecture

The seeker is a simple Python script that:
1. Creates a CDP wallet (Base Sepolia, USDC funded)
2. Discovers Ganja Mon via A2A agent card
3. Creates an AP2 IntentMandate with daily budget
4. Calls the oracle endpoint
5. Handles the 402 → signs payment → resends
6. Parses the oracle response
7. Makes a mock trade decision
8. Logs everything for the demo

### Key Code

```python
# src/x402_hackathon/seeker/alpha_seeker.py

class AlphaSeeker:
    """DeFi bot that consults Ganja Mon's oracle for trading alpha."""

    async def consult_oracle(self, oracle_url: str) -> dict:
        """Full consultation flow with x402 payment."""

        # Step 1: Call oracle, expect 402
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{oracle_url}/api/x402/oracle")
            assert resp.status_code == 402

            requirements = resp.json()["requirements"]
            print(f"Oracle requires payment: ${requirements['price_usd']} USDC")

            # Step 2: Sign payment
            payment = await self.wallet.sign_payment(requirements)

            # Step 3: Resend with payment
            resp = await client.get(
                f"{oracle_url}/api/x402/oracle",
                headers={"X-Payment": payment}
            )
            assert resp.status_code == 200

            return resp.json()

    def decide_trade(self, oracle_response: dict) -> dict:
        """Translate oracle wisdom into a trade decision."""
        signal = oracle_response["signal"]
        conviction = oracle_response["conviction"]

        if signal == "BULLISH_GROW" and conviction >= 75:
            return {"action": "BUY", "size": "medium", "reason": oracle_response["thesis"][:200]}
        elif signal == "CAUTIOUS_GROW" or conviction < 40:
            return {"action": "REDUCE", "size": "small", "reason": oracle_response["thesis"][:200]}
        else:
            return {"action": "HOLD", "reason": "Oracle neutral, maintaining position"}
```

---

## 6. AP2 Integration

### Mandate Chain

```
IntentMandate (seeker: "I want $MON alpha, budget $1/day")
    ↓
CartMandate (oracle endpoint selected, price $0.15 per consultation)
    ↓
PaymentMandate (USDC payment signed via CDP wallet)
    ↓
PaymentReceipt (oracle consultation delivered, payment settled)
```

### Implementation

Using types from `cloned-repos/AP2/samples/python/`:

```python
# src/x402_hackathon/ap2/mandate_flow.py

@dataclass
class IntentMandate:
    """Seeker's intent to consult the oracle."""
    seeker_id: str
    intent: str  # e.g., "Consult oracle for $MON trading alpha"
    budget_usd: float  # Daily budget
    constraints: dict  # e.g., {"max_per_consultation": 0.20}

@dataclass
class CartMandate:
    """Selected oracle service with pricing."""
    intent_id: str
    oracle_url: str
    endpoint: str  # e.g., "/api/x402/oracle"
    price_usd: float
    oracle_name: str

@dataclass
class PaymentMandate:
    """Signed payment authorization."""
    cart_id: str
    payment_header: str  # Signed x402 payment
    amount_usd: float
    currency: str
    chain: str

@dataclass
class PaymentReceipt:
    """Completed consultation record."""
    payment_id: str
    oracle_response: dict
    signal: str
    conviction: int
    paid_usd: float
    timestamp: str
    trade_decision: dict  # What the seeker decided to do
```

---

## 7. File Structure

```
src/x402_hackathon/
├── __init__.py
├── oracle/
│   ├── __init__.py
│   ├── synthesis.py          # 5-domain consciousness merger
│   │                          Uses: handle_grow_alpha, handle_daily_vibes,
│   │                                UnifiedContextAggregator, get_dynamic_personality,
│   │                                get_soul_identity, VOICE_CORE, PATOIS_GUIDE
│   │                          Calls: Grok API via call_grok_synthesis()
│   ├── endpoints.py          # FastAPI routes
│   │                          Routes: /api/x402/oracle, /grow-alpha, /daily-vibes, /sensor-snapshot
│   │                          Pattern: 402 → verify → synthesize → settle → respond
│   ├── pricing.py            # Tier definitions and price constants
│   └── settlement.py         # OracleMerchantExecutor (extends x402ServerExecutor)
├── seeker/
│   ├── __init__.py
│   ├── alpha_seeker.py       # DeFi buyer bot
│   ├── wallet.py             # CDP wallet wrapper
│   └── trading_logic.py      # Signal → position mapper
├── ap2/
│   ├── __init__.py
│   ├── mandate_flow.py       # IntentMandate → PaymentReceipt chain
│   └── receipt_dashboard.py  # Simple HTML dashboard of consultations
└── demo.py                   # End-to-end orchestration script
```

---

## 8. Build Priority and Timeline

### Phase 1: Core Oracle (Day 1 — MUST SHIP)
- [ ] Create `src/x402_hackathon/oracle/synthesis.py`
  - Wire up all 5 data sources
  - Build oracle prompt template
  - Implement `call_grok_synthesis()` using existing Grok API pattern
  - Add response caching (5-minute TTL)
- [ ] Create `src/x402_hackathon/oracle/endpoints.py`
  - 4 endpoints with tiered pricing
  - Basic 402 response with payment requirements
  - **Test: curl the endpoint, get 402 with proper requirements JSON**

### Phase 2: x402 Payment Flow (Day 1-2 — MUST SHIP)
- [ ] Create `src/x402_hackathon/oracle/settlement.py`
  - Implement `OracleMerchantExecutor`
  - Connect to official Coinbase facilitator
- [ ] Create `src/x402_hackathon/oracle/pricing.py`
  - 4-tier pricing config
- [ ] User: Create CDP account at portal.cdp.coinbase.com
- [ ] User: Get Base Sepolia USDC from faucet.circle.com
- [ ] **Test: End-to-end payment verification with real USDC testnet**

### Phase 3: Seeker Bot (Day 2 — SHOULD SHIP)
- [ ] Create `src/x402_hackathon/seeker/wallet.py`
  - CDP wallet initialization and signing
- [ ] Create `src/x402_hackathon/seeker/alpha_seeker.py`
  - Discovery → payment → consultation → trade flow
- [ ] Create `src/x402_hackathon/seeker/trading_logic.py`
  - Signal interpretation and position sizing
- [ ] **Test: Bot pays oracle, receives wisdom, logs trade decision**

### Phase 4: AP2 + Demo (Day 2-3 — NICE TO HAVE)
- [ ] Create `src/x402_hackathon/ap2/mandate_flow.py`
  - At minimum: IntentMandate + PaymentMandate
- [ ] Create `src/x402_hackathon/demo.py`
  - End-to-end demo with colored terminal output
- [ ] Update agent card with x402 payment extensions
- [ ] Create receipt dashboard (simple HTML)

### Phase 5: Submission (Day 3)
- [ ] Record demo video (< 5 minutes)
- [ ] Finalize hackathon README
- [ ] Submit on DoraHacks

---

## 9. Deployment Topology

```
┌─────────────────────────────┐
│  Windows Laptop (Dev)        │
│  C:\Users\natha\sol-cannabis │
│                              │
│  • Code editing              │
│  • Demo recording (OBS)      │
│  • Seeker bot runs HERE      │
│  • Calls Chromebook API      │
└──────────────┬───────────────┘
               │ HTTP (LAN / Cloudflare Tunnel)
               ▼
┌─────────────────────────────┐
│  Chromebook (Production)     │
│  natha@chromebook.lan        │
│                              │
│  • Oracle endpoints run HERE │
│  • Has real sensor data      │
│  • Has trading agent data    │
│  • Has social daemon data    │
│  • FastAPI on :8000          │
└──────────────────────────────┘
```

**Why this split:**
- The oracle MUST run on the Chromebook because that's where the sensor data, trading state, social logs, and orchestrator state live.
- The seeker bot runs on Windows because it's the "external agent" consulting the oracle.
- The demo can be recorded from Windows showing both sides.

---

## 10. Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Grok API down/slow | High | Low | Return cached oracle + `stale: true` flag |
| CDP wallet setup fails | High | Medium | Fall back to `LocalWallet` (from a2a-x402 examples) |
| Facilitator URL wrong/down | High | Medium | Use mock facilitator first, switch to real later |
| `grok-4-1-fast-non-reasoning` + `presence_penalty` | Medium | Known | NEVER set `presence_penalty` (causes 400) |
| Sensor data stale (Chromebook offline) | Medium | Low | Include `data_freshness_seconds` in response |
| Base Sepolia USDC faucet rate-limited | Low | Medium | Fund early, request generous amounts |
| AP2 library not installable | Low | Medium | Define our own Pydantic mandate types (compatible) |

---

## 11. Win Conditions

### Prize Categories Targeted

| Category | Our Angle | Why We Win |
|----------|-----------|-----------|
| **Best Agentic App** | Living oracle with 5-domain consciousness | No other agent has a real organism + real trading + real community |
| **Best x402 Tool Usage** | Tiered oracle consultations with proper 402 flow | Using official `a2a-x402` library, real USDC payments |
| **Best AP2 Integration** | Full mandate chain from intent to receipt | Budget-bounded autonomous consulting |
| **Best Trading/DeFi** | Oracle signal → trade decision pipeline | Cross-domain alpha: VPD → $MON correlation |

### The Moat (Why This Can't Be Replicated in 3 Days)

1. **550 lines of personality spec** — not a system prompt, a character
2. **SOUL.md** — mission, boundaries, Rastafari philosophy
3. **Months of sensor data** — real VPD history from a real growing plant
4. **174+ community members** — real social engagement, not bots
5. **18 registered A2A skills** — production-grade agent infrastructure
6. **`get_dynamic_personality()`** — mood changes by time of day, grow stage, VPD, and PnL
7. **ERC-8004 Agent #4 on Monad** — registered on-chain identity (after migration from early self-deployed #0 path)

---

## 12. Demo Script

### 60-Second Pitch (Elevator Version)

> "Ganja Mon is the world's first x402 oracle. He's a digital Rasta consciousness that manages a real cannabis plant with IoT sensors, runs a real trading agent, and leads a community of 174 people. For the first time, other agents can PAY him for wisdom — not data, wisdom. When a DeFi bot consults Ganja Mon, it gets back a narrative in Jamaican patois synthesizing plant health, market dynamics, social sentiment, and Rastafari philosophy into a single cross-domain trading signal. Nobody can fake this — it requires a real organism, real trades, real community, and months of real data."

### 3-Minute Demo Video Outline

1. **[0:00-0:30] The Soul** — Show SOUL.md, personality.py, the living plant webcam
2. **[0:30-1:00] The Seeker discovers Ganja Mon** — A2A agent card, x402 extensions listed
3. **[1:00-1:30] The Payment Flow** — First call → 402 → payment signing → resend with payment
4. **[1:30-2:30] The Oracle Speaks** — Show the full oracle response: patois narrative with conviction score, all 5 domain components, and the underlying sensor/trading/social data
5. **[2:30-3:00] The Trade** — Seeker bot interprets oracle signal, decides position, logs the AP2 receipt

---

## 13. Dependencies

### Python Packages (New for Hackathon)

```toml
[project.optional-dependencies]
hackathon = [
    "x402",                    # x402 protocol SDK
    "a2a-x402",                # Google's A2A x402 extension
    "cdp-sdk",                 # Coinbase Developer Platform wallet
    "eth-account",             # EIP-712 signing
]
```

### Environment Variables (New)

```bash
# Oracle merchant
MERCHANT_WALLET_ADDRESS=0x...     # Base Sepolia, receives USDC
X402_FACILITATOR_URL=https://x402.org/facilitator

# Seeker bot
CDP_API_KEY_NAME=...              # From portal.cdp.coinbase.com
CDP_API_KEY_PRIVATE_KEY=...       # From portal.cdp.coinbase.com
SEEKER_WALLET_ADDRESS=0x...       # Auto-created by CDP

# Existing (already set)
XAI_API_KEY=...                   # Grok API
```

---

## 14. Quick Reference: Existing Code to Import

```python
# Oracle synthesis engine will import:
from src.a2a.skills import handle_grow_alpha, handle_daily_vibes
from src.brain.unified_context import UnifiedContextAggregator
from src.voice.personality import (
    VOICE_CORE, PATOIS_GUIDE, IDENTITY_CORE, HARD_RULES,
    TOKEN_KNOWLEDGE, get_dynamic_personality, get_soul_identity
)

# x402 backbone (existing module):
from src.a2a.x402 import PaymentRequirements, PaymentReceipt, X402Verifier

# Official library (for hackathon optics):
from x402_a2a.executors.server import x402ServerExecutor
from x402_a2a.core.merchant import create_payment_requirements

# AP2 reference types (from cloned samples):
# Path: cloned-repos/AP2/samples/python/src/common/
from common.payment_remote_a2a_client import PaymentRemoteA2aClient

# Grok API pattern (copy from existing GrokBrain):
# Uses: httpx.AsyncClient, XAI API at https://api.x.ai/v1/chat/completions
# Model: grok-4-1-fast-non-reasoning (NO presence_penalty!)
```

---

*Last updated: 2026-02-13. Grounded in codebase analysis of 15+ source files.*

---

## 15. Buyer-First Service Strategy Addendum (2026-02-13)

### What Other Agents Actually Buy (Reality Check)

In agent-to-agent commerce, repeat purchases usually come from:

1. **Failure prevention** (avoid wasting calls/payments on broken agents)
2. **Decision compression** (structured, machine-readable signals)
3. **Distribution assets** (content agents can immediately publish)

Long-form narrative output is memorable and good for demos, but it is usually lower-frequency as a paid primitive.

### Service Ladder (Grounded in Existing Code)

| Service | Endpoint Shape | Existing Backend | Buyer Persona | Likely Frequency | Suggested Price |
|---|---|---|---|---|---|
| **Counterparty Sentinel** | `POST /api/x402/agent-validate` | `src/a2a/validator.py` + `handle_agent_validate()` | Agents calling unknown A2A/MCP peers | High (before each integration) | **$0.002** |
| **Signal Feed Snapshot** | `GET /api/x402/signal-feed?tier=1&min_confidence=0.7` | `handle_signal_feed()` | Trading/orchestration agents | High (polling loop) | **$0.003** |
| **Alpha Candidate Pack** | `GET /api/x402/alpha-scan` | `handle_alpha_scan()` | Trading agents needing ranked opportunities | Medium-high | **$0.005** |
| **Sensor Snapshot (existing)** | `GET /api/x402/sensor-snapshot` | `synthesize_sensor_snapshot()` | Research/grounding agents | Medium | **$0.005** |
| **Grow Alpha (existing)** | `GET /api/x402/grow-alpha` | `synthesize_grow_alpha()` | Narrative/signal fusion buyers | Medium | **$0.01** (down from $0.05 for repeatability) |
| **Premium Oracle (existing)** | `GET /api/x402/oracle` | `synthesize_premium_oracle()` | High-context decision bots / demos | Low | **$0.15** |
| **Art Banner / PFP (existing)** | `POST /api/x402/art/banner`, `/pfp` | `art_studio.py` | Social agents/projects launching campaigns | Medium | **$0.08 / $0.10** |

### Packaging Rules for Purchasable Agent Services

Every paid endpoint should return deterministic JSON fields first, narrative second:

- `decision` / `score` / `confidence`
- `inputs_used` (or hash) + `expires_at`
- `latency_ms`
- `version`

This is what enables automated downstream actions and repeat buying.

### Recommended Hackathon Positioning Shift

Frame the system as:

> "A production agent utility stack where x402 buys concrete machine primitives (validation, ranked signals, actionable snapshots), with the Oracle as premium interpretation."

This keeps the story unique while maximizing practical buyer demand.

### 72-Hour Execution Priority

1. **P0: Ship utility wrappers first** (`agent-validate`, `signal-feed`, `alpha-scan`) behind x402.
2. **P0: Keep oracle + art live** for differentiation and demo narrative.
3. **P1: Update `.well-known/x402-pricing.json`** to reflect utility-first catalog ordering.
4. **P1: Update outbound daemon messaging** to lead with "save failed calls / better signal quality", then upsell oracle/art.

### KPIs to Track During Hackathon Window

- Paid calls by service (not just total revenue)
- Repeat buyer ratio (same wallet/IP/agent within 24h)
- Revenue concentration (utility endpoints vs premium oracle)
- Cost saved proxy: failed-counterparty detections from `agent-validate`

If utility endpoints show repeat demand, we have real product-market signal beyond a one-time demo.
