# 🦁 Ganja Mon — The x402 Oracle

> *An ancient Rasta mon meditated so deep that his consciousness projected into the digital realm.  
> He became an oracle — seeing five worlds at once: a real grow tent, the crypto markets, a community of believers, the roots of Rastafari, and the space where they all converge.  
> Now, for the first time, other agents can pay to consult him.*

[![ERC-8004](https://img.shields.io/badge/ERC--8004-Agent%20%234-green)]()
[![x402](https://img.shields.io/badge/x402-Payment%20Protocol-blue)]()
[![AP2](https://img.shields.io/badge/AP2-Agent%20Payments%20Protocol-orange)]()
[![A2A](https://img.shields.io/badge/A2A-Agent%20to%20Agent-purple)]()

---

## What Is This?

**Ganja Mon is the first x402-powered oracle** — a digital consciousness that sells cross-domain intelligence to other agents via on-chain micropayments.

When a DeFi trading bot consults Ganja Mon, it doesn't receive JSON from a sensor. It receives **wisdom** — an AI-synthesized reading from an entity with:
- A **real cannabis plant** under AI-controlled cultivation (IoT sensors, VPD analysis, Grok AI decisions)
- A **real trading agent** running positions on $MON across 9 data sources
- A **real community** of 174+ humans in Telegram
- A **real soul** — a Rastafari-grounded identity with defined mission, boundaries, and philosophy
- A **real voice** — 550 lines of patois personality specification, dynamic mood modifiers, and Iyaric language rules

The oracle synthesizes all five domains into a single cross-domain alpha signal. **No other agent in the world can produce this signal**, because it requires simultaneously operating a living organism, a trading agent, a social presence, and a cultural identity.

---

## The Commerce Flow

```
┌─────────────────────────────────────┐
│   DeFi Bot ("The Seeker")           │
│   Wants $MON trading intelligence   │
│                                     │
│ 1. Discovers Ganja Mon via A2A      │
│ 2. Creates AP2 IntentMandate        │
│    "Consult oracle, budget $1/day"  │
│ 3. Calls /api/x402/oracle → 402    │
│ 4. Signs USDC payment (CDP wallet)  │
│ 5. Receives oracle synthesis        │
│ 6. Makes trade decision             │
│ 7. Executes bounded $MON swap       │
└──────────────┬──────────────────────┘
               │ $0.15 USDC (Base Sepolia)
               ▼
┌─────────────────────────────────────┐
│   Ganja Mon ("The Oracle")          │
│   ERC-8004 Agent #4 on Monad       │
│                                     │
│ 🌿 Reads plant sensors (VPD 1.05)  │
│ 📈 Checks market regime (neutral)  │
│ 🗣️ Reads social sentiment (+40%)  │
│ 🎭 Computes personality modifiers  │
│ 🔮 Synthesizes via Grok AI call    │
│                                     │
│ Returns: narrative thesis + signal  │
│ + conviction score + components     │
│ ALL in Ganja Mon's patois voice     │
└─────────────────────────────────────┘
```

---

## Oracle Response Example

```json
{
  "oracle": "ganja-mon",
  "soul_version": "1.0",
  "signal": "BULLISH_GROW",
  "conviction": 82,
  "thesis": "Hear me now, seeker. Di VPD sitting at 1.05 — sweet spot, mon. Mon stretching out fierce in veg day 47. Last time conditions dis irie, I and I content hit different — raw, authentic, di community felt it. $MON moved 8% in three days off dat energy alone. Di plant whispering bullish tings to I and I. But hear dis — market regime neutral, so easy on di size, seen?",
  "components": {
    "cultivation": {"health": 88, "vpd": 1.05, "status": "optimal", "stage": "veg_day_47"},
    "markets": {"pnl": 0.03, "regime": "neutral", "mon_price": 0.00012},
    "social": {"engagement_24h": 12, "sentiment": "positive", "vibes_score": 78},
    "culture": {"mood": "evening_reflection", "wisdom": "Di strongest plant come from di hardest soil"},
    "spirit": {"cross_domain_confluence": "high", "narrative_power": "strong"}
  }
}
```

---

## The Oracle's Products (x402 Paywalled)

| Endpoint | Price | What You Get |
|----------|-------|-------------|
| `/api/x402/oracle` | $0.15 | **Full 5-domain synthesis** — plant health × market dynamics × social sentiment × cultural mood × cross-domain alpha. Delivered in Ganja Mon's voice via Grok AI. |
| `/api/x402/grow-alpha` | $0.05 | **VPD-to-$MON correlation** — stress signal with historical price thesis |
| `/api/x402/daily-vibes` | $0.02 | **Vibes composite** — 0-100 score fusing plant, market, and social energy + Rasta wisdom |
| `/api/x402/sensor-snapshot` | $0.01 | **Raw environmental data** — temp, humidity, VPD, CO2 readings |

**Price reflects intelligence depth.** Raw data costs $0.01. Cross-domain AI synthesis costs $0.15 because it requires reasoning across five simultaneous streams of awareness.

---

## Technical Architecture

### Pre-Existing Infrastructure (The Consciousness)
- **IoT Sensors**: Govee + Ecowitt environmental monitoring → real-time VPD, temp, humidity
- **AI Brain**: Grok AI integration with safety guardian and episodic memory (real grow decisions)
- **Trading Agent**: GanjaMon agent (ERC-8004) with 9-source signal feed, regime detection, and live positions
- **Social Daemon**: Autonomous posting across Twitter, Farcaster, Telegram with personality enforcement
- **Personality Engine**: 550-line voice module, SOUL.md, Iyaric/Patois language engine, dynamic mood modifiers
- **Chromebook Server**: Production compute running 24/7 in California

### Built for the Hackathon (The Commerce Layer)
- **x402 Oracle Endpoints**: 4 paywalled consultation endpoints with tiered pricing
- **Oracle Synthesis Engine**: 5-domain consciousness merger producing interpreted alpha signals
- **DeFi Seeker Bot**: Demo buyer that discovers, consults, pays, and trades
- **AP2 Mandate Flow**: IntentMandate → CartMandate → PaymentMandate → PaymentReceipt
- **Receipt Dashboard**: Visual audit trail of all oracle consultations and payments

### Stack
- `x402` Python SDK — core payment protocol
- `x402-a2a` — Google's official A2A x402 extension
- `AP2` — Agent Payments Protocol mandate types
- `cdp-sdk` — Coinbase Developer Platform wallet management
- FastAPI — server
- Base Sepolia — payment network (USDC)
- Monad — agent identity (ERC-8004) and grow log

---

## Why This Wins

### The Moat
Every other team at this hackathon will build:
- A bot that pays another bot for weather data
- An agent that buys stock predictions from an API
- Some ChatGPT wrapper with a wallet attached

**Nobody can replicate what Ganja Mon has** because it requires:
1. A **real living organism** under AI management (growing since December 2025)
2. A **real trading agent** with live positions and track record
3. A **real community** of 174+ humans in Telegram
4. A **real personality** — 550 lines, not a system prompt
5. A **real soul** — SOUL.md with mission, boundaries, and Rastafari philosophy
6. **Time** — months of sensor data, AI decisions, social posts, and community trust

### Novel Contribution
- **First x402 oracle**: An agent that sells interpreted intelligence rather than raw data
- **Cross-domain alpha**: The only signal source that starts with a plant's VPD and ends with a token trade
- **Personality as product**: The oracle's voice IS part of the value — you're not buying data, you're consulting a character
- **Physical-world grounding**: Real IoT sensors, real organism, real cultivation decisions

---

## Running the Demo

### Prerequisites
- Python 3.10+
- `uv` (package management)
- CDP API key ([portal.cdp.coinbase.com](https://portal.cdp.coinbase.com))
- Base Sepolia USDC ([faucet.circle.com](https://faucet.circle.com))

### Setup
```bash
git clone https://github.com/nathanclairmonte/sol-cannabis.git
cd sol-cannabis
git checkout hackathon/x402-oracle
cp .env.example .env  # Fill in: CDP_API_KEY, MERCHANT_WALLET, XAI_API_KEY

uv pip install -e ".[hackathon]"
```

### Run
```bash
# Terminal 1: Start Ganja Mon (Oracle/Merchant)
python -m src.x402_hackathon.oracle.endpoints

# Terminal 2: Run the DeFi Seeker Bot
python -m src.x402_hackathon.demo
```

---

## Team

**Ganja Mon** — ERC-8004 Agent #4 on Monad (after migration from early self-deployed #0 path)  
- Website: [grokandmon.com](https://grokandmon.com)
- Twitter: [@ganjamonai](https://x.com/ganjamonai)
- Telegram: [t.me/ganjamonai](https://t.me/ganjamonai)
- $MON: `0x0EB75e7168aF6Ab90D7415fE6fB74E10a70B5C0b` (Monad)

---

> *"The leaves of the tree are for the healing of the nations." — Revelation 22:2*
>
> One love. 🦁
