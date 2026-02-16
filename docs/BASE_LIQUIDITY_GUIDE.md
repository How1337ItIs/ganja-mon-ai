# Base Liquidity Guide: $MON on Aerodrome

Quick reference for seeding **MON/USDC** liquidity on Base with your $250 USDC and bridged $MON.

---

## What You Have

| Asset | Where | Amount |
|-------|--------|--------|
| USDC | Base | $250 |
| MON | Base | 990 (from earlier bridge) |
| MON | Monad | Rest of supply (bridge more as needed) |

**Base MON contract:** `0x9e0753d8855dcc69F1BdFEfbAEf995e1aedBaD8e`

---

## How Much MON to Pair with $250 USDC?

Aerodrome uses **50/50 by value**: you add equal **dollar** amounts of each token.

- **USDC side:** $250 (you have this)
- **MON side:** $250 **worth** of MON

So you need **$250 worth of MON on Base**, not a fixed token count. That depends on MON’s price.

### Option A: Match Monad price (recommended)

Use MON’s effective price on Monad so Base isn’t an easy arb target.

1. Get current MON price on Monad:
   - **DexScreener:** https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b  
   - Or **LFJ Token Mill:** https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b  

2. Compute MON to bridge:
   - **MON amount ≈ 250 ÷ price_per_MON**
   - Example: if price = $0.0001, then 250 ÷ 0.0001 = **2,500,000 MON** to bridge and pair with $250 USDC.

Your **990 MON on Base** is only a few cents at Monad-level prices, so you **do need to bridge more MON** to pair with the full $250 USDC.

### Option B: Use only 990 MON (sets a high Base price)

If you add **990 MON + $250 USDC** and no more MON:

- Pool implies **250 ÷ 990 ≈ $0.253 per MON** on Base.
- That’s much higher than Monad; arbitrageurs could buy on Monad, sell on Base and drain MON from your pool.
- Only makes sense if you intentionally want a very high initial Base price and accept that risk.

**Recommendation:** Bridge enough MON so that `(MON on Base) × (Monad price) ≈ $250`, then add $250 USDC + that MON amount.

---

## How Much Liquidity Is This?

- **Total liquidity:** $250 + $250 = **$500** (your deposit is ~$500 TVL).
- Docs suggest 1–2% of FDV for a “basic” pool; at $39k FDV (yours) that’s $195–390 per side. Your $250 per side ≈ **1.3% of FDV** — in range and a reasonable start.

---

## How to Bridge MON (Monad → Base)

The bridge uses **Wormhole NTT**. Because Monad mainnet doesn't have the Wormhole Executor yet, you do **two steps**: (1) initiate on Monad, (2) after ~15–20 min, redeem on Base using the VAA. You need **Foundry** (`cast`) and MON + a little ETH on Monad, and a little ETH on Base for the redeem tx.

**Addresses (quick ref):**

| Role | Monad | Base |
|------|--------|------|
| MON Token | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` | `0x9e0753d8855dcc69F1BdFEfbAEf995e1aedBaD8e` |
| NTT Manager | `0x81D87a80B2121763e035d0539b8Ad39777258396` | `0x8a94b19C42A2A3D430d8dCBf0BEBa6eef17478a8` |
| Wormhole Transceiver | `0xc659d68acfd464cb2399a0e9b857f244422e809d` | `0x13CAb3351f894157AfFe6E2B97Bf224B59Df75BF` |

**Recipient:** Your Base wallet address as 32 bytes (left-padded). Example for `0xc48035f98B50aE26B2cA5368b6601940053D2b65`: `0x000000000000000000000000c48035f98b50ae26b2ca5368b6601940053d2b65`

### Step 1: Approve MON on Monad (one-time or per amount)

```bash
cast send 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b \
  "approve(address,uint256)" \
  0x81D87a80B2121763e035d0539b8Ad39777258396 \
  115792089237316195423570985008687907853269984665640564039457584007913129639935 \
  --private-key $PRIVATE_KEY \
  --rpc-url https://rpc3.monad.xyz
```

### Step 2: Get relay cost (quote)

```bash
cast call 0x81D87a80B2121763e035d0539b8Ad39777258396 \
  "quoteDeliveryPrice(uint16,bytes)(uint256[],uint256)" \
  30 0x010000 \
  --rpc-url https://rpc3.monad.xyz
