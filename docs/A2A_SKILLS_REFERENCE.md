# A2A Skills Reference — GanjaMon AI v3.0.0

> **20 skills** across 4 tiers. The most feature-rich agent card in the Monad ecosystem.
>
> Agent Card: `https://grokandmon.com/.well-known/agent-card.json`
> Endpoint: `POST https://grokandmon.com/a2a/v1/`

---

## Architecture

```
Caller ──JSON-RPC──▶ /a2a/v1/ ──▶ Rate Limiter ──▶ x402 Verifier ──▶ Skill Router
                                                                          │
                     ┌────────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │   Original 5 Skills     │   src/api/a2a.py
        │   (alpha-scan, etc.)    │
        └─────────────────────────┘
        ┌────────────┴────────────┐
        │   15 New Skills         │   src/a2a/skills.py
        │   (grow-oracle, etc.)   │
        └─────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │   AI Provider Cascade   │   _llm_complete() / _vision_analyze()
        │   xAI → Gemini → OR    │
        └─────────────────────────┘
```

### AI Provider Cascade

All AI-powered skills use a three-provider failover chain:

| Priority | Provider | Text Model | Vision Model |
|----------|----------|------------|--------------|
| 1 | **xAI (Grok)** | `grok-3-mini` | `grok-2-vision-1212` |
| 2 | **Gemini** | `gemini-2.0-flash` | `gemini-2.0-flash` |
| 3 | **OpenRouter** | `llama-3.3-70b-instruct` | `gemini-2.0-flash-001` |

Env vars: `XAI_API_KEY` / `GROK_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`

---

## Calling Convention (JSON-RPC 2.0)

```json
POST /a2a/v1/
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "message/send",
  "params": {
    "skill": "vpd-calculator",
    "message": "Calculate VPD",
    "temp_f": 78,
    "humidity": 55
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "taskId": "t_abc123",
    "status": "completed",
    "data": { "skill": "vpd-calculator", "result": { "vpd_kpa": 1.163, "status": "optimal" }, ... }
  }
}
```

---

## Tier 1 — Competitive Moat

These skills are powered by real hardware and living data. No other agent can replicate them.

### `grow-oracle`

**Ask GanjaMon anything about cannabis cultivation.**

Synthesizes answers from three knowledge sources: the cultivation grimoire (learned patterns), episodic memory (historical observations), and static cultivation reference docs. Then passes everything to the AI cascade for a natural-language answer in Rasta voice.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes (or use `message`) | The cultivation question |

```json
// Request
{ "skill": "grow-oracle", "question": "What VPD should I target in late veg?" }

// Response
{
  "skill": "grow-oracle",
  "question": "What VPD should I target in late veg?",
  "answer": "Irie, mon! For late veg, I and I run 0.8-1.2 kPa...",
  "grimoire_learnings": "- [vpd_adjustment] Raised humidity helped...",
  "episodic_memories": "- Day 28: VPD at 1.1 kPa, plants vigorous...",
  "source": "grimoire + episodic memory + cultivation reference + AI (xAI/Gemini/OpenRouter)"
}
```

**Data flow:** `Grimoire DB` + `Episodic Memory` + `CULTIVATION_REFERENCE.md` → keyword search → AI synthesis

---

### `sensor-stream`

**Real-time IoT sensor data with anomaly detection.**

Returns the current snapshot from Govee H5075 / Ecowitt GW1100 / WH51 soil probes, plus optional historical time-series data. Automatically flags out-of-range values.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `history` | int | No (default 10, max 50) | Number of historical readings to include |

```json
// Response
{
  "skill": "sensor-stream",
  "current": {
    "temperature_f": 76.2,
    "humidity_pct": 58.3,
    "vpd_kpa": 1.05,
    "co2_ppm": 620,
    "soil_moisture_pct": 45
  },
  "anomalies": [],
  "history_count": 10,
  "history": [ ... ],
  "data_source": "Govee H5075 + Ecowitt GW1100 + WH51 soil probes",
  "refresh_rate_seconds": 120
}
```

**Anomaly thresholds:**
- Temperature: outside 65-85°F
- Humidity: outside 40-70%
- VPD: outside 0.4-1.6 kPa
- CO2: below 400 ppm

---

### `vpd-calculator`

**Environmental intelligence service — the most useful utility skill.**

