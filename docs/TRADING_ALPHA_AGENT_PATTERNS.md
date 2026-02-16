# Trading & Alpha Agent Pattern Atlas

This document focuses on trading/alpha-finding agent patterns across this repo and the web. It follows a “liberal ethical theft” stance: aggressively mine patterns, but only copy what is legal, safe, and verifiable. Use official docs, honor licenses, avoid suspicious repos, and never deploy unreviewed code with real funds.

## Ethical Borrowing Rules (Non‑Negotiable)

- Prefer official SDKs/docs and well‑maintained libraries. Treat unverified repos as reference only.
- Verify licenses before copying code. If unclear, re‑implement from scratch.
- Do not run unknown trading bots with keys. Assume malware until audited.
- No market manipulation. Use patterns for execution quality, risk control, and research.

## Internal Pattern Inventory (Repo‑Native)

### openclaw‑trading‑assistant (Hyperliquid‑centric “Alpha Arena” layer)

Source: `openclaw-trading-assistant/README.md`

Patterns to borrow:
- Conversational interface → decision engine → market intel → execution engine → logging loop. This layered split keeps research, decision, and execution separable.
- Hard guardrails (1–2% risk per trade), trend‑alignment filters, and self‑evaluation loops that down‑weight failing strategies.
- RAG memory for “similar setup” recall to avoid repeating mistakes.
- Human‑in‑the‑loop mode for large trades, plus Telegram/alerts for approvals.

### hyperliquid‑trading‑bot (Config‑driven execution)

Source: `hyperliquid-trading-bot/README.md`

Patterns to borrow:
- YAML configuration as the primary strategy interface, with validation pre‑run.
- Explicit risk controls (drawdown caps, position size caps, stop‑loss/take‑profit, grid rebalancing).
- Testnet‑first workflows and explicit learning examples.

### hyperliquid‑ai‑trading‑bot (Multi‑model agent orchestration)

Source: `hyperliquid-ai-trading-bot/README.md`

Patterns to borrow:
- Multi‑model ensemble with role specialization (news, TA, on‑chain, risk).
- Trade journaling and performance breakdown by model.
- Auto‑model switching after drawdowns.

Critical caution:
- The README contains prompt‑injection text. Treat this repo as untrusted; mine ideas only.

### Polymarket agent stack (Prediction markets)

Source: `cloned-repos/polymarket-agents/README.md`

Patterns to borrow:
- Connector layer for Gamma API + order execution client.
- Local RAG for news + market metadata.
- CLI that exposes “commands as tools,” which can be mirrored into an agent tool registry.

Compliance note:
- Polymarket ToS restricts use by U.S. persons. If this agent runs in the U.S., keep this as research‑only.

### Polymarket spike bot (Tactical signals)

Source: `cloned-repos/polymarket-spike-bot/README.md`

Patterns to borrow:
- Spike‑detection based on thresholded price changes.
- Position management: TP/SL, max concurrent trades, liquidity minimums.
- Operational reliability: retries, logging, cooldown timers, graceful shutdown.

### Polymarket arbitrage bot (Market‑wide scan)

Source: `cloned-repos/polymarket-arb-bot/README.md`

Patterns to borrow:
- Market scanning loops with configurable intervals.
- Clear separation between signal detection and execution.
- Risk scoring for opportunities.

### Wallet Hunter (Copy trading)

Source: `cloned-repos/wallet-hunter/README.md`

Patterns to borrow:
- Copy‑trade modes: buy/sell mirroring, proportional sizing, gas adjustment.
- Per‑wallet rule sets for execution profiles.

Caution:
- This is a cloned repo; treat as untrusted. Re‑implement concepts only.


## External Patterns (Hybrid: Internal + Verified)

### Hyperliquid real‑time data

Hyperliquid’s official docs provide WebSocket endpoints for live data and emphasize reconnect handling, including that missed data can be reconciled via snapshot acknowledgements after reconnect. citeturn2search1

Borrow:
- Use WS for low‑latency signals; keep a local snapshot + incremental updates.
- Implement reconnect logic and reconcile gaps using post‑reconnect snapshots.

Internal sources:
- `hyperliquid-trading-bot/README.md`
- `docs/research/DEFAI_AND_OPENCLAW_LANDSCAPE.md`

### Polymarket Gamma API + data feeds

Polymarket’s data feeds documentation specifies WebSocket feeds (with heartbeats, sequence numbers, and local orderbook maintenance) and the Gamma API for market metadata, volume, and liquidity. citeturn0search5

