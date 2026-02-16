# ERC-8004 on Monad — Research Note

**Date:** 2026-02-04 (updated after official deployment)  
**Context:** GanjaMon agent uses ERC-8004 registration; $MON and ops are on Monad. This doc summarizes 8004 support on Monad.

---

## Summary

- **ERC-8004** is a **chain-agnostic** standard: Identity, Reputation, and Validation registries are **per-chain singletons** on any EVM chain (EIP-155, 712, 721, 1271).
- **Monad mainnet (chainId 143)** has **official ERC-8004 deployments** from the [erc-8004-contracts](https://github.com/erc-8004/erc-8004-contracts) repo (same deterministic addresses as Ethereum, Base, Polygon, Scroll, BSC).
- **Official Monad mainnet addresses:**
  - **IdentityRegistry:** `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` — [monadscan.com](https://monadscan.com/address/0x8004A169FB4a3325136EB29fA0ceB6D2e539a432)
  - **ReputationRegistry:** `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` — [monadscan.com](https://monadscan.com/address/0x8004BAa17C55a88189AE136b182e5fdA19dE9b63)
- **Your setup:** Use the official registry in `agent-registration.json`: `eip155:143:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`. GanjaMon is registered on-chain with `agentId: 4` and this value is set in the `registrations` entry.

---

## What ERC-8004 Is (Brief)

| Registry        | Role |
|----------------|------|
| **Identity**   | ERC-721 + URIStorage; mints `agentId`, `tokenURI` → registration JSON (A2A/MCP endpoints, wallets, etc.). |
| **Reputation** | Clients submit feedback (score, tags, optional URI + hash); optional x402 payment proofs in off-chain payloads. |
| **Validation** | Request/response log for validators (stake, zkML, TEE); attestations stored on-chain. |

Payments are out of scope; x402 proofs can be referenced in reputation data.  
Spec: [EIP-8004](https://eips.ethereum.org/EIPS/eip-8004).  
Polygon (reference): [ERC-8004 on Polygon](https://docs.polygon.technology/payment-services/agentic-payments/agent-integration/erc8004) (Amoy addresses + mainnet “coming soon”).

---

## Monad vs Other Chains

| Chain   | ChainId | ERC-8004 status |
|--------|---------|------------------|
| Ethereum mainnet | 1 | Identity + Reputation (official). |
| Base, Polygon, Scroll, BSC mainnet | various | Same Identity/Reputation addresses as Ethereum. |
| **Monad mainnet** | **143** | **Official.** Identity `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`, Reputation `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`. |
| Monad testnet | — | Identity/Reputation at testnet addresses (see [erc-8004-contracts README](https://github.com/erc-8004/erc-8004-contracts)). |
| Polygon Amoy | 80002 | Testnet addresses (doc’d). |

Monad mainnet: RPC `https://rpc.monad.xyz`, explorers: [monadscan.com](https://monadscan.com), [monadvision.com](https://monadvision.com).

---

## Implications for GanjaMon

1. **Discovery on Monad**  
   Use the **official** Identity Registry on Monad: `eip155:143:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`. GanjaMon is registered with `agentId: 4`.

2. **Reputation on Monad**  
   The official Reputation Registry is deployed at `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63`. Clients can submit feedback for your agentId once registered.

3. **Validation registry**  
   Per the [erc-8004-contracts README](https://github.com/erc-8004/erc-8004-contracts), the Validation Registry spec is still under update; mainnet deployment table lists only Identity + Reputation.

4. **Multi-chain**  
   You can add more entries to `registrations[]` (e.g. Ethereum, Base) if you register on those chains too; same deterministic addresses apply.

**Next step:** Verify `ownerOf(4)` on the IdentityRegistry matches the operator wallet and keep `src/web/.well-known/agent-registration.json` aligned with the on-chain agent URI.

---

## References

- [EIP-8004: Trustless Agents](https://eips.ethereum.org/EIPS/eip-8004)
- [erc-8004-contracts README](https://github.com/erc-8004/erc-8004-contracts) — **canonical deployment table including Monad mainnet**
- [8004.org Build](https://www.8004.org/build) — supported chains (Monad listed as “coming soon” on site; contracts README has Monad mainnet live)
- [ERC-8004 on Polygon](https://docs.polygon.technology/payment-services/agentic-payments/agent-integration/erc8004)
- Monad: chainId 143, [Add Monad to wallet](https://docs.monad.xyz/guides/add-monad-to-wallet/mainnet), RPC `https://rpc.monad.xyz`, [MonadScan](https://monadscan.com)
- Local: `src/web/.well-known/agent-registration.json`, `src/api/app.py` (mounts `/.well-known`)
