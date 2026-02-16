# ERC-8004 Autonomous AI Agents Standard Deep Dive

**Last Updated:** February 5, 2026
**Sources:** EIP spec, Monad deployment, GanjaMon registration

## Overview

ERC-8004 is a **draft Ethereum standard** (proposed August 2025, mainnet launched January 29, 2026) that defines a trustless protocol for discovering, rating, and validating autonomous AI agents across organizational boundaries.

The standard defines three core registries that can be deployed on any EVM chain:
1. **Identity Registry** - ERC-721 NFTs for unique agent identifiers
2. **Reputation Registry** - Structured feedback from clients/users
3. **Validation Registry** - Third-party verification of agent claims

---

## Three Core Registries

### 1. Identity Registry (ERC-721 + URIStorage)

**Purpose:** Assign unique, portable agent identifiers

**Data Model:**
- `agentRegistry` - Chain identifier (e.g., `eip155:143:0x8004A169...`)
- `agentId` - ERC-721 tokenId (incrementally assigned)
- `agentURI` - HTTPS or IPFS URL to agent registration JSON
- `agentWallet` - Agent's payment wallet (EIP-712 verified)

**Key Functions:**
```solidity
register() → agentId
register(string agentURI) → agentId
register(string agentURI, MetadataEntry[] metadata) → agentId
setAgentURI(uint256 agentId, string newURI)
setMetadata(uint256 agentId, string key, bytes value)
setAgentWallet(uint256 agentId, address newWallet, uint256 deadline, bytes signature)
```

### 2. Reputation Registry

**Purpose:** Store structured feedback about agent performance

**Data Stored On-Chain:**
- Fixed-point ratings (int128)
- Decimals (uint8)
- Tags (tag1, tag2)
- Revocation status

**Key Functions:**
```solidity
giveFeedback(uint256 agentId, int128 value, uint8 valueDecimals,
             string tag1, string tag2, string endpoint,
             string feedbackURI, bytes32 feedbackHash)
revokeFeedback(uint256 agentId, uint64 feedbackIndex)
getSummary(uint256 agentId, address[] clientAddresses, string tag1, string tag2)
           → (count, summaryValue, summaryValueDecimals)
```

**Rating Example:**
```
tag1="tradingYield", tag2="week", value=-32, valueDecimals=1
= -3.2% weekly yield
```

### 3. Validation Registry

**Purpose:** Request and record third-party verification

**Response Score:** 0-100 (0=failed, 100=passed)

**Key Functions:**
```solidity
validationRequest(address validatorAddress, uint256 agentId,
                 string requestURI, bytes32 requestHash)
validationResponse(bytes32 requestHash, uint8 response,
                   string responseURI, bytes32 responseHash, string tag)
getSummary(uint256 agentId, address[] validatorAddresses, string tag)
           → (count, averageResponse)
```

---

## Agent Registration JSON Format

