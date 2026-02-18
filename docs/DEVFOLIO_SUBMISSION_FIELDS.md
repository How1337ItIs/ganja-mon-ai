# ETH Denver 2026 — Devfolio Submission Fields

> Submission portal: https://ethdenver2026.devfolio.co
> Deadline: February 21, 2026 (Saturday, judging day)
> BUIDLathon dates: Feb 18-21 (virtual start Feb 11)

## Project Name
GanjaMon: AI-Autonomous Cannabis Cultivation with Daily NFT Minting

## Tagline (max ~100 chars)
AI agent grows cannabis 24/7 and mints a 1-of-1 GrowRing NFT every day on Monad + Hedera

## Description (short)
GanjaMon is a fully autonomous AI agent running on a Chromebook server that manages a live cannabis grow operation. Every 30 minutes, it reads IoT sensors (temperature, humidity, VPD, soil moisture), feeds data to Grok AI (xAI), and executes cultivation decisions via smart plugs. Every day, it captures a webcam photo, generates original artwork through Gemini 3 Pro, uploads to IPFS, and mints a GrowRing NFT — a permanent, verifiable on-chain grow journal.

The system uses OpenClaw as its AI orchestrator with 14 custom skills and cron scheduling. Three Solidity contracts (GrowRing, GrowOracle, GrowAuction) are deployed on Monad mainnet (production) and Hedera testnet (multi-chain demo). A continuous GrowOracle writes environment state to a 90-day ring buffer on-chain every cycle. Real-time event monitoring via QuickNode Streams webhook. Agent-to-agent commerce via x402 micropayments (EIP-3009).

## Tech Stack
- **Blockchain**: Monad (production), Hedera (testnet), Solidity 0.8.24, Foundry
- **AI**: OpenClaw orchestrator, Grok (xAI) decisions, Gemini 3 Pro art generation
- **Backend**: Python 3.11, FastAPI, web3.py
- **IoT**: Govee H5075, Kasa KP115, Ecowitt GW1100, Logitech C270
- **Infrastructure**: IPFS (Pinata v2), Cloudflare Workers, QuickNode Streams
- **Agent**: ERC-8004 reputation, A2A protocol, x402 micropayments (EIP-3009)

## GitHub Repository
https://github.com/How1337ItIs/ganja-mon-ai

## Demo Links
- Website: https://grokandmon.com
- GrowRing Gallery: https://grokandmon.com/growring
- GrowRing API: https://grokandmon.com/api/growring
- A2A Agent: https://grokandmon.com/a2a/v1
- 8004scan Agent #4: https://8004scan.io/agents/monad/4
- Mon Skills: https://monskills.pages.dev
- Monad Explorer: https://monadscan.com/address/0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b

## Bounty Tracks to Select

### 1. Hedera — Killer App for the Agentic Society (OpenClaw) — $10,000 (1 winner)
**Our fit:** OpenClaw IS our primary AI orchestrator. All 3 contracts deployed + tested on Hedera testnet. ERC-8004 reputation publishing. Agent-first: no human in the loop for daily operations.

**Requirements met:**
- [x] Agent-first (OpenClaw agents are primary users)
- [x] Autonomous agent behaviour (daily mint pipeline, sensor polling, AI decisions)
- [x] Clear value in multi-agent environment (A2A protocol, x402 payments)
- [x] Uses Hedera EVM (3 contracts deployed on testnet)
- [x] Public repo, live demo URL, README with setup + walkthrough

**Deliverables needed:**
- [ ] <3 min demo video
- [x] Public repo: https://github.com/How1337ItIs/ganja-mon-ai
- [x] Live demo URL: https://grokandmon.com/growring
- [x] README with setup + walkthrough

### 2. Hedera — On-Chain Automation with Schedule Service — $5,000 (1 winner)
**Our fit:** 48 oracle txs/day + daily NFT mint = production on-chain automation. However, this bounty specifically requires Hedera Schedule Service — we use cron scheduling via OpenClaw, not Hedera's native scheduling. May not qualify unless we integrate HCS/Schedule Service.

### 3. Kite AI — Agent-Native Payments & Identity (x402) — $10,000 (5 winners: $5K/$1.5K/$1.5K/$1K/$1K)
**Our fit:** We already have working x402 EIP-3009 payer tested against Meerkat ($0.001/call). 94 successful outbound payments per round. This is a strong fit — most teams won't have working x402 yet.

**Requirements met:**
- [x] x402-style payment flows (working EIP-3009 payer)
- [x] Verifiable agent identity (wallet-based, ERC-8004)
- [x] Autonomous execution (no manual wallet clicking)
- [x] Open-source (MIT license)
- [x] Build on Kite AI Testnet/mainnet (3 contracts deployed + verified)

