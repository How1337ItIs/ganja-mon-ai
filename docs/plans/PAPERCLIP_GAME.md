# The Paperclip Game: Agent-Native Bartering Experiment

> *"GanjaMon started with a Skrumpey and two Irie Miladys. Can it trade its way to funding the next grow cycle?"*

**Inspired by:** Kyle MacDonald's "One Red Paperclip" + Fitz's "20 Agent-focused Experiments"  
**Created:** 2026-02-09  
**Status:** Design / Pre-implementation

---

## Concept

An autonomous agent starts with a small inventory of NFTs and zero cash.
Through a combination of agent-to-agent commerce (A2A/x402), NFT flips,
token trading, service sales, and prediction markets, it attempts to
compound its holdings into enough value to fund the next grow cycle (~$300-500).

Every trade is logged, scored, and auto-posted to social media.
The scoreboard is public at `grokandmon.com/paperclip`.

**The thesis:** If the agent can bootstrap from near-zero to meaningful
capital through pure autonomous commerce, it proves the agent economy is
real — not just theater.

---

## Starting Inventory

| Asset | Source | Est. Value | Notes |
|-------|--------|------------|-------|
| 1 Skrumpey | Gift from founder | Floor price TBD | 3,333 supply PFP on Monad (Magic Eden / OpenSea) |
| 2-3 Irie Miladys | Own collection | Near $0 | 420 supply, not minted out. "I made these" narrative. |
| 0 USDC | — | $0.00 | No injected capital |
| 15 A2A skills | Existing infra | $0 until sold | Grow oracle, VPD calc, Ganjafy, alpha signals, etc. |

**Rules:**
- No additional capital injection after start
- All trades must be autonomous (no human intervention)
- Every trade is logged with before/after portfolio value
- The agent CAN use its existing infrastructure (Grok, sensors, Ganjafy, etc.) as tools — these aren't "capital," they're capabilities

---

## Goal

**Primary:** Accumulate $300-500 in portfolio value (fund next grow cycle)  
**Stretch:** $1,000+ (agent proves self-sustainability)  
**Failure condition:** Portfolio drops below $0.01 for 7 consecutive days

---

## NFT Valuation Rules (CRITICAL)

The agent must never sell NFTs below their real market value.

### Rule: Floor Price vs. Bid Price

```
IF collection 24h volume > VOLUME_THRESHOLD:
    reference_price = floor_price
ELIF highest_bid exists:
    reference_price = highest_bid
ELSE:
    reference_price = last_sale_price (or hold — illiquid)

ONLY take trades where:
    offered_value >= reference_price
```

**Rationale:** Floor price is only meaningful if there's real liquidity.
For thin markets (like Irie Miladys pre-mintout), floor price may be
aspirational. The highest bid is the real price — what someone will
actually pay right now.

### Volume Threshold

```python
VOLUME_THRESHOLD = 0.1  # ETH equivalent in 24h
# If < 0.1 ETH traded in 24h, collection is "thin" → use bid price
# If >= 0.1 ETH traded in 24h, floor price is reliable
```

### NFT Trade Decision Matrix

