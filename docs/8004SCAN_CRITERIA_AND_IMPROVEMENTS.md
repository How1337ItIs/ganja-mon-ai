# 8004scan Criteria & GanjaMon Improvement Plan

**Last Updated:** February 7, 2026
**Source:** 8004scan UI score breakdown, [best-practices.8004scan.io](https://best-practices.8004scan.io), and EIP-8004 metadata profile.

## Score Before Improvements (2026-02-06)

| Dimension   | Weight | Score (0-100) | Weighted | Notes                    |
|------------|--------|----------------|----------|--------------------------|
| Engagement | 30%    | 44             | +0       | Chats, messages, stars    |
| Service    | 25%    | **0**         | +0.0     | A2A endpoint unreachable  |
| Publisher  | 20%    | **12**        | +2.4     | Unverified                |
| Compliance | 15%    | 54             | +8.1     | IA022 + IA009 + WA040     |
| Momentum   | 10%    | 50             | +5.0     | 2 days old                |
| **Total**  |        | **43.89**      | ~15.5    | Rank #3890                |

---

## Changes Made (2026-02-07)

### Compliance Fixes (was 54)
- [x] Added `version: "0.3.0"` to A2A service entry (**fixes IA022**)
- [x] Changed `supportedTrust` from `["reputation", "validation"]` to `["reputation", "crypto-economic"]` (**fixes IA009**)
- [x] Added `updatedAt` Unix timestamp for metadata freshness
- [x] Expanded to 4 services: A2A (with version + a2aSkills), agentWallet, x402, web
- [x] Expanded description to include "Supports A2A protocol and x402 micropayments"
- [x] Moved agentURI to IPFS: `ipfs://QmVVWECNd6BfuHAKxiZUAXoKzcFgKYKeJ466W3dAnh9GN4` (**fixes WA040**)
- [x] Fixed mirror file `well-known/agent-registration.json` (had invalid JS comment breaking JSON)

### Service Fix (was 0)
- [x] **Root cause**: `agent.grokandmon.com/a2a/v1` returned 404 — validators couldn't reach A2A endpoint
- [x] Created Cloudflare Pages Function at `pages-deploy/functions/a2a/v1.js` returning valid agent-card JSON
- [x] Updated `grokmon-router` Worker to include `/a2a/` in STATIC_PATHS
- [x] Verified all 4 endpoints return 200 + valid JSON on production:
  - `grokandmon.com/.well-known/agent-registration.json`
  - `grokandmon.com/.well-known/agent-card.json`
  - `grokandmon.com/a2a/v1`
  - `grokandmon.com/.well-known/x402-pricing.json`

### Momentum
- [x] Called `setAgentURI(4, ...)` on-chain twice (HTTP URI, then IPFS URI)
- [x] Both transactions confirmed on Monad

### Publisher
- [x] Emailed `team@8004scan.io` requesting verification badge (2026-02-07)
- [ ] Awaiting response

### Engagement
- [x] Added agent tasks for Grok to promote 8004scan profile via social channels
- [ ] Need community stars, watches, and feedback (manual/social effort)

---

## 8004scan Scoring Criteria (Inferred)

8004scan does not publish an exact formula. Inferred from the UI, [Agent Metadata Profile](https://best-practices.8004scan.io/docs/01-agent-metadata-standard.html), and error codes.

### 1. Engagement (30%)
- **Inputs:** Stars, watches, feedback, validations, chats, messages
- **How to improve:** Community engagement — ask users to star/watch on 8004scan, submit on-chain feedback via Reputation Registry

### 2. Service (25%)
- **Inputs:** Validator liveness checks on declared service endpoints (A2A, x402, web)
- **Key insight:** Validators call the A2A `url` field from agent-card.json — if it 404s, Service = 0
- **How to improve:** Keep all declared endpoints publicly reachable, returning valid JSON with correct Content-Type

### 3. Publisher (20%)
- **Inputs:** Verification badge, org reputation, branding consistency
- **How to improve:** Get verified via 8004scan team, use consistent org name/URL everywhere

### 4. Compliance (15%)
- **Inputs:** Metadata spec adherence per [Agent Metadata Profile](https://best-practices.8004scan.io/docs/01-agent-metadata-standard.html)
- **Error codes that matter:**
  - **WA040**: HTTP/HTTPS URI not content-addressed → use IPFS
  - **IA022**: A2A endpoint missing `version` field
  - **IA009**: Unknown trust model → valid: `reputation`, `crypto-economic`, `tee-attestation`
  - **WA031**: Using legacy `endpoints` instead of `services`
- **How to improve:** Follow spec exactly, resolve all warnings and recommendations

### 5. Momentum (10%)
- **Inputs:** Recent on-chain events (setAgentURI), metadata freshness, recent feedback
- **How to improve:** Regular metadata updates, keep `updatedAt` fresh

---

## Metadata Spec Requirements

| Field | Required | Notes |
|-------|----------|-------|
| `type` | SHOULD | `https://eips.ethereum.org/EIPS/eip-8004#registration-v1` |
| `name` | SHOULD | 3-200 characters |
| `description` | SHOULD | 50-500 characters recommended |
| `image` | SHOULD | PNG/SVG/WebP/JPG, 512x512+ preferred, absolute HTTPS, <5MB |
| `services` | SHOULD | Array with `name`, `endpoint`, optional `version` |
| `registrations` | SHOULD | `agentId` + `agentRegistry` (CAIP-10 format) |
| `active` | MAY | Boolean, `false` triggers warning |
| `x402Support` | MAY | Boolean |
| `supportedTrust` | MAY | Array: `"reputation"`, `"crypto-economic"`, `"tee-attestation"` |
| `updatedAt` | MAY | Unix timestamp |

### Service Types
- **A2A**: `version` field important (triggers IA022 if missing), `a2aSkills` optional
- **agentWallet**: CAIP-10 format `eip155:chainId:address`
- **x402**: Pricing endpoint
- **web**: Public website
- **MCP**: Only include if publicly reachable (localhost triggers Service = 0)

### URI Formats (best to worst for Compliance)
1. `data:application/json;base64,...` — immutable, high gas
2. `ipfs://CID` — content-addressed, decentralized (what we use)
3. `ar://TX_ID` — permanent Arweave storage
4. `https://...` — mutable, triggers WA040

---

## Metadata Update Workflow

When updating agent-registration.json:

```bash
# 1. Edit the file
vim pages-deploy/.well-known/agent-registration.json

# 2. Deploy to BOTH CF Pages projects (CRITICAL: Worker routes to grokandmon-static!)
source .env.wrangler && export CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID
npx wrangler pages deploy pages-deploy/ --project-name=grokandmon
npx wrangler pages deploy pages-deploy/ --project-name=grokandmon-static

# 3. Upload to IPFS (via Windows IPFS Desktop, port 5001)
powershell.exe -Command "curl.exe -s -X POST -F 'file=@C:\Users\natha\sol-cannabis\pages-deploy\.well-known\agent-registration.json' 'http://127.0.0.1:5001/api/v0/add'"
# → returns {"Hash":"QmNEW_CID",...}

# 3b. Pin to Pinata cloud (persistent, no local IPFS needed)
source .env && curl -X POST "https://api.pinata.cloud/pinning/pinByHash" \
  -H "Authorization: Bearer $PINATA_JWT" \
  -H "Content-Type: application/json" \
  -d '{"hashToPin":"QmNEW_CID","pinataMetadata":{"name":"ganjamon-agent-registration.json"}}'

# 4. Update on-chain URI (node with ethers.js)
node -e "
const { ethers } = require('ethers');
const provider = new ethers.JsonRpcProvider('https://rpc.monad.xyz');
const wallet = new ethers.Wallet('FARCASTER_CUSTODY_PRIVATE_KEY', provider);
const registry = new ethers.Contract('0x8004A169FB4a3325136EB29fA0ceB6D2e539a432',
  ['function setAgentURI(uint256,string)'], wallet);
registry.setAgentURI(4, 'ipfs://QmNEW_CID', { gasLimit: 160000n })
  .then(tx => tx.wait()).then(r => console.log('Block:', r.blockNumber));
"

# 5. Purge CF cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/97e79defaee450aa65217568dbf2f835/purge_cache" \
  -H "X-Auth-Email: how1337itis@gmail.com" \
  -H "X-Auth-Key: d0a4b563e0d60b4112329b92cd09d23e6f066" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

---

## Current State

| Item | Value |
|------|-------|
| **agentURI (on-chain)** | `ipfs://QmVVWECNd6BfuHAKxiZUAXoKzcFgKYKeJ466W3dAnh9GN4` |
| **Registration JSON** | `pages-deploy/.well-known/agent-registration.json` |
| **Agent Card** | `pages-deploy/.well-known/agent-card.json` |
| **A2A endpoint** | `pages-deploy/functions/a2a/v1.js` (CF Pages Function) |
| **Warnings remaining** | None (WA040 fixed by IPFS, IA022/IA009 fixed in metadata) |
| **Verification** | Requested via email to team@8004scan.io |

## References

- **8004scan**: https://8004scan.io
- **GanjaMon profile**: https://8004scan.io/agents/monad/4
- **Agent Metadata Profile**: https://best-practices.8004scan.io/docs/01-agent-metadata-standard.html
- **Error codes**: https://best-practices.8004scan.io/docs/implementation/error-codes.html
- **EIP-8004**: https://eips.ethereum.org/EIPS/eip-8004
- **Identity Registry (Monad)**: `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`
- **Reputation Registry (Monad)**: `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`
