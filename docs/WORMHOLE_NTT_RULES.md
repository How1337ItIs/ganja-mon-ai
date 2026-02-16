# Wormhole NTT Debugging Rules

**CRITICAL**: These lessons were learned the hard way. Follow them exactly.

## Lesson 1: Wormholescan UI vs API Discrepancy

**The Problem**: Wormholescan UI shows ONE VAA per transaction, but NTT sends through MULTIPLE transceivers.

**The Mistake**: Seeing "0/13 signatures" on Wormholescan UI and concluding the bridge is broken.

**The Truth**: The UI may be showing an orphan transceiver's VAA status while valid VAAs exist for other transceivers.

**The Fix**: ALWAYS query the Wormholescan API to check ALL VAAs:
```python
import requests

TX_HASH = "0x..."
url = f"https://api.wormholescan.io/api/v1/operations?txHash={TX_HASH}"
resp = requests.get(url)
data = resp.json()
# Check ALL operations - there may be multiple VAAs from different transceivers
```

**Also check by emitter**:
```python
# Get all VAAs from a specific transceiver
emitter = "f2ce259c1ff7e517f8b5ac9ecf86c29de54fc1e4"  # Base T1
chain_id = 30  # Base
url = f"https://api.wormholescan.io/api/v1/vaas/{chain_id}/{emitter}"
```

## Lesson 2: Peer Relationships

- Transceiver peers are IMMUTABLE once set
- NTT Manager sends through ALL registered transceivers (threshold=1)
- Only ONE transceiver pair needs to work for the bridge to function
- Check peer relationships before concluding anything is broken

## Lesson 3: VAA Attestation Speed

- VAA attestation is FAST (~30 seconds on Monad, not 15-20 minutes)
- If a VAA isn't signed after 5 minutes, check the API for ALL VAAs
- Don't wait endlessly for a VAA that's already been signed elsewhere

## Lesson 4: Never Mark Bridge "Broken" Without Full Investigation

Before declaring any bridge direction broken:
1. Query Wormholescan API for ALL VAAs (not just UI)
2. Check ALL transceiver pairs, not just the first one
3. Verify peer relationships on BOTH chains
4. Test with a small amount first
5. Check if previously successful transfers used a different transceiver pair

## Debugging Checklist

```bash
# 1. Get all VAAs for a transaction
curl "https://api.wormholescan.io/api/v1/operations?txHash=0x..."

# 2. Check specific transceiver's VAAs
curl "https://api.wormholescan.io/api/v1/vaas/{chainId}/{emitterAddress}"

# 3. Verify transceiver peers (on-chain)
# Call getWormholePeer(chainId) on each transceiver

# 4. Check NTT Manager transceivers
# Call getTransceivers() on NTT Manager
```

## Key Contract Addresses

See: `.claude/context/token.md` for current bridge infrastructure addresses.

## Real Example

Transaction `0xd3c33d8b57be200a795540c7aff9135638101e1382f1bf00b87b9a69946c4e1b`:
- Wormholescan UI showed: 0/13 signatures (orphan transceiver)
- Wormholescan API showed: 3 VAAs, ALL SIGNED
- Conclusion: 100 MON was NOT lost, just needed to redeem via the correct transceiver

**Don't make snap judgments based on the Wormholescan UI alone.**