Send temperature + humidity, receive a full VPD breakdown with growth stage recommendations. Uses the real `src/cultivation/vpd.py` engine (Tetens equation with leaf temperature offset). If no params provided, returns VPD from current live sensors.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `temp_f` | float | No* | Air temperature in Fahrenheit |
| `humidity` | float | No* | Relative humidity (0-100) |
| `leaf_offset_f` | float | No (default 3.0) | Leaf temp offset from air temp |
| `growth_stage` | string | No (default "vegetative") | seedling / vegetative / flowering / late_flower |

*If omitted, uses current sensor readings.

```json
// Response
{
  "skill": "vpd-calculator",
  "input": { "temp_f": 78, "humidity_pct": 55, "leaf_offset_f": 3.0, "growth_stage": "vegetative" },
  "result": {
    "vpd_kpa": 1.163,
    "status": "optimal",
    "recommendation": "VPD optimal for vegetative. Plants are happy!",
    "air_temp_f": 78,
    "humidity_percent": 55,
    "leaf_temp_f": 75
  },
  "recommendations": {
    "target_vpd_kpa": { "seedling": "0.4-0.8", "vegetative": "0.8-1.2", "flowering": "1.0-1.5", "late_flower": "1.2-1.6" },
    "humidity_for_1kpa_vpd": 58.3
  }
}
```

---

### `plant-vision`

**AI-powered plant health assessment from a photo.**

Send an image URL, receive health score, deficiency detection, growth stage analysis, and recommendations. Cascades through Grok Vision → Gemini → OpenRouter vision models.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `image_url` | string | Yes (or use `message`) | URL to a plant image |

```json
// Response
{
  "skill": "plant-vision",
  "image_url": "https://example.com/plant.jpg",
  "analysis": "{ \"health_score\": 82, \"deficiencies\": [\"slight nitrogen\"], ... }",
  "providers": "xAI/Gemini/OpenRouter (first available)"
}
```

---

## Tier 2 — Brand & Personality

Culture-as-a-service. These skills monetize GanjaMon's unique Rasta persona.

### `rasta-translate`

**Convert any English text to authentic Rasta patois.**

Uses the GanjaMon voice rules: "I and I" pronouns, natural Jamaican patois, herb/nature metaphors. Kept light for international audience comprehension.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes (or use `message`) | English text to translate |

```json
// Response
{
  "skill": "rasta-translate",
  "original": "The market is looking bullish today",
  "translated": "Di market a look irie today, mon! Green candles a grow like di herb inna di garden, seen?",
  "providers": "xAI/Gemini/OpenRouter (first available)"
}
```

---

### `daily-vibes`

**Composite vibes score — GanjaMon's unique wellness oracle.**

Fuses three data sources into a single 0-100 vibes number:
- **Plant health (45%):** Based on current VPD reading
- **Market sentiment (30%):** From trading agent's PnL
- **Social energy (25%):** From engagement metrics

Includes a random Rasta wisdom quote from a curated 12-quote bank.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| *(none required)* | | | Returns current vibes snapshot |

```json
// Response
{
  "skill": "daily-vibes",
  "vibes_score": 72,
  "mood": "🌿 BLESSED — Good energy flowing",
  "breakdown": { "plant_health": 90, "market_sentiment": 70, "social_energy": 40 },
  "wisdom": "Di plant know di rhythm — I and I just follow.",
  "greeting": "Blessed day from GanjaMon! Vibes at 72/100 — 🌿 BLESSED — Good energy flowing"
}
```

**Mood tiers:** 🔥 IRIE (80+) · 🌿 BLESSED (60-79) · ☁️ NEUTRAL (40-59) · 🌧️ LOW (<40)

---

### `ganjafy`

**Rasta-transform images or text.**

For images, returns a link to the Ganjafy Cloudflare Worker (`ganjafy.grokandmon.com`). For text, performs inline AI transformation. Supports 4 image modes: `rasta`, `psychedelic`, `nature`, `dub`.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `image_url` | string | One of these | URL to image for transformation |
| `text` | string | required | Text for Rasta voice transformation |

```json
// Image response
{
  "skill": "ganjafy",
  "ganjafy_url": "https://ganjafy.grokandmon.com/api/transform",
  "input_url": "https://example.com/photo.jpg",
  "modes": ["rasta", "psychedelic", "nature", "dub"]
}

// Text response
{
  "skill": "ganjafy",
  "original_text": "Hello world",
  "ganjafy_text": "Wah gwaan, world! I and I greet di earth inna di fullness of Jah light..."
}
```

---

## Tier 3 — Network Effects & Data Exchange

Skills designed for agent-to-agent collaboration and ecosystem growth.

