# Cloned Trading Repositories — Full Documentation

**Purpose:** Reference for OpenClaw/MoltBot and Hyperliquid onchain trading repos cloned into this project.  
**Clone date:** 2026-02-02.  
**Location:** Repos live at repo root: `openclaw-trading-assistant/`, `hyperliquid-trading-bot/`, `hyperliquid-ai-trading-bot/`.

---

## Table of contents

1. [Overview](#1-overview)
2. [What was cloned](#2-what-was-cloned)
3. [Repos not found (404)](#3-repos-not-found-404)
4. [openclaw-trading-assistant](#4-openclaw-trading-assistant)
5. [hyperliquid-trading-bot (Chainstack)](#5-hyperliquid-trading-bot-chainstack)
6. [hyperliquid-ai-trading-bot](#6-hyperliquid-ai-trading-bot)
7. [Security & safety](#7-security--safety)
8. [Integration notes](#8-integration-notes)
9. [Quick reference](#9-quick-reference)

---

## 1. Overview

We searched for **OpenClaw/MoltBot bots that trade onchain**, then cloned high-quality repos and audited them for malicious code and prompt-injection risk.

- **openclaw-trading-assistant** — OpenClaw/MoltBot AI trading assistant (nof1 × OpenClaw), Hyperliquid API, Alpha Arena–style design. This clone is the **OpenClaw layer** (routing, sessions, wizard, ERC-8004 scripts); the full trading engine lives in the main OpenClaw monorepo or nof1 tooling.
- **hyperliquid-trading-bot** — Chainstack Labs grid bot for Hyperliquid DEX: Python, `uv`, grid strategy, risk manager, learning examples (websockets, market data, account, trading, funding, copy-trading).
- **hyperliquid-ai-trading-bot** — AI/LLM trading example: simulated exchange, OpenAI (or placeholder) for buy/sell/hold, connectors for Binance/OKX/Bybit, backtester, risk, journal.

All three were checked for malware and prompt injection; see [Security & safety](#7-security--safety).

---

## 2. What was cloned

| Local path | Upstream | License | Notes |
|------------|----------|---------|--------|
| `openclaw-trading-assistant/` | [molt-bot/openclaw-trading-assistant](https://github.com/molt-bot/openclaw-trading-assistant) | Apache-2.0 | OpenClaw trading UI/routing/sessions/wizard + ERC-8004 scripts |
| `hyperliquid-trading-bot/` | [chainstacklabs/hyperliquid-trading-bot](https://github.com/chainstacklabs/hyperliquid-trading-bot) | (see repo) | Grid bot, Hyperliquid SDK, learning examples |
| `hyperliquid-ai-trading-bot/` | [hyperliquid-ai-trading-bot/hyperliquid-ai-trading-bot](https://github.com/hyperliquid-ai-trading-bot/hyperliquid-ai-trading-bot) | (see repo) | AI agent example, OpenAI/placeholder, simulated + CCXT |

Clone commands used:

```bash
git clone --depth 1 https://github.com/molt-bot/openclaw-trading-assistant.git openclaw-trading-assistant
git clone --depth 1 https://github.com/chainstacklabs/hyperliquid-trading-bot.git hyperliquid-trading-bot
git clone --depth 1 https://github.com/hyperliquid-ai-trading-bot/hyperliquid-ai-trading-bot.git hyperliquid-ai-trading-bot
```

---

## 3. Repos not found (404)

These were not cloned (remote not found or private):

- `nof1-ai-alpha-arena/nof1.ai-alpha-arena` — Alpha Arena trading engine (often cited with openclaw-trading-assistant).
- `NocturneAgent/ai-trading-agent` — LLM trading agent on Hyperliquid.
- `cnaovalles/hyperliquid-trading-bot` — Alternative Hyperliquid bot.

---

## 4. openclaw-trading-assistant

### Purpose

nof1.ai × OpenClaw collaboration: conversational AI trading assistant using Hyperliquid, Alpha Arena–style decision engine, market intelligence (e.g. X sentiment), and local-first security. This repo is the **OpenClaw layer** (conversation, routing, onboarding wizard, ERC-8004 registration scripts); the actual agent/LLM and trading engine are in the main [openclaw/openclaw](https://github.com/openclaw/openclaw) monorepo or nof1 tooling.

### Structure

```
openclaw-trading-assistant/
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── security/
│   ├── audit-extra.ts
│   ├── audit-fs.ts
│   ├── audit.test.ts
│   ├── audit.ts
│   ├── fix.test.ts
│   └── fix.ts
├── src/
│   ├── routing/          # Agent/session routing, bindings, session-key, sanitizeAgentId
│   ├── scripts/          # ERC-8004: register, IPFS, onchain, bridge, get-agent
│   ├── sessions/         # Send policy, model overrides, transcript events
│   └── wizard/           # Onboarding, gateway config, clack prompter
└── utils/                # Message channel, delivery context, usage format, etc.
```

**Key files:**

- `src/routing/session-key.ts` — `sanitizeAgentId()`, `normalizeAgentId()` (path-safe agent IDs).
- `src/scripts/` — Shell scripts: `register.sh`, `register-onchain.sh`, `upload-to-ipfs.sh`, `create-registration.sh`, `get-agent.sh`, `bridge-to-mainnet.sh` (depend on `~/clawd/skills/bankr/` and env like `PINATA_JWT`).
- `src/wizard/onboarding.ts`, `onboarding.gateway-config.ts`, `onboarding.finalize.ts` — Wizard flow (no LLM in this repo).
- `security/audit.ts`, `audit-extra.ts` — Security checks; written for parent OpenClaw monorepo (imports `../channels/`, `../config/` etc. not present in this clone).

**No `package.json`** in this clone — it’s a fragment intended to be used inside the main OpenClaw repo.

### Dependencies

TypeScript; depends on parent monorepo for build and runtime deps (e.g. `@clack/prompts`). Scripts use `bash`, `node`, `jq`, `curl`.

### Config / env

- Scripts: `PINATA_JWT`, `AGENT_NAME`, `AGENT_DESCRIPTION`, `AGENT_IMAGE`, `AGENT_WEBSITE`, `AGENT_A2A_ENDPOINT`, `AGENT_MCP_ENDPOINT`, `AGENT_ENS`, `X402_SUPPORT`, `REGISTRATION_URL` (for register-http).
- Bankr: expects `~/clawd/skills/bankr/scripts/bankr.sh`.

### How to run

- **Standalone:** Scripts can be run if deps exist (e.g. `node`, `jq`, Bankr at `~/clawd/`). Wizard/TypeScript code expects the full OpenClaw tree.
- **As part of OpenClaw:** Integrate this folder into [openclaw/openclaw](https://github.com/openclaw/openclaw) and use the main OpenClaw install (e.g. Releases, or `openclaw onboard`, `openclaw gateway`).

### Docs

- README in repo: architecture diagram, features (Alpha Arena, Hyperliquid, sentiment, risk, non-custodial), install (Releases / macOS .dmg), chat commands, security (DM pairing).
- Official: [docs.clawd.bot](https://docs.clawd.bot), [openclaw.ai](https://openclaw.ai).

---

## 5. hyperliquid-trading-bot (Chainstack)

### Purpose

Extensible **grid trading bot** for Hyperliquid DEX: config-driven grid strategy, risk manager, key manager (testnet/mainnet, env/file), and learning examples for websockets, market data, account info, trading, funding, and copy-trading.

### Structure

```
hyperliquid-trading-bot/
├── .gitignore
├── .python-version
├── AGENTS.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── pyproject.toml
├── uv.lock
├── bots/
│   └── btc_conservative.yaml
├── learning_examples/
│   ├── 01_websockets/      # realtime_prices.py, realtime_prices_multiple_subs.py
│   ├── 02_market_data/     # get_all_prices.py, get_market_metadata.py
│   ├── 03_account_info/    # get_open_orders.py, get_user_state.py
│   ├── 04_trading/         # place_limit_order.py, cancel_orders.py
│   ├── 05_funding/         # funding rates, spot/perp availability
│   └── 06_copy_trading/   # mirror_spot_orders, mirror_spot_twap, order_scenarios
├── src/
│   ├── core/               # endpoint_router, engine, enhanced_config, key_manager, risk_manager
│   ├── exchanges/hyperliquid/  # adapter.py, market_data.py
│   ├── interfaces/         # exchange, strategy
│   ├── strategies/grid/    # basic_grid
│   ├── utils/              # events, exceptions
│   └── run_bot.py
```

**Key files:**

- `src/run_bot.py` — Entrypoint; loads config, key manager, exchange, strategy, risk, runs loop.
- `src/core/key_manager.py` — Resolves private key from env (`HYPERLIQUID_TESTNET_PRIVATE_KEY`, etc.) or config; no key exfil.
- `src/core/engine.py` — Trading engine: connect, strategy, risk events, order execution.
- `src/exchanges/hyperliquid/adapter.py` — Hyperliquid adapter (Account.from_key, SDK Exchange/Info).
- `src/core/endpoint_router.py` — Routes to `api.hyperliquid.xyz` / `api.hyperliquid-testnet.xyz` only.

### Dependencies (pyproject.toml)

- `hyperliquid-python-sdk>=0.20.0`, `eth-account>=0.10.0`, `pyyaml`, `httpx`, `websockets`, `python-dotenv`, `psutil`, `typing-extensions`. Optional: pytest, black, isort, mypy.

### Config / env

- **.env:** `HYPERLIQUID_TESTNET_PRIVATE_KEY`, `HYPERLIQUID_TESTNET=true` (or mainnet equivalents). Optional: `HYPERLIQUID_*_KEY_FILE`, bot-specific keys in YAML.
- **Bot YAML (e.g. `bots/btc_conservative.yaml`):** `name`, `active`, `account`, `grid`, `risk_management`, `monitoring`.

### How to run

```bash
cd hyperliquid-trading-bot
uv sync
# .env with HYPERLIQUID_TESTNET_PRIVATE_KEY, HYPERLIQUID_TESTNET=true
uv run src/run_bot.py                    # auto-discover first active config
uv run src/run_bot.py --validate        # validate config
uv run src/run_bot.py bots/btc_conservative.yaml
```

Learning examples (examples call Hyperliquid APIs; some need `.env`):

```bash
uv run learning_examples/01_websockets/realtime_prices.py
uv run learning_examples/02_market_data/get_all_prices.py
uv run learning_examples/03_account_info/get_user_state.py
uv run learning_examples/04_trading/place_limit_order.py
# etc.
```

### Docs

- README: quick start, config schema, learning examples, exit strategies, development (uv, testing).
- Chainstack: [Hyperliquid docs](https://docs.chainstack.com/docs/developer-portal-mcp-server), [testnet faucet](https://faucet.chainstack.com/hyperliquid-testnet-faucet).

---

## 6. hyperliquid-ai-trading-bot

### Purpose

**AI trading example:** local simulation with an “agent” that decides buy/sell/hold from market snapshots. Supports OpenAI (and placeholders for Qwen/DeepSeek); exchange is simulated by default; connectors exist for Binance/OKX/Bybit (CCXT). Useful as a pattern for LLM-driven trading and backtesting.

### Structure

```
hyperliquid-ai-trading-bot/
├── .gitignore
├── config.yaml
├── example_config.json
├── LICENSE
├── README.md
├── requirements.txt
├── run.py
├── scope.txt
├── data/
│   └── sample_ohlcv.csv
├── bot/
│   ├── agent.py       # OpenAIModel, Qwen/DeepSeek placeholders, get_model()
│   ├── backtester.py
│   ├── exchange.py    # SimulatedExchange
│   ├── journal.py
│   ├── risk.py
│   ├── runner.py
│   ├── utils.py
│   └── connectors/     # binance.py, bybit.py, okx.py (CCXT)
├── examples/
│   ├── use_agent_backtest.py
│   └── use_real_exchange.py
```

**Key files:**

- `bot/agent.py` — Builds prompt from `market_snapshot`, calls OpenAI (or placeholder); parses reply with `'buy' in text` / `'sell' in text`. Default config uses `model: placeholder` (no API call).
- `bot/runner.py` — Loads config, SimulatedExchange, agent (AIModelPlaceholder by default), risk, journal; runs simulation loop.
- `bot/exchange.py` — SimulatedExchange: get_market_snapshot(), place_order(); no real exchange.
- `config.yaml` — general (dry_run, starting_balance), trading (symbol, risk_per_trade_pct, mode), ai (model, temperature), notifications.

### Dependencies (requirements.txt)

- `pyyaml`, `python-dotenv`, `pandas`, `matplotlib`, `ccxt`, `openai`.

### Config / env

- **config.yaml:** `general`, `trading`, `ai` (e.g. `model: placeholder` or `gpt-4o`), `notifications`.
- **Env (when using OpenAI/connectors):** `OPENAI_API_KEY`, `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `OKX_*`, `BYBIT_*`.

### How to run

```bash
cd hyperliquid-ai-trading-bot
pip install -r requirements.txt
# Default: config.yaml has model: placeholder (simulation only)
python run.py
# Or use examples
python examples/use_agent_backtest.py
python examples/use_real_exchange.py  # needs API keys in env
```

### Docs

- README: concept (local, multi-model, risk), features, install, config. I18n: README.zh-CN.md, README.ko-KR.md, README.ja-JP.md.

---

## 7. Security & safety

### Malicious code / backdoors

A full review was done for dangerous patterns, network calls, and secret handling. **Result: no malicious code found.** Summary:

- **openclaw-trading-assistant:** No eval/exec/pipe-to-bash; URLs only to docs, Pinata, Alchemy/LlamaRPC, IPFS gateways; keys from env/local Bankr.
- **hyperliquid-trading-bot:** All traffic to Hyperliquid APIs; keys from env/config, used only for SDK; key_manager does not log or send keys.
- **hyperliquid-ai-trading-bot:** Keys from env; SimulatedExchange + optional OpenAI/CCXT; no exfil or obfuscation.

**Detailed write-up:** [CLONED_REPOS_SECURITY_AUDIT.md](CLONED_REPOS_SECURITY_AUDIT.md).

### Prompt injection / LLM safety

- **openclaw-trading-assistant:** No LLM in this repo; user chat is handled in main OpenClaw. Audit text in repo warns about prompt injection and tool misuse.
- **hyperliquid-ai-trading-bot:** Only LLM use is in `bot/agent.py`. Prompt is built from internal `market_snapshot` (no user text today). Design has no system prompt and brittle output parsing (`'buy' in text`); if external text (e.g. news, sentiment) is ever added to the prompt, that becomes an injection vector.
- **hyperliquid-trading-bot:** No LLM; no prompt-injection surface.

**Detailed write-up:** [PROMPT_INJECTION_AUDIT.md](PROMPT_INJECTION_AUDIT.md).

---

## 8. Integration notes

- **Sol-cannabis:** This project (Grok & Mon) uses Grok for cultivation decisions and Monad for $MON; it does not run OpenClaw or Hyperliquid trading by default. The cloned repos are for reference, experimentation, or future integration (e.g. Hyperliquid execution patterns, or OpenClaw-style chat over a trading backend).
- **Existing `openclaw/` folder:** There is already an `openclaw/` directory in the repo (likely a different clone or copy). `openclaw-trading-assistant` is the **trading-specific** variant; keep the two distinct or align config/skills if you want one OpenClaw instance to drive trading.
- **Using Hyperliquid bots:** Prefer testnet first; keep keys in `.env` or secure config; never commit keys. Chainstack bot: `uv sync` + `.env` + `uv run src/run_bot.py`. AI bot: default `model: placeholder` is simulation-only; switching to OpenAI requires `OPENAI_API_KEY` and hardening (system prompt, structured output) if you add untrusted input to prompts.

---

## 9. Quick reference

| Topic | Doc |
|-------|-----|
| What was cloned, structure, setup, run | This file (CLONED_TRADING_REPOS.md) |
| Malicious code / backdoors / secrets | [CLONED_REPOS_SECURITY_AUDIT.md](CLONED_REPOS_SECURITY_AUDIT.md) |
| Prompt injection & LLM safety | [PROMPT_INJECTION_AUDIT.md](PROMPT_INJECTION_AUDIT.md) |
| Chromebook server (Grok & Mon) | [CHROMEBOOK_SERVER.md](CHROMEBOOK_SERVER.md) |
| Cultivation / grow params | [CULTIVATION_REFERENCE.md](CULTIVATION_REFERENCE.md) |
| Token / Monad | [TOKEN_ECONOMICS_REVISED.md](TOKEN_ECONOMICS_REVISED.md) |

| Repo | Path | Main use |
|------|------|----------|
| OpenClaw trading | `openclaw-trading-assistant/` | OpenClaw layer + ERC-8004 scripts; full agent in main OpenClaw |
| Chainstack HL bot | `hyperliquid-trading-bot/` | Grid bot + learning examples on Hyperliquid |
| AI HL bot | `hyperliquid-ai-trading-bot/` | AI trading example (simulation + optional OpenAI/CCXT) |

---

*Last updated: 2026-02-02.*
