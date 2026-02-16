# Wormhole NTT Deployment Lessons Learned

## Critical Insights from Base Migration Session

### 1. WormholeTransceiver Peers Cannot Be Updated

**Problem**: Once a peer is set on a WormholeTransceiver, it CANNOT be changed. This is by design.

**Code Location**: `WormholeTransceiverState.sol:166-171`
```solidity
// We don't want to allow updating a peer since this adds complexity in the accountant
// If the owner makes a mistake with peer registration they should deploy a new Wormhole
// transceiver and register this new transceiver with the NttManager
if (oldPeerContract != bytes32(0)) {
    revert PeerAlreadySet(peerChainId, oldPeerContract);
}
```

**Solution**: Deploy a NEW transceiver with the correct peer, then register it with the NTT Manager.

### 2. NTT Contracts Require ERC1967 Proxy Pattern

**Problem**: NTT contracts (NttManager, WormholeTransceiver) use `onlyDelegateCall` modifier on `initialize()`. Deploying them directly results in uninitialized contracts (owner = 0x0).

**Solution**:
1. Deploy the implementation contract
2. Deploy ERC1967Proxy with initialization calldata
3. The proxy forwards the initialize call to the implementation

**Proxy Constructor**:
```solidity
constructor(address _logic, bytes memory _data) payable {
    _upgradeToAndCall(_logic, _data, false);
}
```

### 3. Library Linking for TransceiverStructs

**Problem**: WormholeTransceiver bytecode contains library placeholder that must be replaced.

**Bytecode Contains**: `__$93083e246e55d56d98f3df2872cd16bfd0$__`

**Solution**:
1. Deploy TransceiverStructs library first
2. Replace placeholder with library address (lowercase, no 0x)
3. Then deploy the transceiver

### 4. Wormhole VAA Generation is Fast

**Reality**: Wormhole VAA attestations generate within **seconds**, not 15-20 minutes as some documentation suggests.

**Practical Impact**: Don't wait around - check immediately after initiating a bridge transfer.

### 5. Monad Has Higher Gas Costs

**Problem**: Transactions on Monad require ~2x the estimated gas compared to Base/Ethereum.

**Example**:
- Gas estimate: 146,660
- Actual required: 293,320 (exactly 2x)

**Solution**: Always multiply gas estimate by 2 for Monad transactions.

### 5. Function Selector Accuracy

**Problem**: Using wrong function selectors causes silent failures or unexpected behavior.

**Correct Selectors**:
- `setWormholePeer(uint16,bytes32)`: `0x7ab56403`
- `getWormholePeer(uint16)`: Different selector than assumed
- `setTransceiver(address)`: Compute via keccak256

**Solution**: Always compute selectors using `web3.keccak(text="functionName(types)")[:4]`

### 6. Multiple Transceivers for Bridge Migration

**Problem**: When migrating NTT infrastructure, you may need MULTIPLE transceivers on each chain:
- Old transceiver: Trusted by existing infrastructure
- New transceiver: Trusts new peer infrastructure

**Architecture**:
```
Chain A                          Chain B
┌─────────────────┐             ┌─────────────────┐
│ NTT Manager     │             │ NTT Manager     │
│  └ Transceiver1 │─────────────│  └ Transceiver1 │
│  └ Transceiver2 │─────────────│  └ Transceiver2 │
└─────────────────┘             └─────────────────┘
```

With threshold=1, messages can be attested by any registered transceiver.

### 7. NTT Mode Verification

**Key Storage Patterns**:
- Token address: Readable via standard getter
- Mode (LOCKING vs BURNING): Verify after deployment
- Owner: Check OwnableUpgradeable storage slot

**Mode Slot for NttManagerNoRateLimiting**: Implementation-specific

### 8. ERC1967 Proxy Code Size

**Reference**:
- OpenZeppelin ERC1967Proxy: 177 bytes (minimal)
- Wormhole's proxy variation: 209 bytes

