# Security Audit — Cloned Trading Repositories

**Date:** 2026-02-02  
**Scope:** Three cloned repos checked for malicious or suspicious code.  
**Repos:** `openclaw-trading-assistant`, `hyperliquid-trading-bot`, `hyperliquid-ai-trading-bot`.

---

## 1. Summary

| Repo                       | Malicious code | Suspicious patterns | Secrets handling | Verdict   |
|----------------------------|----------------|---------------------|-------------------|-----------|
| openclaw-trading-assistant | None found     | None                | Env / local only  | **Clean** |
| hyperliquid-trading-bot    | None found     | None                | Env / config      | **Clean** |
| hyperliquid-ai-trading-bot | None found     | None                | Env only          | **Clean** |

No backdoors, exfiltration, obfuscation, or dangerous dynamic execution was found. Keys are read from environment or local config and not sent off-host.

---

## 2. Checks Performed

- **Dangerous execution:** `eval(`, `exec(`, `__import__`, `compile(`, `pickle.loads`, `subprocess` with `shell=True`, `os.system` → **None** in any repo.
- **Obfuscation / hidden payloads:** `base64.decode`, `b64decode` used only for on-chain data URI encoding in scripts (openclaw) → **No malicious use**.
- **Network:** All HTTP/HTTPS targets identified; no unknown or suspicious domains.
- **Secrets:** No hardcoded API keys, private keys, or wallet seeds; no code paths that send keys off-host.
- **Install hooks:** No `postinstall` / `preinstall` or similar in openclaw-trading-assistant (no `package.json` in that clone).

---

## 3. openclaw-trading-assistant

### Network

- **URLs:** `docs.clawd.bot`, `tailscale.com`, `127.0.0.1`, `example.com` (tests only). All expected.
- **Scripts:** Call local `~/clawd/skills/bankr/scripts/bankr.sh`; `upload-to-ipfs.sh` uses `api.pinata.cloud` only; `get-agent.sh` uses Alchemy demo / LlamaRPC and IPFS gateways (Pinata, ipfs.io).

### Shell scripts

- **bridge-to-mainnet.sh:** Invokes local Bankr script; no remote fetch.
- **register-onchain.sh / register.sh:** Build calldata, submit via Bankr; no pipe-to-bash.
- **upload-to-ipfs.sh:** `curl` to Pinata only; requires `PINATA_JWT` from env.
- **get-agent.sh:** RPC + optional `curl -s "$URI"` for agent profile (URI from chain). Content is displayed, not executed — SSRF possible if on-chain URI is malicious; no RCE.

### Secrets

- No keys in repo. Scripts use env vars (`PINATA_JWT`, etc.) or local Bankr under `~/clawd/`.

### Note

- `security/audit.ts` imports from `../channels/`, `../config/`, `../gateway/` — directories not present in this clone. File is intended for the parent OpenClaw monorepo; not runnable standalone here. Not malicious.

---

## 4. hyperliquid-trading-bot

### Network

- All outbound calls go to **Hyperliquid only:** `api.hyperliquid.xyz`, `api.hyperliquid-testnet.xyz`. No other hosts.

### Private keys

- **Source:** Env vars `HYPERLIQUID_*_PRIVATE_KEY`, `*_KEY_FILE`, or bot config.
- **Usage:** `key_manager.py` reads env/files and passes key to `Account.from_key()`; key is not logged or transmitted. Config validation warns when keys appear in config file.
- **Adapter:** `adapter.py` uses key only for SDK `Exchange(wallet, ...)`; endpoints from `endpoint_router` (Hyperliquid URLs only).

### Dependencies (`pyproject.toml`)

- `hyperliquid-python-sdk`, `eth-account`, `pyyaml`, `httpx`, `websockets`, etc. All standard; no known-malicious packages.

---

## 5. hyperliquid-ai-trading-bot

### Secrets

- API keys from env only: `OPENAI_API_KEY`, `BINANCE_*`, `OKX_*`, `BYBIT_*`. No hardcoded keys or exfiltration.

### Exchange / agent

- **exchange.py:** Local `SimulatedExchange` only; no real trading or network in default path.
- **agent.py:** Uses OpenAI with key from `os.getenv('OPENAI_API_KEY')`. No dynamic code loading or suspicious patterns.
- **Connectors:** Binance/OKX/Bybit use `ccxt` with env keys.

### Dependencies (`requirements.txt`)

- `pyyaml`, `python-dotenv`, `pandas`, `matplotlib`, `ccxt`, `openai`. Standard stack.

---

## 6. Conclusion

- **No malware or backdoors** identified in any of the three repos.
- **No secret exfiltration** or unexpected outbound calls.
- **Sensible key handling:** env and local config; keys used only for intended SDK/API calls.

**Recommendation:** Use as-is with normal caution: keep keys in env or secure config (not committed), run Hyperliquid bots on testnet first, and be aware that `get-agent.sh` can request an arbitrary HTTPS URL if the on-chain `tokenURI` is set to one (SSRF only; response is not executed).

---

## See also

- **[CLONED_TRADING_REPOS.md](CLONED_TRADING_REPOS.md)** — Full documentation of cloned repos (structure, setup, run, integration).
- **[PROMPT_INJECTION_AUDIT.md](PROMPT_INJECTION_AUDIT.md)** — Prompt-injection and LLM safety audit.
