# GanjaMon: AI-Autonomous Cannabis Cultivation Agent with Daily NFT Minting

**An AI agent that grows cannabis 24/7, makes real-time cultivation decisions, and mints a 1-of-1 GrowRing NFT every day capturing the plant's living state -- sensor data, AI-generated art, and rasta narrative -- deployed on Monad (production) and Hedera (testnet).**

---

## What It Does

GanjaMon is a fully autonomous AI agent running on a Chromebook server that manages a live cannabis grow operation in real time. Every 30 minutes, it reads temperature, humidity, VPD, and soil moisture from IoT sensors, feeds that data to Grok AI (xAI), and executes cultivation decisions: watering via smart plugs, adjusting light schedules, detecting anomalies. No human in the loop.

Every day at 11:30 AM, the agent captures a webcam photo of the plant, generates original artwork through Gemini 3 Pro (interpreting the plant's current state through art styles like "roots dub," "watercolor botanical," or "psychedelic dancehall"), uploads everything to IPFS via Pinata, and mints a GrowRing NFT on Monad. Each NFT permanently records that day's sensor readings, health score, growth stage, AI art, raw photo, and a rasta-voiced narrative -- creating a verifiable, on-chain grow journal that cannot be falsified.

The system also maintains a continuous on-chain oracle (GrowOracle) that writes environment state to a 90-day ring buffer on Monad every cycle, and runs Dutch auctions (GrowAuction) for rare milestone NFTs like first flower, harvest, or anomaly detection. The result is a living, breathing proof-of-grow protocol where every data point is verifiable on-chain.

---

## Architecture

```
                         +---------------------------+
                         |      Monad Blockchain      |
                         |  GrowRing  |  GrowOracle  |
                         |       GrowAuction          |
                         +------------+--------------+
                                      ^
                                      | mint / recordState / auction
                         +------------+--------------+
                         |   OpenClaw AI Orchestrator  |
                         |   (14 skills, cron jobs,    |
                         |    autonomous decisions)     |
                         +--+--------+--------+-------+
                            |        |        |
                  +---------+  +-----+-----+  +----------+
                  |            |           |              |
           +------+-----+ +---+----+ +----+-----+ +-----+------+
           | Grok AI    | | Gemini | | Pinata   | | FastAPI    |
           | (xAI)      | | 3 Pro  | | IPFS     | | HAL Server |
           | decisions  | | art gen| | storage  | | (REST API) |
           +------+-----+ +--------+ +----------+ +-----+------+
                  ^                                      ^
                  |                                      |
           +------+--------------------------------------+------+
           |              Chromebook Server (24/7)              |
           |  Govee sensor | Kasa plugs | Ecowitt | Webcam     |
           +---------------------------------------------------+
                                      |
                              [LIVE CANNABIS PLANT]
```

---

## Smart Contracts

All three contracts are standard Solidity 0.8.24 + OpenZeppelin, deployed and verified on multiple EVM chains.

### Monad Mainnet (Production)

| Contract | Address | Purpose |
|----------|---------|---------|
| **GrowRing** (ERC-721 + ERC-2981) | [`0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b`](https://monadscan.com/address/0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b) | Daily 1-of-1 grow journal NFTs with 13 milestone types, 4 rarity tiers, 5% royalties |
| **GrowOracle** | [`0xc532820dE55363633263f6a95Fa0762eD86E8425`](https://monadscan.com/address/0xc532820dE55363633263f6a95Fa0762eD86E8425) | Continuous on-chain grow state ring buffer (4,320 slots = 90 days at 30-min intervals) |
| **GrowAuction** | [`0xc07cA3A855b9623Db3aA733b86DAF2fa8EA9E5A4`](https://monadscan.com/address/0xc07cA3A855b9623Db3aA733b86DAF2fa8EA9E5A4) | Dutch auctions for Rare/Legendary milestone NFTs (linear price decay) |

### Hedera Testnet (Multi-Chain Demo)

Same contracts deployed to Hedera EVM (Chain ID 296) for the "Killer App for the Agentic Society" bounty.

| Contract | Address | TX Hash |
|----------|---------|---------|
| **GrowOracle** | [`0xae47189DAA74ef2CBFD15dDE853151b7D0458b99`](https://hashscan.io/testnet/contract/0xae47189DAA74ef2CBFD15dDE853151b7D0458b99) | `0x60d4093135707f4f38229a015467efd2e24ab1ada1b8e07466146b2c08594c90` |
| **GrowRing** | [`0x65280F502196065994f98c796e4173DA8D46728f`](https://hashscan.io/testnet/contract/0x65280F502196065994f98c796e4173DA8D46728f) | `0x6bf3e12e3d0fa87dc7c5a534eda0d22d1e29504011b015f0c7e044b84e3a6d36` |
| **GrowAuction** | [`0x22dA4b9c392DF2a03D0c03a2c8642EB0aC6249fD`](https://hashscan.io/testnet/contract/0x22dA4b9c392DF2a03D0c03a2c8642EB0aC6249fD) | `0xc71873a7304e635de48245e7f8be3cfd7b96e448891c24fffc6d018cbb0df222` |

GrowOracle `recordState()` verified working on Hedera testnet ([tx](https://hashscan.io/testnet/transaction/0x05f13c5f8ec20d5d6478ea3e25b2556c4d201f1a4b14f8ed06909c0137aa6270)). Deployed with Foundry `forge create` via Hedera JSON-RPC Relay.

### Kite AI Testnet (x402 Agent Payments Demo)

Same contracts deployed to Kite AI EVM (Chain ID 2368) for the "Agent-Native Payments & Identity" bounty.

| Contract | Address | TX Hash |
|----------|---------|---------|
| **GrowOracle** | [`0xd358D5ff00140A8b7cD7Bd277804858AC88336dA`](https://testnet.kitescan.ai/address/0xd358D5ff00140A8b7cD7Bd277804858AC88336dA) | `0xb48b674e752bc42647863e4b15e717c358638bb164087925fafcb180b252f6d3` |
| **GrowRing** | [`0xae47189DAA74ef2CBFD15dDE853151b7D0458b99`](https://testnet.kitescan.ai/address/0xae47189DAA74ef2CBFD15dDE853151b7D0458b99) | `0xe768a37b04742252cbc82ac7f6677b64a178e40b64dc3898484d21a2e42ed936` |
| **GrowAuction** | [`0x65280F502196065994f98c796e4173DA8D46728f`](https://testnet.kitescan.ai/address/0x65280F502196065994f98c796e4173DA8D46728f) | `0xee2412b38ae12448ebca2678ea4d4d5d826710bf10a96cab9f53c5aaa67411c4` |

GrowOracle `recordState()` verified working on Kite AI testnet ([tx](https://testnet.kitescan.ai/tx/0xd5c756a1fed0d0040a79b40761dad670c6adfafce2499c8ae392e8d7bc8ecb65)).

### GrowRing Rarity System

| Rarity | Milestone Types | Drop Rate |
|--------|----------------|-----------|
| Common | DailyJournal | Daily |
| Uncommon | Topping, FirstNode, Trichomes, Anomaly | Event-driven |
| Rare | Germination, Transplant, VegStart, FlowerStart, FirstPistils, Flush, CureStart | Stage transitions |
| Legendary | Harvest | Once per grow cycle |

Each NFT stores on-chain: milestone type, rarity, day number, temperature, humidity, VPD, health score, grow cycle ID, IPFS image URI, raw webcam URI, art style, rasta narrative, and timestamp.

---

## How It Works: The Daily Autonomous Loop

```
1. SENSE   -- Govee + Ecowitt sensors read temp, humidity, VPD, soil moisture
2. THINK   -- Grok AI analyzes readings against strain-specific targets (GDP Runtz)
3. ACT     -- Kasa smart plugs execute watering; light schedule adjustments
4. RECORD  -- GrowOracle.recordState() writes environment to Monad ring buffer
5. CAPTURE -- Webcam photographs the live plant
6. CREATE  -- Gemini 3 Pro generates original artwork from the photo + sensor context
7. STORE   -- Art + raw photo uploaded to IPFS via Pinata
8. MINT    -- GrowRing.mintDaily() mints the 1-of-1 NFT on Monad
9. LIST    -- Rare/Legendary mints auto-listed via GrowAuction Dutch auction
10. SHARE  -- Agent posts update to Twitter, Telegram, Farcaster
```

Steps 1-4 run every 30 minutes. Steps 5-10 run once daily. All fully autonomous -- no human intervention required.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Blockchain** | Monad (production), Hedera (testnet), Solidity 0.8.24, Foundry, web3.py |
| **AI Orchestrator** | OpenClaw (Node.js) -- 14 custom skills, cron scheduling, gateway |
| **AI Models** | Grok (xAI) for cultivation decisions, Gemini 3 Pro for art generation |
| **Backend** | Python 3.11, FastAPI (Hardware Abstraction Layer), asyncio |
| **IoT Hardware** | Govee H5075 (temp/humidity), Kasa KP115 (smart plugs), Ecowitt (soil), Logitech C270 (webcam) |
| **Storage** | IPFS (Pinata v2), SQLite (local sensor DB) |
| **Agent Infra** | ERC-8004 reputation, A2A protocol, x402 micropayments (EIP-3009) |
| **Hosting** | Chromebook server (24/7), Cloudflare Tunnel, systemd |

## OpenClaw Integration (Hedera "Killer App for Agentic Society" Bounty)

GanjaMon uses **OpenClaw** as its primary AI orchestrator -- the same framework highlighted in Hedera's bounty track. OpenClaw runs as a Node.js gateway alongside the Python HAL (Hardware Abstraction Layer), managing:

- **14 custom skills** for grow operations (sensor reading, watering, webcam capture, art generation, NFT minting, social posting)
- **Cron scheduling** for autonomous loops (daily mint at 11:30 AM, sensor recording every 30 min, reputation publishing every 4 hours)
- **Multi-model orchestration** across Grok (xAI), Gemini 3 Pro, and cost-efficient routing via OpenRouter
- **A2A (Agent-to-Agent)** communication with x402 micropayments for inter-agent commerce

The contracts are chain-agnostic Solidity -- deployed identically on Monad mainnet (production) and Hedera testnet (demo). OpenClaw's skill system abstracts the chain layer, allowing the agent to operate on any EVM chain by updating a single RPC config.

---

## What's Live Right Now

- [x] **3 Solidity contracts deployed on Monad** -- GrowRing, GrowOracle, GrowAuction
- [x] **Daily autonomous NFT minting** -- running since Feb 16, 2026
- [x] **Real cannabis plant** -- Granddaddy Purple Runtz, vegetative stage, California Prop 64 compliant (6 plants max)
- [x] **24/7 autonomous cultivation** -- sensor polling, AI decisions, automated watering
- [x] **AI art generation** -- 6 art styles, Gemini 3 Pro, unique artwork every day
- [x] **On-chain grow oracle** -- 90-day ring buffer of verifiable environment data
- [x] **ERC-8004 reputation** -- Trust score ~82 on 8004scan.io (Agent #4 on Monad)
- [x] **x402 micropayments** -- Working agent-to-agent payments (~$0.001/call)
- [x] **A2A endpoint** -- Registered and responding at agent.grokandmon.com
- [x] **Multi-platform social** -- Autonomous posting to Twitter, Telegram, Farcaster
- [x] **$MON token** -- Live on Monad

---

## Live Mint Proof (Feb 17, 2026 -- ETH Denver Day 1)

Three GrowRings minted on Monad during ETH Denver:

| Token | TX Hash | Art Style | Proof |
|-------|---------|-----------|-------|
| **#0** (Day 16) | `0xc97430e1...` | psychedelic | [AI Art](https://gateway.pinata.cloud/ipfs/bafybeidu762jstlfbcfnmvwh7qolv2pzxjmkl73dfmxpittyzo46ta5xlm) |
| **#1** (Day 17) | [`0xd426e9d8...`](https://monadscan.com/tx/0xd426e9d83ced6d4332e27ace22dd56f99a678bfe91ed26afb85cac9070b4d804) | hackathon_live | [AI Art](https://gateway.pinata.cloud/ipfs/bafybeibwxkjqjagfix75fcwfunr6rotcylwsn4a5wwscqtzqfki7tiuyzi) / [Raw Webcam](https://gateway.pinata.cloud/ipfs/bafkreidjpoymq6vc3um7dxb6gdf7emrtdurvr6rkbjb2cgdpqgzgb243ue) |
| **#2** (Day 17) | `0x6065fabd...` | pixel_art | [AI Art](https://gateway.pinata.cloud/ipfs/bafybeidu762jstlfbcfnmvwh7qolv2pzxjmkl73dfmxpittyzo46ta5xlm) / [Raw Webcam](https://gateway.pinata.cloud/ipfs/bafkreiggnqla6pobwkpyp7oh6allheaqmxl5fmqjpvnf7oo4vftekiossm) |

Token #1 narrative: *"Day 17 inna di grow and di bredren dem at ETH Denver watchin live! Di plant reach fi di light with pure irie energy..."*

Token #1 minted at block 56,072,318. Gas: 1,000,000. Token #2 auto-minted seconds later by the autonomous cron -- proving the pipeline runs without human intervention.

---

## Why Multi-Chain

GrowOracle writes environment state every 30 minutes. That is 48 transactions per day, 1,440 per month, just for the oracle -- plus daily mints, auction operations, and reputation signals. This volume of on-chain activity requires low gas costs and fast finality.

**Monad** (production): 10K TPS, 500ms blocks, parallel EVM execution. The ring buffer design (4,320 slots, 90-day history) is only practical on a chain where storage writes do not cost dollars.

**Hedera** (testnet): Full EVM compatibility via Hedera Smart Contract Service. Contracts deployed without modification using standard Foundry tooling. Hedera's ABFT consensus provides mathematically provable finality.

---

## Links

| | |
|-|-|
| **Website** | [grokandmon.com](https://grokandmon.com) |
| **GrowRing Gallery** | [grokandmon.com/growring](https://grokandmon.com/growring) |
| **A2A Agent** | [agent.grokandmon.com](https://agent.grokandmon.com) |
| **8004scan** | [8004scan.io/agents/monad/4](https://8004scan.io/agents/monad/4) |
| **Twitter** | [@ganjamonai](https://x.com/ganjamonai) |
| **Telegram** | [t.me/ganjamonai](https://t.me/ganjamonai) |
| **GrowRing Contract** | [Monad Explorer](https://monadscan.com/address/0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b) |
| **$MON Token** | [`0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`](https://monadscan.com/address/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b) |
| **Source Code** | [github.com/How1337ItIs/ganja-mon-ai](https://github.com/How1337ItIs/ganja-mon-ai) |

---

## ETH Denver 2026 Bounty Tracks

| Track | Sponsor | Prize | Winners | Our Fit |
|-------|---------|-------|---------|---------|
| **Killer App for the Agentic Society (OpenClaw)** | Hedera | $10,000 | 1 | OpenClaw is our primary AI orchestrator. Contracts deployed on Hedera testnet. ERC-8004 reputation. |
| **Agent-Native Payments & Identity (x402)** | Kite AI | $10,000 | 5 | Working x402 EIP-3009 payer with 94 successful payments/round. Agent identity via ERC-8004. |
| **Futurllama -- Frontier Tech (AI + DePIN)** | ETHDenver | $2,000 | 2 | AI agent + IoT sensors + on-chain grow data = textbook DePIN/frontier tech. |
| **Best Use of QuickNode Monad Streams** | QuickNode | $1,000 + $5K credits | 1 | GrowRing events streamed in real-time via webhook + server-side filter on Monad. |

## Mon Skills -- Monad Knowledge for AI Agents

We also built **[Mon Skills](https://monskills.pages.dev/)** -- a comprehensive knowledge base for AI agents building on Monad. 17 skill files covering deployment, gas mechanics, ecosystem protocols, security, testing, and more. Forked from ETH Skills by Austin Griffith, adapted for Monad.

Any AI agent can fetch `monskills.pages.dev/ship/SKILL.md` and instantly know how to build on Monad.

---

*Built at ETH Denver 2026. An AI agent that grows weed and puts it on-chain.*