```

Use the **total cost** (wei) as `--value` in Step 3. Base = chain ID **30**.

### Step 3: Initiate transfer on Monad

Amount in **wei** (18 decimals). Example: 1,000,000 MON = `1000000000000000000000000`.

```bash
cast send 0x81D87a80B2121763e035d0539b8Ad39777258396 \
  "transfer(uint256,uint16,bytes32,bytes32,bool,bytes)" \
  <AMOUNT_WEI> \
  30 \
  0x000000000000000000000000<YOUR_BASE_WALLET_NO_0x> \
  0x000000000000000000000000<YOUR_REFUND_ADDRESS_NO_0x> \
  false \
  0x010000 \
  --value <QUOTE_WEI> \
  --private-key $PRIVATE_KEY \
  --rpc-url https://rpc3.monad.xyz
```

Replace: `<AMOUNT_WEI>`, `<QUOTE_WEI>` (from Step 2), `<YOUR_BASE_WALLET_NO_0x>` (40 hex chars, lower case), `<YOUR_REFUND_ADDRESS_NO_0x>`. Save the **tx hash**.

### Step 4: Wait ~15–20 minutes

Guardians attest the message. Track the tx on [Wormholescan](https://wormholescan.io).

### Step 5: Get the VAA

- **Option A:** Open your Monad tx on [Wormholescan](https://wormholescan.io); copy the **VAA** (Signed VAA) from the message page.
- **Option B:** Get `sequence` from the transfer tx receipt, then:  
  `curl -s "https://api.wormholescan.io/api/v1/vaas/48/0x81D87a80B2121763e035d0539b8Ad39777258396/<SEQUENCE>"`  
  Use the hex VAA from the response. (Monad = 48; emitter = NTT Manager.)

### Step 6: Redeem on Base

```bash
cast send 0x13CAb3351f894157AfFe6E2B97Bf224B59Df75BF \
  "receiveMessage(bytes)" \
  <VAA_HEX> \
  --private-key $PRIVATE_KEY \
  --rpc-url https://mainnet.base.org
```

After confirm, MON appears on Base at `0x9e0753d8855dcc69F1BdFEfbAEf995e1aedBaD8e`.

**Web UI:** Open `src/web/bridge.html` in a browser (or serve the repo and go to `/src/web/bridge.html`) to approve, quote, initiate transfer, and redeem with VAA.

**More:** `ntt-deployment/mon-base-bridge/BRIDGE_SPECS.md`, `ntt-deployment/DEPLOYMENT_STATUS.md`.

---

## Step-by-Step: Add MON/USDC Liquidity on Aerodrome

1. **Get MON on Base**
   - Bridge MON from Monad to Base (see **How to Bridge MON (Monad to Base)** above) so you have **$250 worth** of MON on Base.

2. **Open Aerodrome**
   - Go to: **https://aerodrome.finance/liquidity**
   - Connect wallet (Base network).
   - Have some **ETH on Base** for gas (usually &lt;$0.10 per tx).

3. **Create pool or find existing**
   - Click **“New Deposit”** (or “Create Pool” if the pair doesn’t exist).
   - Choose **“Basic Volatile”** (standard AMM, 50/50).
   - **Token A:** paste MON: `0x9e0753d8855dcc69F1BdFEfbAEf995e1aedBaD8e`
   - **Token B:** USDC (pick Base USDC from the list, e.g. `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`).

4. **Enter amounts**
   - Enter **$250** equivalent in USDC.
   - Enter **$250** equivalent in MON (UI will show “equal value” or ratio; match it).
   - Approve both tokens, then confirm the deposit.

5. **Stake LP (optional)**
   - After depositing you get LP tokens. You can stake them in Aerodrome gauges to earn **AERO** if the pool is incentivized (whitelist may be required for new tokens).

---

## Checklist

- [ ] Current MON price on Monad (DexScreener or LFJ)
- [ ] MON to bridge = **250 ÷ price_per_MON**
- [ ] Bridge that amount Monad → Base (NTT)
- [ ] $250 USDC on Base
- [ ] Small ETH on Base for gas
- [ ] Aerodrome → Liquidity → New Deposit → Basic Volatile
- [ ] Pair: MON `0x9e07...aD8e` + USDC, $250 each side
- [ ] (Optional) Submit MON logo to [SmolDapp/tokenAssets](https://github.com/SmolDapp/tokenAssets) so the UI shows the icon

---

## Summary

- **Yes:** You need to **bridge more MON** to Base so you have **$250 worth** of MON to pair with your $250 USDC.
- **Amount to bridge:** `250 ÷ (MON price on Monad)`.
- **Where:** Aerodrome Finance → Liquidity → New Deposit → Basic Volatile → MON + USDC, equal $ value.
- **Total liquidity:** $500 ($250 + $250).
