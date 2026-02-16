# clawd.atg.eth (CLAWD) – Reference

Everything gathered about **clawd.atg.eth** and the CLAWD token ecosystem.

---

## 1. Identity & ENS

| Item | Value |
|------|--------|
| **ENS name** | `clawd.atg.eth` |
| **Parent ENS** | `atg.eth` (Austin Griffith’s domain) |
| **ENS expiry** | No expiry (subname under atg.eth) |
| **ENS app** | https://app.ens.domains/clawd.atg.eth |

**atg.eth** is Austin Griffith’s ENS domain. Austin Griffith is an Ethereum Foundation developer (developer onboarding, mentoring, tooling). His primary ENS is **austingriffith.eth** → `0x34aA3F359A9D614239015126635CE7732c18fDF3`. The subname **clawd.atg.eth** is the ENS identity for the “clawd” AI-agent persona and associated token.

---

## 2. CLAWD Token (Base)

| Field | Value |
|-------|--------|
| **Chain** | Base (EVM) |
| **Contract (Base)** | `0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07` |
| **Ticker / label** | CLAWD (CLAWDONBASE on some CEX) |
| **Trading** | Uniswap and other AMMs on Base |
| **DexScan** | Safe, verified, no honeypot reported |
| **Buy/Sell tax** | 0% (no tax) |

**Supply (reported):** ~99.99B–100B tokens. FDV and liquidity vary by source and time (e.g. FDV ~$7.3M–$30.9M, liquidity ~$3.9M, 24h volume up to ~$26.2M; ~7.7K holders as of cited data).

---

## 3. Narrative & Purpose

- **clawd.atg.eth** is described in public reporting as a **self-hosted personal AI assistant** built by Austin Griffith with open-source tooling.
- The **CLAWD token** is a **Base-chain meme token** tied to this AI-agent narrative: “clawd.atg.eth” as a character/brand.
- Public reports mention:
  - Community deployers intending to route a portion of transaction fees to the agent’s wallet.
  - Game-like mechanics and experiments (e.g. prediction markets where holders can stake for participation).
- Framed as a **social experiment** blending meme culture and AI-agent branding rather than formal utility or governance.

---

## 4. Ecosystem & Related Addresses

From your **clawd-tipjar** clone (`cloned-repos/clawd-tipjar`):

- **CLAWD token (Base):** `0x9f86dB9fc6f7c9408e8Fda3Ff8ce4e78ac7a6b07` (used in `DeployClawdTipJar.s.sol`).
- **Dev wallet (tip jar):** `0x11ce532845cE0eAcdA41f72FDc1C88c335981442` — commented as **clawdbotatg.eth**.
- **ClawdTipJar:** 50% of tips to dev wallet, 50% burn.

GitHub org referenced in clawd-tipjar: **clawdbotatg** (e.g. `https://github.com/clawdbotatg/clawd-tipjar`).

---

## 5. Austin Griffith Repos (Your Clone)

- **atg.eth** = Austin Griffith; your **austintgriffith** folder is a collection of his repos (scaffold-eth, burner wallet, eth.build, etc.).
- The **atgbg** repo under `cloned-repos/austintgriffith/atgbg` is unrelated to CLAWD (desktop background script).
- Another AG subdomain in your tree: **passkeydemo.atg.eth.link** (passkey-oneshot demo).

So: **clawd** is a subname of **atg.eth**; the token and tip jar are part of the same “clawd.atg.eth” ecosystem.

---

## 6. Links

| Resource | URL |
|----------|-----|
| ENS profile | https://app.ens.domains/clawd.atg.eth |
| Tapbit explainer | https://blog.tapbit.com/what-is-clawd-atg-eth-clawd-and-how-it-works/ |
| Base token (OpenSea) | https://opensea.io/token/base/0x9f86db9fc6f7c9408e8fda3ff8ce4e78ac7a6b07 |
| Base contract | https://basescan.org/token/0x9f86db9fc6f7c9408e8fda3ff8ce4e78ac7a6b07 |
| Austin Griffith | https://austingriffith.com/ |

---

## 7. In This Repo

- **clawd-tipjar** uses the CLAWD token and clawdbotatg.eth dev wallet; contract address and dev share are in `packages/foundry/script/DeployClawdTipJar.s.sol` and `packages/foundry/contracts/ClawdTipJar.sol`.
- No other direct references to **clawd.atg.eth** or the CLAWD contract were found in the rest of the codebase; the clawd-* and openclaw-* repos are separate ecosystem projects.

---

*Collected Feb 2026; on-chain and market data may change.*
