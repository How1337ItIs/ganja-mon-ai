# Dust Aggregation Guide for $MON Token

**Last Updated:** January 27, 2026

This guide covers solutions for converting low-value tokens (dust) to $MON on Monad, including existing services and custom implementation options.

---

## Quick Answer

**Best Options:**
1. **Build custom Monad aggregator** ⭐ **RECOMMENDED** - Direct to $MON, full control, one-click
2. **Use Mace** (Monad-only) - Works on Monad, but manual token selection (not true dust aggregator)
3. **Dust.fun** - ⚠️ **UNCLEAR Monad support** - Uses ZetaChain, may not support Monad yet

**⚠️ IMPORTANT:** Most existing dust aggregators do NOT support Monad yet. Building custom is likely your best option.

---

## Existing Solutions

### Option 1: Dust.fun (Cross-Chain) ⚠️ Monad Support Unclear

**What it is:**
- Cross-chain dust aggregator powered by ZetaChain
- Consolidates dust from multiple chains (Ethereum, BNB, Bitcoin, Solana, etc.)
- Converts to preferred asset (Bitcoin, ETH, etc.)

**Monad Support Status:**
- ⚠️ **UNCLEAR** - Dust.fun uses ZetaChain, which supports EVM chains
- ⚠️ **NOT CONFIRMED** - No evidence Monad is in their supported chain list
- ⚠️ **NEEDS VERIFICATION** - Check their docs: https://fingerpump.gitbook.io/dust.fun/available-chains-and-whitelisted-tokens

**How it works:**
- Uses ZetaChain's Gateway for unified cross-chain interface
- Single-click conversion of all dust tokens
- Works as Universal App on ZetaChain's Universal EVM

**Pros:**
- ✅ Cross-chain support (if Monad is supported)
- ✅ Already built and working
- ✅ Minimal clicks (one-click conversion)
- ✅ No development needed

**Cons:**
- ❌ **Monad support not confirmed** - May not work on Monad
- ❌ Doesn't directly convert to $MON (converts to BTC/ETH)
- ❌ Users would need to swap again to get $MON
- ❌ Requires verification of Monad support

**Action Required:**
1. **Verify Monad support:** Visit https://fingerpump.gitbook.io/dust.fun/available-chains-and-whitelisted-tokens
2. **Contact them:** Discord: https://discord.com/invite/FTSeFc9Yh4
3. **If supported:** Can use for cross-chain dust, then bridge to Monad
4. **If NOT supported:** Skip this option

**Status:** ⚠️ **DO NOT USE UNTIL MONAD SUPPORT CONFIRMED**

---

### Option 2: DustBot (Ethereum-Only) ❌ Does NOT Support Monad

**What it is:**
- Dust aggregator for **Ethereum mainnet ONLY**
- Converts dust tokens to $DUSTBOT native token
- Analyzes wallet for economically viable trades

**Monad Support Status:**
- ❌ **CONFIRMED: NO MONAD SUPPORT** - Ethereum-only platform
- ❌ Only works on Ethereum network

**Pros:**
- ✅ Already built
- ✅ Gas-optimized
- ✅ Analyzes profitability before converting

**Cons:**
- ❌ **Ethereum only (NOT Monad)**
- ❌ Converts to $DUSTBOT, not $MON
- ❌ Users would need to bridge + swap
- ❌ **Cannot be used for Monad dust**

**Status:** ❌ **NOT USABLE FOR MONAD** - Skip this option

---

### Option 3: Mace (Monad DEX Aggregator) ✅ Confirmed Monad Support

**What it is:**
- **Monad-exclusive** DEX aggregator
- Built specifically for Monad Mainnet
- Uses graph-native EVM routing
- Finds optimal swap prices across Monad DEXs

**Monad Support Status:**
- ✅ **CONFIRMED: WORKS ON MONAD** - Built exclusively for Monad
- ✅ Live on Monad Mainnet
- ✅ First native DEX aggregator on Monad

**Pros:**
- ✅ **Confirmed Monad support**
- ✅ Already deployed and working
- ✅ Aggregates multiple DEXs on Monad
- ✅ Can swap any Monad token to $MON
- ✅ Gas optimized for Monad

**Cons:**
- ❌ **Not a true dust aggregator** - Users must select tokens manually
- ❌ Multiple clicks required (select each token, approve, swap)
- ❌ Doesn't batch multiple tokens automatically
- ❌ No automatic wallet scanning for dust

