# $MON Token

## Monad (Native)

| Parameter | Value |
|-----------|-------|
| **Chain** | Monad (Chain ID 143) |
| **Contract** | `0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b` |
| **Market** | `0xfB72c999dcf2BE21C5503c7e282300e28972AB1B` |
| **Trade** | [LFJ Token Mill](https://lfj.gg/monad/trade/0x0eb75e7168af6ab90d7415fe6fb74e10a70b5c0b) |

## Base (Bridged via Wormhole NTT)

| Parameter | Value |
|-----------|-------|
| **Chain** | Base (Chain ID 8453) |
| **Contract** | `0xE390612D7997B538971457cfF29aB4286cE97BE2` |
| **Pool** | `0x2f2ec3e1b42756f949bd05f9b491c0b9c49fee3a` (MON/USDC on Aerodrome) |
| **Trade** | [Aerodrome](https://aerodrome.finance/swap?from=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&to=0xE390612D7997B538971457cfF29aB4286cE97BE2) |

## Wormhole NTT Bridge Infrastructure

### Monad Side (LOCKING mode)
| Contract | Address |
|----------|---------|
| NTT Manager | `0x81D87a80B2121763e035d0539b8Ad39777258396` |
| OLD Transceiver | `0xc659d68acfd464cb2399a0e9b857f244422e809d` |
| Transceiver v2 | `0x030D72714Df3cE0E83956f8a29Dd435A0DB89123` |
| Transceiver v3 | `0xF682dd650aDE9B5d550041C7502E7A3fc1A1B74A` |
| TransceiverStructs Lib | `0x49639C591ae6778A2428B15Cd5C27be541D5a260` |

### Base Side (BURNING mode)
| Contract | Address |
|----------|---------|
| NTT Manager | `0xAED180F30c5bd9EBE5399271999bf72E843a1E09` |
| Transceiver 1 | `0xf2ce259C1Ff7E517F8B5aC9ECF86c29de54FC1E4` |
| Transceiver 2 | `0x3e7bFF16795b96eABeC56A4aA2a26bb0BE488C2D` |
| TransceiverStructs Lib | `0x69DF57faF9F74b218CE9D79240dDbc6C16e862C4` |

### Wormhole Chain IDs
- Monad: 48
- Base: 30

### Bridge Path Status

| Direction | Status | Path |
|-----------|--------|------|
| **Monad -> Base** | WORKING | OLD Monad Transceiver -> Base Transceiver 1 |
| **Base -> Monad** | WORKING | Base T1 -> Monad v2 (VAAs signed, needs manual redemption) |

### Transceiver Peer Relationships

| Base Transceiver | Monad Peer | Status |
|------------------|------------|--------|
| T1 (`0xf2ce...`) | v2 (`0x030D...`) | WORKING |
| T2 (`0x3e7b...`) | v3 (`0xF682...`) | WORKING |

**NOTE**: Both directions work! VAAs are signed within ~30 seconds.
If Wormholescan UI shows "0/13 signatures", check the API - it may be showing an orphan transceiver.

### Key Facts
- VAA attestation is FAST (~30 seconds, not 15-20 minutes)
- Monad requires 2x gas estimates
- Transceiver peers are IMMUTABLE once set
- NTT Manager sends through ALL registered transceivers (threshold=1)

See: `docs/NTT_DEPLOYMENT_LESSONS.md` for detailed lessons learned.
See: `docs/BASE_MON_POOL.txt` for Aerodrome pool details.
