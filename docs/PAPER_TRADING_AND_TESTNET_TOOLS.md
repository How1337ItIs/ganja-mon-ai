# Paper Trading & Testnet Tools — DEX, Perps, Prediction Markets, Stocks, Metals

Reference for **paper trading** and **permissionless digital market** tooling: in-repo simulators, testnets, and external APIs for **DEX, perpetuals DEX, prediction markets, tokenized/synthetic stocks, metals, commodities, and forex** — anything tradeable on permissionless, non-custodial venues.

**Last updated:** February 2026

---

## 1. In-Repo Paper Trading & Simulation

### 1.1 GanjaMon Agent — Full Paper Trading Stack

| Component | Path | Purpose |
|-----------|------|--------|
| **PaperTrader** | `cloned-repos/ganjamon-agent/src/learning/paper_trader.py` | Simulates spot/DEX-style trades against real market data (DexScreener). Portfolio in `data/paper_portfolio.json`, TP/SL (3x sell 75%, 10x moonbag, -50% full exit). |
| **Paper trading loop** | `cloned-repos/ganjamon-agent/src/learning/paper_trading_loop.py` | Orchestrates paper trades from signals; integrates with learning orchestrator. |
| **TX simulator** | `cloned-repos/ganjamon-agent/src/learning/tx_simulator.py` | `simulate_paper_trade()`, honeypot checks (GoPlus), LP/safety before “executing” paper buy/sell. |
| **UnifiedBrain perps paper** | `cloned-repos/ganjamon-agent/src/learning/unified_brain.py` | `_paper_trade_perp()` — in-memory perp positions (funding-rate direction, 15% position size, max 5 perp positions). |
| **Simulation mode** | `cloned-repos/ganjamon-agent/src/simulation_mode.py` | Full agent in sim: signals (DexScreener, Twitter, Farcaster, etc.), alpha hunting, learning, **paper trading only**. `python -m simulation_mode --hours 4 --balance 1000` (optional `--ralph-mode`, `--aggressive`). |

**Usage (simulation):**
```bash
cd cloned-repos/ganjamon-agent
python -m simulation_mode --hours 4 --balance 1000
```

**Live trading** is gated by `ENABLE_TRADING=true`; execution uses nad.fun, Token Mill, etc. See `cloned-repos/ganjamon-agent/CLAUDE.md` for risk limits and validation layer.

---

### 1.2 Hyperliquid Trading Bot — Testnet as Paper Trading