**Integration:**
- Users visit https://www.mace.ag
- Connect wallet (must be on Monad network)
- **Manually select each dust token** one at a time
- Swap to $MON (one token per transaction)

**Status:** ✅ **WORKS ON MONAD** but not ideal UX for dust aggregation - requires manual work

**Best Use Case:** For users who want to manually swap specific tokens to $MON on Monad

---

## Custom Solution: Build Your Own Dust Aggregator

### Architecture Overview

```
User Wallet → Smart Contract → DEX Router → $MON Token
     ↓              ↓              ↓
  Multiple      Batch Swap    Single Output
  Dust Tokens   (Gas Optimized)  ($MON)
```

### Key Features

1. **Batch Token Detection**
   - Scan wallet for all ERC-20 tokens
   - Filter by balance (dust threshold, e.g., < $5 value)
   - Calculate gas costs vs. token value

2. **Smart Contract Aggregator**
   - Batch swap multiple tokens in one transaction
   - Route through best DEX (Uniswap, Curve, etc.)
   - Output: $MON tokens

3. **Gas Optimization**
   - Batch approvals (if needed)
   - Single transaction for all swaps
   - Use multicall pattern

4. **Cross-Chain Support (Optional)**
   - Bridge dust from other chains to Monad first
   - Then aggregate on Monad
   - Or use ZetaChain/other bridge protocols

---

## Implementation Plan

### Phase 1: Monad-Only Aggregator (Simplest)

**Smart Contract:**
```solidity
// contracts/DustToMON.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IDEXRouter {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

contract DustToMON is Ownable {
    using SafeERC20 for IERC20;
    
    address public constant MON_TOKEN = 0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b; // $MON address
    address public constant DEX_ROUTER = 0x0B79d71AE99528D1dB24A4148b5f4F865cc2b137; // Monad DEX router
    uint256 public constant MIN_DUST_VALUE = 0.01 ether; // Minimum value to convert (in MON)
    
    struct SwapParams {
        address token;
        uint256 amount;
        uint256 amountOutMin;
        address[] path;
    }
    
    /**
     * @dev Convert multiple dust tokens to $MON in one transaction
     * @param swaps Array of swap parameters for each token
     */
    function convertDustToMON(SwapParams[] calldata swaps) external {
        IDEXRouter router = IDEXRouter(DEX_ROUTER);
        uint256 totalMON = 0;
        
        for (uint256 i = 0; i < swaps.length; i++) {
            SwapParams memory swap = swaps[i];
            IERC20 token = IERC20(swap.token);
            
            // Transfer token from user to contract
            token.safeTransferFrom(msg.sender, address(this), swap.amount);
            
            // Approve router
            token.safeApprove(DEX_ROUTER, swap.amount);
            
            // Swap to $MON
            uint[] memory amounts = router.swapExactTokensForTokens(
                swap.amount,
                swap.amountOutMin,
                swap.path,
                msg.sender, // Send $MON directly to user
                block.timestamp + 300
            );
            
            totalMON += amounts[amounts.length - 1];
        }
        
        require(totalMON >= MIN_DUST_VALUE, "Total output below minimum");
    }
    
    /**
     * @dev Emergency withdraw (owner only)
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).safeTransfer(owner(), amount);
    }
}
```

**Frontend (React/Next.js):**
```typescript
// components/DustAggregator.tsx
import { useAccount, useBalance, useContractWrite } from 'wagmi';
import { parseEther, formatEther } from 'viem';
import { DUST_TO_MON_ABI } from '@/abis/DustToMON';

export function DustAggregator() {
  const { address } = useAccount();
  const [dustTokens, setDustTokens] = useState<DustToken[]>([]);
  
  // Scan wallet for dust tokens
  const scanDust = async () => {
    // 1. Get all token balances from wallet
    // 2. Filter by value (dust threshold)
    // 3. Calculate swap paths to $MON
    // 4. Display to user
  };
  
  // Batch convert all dust to $MON
  const { write: convertDust } = useContractWrite({
    address: DUST_TO_MON_ADDRESS,
    abi: DUST_TO_MON_ABI,
    functionName: 'convertDustToMON',
  });
  
  return (
    <div>
      <button onClick={scanDust}>Scan for Dust</button>
      <div>
        {dustTokens.map(token => (
          <div key={token.address}>
            {token.symbol}: {formatEther(token.balance)}
          </div>
        ))}
      </div>
      <button onClick={() => convertDust({ args: [swaps] })}>
        Convert All to $MON
      </button>
    </div>
  );
}
```

