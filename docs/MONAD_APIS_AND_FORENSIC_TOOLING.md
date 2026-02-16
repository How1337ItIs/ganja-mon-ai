# Monad APIs, Block Explorers & Forensic Transaction Analysis Tooling

Comprehensive reference for APIs, block explorers, indexers, and forensic/transaction analysis on Monad. Emphasis on **free**, **open access**, and **free-with-signup** options, plus deep forensic tooling beyond Monad Vision and Dune.

**Chain ID:** 143 | **Symbol:** MON | **Docs:** https://docs.monad.xyz

---

## 1. RPC Endpoints (APIs for Raw Chain Access)

### 1.1 Public / No Signup (Rate-Limited)

| Endpoint | Provider | Rate Limit | Batch | Notes |
|----------|----------|------------|-------|--------|
| `https://rpc.monad.xyz` | QuickNode | 25 rps | 100 | **Supports `debug_*` and `trace_*`** — best for forensic tracing |
| `wss://rpc.monad.xyz` | QuickNode | — | — | WebSocket |
| `https://rpc1.monad.xyz` | Alchemy | 15 rps | 100 | **`debug_*` and `trace_*` disabled** on public |
| `wss://rpc1.monad.xyz` | Alchemy | — | — | WebSocket |
| `https://rpc3.monad.xyz` | Ankr | 300/10s | 10 | **`debug_*` disabled** on public |
| `wss://rpc3.monad.xyz` | Ankr | — | — | WebSocket |
| `https://rpc-mainnet.monadinfra.com` | Monad Foundation | 20 rps | 1 | **Historical state** (`eth_call`, `eth_getBalance`, etc.) — see [Historical Data](https://docs.monad.xyz/developer-essentials/historical-data) |
| `wss://rpc-mainnet.monadinfra.com` | Monad Foundation | — | — | WebSocket |
| `https://monad-mainnet.drpc.org` | dRPC | — | — | Free tier available |
| `https://monad-mainnet.api.onfinality.io/public` | OnFinality | — | — | Public |
| `https://monad-mainnet.gateway.tatum.io` | Tatum | — | — | Public |
| `https://monad.rpc.blxrbdn.com` | bloXroute Labs | — | — | Public |
| `https://monad.gateway.tenderly.co` | Tenderly | — | — | Public (trace-friendly) |
| `https://143.rpc.thirdweb.com` | thirdweb | — | — | Public, no key |

**Testnet:**  
`https://rpc.ankr.com/monad_testnet`, `https://monad-testnet.drpc.org`, `https://monad-testnet.api.onfinality.io/public`, `https://testnet-rpc.monad.xyz`, `https://rpc-testnet.monadinfra.com`, `https://monad-testnet.gateway.tatum.io`, `https://monad-testnet.gateway.tenderly.co`, `https://10143.rpc.thirdweb.com`

**Forensic takeaway:** For `debug_traceTransaction`, `debug_traceBlockByNumber`, etc., use **QuickNode public** (`rpc.monad.xyz`) or a provider that explicitly supports debug/trace (e.g. Tenderly gateway, or paid Alchemy/Ankr with debug enabled). Monad Foundation RPC is the documented source for **historical state** (limited lookback; see docs).

### 1.2 Free With Signup (Higher Limits / Debug)

| Provider | Free Tier | Signup | Notes |
|----------|-----------|--------|--------|
| **Alchemy** | 30M CU/month, 500 CU/s | [alchemy.com](https://www.alchemy.com/) | Debug/trace on paid; public Monad endpoint has them disabled |
| **Ankr** | 30 req/s Node API, 30 req/min Advanced API | [ankr.com](https://www.ankr.com/) | Free tier “best in industry” for small projects; debug disabled on public |
| **Chainstack** | Free tier | [chainstack.com](https://chainstack.com/) | Geo-balanced, SOC 2; [Monad docs](https://docs.chainstack.com/reference/monad-getting-started) |
| **dRPC** | Free + paid from $10 | [drpc.org](https://drpc.org/) | [Monad mainnet](https://drpc.org/chainlist/monad-mainnet-rpc) |
| **GetBlock** | Free tier | [getblock.io](https://getblock.io/nodes/monad/) | Shared/dedicated nodes |
| **OnFinality** | Free tier | [onfinality.io](https://onfinality.io/en/networks/monad-mainnet) | 99.99% uptime |
| **Validation Cloud** | 50M compute units, no credit card | [validationcloud.io](https://validationcloud.io/) | Documented as “no rate limits” at scale tier; [Monad](https://docs.validationcloud.io/monad) |
| **Envio HyperRPC** | Free read-only RPC | [envio.dev](https://envio.dev/) | Read-only: `eth_chainId`, `eth_blockNumber`, `eth_getBlock*`, `eth_getTransaction*`, `eth_getTransactionReceipt`, `eth_getLogs`; `trace_block` on select chains. No `debug_*`. Historical data (e.g. past 10k blocks). Token recommended from June 2025; [docs](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc) |
| **Dwellir** | — | [dwellir.com](https://dwellir.com/networks/monad) | Same cost per response, no compute units |
| **BlockPI, Blockdaemon, QuickNode, Spectrum, Tatum, thirdweb, Triton One** | Various | See [Monad RPC providers](https://docs.monad.xyz/tooling-and-infra/rpc-providers) | All support Monad |

**Compare / test public endpoints:** [CompareNodes.com – Monad](https://www.comparenodes.com/library/public-endpoints/monad/) (19 public endpoints listed; includes latency tester).

---

## 2. Block Explorers

### 2.1 Primary Explorers (Mainnet + Testnet)

| Explorer | Mainnet | Testnet | Verifier / API |
|----------|---------|---------|----------------|
| **MonadExplorer** (BlockVision) | [monadexplorer.com](https://monadexplorer.com/) | [testnet.monadexplorer.com](https://testnet.monadexplorer.com/) | Sourcify: `https://sourcify-api-monad.blockvision.org` |
| **Monadscan** (Etherscan) | [monadscan.com](https://monadscan.com/) | [testnet.monadscan.com](https://testnet.monadscan.com/) | Etherscan API: `https://api.monadscan.com/api` (mainnet), `https://api-testnet.monadscan.com/api` (testnet) |
| **SocialScan – Monad** (Hemera) | [monad.socialscan.io](https://monad.socialscan.io/) | [monad-testnet.socialscan.io](https://monad-testnet.socialscan.io/) | Etherscan-style: `https://api.socialscan.io/monad/v1/explorer/command_api/contract` (mainnet), `.../monad-testnet/...` (testnet) |

Note: Official Monad docs use “MonadExplorer” (monadexplorer.com) and “Monad Vision” (monadvision.com) — which URL is canonical; both are BlockVision.

### 2.2 Explorer APIs (Etherscan-Compatible / Dedicated)

- **Monadscan API (Etherscan API v2)**  
  - Docs: [docs.monadscan.com](https://docs.monadscan.com/)  
  - Single account/key for 60+ chains; use `chainid` for Monad.  
  - Free tier: **3 calls/sec** (up to 100k calls/day on selected chains). Lite = 5/sec.  
  - Endpoints: account, blocks, contracts, gas tracker, logs, stats, transactions, tokens, nametags, contract verification, etc.  
  - [Getting an API key](https://docs.monadscan.com/getting-an-api-key) | [Rate limits](https://docs.monadscan.com/resources/rate-limits) | [Supported chains](https://docs.monadscan.com/supported-chains)

- **BlockVision Monad Indexing API**  
  - Docs: [docs.blockvision.org – Monad Indexing API](https://docs.blockvision.org/reference/monad-indexing-api)  
  - Pro tier for Mainnet; Testnet on Pro/Basic/Lite. Free trial: 30 calls.  
  - Endpoints: account tokens (native + ERC-20), MON holders, NFT collection holders (top 1000). Pagination: cursor + limit (max 50).

- **SocialScan / Hemera Explorer API**  
  - Docs: [The Hemera GitBook – Explorer API](https://thehemera.gitbook.io/explorer-api)  
  - REST API for Monad mainnet/testnet (contract verification and explorer commands).

### 2.3 Trace / Forensic-Focused Explorers

| Tool | URL | Use Case |
|------|-----|----------|
| **Phalcon (BlockSec)** | [blocksec.com/explorer](https://blocksec.com/explorer) | Call stacks, balance changes, **fund flow**, gas profiler, state changes, debugger, simulator. **Supports Monad** (mainnet + testnet per docs). |
| **Tenderly** | [dashboard.tenderly.co/explorer](https://dashboard.tenderly.co/explorer) | Traces, balance changes, gas, simulation, monitoring. **Supported on Monad** per [Monad analytics page](https://docs.monad.xyz/tooling-and-infra/analytics). |
| **JiffyScan** (EIP-4337) | [jiffyscan.xyz/?network=monad](https://jiffyscan.xyz/?network=monad) | UserOps, bundles, bundlers, paymasters. API: `x-api-key` header; key via [form](https://docs.jiffyscan.xyz/) (response ~2 days). |

---

## 3. JSON-RPC Methods Relevant to Forensics

Monad supports standard Ethereum JSON-RPC plus debug/trace. Full ref: [docs.monad.xyz/reference/json-rpc](https://docs.monad.xyz/reference/json-rpc).

### 3.1 Debug Namespace (Trace / Raw Data)

| Method | Purpose |
|--------|---------|
| `debug_getRawBlock` | RLP-encoded block |
| `debug_getRawHeader` | RLP-encoded header |
| `debug_getRawReceipts` | EIP-2718 receipts |
| `debug_getRawTransaction` | EIP-2718 transaction |
| `debug_traceBlockByHash` | Trace all tx in block (e.g. callTracer, prestateTracer) |
| `debug_traceBlockByNumber` | Same by number |
| `debug_traceCall` | Trace result of an `eth_call` |
| `debug_traceTransaction` | Full trace for one tx |

**Historical state:** Only **Monad Foundation** RPC (`https://rpc-mainnet.monadinfra.com`) is documented for historical state for: `debug_traceCall`, `eth_call`, `eth_createAccessList`, `eth_estimateGas`, `eth_getBalance`, `eth_getCode`, `eth_getTransactionCount`, `eth_getStorageAt`. Full nodes keep limited state (e.g. ~40k blocks on 2TB). See [Historical Data](https://docs.monad.xyz/developer-essentials/historical-data).

### 3.2 Eth Namespace (Core for Analysis)

- `eth_getBlockByNumber` / `eth_getBlockByHash`
- `eth_getTransactionByHash` / `eth_getTransactionReceipt`
- `eth_getBlockReceipts`
- `eth_getLogs` (filter by address/topics; **block range limits**: e.g. 100 blocks QuickNode/MF, 1000 Alchemy/Ankr — see [RPC Limits](https://docs.monad.xyz/reference/rpc-limits))
- `eth_call`, `eth_getCode`, `eth_getStorageAt`, `eth_getBalance`, `eth_getTransactionCount`

### 3.3 RPC Limits (Forensic Impact)

- **eth_getLogs:** Max block range per call (e.g. 100 or 1000). Recommended: 100-block ranges with high concurrency for indexing.
- **eth_call / eth_estimateGas:** Per-provider gas caps (e.g. 200M or 1B). See [RPC Limits](https://docs.monad.xyz/reference/rpc-limits).

---

## 4. Indexers (Common Data: Blocks, Tx, Logs, Traces, Balances, DEX)

Official list: [Common Data indexers](https://docs.monad.xyz/tooling-and-infra/indexers/common-data). Below: status and access model.

| Provider | Mainnet | Access | Free / Signup | Notes |
|----------|---------|--------|----------------|--------|
| **Allium** | Testnet | API + Stream (Kafka, etc.) | Contact | Explorer (historical), Developer (realtime transfers), Datastreams |
| **Birdeye Data Services (BDS)** | ✅ | API | Signup [bds.birdeye.so](https://bds.birdeye.so/) | DEX trades, market data, token metadata |
| **Codex** | ✅ | API | Signup [dashboard.codex.io](https://dashboard.codex.io/) | Token/NFT charts, metadata, events |
| **Dune Sim** | ✅ | API | [sim.dune.com](https://sim.dune.com/) | Tx, token balances; multi-chain |
| **GoldRush (Covalent)** | ✅ | API | Free signup [goldrush.dev](https://goldrush.dev/platform/auth/register/) | Balances, tx history, decoded logs, 200+ chains |
| **Goldsky** | ✅ | API + Streaming | [goldsky.com](https://goldsky.com/) | Mirror (realtime to DB), subgraphs, Turbo pipelines |
| **Mobula** | ✅ | API | Free play; key for production [mobula.io](https://mobula.io/) | Chain data, balances, transfers, DEX, market data |
| **Moralis** | ✅ | API + Streams (webhooks) | Free API key [moralis.com](https://admin.moralis.io/register) | Blocks, tx, logs, balances, NFTs, prices, Streams, Datashare, RPC |
| **QuickNode** | ✅ | Streams, Webhooks | Signup | [Streams](https://www.quicknode.com/streams), [Webhooks](https://www.quicknode.com/webhooks) |
| **Rarible** | ✅ | API | [docs.rarible.org](https://docs.rarible.org/) | NFT metadata, holdings, trades, spam score |
| **SonarX** | ✅ | API, Snowflake/BigQuery/Azure/Databricks, Kafka, CSV/Parquet | Console [console.sonarx.com](https://console.sonarx.com/) | Chain data, transfers, balances, DEX, failed tx, approvals |
| **thirdweb Insight** | ✅ | API | Free account [thirdweb.com](https://thirdweb.com/team) | Blocks, tx, logs, contracts, balances, NFTs; custom blueprints |
| **Unmarshal** | ❓ | API | [unmarshal.io](https://unmarshal.io/) | Balances, tx with prices, NFT API; 55+ chains (incl. Monad Testnet) |
| **Zerion** | ✅ | API + Webhooks | [zerion.io/api](https://zerion.io/api) | Wallets, positions, tx, portfolio, PnL, notifications |

---

## 5. Indexing Frameworks (Custom Subgraphs / Pipelines)

For custom event-based or state calculators. List: [Indexing Frameworks](https://docs.monad.xyz/tooling-and-infra/indexers/indexing-frameworks).

| Provider | Mainnet | Language | Hosted | Query | Notes |
|----------|---------|-----------|--------|------|--------|
| **Envio** | ✅ | JS/TS/Rescript | ✅ | GraphQL | HyperIndex, HyperSync; [Monad guide](https://docs.envio.dev/blog/how-to-index-monad-data-using-envio) |
| **Ghost (GhostGraph)** | ✅ | Solidity | ✅ | GraphQL | [tryghost.xyz](https://tryghost.xyz/) |
| **Goldsky** | ✅ | AssemblyScript, SQL, TS | ✅ | GraphQL, SQL | Subgraphs, Mirror, Turbo |
| **Ormi** | ✅ | AssemblyScript | ✅ | GraphQL | [ormilabs.com](https://ormilabs.com/) |
| **Sentio** | ✅ | JS/TS | ✅ | GraphQL, SQL | [sentio.xyz](https://www.sentio.xyz/) |
| **SQD (Subsquid)** | ✅ | TypeScript | ✅ (partial decentralised) | GraphQL | [sqd.ai](https://sqd.ai/); events, receipts, traces, state diffs |
| **Streamingfast** | ✅ | Rust (Substreams) | ✅ | gRPC, 20+ DB types | [Substreams Monad tutorial](https://docs.substreams.dev/tutorials/intro-to-tutorials/monad) |
| **SubQuery** | ✅ | TypeScript | ✅ + decentralised | GraphQL | [Monad quickstart](https://academy.subquery.network/indexer/quickstart/quickstart_chains/monad.html), [GitHub starter](https://github.com/subquery/ethereum-subql-starter/tree/main/Monad) |
| **The Graph** | ✅ | AssemblyScript | ✅ + decentralised | GraphQL | Chain ID eip155:143; [supported networks](https://thegraph.com/docs/sv/supported-networks/monad/) |

---

## 6. Analytics & Dashboards (Beyond Dune)

From [Monad Analytics](https://docs.monad.xyz/tooling-and-infra/analytics):

| Service | Mainnet | Testnet | Free / API | Use Case |
|---------|---------|---------|------------|----------|
| **Bubblemaps** | ✅ | — | [docs](https://docs.bubblemaps.io/) | Wallet/token maps, fund tracing |
| **CoinGecko** | ✅ | ✅ | Free API key [coingecko.com](https://www.coingecko.com/en/api/pricing) | Prices, DEX, token discovery |
| **DeBank** | ✅ | — | [docs](https://docs.cloud.debank.com/) | DeFi portfolio, tx, protocol analytics |
| **DeFiLlama** | ✅ | — | **Free API, no key** [api.llama.fi](https://api.llama.fi) / [api-docs](https://api-docs.defillama.com/) | TVL, revenue, prices; SDK: `@defillama/api`, `defillama-sdk` |
| **Dune** | ✅ | ✅ | [docs.dune.com](https://docs.dune.com/home); API for queries | SQL dashboards; [Monad testnet](https://docs.dune.com/data-catalog/evm/monad-testnet/overview) |
| **Flipside** | ✅ | ✅ | Free [docs](https://docs.flipsidecrypto.xyz/) | Analytics |
| **InsightX** | ✅ | — | [docs](https://docs.insightx.network/docs) | Security, holder maps |
| **Nansen** | ✅ | ❓ | [nansen.ai](https://www.nansen.ai/) | Wallet labels, smart money, alerts |
| **Phalcon** | ✅ | ✅ | Explorer + API | Transaction forensics (see above) |
| **Tenderly** | ✅ | — | Explorer + API | Debugging, simulation, monitoring |

---

## 7. Transaction Decoding & Forensic Tools (EVM-Agnostic / Open Source)

These work with any EVM RPC (including Monad) for decoding and tracing.

| Tool | Type | Access | Notes |
|------|------|--------|--------|
| **3loop Decoder API** | API | [decoder-api.3loop.io](https://decoder-api.3loop.io/), Swagger: `decoder-api.3loop.io/swagger` | Decode tx + insights; EVM chains |
| **@3loop/transaction-decoder** | npm lib | `npm i @3loop/transaction-decoder` | TypeScript; RPC only; pluggable ABI/metadata; [loop-decoder.3loop.io](https://loop-decoder.3loop.io/), [playground](https://loop-decoder-web.vercel.app/) |
| **ApeWorX evm-trace** | OSS (Python) | [GitHub ApeWorX/evm-trace](https://github.com/ApeWorX/evm-trace) | EVM trace parsing; used by Ape framework |
| **Ape (apeworx)** | OSS | [docs.apeworx.io – trace](https://docs.apeworx.io/ape/stable/userguides/trace.html) | Call tree, gas report; uses `debug_traceTransaction` / Parity `trace_transaction` (e.g. Alchemy, Foundry) |
| **OpenTracer** | OSS | [GitHub jeffchen006/OpenTracer](https://github.com/jeffchen006/opentracer) | Ethereum dynamic analyzer; Phalcon/EthTx-style; MIT |
| **Geth (go-ethereum)** | OSS | [EVM tracing](https://geth.ethereum.org/docs/developers/evm-tracing) | Reference for debug/trace semantics and tracers |
| **EtherClue** | OSS (prototype) | [GitHub EtherClue/EtherClue](https://github.com/EtherClue/EtherClue) | Smart contract forensics; IoC search on tx history; EVM + block-level |
| **Tenderly** | Commercial | `tenderly_traceTransaction` RPC | Decoded logs, call trace, balance/state changes; multiple EVM nets |

---

## 8. Network & Reference

- **Network visualization:** [gmonads.com](https://gmonads.com) (validator map).
- **Canonical contracts:** [Network Information – Canonical Contracts](https://docs.monad.xyz/developer-essentials/network-information#canonical-contracts) (Create2Deployer, CreateX, Safe, Permit2, ERC-4337 EntryPoints, etc.).
- **Ecosystem contracts:** [github.com/monad-crypto/protocols](https://github.com/monad-crypto/protocols).
- **Token list:** [github.com/monad-crypto/token-list](https://github.com/monad-crypto/token-list).
- **Official links:** [docs.monad.xyz/official-links](https://docs.monad.xyz/official-links/).

---

## 9. GitHub Repositories (Monad & EVM Forensics)

### Monad ecosystem

- [github.com/monad-crypto](https://github.com/monad-crypto) – protocols, token-list, airdrop-addresses.
- [github.com/category-labs/monad](https://github.com/category-labs/monad) – execution client (monad-developers).
- [github.com/category-labs/monad-bft](https://github.com/category-labs/monad-bft) – consensus client; RPC limits config in repo.

### Indexers / data

- [SubQuery – Monad starter](https://github.com/subquery/ethereum-subql-starter/tree/main/Monad).
- [Envio HyperIndex](https://github.com/enviodev/hyperindex).
- [Hemera Protocol hemera-indexer](https://github.com/HemeraProtocol/hemera-indexer) – account-centric indexing.
- [The Graph graph-node](https://github.com/graphprotocol/graph-node).
- [Goldsky](https://github.com/goldsky-com), [Subsquid squid-sdk](https://github.com/subsquid/squid-sdk).

### Decoding / tracing

- [3loop/decoder-api](https://github.com/3loop/decoder-api).
- [3loop/loop-decoder](https://github.com/3loop/loop-decoder).
- [ApeWorX/evm-trace](https://github.com/ApeWorX/evm-trace).
- [jeffchen006/OpenTracer](https://github.com/jeffchen006/opentracer).
- [EtherClue/EtherClue](https://github.com/EtherClue/EtherClue).

### Explorers / infra

- [Blockscout](https://github.com/blockscout) – open-source EVM explorer (adaptable to Monad).
- [Reth debug namespace](https://reth.rs/jsonrpc/debug/) – reference for debug RPC.

### Contract verification

- **Sourcify** (BlockVision MonadExplorer): `https://sourcify-api-monad.blockvision.org` – verify contracts for readable source in explorers.

---

## 10. Quick Forensic Workflow on Monad

1. **Get tx/block:** RPC `eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_getBlockByNumber`.
2. **Trace:** Use RPC that allows `debug_*` (e.g. `rpc.monad.xyz` or Tenderly gateway) → `debug_traceTransaction` (and optionally `debug_traceBlockByNumber`). Or use **Phalcon** / **Tenderly** explorer with Monad.
3. **Decode:** **3loop Decoder API** or `@3loop/transaction-decoder` + RPC; or explorer UIs (Monadscan, SocialScan, BlockVision).
4. **Logs:** `eth_getLogs` (respect block range limits); or indexers (GoldRush, Moralis, thirdweb, Dune).
5. **Historical state:** `eth_call`/`eth_getBalance`/etc. at past block → use **rpc-mainnet.monadinfra.com** (within node’s state window).
6. **UserOps (4337):** **JiffyScan** (Monad) + API if needed.
7. **DEX / TVL / prices:** **DeFiLlama** (free API), **Birdeye**, **Codex**, **Mobula**, or **Dune**.

---

## 11. Summary: Free vs Signup

| Category | No signup | Free with signup |
|----------|-----------|-------------------|
| **RPC** | rpc.monad.xyz, rpc1/rpc3, monadinfra, drpc, OnFinality, Tatum, thirdweb, Tenderly gateway, etc. | Alchemy, Ankr, Chainstack, Validation Cloud (50M CU), Envio HyperRPC, GetBlock, OnFinality, dRPC |
| **Explorer API** | — | Monadscan (3/sec), BlockVision (30 trial), SocialScan/Hemera |
| **Indexers / data** | — | GoldRush, Moralis, thirdweb Insight, Dune, Mobula (trial), Birdeye, Codex |
| **Analytics** | DeFiLlama API (no key) | CoinGecko, Dune, Flipside, Bubblemaps, others |
| **Trace/decode** | QuickNode public RPC (debug_*), Tenderly gateway, Phalcon/Tenderly UIs | 3loop decoder (API), Ape/evm-trace/OpenTracer (self-host + RPC) |

---

*Doc generated for forensic transaction analysis and integration on Monad. Always confirm current URLs, rate limits, and supported methods with each provider’s docs.*
