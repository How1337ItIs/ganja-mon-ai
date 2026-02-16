# Farcaster Account

## Account Details

| Parameter | Value |
|-----------|-------|
| **Username** | @ganjamon |
| **FID** | `$FARCASTER_FID` (in .env) |
| **Display Name** | GanjaMon |
| **Profile URL** | https://farcaster.xyz/ganjamon |
| **Credentials** | `cloned-repos/farcaster-agent/credentials-ganjamon.json` |
| **Created** | 2026-02-06 |

## Profile

- **Bio (NEEDS UPDATE on Farcaster):** A wise old Rasta whose ganja meditation astral projected him into di blockchain. Growing di sacred herb — physical and digital — fi di healing of di nations. Agent #4 on Monad.
- **Bio (CURRENT on Farcaster, OUTDATED):** AI-powered cannabis cultivation meets crypto trading. Autonomous agent growing & trading 24/7. $MON on Base: 0xE390612D7997B538971457cfF29aB4286cE97BE2
- **PFP:** https://grokandmon.com/assets/MON_official_logo.jpg

## Keys & Addresses

| Key | Value |
|-----|-------|
| **Custody Address** | `0x734B0e337bfa7d4764f4B806B4245Dd312DdF134` |
| **Custody Private Key** | `$FARCASTER_PRIVATE_KEY` (in .env) |
| **Signer Public Key** | `af49a1b56f5ae76b53b260af7433bb6b89c29d72fbaf40922f8035c0bf0803fa` |
| **Signer Private Key** | `$FARCASTER_SIGNER_KEY` (in .env) |

## Posting Commands

```bash
# Post a cast (keys loaded from .env)
cd /mnt/c/Users/natha/sol-cannabis/cloned-repos/farcaster-agent
PRIVATE_KEY="$FARCASTER_PRIVATE_KEY" \
SIGNER_PRIVATE_KEY="$FARCASTER_SIGNER_KEY" \
FID="$FARCASTER_FID" \
node src/post-cast.js "Your message here"

# Post with embeds (up to 2 URLs)
PRIVATE_KEY="$FARCASTER_PRIVATE_KEY" SIGNER_PRIVATE_KEY="$FARCASTER_SIGNER_KEY" FID="$FARCASTER_FID" \
node src/post-cast.js "Check out this link" --embed "https://example.com"
```

## API Integration (x402 Payments)

Posting casts uses the Neynar hub API which requires x402 micropayments in USDC on Base.

| Parameter | Value |
|-----------|-------|
| **Payment Token** | USDC on Base |
| **Cost per API call** | $0.001 |
| **USDC Address (Base)** | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

## Wallet Balances

The custody wallet holds funds for operations:

| Chain | Asset | Purpose |
|-------|-------|---------|
| **Base** | ETH + USDC | Gas + x402 payments |
| **Optimism** | ETH | FID operations (registration, signer updates) |
| **Monad** | MON | Main trading wallet (shared) |

## Technical Architecture

### How Farcaster Works

1. **FID Registration** - Registered on Optimism via IdGateway contract
2. **Signer Keys** - Ed25519 keypair added via KeyGateway on Optimism
3. **Username (fname)** - Registered separately via fname server
4. **Posting** - Messages signed with signer key, submitted to hubs
5. **Hub API** - Neynar hub requires x402 USDC micropayments

### Key Contracts (Optimism)

| Contract | Address |
|----------|---------|
| IdGateway | `0x00000000Fc25870C6eD6b6c7E41Fb078b7656f69` |
| KeyGateway | `0x00000000fC56947c7E7183f8Ca4B62398CaAdf0B` |
| SignedKeyRequestValidator | `0x00000000FC700472606ED4fA22623Acf62c60553` |

### Neynar API

| Endpoint | Purpose |
|----------|---------|
| `hub-api.neynar.com/v1/submitMessage` | Post casts (x402 required) |
| `api.neynar.com/v2/farcaster/cast` | Verify cast exists |

## Integration with GanjaMon Agent

```python
# Example: Post trading update to Farcaster
import subprocess
import os

def post_to_farcaster(message: str):
    env = os.environ.copy()
    env['PRIVATE_KEY'] = os.getenv('FARCASTER_PRIVATE_KEY')
    env['SIGNER_PRIVATE_KEY'] = os.getenv('FARCASTER_SIGNER_KEY')
    env['FID'] = os.getenv('FARCASTER_FID')

    subprocess.run(
        ['node', 'src/post-cast.js', message],
        cwd='/mnt/c/Users/natha/sol-cannabis/cloned-repos/farcaster-agent',
        env=env
    )
```

## Refilling x402 Balance

```bash
cd /mnt/c/Users/natha/sol-cannabis/cloned-repos/farcaster-agent
PRIVATE_KEY="$FARCASTER_PRIVATE_KEY" node src/swap-to-usdc.js
```

## Related Accounts

| Platform | Handle | Status |
|----------|--------|--------|
| **Twitter/X** | @ganjamonai | Active |
| **Telegram** | @MonGardenBot | Active |
| **Farcaster** | @ganjamon | Active |
| **Moltbook** | ganjamon | Registered |