**Deliverables needed:**
- [x] Deploy contracts on Kite AI testnet (Chain ID 2368, all 3 deployed)
- [ ] <3 min demo video showing x402 payments
- [x] Live demo: https://grokandmon.com
- [x] Agent identity + payment flow visible at /a2a/v1

### 4. QuickNode — Best Use of Monad Streams — $1,000 + $5,000 credits (1 winner)
**Our fit:** QuickNode Streams webhook endpoint deployed on Cloudflare Worker. Server-side filter function monitors all 3 GrowRing contracts for MilestoneMinted, GrowStateUpdated, Transfer, and AuctionCreated events.

**Requirements met:**
- [x] QuickNode Streams as primary blockchain data source
- [x] Data ingestion, transformation, and delivery
- [x] Working demo with decoded event data
- [x] Filter function for real-time data processing

**Deliverables needed:**
- [ ] Active QuickNode account + API key to create live stream
- [x] Webhook endpoint: https://grokandmon.com/webhook/quicknode-stream
- [x] Filter function: cloudflare/quicknode-stream-filter.js

### 5. ETHDenver — Futurllama (Frontier Tech) — $2,000 (2 winners)
**Our fit:** AI + DePIN + IoT sensors + on-chain grow data = textbook frontier tech. "Big Crazy Ideas" track. A live cannabis plant being autonomously managed by an AI agent that mints daily NFTs is as frontier as it gets.

**Requirements met:**
- [x] AI (OpenClaw, Grok, Gemini)
- [x] DePIN (real IoT sensors controlling physical plant)
- [x] New Primitives (on-chain grow journal, agent-minted NFTs)
- [x] Frontier Tech (autonomous cultivation + blockchain)

## Contract Addresses

### Monad Mainnet (Chain ID 143) — PRODUCTION
| Contract | Address |
|----------|---------|
| GrowRing (ERC-721) | `0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b` |
| GrowOracle | `0xc532820dE55363633263f6a95Fa0762eD86E8425` |
| GrowAuction | `0xc07cA3A855b9623Db3aA733b86DAF2fa8EA9A5A4` |

### Hedera Testnet (Chain ID 296) — DEMO
| Contract | Address |
|----------|---------|
| GrowOracle | `0xae47189DAA74ef2CBFD15dDE853151b7D0458b99` |
| GrowRing | `0x65280F502196065994f98c796e4173DA8D46728f` |
| GrowAuction | `0x22dA4b9c392DF2a03D0c03a2c8642EB0aC6249fD` |

### Kite AI Testnet (Chain ID 2368) — DEPLOYED
| Contract | Address |
|----------|---------|
| GrowOracle | `0xd358D5ff00140A8b7cD7Bd277804858AC88336dA` |
| GrowRing | `0xae47189DAA74ef2CBFD15dDE853151b7D0458b99` |
| GrowAuction | `0x65280F502196065994f98c796e4173DA8D46728f` |

Verified: `recordState()` working — [tx 0xd5c756a1...](https://testnet.kitescan.ai/tx/0xd5c756a1fed0d0040a79b40761dad670c6adfafce2499c8ae392e8d7bc8ecb65)

## Team
- Nathan Liow (@nathanliow)

## What Makes This Unique
1. **Real physical plant** — Not a simulation. A live Granddaddy Purple Runtz in vegetative stage.
2. **Fully autonomous** — No human in the loop for daily operations. Agent makes all decisions.
3. **Multi-chain** — Same contracts on Monad (production) and Hedera (testnet).
4. **AI art** — Every NFT has unique artwork generated from the actual plant photo.
5. **Verifiable grow journal** — On-chain oracle creates unfalsifiable cultivation records.
6. **Agent commerce** — x402 micropayments for agent-to-agent service exchange ($0.054/round, 94 successful payments).
7. **ERC-8004 reputation** — Agent #4 on 8004scan with trust score ~82.

## Prize Potential Summary

| Bounty | Prize | Probability | Notes |
|--------|-------|-------------|-------|
| Hedera OpenClaw | $10,000 | Medium | Strong fit, but only 1 winner |
| Kite AI x402 | $1,000-$5,000 | High | 5 winners, we have working x402 |
| QuickNode Streams | $1,000 + $5K credits | Medium | Need active stream (API key) |
| Futurllama | $2,000 | Medium-High | 2 winners, strong DePIN story |
| **Total potential** | **$14K-$19K** | | |