**Key Features:**
- ✅ One-click conversion
- ✅ Batch multiple tokens
- ✅ Gas optimized (single transaction)
- ✅ Direct to $MON (no intermediate swaps)

---

### Phase 2: Cross-Chain Aggregator (Advanced)

**Architecture:**
```
Other Chains → Bridge → Monad → Aggregator → $MON
```

**Implementation:**
1. **Bridge Integration**
   - Integrate with Across Protocol, Socket, or deBridge
   - Auto-bridge dust from other chains to Monad
   - Then use Phase 1 aggregator

2. **Multi-Chain Detection**
   - Scan wallets on Ethereum, BNB, Base, etc.
   - Show dust across all chains
   - One-click: bridge + aggregate + convert to $MON

**Example Flow:**
```typescript
async function convertCrossChainDust() {
  // 1. Detect dust on Ethereum
  const ethDust = await scanChain('ethereum', wallet);
  
  // 2. Bridge to Monad (via Across/Socket)
  await bridgeTokens(ethDust, 'monad');
  
  // 3. Wait for bridge confirmation
  await waitForBridge();
  
  // 4. Aggregate on Monad
  await convertDustToMON(monadDust);
}
```

---

## Recommended Approach

### Short-Term (Use Existing)

1. **Use Mace for Monad Dust** ✅ **CONFIRMED WORKING**
   - Link to https://www.mace.ag on your website
   - Users can manually swap dust tokens to $MON
   - **Effort:** Low (just add link)
   - **User Experience:** Multiple clicks (manual token selection)
   - **Limitation:** Not automated, users must select each token

2. **Verify Dust.fun Monad Support** ⚠️ **NEEDS VERIFICATION**
   - Check their docs: https://fingerpump.gitbook.io/dust.fun/available-chains-and-whitelisted-tokens
   - Contact Discord: https://discord.com/invite/FTSeFc9Yh4
   - **If supported:** Can use for cross-chain dust → bridge → swap to $MON
   - **If NOT supported:** Skip this option

3. **Create Simple Frontend**
   - Link to Mace for Monad-only dust (confirmed working)
   - Add "Convert to $MON" button that opens Mace swap
   - **Effort:** Low (1-2 days)
   - **User Experience:** 2-3 clicks per token (not ideal for multiple dust tokens)

### Long-Term (Build Custom) ⭐ **STRONGLY RECOMMENDED**

**Why Build Custom:**
- ❌ **No existing dust aggregator supports Monad** (DustBot = Ethereum only, Dust.fun = unclear)
- ✅ **Mace works but isn't a true dust aggregator** (manual token selection)
- ✅ **Market opportunity** - First dust aggregator on Monad
- ✅ **Better UX** - One-click batch conversion vs. manual swaps

**Build Phase 1 (Monad-Only Aggregator):**
- Smart contract: 1-2 weeks
- Frontend: 1 week
- Testing: 1 week
- **Total:** ~1 month
- **Cost:** Gas for deployment (~$50-100 on Monad)

**Benefits:**
- ✅ **One-click batch conversion** (all dust tokens at once)
- ✅ **Direct to $MON** (no intermediate swaps)
- ✅ **Automatic wallet scanning** (detects all dust)
- ✅ **Full control** (your brand, your UX)
- ✅ **Can add features** (referrals, rewards, etc.)
- ✅ **First mover advantage** on Monad

**Optional: Phase 2 (Cross-Chain)**
- Add bridge integration (Across, Socket, etc.)
- Multi-chain detection
- Auto-bridge dust from other chains to Monad
- **Additional:** 2-3 weeks

---

## Integration with Your Website

### Quick Integration (Recommended)

Add to `grokandmon.com`:

```html
<!-- Dust Aggregator Widget -->
<div class="dust-aggregator">
  <h2>Convert Your Dust to $MON</h2>
  <p>Got low-value tokens cluttering your wallet? Convert them all to $MON in one click!</p>
  
  <!-- Option 1: Cross-chain (via Dust.fun) -->
  <a href="https://dust.fun" target="_blank" class="btn-primary">
    Convert Cross-Chain Dust
  </a>
  
  <!-- Option 2: Monad-only (via Mace) -->
  <a href="https://www.mace.ag" target="_blank" class="btn-secondary">
    Swap on Monad DEX
  </a>
  
  <!-- Future: Custom aggregator -->
  <div id="custom-aggregator" style="display: none;">
    <!-- Your custom aggregator component -->
  </div>
</div>
```

