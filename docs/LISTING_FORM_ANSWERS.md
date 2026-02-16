# CoinGecko Form - Technical Fields Answers

**Sections 3, 4, and 5: Exchange, Explorer, and Contract Information**

---

## 3. Exchange Trading Information

### ⚠️ IMPORTANT: Monad Exchange Challenge

**Problem:** LFJ Token Mill and most Monad DEXs are likely **not yet listed on CoinGecko** because Monad mainnet only launched in December 2025 (7 weeks ago).

### 🎯 RECOMMENDED APPROACH

**Option 1: Use DexScreener (Recommended)**
- DexScreener aggregates data from multiple chains including Monad
- CoinGecko accepts DexScreener as a valid source

```
Exchange Name: DexScreener

Exchange Trade URL: 
https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

**Option 2: Try LFJ Token Mill**
- Check if "LFJ" or "LFJ Token Mill" appears in CoinGecko's exchange dropdown
- If it does, use:

```
Exchange Name: LFJ Token Mill (or just "LFJ")

Exchange Trade URL:
https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

**Option 3: If Neither Works**
- You may need to wait for CoinGecko to add Monad exchanges
- Or submit with just DexScreener and note in "Additional Info" that native Monad DEXs are not yet on CoinGecko

### 📝 Additional Note to Include (if needed)

```
Note: $MON trades on LFJ Token Mill (Monad's primary DEX) and is tracked by DexScreener. 
As Monad mainnet only launched in December 2025, native Monad exchanges may not yet be 
in CoinGecko's database. We've provided the DexScreener analytics link as the primary 
trading reference. Contract: 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

---

## 4. Block Explorer Links

**Copy-Paste Ready:**

### Explorer Link (1) - PRIMARY
```
https://monadscan.com/token/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Explorer Link (2) - Contract Address View
```
https://monadscan.com/address/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Explorer Link (3) - SocialScan (Alternative Monad Explorer)
```
https://monad.socialscan.io/address/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Explorer Link (4) - Leave blank or use DexScreener
```
https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Explorer Link (5) - Leave blank
```
(leave empty)
```

---

## 5. Contract Information

### Blockchain Platform (1) *
```
Monad
```

**If "Monad" is not in the dropdown:**
- Try: "Other" or "EVM Compatible"
- Add note: "Monad (Chain ID 143) - EVM-compatible Layer 1"

### Contract Address (1) *
```
0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Contract Decimal Places (1) *
```
18
```

---

## 📋 Complete Copy-Paste Summary

### Section 3: Exchange Trading
```
Exchange Name: DexScreener
Exchange Trade URL: https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Section 4: Block Explorers
```
Explorer Link (1): https://monadscan.com/token/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
Explorer Link (2): https://monadscan.com/address/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
Explorer Link (3): https://monad.socialscan.io/address/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
Explorer Link (4): https://dexscreener.com/monad/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
Explorer Link (5): (leave blank)
```

### Section 5: Contract Information
```
Blockchain Platform: Monad (or "Other" if not listed)
Contract Address: 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
Contract Decimal Places: 18
```

---

## 🔍 How to Verify Decimal Places (if asked)

1. Go to MonadScan: https://monadscan.com/token/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
2. Look for "Decimals" field in token info
3. Should show: **18**

Or use this ethers.js/web3 call:
```javascript
const decimals = await contract.decimals(); // Returns 18
```

---

## ⚠️ Potential Issues & Solutions

### Issue 1: "Monad" not in blockchain dropdown
**Solution:** 
- Select "Other" or "EVM Compatible"
- Add note in "Additional Information": "Monad (Chain ID 143) - EVM-compatible Layer 1 blockchain"

### Issue 2: Exchange not found in dropdown
**Solution:**
- Use DexScreener (they aggregate Monad data)
- Add note: "Native Monad DEXs not yet on CoinGecko; using DexScreener aggregator"

### Issue 3: Form rejects Monad explorers
**Solution:**
- Emphasize DexScreener link (they recognize this)
- Note that Monad is a new chain (Dec 2025 launch)

---

## 📝 Additional Information Field (if available)

**Use this to explain Monad situation:**

```
$MON is deployed on Monad, an EVM-compatible Layer 1 blockchain that launched mainnet 
in December 2025. The token trades on LFJ Token Mill (Monad's primary DEX) and is tracked 
by DexScreener. As Monad is a new ecosystem, native exchanges may not yet be in CoinGecko's 
database. We've provided MonadScan (official Monad explorer) and DexScreener links for 
verification. Contract address: 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b (ERC-20 standard, 
18 decimals). All on-chain activity is verifiable via the provided explorer links.
```

---

## ✅ Pre-Submission Checklist

Before clicking submit, verify:

- [ ] Contract address is correct: `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`
- [ ] Decimals is 18 (standard ERC-20)
- [ ] MonadScan link works and shows token
- [ ] DexScreener link works and shows trading data
- [ ] If "Monad" not in dropdown, selected "Other" with explanation
- [ ] Exchange link points to actual trading pair (not just homepage)

---

## 🎯 FINAL RECOMMENDATION

**Best approach for smooth approval:**

1. **Exchange:** Use DexScreener (most likely to be recognized)
2. **Explorers:** MonadScan (primary) + SocialScan + DexScreener
3. **Blockchain:** Try "Monad" first, use "Other" if not available
4. **Add explanatory note** about Monad being a new chain

This gives CoinGecko multiple ways to verify your token while acknowledging the new ecosystem challenge.

---

**Last Updated:** January 30, 2026
