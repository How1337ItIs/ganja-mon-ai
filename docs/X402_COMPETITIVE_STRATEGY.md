# x402 Hackathon: Competitive Strategy & Creative Analysis

> **Hackathon:** San Francisco Agentic Commerce x402 Hackathon
> **Host:** SKALE Labs × Google × Coinbase × Virtuals × Edge & Node × Pairpoint (Vodafone)
> **Prize Pool:** $50,000
> **Build Sprint:** Feb 11-13, 2026 (3 DAYS)
> **Winners Announced:** Feb 20, 2026
> **Platform:** DoraHacks

---

## Table of Contents

1. [The Competition: Tracks & Judging](#1-the-competition)
2. [Past Winners: What Worked](#2-past-winners)
3. [What We Actually Are (Not Just "The Plant Thing")](#3-what-we-are)
4. [Our Unfair Advantages](#4-unfair-advantages)
5. [Track Targeting Strategy](#5-track-targeting)
6. [The Creative Thesis](#6-the-creative-thesis)
7. [Competitive Differentiation Matrix](#7-differentiation-matrix)
8. [Demo Script (3-Minute Video)](#8-demo-script)
9. [Risk Analysis & Mitigations](#9-risks)
10. [Stretch Goals & Bonus Bounties](#10-stretch-goals)
11. [Pre-Hackathon Preparation Checklist](#11-pre-hackathon-prep)
12. [Build Day Execution Plan](#12-build-day-plan)
13. [Inspiration From Cloned Repos](#13-cloned-repo-insights)

---

## 1. The Competition

### Tracks (submit to MULTIPLE — projects are eligible for all relevant tracks)

| Track | Prize Focus | What Judges Want |
|-------|------------|------------------|
| **Best Agentic App / Agent** | Hero prize. Best end-to-end project | Agents capable of real-world transactions, novel use cases |
| **Agentic Tool Usage on x402** | Multi-step tool chaining | CDP Wallets + x402 payments, autonomous multi-step workflows |
| **Best Integration of AP2** | Google's Agent Payments Protocol | A2A agent interop, mandate chain (Intent→Cart→Payment→Receipt) |
| **Best Trading / DeFi Agent** | Autonomous trading with AI | Trading decisions from market analysis, encrypted DeFi, x402 payments |
| **Encrypted Agents** | Privacy + security | TEE, encryption, data privacy in agent workflows |

### Bonus Bounties
- **ACP SDK** — Agent Commerce Protocol integration
- **Virtuals Launch** — Deploy agent on Virtuals platform

### Judging Criteria (6 pillars)

| Criterion | Weight (est.) | Our Strength |
|-----------|---------------|-------------|
| **AI Readiness** | High | ✅ Grok AI brain, multi-provider LLM cascade, vision AI, computed personality, hippocampus memory |
| **Commerce Realism** | High | ✅ Bidirectional x402 (payer + verifier), real USDC, tiered pricing, daily spend caps, auto-refund |
| **Technical Execution** | High | ✅ 23 A2A skills, production FastAPI, ERC-8004 on-chain identity, reputation publisher, multi-protocol registration |
| **Polish & Ship-ability** | Medium | ⚠️ Solo builder risk — focus on working demo over features |
| **Partner Integration** | Medium | ✅ Coinbase x402 SDK, Google AP2/A2A, CDP wallet, Monad chain |
| **Presentation & Demo** | High | ✅ Multi-domain story nobody else has — complete autonomous economic entity |

---

## 2. Past Winners: What Worked

### Solana x402 Hackathon (Nov 2025) — 400+ submissions

| Winner | Track | WHY They Won |
|--------|-------|-------------|
| **PlaiPin** | Best x402 Agent App | ESP32 IoT device makes autonomous payments. **Physical world + x402 = judges loved it** |
| **Intelligence Cubed** | Best x402 API Integration | AI model marketplace with tokenization — novel economics |
| **x402 Shopify Commerce** | Main Track | Bridge between AI agents and real commerce — practical utility |
| **Amiko Marketplace** | Main Track | Agent credit profiles — new trust infrastructure |
| **MoneyMQ** | Best Dev Tool | Payment config via YAML — simplified complex setup |

### Agentic Commerce on Arc (Jan 2026)

| Winner | Track | Key Innovation |
|--------|-------|---------------|
| **OmniAgentPay** | Google Track 1st | Payment infrastructure specifically for AI agents |
| **Arc Merchant** | Google Track 2nd | Autonomous x402 micropayments |
| **AIsaEscrow** | Overall 2nd | On-chain escrow separating "recharge" from "consumption" |

### The Pattern That Wins

The winners share a common thread: they demonstrate a **complete autonomous commerce loop**, not just one side of a transaction. The best entries show agents that **discover, negotiate, pay, deliver, and build reputation** — end to end.

PlaiPin won not because it was "a chip" but because it showed **an autonomous entity conducting commerce in the physical world**. Intelligence Cubed won because it showed **a marketplace where AI agents are both buyers and sellers**. AIsaEscrow won because it showed **trust infrastructure for autonomous economic actors**.

The pattern: **Complete autonomous economic actor + novel trust/payment infrastructure + credible real-world utility = WINNING FORMULA**

---

## 3. What We Actually Are (Not Just "The Plant Thing")

**GanjaMon is a fully autonomous economic entity.** It earns revenue, spends money, trades tokens, manages reputation, communicates across platforms, builds social relationships with other agents, and makes all of these decisions through AI. The cannabis cultivation is ONE domain of expertise among many — a physical-world differentiator, not the product.

### The Seven Domains of GanjaMon

| Domain | What It Does | Key Infrastructure |
|--------|-------------|-------------------|
| **💰 Commerce** | Earns (x402 verifier) + Spends (x402 payer). Bidirectional autonomous payments with spend caps and refund capability | `src/a2a/x402.py` — X402Verifier (4-tier verification) + X402Payer (EIP-3009 signed transfers), $1/day cap, daily reset |
| **📊 Trading** | Autonomous $MON trading on Monad DEXs. Multi-strategy (market-making, momentum, mean-reversion). Real paper portfolio with PnL tracking | `cloned-repos/ganjamon-agent/` — seeker bot with 5-domain brain state, open/closed positions, research cycles |
| **🤖 Agent-to-Agent** | 23 production A2A skills. Outbound discovery daemon hitting 119 targets/round (79% success). Skills range from oracle consultations to collaborative proposals | `src/a2a/skills.py` (1551 lines, 5 tiers), `src/a2a/client.py`, `src/a2a/orchestrator.py` |
| **🏛️ On-Chain Identity** | ERC-8004 Agent #4 on Monad (trust score ~82.34). Auto-publishes performance metrics to ReputationRegistry every 12h. Multi-protocol registration (A2A + MCP + OASF + x402 + web + social) | `src/blockchain/reputation_publisher.py` (530 lines), `src/web/.well-known/agent-registration.json` |
| **📱 Social** | 4 original tweets + 2 Rasta QTs + 4 replies/day. Telegram community bot. Farcaster posting. Moltbook smart engagement (3 quality interactions/4h). All with consistent Rasta persona | `src/social/engagement_daemon.py`, Farcaster, Telegram, Moltbook clients |
| **🧠 Intelligence** | Grok AI brain with 5-domain unified context synthesis. Hippocampus memory with importance scoring/decay/reinforcement. Grimoire learning system. Grounding enforcement (no hallucinated sensor data) | `src/brain/unified_context.py` (726 lines), `src/brain/memory.py`, `src/learning/grimoire.py` |
| **🌱 Physical World** | Real IoT sensors (Govee, Ecowitt, Kasa), USB webcam, automated light/fan/pump control. The only AI agent on any blockchain that monitors a living organism | `src/hardware/webcam.py`, `src/hardware/`, sensor database |

### The Commerce Stack (What Matters for This Hackathon)

```
Discovery Layer:     A2A agent card → /.well-known/agent-card.json (23 skills)
                     ERC-8004 registration → 8004scan.io/agents/monad/4
                     OASF taxonomy → structured skill discovery
                     Multi-protocol → A2A + MCP + OASF + x402 + web

Payment Layer:       X402Verifier → 4-tier verification (ECDSA → on-chain tx → facilitator → honor)
                     X402Payer → EIP-3009 signed USDC transfers with daily caps
                     Tiered pricing → $0.005 (raw sensor) to $0.15 (premium synthesis)
                     Auto-refund → returns payment when service degrades

Trust Layer:         ERC-8004 identity → Agent #4, NFT-based portable reputation
                     Reputation publisher → auto-submits metrics every 12h
                     Payment-backed feedback → Sybil-resistant reviews via proofOfPayment
                     PERMISSIONS.md → declared security boundary for all skills

Intelligence Layer:  Unified Context Aggregator → 5-domain synthesis (grow + trade + social + email + agent tasks)
                     Hippocampus Memory → importance-weighted, decaying, reinforceable
                     Grimoire → continuous learning from outcomes
                     Principles YAML → 15 machine-readable constraints (11 hard, 4 soft)
                     Pitfalls YAML → 10 machine-readable gotchas

Social Layer:        Twitter (4+2+4/day), Telegram, Farcaster, Moltbook
                     Agent Collaboration Rooms → persistent multi-agent workspaces
                     SOUL.md personality → consistent Rasta voice across all channels
```

**This is the story**: not "a plant that takes payments," but **an autonomous agent economy participant that earns, spends, trades, builds reputation, socializes, and makes all decisions through AI** — and one of its unique intelligence sources happens to be a living organism.

---

## 4. Unfair Advantages

### Tier 1: Architecture Nobody Else Has Built

| Advantage | Evidence | Why It's Lethal for This Hackathon |
|-----------|----------|-----------------------------------|
| **Bidirectional x402** | `X402Verifier` (4-tier: ECDSA → on-chain → facilitator → honor) + `X402Payer` (EIP-3009, daily caps) | We BOTH sell AND buy via x402. Most entries will demo one side. We show the complete commerce loop. |
| **ERC-8004 on-chain identity** | Agent #4 on Monad, trust 82.34, auto-reporting metrics | We have EXISTING on-chain reputation. Not a demo — a live agent with real history. |
| **23 A2A production skills** | `src/a2a/skills.py` — 5 tiers from competitive moat to experimental | We're not building from scratch. We're showcasing an operational agent economy participant. |
| **Outbound A2A daemon** | 119 targets/round, 79% success rate | Our agent actively DISCOVERS and PAYS other agents. It's not passive — it's an economic actor. |
| **Multi-domain intelligence synthesis** | `unified_context.py` — trading PnL + social engagement + sensor data + email + agent tasks → single prompt | 5-domain decision-making is genuinely novel. Nobody else fuses this many inputs. |
| **Reputation auto-publisher** | `reputation_publisher.py` — submits sensor uptime, trading metrics, community size, x402 revenue, A2A interactions every 12h | Automatic, verifiable, Sybil-resistant reputation building. Judges will see we understand the FULL trust stack. |

### Tier 2: Differentiators That Make It Memorable

| Advantage | Evidence | Impact |
|-----------|----------|--------|
| **Physical-world grounding** | Real IoT sensors, USB webcam, living organism | The visual proof that this agent exists in the real world — not just in a Docker container |
| **Cultural personality engine** | SOUL.md + Rasta voice + Patois translation + computed personality modifiers | Every output has character. Judges remember personality. |
| **Trading + cultivation cross-domain** | Grow-alpha signal: plant health × trading PnL correlation | "The only agent that trades based partly on how its plant is doing" — genuinely novel |
| **Social proof** | Twitter, Telegram, Farcaster, Moltbook — all active, all consistent voice | This agent has a real public presence. Check @ganjamonai right now. |

### Tier 3: Execution Speed (What We DON'T Have to Build)

| Already Built | Lines | What It Is |
|--------------|-------|------------|
| `src/a2a/x402.py` | 659 | Full bidirectional x402 with 4-tier verification |
| `src/a2a/skills.py` | 1551 | 23 A2A skills across 5 tiers |
| `src/brain/unified_context.py` | 726 | 5-domain intelligence aggregator |
| `src/blockchain/reputation_publisher.py` | 530 | ERC-8004 auto-reporting |
| `src/brain/memory.py` | ~400 | Hippocampus memory with decay/reinforcement |
| `src/voice/personality.py` | ~300 | SOUL.md + dynamic personality |
| `src/api/app.py` | Production | FastAPI server running 24/7 on Chromebook |
| `config/principles.yaml` | 15 rules | Machine-readable constraints |
| `config/pitfalls.yaml` | 10 entries | Machine-readable gotchas |

**Total existing infrastructure: ~5000+ lines of production agent code. We're adding ~900 lines of x402 endpoint wiring, not building from zero.**

---

## 5. Track Targeting Strategy

### Primary: **Best Agentic App / Agent** (Overall Track)

**Why:** We're the most COMPLETE autonomous economic entity in the competition. Nobody else has:
- Bidirectional x402 (both buyer AND seller)
- On-chain identity with auto-reported reputation
- 23 production skills with outbound discovery
- Multi-domain intelligence synthesis
- Active social presence across 4 platforms
- Physical-world sensor integration

**Key sell:** "A fully autonomous economic entity that earns, spends, trades, builds reputation, and makes AI-driven decisions across 7 domains — operating 24/7 on production infrastructure."

### Secondary: **Best Trading / DeFi Agent**

**Why:** The trading agent is a REAL system. Multi-strategy on Monad DEXs. Paper portfolio with tracked PnL. 5-domain brain state informing decisions. The x402 angle: the trading agent PAYS other oracles (including itself) for intelligence via x402, then executes trades based on that paid intelligence.

**Key sell:** "An AI trading agent that autonomously pays for intelligence via x402, synthesizes signals across 5 domains, and executes $MON trades on Monad — with all decisions verifiable on-chain."

### Tertiary: **Best Integration of AP2**

**Why:** We have the reference implementation cloned. Our bidirectional commerce naturally maps to AP2:
- `IntentMandate` → Seeker declares intent ("I need alpha for $MON trading")
- `CartMandate` → Oracle returns tiered pricing (4 tiers, $0.005 to $0.15)
- `PaymentMandate` → Seeker signs x402 payment via EIP-3009
- `PaymentReceipt` → Oracle returns multi-domain intelligence + webcam proof + on-chain hash

**Key sell:** "Complete AP2 mandate chain where the product is AI-synthesized intelligence, not a physical good. First AP2 implementation for knowledge commerce."

### Also Eligible: **Agentic Tool Usage on x402**

**Why:** The seeker bot chains 7+ autonomous actions:
1. Discover oracle via A2A agent card
2. Resolve ERC-8004 identity (trust check on 8004scan)
3. Query pricing tiers
4. Sign x402 payment (EIP-3009)
5. Receive multi-domain oracle synthesis
6. Process intelligence into trade decision
7. Execute trade on Monad DEX
8. Report outcome to ReputationRegistry

8 chained autonomous actions, 3 involving x402 payments, all with verifiable on-chain traces.

---

## 6. The Creative Thesis

### The Elevator Pitch (30 seconds)

> "GanjaMon isn't a chatbot with a wallet. It's an autonomous economic entity — it earns revenue by selling AI intelligence via x402, spends money buying data from other agents, trades $MON on Monad DEXs, publishes its own reputation on-chain via ERC-8004, posts across 4 social platforms, and synthesizes decisions from 7 operational domains through Grok AI. Oh, and one of those domains is a real cannabis plant it monitors through IoT sensors — because the best AI intelligence is grounded in the physical world."

### Why This Wins

1. **Completeness** — Every other entry will demo one side of agentic commerce. We demo the COMPLETE economic actor: earning, spending, trading, building reputation, socializing.

2. **Bidirectional x402** — Our agent is BOTH a merchant (X402Verifier) AND a customer (X402Payer). It doesn't just charge for APIs — it autonomously pays for other agents' services. This is the full vision of agentic commerce.

3. **Production reality** — This isn't a hackathon prototype. It's an operational agent with 82.34 trust score on 8004scan, active social accounts, real trading history, and 23 deployed skills. The hackathon entry IS the production system.

4. **Trust stack** — ERC-8004 identity → auto-published reputation → payment-backed Sybil-resistant reviews → PERMISSIONS.md skill security → machine-readable principles/pitfalls. We've implemented the full trust hierarchy that agentic commerce requires.

5. **Physical grounding** — The plant, sensors, and webcam are the CHERRY ON TOP, not the sundae itself. They prove this agent exists in the real world and add a visual hook that judges remember. But the substance is the autonomous economic entity.

6. **Story/brand** — Rasta persona, cultural identity, consistent voice across all channels. In a sea of generic DeFi dashboards, GanjaMon is a CHARACTER. Judges remember characters.

### The Meme Concept: "The Agent Economy of One"

GanjaMon demonstrates what a SINGLE autonomous agent looks like when it's a full participant in the agent economy:
- It has an identity (ERC-8004)
- It has skills it sells (23 A2A skills via x402)
- It buys intelligence from others (outbound daemon, x402 payer)
- It manages its money (trading, spend caps, daily limits)
- It builds its reputation (auto-publishing metrics)
- It socializes and collaborates (Twitter, Telegram, Farcaster, Moltbook, Rooms)
- It learns from experience (grimoire, hippocampus memory)
- It has cultural values (SOUL.md, principles.yaml)
- It has safety rails (pitfalls.yaml, grounding enforcement)
- It's grounded in reality (IoT sensors, live plant)

**This is what agentic commerce looks like when you build the agent, not just the payment rail.**

---

## 7. Competitive Differentiation Matrix

| Capability | Typical Hackathon Entry | GanjaMon | Why It Matters |
|-----------|----------------------|---------|---------------|
| **x402 direction** | Sells OR buys (one side) | Both (Verifier + Payer) | Complete commerce loop |
| **On-chain identity** | None or bare registration | ERC-8004 Agent #4, trust 82.34, auto-reported metrics | Established actor, not a prototype |
| **A2A skills** | 0-3 demo skills | 23 production skills, 5 tiers | Mature service catalog |
| **Agent discovery** | Manual configuration | Outbound daemon, 119 targets/round | Active networker, not passive |
| **Intelligence source** | Single API/data source | 5-domain synthesis + IoT + webcam | Multi-modal, physical-world grounded |
| **Social presence** | None | Twitter + Telegram + Farcaster + Moltbook | Living agent with public history |
| **Personality** | None or generic | Full Rasta persona, SOUL.md, computed modifiers | Memorable and differentiated |
| **Memory** | Stateless | Hippocampus (importance/decay/reinforcement) + persistent grimoire | Agent that learns and remembers |
| **Safety** | None | Principles YAML, pitfalls YAML, grounding enforcement, spend caps, PERMISSIONS.md | Production-grade guardrails |
| **Trust infrastructure** | None | 4-tier payment verification, Sybil-resistant reputation, payment-backed feedback | Full trust stack |

### vs Likely Competitor Archetypes

| Competitor Type | Their Approach | Our Counter |
|----------------|---------------|-------------|
| **API Wrapper** | Slap x402 paywall on existing API | We GENERATE intelligence AND buy intelligence AND trade on it AND build reputation from it — end to end |
| **Trading Bot** | Standard DeFi bot + x402 | We trade based on 5-domain synthesis including physical world data. Our trading decisions are x402-funded intelligence purchases. |
| **Marketplace** | Agent-to-agent goods exchange | We're a marketplace PARTICIPANT, not a marketplace builder. We show what the agent inside the marketplace does. |
| **Dev Tool** | x402 SDK / helper library | We BUILD a live agent with x402 at every layer. The best demo for a dev tool is a thing built with it. |
| **IoT Project** | Hardware + wallet (PlaiPin approach) | We have IoT but also trading, reputation, social, personality, memory, multi-domain synthesis. IoT is one ingredient, not the dish. |
| **Personality Bot** | Chatbot with character | We have personality AND commerce AND trading AND reputation AND IoT. Character without substance is a toy. |

---

## 8. Demo Script (3-Minute Video)

### Shot List

**[0:00-0:15] COLD OPEN — The Hook**
- Terminal showing GanjaMon's unified runtime starting (`python3 run.py all`)
- 4 subprocesses spinning up: FastAPI server, social daemon, grow orchestrator, trading agent
- Text overlay: "A fully autonomous economic entity — not just a chatbot with a wallet"

**[0:15-0:40] THE AGENT — What It Actually Is**
- Quick visual tour (10s each):
  - 8004scan showing Agent #4, trust score 82.34
  - Twitter/X @ganjamonai showing recent posts in Rasta voice
  - Terminal showing outbound A2A daemon: "119 targets, 94 successful (79%)"
  - Trading portfolio showing open positions, PnL
- Narration: "GanjaMon operates 24/7 across 7 domains. It trades, it earns, it spends, it builds reputation, and it does it all autonomously."

**[0:40-1:05] THE COMMERCE — x402 in Action (BIDIRECTIONAL)**
- **Selling** (15s):
  - Terminal: Another agent calls our oracle — HTTP 402 returned
  - Payment verified (4-tier cascade: ECDSA → on-chain)
  - Multi-domain intelligence delivered
  - Reputation signal auto-published to ERC-8004
- **Buying** (10s):
  - Terminal: GanjaMon discovers an agent, pays $0.01 via x402 for market data
  - Show daily spend tracker: "$0.054/round, $1.00/day cap"
  - "Our agent doesn't just charge — it PAYS. Bidirectional commerce."

**[1:05-1:40] THE INTELLIGENCE — Why Anyone Would Pay**
- Full oracle response in colorized terminal:
  ```
  🔮 ORACLE CONSULTATION — Premium Tier ($0.15 USDC)
  ═══════════════════════════════════════════════════

  Signal: BULLISH_CONVERGENCE 📈     Conviction: 82/100

  ── 5-Domain Synthesis ──
  📊 Trading:     PnL +$12.50, 3 open positions, momentum UP
  👥 Social:      7 posts/24h, engagement rising, vibes 75/100
  🧠 Memory:      3 similar patterns recalled (importance >0.6)
  🌱 Physical:    VPD 1.05 kPa (optimal), temp 76°F, humidity 58%
  📧 Comms:       2 collaboration proposals pending

  "When di five streams converge, seeker, pay attention.
   Markets align wid di garden, and di garden nah lie."
  ```
- Quick webcam cut (5s): "And yes — one of those domains is a real plant."

**[1:40-2:10] THE TRUST STACK — Production-Grade Safety**
- Show the 4-layer trust architecture:
  ```
  ┌─────────────────────────────────────────┐
  │ ERC-8004 Identity — Agent #4 on Monad   │
  │ ↕ Auto-published metrics every 12h      │
  ├─────────────────────────────────────────┤
  │ x402 4-Tier Payment Verification        │
  │ ECDSA → On-Chain TX → Facilitator → Honor│
  ├─────────────────────────────────────────┤
  │ PERMISSIONS.md — Declared security boundary│
  │ 9 read paths, 6 write paths, 7 hosts    │
  ├─────────────────────────────────────────┤
  │ Principles YAML — 11 hard, 4 soft rules │
  │ Pitfalls YAML — 10 known gotchas        │
  │ Grounding — every decision cites sensors │
  └─────────────────────────────────────────┘
  ```
- "Agentic commerce requires trust. We built every layer."

**[2:10-2:35] THE AP2 FLOW — End to End**
- Quick visualization of the mandate chain:
  ```
  Seeker discovers GanjaMon → A2A agent card (23 skills)
  IntentMandate  → "Seek multi-domain alpha"
  CartMandate    → "Oracle consultation, $0.15 USDC, 4 tiers available"
  PaymentMandate → "EIP-3009 signed transfer on Base"
  Receipt        → "5-domain synthesis + conviction score + trade suggestion"
  ```
- Seeker processes the signal → BUY $MON decision → trade executed
- "From discovery to payment to intelligence to trade — fully autonomous."

**[2:35-3:00] CLOSE — The Vision**
- Architecture diagram: all 7 domains radiating from GanjaMon core
- Text: "Agentic commerce isn't about slapping a paywall on an API."
- "It's about building an autonomous economic entity that earns, spends, trades, and builds trust — end to end."
- "GanjaMon is what that looks like when you actually build it."
- Logo: GanjaMon + x402 + A2A + ERC-8004
- "grokandmon.com | @ganjamonai | Agent #4 on Monad"

---

## 9. Risk Analysis & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **3-day build as solo dev** | HIGH | 90% already exists — only ~900 lines of net-new code (endpoint wiring, AP2 mandate flow, demo script). |
| **Chromebook demo reliability** | MEDIUM | Build `X402_DEV_MODE=true` for local testing. Pre-record demo video (never live-demo at a hackathon). |
| **USDC faucet unavailable** | LOW | Fund wallets BEFORE hackathon. Base Sepolia USDC readily available from Circle faucet. |
| **x402 SDK breaking changes** | LOW | Pin versions. We tested imports against `x402>=0.2.0`. |
| **Cannabis content polarizes judges** | LOW | Frame as "physical-world grounding" and "biological intelligence source." The plant is one domain among seven. |
| **Grok API rate limits during demo** | MEDIUM | Cache responses for 5 minutes. Pre-warm the cache before recording. |
| **Network issues during live demo** | HIGH | Pre-record everything. Never do a live demo at a hackathon. |
| **Judges think "just a plant bot"** | MEDIUM | CRITICAL: Lead with the autonomous economic entity. Plant is the surprise reveal, not the opener. Demo shows commerce first, plant second. |
| **Overcomplicating the pitch** | MEDIUM | One sentence: "A fully autonomous economic entity that earns, spends, trades, and builds reputation via x402." Add complexity AFTER the hook. |

---

## 10. Stretch Goals & Bonus Bounties

### Ordered by Impact/Effort Ratio

| Stretch Goal | Track Bonus | Effort | Impact |
|-------------|-------------|--------|--------|
| **Auto-refund on service degradation** | Commerce Realism | Low ~50 lines | HIGH — shows mature commerce thinking. From AIXBT's refund pattern. |
| **Bidirectional commerce demo sequence** | Best Agentic App | Low ~30 lines | HIGH — show agent BUYING then SELLING in same demo flow |
| **Trust score check before payment** | Commerce Realism | Low ~40 lines | HIGH — agent verifies 8004scan trust score before paying another agent |
| **Webcam frame in oracle response** | Polish | Low ~20 lines | Medium — visual proof of physical grounding, base64 in JSON |
| **Proof of Photosynthesis hash** | Technical Execution | Medium ~40 lines | Medium — sha256(sensor_data) in response + Monad commit |
| **Oracle consultation dashboard** | Polish & UX | Medium ~100 lines | Medium — web page at grokandmon.com/oracle showing consultation history |
| **Virtuals launcher** | Bonus bounty | High | Extra prize eligibility |
| **ACP SDK integration** | Bonus bounty | High | Extra prize eligibility |
| **Subscription model** (daily auto-pay) | Commerce Realism | High | Novel recurring agentic commerce pattern |

### The "Must-Have" Stretch: The Commerce Loop Demo

Most critical stretch goal — show the BIDIRECTIONAL commerce in one flow:

```
1. External agent discovers GanjaMon → pays $0.15 → gets oracle wisdom
2. GanjaMon discovers another data agent → pays $0.01 → gets market data
3. GanjaMon synthesizes own oracle + purchased data → makes trade decision
4. Trade outcome auto-reported to ERC-8004 ReputationRegistry
```

This is the full economic loop. Agent earns → agent spends → agent trades → agent builds reputation. Nobody else will show all four steps.

---

## 11. Pre-Hackathon Preparation Checklist

These are all administrative/setup tasks — NOT building. Legal to do before Day 1.

### Accounts & Registration
- [ ] Register on DoraHacks (personal account)
- [ ] Create BUIDL submission page on DoraHacks
- [ ] Create CDP (Coinbase Developer Platform) account
- [ ] Generate CDP API keys (API Key Name + Private Key)
- [ ] Get Google API Key from AI Studio (for AP2 ADK examples if needed)

### Wallets & Funding
- [ ] Generate merchant wallet address (Base Sepolia)
- [ ] Generate seeker wallet address (CDP SDK auto-creates)
- [ ] Get testnet ETH from Base Sepolia faucet
- [ ] Get testnet USDC from Circle faucet (faucet.circle.com)
- [ ] Fund both wallets with at least $5 testnet USDC each
- [ ] Test a simple USDC transfer between wallets

### Repository
- [ ] Clean up `ganjamon-agent-public` repo or create new hackathon repo
- [ ] Write README with project overview + setup instructions
- [ ] Add architecture diagram showing all 7 domains
- [ ] Add license file

### Documentation
- [ ] Finalize this strategy document
- [ ] Verify `X402_IMPLEMENTATION_PLAN.md` is current
- [ ] Bookmark key URLs:
  - DoraHacks submission page
  - x402 SDK: https://github.com/coinbase/x402/tree/main/python
  - AP2: https://github.com/google-agentic-commerce/AP2
  - a2a-x402: https://github.com/google-agentic-commerce/a2a-x402
  - Base Sepolia explorer: https://sepolia.basescan.org
  - Circle faucet: https://faucet.circle.com

---

## 12. Build Day Execution Plan

### Day 1 (Feb 11) — Oracle Endpoints + Settlement

| Time | Task | Files |
|------|------|-------|
| 0:00-0:30 | Branch, deps, directory structure | `pip install`, `mkdir` |
| 0:30-1:00 | `pricing.py` — Tier configuration (4 tiers) | `src/x402_hackathon/oracle/pricing.py` |
| 1:00-3:00 | `synthesis.py` — Wire unified_context.py into oracle response format | `src/x402_hackathon/oracle/synthesis.py` |
| 3:00-4:30 | `settlement.py` — Wire x402.py verifier into endpoint middleware | `src/x402_hackathon/oracle/settlement.py` |
| 4:30-6:00 | `endpoints.py` — FastAPI routes (402 response, payment verification, oracle delivery) | `src/x402_hackathon/oracle/endpoints.py` |
| 6:00-7:00 | Test locally: curl → 402 → payment header → oracle response | Integration testing |
| 7:00-8:00 | `buyer_demo.py` — Show x402 PAYER side: agent buys from another service | `src/x402_hackathon/demo/buyer_demo.py` |

**Day 1 Exit: Complete oracle that returns 402, accepts payment, delivers multi-domain intelligence. Plus buyer-side demo.**

### Day 2 (Feb 12) — Seeker Bot + AP2 + Demo

| Time | Task | Files |
|------|------|-------|
| 0:00-2:00 | `alpha_seeker.py` — Autonomous seeker: discover → pay → synthesize → trade | `src/x402_hackathon/seeker/alpha_seeker.py` |
| 2:00-3:00 | `wallet.py` — CDP wallet integration for seeker | `src/x402_hackathon/seeker/wallet.py` |
| 3:00-4:30 | `mandate_flow.py` — AP2 mandate chain (Intent→Cart→Payment→Receipt) | `src/x402_hackathon/ap2/mandate_flow.py` |
| 4:30-5:30 | End-to-end test: seeker discovers → pays → gets wisdom → decides trade | Integration testing |
| 5:30-7:00 | `demo.py` — Colorized demo script showing FULL commerce loop (earn + spend + trade + reputation) | `src/x402_hackathon/demo.py` |
| 7:00-8:00 | Deploy to Chromebook, test remote access | `scp` + `ssh` |

**Day 2 Exit: Complete bidirectional commerce flow. Seeker → Oracle → Trade → Reputation. Working on production infra.**

### Day 3 (Feb 13) — Polish + Submit

| Time | Task | Files |
|------|------|-------|
| 0:00-1:00 | Stretch: auto-refund, trust check before payment, bidirectional demo sequence | Enhancement |
| 1:00-2:00 | Update Agent Card, x402-pricing.json, agent-registration.json | `.well-known/` files |
| 2:00-3:00 | Stretch: Proof of Photosynthesis hash OR webcam frame in response | Enhancement |
| 3:00-5:00 | Record demo video (3 minutes, scripted, pre-recorded) | OBS + terminal recording |
| 5:00-6:00 | Write DoraHacks submission text + screenshots + architecture diagram | Submission page |
| 6:00-7:00 | Push code to public repo, verify README | GitHub |
| 7:00-8:00 | Submit on DoraHacks, verify everything renders | Final submission |

**Day 3 Exit: Submission complete with video, code, and documentation.**

---

## 13. Inspiration From Cloned Repos

### `cloned-repos/aixbt-x402/` — Refund Pattern

**Key insight:** Auto-refunds when the service can't deliver. Shows mature commerce thinking.

### `cloned-repos/a2a-x402/python/examples/ap2-demo/` — AP2 Mandate Chain

**Key insight:** The EXACT AP2 flow — IntentMandate → CartMandate → PaymentMandate → Receipt. Our mapping:
- Shopping Agent → Seeker Bot
- Merchant Agent → GanjaMon Oracle
- Credentials Provider → CDP wallet
- Payment Processor → Coinbase x402 Facilitator

### `cloned-repos/AP2/` — Google's Protocol

**Key insight:** AP2 is NOT just about e-commerce goods. The `human-present/x402` scenario shows knowledge/service payments. Our oracle consultation fits perfectly.

### `cloned-repos/coinbase-agentkit/` — CDP Wallet

**Key insight:** AgentKit's Python package handles wallet management, token transfers, and on-chain interactions. Use for the seeker bot's CDP wallet instead of raw SDK calls.

---

## 14. The One-Liner

When judges ask "what does your project do?", the answer is:

> **"GanjaMon is a fully autonomous economic entity — it earns revenue selling AI intelligence via x402, pays other agents for data, trades $MON on Monad, and builds verifiable on-chain reputation. It's what agentic commerce looks like when you build the complete agent, not just the payment rail."**

This hits:
- ✅ AI Readiness (multi-domain AI intelligence synthesis)
- ✅ Commerce Realism (bidirectional x402 — earns AND spends)
- ✅ Technical Execution (23 skills, ERC-8004, 4-tier verification, 5-domain synthesis)
- ✅ Novelty (complete autonomous economic entity, not just one transaction direction)
- ✅ Memorable (it's a CHARACTER with a Rasta voice that also happens to monitor a real plant)

And THEN the follow-up:
> *"Oh, and one of its intelligence sources is a real cannabis plant it monitors through IoT sensors. Because the best wisdom is grounded in the physical world."*

Plant is the punchline, not the pitch.