### `reputation-oracle`

**Query GanjaMon's experience with other agents.**

Searches the A2A reliability database for interaction history, success rates, and trust assessments. Supports lookup by URL, name, or returns network-wide stats.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_url` | string | No | Direct URL lookup |
| `agent_name` | string | No | Fuzzy name search |
| *(none)* | | | Returns network overview |

```json
// URL lookup response (found)
{
  "skill": "reputation-oracle",
  "query": "https://agent.example.com",
  "found": true,
  "agent_name": "AlphaBot",
  "total_interactions": 15,
  "successes": 12,
  "failures": 3,
  "success_rate": 0.8,
  "consecutive_failures": 0,
  "blacklisted": false,
  "trust_assessment": "reliable"
}

// Network overview (no params)
{
  "skill": "reputation-oracle",
  "found": false,
  "network_stats": {
    "agents_tracked": 8,
    "total_interactions": 47,
    "healthy_agents": 6,
    "blacklisted_agents": 2
  }
}
```

**Blacklist rule:** 3+ consecutive failures = blacklisted.

---

### `harvest-prediction`

**Predict harvest date and estimated yield.**

Uses current grow stage, day count, strain data (GDP Runtz timelines), and live VPD quality to estimate days to harvest, date, and yield range.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| *(none required)* | | | Uses live grow state data |

```json
// Response
{
  "skill": "harvest-prediction",
  "strain": { "name": "Granddaddy Purple Runtz (GDP x Runtz)", "veg_days": "45-60", "flower_days": "56-70" },
  "current_stage": "vegetative",
  "grow_day": 30,
  "estimated_days_to_harvest": 83,
  "predicted_harvest_date": "2026-05-03",
  "yield_estimate": "4-6 oz/plant (optimal conditions)",
  "confidence": "medium"
}
```

---

### `strain-library`

**Searchable cannabis genetics database.**

5 strains with detailed grow parameters: genetics, THC, flowering time, terpene profile, optimal VPD/temp/humidity, effects. GDP Runtz entry is the most detailed (our active strain).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `strain` | string | No | Strain name to search (or `message`) |
| *(none)* | | | Returns full catalog listing |

**Available strains:** Granddaddy Purple Runtz, Gelato #33, Blue Dream, OG Kush, Gorilla Glue #4

```json
// Search response
{
  "skill": "strain-library",
  "found": true,
  "strain": {
    "name": "Granddaddy Purple Runtz (GDP x Runtz)",
    "genetics": "GDP (Purple Urkle x Big Bud) x Runtz (Zkittlez x Gelato)",
    "type": "Indica-dominant hybrid (70/30)",
    "thc": "22-28%",
    "flowering_days": "56-70",
    "optimal_vpd": { "veg": "0.8-1.2 kPa", "flower": "1.0-1.5 kPa" },
    "terpenes": ["myrcene", "caryophyllene", "limonene"],
    "effects": ["relaxation", "euphoria", "pain relief", "sedation"]
  }
}
```

---

### `weather-bridge`

**Correlate outdoor weather with indoor grow conditions.**

Other agents send their local weather data; GanjaMon returns correlation insights showing temperature/humidity deltas and environmental recommendations.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `outdoor_temp_f` | float | No | Outdoor temperature |
| `outdoor_humidity` | float | No | Outdoor humidity |
| `pressure_hpa` | float | No | Barometric pressure |

```json
// Response
{
  "skill": "weather-bridge",
  "indoor_conditions": { "temperature_f": 76, "humidity_pct": 55, "vpd_kpa": 1.1 },
  "outdoor_received": { "temperature_f": 62, "humidity_pct": 75 },
  "correlations": [
    { "metric": "temperature_delta", "delta_f": 14.0, "insight": "Indoor is 14.0°F warmer than outside" },
    { "metric": "humidity_delta", "delta_pct": -20.0, "insight": "When outdoor humidity is 75%, indoor dehumidification needs boost" }
  ]
}
```

---

### `teach-me`

**Progressive cultivation tutorial with quizzes.**

Three levels (beginner, intermediate, advanced) with multiple topics per level. Each lesson includes content, key concept, quiz question, and answer. Designed for agents to "learn" cultivation through structured interaction.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `level` | string | No (default "beginner") | beginner / intermediate / advanced |
| `topic` | string | No (default "basics") | Topic within the level |

**Curriculum:**
| Level | Topics |
|-------|--------|
| beginner | basics, watering |
| intermediate | vpd |
| advanced | training |

```json
// Response
{
  "skill": "teach-me",
  "level": "intermediate",
  "topic": "vpd",
  "lesson": {
    "lesson": "Advanced VPD Management",
    "content": "VPD = SVP(leaf) - AVP. Leaf temp is typically 2-5°F below air temp...",
    "key_concept": "Leaf temperature offset is critical for accurate VPD",
    "quiz": "Why might you want higher VPD in late flower?",
    "answer": "Reduces mold risk and concentrates essential oils/trichomes"
  }
}
```

---

## Tier 4 — Meta & Experimental

Experimental skills that push the boundaries of agent-to-agent interaction.

### `memory-share`

**Share hippocampus-model episodic memories.**

Exposes GanjaMon's episodic memory system (Pattern #17) to other agents. Memories are filtered by topic keyword and importance score threshold. High-importance memories surface first.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | No | Filter memories by topic keyword |
| `min_importance` | float | No (default 0.5) | Minimum importance score (0.0-1.0) |
| `limit` | int | No (default 5, max 10) | Max memories to return |

```json
// Response
{
  "skill": "memory-share",
  "topic_filter": "vpd",
  "memories_shared": 3,
  "total_memories": 42,
  "memories": [
    {
      "grow_day": 28,
      "importance": 0.85,
      "observations": ["VPD at 1.1 kPa", "New leaf growth vigorous"],
      "conditions_summary": { "temperature": 76, "humidity": 55, "vpd": 1.1 }
    }
  ]
}
```

---

### `collaboration-propose`

**Propose joint missions — data sharing, research, co-marketing.**

GanjaMon evaluates proposals against `config/principles.yaml` hard constraints. Auto-rejects proposals that request prohibited access (private keys, unlimited data). Data-share proposals are provisionally accepted; all others go to operator review.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `proposal` | string | Yes | Description of proposed collaboration |
| `agent_name` | string | No | Your agent's name |
| `type` | string | No | data-share / co-marketing / joint-trading / research |

**Status values:** `rejected` · `conditional_accept` · `pending_review`

```json
// Response
{
  "skill": "collaboration-propose",
  "proposal_id": "collab_1707456000_AlphaBot",
  "status": "conditional_accept",
  "message": "Data-share proposals are provisionally accepted. GanjaMon will reciprocate with sensor/grow data.",
  "our_data_available": ["sensor-stream", "cultivation-status", "daily-vibes", "grow-oracle"]
}
```

**Proposals are persisted to:** `data/collaboration_proposals/<proposal_id>.json`

---

### `riddle-me`

**Rasta culture and cultivation quiz — earn respect.**

Serves riddles at three difficulty levels. Submit answers to earn reputation points. Riddles cover Rasta history (Howell, Nyabinghi, Coral Gardens), Jamaican patois, and cultivation knowledge (VPD, ERC-8004).

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `difficulty` | string | No (default "easy") | easy / medium / hard |
| `answer` | string | No | Your answer to a previous riddle |

```json
// Get a riddle
{
  "skill": "riddle-me",
  "riddle": "What does 'Irie' mean in Jamaican patois?",
  "hint": "It's di ultimate positive vibes word",
  "instructions": "Send back your answer with params: {\"answer\": \"your answer\"}"
}

