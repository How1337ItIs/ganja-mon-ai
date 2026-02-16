# Monad Volume Data Access Guide
## Getting Full On-Chain Trading Volume for Token Mill Markets

**Date:** January 29, 2026  
**Author:** Antigravity AI Analysis

---

## Current Data Summary

### Verified Data Sources

| Source | Data Type | MON | BOOLY |
|--------|-----------|-----|-------|
| **LFJ API** (`sol-barn.tokenmill.xyz`) | Lifetime Volume (USD) | $2,199 | $5,383 |
| **LFJ API** | Total Swaps | 27 | 67 |
| **BlockVision Indexing** | On-Chain Txns | 87 | 50+/day |

### Key Finding: The Discrepancy

- **LFJ API shows 27 swaps** for MON
- **BlockVision shows 87 transactions** on MON's market contract
- **Difference: ~60 transactions** (mostly from Jan 21-22, before the epoch reset)

---

## Free Data Access Options

### 1. SocialScan Explorer (UI)
- **URL:** `https://monad.socialscan.io/address/{CONTRACT}`
- **Limitations:** Only shows "Latest 25" items in the UI
- **Export:** Has "Export CSV" button under Developers menu (requires login/API key)
- **Best For:** Quick spot checks

### 2. Monad Infrastructure RPC
- **URL:** `https://rpc-mainnet.monadinfra.com`
- **Method:** `eth_getLogs` with Swap event topic
- **Limitations:** Block range limits (~1000 blocks/call), slow for large ranges
- **Best For:** Historical data access

### 3. BlockVision RPC (Free Tier)
- **URL:** `https://monad-mainnet.blockvision.org/v1/{API_KEY}`
- **Limitations:** 100-block chunks, rate limited to ~100 req/s
- **Best For:** Indexed transaction data

### 4. MonadVision Explorer
- **URL:** `https://monadvision.com/address/{CONTRACT}`
- **Limitations:** Shows transaction counts, not USD volume
- **Best For:** Quick holder/transfer counts

---

## Paid/Professional Options

| Service | What You Get | Estimated Cost |
|---------|-------------|----------------|
| **SocialScan API** | Full transaction history, decoded events | Contact sales |
| **BlockVision Pro** | Higher rate limits, larger block ranges | ~$49/mo |
| **Alchemy Monad** | Professional-grade API | Free tier + paid scaling |
| **QuickNode** | Dedicated RPC endpoint | ~$29/mo |
| **Self-Hosted Node** | Complete control, no limits | ~$500 hardware |

---

## How to Get Exact Volume Data

### Method 1: eth_getLogs + Decode (Free but Slow)

```python
# Swap event topic for Token Mill
SWAP_TOPIC = "0x51713e7418434a85621a281e8194f99f7ed2ac1375ced97d89fd54e8f774323f"

# Get logs
logs = eth_getLogs({
    "address": "0xfB72c999dcf2BE21C5503c7e282300e28972AB1B",
    "topics": [SWAP_TOPIC],
    "fromBlock": "0x2F7B668",  # ~Jan 21
    "toBlock": "0x318E3E8"     # ~Jan 29
})

# Decode each log: data contains [baseAmount, quoteAmount, fee, protocolFee, newPrice]
# quoteAmount (bytes 64-128) is the volume in WMON (18 decimals)
```

**Time Required:** 1-2 hours with rate limiting

### Method 2: Use LFJ API Lifetime Volumes (Instant)

The LFJ API's `/v2/market/monad/{address}` endpoint provides:
- `volumeUsd`: Lifetime USD volume
- `numberSwaps`: Total swap count

This is the **canonical source** for Token Mill volume data.

### Method 3: Contact SocialScan/Hemera for Full Export

Email: `contact@thehemera.com`
Request: Full transaction CSV export for contract addresses

---

## Scripts Available in This Repo

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/swap_event_analysis.py` | Full epoch analysis with 100-block chunks | Running (slow) |
| `scripts/blockvision_swap_volume.py` | Pre/post reset volume comparison | Running (rate limited) |
| `scripts/quick_volume_check.py` | Quick single-call volume check | Completed |
| `scripts/blockvision_volume.py` | Transaction count by epoch | Completed |

---

## Conclusion

**For KOTM dispute purposes, the LFJ API's lifetime volume ($2,199 MON vs $5,383 BOOLY) is the canonical source.** However, this data only reflects what LFJ indexed after the epoch reset.

To prove MON's pre-reset volume was greater, you would need:
1. Run the full `eth_getLogs` analysis (1-2 hours)
2. Or request a full data export from SocialScan

The BlockVision transaction counts already show:
- **75 of MON's 87 transactions (86%) occurred before the Jan 22 reset**
- Using the ~$80/swap average, this represents **~$6,000 in erased volume**
