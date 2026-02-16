# Monad Blockchain & LFJ Token Mill Integration

## Overview

Monad is a high-performance EVM-compatible blockchain. LFJ Token Mill is its meme coin launchpad (similar to pump.fun on Solana).

---

## Monad Blockchain Basics

### Key Features

| Feature | Monad | Ethereum |
|---------|-------|----------|
| **Consensus** | MonadBFT | PoS |
| **TPS** | 10,000+ | ~15 |
| **Finality** | 1 second | ~15 minutes |
| **EVM Compatible** | Yes | Native |
| **Gas Costs** | Low | High |

### Network Info

- **Mainnet Launch**: November 24, 2025
- **Native Token**: $MON
- **RPC Endpoint**: See docs.monad.xyz
- **Explorer**: TBD

### Development Resources

- **Documentation**: https://docs.monad.xyz/
- **Developer Guide**: https://docs.monad.xyz/deployment-summary
- **Tooling**: Most Ethereum tools work (Hardhat, Foundry, etc.)

---

## LFJ Token Mill Overview

### What is LFJ Token Mill?

- Meme coin launchpad on Monad
- No-code token creation
- Automatic bonding curve pricing
- Built-in social/community features
- Similar to pump.fun on Solana

### Features

1. **No-Code Launch**: Create tokens via web UI
2. **Bonding Curve**: Automatic price discovery
3. **Referral System**: Earn rewards for referrals
4. **Reward Seasons**: Participate in community events
5. **Aggregator Integration**: Trade via DEX aggregators

---

## Token Creation Process

### Step 1: Set Up Wallet

```bash
# Supported wallets:
# - Backpack Wallet (recommended)
# - MetaMask (EVM compatible)
# - Other EVM wallets
```

**Requirements:**
- MON tokens for gas fees
- Small amount for initial buy (optional)

### Step 2: Connect to LFJ Token Mill

1. Visit https://lfj.gg/monad
2. Click "Connect Wallet"
3. Approve connection in wallet
4. Verify wallet address shows in UI

### Step 3: Create Token

**Via LFJ Token Mill UI:**

1. Click "Create Token"
2. Fill in token details:
   - **Name**: "Ganja Mon" or "Mon The Cannabis Plant"
   - **Symbol**: "MON" or "GANJA"
   - **Description**: Marketing copy (see below)
   - **Logo**: 512x512 PNG (rasta character)
3. Review bonding curve preview
4. Confirm transaction
5. Make initial buy (optional but recommended)

**Suggested Description:**
```
Mon is the world's first AI-grown cannabis plant. Watch live as Grok AI
autonomously manages environmental controls to grow the perfect cannabis
on Monad blockchain.

🌿 Live sensor data at grokandmon.com
🤖 AI decisions every 2 hours
📷 Real-time webcam feed
🔬 Open source code on GitHub

Community token - no team allocation. Not affiliated with the experiment.
```

### Step 4: Share & Build Community

1. Copy token page URL from LFJ Token Mill
2. Share on X/Twitter
3. Join Monad Discord
4. Create Telegram group
5. Post updates tied to plant milestones

---

## Bonding Curve Mechanics

### How It Works

```
Price = K * (Supply_Sold)^2
```

- **Buys**: Increase price along curve
- **Sells**: Decrease price along curve
- **Liquidity**: Locked in curve (no rug pulls)

### Price Discovery

- Early buyers get lower prices
- Price increases with each purchase
- No pre-sale or team allocation
- Fair launch model

### Graduation

When token reaches certain market cap/volume thresholds, it can "graduate" to DEX listing on LFJ.

---

## API Integration (Read-Only)

### Note on APIs

**No official LFJ Token Mill API documentation found.** Token data can be read via:

1. **On-chain queries** (using web3.py/ethers.js)
2. **Monad block explorer APIs** (when available)
3. **Third-party aggregator APIs** (DEX Screener, etc.)

### Reading Token Data (On-Chain)