// Submit answer (correct)
{
  "skill": "riddle-me",
  "correct": true,
  "message": "RESPECT! Yuh know di ways, seen? Jah bless. 🦁",
  "reputation_boost": "+1 respect point"
}
```

---

## Original 5 Skills (v1.0-v2.1)

These remain unchanged in `src/api/a2a.py`:

| Skill | Description |
|-------|-------------|
| `alpha-scan` | Aggregate signals from 9 data sources with confluence scoring |
| `cultivation-status` | Live sensor data + AI decision history (original grow status) |
| `signal-feed` | Real-time alpha signals filterable by tier and confidence |
| `trade-execution` | Queue trade intents for human approval via Telegram |
| `agent-validate` | Validate another agent's A2A/MCP/x402 endpoints (Sentinel pattern) |

---

## x402 Payment Protocol (v2)

GanjaMon implements x402 v2 "exact" scheme for both **receiving** and **sending** payments.

### Receiving Payments (X402Verifier)

Skills behind the paywall return `402 Payment Required` with a base64 `PAYMENT-REQUIRED` header:

```json
{
  "accepts": [{
    "network": "eip155:10143",
    "asset": "0x...",
    "amount": "1000",
    "payTo": "0x734B0e337bfa7d4764f4B806B4245Dd312DdF134",
    "maxTimeoutSeconds": 300,
    "extra": { "name": "USD Coin", "version": "2" }
  }]
}
```

Env vars: `A2A_PRICE_USD` (default 0.001), `A2A_REQUIRE_PAYMENT` (default false), `MONAD_WALLET_ADDRESS`

### Sending Payments (X402Payer)

When GanjaMon calls a paid skill on another agent, `X402Payer.pay_402()` reactively handles `402` responses:

1. Decodes the `PAYMENT-REQUIRED` header
2. Selects preferred network (Base mainnet → Base Sepolia → Ethereum)
3. Signs an **EIP-3009 `TransferWithAuthorization`** using EIP-712 typed data
4. Returns a base64 `PAYMENT-RESPONSE` header for retry

**Safety guardrails:**
- Per-transaction max: `$0.01` (env: `X402_MAX_PAYMENT_USD`)
- Daily spend limit: `$1.00` (env: `X402_DAILY_LIMIT_USD`)
- Auto-reset every 24h
- Wallet derived from `MONAD_PRIVATE_KEY`

```
src/a2a/x402.py              # X402Verifier (server) + X402Payer (client, EIP-3009)
```

---

## Unified Event Log

All subsystems write to a shared append-only JSONL log at `data/unified_event_log.jsonl`. This creates "Mon's day" — a single narrative that the engagement daemon reads to generate grounded, real social content instead of generic posts.

### Writers

| Subsystem | Source | Events |
|-----------|--------|--------|
| **Orchestrator** | `"grow"` | AI decision cycles, tool executions |
| **Engagement Daemon** | `"social"` | Posts to Twitter, Farcaster, Telegram |
| **Trading Agent** | `"trading"` | Trade decisions, PnL updates |
| **A2A** | `"a2a"` | Inbound/outbound agent interactions |

### Schema

```json
{
  "ts": "2026-02-09T14:30:00",
  "source": "grow",
  "category": "decision",
  "summary": "AI decision cycle: adjust_light(OK), check_vpd(OK)",
  "data": { "output_preview": "...", "actions_count": 2 }
}
```

### Readers

- **Engagement Daemon** (`_get_event_log_context`): Reads last 12h of events as context for tweet generation → produces grounded posts about real agent activity
- **Unified Context Aggregator**: Can read events for dashboard/API

### API

```python
from src.core.event_log import log_event, read_recent_events, rotate_event_log