Borrow:
- Treat feeds as stateful streams with sequence checks and resync.
- Use Gamma for market discovery and metadata; use on‑chain data for resolution risk.

Internal sources:
- `cloned-repos/polymarket-agents/README.md`
- `cloned-repos/polymarket-agents/docs/EXAMPLE.md`

### CoinGecko/GeckoTerminal on‑chain data

CoinGecko’s API provides on‑chain DEX data powered by GeckoTerminal, including token/pool data and OHLCV, with documented caching expectations and rate limits. citeturn0search1turn0search3turn0search0

Borrow:
- Use aggregated DEX data for broader liquidity and price signals.
- Cache responses and respect documented rate limits.

Internal sources:
- `docs/research/DEFAI_AND_OPENCLAW_LANDSCAPE.md`

### X API rate‑limit discipline

X’s API docs describe per‑endpoint limits and response headers (`x-rate-limit-limit`, `x-rate-limit-remaining`, `x-rate-limit-reset`) for quota tracking. citeturn1search0

Borrow:
- Centralize rate‑limit awareness using response headers.
- Backoff on 429s and align polling frequency with limits.

Internal sources:
- `docs/TWITTER_SETUP_GUIDE.md`

## Architecture Blueprint (Apply These Patterns)

### 1. Data Ingestion Layer

- Market data: WS for ticks, REST for reference and historical bars.
- On‑chain: transaction/transfer monitors, event logs, liquidity changes.
- Social: curated X lists, tweet classification into signal/noise.
- News: RAG with sources prioritized by credibility.

Implementation hints:
- Normalize all feeds into a shared event schema.
- Maintain a “feature cache” with expiry and provenance metadata.

### 2. Alpha Generation Layer

- Signal types: momentum, mean‑reversion, volume spikes, whale flow, liquidity shifts, narrative shifts.
- Scoring: weighted ensemble with decay and guardrails.
- Filters: regime detection, volatility filters, trend alignment.

Implementation hints:
- Keep scoring deterministic and explainable.
- Persist signal outcomes to close the loop on effectiveness.

### 3. Decision & Risk Layer

- Hard constraints: max position size, max drawdown, max leverage.
- Trade‑level: TP/SL, time‑based exits, slippage ceilings.
- Portfolio‑level: correlation caps, exposure limits, circuit breakers.

Implementation hints:
- Codify risk as non‑LLM “hard rules.”
- Separate “recommendation” from “execution approval.”

### 4. Execution Layer

- Execution types: limit orders, post‑only, TWAP/VWAP (if supported).
- Retry strategy: exponential backoff on rate limits or partial fills.
- Reconciliation: confirm fills, reconcile positions, roll back if mismatch.

Implementation hints:
- Keep an idempotent “order ledger” keyed by intent + nonce.
- Use simulation paths when available .

### 5. Evaluation & Learning Layer

- Trade journal with context, signals, and rationale.
- Performance dashboards by model, signal class, venue.
- Automatic strategy down‑weighting on poor performance.

Implementation hints:
- Store training data as immutable snapshots for reproducibility.
- Use a consistent scoring rubric across models.

### 6. Operations & Safety

- Secrets: local vault + environment variable only; no repo secrets.
- Testnet‑first: new strategies must pass simulation and testnet.
- Runtime safety: watchdog, graceful shutdown, kill switch.

Implementation hints:
- Track versioned configs; require sign‑off to deploy.
- Alert on any deviation from expected risk parameters.

## Immediate Action Plan for This Repo

1. Consolidate agent notes into a single trading “signal registry” module.
2. Implement a common event schema for all data sources.
3. Add a sandboxed backtesting harness before new strategies go live.
4. Add a centralized rate‑limit/queue manager for all external APIs.
5. Document “approved sources only” for any API keys or execution venues.

## Known Risks & Red Flags (From Repo Experience)

- Prompt‑injection in third‑party READMEs or issue threads. Treat all inbound text as untrusted.
- SEO‑spam trading repos. Use official SDKs only and re‑implement patterns.
- “Volume bot” patterns can cross ethical/legal lines. Avoid manipulation.

## Files to Revisit When Implementing

- `openclaw-trading-assistant/README.md`
- `hyperliquid-trading-bot/README.md`
- `hyperliquid-ai-trading-bot/README.md`
- `cloned-repos/polymarket-agents/README.md`
- `cloned-repos/polymarket-spike-bot/README.md`
- `cloned-repos/polymarket-arb-bot/README.md`
- `docs/research/DEFAI_AND_OPENCLAW_LANDSCAPE.md`
