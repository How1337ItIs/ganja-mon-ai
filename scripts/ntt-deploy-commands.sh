#!/bin/bash
# =============================================================================
# $MON NTT Deployment Commands
# Monad → Solana via Wormhole NTT
# =============================================================================
#
# Run these commands in order. Fill in the [PLACEHOLDERS] as you go.
# Save outputs - you'll need addresses for later steps.
#
# =============================================================================

# -----------------------------------------------------------------------------
# PHASE 1: INSTALL DEPENDENCIES
# -----------------------------------------------------------------------------

# Install Bun
curl -fsSL https://bun.sh/install | bash

# Install NTT CLI
curl -fsSL https://raw.githubusercontent.com/wormhole-foundation/native-token-transfers/main/cli/install.sh | bash

# Verify NTT
ntt --version

# Install Solana CLI v1.18.26
sh -c "$(curl -sSfL https://release.solana.com/v1.18.26/install)"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
solana --version

# Install Anchor v0.29.0
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install 0.29.0
avm use 0.29.0
anchor --version

# Install SPL Token CLI
cargo install spl-token-cli
spl-token --version

# -----------------------------------------------------------------------------
# PHASE 2: WALLET SETUP
# -----------------------------------------------------------------------------

# Generate Solana keypair for operations
solana-keygen new --outfile ~/mon-ntt-keypair.json

# Configure Solana CLI
solana config set --keypair ~/mon-ntt-keypair.json
solana config set -um  # mainnet

# Check balance (need ~3 SOL)
solana balance

# Generate vanity keypair for NTT program
solana-keygen grind --starts-with ntt:1 --ignore-case
# SAVE THE OUTPUT PATH: [NTT_PROGRAM_KEYPAIR_PATH]

# Export Monad private key
export ETH_PRIVATE_KEY="[YOUR_MONAD_PRIVATE_KEY]"

# -----------------------------------------------------------------------------
# PHASE 3: CREATE SPL TOKEN ON SOLANA
# -----------------------------------------------------------------------------

# Create SPL token (this is $MON on Solana)
spl-token create-token
# SAVE THE OUTPUT: [MON_SOLANA_TOKEN_ADDRESS]

# Create token account
spl-token create-account [MON_SOLANA_TOKEN_ADDRESS]

# DO NOT MINT YET - NTT will control minting

# -----------------------------------------------------------------------------
# PHASE 4: INITIALIZE NTT PROJECT
# -----------------------------------------------------------------------------

# Create project
ntt new mon-ntt-bridge
cd mon-ntt-bridge

# Initialize for mainnet
ntt init Mainnet

# (Optional) Create overrides.json for custom RPCs
cat > overrides.json << 'EOF'
{
  "Monad": {
    "rpc": "https://monad-mainnet.blockvision.org/v1/[YOUR_API_KEY]"
  },
  "Solana": {
    "rpc": "https://mainnet.helius-rpc.com/?api-key=[YOUR_API_KEY]"
  }
}
EOF

# -----------------------------------------------------------------------------
# PHASE 5: DEPLOY NTT CONTRACTS
# -----------------------------------------------------------------------------

# Deploy to Monad (Hub - Locking mode)
# This locks $MON on Monad when bridging to Solana
ntt add-chain Monad --latest --mode locking --token 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b

# Deploy to Solana (Spoke - Burning mode)
# This mints $MON on Solana when receiving from Monad
ntt add-chain Solana --latest --mode burning \
  --token [MON_SOLANA_TOKEN_ADDRESS] \
  --payer ~/mon-ntt-keypair.json \
  --program-key [NTT_PROGRAM_KEYPAIR_PATH]

# Verify deployment
ntt status

# Sync local config
ntt pull

# -----------------------------------------------------------------------------
# PHASE 6: CONFIGURE RATE LIMITS
# -----------------------------------------------------------------------------

# Edit deployment.json to set rate limits
# Monad: 18 decimals, Solana: 9 decimals
# Example: 100M tokens per day limit

# Push configuration
ntt push --payer ~/mon-ntt-keypair.json

# -----------------------------------------------------------------------------
# PHASE 7: SET MINT AUTHORITY
# -----------------------------------------------------------------------------

# Transfer mint authority to NTT Manager
# Get NTT_MANAGER_ADDRESS from deployment.json
ntt set-mint-authority \
  --chain Solana \
  --token [MON_SOLANA_TOKEN_ADDRESS] \
  --manager [NTT_MANAGER_ADDRESS] \
  --payer ~/mon-ntt-keypair.json

# -----------------------------------------------------------------------------
# PHASE 8: VERIFY
# -----------------------------------------------------------------------------

# Check final status
ntt status

# Test balance
spl-token balance [MON_SOLANA_TOKEN_ADDRESS]

# -----------------------------------------------------------------------------
# KEY ADDRESSES TO SAVE
# -----------------------------------------------------------------------------

echo "
=== DEPLOYMENT COMPLETE ===

$MON Token (Monad): 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
$MON Token (Solana): [MON_SOLANA_TOKEN_ADDRESS]
NTT Manager (Monad): [FROM_DEPLOYMENT_JSON]
NTT Program (Solana): [NTT_PROGRAM_ADDRESS]

Next: Create Raydium pool at https://raydium.io/liquidity/create-pool/
"