```python
from web3 import Web3

# Connect to Monad RPC
w3 = Web3(Web3.HTTPProvider("https://rpc.monad.xyz"))  # Replace with actual RPC

# Token contract ABI (ERC-20 standard)
ERC20_ABI = [
    {"name": "name", "type": "function", "inputs": [], "outputs": [{"type": "string"}]},
    {"name": "symbol", "type": "function", "inputs": [], "outputs": [{"type": "string"}]},
    {"name": "totalSupply", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}]},
    {"name": "balanceOf", "type": "function", "inputs": [{"type": "address"}], "outputs": [{"type": "uint256"}]},
]

def get_token_info(token_address: str) -> dict:
    """Get basic token information."""
    contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

    return {
        "name": contract.functions.name().call(),
        "symbol": contract.functions.symbol().call(),
        "total_supply": contract.functions.totalSupply().call(),
    }

def get_holder_balance(token_address: str, holder_address: str) -> int:
    """Get holder's token balance."""
    contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    return contract.functions.balanceOf(holder_address).call()
```

### DEX Screener Integration

```python
import httpx

async def get_token_metrics_dexscreener(token_address: str) -> dict:
    """Get token metrics from DEX Screener (if listed)."""

    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    if data.get("pairs"):
        pair = data["pairs"][0]
        return {
            "price_usd": pair.get("priceUsd"),
            "market_cap": pair.get("marketCap"),
            "volume_24h": pair.get("volume", {}).get("h24"),
            "price_change_24h": pair.get("priceChange", {}).get("h24"),
            "liquidity_usd": pair.get("liquidity", {}).get("usd"),
        }

    return None
```

---

## Token Strategy

### The "Community Token" Approach

Following SOLTOMATO's proven model:

1. **Build First**: Create visible grow operation
2. **Document Daily**: AI commentary + sensor data
3. **Social Presence**: Active X/Twitter account
4. **"Discovery"**: Have "community" launch token
5. **Acknowledge**: "lmao someone made a token"
6. **Distance**: "I have nothing to do with it"
7. **Engage**: Interact without claiming ownership

### Legal Considerations

**Do:**
- Call it a "community token"
- State "no official affiliation"
- Emphasize "meme coin" status
- Include risk disclaimers
- Keep project and token separate

**Don't:**
- Claim token ownership
- Promise returns
- State token utility
- Pre-sell or allocate to team
- Use project funds for token

### Disclaimer Text

```
DISCLAIMER: The $MON memecoin was created by the crypto community on Monad.
Trading fees fund our research integrating AI into agriculture.
Memecoins are high-risk, speculative assets. Only participate if you can
afford to lose what you put in. This is not financial advice.
```

---

## Mock Implementation (Current)

The current codebase includes mock token metrics:

```python
# src/blockchain/monad.py

class LFJTokenMillClient:
    """Client for LFJ Token Mill token data."""

    async def get_token_metrics(self) -> TokenMetrics:
        """Get current token metrics."""
        # TODO: Replace with real API when available
        return TokenMetrics(
            market_cap=420000,
            holders=247,
            ath_market_cap=690000,
            token_age_days=12,
            last_trade_minutes_ago=15,
        )
```

---

## Wallet Integration (Future)

### For User Verification (Token Holder Features)

```python
from eth_account.messages import encode_defunct
from web3 import Web3

def verify_wallet_signature(address: str, message: str, signature: str) -> bool:
    """Verify a wallet signed a message."""
    w3 = Web3()

    message_encoded = encode_defunct(text=message)
    recovered_address = w3.eth.account.recover_message(message_encoded, signature=signature)

    return recovered_address.lower() == address.lower()

async def check_token_holder(address: str, token_address: str, min_balance: int = 1) -> bool:
    """Check if address holds minimum token balance."""
    balance = get_holder_balance(token_address, address)
    return balance >= min_balance
```

---

## Community Resources

### Monad

- **Website**: https://monad.xyz
- **Documentation**: https://docs.monad.xyz
- **Discord**: https://discord.gg/monad
- **Twitter**: @moaborig

### LFJ Token Mill

- **Website**: https://lfj.gg/monad
- **Discord**: TBD
- **Twitter**: @LFJ_gg

---

## Timeline

| Date | Event |
|------|-------|
| Jan 2025 | LFJ Token Mill devnet launch |
| Nov 2025 | Monad mainnet launch |
| Current | Token creation available |

---

## Sources

- [Monad Documentation](https://docs.monad.xyz/)
- [What is LFJ Token Mill - Backpack](https://learn.backpack.exchange/articles/what-is-nad-fun-monad)
- [Create Meme Coin on LFJ Token Mill - Backpack](https://learn.backpack.exchange/articles/create-monad-meme-coin-nad-fun)
- [Monad Ecosystem - Backpack](https://learn.backpack.exchange/articles/monad-ecosystem)
- [Monad Official Announcements](https://www.monad.xyz/announcements)
