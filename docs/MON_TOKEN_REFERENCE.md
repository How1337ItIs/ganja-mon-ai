# $MON Token Reference Sheet

**Last Updated:** January 29, 2026

Quick reference for all $MON (Ganja Mon) token details, addresses, and key metrics.

---

## Core Token Details

| Parameter | Value |
|-----------|-------|
| **Name** | Ganja Mon |
| **Symbol** | $MON |
| **Chain** | Monad (Chain ID 143) |
| **Token Standard** | ERC-20 |
| **Total Supply** | 1,000,000,000 (1B) |
| **Decimals** | 18 |
| **Launch Date** | ~January 20, 2026 |
| **Launch Platform** | LFJ Token Mill |

---

## Contract Addresses

### $MON Token (Primary - Use for Bridges)
```
0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Token Mill Market (Bonding Curve)
```
0xfB72c999dcf2BE21C5503c7e282300e28972AB1B
```
*Note: This is the AMM market contract where $MON trades vs WMON. NOT used for bridging.*

### LFJ Token Mill Factory (Monad Mainnet)
```
0xe70d21aD211DB6DCD3f54B9804A1b64BB21b17B1
```
*Source: [LFJ Deployment Addresses](https://developers.lfj.gg/deployment-addresses/monad-mainnet)*

---

## Current Metrics (Late Jan 2026)

| Metric | Value | Notes |
|--------|-------|-------|
| **Market Cap** | ~$55K | Micro-cap |
| **Holders** | ~97 | Organic, real users |
| **24h Volume** | ~$2-3K | Low; Monad "trenches" quiet |
| **Age** | ~9 days | Since Jan 20, 2026 |

---

## Trading Locations

### Current (Monad Only)
- **LFJ Token Mill**: https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
- **LFJ v1 DEX Pool** (traderjoe): Secondary liquidity
- **DexScreener**: https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b

### Planned (Cross-Chain)
- **Base**: Via LayerZero OFT or Wormhole NTT (researching)
- **Solana**: Via Wormhole NTT (proven path - native MON uses this)

---

## Community & Socials

| Platform | Handle/Link | Size |
|----------|-------------|------|
| **Website** | https://grokandmon.com | - |
| **Twitter/X** | @ganjamonai | ~39 followers |
| **Telegram** | [link] | 100+ members (CT OGs) |

---

## Token Mill Specifics

### How LFJ Token Mill Works
- Tokens are **standard ERC-20s** created by the factory
- Bonding curve is a **separate market contract** (reserves, swap logic)
- **No graduation** - the curve is perpetual (unlike pump.fun)
- LFJ does **NOT** provide a bridge - bridging is DIY via LayerZero/Wormhole

### KOTM (King of the Mill)
- Competition based on **bonding curve volume** (not v1 DEX volume)
- Epochs run **1-2 weeks** (not 4 hours as docs say - confirmed by LFJ team)
- Winner gets prize pool

### KOTM History (Jan 22-29, 2026 Epoch)
$MON lost to BOOLY despite organic superiority:

| Metric | $MON | BOOLY | Winner |
|--------|------|-------|--------|
| Market Cap | $55K | $4.5K | $MON (12x) |
| Holders | 97 | 15-19 | $MON (6.5x) |
| Transfers | 1,643 | 263 | $MON (6.2x) |
| Twitter Followers | 39 | 6 | $MON |
| Telegram | 100+ | None | $MON |

**What Happened:** BOOLY wash-traded 901M tokens in final 27 minutes via single wallet.

---

## Bridging Research Summary

### Recommended Approach
1. **Solana FIRST** (different audience, memecoin culture)
2. Use **Wormhole NTT** (already proven for Monad→Solana)
3. Seed **$2-3K liquidity** on Raydium CPMM
4. Base as Phase 2 if Solana works

### Bridge Technology Options

| Technology | Monad→Solana | Monad→Base | Notes |
|------------|--------------|------------|-------|
| **Wormhole NTT** | Proven (native MON uses it) | Supported | Recommended |
| **LayerZero OFT** | Supported | Supported | One stack for all |

### Liquidity Requirements (Micro-Cap Reality)

| Liquidity | Slippage | Practical? |
|-----------|----------|------------|
| $1K-$2K | 10-30% | Yes - functional |
| $3K-$5K | 3-10% | Yes - reasonable UX |
| $25K+ | <2% | No - half the mcap! |

### DEX Options

**Solana:**
- Raydium CPMM (~0.3 SOL to create)
- Orca Whirlpools (concentrated liquidity)

**Base:**
- Aerodrome (dominant, veAERO tokenomics)
- Uniswap V3

---

## Key Files & Documentation

| File | Purpose |
|------|---------|
| `docs/COINGECKO_COINMARKETCAP_APPLICATIONS.md` | CoinGecko & CMC listing applications (pre-filled $MON data) |
| `docs/research/BRIDGE_MON_TO_BASE_OR_SOLANA.md` | Full bridging research |
| `docs/LFJ_TOKEN_MILL_VOLUME_REPORT.md` | KOTM forensic analysis |
| `HOW_TO_BUY_MON.md` | User guide for buying $MON |
| `src/web/swap.html` | Swap interface code |
| `src/telegram/personality.py` | Bot with token details |

---

## API Endpoints

### DexScreener
```bash
curl "https://api.dexscreener.com/latest/dex/tokens/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b"
```

### BlockVision (Token Trades)
```bash
curl -H "x-api-key: YOUR_KEY" \
  "https://api.blockvision.org/v2/monad/token/trades?tokenAddress=0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b&limit=10"
```

### LFJ Token Mill Factory (Get Market)
```javascript
// Get market address for any token
const market = await factory.getMarketOf("0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b");
```

---

## Quick Links

- **Trade $MON**: https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
- **DexScreener**: https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
- **LFJ Docs**: https://docs.tokenmill.xyz/
- **Monad Docs**: https://docs.monad.xyz/
- **Wormhole NTT**: https://wormhole.com/docs/products/token-transfers/native-token-transfers/overview
- **LayerZero OFT**: https://docs.layerzero.network/v2/developers/evm/oft/quickstart

---

## Token Verification Checklist

Before bridging, verify $MON is a plain ERC-20:
- [ ] No fee-on-transfer
- [ ] No transfer hooks
- [ ] No blacklist functionality
- [ ] Standard `transfer()` returns bool
- [ ] No rebasing mechanics

*Token Mill tokens should be standard ERC-20, but always verify.*
