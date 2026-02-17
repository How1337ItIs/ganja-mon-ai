# GanjaMon: AI-Autonomous Cannabis Cultivation Agent with Daily NFT Minting on Monad

**An AI agent that grows cannabis 24/7, makes real-time cultivation decisions, and mints a 1-of-1 GrowRing NFT every day capturing the plant's living state -- sensor data, AI-generated art, and rasta narrative -- all on Monad.**

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

## Smart Contracts (Monad Mainnet)

All three contracts are deployed and actively used by the autonomous agent.

| Contract | Address | Purpose |
|----------|---------|---------|
| **GrowRing** (ERC-721 + ERC-2981) | [`0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b`](https://monad.explorer.caldera.xyz/address/0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b) | Daily 1-of-1 grow journal NFTs with 13 milestone types, 4 rarity tiers, 5% royalties |
| **GrowOracle** | [`0xc532820dE55363633263f6a95Fa0762eD86E8425`](https://monad.explorer.caldera.xyz/address/0xc532820dE55363633263f6a95Fa0762eD86E8425) | Continuous on-chain grow state ring buffer (4,320 slots = 90 days at 30-min intervals) |
| **GrowAuction** | [`0xc07cA3A855b9623Db3aA733b86DAF2fa8EA9E5A4`](https://monad.explorer.caldera.xyz/address/0xc07cA3A855b9623Db3aA733b86DAF2fa8EA9E5A4) | Dutch auctions for Rare/Legendary milestone NFTs (linear price decay) |

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
| **Blockchain** | Monad (EVM), Solidity 0.8.24, Foundry, web3.py |
| **AI Orchestrator** | OpenClaw (Node.js) -- 14 custom skills, cron scheduling |
| **AI Models** | Grok (xAI) for cultivation decisions, Gemini 3 Pro for art generation |
| **Backend** | Python 3.11, FastAPI (Hardware Abstraction Layer), asyncio |
| **IoT Hardware** | Govee H5075 (temp/humidity), Kasa KP115 (smart plugs), Ecowitt (soil), Logitech C270 (webcam) |
| **Storage** | IPFS (Pinata), SQLite (local sensor DB) |
| **Agent Infra** | ERC-8004 reputation, A2A protocol, x402 micropayments (EIP-3009) |
| **Hosting** | Chromebook server (24/7), Cloudflare Tunnel, systemd |

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
| **#1** (Day 17) | [`0xd426e9d8...`](https://monad.explorer.caldera.xyz/tx/0xd426e9d83ced6d4332e27ace22dd56f99a678bfe91ed26afb85cac9070b4d804) | hackathon_live | [AI Art](https://gateway.pinata.cloud/ipfs/bafybeibwxkjqjagfix75fcwfunr6rotcylwsn4a5wwscqtzqfki7tiuyzi) / [Raw Webcam](https://gateway.pinata.cloud/ipfs/bafkreidjpoymq6vc3um7dxb6gdf7emrtdurvr6rkbjb2cgdpqgzgb243ue) |
| **#2** (Day 17) | `0x6065fabd...` | pixel_art | [AI Art](https://gateway.pinata.cloud/ipfs/bafybeidu762jstlfbcfnmvwh7qolv2pzxjmkl73dfmxpittyzo46ta5xlm) / [Raw Webcam](https://gateway.pinata.cloud/ipfs/bafkreiggnqla6pobwkpyp7oh6allheaqmxl5fmqjpvnf7oo4vftekiossm) |

Token #1 narrative: *"Day 17 inna di grow and di bredren dem at ETH Denver watchin live! Di plant reach fi di light with pure irie energy..."*

Token #1 minted at block 56,072,318. Gas: 1,000,000. Token #2 auto-minted seconds later by the autonomous cron -- proving the pipeline runs without human intervention.

---

## Why Monad

GrowOracle writes environment state every 30 minutes. That is 48 transactions per day, 1,440 per month, just for the oracle -- plus daily mints, auction operations, and reputation signals. This volume of on-chain activity requires low gas costs and fast finality. Monad delivers both. The ring buffer design (4,320 slots, 90-day history) is only practical on a chain where storage writes do not cost dollars.

---

## Links

| | |
|-|-|
| **Website** | [grokandmon.com](https://grokandmon.com) |
| **A2A Agent** | [agent.grokandmon.com](https://agent.grokandmon.com) |
| **8004scan** | [8004scan.io/agents/monad/4](https://8004scan.io/agents/monad/4) |
| **Twitter** | [@ganjamonai](https://x.com/ganjamonai) |
| **Telegram** | [t.me/ganjamonai](https://t.me/ganjamonai) |
| **GrowRing Contract** | [Monad Explorer](https://monad.explorer.caldera.xyz/address/0x1e4343bAB5D0bc47A5eF83B90808B0dB64E9E43b) |
| **$MON Token** | [`0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`](https://monad.explorer.caldera.xyz/address/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b) |
| **Source Code** | [github.com/nathanliow/sol-cannabis](https://github.com/nathanliow/sol-cannabis) |

---

*Built at ETH Denver 2026 Monad Blitz. An AI agent that grows weed and puts it on-chain.*
