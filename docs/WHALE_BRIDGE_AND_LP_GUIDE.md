# Hey Whale 🐋 — Bridge, Add Liquidity & Grow $MON on Base

Thanks for supporting $MON! This guide walks you through:

1. **Bridge** your $MON from Monad → Base
2. **Add liquidity** to the MON/USDC pool on Aerodrome
3. **Help get $MON visible** and working toward AERO emissions

---

## What You'll Need

| Item | Why |
|------|-----|
| **$MON on Monad** | What you're bridging to Base |
| **A small amount of native MON** | Gas for the bridge tx on Monad (~0.01 MON) |
| **ETH on Base** | Gas for Base transactions ($0.01–$0.10 each) |
| **USDC on Base** | To pair with $MON in the liquidity pool |
| **MetaMask or similar wallet** | Works on both Monad and Base |

---

## Step 1: Bridge $MON from Monad to Base

We have a bridge UI that handles everything through your browser wallet.

### 🌉 Bridge: [mon-bridge.pages.dev](https://mon-bridge.pages.dev)

1. Open the bridge and click **Connect Wallet** (top right)
2. Make sure the **"Monad → Base"** tab is selected (green border)
3. **Enter the amount** of MON you want to bridge
4. Click **Get Quote** to see the relay fee (paid in native MON, usually tiny)
5. Click **Approve MON** and confirm in your wallet
6. Click **Transfer to Base** and confirm
7. **Wait for the VAA** — the page auto-tracks it (usually seconds to a couple minutes)
8. Once the VAA is ready, click **Redeem on Base** — your wallet switches to Base automatically
9. Confirm the redeem transaction — your $MON appears on Base 🎉

### How much MON to bridge?

Aerodrome uses **50/50 by dollar value**, so you want equal $ amounts on each side:

```
MON to bridge = (your USDC amount) ÷ (MON price on Monad)
```

**Example:** $500 USDC and MON price is $0.00004 → bridge 12,500,000 MON

Check MON price:
- [DexScreener (Monad)](https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b)
- [LFJ Token Mill](https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b)

---

## Step 2: Add Liquidity on Aerodrome

Aerodrome is the biggest DEX on Base. We already have a MON/USDC pool (Basic Volatile, 0.3% fee).

