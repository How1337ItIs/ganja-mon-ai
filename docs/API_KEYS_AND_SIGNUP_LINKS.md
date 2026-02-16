# API Keys in This Project & Links to Fetch the Rest

**Security:** Never commit real keys. Use `.env` (gitignored) or env vars. This doc lists **env var names** and **signup links** only — no secret values.

---

## 1. Keys This Project Already Uses (env var names)

Set these in `.env` at repo root and/or `rasta-voice/.env` as needed.

| Env var | Where used | Notes |
|---------|------------|--------|
| **XAI_API_KEY** | `src/orchestrator.py`, `src/api/app.py`, `src/telegram/personality.py`, rasta-voice | xAI Grok API (brain + telegram + rasta) |
| **GOVEE_API_KEY** | `src/api/app.py` | Govee devices (temp/humidity/CO2/humidifier) |
| **DEEPGRAM_API_KEY** | `rasta-voice/rasta_live.py`, `rasta_live_megaphone.py` | STT for rasta pipeline |
| **GROQ_API_KEY** | `rasta-voice/rasta_live.py`, `rasta_live_megaphone.py` | LLM for rasta (Patois) |
| **ELEVENLABS_API_KEY** | `rasta-voice/rasta_live.py`, `rasta_live_megaphone.py` | TTS for rasta |
| **ELEVENLABS_VOICE_ID** | rasta-voice (optional; has default) | Voice ID (e.g. Denzel) |
| **TWITTER_API_KEY** | `src/social/twitter.py`, `scheduled_tweet.py` | Twitter/X API (consumer key) |
| **TWITTER_API_SECRET** | `src/social/twitter.py`, `scheduled_tweet.py` | Twitter/X API (consumer secret) |
| **TWITTER_ACCESS_TOKEN** | `src/social/twitter.py`, `scheduled_tweet.py` | Twitter/X API |
| **TWITTER_ACCESS_SECRET** | `src/social/twitter.py`, `scheduled_tweet.py` | Twitter/X API |
| **TWITTER_BEARER_TOKEN** | `src/social/twitter.py` | Twitter/X API (Bearer) |
| **TELEGRAM_BOT_TOKEN** | `src/telegram/bot.py` | Telegram bot |
| **TELEGRAM_API_ID** / **TELEGRAM_API_HASH** / **TELEGRAM_PHONE** | Various telegram scripts | Telegram client (e.g. Rose/filters) |
| **GEMINI_API_KEY** | `telegram_batch_ganjafy.py` | Google Gemini (optional) |
| **BLOCKVISION_API_KEY** | `scripts/blockvision_*.py`, `scripts/quick_volume_check.py`, `scripts/get_market_volume.py` | BlockVision Monad RPC/API (set in .env; do not commit) |
| **MONAD_RPC_URL** | `scripts/lfj_volume_report.py`, `scripts/get_market_volume.py` | Override RPC (e.g. BlockVision URL with key) |
| **ADMIN_PASSWORD** | API (see CLAUDE.md) | Dashboard admin |
| **MON_CONTRACT** | `src/telegram/personality.py` (optional) | $MON token CA for messages |
| **ECOWITT_GATEWAY_IP** | `src/orchestrator.py`, `src/api/app.py` | Ecowitt soil moisture gateway |
| **KASA_*_IP** | `src/orchestrator.py`, `src/mcp/tools.py`, `src/api/app.py` | Kasa plug IPs (pump, fans, light, etc.) |
| **TAPO_USERNAME** / **TAPO_PASSWORD** / **TAPO_GROW_LIGHT_IP** | orchestrator, MCP, app | Tapo smart plug (light) |
| **USE_HARDWARE** | `src/api/app.py` | `true`/`false` |
| **CORS_ORIGINS** | `src/api/app.py` | Allowed origins |
| **IP_CAMERA_URL** (optional **IP_CAMERA_USER** / **IP_CAMERA_PASS**) | `src/api/app.py` | MJPEG/IP camera |

---

## 2. Links to Get API Keys (project + Monad/forensic tooling)

### Already in use in this repo

| Service | Get key / signup |
|---------|-------------------|
| **xAI (Grok)** | https://console.x.ai/ (API keys) |
| **Govee** | https://developer.govee.com/ (register app, get API key) |
| **Deepgram** | https://console.deepgram.com/ (sign up, API key in dashboard) |
| **Groq** | https://console.groq.com/ (API keys) |
| **ElevenLabs** | https://elevenlabs.io/app/settings/api-keys |
| **Twitter / X** | https://developer.twitter.com/ (Projects & Apps → keys and tokens) |
| **Telegram Bot** | https://t.me/BotFather → /newbot → token |
| **Telegram API (client)** | https://my.telegram.org/apps (API ID & API Hash) |
| **Google Gemini** | https://aistudio.google.com/apikey or Google AI Studio |
| **BlockVision** | https://www.blockvision.org/ or https://docs.blockvision.org/ (Monad RPC/Indexing API; trial then Pro) |

