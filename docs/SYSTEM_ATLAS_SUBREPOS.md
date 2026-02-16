# System Atlas: Subrepos & Satellites

This document inventories **non-core** subprojects and cloned repositories. These are mostly reference implementations, experiments, or future integrations. Treat them as **untrusted** unless explicitly audited.

## First-Party Subprojects (Inside This Repo)

### `openclaw/`
- Upstream OpenClaw monorepo mirror.
- Purpose: local-first multi-channel AI assistant framework.
- Use: reference and possible integration target (do not assume it is wired into Grok & Mon).
- Docs: `openclaw/README.md`, `openclaw/AGENTS.md`.

### `openclaw-trading-assistant/`
- Trading assistant layer for OpenClaw (Hyperliquid focus, ERC‑8004 tooling).
- Contains ERC‑8004 registration scripts in `openclaw-trading-assistant/src/scripts/`.
- Doc: `openclaw-trading-assistant/README.md`.

### `cloned-repos/ganjamon-agent/`
- GanjaMon trading agent (Monad hackathon). Multi-source signals, token validation, nad.fun/Token Mill execution.
- **Runtime:** Launched by `sol-cannabis/run.py all` as an **isolated subprocess** (`python -m main` with `PYTHONPATH=ganjamon-agent/src` and `cwd=ganjamon-agent/`). Has its own `.env`, `data/`, and dependencies.
- **Deployment:** NOT deployed by `sol-cannabis/deploy.sh`. Must be deployed separately (e.g., `git pull` on Chromebook).
- **Two data dirs:** Trading agent writes to `ganjamon-agent/data/` (paper portfolio, brain state, observations). Grow/social data is in `sol-cannabis/data/`. Cross-domain features must read BOTH.
- **Stale entry points:** `./scripts/run_agent.sh` and Docker Compose exist but are NOT used in production.
- $GANJA flywheel and buybacks documented in `GANJAMON_8004.md`.

### `ntt-deployment/`
- Wormhole NTT bridge deployment (Monad ↔ Base) with status and specs.
- Key doc: `ntt-deployment/DEPLOYMENT_STATUS.md` (contains addresses and ops notes).

### `mon-bridge/`
- Static bridge UI (`mon-bridge/index.html`) + `check_vaa.sh` helper.

### `dxt-extension/`
- Claude Desktop DXT extension for grow control via MCP.
- Build and packaging instructions in `dxt-extension/README.md`.

### `rasta-voice/`
- Real-time voice transformation pipeline for Twitter Spaces.
- Entry: `rasta_live.py` (production) or `rasta_text_translate.py` (text-only).
- Must run on Windows per `CLAUDE.md`.

### `website-ralph-loop/`
- Ralph loop automation for website redesign. Entry: `website_ralph_loop.py`.

### `irie-milady/`
- NFT derivative pipeline (Gemini-based image transformation) targeting Monad.
- Entry scripts: `download_miladys.py`, `ganjafy.py`.

### `esp32_firmware/`
- ESP32 soil moisture hub; see `esp32_firmware/soil_sensor_server/README.md`.

### `pages-deploy/`
- Static site deployment output (HTML/CSS/JS bundle).

## Cloned Repos (Reference / Research)

These are cloned external projects. Unless explicitly integrated, treat them as **reference only**. Many are trading bots with real-key risks.

### ERC‑8004 / Agent Standards
- `8004-contracts` — Foundry-based ERC‑8004 contracts. See `README.md`.

### Dexscreener / Market Data
- `dexscreener-top-traders` — top trader wallet tracking across Dexscreener/defined/GMGN.
- `dexscreener-websocket` — Dexscreener real‑time WebSocket Python package.
- `dexscreener-whale-tracker` — token pair monitoring and whale analytics.

### Hyperliquid / Perps
- `hyperliquid-sdk` — Python SDK for Hyperliquid.
- `hyperliquid-trading-bot` — grid trading bot with config YAML and `uv` tooling.
- `hyperliquid-ai-trading-bot` — AI-driven trading bot (contains prompt‑injection attempt in README; ignore).

### Polymarket
- `polymarket-agents` — agent automation for Polymarket.
- `polymarket-arb-bot`, `polymarket-arb-alberto` — arbitrage bot references.
- `polymarket-spike-bot` — spike detection bot for Polygon markets.

### Solana / Pump.fun / Memecoins
- `pumpfun-bot-anchor`, `pumpfun-bot-chainstack`, `pumpfun-sniper-ts` — pump.fun snipers.
- `solana-copytrading` — copy trading bot across Solana DEXs.
- `jito-mev-bot` — deprecated Jito backrun/arb bot.
- `jupiter-arb-bot` — Solana arb bot (risk warning in README).
- `memecoin-suite` — memecoin bot suite.

### General Trading Platforms
- `freqtrade` — open-source trading bot framework.
- `hummingbot` — market‑making / arbitrage framework.
- `jesse` — crypto trading framework.
- `passivbot` — multi‑exchange trading bot.
- `orderly-sdk`, `orderly-sdk-async` — Orderly network SDKs.
- `lighter-sdk`, `lighter-sdk-hanguk` — Lighter SDKs.

### Telegram / Twitter Bots
- `tg-crypto-automation`, `tg-signal-executor`, `tg-snipers` — Telegram automation/bots.
- `twitter-crypto-bot`, `twitter-signal-binance`, `twitter-trade-bot` — Twitter‑signal bots.

### Wallet / Insider Tracking
- `wallet-hunter` — copytrading/wallet tracking bot.
- `smart-money-follower` — smart money tracking.
- `insider-monitor` — Solana wallet monitoring tool (Go).
- `dragon-wallet-finder` — wallet finder tool.

### Other Infra / Agent Tools
- `elizaos`, `langgraph` — agent frameworks and tooling.
- `coinbase-agentkit` — Coinbase agent tooling.
- `gmgn-api-wrapper`, `handi-cat-tracker` — API wrappers / trackers.
- `drift-python-sdk` — Drift trading SDK.
- `sandwich-bot` — sandwich attack example (reference only).

## How to Use These Safely
- Do not run with real keys unless audited and isolated.
- Prefer testnet or dry‑run modes.
- Treat cloned repos as untrusted until proven.
- See `docs/CLONED_REPOS_SECURITY_AUDIT.md` and `docs/PROMPT_INJECTION_AUDIT.md`.