Both work correctly; size difference is due to implementation details.

### 9. Error Decoding

**Common NTT Errors**:
- `0xb55eeae9`: `PeerAlreadySet(uint16 chainId, bytes32 peerContract)`
- Reverts with `0x`: Often permission/modifier check failure

### 10. CRITICAL: Bidirectional Peer Symmetry

**Problem**: Transceiver peers must be configured SYMMETRICALLY for bidirectional transfers:
- If Chain A Transceiver peers with Chain B Transceiver X
- Then Chain B Transceiver X MUST peer with Chain A Transceiver (same one)

**Example of BROKEN configuration**:
```
Monad Transceiver v2 -> peers with Base Transceiver 2
Base Transceiver 2 -> peers with Monad Transceiver v2  ✅ CORRECT

Monad Transceiver v3 -> peers with Base Transceiver 2
Base Transceiver 2 -> peers with Monad Transceiver v2  ❌ ASYMMETRIC!
```

**Impact**:
- Monad -> Base: v3's VAA rejected by Base T2 (expects v2)
- Base -> Monad: Base T2's VAA rejected by v3 (expects T2 but got v2's peer)

**Solution**: Always configure peers symmetrically. Since peers are immutable, asymmetric configuration requires deploying new transceivers.

### 11. NTT Manager Sends Through ALL Registered Transceivers

**Key Insight**: When you initiate a transfer, the NTT Manager sends messages through ALL registered transceivers simultaneously.

**Practical Impact**:
- With threshold=1, ANY transceiver's VAA can be used for redemption
- Multiple VAAs are generated for each transfer (one per transceiver)
- Choose the VAA from the transceiver that has a valid peer on the destination chain

### 12. Contract Address Summary

**Base (New)**:
- MON Token: `0xE390612D7997B538971457cfF29aB4286cE97BE2`
- NTT Manager Proxy: `0xAED180F30c5bd9EBE5399271999bf72E843a1E09`
- Transceiver 1: `0xf2ce259C1Ff7E517F8B5aC9ECF86c29de54FC1E4` (peers with OLD Monad)
- Transceiver 2: `0x3e7bFF16795b96eABeC56A4aA2a26bb0BE488C2D` (peers with Monad v2)
- TransceiverStructs Library: `0x69DF57faF9F74b218CE9D79240dDbc6C16e862C4`

**Monad (Updated)**:
- MON Token: `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b`
- NTT Manager: `0x81D87a80B2121763e035d0539b8Ad39777258396`
- OLD Transceiver: `0xc659d68acfd464cb2399a0e9b857f244422e809d` (peers with OLD Base)
- Transceiver v2: `0x030D72714Df3cE0E83956f8a29Dd435A0DB89123` (peers with Base Transceiver 1 - MISCONFIG)
- Transceiver v3: `0xF682dd650aDE9B5d550041C7502E7A3fc1A1B74A` (peers with Base Transceiver 2)
- TransceiverStructs Library: `0x49639C591ae6778A2428B15Cd5C27be541D5a260`

**Wormhole Chain IDs**:
- Base: 30
- Monad: 48

**Working Bridge Paths** (Tested 2026-02-03):
- Monad -> Base: OLD Monad Transceiver -> Base Transceiver 1 ✅ TESTED
- Base -> Monad: Base Transceiver 2 -> Monad Transceiver v3 (configured, needs ETH for gas test)

**Common Error Selectors**:
- `0x79b1ce56`: `InvalidWormholePeer(uint16 chainId, bytes32 emitterAddress)`
- `0xb55eeae9`: `PeerAlreadySet(uint16 chainId, bytes32 peerContract)`
- `0xe450d38c`: `ERC20InsufficientBalance(address sender, uint256 balance, uint256 needed)`
- `0x5fb5729e`: `CallerNotMinter(address caller)`

---
*Document created: 2026-02-03*
*Migration Status: TESTED - Monad -> Base working, Base -> Monad configured*