### Monad / forensic APIs (from MONAD_APIS_AND_FORENSIC_TOOLING.md)

Use these when you need higher limits, debug/trace, or dedicated keys.

| Service | Get key / signup |
|---------|-------------------|
| **Monadscan (Etherscan API)** | https://docs.monadscan.com/getting-an-api-key (free 3/sec; same key for 60+ chains) |
| **Alchemy** | https://dashboard.alchemy.com/ (Monad in chain list) |
| **Ankr** | https://www.ankr.com/rpc/ or https://www.ankr.com/account/ |
| **Chainstack** | https://chainstack.com/ (free tier, add Monad) |
| **dRPC** | https://drpc.org/ (Monad mainnet) |
| **GetBlock** | https://getblock.io/ (nodes → Monad) |
| **OnFinality** | https://onfinality.io/ (networks → Monad Mainnet) |
| **Validation Cloud** | https://validationcloud.io/ (50M CU free, no card) |
| **Envio HyperRPC** | https://envio.dev/app/api-tokens (token for HyperRPC/HyperSync) |
| **Dwellir** | https://dwellir.com/networks/monad |
| **GoldRush (Covalent)** | https://goldrush.dev/platform/auth/register/ |
| **Moralis** | https://admin.moralis.io/register |
| **thirdweb** | https://thirdweb.com/team (Insight API) |
| **Dune** | https://dune.com/ (account → API for query execution) |
| **CoinGecko** | https://www.coingecko.com/en/api/pricing (free tier) |
| **Birdeye** | https://bds.birdeye.so/ (Birdeye Data Services) |
| **Codex** | https://dashboard.codex.io/ |
| **Mobula** | https://mobula.io/ (dashboard / API key) |
| **JiffyScan (4337)** | https://docs.jiffyscan.xyz/ (request API key via form; ~2 days) |
| **BlockVision (Monad Indexing)** | https://docs.blockvision.org/reference/monad-indexing-api (Pro for mainnet; 30 free trial calls) |
| **SocialScan / Hemera** | https://thehemera.gitbook.io/explorer-api (explorer API access) |
| **Phalcon (BlockSec)** | https://blocksec.com/explorer (use UI; check BlockSec for API if needed) |
| **Tenderly** | https://dashboard.tenderly.co/ (account; explorer + API) |
| **3loop Decoder** | https://loop-decoder.3loop.io/ or decoder API docs (Swagger: decoder-api.3loop.io/swagger) |

### No key required (use as-is)

- **DeFiLlama:** https://api.llama.fi (no key)
- Public RPCs: `https://rpc.monad.xyz`, `https://rpc1.monad.xyz`, `https://rpc3.monad.xyz`, `https://rpc-mainnet.monadinfra.com`, `https://143.rpc.thirdweb.com`, etc. (rate-limited; see Monad doc)
- **Phalcon / Tenderly** web UIs for traces (no key for basic use)

---

## 3. Hardcoded key cleanup

**BlockVision:** Some scripts had a fallback key in code. That fallback has been removed so only `BLOCKVISION_API_KEY` from the environment is used. Set it in `.env` and get a key from BlockVision if you need their RPC/API.

---

## 4. Quick copy: .env template (names only)

```bash
# Brain / API
XAI_API_KEY=
ADMIN_PASSWORD=

# Hardware
GOVEE_API_KEY=
ECOWITT_GATEWAY_IP=
KASA_WATER_PUMP_IP=
KASA_EXHAUST_FAN_IP=
KASA_CIRC_FAN_IP=
KASA_GROW_LIGHT_IP=
TAPO_USERNAME=
TAPO_PASSWORD=
TAPO_GROW_LIGHT_IP=

# Rasta voice (Windows)
DEEPGRAM_API_KEY=
GROQ_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Twitter
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_BEARER_TOKEN=

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=

# Optional
GEMINI_API_KEY=
MON_CONTRACT=
MONAD_RPC_URL=
BLOCKVISION_API_KEY=
```

Use `.env.example` in repo root and `rasta-voice/.env.example` for full templates; copy to `.env` and fill values.