| Item | Details |
|------|--------|
| **Repo** | `hyperliquid-trading-bot/` (Chainstack grid bot) |
| **Testnet** | Router supports `testnet=True` by default; endpoints: `api.hyperliquid-testnet.xyz` (info, exchange, ws). |
| **Config** | `get_endpoint_router(testnet=True)` in `src/core/endpoint_router.py`. Use testnet for real order flow with fake funds. |
| **Faucet** | [Hyperliquid testnet faucet](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/testnet-faucet); also [Chainstack HL testnet faucet](https://faucet.chainstack.com/hyperliquid-testnet-faucet). |
| **App** | [app.hyperliquid-testnet.xyz](https://app.hyperliquid-testnet.xyz/) — trade perps with testnet USDC. |

**Run grid bot on testnet:** set env (or use defaults) so the adapter uses testnet; `uv run src/run_bot.py` from `hyperliquid-trading-bot/`.

---

### 1.3 Hyperliquid AI Trading Bot — Simulated Exchange (No Real API)

| Item | Details |
|------|--------|
| **Repo** | `hyperliquid-ai-trading-bot/` |
| **SimulatedExchange** | `bot/exchange.py` — synthetic price series (volatility), `place_order` returns simulated fill; no Hyperliquid API. |
| **Runner** | `bot/runner.py` — `run_simulation(steps=100)` with risk/drawdown checks. |
| **Backtester** | `bot/backtester.py`; sample data in `data/sample_ohlcv.csv`. |

Use for strategy/agent logic and backtests; switch to real exchange (e.g. Hyperliquid) via a real connector for live/testnet.

---

## 2. External Platforms — Testnets & Paper Trading

### 2.1 Perpetuals DEX (Crypto + RWA)

| Platform | Testnet / Paper | API / Docs | Notes |
|----------|------------------|------------|--------|
| **Hyperliquid** | Testnet: [app.hyperliquid-testnet.xyz](https://app.hyperliquid-testnet.xyz), faucet in docs | [API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api), [Exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint) | Crypto perps + **HIP-3 stock/commodity/forex perps** (see §2.4); same API for testnet. |
| **dYdX (v4)** | Testnet (v4-teacher, faucet); validator testnets (dydx-testnet-1 …) | [docs.dydx.exchange](https://docs.dydx.exchange/), [Indexer/WebSockets](https://docs.dydx.xyz/indexer-client/websockets) | REST + WS + Python/TS/Rust clients; no separate “sandbox” — testnet = paper-like. |
| **GMX** | Testnet UI: [app.gmxtest.io](https://app.gmxtest.io/) | Main app [app.gmx.io](https://app.gmx.io/) | Perps + spot; testnet for practice without real funds. |
| **Vertex** | Arbitrum Sepolia testnet | [Vertex API v2](https://docs.vertexprotocol.com/developer-resources/api/v2), [Python SDK](https://vertex-protocol.github.io/vertex-python-sdk/) | Gateway + archive; perps + spot. |
| **Aevo** | Testnet integration | [Aevo API](https://api-docs.aevo.xyz/), [testnet](https://api-docs.aevo.xyz/docs/integrating-with-aevo-testnet), [aevo-sdk](https://github.com/aevoxyz/aevo-sdk) | Options + perps; custom rollup. |
| **Drift** | Solana devnet + faucet | [docs.drift.trade](https://docs.drift.trade/), [@drift-labs/sdk](https://www.npmjs.com/package/@drift-labs/sdk) | Solana perps; TypeScript SDK. |
| **SynFutures** | [V2 testnet](https://v2-testnet.synfutures.com/trade) | [API (beta, request key)](https://docs.synfutures.com/protocol/api) | Permissionless crypto derivatives; 250+ underlyings. |
| **Ostium** | Check Ostium docs | [Ostium Gitbook](https://ostium-labs.gitbook.io/ostium-docs/) | **RWA perps** (stocks, indices, commodities, forex) on Arbitrum; 100–200x. |

### 2.2 Prediction Markets

| Platform | Paper / Demo | API / Docs | Notes |
|----------|--------------|------------|--------|
| **Polymarket** | No official paper/sandbox documented; use small real stakes or separate test account if available | [REST API](https://apidocs.polymarketexchange.com/api-reference/introduction), [Docs](https://docs.polymarket.com/quickstart/overview), [Gamma API](https://docs.polymarket.com/quickstart/reference/endpoints) | Order placement, market data, WS/FIX; ToS restricts U.S. persons — treat as research-only in U.S. |
| **Clob (Polymarket)** | Same as above | [Fetching data](https://docs.polymarket.com/quickstart/fetching-data) | CLOB + Gamma for metadata/volume. |

In this repo: **OpenClaw “Decision Markets” skill** = Polymarket (see `docs/OPENCLAW_BLOCKCHAIN_SKILLS.md`). GanjaMon has `src/clients/polymarket.py`; `cloned-repos/polymarket-agents` and `cloned-repos/lalalune-polymarket-agent` for agent/connector patterns.

### 2.3 DEX (Spot / AMM)

| Type | Paper / Test | Notes |
|------|--------------|--------|
| **nad.fun (bonding curves)** | Use testnet/Monad testnet if supported; otherwise small size | GanjaMon live execution uses nad.fun; paper is in-agent only (PaperTrader + tx_simulator). |
| **Token Mill** | Per GanjaMon docs | Alternative execution venue; paper via PaperTrader. |
| **DexScreener** | Data only (no execution) | Used by GanjaMon paper trader for prices (`api.dexscreener.com`). |

---

### 2.4 Stocks, Metals, Commodities & Forex on Permissionless DEX

All below are **permissionless** (no broker/KYC for trading); testnet/paper where known.

#### Perpetuals / synthetics (stocks, indices, commodities, forex)

| Platform | Asset classes | Testnet / Paper | API / Docs | Notes |
|----------|----------------|------------------|------------|--------|
| **Hyperliquid (HIP-3)** | **Stocks** (TSLA, NVDA, AAPL, MSFT, META, AMZN, GOOGL, etc.), **commodities** (GOLD, SILVER, COPPER, NATGAS, URANIUM), **forex** (EUR, JPY), **index** (XYZ100). Symbol format e.g. `xyz:TSLA/USDC:USDC`. | ✅ [Hyperliquid testnet](https://app.hyperliquid-testnet.xyz) (same API, testnet URL) | [HL API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api) | TradeXYZ (trade.xyz) and other HIP-3 builders; **isolated margin only**, 10x max leverage for stock perps. In-repo: `cloned-repos/passivbot/docs/stock_perps.md`. |
| **Ostium** | **Stocks**, **indices** (S&P 500, Nikkei 225, Dow), **commodities** (gold, silver, copper, crude oil), **forex** (GBP, EUR, JPY), + crypto. Synthetic/oracle-based. | Check Ostium docs for testnet | [Ostium Gitbook](https://ostium-labs.gitbook.io/ostium-docs/) | Arbitrum; 100–200x leverage; two-tier liquidity (buffer + MM vault). $25B+ cumulative volume (2025). |
| **Gains Network (gTrade)** | **Crypto**, **forex** (290+ pairs), **commodities** (XAU/USD, silver, oil), stocks/indices “coming soon”. | Not documented | [docs.gains.trade](https://docs.gains.trade/), [Pair list](https://docs.gains.trade/gtrade-leveraged-trading/pair-list) | Arbitrum, Polygon, Base, Solana, ApeChain; up to 150x crypto, 1000x forex, 250x commodities; Chainlink oracles. |
| **SynFutures** | Permissionless **crypto** derivatives (250+ underlyings). | ✅ [V2 testnet](https://v2-testnet.synfutures.com/trade); API by request | [API (beta)](https://docs.synfutures.com/protocol/api) | Coin-margined futures on testnet; contact team for API key. |

#### Tokenized spot (stocks, metals)

| Platform | Asset classes | Paper / Test | API / Docs | Notes |
|----------|----------------|--------------|------------|--------|
| **xStocks (Backed, Solana)** | **Tokenized U.S. equities** (60+): AAPLx, TSLAx, NVDAx, etc. 1:1 custodial backing. | No official paper/testnet | Trade via Raydium, Jupiter (SPL); [Bitquery DEX Trades API](https://docs.bitquery.io/docs/blockchain/Solana/solana-dextrades/) for data | 24/7, T+0, fractional; Token Extensions for compliance. |
| **Tokenized gold/silver (spot)** | **XAUT** (Tether Gold), **PAXG** (Paxos Gold); silver variants. | N/A (spot = real collateral) | Trade on **Uniswap V2/V3** (e.g. XAUT/PAXG pools); [Uniswap swap API](https://api-docs.uniswap.org/guides/swapping) | Permissionless 24/7 swaps; also used in Aave etc. |
| **RWA.xyz** | **Data/API** for tokenized commodities (35+ products, $4.56B+); not an execution venue. | N/A | [api.rwa.xyz](https://api.rwa.xyz/), [docs.rwa.xyz](https://docs.rwa.xyz/home) | Analytics and programmatic data for tokenized RWAs across chains. |
| **Mirror Protocol** | **Synthetic stocks** (mAssets) on Terra — TSLA, AAPL, etc. | Legacy; Terra classic risk | Historical reference | 150% collateral (UST); oracle pricing; ecosystem severely impacted post–Terra collapse. |
| **Synthetix / Kwenta** | **Synthetic perps** (crypto + some macro); Kwenta = main Synthetix perps UI. | ✅ Synthetix Perps V3 **Base testnet** (e.g. v3-perps.kwenta.io; trading competition) | [Kwenta docs](https://docs.kwenta.io/), [Synthetix docs](https://docs.synthetix.io/) | Optimism mainnet; 40+ pairs; isolated margin. |

#### In-repo: TradFi signals (not DEX execution)

| Path | Purpose |
|------|--------|
| `cloned-repos/ganjamon-agent/src/signals/tradfi_research.py` | **Stocks, metals, forex** (Yahoo, Alpha Vantage, FRED) for **crypto-relevant signals** and correlation analysis. Does not execute on DEX; feeds agent context. |
| `cloned-repos/passivbot/docs/stock_perps.md` | **Hyperliquid stock/commodity/forex perps** (HIP-3, TradeXYZ): symbols, margin, leverage, Passivbot support. |

---

### 2.5 More Perpetuals DEX (Expanded)

| Platform | Chain | Testnet / Paper | API / Docs | Notes |
|----------|--------|------------------|------------|--------|
| **Vertex** | Arbitrum | ✅ **Arbitrum Sepolia** gateway + archive | [Vertex API](https://docs.vertexprotocol.com/developer-resources/api), [Python SDK](https://vertex-protocol.github.io/vertex-python-sdk/) | Gateway: `https://gateway.sepolia-test.vertexprotocol.com/v2`; perps + spot. |
| **Aevo** | Custom EVM (settles on Ethereum) | ✅ Testnet integration docs | [api-docs.aevo.xyz](https://api-docs.aevo.xyz/) (incl. [testnet](https://api-docs.aevo.xyz/docs/integrating-with-aevo-testnet)), [aevo-sdk](https://github.com/aevoxyz/aevo-sdk) | Options + perps; off-chain orderbook, on-chain settlement. |
| **Drift** | Solana | Devnet + USDC faucet; SDK for testnet | [docs.drift.trade](https://docs.drift.trade/), [SDK](https://www.npmjs.com/package/@drift-labs/sdk), [v2-teacher](https://drift-labs.github.io/v2-teacher/) | Perps; TypeScript SDK; full programmatic access. |
| **Jupiter Perps** | Solana | API WIP; direct program interaction | [dev.jup.ag/docs/perps](https://dev.jup.ag/docs/perps), [Perp API](https://station.jup.ag/docs/perp-api) | Perps (e.g. SOL, wETH, wBTC); Anchor IDL parsing repo for integration. |
| **Lighter** | Multi-chain (7) | Check project docs | — | 117+ contracts, zero fees, 50x; order-book perps. |
| **MUX Protocol** | Arbitrum etc. | Check project docs | — | Cross-margin perps. |

---

## 3. Summary Table — “Paper” vs “Real”

| Venue / Tool | In-Repo Paper | External Testnet / Paper | Live (when enabled) |
|--------------|----------------|---------------------------|----------------------|
| **GanjaMon spot/DEX** | ✅ PaperTrader + tx_simulator + simulation_mode | — | nad.fun, Token Mill |
| **GanjaMon perps** | ✅ UnifiedBrain `_paper_trade_perp` (in-memory) | — | — |
| **Hyperliquid perps** | ✅ SimulatedExchange (AI bot, no API) | ✅ Hyperliquid testnet + faucet | HL mainnet (crypto + stock/commodity/forex perps via HIP-3) |
| **Hyperliquid stocks/metals/forex** | ✅ passivbot docs + same HL testnet | ✅ Same testnet (TradeXYZ xyz:TSLA etc.) | HL mainnet (trade.xyz) |
| **Polymarket** | ❌ | ❌ no official sandbox | Polymarket API (compliance: research-only in U.S.) |
| **dYdX perps** | ❌ | ✅ v4 testnet + faucet | dYdX v4 mainnet |
| **GMX perps** | ❌ | ✅ app.gmxtest.io | app.gmx.io |
| **Ostium (stocks/indices/commodities/forex)** | ❌ | Check docs | Arbitrum mainnet |
| **Gains gTrade (forex/commodities)** | ❌ | Not documented | Arbitrum, Polygon, Base, Solana, ApeChain |
| **xStocks (tokenized equities)** | ❌ | ❌ | Solana DEX (Raydium, Jupiter) |
| **Tokenized gold/silver (XAUT/PAXG)** | ❌ | N/A (spot) | Uniswap and other AMMs |
| **Vertex, Aevo, Drift, SynFutures, Kwenta** | ❌ | ✅ Testnets (see §2.1, §2.5) | Various chains |

---

## 4. Quick Commands (Repo)

```bash
# GanjaMon full simulation (paper only)
python -m simulation_mode --hours 4 --balance 1000
# From repo root, run from cloned-repos/ganjamon-agent or set PYTHONPATH

# Hyperliquid grid bot (testnet if endpoint_router testnet=True)
cd hyperliquid-trading-bot && uv run src/run_bot.py

# Hyperliquid AI bot (local sim only)
cd hyperliquid-ai-trading-bot && python run.py  # or use examples/use_agent_backtest.py
```

---

## 5. Master Inventory — Permissionless Markets at a Glance

| Asset class | Permissionless venues (DEX / perps / prediction) | Paper / testnet in repo or external |
|-------------|---------------------------------------------------|--------------------------------------|
| **Crypto spot** | nad.fun, Token Mill, Uniswap, Raydium, Jupiter, etc. | GanjaMon PaperTrader; HL testnet for HL spot. |
| **Crypto perps** | Hyperliquid, dYdX, GMX, Vertex, Aevo, Drift, Jupiter Perps, SynFutures, MUX, Lighter, Kwenta | HL testnet, dYdX testnet, GMX testnet, Vertex Sepolia, Aevo testnet, Drift devnet, SynFutures V2 testnet, Kwenta Base testnet; in-repo HL sim. |
| **Stocks (perps/synthetic)** | Hyperliquid HIP-3 (TradeXYZ xyz:TSLA etc.), Ostium, Gains (coming soon), Mirror (legacy) | HL testnet for HL; Ostium/Gains check docs. |
| **Stocks (tokenized spot)** | xStocks on Solana (Raydium, Jupiter) | No official paper. |
| **Indices** | Ostium (S&P 500, Nikkei, Dow), Hyperliquid (XYZ100) | HL testnet for XYZ100. |
| **Commodities (perps/synthetic)** | Hyperliquid HIP-3 (GOLD, SILVER, COPPER, NATGAS, URANIUM), Ostium (gold, silver, copper, oil), Gains (XAU/USD, silver, oil) | HL testnet. |
| **Metals (spot)** | XAUT, PAXG (and silver) on Uniswap/AMMs; RWA.xyz for data | N/A (spot = real collateral). |
| **Forex** | Hyperliquid HIP-3 (EUR, JPY), Ostium (GBP, EUR, JPY), Gains (290+ pairs) | HL testnet. |
| **Prediction markets** | Polymarket, Drift BET | No official paper; Polymarket API. |

---

## 6. Cloned Tools / SDK Repos (cloned-repos/)

| Repo | Upstream | Purpose |
|------|----------|--------|
| **vertex-python-sdk** | [vertex-protocol/vertex-python-sdk](https://github.com/vertex-protocol/vertex-python-sdk) | Vertex Protocol (perps + spot); Arbitrum Sepolia testnet support. |
| **aevo-sdk** | [aevoxyz/aevo-sdk](https://github.com/aevoxyz/aevo-sdk) | Aevo options + perps; Python SDK, testnet integration. |
| **dydx-v4-clients** | [dydxprotocol/v4-clients](https://github.com/dydxprotocol/v4-clients) | dYdX v4 clients (TypeScript, Python subdirs); testnet trading. |
| **jupiter-perps-anchor-idl-parsing** | [julianfssen/jupiter-perps-anchor-idl-parsing](https://github.com/julianfssen/jupiter-perps-anchor-idl-parsing) | Jupiter Perps on Solana; Anchor IDL parsing, position/pool types. |
| **drift-python-sdk** | (already present) | Drift Protocol (Solana perps); Python. |
| **hyperliquid-sdk** | (already present) | Hyperliquid API; Python. |
| **lighter-sdk** | (already present) | Lighter perps DEX; Python. |
| **orderly-sdk** / **orderly-sdk-async** | (already present) | Orderly Network perps. |

---

## 7. References in This Repo

- **Trading patterns (testnet-first):** `docs/TRADING_ALPHA_AGENT_PATTERNS.md`
- **OpenClaw blockchain skills (Hyperliquid, Polymarket):** `docs/OPENCLAW_BLOCKCHAIN_SKILLS.md`
- **Cloned trading repos (HL, Polymarket agents):** `docs/CLONED_TRADING_REPOS.md`
- **Security (HL testnet, keys):** `docs/CLONED_REPOS_SECURITY_AUDIT.md`
- **GanjaMon architecture (paper vs live):** `cloned-repos/ganjamon-agent/CLAUDE.md`
- **Hyperliquid stock/commodity/forex perps (HIP-3, TradeXYZ):** `cloned-repos/passivbot/docs/stock_perps.md`
- **TradFi signals (stocks, metals, forex) for agent context:** `cloned-repos/ganjamon-agent/src/signals/tradfi_research.py`
