# MegaETH NFT Mint + Revenue Splits — Plan for Creators

A step-by-step plan for running an NFT mint on **MegaETH** and splitting ETH revenue automatically using **Splits** (0xSplits). Use this as a checklist and reference; adjust percentages and tooling to your project.

---

## 1. Overview

**Goal:** Mint NFTs on MegaETH and send all primary (and optionally secondary) revenue to a **Split** contract so it’s distributed by percentage to multiple addresses — no manual payouts.

**Flow:**
1. Deploy **Splits** on MegaETH (fork 0xSplits; they don’t support MegaETH out of the box).
2. Create **one Split** with your recipients and percentages (e.g. creator 70%, collaborator 20%, treasury 10%).
3. Deploy your **NFT contract** with the Split’s address as the **mint payout recipient** (and optionally as the **EIP-2981 royalty** recipient).
4. Mint revenue goes to the Split; someone calls `distributeETH`; recipients withdraw their share.

**Why Splits:** Audited, no protocol fee (only gas), same pattern used by Zora and others for NFT revenue. Splits don’t support fee-on-transfer, rebasing, or non-transferable tokens — **ETH and standard ERC20 only**.

**MegaETH:** EVM-compatible. Mainnet **Chain ID 4326**; Testnet **6342**. RPC (testnet): `https://carrot.megaeth.com/rpc`. Use **Mega CLI** or **Foundry** for deployment.

---

## 2. Splits: Fork and Deploy on MegaETH

Splits is not deployed on MegaETH by default, so you deploy it yourself by forking the official contracts.

### 2.1 Fork the repo

