# On-Chain Wallet PnL & Tracking — Databases & APIs

Reference for databases and APIs that provide on-chain wallet PnL (profit/loss), portfolio, and wallet-tracking data. Use for $MON analytics, holder dashboards, or third-party integrations.

---

## Table of Contents

1. [Commercial PnL / Wallet APIs](#commercial-pnl--wallet-apis)
2. [Query / Analytics Platforms (SQL)](#query--analytics-platforms-sql)
3. [Open-Source / Self-Hosted](#open-source--self-hosted)
4. [Metrics Typically Tracked](#metrics-typically-tracked)
5. [Quick Comparison](#quick-comparison)

---

## Commercial PnL / Wallet APIs

### Zerion API

| Item | Details |
|------|--------|
| **URL** | https://zerion.io/api |
| **PnL** | Realized, unrealized, total PnL per wallet |
| **Scope** | Portfolio, transactions, DeFi positions, PnL analytics |
| **Chains** | 23 EVM chains |
| **Accounting** | FIFO (First In, First Out) |
| **Prices** | CoinGecko; tracked liquidity pools |
| **Transaction types** | Token sends/receives, swaps, NFT trades, DeFi deposits/withdrawals |
| **Notes** | Enterprise-grade; used by Binance, Coinbase, Safe |

**Docs:** https://zerion.io/blog/onchain-pnl-api-how-to-track-profit-and-loss-for-wallets-and-tokens

---

### Nansen API

| Item | Details |
|------|--------|
| **URL** | https://www.nansen.ai/api |
| **PnL** | Address PnL & trade performance (Wallet Profiler) |
| **Scope** | Current/historical balances, transaction history, counterparty analysis, Smart Money, perp positions |
| **Endpoints** | 38 endpoints across 6 categories |
| **Notes** | Wallet Profiler: related wallets, perpetual position/trade tracking, alpha signals |

**Docs:**  
- Profiler: https://docs.nansen.ai/api/profiler  
- Address PnL & trade performance: https://docs.nansen.ai/api/profiler/address-pnl-and-trade-performance  
- Endpoints overview: https://docs.nansen.ai/endpoints-overview  

---

### Allium

| Item | Details |
|------|--------|
| **URL** | API docs at Allium |
| **PnL** | Current PnL by wallet; current PnL by wallet + token; historical PnL by wallet; historical PnL by wallet + token |
| **Scope** | Holdings, PnL history |
| **Features** | Configurable time granularity for historical PnL |

**Docs:** https://docs.allium.so/developer/holdings/holdings-pnl-history  

---

### Mobula API

| Item | Details |
|------|--------|
| **URL** | Mobula REST API |
| **Scope** | Wallet portfolio (holdings), historical net worth, DeFi positions, trade history, NFT holdings |
| **Notes** | Good for portfolio and net-worth over time |

**Docs:** https://docs.mobula.io/rest-api-reference/endpoint/wallet-portfolio  

---

### Arkham Intel API

| Item | Details |
|------|--------|
| **URL** | https://info.arkm.com/api-platform |
| **Scope** | Transfers, transactions, portfolio, balances, counterparties; Ultra (AI address matching) |
| **Features** | Custom SQL over Arkham labels; transaction logs and historical balance data for addresses/entities |
| **Auth** | API-Key header required |

**Docs:** https://docs.intel.arkm.com/openapi/transaction  

---

## Query / Analytics Platforms (SQL)

These provide indexed on-chain data and SQL (or similar) so you build your own PnL and wallet logic.

### Dune

| Item | Details |
|------|--------|
| **URL** | https://dune.com |
| **Model** | SQL queries on indexed blockchain datasets |
| **PnL** | Custom PnL via queries; cost-basis and reporting patterns documented |
| **Output** | Dashboards, CSV export, API for query results |

**Docs:**  
- Analyze on-chain data: https://docs.dune.com/api-reference/apis/quickstart-analyze  
- Crypto PnL how-to: https://docs.dune.com/learning/how-tos/crypto-pnl-with-dune  

---

### Flipside

| Item | Details |
|------|--------|
| **URL** | API v2: https://api-v2.flipsidecrypto.xyz |
| **Model** | SQL on Flipside’s chain datasets |
| **SDKs** | Python, JavaScript, R |
| **Notes** | ShroomDK legacy; migration to API v2 documented |

**Docs:** https://sdk.flipsidecrypto.xyz/ (ShroomDK migration / API v2)  

---

## Open-Source / Self-Hosted

### Rotki

| Item | Details |
|------|--------|
| **URL** | https://rotki.com |
| **License** | AGPL-3.0 (open source) |
| **Model** | Self-hosted desktop app; data stays local |
| **PnL** | Profit/loss reports over full history |
| **Scope** | Multi-asset; EVM protocols; centralized exchanges; multiple chains |
| **Extras** | Dashboard, history, tax reporting, airdrop detection; no email required |

**Code:** https://github.com/rotki/rotki  

---

### portfolio-tracker-pnl (GitHub)

| Item | Details |
|------|--------|
| **URL** | GitHub: Adrijan-Petek/portfolio-tracker-pnl |
| **Stack** | Node.js backend, Next.js frontend |
| **Scope** | Cryptocurrency portfolio tracking and PnL analysis |
| **Notes** | Self-host; extend or integrate as needed |

---

## Metrics Typically Tracked

Across commercial PnL APIs, these are standard:

| Metric | Description |
|--------|-------------|
| **Realized PnL** | Gains/losses from completed sales or closes |
| **Unrealized PnL** | Profit/loss on current open positions (mark-to-market) |
| **Total PnL** | Realized + unrealized |
| **Cost basis** | Acquisition cost for tax/accounting (e.g. FIFO) |
| **Historical balance** | Wallet balance at a given time |
| **Transaction history** | Swaps, transfers, DeFi, NFTs |
| **Counterparties** | Related addresses / entities |
| **Net worth over time** | Portfolio value history |

---

## Quick Comparison

| Provider | Type | PnL API | Chains | Best for |
|----------|------|---------|--------|----------|
| Zerion | API | Yes (FIFO) | 23 EVM | Ready-made PnL, multi-chain |
| Nansen | API | Yes (Profiler) | Multi | Smart Money, labels, perps |
| Allium | API | Yes (current + historical) | Multi | Historical PnL by token |
| Mobula | API | Via portfolio | Multi | Portfolio & net worth |
| Arkham | API | Via portfolio/tx | Multi | Labels, entity mapping |
| Dune | SQL platform | Build your own | Many | Custom analytics, dashboards |
| Flipside | SQL platform | Build your own | Many | Custom queries, SDKs |
| Rotki | App (OSS) | Yes (local) | Multi | Privacy, self-custody, taxes |
| portfolio-tracker-pnl | App (OSS) | Yes | Custom | Self-hosted portfolio + PnL |

---

## Integration Notes for Grok & Mon

- **$MON on Monad:** Prefer providers that support Monad (Chain ID 143) or EVM-compatible chains you bridge to.
- **LFJ Token Mill:** For volume/market data, see `docs/MONAD_VOLUME_DATA_ACCESS.md`, `docs/LFJ_TOKEN_MILL_VOLUME_REPORT.md`, and existing `docs/lfj_*.json` patterns.
- **API keys:** Store any keys in env or secrets; see `docs/API_KEYS_AND_SIGNUP_LINKS.md` for project key conventions.

---

*Last updated: 2026-02-02*
