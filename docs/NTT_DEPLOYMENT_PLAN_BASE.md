# $MON NTT Deployment Plan: Monad → Base

**Created:** January 29, 2026
**Status:** Ready to Deploy
**Estimated Time:** 1-2 hours
**Estimated Cost:** ~$30-140 (no liquidity)

---

## Why Base is Simpler

- Both chains are EVM (same tooling)
- No Rust/Anchor/SPL needed
- Base gas is extremely cheap (L2)
- LayerZero OFT is also an option (but sticking with NTT for consistency)

---

## Chain Reference

| Chain | Wormhole ID | CLI Name | Type |
|-------|-------------|----------|------|
| Monad | 48 | `Monad` | EVM |
| Base | 30184 | `Base` | EVM |

---

## Prerequisites

### Software (EVM only - much simpler!)

- [ ] **Node.js** v18+
- [ ] **Bun** v1.2.23+
- [ ] **Foundry** (forge, cast)
- [ ] **NTT CLI**

### Wallets

- [ ] **Monad wallet** with ~0.5 MON for gas
- [ ] **Base wallet** with ~0.01-0.05 ETH for gas
- [ ] Same private key works for both (EVM)

---

## Deployment Steps

### Phase 1: Install Dependencies (~10 min)

```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc

# Install NTT CLI
curl -fsSL https://raw.githubusercontent.com/wormhole-foundation/native-token-transfers/main/cli/install.sh | bash

# Verify
ntt --version

# Install Foundry (for contract interaction)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Verify
forge --version
cast --version
```

### Phase 2: Deploy Token on Base (~15 min)

You need an ERC-20 $MON token on Base. Two options:

**Option A: Deploy New Token (Recommended)**

```bash
# Clone example token
git clone https://github.com/wormhole-foundation/example-ntt-token-evm.git
cd example-ntt-token-evm

# Deploy to Base
forge create --broadcast \
  --rpc-url https://mainnet.base.org \
  --private-key $ETH_PRIVATE_KEY \
  src/PeerToken.sol:PeerToken \
  --constructor-args "Ganja Mon" "MON" $YOUR_ADDRESS $YOUR_ADDRESS
```

**Option B: Use Existing Mintable ERC-20**

If you already have a mintable ERC-20 on Base, use that address.

**Save the token address:** `[MON_BASE_ADDRESS]`

### Phase 3: Initialize NTT Project (~5 min)

```bash
# Create project
ntt new mon-base-bridge
cd mon-base-bridge

# Initialize for mainnet
ntt init Mainnet
```

### Phase 4: Deploy NTT (~30 min)

```bash
# Export private key
export ETH_PRIVATE_KEY="your_private_key_here"

# Deploy to Monad (Hub - Locking)
ntt add-chain Monad --latest --mode locking \
  --token 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b

# Deploy to Base (Spoke - Burning)
ntt add-chain Base --latest --mode burning \
  --token [MON_BASE_ADDRESS]

# Verify
ntt status
```

### Phase 5: Configure Rate Limits (~5 min)

Edit `deployment.json`:

```json
{
  "network": "Mainnet",
  "chains": {
    "Monad": {
      "limits": {
        "outbound": "100000000.000000000000000000",
        "inbound": {
          "Base": "100000000.000000000000000000"
        }
      }
    },
    "Base": {
      "limits": {
        "outbound": "100000000.000000000000000000",
        "inbound": {
          "Monad": "100000000.000000000000000000"
        }
      }
    }
  }
}
```

Push config:
```bash
ntt push
```

### Phase 6: Set Mint Authority on Base (~5 min)

```bash
# Get NTT Manager address from deployment.json
# Set it as minter on your Base token

cast send [MON_BASE_ADDRESS] \
  "setMinter(address)" [NTT_MANAGER_ADDRESS] \
  --private-key $ETH_PRIVATE_KEY \
  --rpc-url https://mainnet.base.org
```

### Phase 7: Test Bridge (~10 min)

Bridge a small amount (1000 $MON) from Monad to Base to verify.

---

## Cost Breakdown (No Liquidity)

| Item | Chain | Cost |
|------|-------|------|
| Token deployment | Base | ~$5-20 |
| NTT Manager deployment | Monad | ~$2-6 |
| NTT Manager deployment | Base | ~$5-25 |
| Rate limit config | Both | ~$1-5 |
| Set minter | Base | ~$0.50 |
| **Total** | | **~$15-60** |

*Actual costs depend on gas prices. Base is very cheap.*

---

## Wormhole Contract Addresses

### Monad Mainnet
| Contract | Address |
|----------|---------|
| Core Bridge | `0x194B123c5E96B9b2E49763619985790Dc241CAC0` |
| Relayer | `0x27428DD2d3DD32A4D7f7C497eAaa23130d894911` |

### Base Mainnet
| Contract | Address |
|----------|---------|
| Core Bridge | `0xbebdb6C8ddC678FfA9f8748f85C815C556Dd8ac6` |
| Relayer | `0x706F82e9bb5b0813501714Ab5974216704980e31` |

---

## After Deployment

1. Create Aerodrome pool: https://aerodrome.finance/liquidity
2. Seed with $MON/ETH or $MON/USDC
3. Announce to community

---

## Quick Commands Reference

```bash
# Check deployment status
ntt status

# Sync with on-chain
ntt pull

# Push config changes
ntt push
```