### 💧 Direct deposit link:
**[Aerodrome → MON/USDC Deposit](https://aerodrome.finance/deposit?token0=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&token1=0xe390612d7997b538971457cff29ab4286ce97be2&type=-1&chain0=8453&chain1=8453)**

If that link doesn't work, do it manually:

1. Go to [aerodrome.finance/liquidity](https://aerodrome.finance/liquidity)
2. Connect your wallet (make sure you're on **Base**)
3. Click **"New Deposit"**
4. Select **"Basic Volatile"** pool type
5. For **Token A**, paste MON: `0xE390612D7997B538971457cfF29aB4286cE97BE2`
6. For **Token B**, select **USDC** (or paste: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`)
7. Enter your amounts — **equal $ value** on each side
8. **Approve** both tokens when prompted
9. Click **"Deposit"** and confirm

> **Note:** The pool currently shows MON as "undefined" on Aerodrome because our token logo isn't submitted yet. It's under "Unknown" pools — you may need to click **"Search unknown pools"** to find it. We're working on getting the logo added via [SmolDapp tokenAssets](https://github.com/SmolDapp/tokenAssets).

### Pool Info

| | Details |
|-|---------|
| **Pool Address** | [`0x2f2ec3e1b42756f949bd05f9b491c0b9c49fee3a`](https://basescan.org/address/0x2f2ec3e1b42756f949bd05f9b491c0b9c49fee3a) |
| **Type** | Basic Volatile (50/50 by value, 0.3% fee) |
| **Current TVL** | ~$267 (we're early!) |
| **Swap link** | [Buy MON on Aerodrome](https://aerodrome.finance/swap?from=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&to=0xE390612D7997B538971457cfF29aB4286cE97BE2) |

---

## Step 3: The Path to AERO Emissions

Here's the honest picture on how Aerodrome emissions work — it's not as simple as "create a gauge and vote." There's a process.

### How Aerodrome Works

Aerodrome has a **listing system** that determines whether a pool can receive AERO emissions:

- **Unlisted pools** (where we are now): Operate as **fee-only** pools. LPs earn 90% of trading fees directly. No AERO emissions, no staking, no gauge.
- **Listed pools**: Have a gauge, can be voted on by veAERO holders, LPs can stake to earn AERO emissions. This is where we want to be.

### What's Required for Listing?

Per [Aerodrome's Partner FAQs](https://aerodrome.notion.site/partner-faqs):

- **$500k daily average DEX volume** (30-day) or **$1M daily CEX volume**
- They also evaluate: product-market fit, tokenomics, distribution, security, traction
- You start the process by engaging directly with the Aerodrome team

We're not there yet on volume — but every bit of liquidity and trading activity gets us closer.

### What We Can Do Now

#### A. Use Aero Launch for Better Visibility

[Aero Launch](https://aerodrome.finance/launch) is Aerodrome's tool for token creators. Benefits:
- **"Emerging" tag** — increases visibility on the Aerodrome frontend so users can find and trade $MON by ticker
- **Integrated liquidity locker** — shows long-term commitment, builds trust
- Pools created through Launch are automatically optimized for future listing

#### B. Build Volume and Traction

The more trading volume the pool generates, the faster we qualify for listing:
- More liquidity = lower slippage = more traders
- Every swap generates fees that demonstrate real market activity
- This is the organic path to meeting listing requirements

#### C. Incentivize Liquidity Before Listing (Optional)

Even before listing, we can incentivize LPs through **third-party platforms**:
- **[Merkl](https://merkl.angle.money/)** — deposit token rewards for LPs
- **[Metrom](https://metrom.xyz/)** — similar incentive distribution

This lets us attract more LPs and TVL even without AERO emissions.

#### D. Engage the Aerodrome Team

Once we have traction, we reach out to the Aerodrome team directly to begin the listing process. Listed projects get:
- Gauge creation (staking + AERO emissions)
- Ability to deposit incentives natively on Aerodrome
- Marketing support (likes, comments, RTs, quote tweets)
- A 4-week grace period to establish liquidity before fee-based incentive limits apply

### After Listing (Future State)

Once listed, the full flywheel kicks in:

1. **veAERO holders vote** for the MON/USDC pool each weekly epoch (Thu→Wed UTC)
2. **AERO emissions** flow to staked LPs proportional to votes received
3. **We can deposit incentives** (bribes) on Aerodrome to attract more veAERO votes
4. Every $1 in voter incentives historically → **$1.50–$2.00 in AERO rewards** for LPs
5. LPs who **stake** their positions earn AERO instead of fees

---

## Quick Checklist

- [ ] Check MON price on Monad ([DexScreener](https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b))
- [ ] Calculate MON to bridge (USDC amount ÷ MON price)
- [ ] Bridge MON → Base at [mon-bridge.pages.dev](https://mon-bridge.pages.dev)
- [ ] Wait for VAA & redeem on Base
- [ ] Have USDC + ETH (for gas) on Base
- [ ] Add liquidity on [Aerodrome](https://aerodrome.finance/deposit?token0=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&token1=0xe390612d7997b538971457cff29ab4286ce97be2&type=-1&chain0=8453&chain1=8453)
- [ ] (Bonus) Trade some $MON to generate volume
- [ ] (Bonus) Tell frens about the pool

---

## Key Links

| Resource | Link |
|----------|------|
| **Bridge** | [mon-bridge.pages.dev](https://mon-bridge.pages.dev) |
| **Buy MON on Base** | [Aerodrome Swap](https://aerodrome.finance/swap?from=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&to=0xE390612D7997B538971457cfF29aB4286cE97BE2) |
| **Add Liquidity** | [Aerodrome Deposit](https://aerodrome.finance/deposit?token0=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&token1=0xe390612d7997b538971457cff29ab4286ce97be2&type=-1&chain0=8453&chain1=8453) |
| **Aero Launch** | [aerodrome.finance/launch](https://aerodrome.finance/launch) |
| **MON on DexScreener** | [Monad](https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b) |
| **Pool on BaseScan** | [0x2f2e...](https://basescan.org/address/0x2f2ec3e1b42756f949bd05f9b491c0b9c49fee3a) |
| **Website** | [grokandmon.com](https://grokandmon.com) |
| **Telegram** | [t.me/ganjamonai](https://t.me/ganjamonai) |
| **Twitter/X** | [@ganjamonai](https://x.com/ganjamonai) |

---

## Contract Addresses

| | Monad | Base |
|-|-------|------|
| **$MON Token** | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` | `0xE390612D7997B538971457cfF29aB4286cE97BE2` |
| **USDC** | — | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |

---

## Need Help?

Drop a message in [Telegram](https://t.me/ganjamonai) or reach out on [X (@ganjamonai)](https://x.com/ganjamonai). We appreciate the support immensely 🙏🌱

*Powered by Wormhole NTT • Aerodrome Finance • Base*