- **Repo:** [github.com/0xSplits/splits-contracts](https://github.com/0xSplits/splits-contracts)
- Fork (or clone) and add MegaETH to the project’s network config (Foundry `foundry.toml` or deploy scripts).
- **Docs:** [docs.splits.org/core](https://docs.splits.org/core) — Split (V1), [SplitV2](https://docs.splits.org/core/split-v2) if you want push/pull options.

### 2.2 Add MegaETH to deployment config

In your fork, add a network entry for MegaETH, for example:

- **Mainnet:** Chain ID `4326`, RPC from [MegaETH docs](https://docs.megaeth.com/) (e.g. [megaeth.com](https://megaeth.com)).
- **Testnet:** Chain ID `6342`, RPC `https://carrot.megaeth.com/rpc`.

Use the same format as existing chains in the repo (e.g. in `script/` or `deploy/` and Foundry config).

### 2.3 Deploy core contract(s)

- Deploy **SplitMain** (and any dependencies their deploy script uses) to **MegaETH testnet** first.
- Use **Mega CLI** from your project root:
  - `npm install -g megaeth-cli`
  - `mega setup` (Foundry)
  - `mega account create` (or use `--private-key` for CI)
  - `mega deploy <path>:SplitMain --testnet --broadcast --account <name>`
- Or use Foundry’s `forge script` / `forge create` with MegaETH RPC and chain ID.
- **Verify** the contract on the chain’s block explorer (e.g. MegaETH Blockscout) so others can read it.

### 2.4 Create your Split

- Use **SplitMain** to create a **Split**: pass recipient addresses and **ownership percentages** (must sum to 100%).
- Each Split gets its **own payable address** (proxy). Save this address — this is the **mint payout address** for your NFT.
- **Immutable vs controller:** Immutable = no one can change recipients (simplest, most trustless). Controller = one address can change the Split; use a **multisig** if you need flexibility.
- Keep recipient count reasonable; Splits docs note ~2000 recipients per Split as a practical limit.

### 2.5 Distribute and withdraw

- ETH (and ERC20s) sent to the Split sit there until **distribution** is triggered.
- Someone must call `distributeETH` (and/or `distributeERC20`) on the Split; then each recipient can **withdraw** their share.
- You can run this manually, or automate with a small keeper/bot; document who is responsible.

---

## 3. NFT Contract and Integration

### 3.1 Mint payout address = Split address

- Your **NFT mint contract** should send primary sale proceeds (ETH) to a **single payout address**.
- Set that payout address to the **Split contract address** you created in §2.4.
- All mint revenue then goes into the Split and is split by your configured percentages.

### 3.2 Royalties (EIP-2981)

- Implement **EIP-2981** (`royaltyInfo(tokenId, salePrice)`) so marketplaces can pay royalties on secondary sales.
- Set the **royalty recipient** to the same Split address (or a second Split if you want different percentages for secondary).
- One recipient per `royaltyInfo` is fine — that recipient is the Split, which then distributes to multiple parties.

### 3.3 NFT best practices (summary)

- **Before deploy:** Collection name, symbol, and max supply are usually **immutable**; double-check them.
- **Mint price and limits:** Set public mint price and max mints per wallet; test on testnet.
- **Media:** Use standard formats (e.g. PNG/WEBP, 1024×1024, &lt;300KB for images) for broad compatibility.
- **Secrets:** Never commit API keys or private keys; use env vars and secure key management.

---

## 4. MegaETH Deployment (NFT + tooling)

### 4.1 Use Mega CLI (recommended for MegaETH)

- **Quickstart:** [mega-cli.mintlify.app/quickstart](https://mega-cli.mintlify.app/quickstart)
- **Commands:** [mega-cli.mintlify.app/commands/deploy](https://mega-cli.mintlify.app/commands/deploy)
- Init: `mega init my-nft-project` (or `--foundry` for contracts only).
- Compile: `mega compile`.
- Deploy: `mega deploy <contract-path>:<ContractName> --testnet --broadcast --account <account>` (then repeat for mainnet with mainnet RPC/chain ID when ready).

### 4.2 Deployment order

1. Deploy **SplitMain** (and deps) on MegaETH testnet.
2. **Create your Split** via SplitMain; record the Split address.
3. Deploy **NFT contract** with Split address as payout (and optionally royalty recipient).
4. Test: mint → check Split balance → call `distributeETH` → withdraw as each recipient.
5. When satisfied, repeat on **MegaETH mainnet** (Chain ID 4326).

### 4.3 Verification and faucet

- **Verify** contracts on the chain explorer after deploy (Mega CLI: `--verify` if supported, or use explorer’s “Verify” flow).
- Testnet ETH: use `mega faucet --account <account>` (see [Mega CLI docs](https://mega-cli.mintlify.app/commands/faucet)).

---

## 5. Security and Best Practices

### 5.1 Splits

- **Controller:** Prefer **immutable** Split, or a **multisig** as controller — avoid a single EOA with power to change recipients.
- **Token compatibility:** Only ETH and standard ERC20. No fee-on-transfer, rebasing, or non-transferable tokens.
- **Tests:** Run 0xSplits’ existing test suite against a MegaETH fork or testnet to catch chain-specific issues (gas, opcodes).

### 5.2 Transparency

- Publish **split percentages and recipient addresses** (e.g. in a one-pager or project docs). Clear allocation avoids the kind of backlash seen in opaque “community vs public” distributions (e.g. some MegaETH ICO feedback).

### 5.3 Access and keys

- Use a **multisig or secure EOA** for deployer and any privileged roles.
- Keep **private keys and API keys** in env vars or a secrets manager; never in repo or client-side code.

---

## 6. Launch Checklist

**Pre-launch**

- [ ] Split created on MegaETH (testnet then mainnet) and address saved.
- [ ] NFT contract deployed with **payout address = Split address**.
- [ ] EIP-2981 implemented with **royalty recipient = Split** (or second Split), if desired.
- [ ] Mint price, supply, and per-wallet limits set and verified.
- [ ] Contracts verified on block explorer.
- [ ] Frontend / mint site points to correct contract and **MegaETH chain (4326)**.
- [ ] One-pager or doc with split % and recipient addresses (recommended).

**Post-mint**

- [ ] Document who triggers **distributeETH** (and how often) so recipients can withdraw.
- [ ] Optional: automate distribution (keeper/bot) or set a simple schedule.

**Optional**

- [ ] Publish allocation breakdown (e.g. “70% creator, 20% collaborator, 10% treasury”) and recipient addresses for transparency.

---

## Quick reference

| Item | Value |
|------|--------|
| MegaETH mainnet Chain ID | 4326 |
| MegaETH testnet Chain ID | 6342 |
| MegaETH testnet RPC | https://carrot.megaeth.com/rpc |
| Splits contracts | [github.com/0xSplits/splits-contracts](https://github.com/0xSplits/splits-contracts) |
| Splits docs | [docs.splits.org](https://docs.splits.org) |
| Create a Split (existing chains) | [app.splits.org/new/split](https://app.splits.org/new/split/) |
| Mega CLI docs | [mega-cli.mintlify.app](https://mega-cli.mintlify.app) |

---

*Plan written for sharing with a creator running an NFT mint on MegaETH and using on-chain revenue splits. Based on 0xSplits docs, Mega CLI docs, and common NFT/smart-contract best practices.*