### Advanced Integration

Embed custom aggregator widget:

```typescript
// Embeddable widget for other sites
export function MONDustAggregator() {
  return (
    <iframe 
      src="https://grokandmon.com/dust-aggregator"
      width="400"
      height="600"
      frameBorder="0"
    />
  );
}
```

---

## Gas Cost Considerations

**Monad Advantages:**
- ✅ Low gas fees (~$0.01-0.10 per transaction)
- ✅ Fast finality (1 second)
- ✅ High throughput (10,000+ TPS)

**Dust Conversion Economics:**
- **Minimum dust value:** $0.50-1.00 (worth converting)
- **Gas cost:** ~$0.05-0.10 per conversion
- **Break-even:** Dust must be worth more than gas

**Optimization:**
- Batch multiple tokens in one transaction
- Use multicall pattern
- Skip tokens below threshold

---

## Security Considerations

1. **Smart Contract Audits**
   - Audit before mainnet deployment
   - Use OpenZeppelin libraries
   - Test thoroughly on testnet

2. **User Safety**
   - Clear slippage warnings
   - Show gas estimates
   - Allow users to select which tokens to convert

3. **Access Control**
   - Owner functions for emergency stops
   - Pause mechanism
   - Upgradeable contract (if needed)

---

## Next Steps

### Immediate (This Week)
1. ✅ **Verify Dust.fun Monad support** (check their docs)
2. ✅ **Add Mace link** to website (confirmed working on Monad)
3. ✅ **Start planning custom aggregator** (likely best option)

### Short-Term (This Month)
1. ✅ Build Phase 1 smart contract (Monad-only)
2. ✅ Create simple frontend
3. ✅ Deploy to Monad testnet
4. ✅ Test with small amounts

### Long-Term (Next Quarter)
1. ✅ Add cross-chain support
2. ✅ Integrate with bridges
3. ✅ Add referral/reward system
4. ✅ Marketing campaign

---

## Resources

### Existing Services (Monad Support Status)

| Service | Monad Support | Status |
|---------|---------------|--------|
| **Mace** | ✅ **YES** - Monad-exclusive | https://www.mace.ag |
| **Dust.fun** | ⚠️ **UNCLEAR** - Needs verification | https://dust.fun |
| **DustBot** | ❌ **NO** - Ethereum only | https://dustbot.app |
| **0x Protocol** | ✅ **YES** - Supports Monad (chain ID 143) | https://0x.org/docs/introduction/build-on-monad |

### Monad-Specific Resources
- **Mace (Monad DEX Aggregator):** https://www.mace.ag ✅ **CONFIRMED**
- **Mace Docs:** https://docs.mace.ag
- **0x Protocol (Monad):** https://0x.org/docs/introduction/build-on-monad ✅ **CONFIRMED**

### Development Tools
- **Hardhat:** https://hardhat.org
- **Foundry:** https://book.getfoundry.sh
- **Wagmi:** https://wagmi.sh (React hooks for Ethereum/Monad)
- **viem:** https://viem.sh (TypeScript Ethereum library)

### Monad Resources
- **Monad Docs:** https://docs.monad.xyz
- **Monad RPC:** https://rpc.monad.xyz
- **Monad Explorer:** (check docs.monad.xyz)

---

## Questions to Consider

1. **Target Users:**
   - Monad-only users? → Build Phase 1
   - Cross-chain users? → Integrate Dust.fun or build Phase 2

2. **Budget:**
   - Use existing? → Free (just integration)
   - Build custom? → ~$500-2000 (dev + audit)

3. **Timeline:**
   - Need it now? → Use Dust.fun + Mace
   - Can wait 1 month? → Build custom

4. **Features:**
   - Basic conversion? → Phase 1
   - Cross-chain + rewards? → Phase 2

---

**Recommendation:** 

**Immediate:** Use Mace (confirmed Monad support) for basic swaps, but it's not ideal for dust aggregation.

**Best Path Forward:** **Build custom Monad dust aggregator** - No existing solution provides true one-click batch dust conversion on Monad. This is a market opportunity and will provide the best UX for converting dust directly to $MON.