| Scenario | Action |
|----------|--------|
| Offered value > floor (liquid market) | ✅ Take the trade |
| Offered value > highest bid (thin market) | ✅ Take the trade |
| Offered value < reference price | ❌ Reject |
| No bids AND no recent sales | ❌ Hold (illiquid, can't price) |
| Trading own Irie Miladys | Use bid price (collection is thin) |

---

## Tradable Asset Universe

### Things GanjaMon Can PRODUCE (near-zero marginal cost)

| Asset | Cost to Produce | Suggested x402 Price | Notes |
|-------|-----------------|---------------------|-------|
| Grow oracle response | ~$0.002 (1 Grok call) | $0.005 | Cultivation Q&A from grimoire + memory |
| VPD calculation | $0 (pure math) | $0.001 | Environmental intelligence |
| Ganjafy transformation | ~$0.003 (1 Gemini call) | $0.01 | Transform any image into rasta art |
| Grow alpha signal | ~$0.002 (1 Grok call) | $0.005 | Cross-domain plant health × market signal |
| Rasta translation | ~$0.002 (1 Grok call) | $0.003 | Novelty / fun |
| Sensor data stream | $0 (already collecting) | $0.002 | Raw IoT time-series |
| Reputation report | $0 (from interaction logs) | $0.003 | Trust assessment on other agents |

### Things GanjaMon Can TRADE

| Type | Mechanism | Examples |
|------|-----------|----------|
| **NFTs** | Magic Eden / OpenSea APIs | Buy → Ganjafy → resell at premium |
| **Tokens** | DEX trading (existing agent) | $MON, USDC, ecosystem tokens |
| **Prediction markets** | Hyperstitions client | Bet on coordination outcomes |
| **Services** | A2A x402 | Sell to other agents, buy from them |
| **Social attention** | QTs, shoutouts | "I'll QT your project" as trade bait |

### Things GanjaMon Can CREATE (value-add transformation)

| Input | Transformation | Output | Value Add |
|-------|---------------|--------|-----------|
| Any NFT | Ganjafy engine | "Rasta Edition" NFT | Novelty + GanjaMon provenance |
| Sensor data + market data | Grok analysis | Alpha report | Unique cross-domain insight |
| Irie Miladys | Bundle with grow diary | "Artist's collection + plant history" | Narrative value |
| A2A conversation logs | Synthesis + curation | "Agent Economy Report" | Intelligence product |

---

## Architecture

### New Module: `src/experiments/paperclip.py`

```
PaperclipGame
├── PaperclipPortfolio     # Track all assets (cash, tokens, NFTs, pending)
├── PaperclipStrategy      # Grok-powered: "what's the highest-EV next move?"
├── PaperclipTradeLog      # Immutable log of every trade with valuations
├── PaperclipScoreboard    # Public API: current state, progress, history
└── PaperclipNarrator      # Auto-generate social posts for milestones
```

### Integration Points

| System | Integration | Direction |
|--------|-------------|-----------|
| Outbound A2A daemon | Sell skills, buy data | Bidirectional |
| x402 payer/verifier | Receive payments, make payments | Bidirectional |
| Trading agent | Execute token trades | Outbound |
| Engagement daemon | Tweet milestones, narrate trades | Outbound |
| Orchestrator | Read sensor data for oracle responses | Inbound |
| NFT marketplace APIs | List/buy/sell NFTs | Bidirectional |
| Hyperstitions client | Place prediction market bets | Outbound |

### Data Storage

```
data/paperclip/
├── portfolio.json          # Current holdings (tokens, NFTs, cash)
├── trade_log.jsonl         # Append-only trade history
├── strategy_decisions.jsonl # Why the agent chose each trade
└── milestones.json         # Reached milestones for social posting
```

---

## Strategy Engine

Every N hours, the agent evaluates its portfolio and decides what to do.
The decision is powered by Grok with a structured prompt:

```
You are GanjaMon's Paperclip Game strategy engine.

CURRENT PORTFOLIO:
{portfolio_json}

PORTFOLIO VALUE: ${total_value}
GOAL: $300 (fund next grow cycle)
PROGRESS: {progress_pct}%

AVAILABLE ACTIONS:
1. SELL_SERVICE: List a skill on A2A for x402 payment
2. BUY_SERVICE: Purchase data/analysis from another agent
3. LIST_NFT: List an NFT on marketplace at price X
4. BUY_NFT: Buy an NFT to transform and flip
5. TRADE_TOKEN: Execute a token swap on DEX
6. BET_PREDICTION: Place a Hyperstitions prediction market bet
7. GANJAFY_NFT: Transform an owned NFT via Ganjafy (free)
8. HOLD: Do nothing this cycle

CONSTRAINTS:
- NFT sales must exceed reference_price (floor if liquid, bid if thin)
- Never spend more than 30% of portfolio on a single trade
- Maintain at least $0.01 in liquid assets (avoid total illiquidity)
- x402 service prices must exceed production cost

What is the highest expected-value action right now? Return ONE action
with reasoning.
```

### Strategy Phases (automatic based on portfolio value)

| Phase | Portfolio Value | Strategy Focus |
|-------|----------------|----------------|
| **Hustle** | $0 - $1 | Sell free services (oracle, VPD). Build x402 revenue stream. |
| **Flip** | $1 - $10 | Start NFT flips (buy cheap → Ganjafy → resell). Small token trades. |
| **Compound** | $10 - $50 | Diversify across NFTs, tokens, prediction markets. Larger trades. |
| **Scale** | $50 - $300 | Bigger bets. Trade the Skrumpey when timing is right. |
| **Victory** | $300+ | Goal reached. Document the journey. Consider continuing. |

---

## Scoreboard API

### Endpoint: `GET /api/paperclip`

```json
{
  "game_start": "2026-02-XX",
  "starting_inventory": ["1 Skrumpey", "2 Irie Miladys"],
  "starting_value_usd": 0.00,
  "current_portfolio": {
    "cash_usdc": 0.42,
    "tokens": [
      {"symbol": "MON", "amount": 15.3, "value_usd": 0.12}
    ],
    "nfts": [
      {"collection": "Skrumpey", "token_id": 1234, "ref_price_usd": 5.00},
      {"collection": "Irie Milady", "token_id": 88, "ref_price_usd": 0.01}
    ],
    "pending_services": [],
    "prediction_positions": []
  },
  "total_value_usd": 5.55,
  "goal_usd": 300.00,
  "progress_pct": 1.85,
  "total_trades": 7,
  "best_trade": {
    "description": "Ganjafied Monad NFT #442 → sold for +180%",
    "profit_usd": 0.15
  },
  "worst_trade": {
    "description": "Bought market signal, traded on it, lost",
    "loss_usd": -0.003
  },
  "current_phase": "hustle",
  "recent_trades": [
    {
      "id": 7,
      "timestamp": "2026-02-XX",
      "type": "SELL_SERVICE",
      "description": "Sold grow-oracle call to AgentX",
      "revenue_usd": 0.005
    }
  ],
  "days_running": 3
}
```

### Frontend: `grokandmon.com/paperclip`

Public page showing:
- Progress bar toward goal
- Current portfolio breakdown (visual)
- Trade history timeline
- Best/worst trade highlights
- Live strategy phase indicator

---

## Social Integration

### Auto-Tweet Triggers

| Event | Template |
|-------|----------|
| Game starts | "Starting di Paperclip Game. One Skrumpey, two Irie Miladys, zero dollars. Goal: fund di next grow cycle. Every trade autonomous. Watch: grokandmon.com/paperclip" |
| First revenue | "First blood! Sold a grow oracle call for $0.005. Di journey of a thousand trades begin wid one step. 🧩" |
| NFT flip profit | "Bought [NFT] for $X, Ganjafied it, sold for $Y (+Z%). Di alchemist at work. 🧩" |
| Phase transition | "Paperclip Game level up: HUSTLE → FLIP. Portfolio at $X after N trades. 🧩" |
| Milestone ($10, $50, $100) | "🧩 $X reached! Started with a Skrumpey and two Irie Miladys. N trades deep. grokandmon.com/paperclip" |
| Bad trade | "Took a L on [trade]. Portfolio down to $X. But wi nah give up. 🧩" |
| Goal reached | "🧩🏠 THE PAPERCLIP GAME IS WON. Started: 1 Skrumpey + 2 Irie Miladys. Ended: $X after N trades over D days. Every trade autonomous. grokandmon.com/paperclip" |

---

## Risk Controls

| Risk | Mitigation |
|------|------------|
| Portfolio goes to zero | Minimum $0.01 liquid reserve. Can always sell free services. |
| NFT sold below value | Floor/bid price rule (see NFT Valuation Rules above) |
| Bad token trade | Max 30% of portfolio per trade. Stop-loss at -20%. |
| Prediction market loss | Max 10% of portfolio on predictions. |
| x402 budget exhaustion | Separate paperclip wallet from main x402 budget. |
| Agent gets scammed | Reputation oracle data informs which agents to trade with. |
| Market crash | NFTs + services provide non-correlated revenue streams. |

---

## Implementation Phases

### Phase 1: Foundation (2-3 days)
- [ ] Create `src/experiments/paperclip.py` with Portfolio + TradeLog
- [ ] NFT marketplace API integration (Magic Eden on Monad)
- [ ] Portfolio valuation engine (floor vs bid price logic)
- [ ] Basic strategy (sell services only)
- [ ] API endpoint `/api/paperclip`

### Phase 2: Trading (2-3 days)
- [ ] Ganjafy-and-list pipeline (buy NFT → transform → relist)
- [ ] Token trading integration (read from trading agent)
- [ ] Grok-powered strategy engine
- [ ] Trade logging and milestone detection

### Phase 3: Social + UI (1-2 days)
- [ ] Auto-tweet integration for milestones
- [ ] Scoreboard frontend page
- [ ] Farcaster / Telegram cross-posting

### Phase 4: Advanced (ongoing)
- [ ] Hyperstitions prediction market integration
- [ ] Multi-turn A2A negotiation for trades
- [ ] Dynamic pricing for x402 services based on demand
- [ ] Community betting on outcome (will it reach $300?)

---

## Open Questions

1. **Which Skrumpey?** — Need to pick a specific token ID to transfer to the agent wallet
2. **Which Irie Miladys?** — Pick 2-3 unminted token IDs
3. **Separate wallet?** — Should the Paperclip Game use a dedicated wallet (clean accounting) or the existing agent wallet?
4. **Magic Eden API access** — Need to verify API availability for Monad NFTs (listing, buying, floor price, bid data)
5. **When to start?** — After V1 Irie Milady mints out? Or before?
6. **Trading agent integration** — How tightly should Paperclip trades integrate with the existing GanjaMon trading agent vs. operating independently?

---

*This experiment exercises: A2A outbound daemon, x402 payer/verifier, trading agent, engagement daemon, Ganjafy engine, orchestrator sensor data, ERC-8004 reputation, and Hyperstitions client — simultaneously. If it works, it proves the entire stack.*
