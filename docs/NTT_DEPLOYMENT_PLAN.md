# $MON NTT Deployment Plan: Monad → Solana

**Created:** January 29, 2026
**Status:** Ready to Deploy
**Estimated Time:** 2-4 hours
**Estimated Cost:** ~$100-200 gas + ~$2-3K liquidity

---

## Executive Summary

Deploy $MON (Ganja Mon) from Monad to Solana using Wormhole's Native Token Transfers (NTT) framework. This uses the same battle-tested infrastructure that powers native MON bridging.

**Architecture:** Hub-and-Spoke (Lock on Monad, Mint on Solana)
- Monad = Hub (tokens locked in NTT contract)
- Solana = Spoke (SPL tokens minted 1:1)

---

## Prerequisites Checklist

### Software Requirements

- [ ] **Node.js** v18+ installed
- [ ] **Bun** v1.2.23+ installed ([bun.sh](https://bun.sh))
- [ ] **Rust** installed ([rustup.rs](https://rustup.rs))
- [ ] **Solana CLI** v1.18.26 installed
- [ ] **Anchor** v0.29.0 installed
- [ ] **Foundry** (forge, cast) installed

### Wallets & Keys

- [ ] **Monad wallet** with:
  - Private key exported
  - ~0.5 MON for gas (Monad native token)
  - Access to $MON tokens to bridge

- [ ] **Solana wallet** with:
  - Keypair JSON file
  - ~2-3 SOL for deployment + pool creation

### API Keys (Optional but Recommended)

- [ ] **Monad RPC** (BlockVision or public)
- [ ] **Solana RPC** (Helius, Triton, or public)

---

## Chain & Contract Reference

### Wormhole Chain IDs

| Chain | Wormhole ID | CLI Name |
|-------|-------------|----------|
| Monad Mainnet | 48 | `Monad` |
| Solana Mainnet | 1 | `Solana` |

### Wormhole Contracts (Monad Mainnet)

| Contract | Address |
|----------|---------|
| Core Bridge | `0x194B123c5E96B9b2E49763619985790Dc241CAC0` |
| Token Bridge | `0x0B2719cdA2F10595369e6673ceA3Ee2EDFa13BA7` |
| Relayer | `0x27428DD2d3DD32A4D7f7C497eAaa23130d894911` |

### Wormhole Contracts (Solana Mainnet)

| Contract | Address |
|----------|---------|
| Core Bridge | `worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth` |
| Token Bridge | `wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb` |

### $MON Token (Monad)

| Parameter | Value |
|-----------|-------|
| Contract | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` |
| Decimals | 18 |
| Total Supply | 1,000,000,000 |

---

## Deployment Steps

### Phase 1: Environment Setup (~30 min)

#### 1.1 Install NTT CLI

```bash
# Install Bun if not already installed
curl -fsSL https://bun.sh/install | bash

# Install NTT CLI
curl -fsSL https://raw.githubusercontent.com/wormhole-foundation/native-token-transfers/main/cli/install.sh | bash

# Verify installation
ntt --version
```

#### 1.2 Install Solana CLI

```bash
# Install Solana CLI v1.18.26
sh -c "$(curl -sSfL https://release.solana.com/v1.18.26/install)"

# Add to PATH
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

# Verify
solana --version
```

#### 1.3 Install Anchor

```bash
# Install Anchor v0.29.0
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install 0.29.0
avm use 0.29.0

# Verify
anchor --version
```

#### 1.4 Install SPL Token CLI

```bash
cargo install spl-token-cli

# Verify
spl-token --version
```

### Phase 2: Wallet Setup (~15 min)

#### 2.1 Configure Solana Wallet

```bash
# Generate new keypair for operations (or use existing)
solana-keygen new --outfile ~/mon-ntt-keypair.json

# Configure CLI to use this keypair
solana config set --keypair ~/mon-ntt-keypair.json

# Set to mainnet
solana config set -um

# Check balance (need ~2-3 SOL)
solana balance
```

#### 2.2 Generate NTT Program Keypair

```bash
# Generate keypair for NTT program (vanity address starting with "ntt")
solana-keygen grind --starts-with ntt:1 --ignore-case

# Save the output path - you'll need it for deployment
# Example output: nttXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.json
```

#### 2.3 Export Monad Private Key

```bash
# Set environment variable with your Monad private key
export ETH_PRIVATE_KEY="your_monad_private_key_here"
```

### Phase 3: Create SPL Token on Solana (~20 min)

#### 3.1 Create the $MON SPL Token

```bash
# Create new SPL token (this is your $MON on Solana)
spl-token create-token

# Save the token mint address! Example output:
# Creating token XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# This is your $MON_SOLANA_ADDRESS
```

#### 3.2 Create Token Account

```bash
# Create associated token account
spl-token create-account $MON_SOLANA_ADDRESS
```

**IMPORTANT:** Don't mint any tokens yet. The NTT program will control minting.

### Phase 4: Initialize NTT Project (~15 min)

#### 4.1 Create NTT Project

```bash
# Create new NTT project
ntt new mon-ntt-bridge
cd mon-ntt-bridge

# Initialize for mainnet
ntt init Mainnet
```

#### 4.2 Create overrides.json (for RPC endpoints)

```bash
cat > overrides.json << 'EOF'
{
  "Monad": {
    "rpc": "https://monad-mainnet.blockvision.org/v1/YOUR_API_KEY"
  },
  "Solana": {
    "rpc": "https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY"
  }
}
EOF
```

*Note: Replace with your actual RPC endpoints. Public RPCs work but may be slower.*

### Phase 5: Deploy NTT Contracts (~45 min)

#### 5.1 Add Monad Chain (Hub - Locking Mode)

```bash
# Deploy NTT Manager on Monad
# Mode: locking (tokens are locked on Monad, not burned)
ntt add-chain Monad --latest --mode locking --token 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

**Expected output:** NTT Manager contract deployed on Monad

#### 5.2 Add Solana Chain (Spoke - Burning Mode)

```bash
# Deploy NTT on Solana
# Mode: burning (tokens can be burned to release on Monad)
ntt add-chain Solana --latest --mode burning \
  --token $MON_SOLANA_ADDRESS \
  --payer ~/mon-ntt-keypair.json \
  --program-key ./nttXXXX.json
```

*Replace `$MON_SOLANA_ADDRESS` with SPL token from Phase 3*
*Replace `./nttXXXX.json` with keypair from Phase 2.2*

#### 5.3 Verify Deployment

```bash
# Check deployment status
ntt status

# Sync local config with on-chain state
ntt pull
```

### Phase 6: Configure Rate Limits (~10 min)

#### 6.1 Edit deployment.json

Open `deployment.json` and configure rate limits:

```json
{
  "network": "Mainnet",
  "chains": {
    "Monad": {
      "token": "0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b",
      "mode": "locking",
      "limits": {
        "outbound": "100000000.000000000000000000",
        "inbound": {
          "Solana": "100000000.000000000"
        }
      }
    },
    "Solana": {
      "token": "YOUR_SPL_TOKEN_ADDRESS",
      "mode": "burning",
      "limits": {
        "outbound": "100000000.000000000",
        "inbound": {
          "Monad": "100000000.000000000000000000"
        }
      }
    }
  }
}
```

**Rate limit notes:**
- Monad uses 18 decimals
- Solana uses 9 decimals (SPL standard)
- 100M tokens = reasonable daily limit
- Adjust based on expected volume

#### 6.2 Push Configuration

```bash
# Push rate limits to contracts
ntt push --payer ~/mon-ntt-keypair.json
```

### Phase 7: Set Mint Authority on Solana (~5 min)

The NTT program needs authority to mint $MON on Solana.

```bash
# Set mint authority to NTT Manager PDA
ntt set-mint-authority \
  --chain Solana \
  --token $MON_SOLANA_ADDRESS \
  --manager $NTT_MANAGER_ADDRESS \
  --payer ~/mon-ntt-keypair.json
```

*Get `$NTT_MANAGER_ADDRESS` from `deployment.json` after Phase 5*

### Phase 8: Test Bridge (~15 min)

#### 8.1 Small Test Transfer

```bash
# Bridge a small amount (1000 $MON) to verify everything works
# This will lock tokens on Monad and mint on Solana
```

**Manual test via Wormhole Connect or custom UI needed**

#### 8.2 Verify on Solana

```bash
# Check your SPL token balance
spl-token balance $MON_SOLANA_ADDRESS
```

---

## Phase 9: Create Liquidity Pool (~30 min)

### 9.1 Bridge Tokens for LP

Bridge enough $MON to Solana for liquidity pool:
- Recommended: $1.5K worth of $MON
- Plus buffer for trading

### 9.2 Create Raydium CPMM Pool

1. Visit [Raydium Create Pool](https://raydium.io/liquidity/create-pool/)
2. Select "CPMM" (Standard AMM)
3. Configure:
   - Token A: $MON (your SPL token address)
   - Token B: SOL
   - Initial price: Match Monad price
   - Deposit: ~$1.5K $MON + ~$1.5K SOL

**Pool creation cost:** ~0.3 SOL

### 9.3 Verify Pool

- Pool should appear on Raydium
- Test with small swap
- Share pool address with community

---

## Deployment Checklist

### Pre-Deployment
- [ ] All software installed and verified
- [ ] Monad wallet funded (~0.5 MON)
- [ ] Solana wallet funded (~3 SOL)
- [ ] Private keys exported securely
- [ ] RPC endpoints configured (optional)

### Deployment
- [ ] NTT project initialized
- [ ] SPL token created on Solana
- [ ] Monad chain added (locking mode)
- [ ] Solana chain added (burning mode)
- [ ] Rate limits configured
- [ ] Mint authority transferred
- [ ] Test transfer successful

### Post-Deployment
- [ ] Liquidity pool created on Raydium
- [ ] Pool tested with small swap
- [ ] Contract addresses documented
- [ ] Community announcement prepared

---

## Contract Addresses (Fill After Deployment)

| Chain | Contract | Address |
|-------|----------|---------|
| Monad | $MON Token | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` |
| Monad | NTT Manager | `[FILL AFTER DEPLOY]` |
| Solana | $MON SPL Token | `[FILL AFTER DEPLOY]` |
| Solana | NTT Program | `[FILL AFTER DEPLOY]` |
| Solana | Raydium Pool | `[FILL AFTER DEPLOY]` |

---

## Troubleshooting

### "Rate limit exceeded"
- Increase limits in deployment.json
- Run `ntt push` to update

### "Insufficient funds"
- Monad: Need native MON for gas
- Solana: Need SOL for rent + gas

### "Program deployment failed"
- Check Solana CLI version (must be v1.18.26)
- Check Anchor version (must be v0.29.0)
- Use staked RPC for reliability

### "Token not found"
- Verify token address is correct
- Ensure you're on mainnet, not testnet

---

## Cost Breakdown

| Item | Estimated Cost |
|------|----------------|
| NTT deployment (Monad) | ~0.1-0.3 MON (~$2-6) |
| NTT deployment (Solana) | ~0.5-1 SOL (~$50-100) |
| SPL token creation | ~0.002 SOL (~$0.20) |
| Raydium pool creation | ~0.3 SOL (~$30) |
| **Subtotal (infrastructure)** | **~$80-140** |
| Seed liquidity | $2,000-3,000 |
| **Total** | **~$2,100-3,200** |

---

## Post-Deployment Marketing

### Announcement Template

```
$MON is now LIVE on Solana!

The first AI-grown cannabis token is going multichain.

How to buy:
1. Bridge: [wormhole link]
2. Swap: [raydium link]

Contract: [solana address]

Watch Mon grow: https://grokandmon.com
```

### Action Items
1. Update website with Solana info
2. Add Solana contract to DexScreener
3. Tweet announcement as Rasta
4. Pin in Telegram
5. Consider launch stream

---

## References

- [Wormhole NTT Docs](https://wormhole.com/docs/products/token-transfers/native-token-transfers/overview)
- [NTT Solana Deployment](https://wormhole.com/docs/products/token-transfers/native-token-transfers/guides/deploy-to-solana/)
- [NTT EVM Deployment](https://wormhole.com/docs/products/token-transfers/native-token-transfers/guides/deploy-to-evm/)
- [Raydium Create Pool](https://raydium.io/liquidity/create-pool/)
- [Monad NTT Blog Post](https://wormhole.com/blog/mon-the-native-token-of-monad-goes-multichain-with-wormhole-ntt)