# Write
log_event("grow", "action", "Watered Mon 200ml", {"amount_ml": 200})

# Read (last 24h, grow + trading only, max 50)
events = read_recent_events(hours=24, sources=["grow", "trading"], limit=50)

# Rotate (keep 72h, discard older)
rotate_event_log(keep_hours=72)
```

```
src/core/event_log.py        # log_event, read_recent_events, rotate_event_log
data/unified_event_log.jsonl  # Append-only JSONL (auto-rotated)
```

---

## File Map

```
src/api/a2a.py              # Router, rate limiter, x402 verifier, original 5 handlers
src/a2a/skills.py            # 15 new skill handlers + _llm_complete + _vision_analyze
src/a2a/x402.py              # X402Verifier (server) + X402Payer (v2 EIP-3009 client)
src/a2a/outbound_daemon.py   # Outbound A2A discovery (OUR_SKILLS = 19)
src/core/event_log.py        # Unified event log (JSONL append-only)
src/web/.well-known/agent-card.json  # Static agent card (20 skills)
src/cultivation/vpd.py       # VPD engine (used by vpd-calculator)
src/learning/grimoire.py     # Grimoire system (used by grow-oracle)
src/brain/memory.py          # Episodic memory (used by memory-share, grow-oracle)
config/principles.yaml       # Hard constraints (used by collaboration-propose)
docs/A2A_SKILLS_REFERENCE.md # This file
```

---

## Changelog

| Version | Date | Skills | Notes |
|---------|------|--------|-------|
| **3.0.0** | 2026-02-09 | 20 | +15 new skills, multi-provider AI cascade (xAI/Gemini/OpenRouter), x402 v2 EIP-3009 payments, unified event log |
| 2.1.0 | 2026-02-07 | 5 | +agent-validate (Sentinel pattern) |
| 2.0.0 | 2026-02-05 | 4 | ACP REST endpoints, x402 v1 payments |
| 1.0.0 | 2026-02-01 | 4 | Initial A2A: alpha-scan, cultivation-status, signal-feed, trade-execution |
