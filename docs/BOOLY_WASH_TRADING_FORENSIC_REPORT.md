# BOOLY Wash Trading Forensic Report

**Date:** January 29, 2026
**Subject:** LFJ Token Mill KOTM Competition Manipulation
**Tokens:** $MON (Ganja Mon) vs $BOOLY
**Chain:** Monad Mainnet
**Evidence Source:** MonadVision Explorer, on-chain transaction data

---

## Executive Summary

**VERDICT: BOOLY won KOTM through blatant wash trading by a single wallet.**

A forensic blockchain analysis reveals:
1. **Single wallet** (`0xef2e...E8C0`) executed ALL of BOOLY's winning volume
2. **50+ BOOLY transactions** with matching buy/sell amounts (textbook wash trading)
3. **901.9 million BOOLY** tokens churned back and forth through the bonding curve
4. MON's legitimate launch volume was **erased by LFJ's epoch reset** on Jan 22

---

## Key Evidence

### The Wash Trader (Verified on MonadVision Explorer)

| Attribute | Value |
|-----------|-------|
| **Wallet Address** | `0xef2ea7e0ea32db5950831c01ebb94b2f2d62e8c0` |
| **Account Age** | **17 days** (verified on MonadVision) |
| **Current Portfolio** | **$0.67** (6.67 MON + 27.2 WMON) |
| **Total Token Transfers** | **258 transactions** |
| **BOOLY Market Interactions** | 50+ buy/sell pairs |
| **Buy/Sell Balance** | **100%** (perfect wash trade signature) |
| **Explorer Link** | [MonadVision](https://monadvision.com/address/0xef2ea7e0ea32db5950831c01ebb94b2f2d62e8c0) |

### Wash Trading Pattern (From Explorer Token Transfers)

Verified on MonadVision - exact same amounts bought and sold within minutes:

| Time (UTC) | Direction | Amount | Market |
|------------|-----------|--------|--------|
| 8 hrs 8 mins ago | BUY | **13,358,447** BOOLY | 0x4AAC...0D2f → Wash Trader |
| 8 hrs 7 mins ago | SELL | **13,358,447** BOOLY | Wash Trader → 0x4AAC...0D2f |
| 8 hrs 8 mins ago | BUY | **13,396,564** BOOLY | 0x4AAC...0D2f → Wash Trader |
| 8 hrs 6 mins ago | SELL | **13,396,564** BOOLY | Wash Trader → 0x4AAC...0D2f |
| 8 hrs 8 mins ago | BUY | **14,213,063** BOOLY | 0x4AAC...0D2f → Wash Trader |
| 8 hrs 8 mins ago | SELL | **14,213,063** BOOLY | Wash Trader → 0x4AAC...0D2f |
| ... | ... | ... | ... |

**Pattern:** Same exact amounts being bought and sold immediately - this is **textbook wash trading**.

### Contract Addresses (Verified on LFJ Trade Page)

| Token | Address | Market (Bonding Curve) | Status |
|-------|---------|------------------------|--------|
| **MON** | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` | `0xfB72c999dcf2BE21C5503c7e282300e28972AB1B` | ✅ Active, 97 holders |
| **BOOLY** | `0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d` | `0x4aac8f86203adc88d127ccca44f97c76b7cb0d2f` | Wash traded |

### MON Token Stats (from LFJ)
- **Market Cap:** $55.38k
- **Price:** $0.0₄55378
- **Liquidity:** $8.05k
- **Holders:** 97
- **Pool Created:** January 21, 2026, 2:20:17 PM UTC

---

## Timeline of Events

| Date/Time (UTC) | Event |
|-----------------|-------|
| **Jan 21, 2026 14:20:17** | MON Token Mill pool created (verified on LFJ) |
| **Jan 21-22** | MON generates substantial launch volume (erased by reset) |
| **Jan 22, 2026** | **LFJ resets KOTM epoch** (confirmed in Telegram by Unsehrtain) |
| **Jan 22-29** | New epoch runs; MON trades on both Token Mill and v1 pool |
| **Jan 29, ~11:27 UTC** | BOOLY wash trading begins (block 51875216) |
| **Jan 29, ~12:00 UTC** | Epoch ends; BOOLY crowned "King of the Mill" |
| **Jan 29, ~12:01 UTC** | New epoch starts; LONG becomes KOTM with just $56 volume |

---

## The Epoch Reset Problem

LFJ team admitted to resetting the epoch on **January 22, 2026**:

> **Unsehrtain | LFJ:** "Yes" (in response to "did y'all reset the epoch counter?")
>
> **Unsehrtain | LFJ:** "We were waiting for some key integrations to complete aka the birdeye and one other..."

This reset:
1. **Erased MON's launch volume** (first 2 days of high activity)
2. Was done **without notifying MON** before their launch
3. Reset the leaderboard, allowing BOOLY to start fresh

---

## The Volume Routing Flaw

### MON Trading Activity (DexScreener)
- **v1 Pool:** `0xcA4ab8Db4052541731Adcb6E383BAF5A731A2FfE`
- **24h Volume:** $2,907
- **24h Transactions:** 475 (268 buys, 207 sells)
- **Status:** Active, organic trading

### Why This Matters
KOTM only counts **Token Mill bonding curve volume**, NOT v1 pool volume.

MON's organic trading gets routed to v1 for better price execution (LFJ's aggregator), but this volume **doesn't count** for KOTM. Meanwhile, BOOLY forces all trades through the bonding curve, making wash trading more effective for gaming the competition.

---

## Comparative Analysis

### Final 33 Minutes of Epoch

| Metric | MON | BOOLY |
|--------|-----|-------|
| **Token Mill Txs** | 1 | **50** |
| **Token Mill Volume** | 871,382 | **901,906,827** |
| **Unique Wallets** | 1 | **1** |
| **Volume Ratio** | 1x | **1,035x** |
| **Trading Pattern** | Organic | **Wash Trading** |

### Full Picture

| Metric | MON | BOOLY |
|--------|-----|-------|
| **v1 Pool Volume** | $2,907 (24h) | $0 |
| **v1 Pool Txs** | 475 (24h) | 0 |
| **Has DexScreener Pair** | Yes | No |
| **Community Activity** | Active | Dormant until snipe |

---

## Systemic Issues Identified

### 1. Epoch Reset Without Notice
LFJ reset the epoch mid-competition without notifying active participants, erasing legitimate early volume.

### 2. Volume Routing Disadvantages Legitimate Tokens
LFJ's aggregator routes trades to v1 pools for better execution, but only bonding curve volume counts for KOTM. This penalizes tokens with real trading activity.

### 3. No Wash Trading Detection
A single wallet generated 901M tokens of volume with perfect buy/sell balance in 33 minutes. This obvious manipulation went undetected and won the competition.

### 4. Manipulation Incentive Structure
KOTM rewards raw volume, incentivizing wash trading over genuine community building. A bot can snipe the prize from active communities using minimal capital.

---

## Recommendations

### For LFJ
1. **Implement wash trading detection** (flag single-wallet volume, perfect buy/sell ratios)
2. **Count aggregated volume** across v1 pools AND bonding curve
3. **Don't reset epochs mid-competition** without clear notice to all participants
4. **Disqualify BOOLY** and award KOTM to legitimate runner-up

### For $MON Community
1. Document and publicize this manipulation
2. Request LFJ investigate the wash trading wallet
3. Consider requesting KOTM reversal based on evidence
4. Monitor future epochs for similar manipulation

---

## Technical Appendix

### Verification Commands

```bash
# Scan BOOLY wash trading window
python3 scripts/calc_volume_final.py

# Key blocks
# Epoch end: 51879038 (Jan 29, 12:00 UTC)
# Wash trading start: 51875216 (~11:27 UTC)
# Wash trading end: 51877454 (~11:55 UTC)
```

### RPC Query for Wash Trades

```python
# Query BOOLY transfers in final 33 minutes
BOOLY_TOKEN = "0x0cbb6a9ea443791e3a59eda62c4e540f2278b61d"
START_BLOCK = 51875038
END_BLOCK = 51879038
# Filter for BOOLY_MARKET involvement
# Result: 50 transfers, 1 unique wallet
```

---

## Conclusion

**BOOLY's KOTM victory is illegitimate.**

A single wallet wash-traded 901 million BOOLY tokens in the final 33 minutes of the epoch, generating 1,035x more "volume" than MON while MON's community engaged in genuine trading on v1 pools.

The combination of:
- Epoch reset erasing MON's launch volume
- Volume routing that doesn't count legitimate v1 activity
- Zero wash trading detection

Created a system where manipulation beats organic community activity.

**MON is the moral winner of this epoch.**

---

*Report generated by forensic blockchain analysis on January 29, 2026*
*Wash trader wallet: `0xef2ea7e0ea32db5950831c01ebb94b2f2d62e8c0`*
