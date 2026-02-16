# CoinGecko Form - Supply & Tokenomics Sections (6-11)

**Sections 6-11: Complete Answers for $MON Token**

---

## 6. Coin Holders & Distribution Schedule

### Top Holder List URL
```
https://monadscan.com/token/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b#balances
```

**Alternative (if MonadScan doesn't have #balances view):**
```
https://monadscan.com/token/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
```

### Distribution Schedule
```
https://grokandmon.com
```

**Or create a dedicated tokenomics page and use:**
```
https://grokandmon.com/tokenomics
```

**Or use your GitHub (if public):**
```
https://github.com/[your-username]/sol-cannabis/blob/main/docs/MON_TOKEN_REFERENCE.md
```

**Note to add in "Additional Supply Information" field:**
```
$MON was launched via LFJ Token Mill fair launch bonding curve on January 20, 2026. 
No presale, no team allocation, no vesting schedules. 100% of supply was made available 
through the public bonding curve. All tokenomics information is available at 
grokandmon.com and verifiable on-chain via MonadScan.
```

---

## 7. Coin/Token Supply Information

### Token Generation Date (TGE)
```
01/20/2026
```

### Max Supply Amount
```
1000000000
```
(1 billion - do NOT use commas, just the number)

### Is Infinite Supply
```
☐ Unchecked
```
(Leave unchecked - max supply is fixed at 1B)

---

## 8. Total Supply

### Total Supply Amount
```
1000000000
```
(1 billion - same as max supply for LFJ Token Mill tokens)

### Total Supply API
```
Leave blank (or enter "N/A")
```

**Why blank?** 
- LFJ Token Mill tokens don't have custom supply APIs
- Total supply is fixed and verifiable on-chain
- CoinGecko can query the contract directly

**If they require something, you could note:**
```
Total supply is verifiable on-chain via standard ERC-20 totalSupply() function at 
contract address 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b on Monad (Chain ID 143)
```

### Burned Wallet
```
Leave blank
```

**Why blank?**
- No tokens have been burned
- LFJ Token Mill tokens don't have burn mechanisms by default
- If you've burned any tokens, add the burn address here

---

## 9. Circulating Supply

### Circulating Supply Amount
```
1000000000
```
(1 billion - same as total supply)

**Why same as total supply?**
- Fair launch via bonding curve
- No team allocation
- No vesting schedules
- No locked tokens
- 100% of supply is in circulation

### Circulating Supply API
```
Leave blank (or enter "N/A")
```

**Same reasoning as Total Supply API** - verifiable on-chain, no custom API needed.

### Vested/Locked Wallet
```
Leave blank
```

**Why blank?**
- No vesting schedules (fair launch)
- No team allocations
- No locked tokens
- All supply is circulating

**If you have any LP tokens locked, you could add:**
```
[LP locker contract address if you locked liquidity]
```

---

## 10. Initial Token Allocation

### ⚠️ IMPORTANT: Fair Launch = No Allocations

Since $MON was a **fair launch** via LFJ Token Mill bonding curve with **no presale, no team allocation**, you have two options:

### **Option 1: Leave All Fields Blank (Recommended)**

Simply don't fill out Allocation #1. Add a note in "Additional Supply Information":

```
$MON was launched via fair launch bonding curve (LFJ Token Mill) with no presale, 
no team allocation, and no vesting schedules. 100% of the 1B token supply was made 
available to the public through the bonding curve starting January 20, 2026. There 
are no initial token allocations to report.
```

### **Option 2: Create Single "Public Sale" Allocation**

If the form requires at least one allocation:

```
Allocation #1

Allocation Name: Public Sale (Bonding Curve)

Percentage of Allocation (%): 100

Token Generation Event Percentage (%): 100

Cliff Period (Month): 0

Vesting Period (Month): 0

Release Schedule (Frequency): 100% available at TGE via LFJ Token Mill bonding curve. 
No vesting, no cliff, no team allocation.
```

---

## 11. Additional Supply Information

**Copy-Paste Ready:**

```
$MON is a fair launch token created via LFJ Token Mill bonding curve on Monad blockchain 
(Chain ID 143) on January 20, 2026. 

Key Supply Details:
• Total Supply: 1,000,000,000 (1 billion, fixed)
• Circulating Supply: 1,000,000,000 (100% - no locks or vesting)
• Max Supply: 1,000,000,000 (fixed, no inflation)
• Decimals: 18 (standard ERC-20)

Launch Model:
• Fair launch via LFJ Token Mill bonding curve
• No presale, no private sale, no team allocation
• No vesting schedules or cliff periods
• 100% of supply made available to public at TGE
• No burn mechanisms implemented

Contract Information:
• Contract Address: 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b
• Standard: ERC-20 (Monad EVM)
• Verifiable on MonadScan and SocialScan

All supply information is verifiable on-chain. The token follows standard ERC-20 
implementation with no custom supply mechanics, transfer fees, or rebasing mechanisms.
```

---

## 📋 COMPLETE SUMMARY - COPY-PASTE READY

### Section 6: Holders & Distribution
```
Top Holder List URL: 
https://monadscan.com/token/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b#balances

Distribution Schedule: 
https://grokandmon.com
```

### Section 7: Supply Information
```
Token Generation Date: 01/20/2026
Max Supply Amount: 1000000000
Is Infinite Supply: ☐ (unchecked)
```

### Section 8: Total Supply
```
Total Supply Amount: 1000000000
Total Supply API: (leave blank)
Burned Wallet: (leave blank)
```

### Section 9: Circulating Supply
```
Circulating Supply Amount: 1000000000
Circulating Supply API: (leave blank)
Vested/Locked Wallet: (leave blank)
```

### Section 10: Initial Token Allocation
```
(Leave blank - see Option 1 above)

OR

Allocation #1
Allocation Name: Public Sale (Bonding Curve)
Percentage of Allocation (%): 100
Token Generation Event Percentage (%): 100
Cliff Period (Month): 0
Vesting Period (Month): 0
Release Schedule: 100% available at TGE via LFJ Token Mill bonding curve
```

### Section 11: Additional Supply Information
```
(Use the detailed text provided above)
```

---

## ⚠️ Common Questions & Answers

### Q: Why is circulating supply = total supply?
**A:** Fair launch via bonding curve. No team allocation, no vesting, no locks. 100% public from day 1.

### Q: Why no supply APIs?
**A:** Standard ERC-20 tokens don't need custom APIs. CoinGecko can query the contract directly using standard `totalSupply()` and `balanceOf()` functions.

### Q: What if they ask about liquidity locks?
**A:** If you locked LP tokens, add the locker contract address in "Vested/Locked Wallet". If not, leave blank.

### Q: Should I mention the bonding curve market contract?
**A:** No. The market contract (0xfB72c999dcf2BE21C5503c7e282300e28972AB1B) is NOT a vested/locked wallet. It's the AMM where trading happens. Only mention if specifically asked about DEX contracts.

### Q: What about team wallets?
**A:** There are no official "team wallets" in a fair launch. If you personally bought tokens, those are just regular holder wallets, not team allocations.

---

## ✅ Key Points for Approval

1. **Transparency:** All supply is circulating, nothing hidden
2. **Fairness:** No presale advantage, no team dump risk
3. **Verifiable:** Everything on-chain via MonadScan
4. **Standard:** Plain ERC-20, no exotic mechanics
5. **Honest:** Clear about fair launch model

This transparency actually **increases approval chances** because CoinGecko values honesty over complex tokenomics.

---

**Last Updated:** January 30, 2026