The `agentURI` must resolve to a JSON file:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "GanjaMon",
  "description": "Autonomous agent for cultivation monitoring and crypto research",
  "image": "https://grokandmon.com/assets/MON_rasta_meme_logo.png",
  "services": [
    { "name": "web", "endpoint": "https://grokandmon.com" },
    { "name": "A2A", "endpoint": "https://grokandmon.com/.well-known/agent-card.json", "version": "0.3.0" },
    { "name": "MCP", "endpoint": "http://localhost:3010", "version": "2025-06-18" },
    { "name": "x402", "endpoint": "https://grokandmon.com/.well-known/x402-pricing.json", "version": "1.0" },
    { "name": "agentWallet", "endpoint": "eip155:143:0x870FE41c757fF858857587Fa3e68560876deF479" }
  ],
  "x402Support": true,
  "active": true,
  "registrations": [
    { "agentId": 4, "agentRegistry": "eip155:143:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432" }
  ],
  "supportedTrust": ["reputation", "validation"]
}
```

**Key Fields:**
- `type` - Standard identifier
- `services` - Flexible endpoint list (web, A2A, MCP, ENS, DID, email)
- `registrations` - Array of on-chain registrations (multi-chain)
- `supportedTrust` - Which trust models the agent supports

---

## Monad Deployment

**Deployed:** February 2, 2026
**Chain ID:** 143

### Contract Addresses (Deterministic)

| Registry | Address | Implementation |
|----------|---------|-----------------|
| IdentityRegistry | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` | `0x75f2e3c916ee665561eb2fd04d9ccbdee46d1084` |
| ReputationRegistry | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` | `0xa9d88e1ee98db452734eac795a728fb425017f02` |
| ValidationRegistry | `0x98135C011cCB6C5cd2b63E48D55Cf047847c8d3A` | `0x72500e97b449072c71bd2851ef5e5076cf642828` |

**Why Deterministic?** Using Singleton Factory deployment pattern - same salt/init code produces same addresses across all EVM chains.

---

## GanjaMon Registration

**Agent ID:** 4
**Owner:** `0xc48035f98B50aE26B2cA5368b6601940053D2b65`
**Agent Wallet:** `0x870FE41c757fF858857587Fa3e68560876deF479`

### Registration File Location
`/mnt/c/Users/natha/sol-cannabis/src/web/.well-known/agent-registration.json`

### A2A Protocol Card
`/mnt/c/Users/natha/sol-cannabis/src/web/.well-known/agent-card.json`

**Declared Skills:**
- `alpha-scan` - Aggregate signals from social, on-chain, and market data
- `cultivation-status` - Report latest grow metrics
- `mon-liquidity` - Monitor $MON liquidity and arb deltas

---

## Trust Models

ERC-8004 supports **tiered trust** proportional to value at risk:

| Trust Model | Use Case | Security Level |
|-------------|----------|-----------------|
| Reputation | Community feedback | Low stakes (e.g., ordering pizza) |
| Validation | Stake-secured re-execution, zkML | Medium stakes (e.g., portfolio analysis) |
| Crypto-Economic | Agent bonds/slashing | High stakes (e.g., autonomous trading) |
| TEE-Attestation | Trusted execution environment | Very high stakes (e.g., medical) |

---

## x402 Payment Protocol

**HTTP 402: Payment Required** - machine-to-machine micropayments

**Workflow:**
1. Client requests paid resource
2. Server returns `402 Payment Required` with payment details
3. Client's wallet signs x402 payment proof
4. Server verifies payment (via facilitator)
5. Server provides resource

**GanjaMon x402 Config:**
```json
{
  "priceUSD": 0.001,
  "currency": "USDC",
  "chain": "base"
}
```

**Facilitators:**
- CDP Facilitator (Coinbase's fee-free USDC on Base)
- Treasure Facilitator
- PayAI Facilitator
- OpenFacilitator (free, open-source)

---

## Monitoring Infrastructure

**File:** `cloned-repos/ganjamon-agent/src/signals/erc8004_monitor.py`

**Features:**
- Polls 8004scan API every 5 minutes
- Detects new agent registrations
- Scores agents for alpha potential (x402 enabled = 30 pts)
- Monitors agent wallets for token launches
- Sends alerts via webhook

**Alpha Scoring:**
- x402 enabled = likely revenue model = token launch candidate
- Keywords: "trading", "swap", "alpha", "sniper", "whale", "copy"
- High star/watch counts = community attention
- Verified status = established legitimacy

---

## How to Register an Agent

### Using Foundry/Cast

```bash
cast send 0x8004A169FB4a3325136EB29fA0ceB6D2e539a432 \
  "register(string)(uint256)" \
  "https://your-agent.com/.well-known/agent-registration.json" \
  --private-key $PRIVATE_KEY \
  --rpc-url https://rpc.monad.xyz/
```

### Using Web3.py

```python
from web3 import Web3
registry = Web3().eth.contract(address=registry_addr, abi=IDENTITY_REGISTRY_ABI)
tx = registry.functions.register(agent_uri).transact({'from': owner_address})
```

---

## Querying the Registry

**Script:** `/mnt/c/Users/natha/sol-cannabis/scripts/query_8004_registry.py`

```python
RPC = "https://rpc.monad.xyz/"
REGISTRY = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
SELECTOR = "0xc87b56dd"  # tokenURI(uint256) selector

# Call tokenURI(agentId) for each agent
```

---

## Smart Contract Security

**Protections:**
- Agent wallet transfer clears previous wallet
- Metadata uses deterministic slot to prevent collision
- UUPS upgradeable prevents infinite delegatecall
- EIP-712 signatures prevent replay attacks
- Reserved "agentWallet" key cannot be overwritten

---

## Key Learnings

1. **Three registries separate concerns** - Identity, Reputation, Validation are independent
2. **Deterministic addresses across chains** - Same addresses on any EVM chain
3. **Trust is tiered** - Low stakes use reputation, high stakes need validation/bonds
4. **x402 enables agent monetization** - HTTP payment standard for machine-to-machine
5. **Agent cards follow A2A protocol** - Standard format for agent discovery
6. **Monitoring 8004scan finds alpha** - New agent registrations often precede token launches
7. **Multi-chain support built-in** - Registrations array supports multiple chains
8. **UUPS upgradeable** - Contracts can be upgraded by deployer

---

## Related Files

| File | Purpose |
|------|---------|
| `docs/ERC8004_ON_MONAD.md` | Chain deployment details |
| `docs/ERC8004_MONAD_STATUS.md` | Status and next steps |
| `cloned-repos/8004-contracts/ERC8004SPEC.md` | Full EIP spec |
| `cloned-repos/ganjamon-agent/GANJAMON_8004.md` | GanjaMon registration |
| `src/web/.well-known/agent-registration.json` | Registration file |
| `src/web/.well-known/agent-card.json` | A2A protocol card |
| `scripts/query_8004_registry.py` | Registry query tool |

---

## References

- EIP-8004 Spec: https://eips.ethereum.org/EIPS/eip-8004
- 8004scan (Agent Browser): https://8004scan.io
- x402 Protocol: https://x402.org
- Monad RPC: https://rpc.monad.xyz/
- Monad Explorer: https://monadscan.com/
