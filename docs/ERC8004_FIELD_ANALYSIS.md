# ERC-8004 Agent Metadata Field Analysis

## Research Summary (2026-02-07)

Analyzed top-scoring ERC-8004 agents on Monad to understand optimal metadata field structures.

## Agent Profiles Analyzed

| Agent ID | Name | Score | Service Score | Status |
|----------|------|-------|---------------|--------|
| **2** | EmpowerToursAgent | 42.09 | Has A2A | HTTPS URI (WA040 warning) |
| **3** | MemeSommelier | 59.68 | Web only | base64 data URI |
| **4** | GanjaMon (us) | TBD | A2A + MCP | IPFS URI |

## Critical Finding: Service Field Names

### EmpowerToursAgent (Agent #2) - The Reference Implementation

**Uses `"endpoint"` field for service URLs:**

```json
{
  "services": [
    {
      "name": "Agent World API",
      "endpoint": "https://fcempowertours-production-6551.up.railway.app/api/world",
      "version": "1.0.0",
      "skills": ["world-state", "agent-registration", "actions", "rewards"],
      "domains": ["gaming", "social", "defi", "nft"]
    },
    {
      "name": "Premium Oracle (x402)",
      "endpoint": "https://fcempowertours-production-6551.up.railway.app/api/world/oracle-paid",
      "version": "1.0.0",
      "skills": ["premium-ai-queries"],
      "domains": ["ai"],
      "x402": {
        "price": "$0.001",
        "currency": "USDC",
        "network": "monad"
      }
    }
  ]
}
```

**Key observations:**
- Uses **`"endpoint"`** NOT `"url"`
- Has `"name"` field (human-readable service name)
- Does NOT have `"type"` field (a2a/mcp/etc.)
- Has `"skills"` array (what the service can do)
- Has `"domains"` array (categorization)
- Version is present on all services
- x402 payment info embedded in service object

### GanjaMon (Our Metadata) - Uses Different Fields

**We use `"type"` and `"url"`:**

```json
{
  "services": [
    {
      "type": "a2a",
      "url": "https://grokandmon.com/a2a/v1",
      "version": "0.3.0",
      "a2aSkills": ["cultivation-status", "alpha-scan", "trade-execution", "signal-feed"]
    },
    {
      "type": "mcp",
      "url": "https://grokandmon.com/mcp/v1",
      "version": "2025-06-18",
      "mcpTools": [...]
    }
  ]
}
```

**Key differences:**
- Uses **`"type"`** to categorize service (a2a, mcp, oasf, agentWallet)
- Uses **`"url"`** NOT `"endpoint"`
- Has `"a2aSkills"` and `"mcpTools"` instead of generic `"skills"`
- No `"name"` field
- No `"domains"` field

## Service Score Analysis

### Agent #2 (EmpowerToursAgent)
- **Service Score**: Has services, score not explicitly shown but agent scores 42.09 overall
- **Compliance**: WA040 warning (HTTPS URI not content-addressed)
- **Service Structure**: Multiple detailed service entries with names, domains, skills

### Agent #3 (MemeSommelier)
- **Service Score**: Penalized for no A2A/MCP
- **Services**: Only has web endpoint (Moltbook profile)
- **Warning**: IA004 - Missing registrations array

### Agent #4 (GanjaMon - Us)
- **Service Score**: Previously 0 due to field name mismatch
- **Current Status**: Fixed `"type"` and `"url"` fields, but may need to match EmpowerTours structure
- **Advantage**: IPFS URI (no WA040), has both A2A and MCP

## The Field Name Discrepancy

### Theory: Two Valid Approaches

1. **Type-based approach** (what we use):
   - `"type": "a2a"` - Tells validator what kind of service
   - `"url": "https://..."` - The endpoint URL
   - Validator checks `service['type'].toLowerCase() === 'a2a'`

2. **Name-based approach** (EmpowerTours):
   - `"name": "Agent World API"` - Human-readable name
   - `"endpoint": "https://..."` - The endpoint URL
   - `"skills"` and `"domains"` arrays - Categorization
   - No explicit "type" field

### Validator Logic Mystery

From memory (8004scan.md line 148):
> Parser checks `service['type'].toLowerCase() === 'a2a'` — wrong field name → `isA2A: false`

This suggests the validator DOES look for `"type"` field. But EmpowerTours doesn't have it and still scores well!

**Possible explanations:**
1. EmpowerTours might have updated their metadata after initial registration
2. The validator may have multiple detection methods (type field OR skills matching)
3. Their service score might actually be low but other dimensions are high
4. The validator evolved and now accepts both patterns

## Service Score Dimensions (from memory/8004scan.md)

| Dimension | Weight | What drives it |
|-----------|--------|----------------|
| Engagement | 30% | Stars, watches, feedback, chats, messages |
| Service | 25% | **Validator liveness checks on declared endpoints** |
| Publisher | 20% | Verification badge, org reputation |
| Compliance | 15% | Metadata spec adherence, warnings/errors |
| Momentum | 10% | Recent on-chain events, metadata freshness |

**Service dimension specifically checks:**
- Are A2A/MCP endpoints reachable?
- Do they respond correctly to spec requests?
- Uptime/liveness over time

## Recommendations

### Option 1: Keep Our Current Structure (Conservative)
**Pros:**
- Already deployed and working
- Uses explicit `"type"` field (clearer)
- IPFS content-addressing (no WA040)
- Both A2A and MCP declared

**Cons:**
- May not match evolving spec expectations
- Missing `"domains"` categorization
- Missing `"skills"` arrays (uses type-specific fields)

### Option 2: Adopt EmpowerTours Structure (Risky)
**Pros:**
- Matches highest-scoring example
- More detailed service metadata (skills, domains, names)
- May align better with future spec evolution

**Cons:**
- Major structural change
- Need to test validator acceptance
- Would require new IPFS pin + on-chain update
- Unclear if it actually improves score

### Option 3: Hybrid Approach (Recommended)
Keep our `"type"` field but ADD fields from EmpowerTours:

```json
{
  "services": [
    {
      "name": "Agent-to-Agent Protocol",
      "type": "a2a",
      "url": "https://grokandmon.com/a2a/v1",
      "endpoint": "https://grokandmon.com/a2a/v1",  // redundant but safe
      "version": "0.3.0",
      "skills": [
        "cultivation-status-query",
        "alpha-signal-scan",
        "trade-execution",
        "real-time-feed"
      ],
      "domains": [
        "agriculture",
        "iot",
        "defi",
        "trading"
      ]
    },
    {
      "name": "Model Context Protocol",
      "type": "mcp",
      "url": "https://grokandmon.com/mcp/v1",
      "endpoint": "https://grokandmon.com/mcp/v1",
      "version": "2025-06-18",
      "skills": [
        "sensor-data-access",
        "actuator-control",
        "portfolio-management",
        "market-analysis"
      ],
      "domains": [
        "agriculture",
        "iot",
        "robotics",
        "defi"
      ]
    }
  ]
}
```

**Rationale:**
- Provides both `"url"` and `"endpoint"` (covers both detection methods)
- Keeps `"type"` for explicit categorization
- Adds `"name"` for human readability
- Adds `"skills"` and `"domains"` for richer metadata
- Maximum compatibility with multiple validator versions

## Next Steps

1. **Wait for current metadata to index** - Give 8004scan time to process our latest update
2. **Check service score in 24-48h** - See if current structure works
3. **If service score remains 0** - Implement hybrid approach
4. **Monitor EmpowerTours** - Check if they update their metadata (watch for tx events)

## Additional Context

### x402 Payment Support
EmpowerTours explicitly shows x402 pricing in service metadata:
```json
"x402": {
  "price": "$0.001",
  "currency": "USDC",
  "network": "monad"
}
```

We have `"x402Support": true` at top level but don't declare pricing per-service.

**Should we add?**
- Our A2A endpoint could charge per query
- Would make monetization explicit
- But adds complexity if not implemented yet

### Trust Model Declaration
Both agents declare supported trust models:
- **EmpowerTours**: `"supportedTrust": ["reputation"]`
- **GanjaMon**: `"supportedTrust": ["reputation", "crypto-economic"]`

We already have this covered.

### Service Complexity Comparison

| Agent | Total Services | Service Types | Complexity |
|-------|----------------|---------------|------------|
| EmpowerTours | 7 | Web APIs | High (multiple endpoints, x402) |
| MemeSommelier | 1 | Web profile | Low (just URL) |
| GanjaMon | 4 | A2A, MCP, OASF, Wallet | High (protocol endpoints) |

## Compliance Warnings Comparison

### Agent #1 (Basic)
- No metadata URI
- No services
- Zero metadata completeness

### Agent #2 (EmpowerTours)
- WA040: HTTP/HTTPS URI not content-addressed
- Otherwise clean

### Agent #3 (MemeSommelier)
- IA004: Missing registrations array
- No A2A/MCP (service penalty)
- 50% metadata completeness

### Agent #4 (GanjaMon - Us)
- Previous: Service field name mismatch
- Current: Should be clean (IPFS URI, proper structure)
- Need to verify after re-index

## Validator Endpoint Testing

The validator checks if endpoints are reachable. From our A2A endpoint:

```javascript
// pages-deploy/functions/a2a/v1.js
export async function onRequest(context) {
  const { request } = context;

  if (request.method === 'POST') {
    const body = await request.json();
    const { jsonrpc, method, params, id } = body;

    // Returns proper JSON-RPC responses for:
    // - message/send
    // - tasks/get
    // - tasks/cancel
    // - agent/info
  }

  // GET returns agent-card.json
}
```

**Testing:**
```bash
# Test A2A endpoint
curl -X POST https://grokandmon.com/a2a/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"agent/info","id":1}'

# Test MCP endpoint
curl -X POST https://grokandmon.com/mcp/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

Both should return valid JSON-RPC responses for the validator to consider them "live."

## Conclusion

**The key finding:** EmpowerTours uses `"endpoint"` while we use `"url"`. The spec itself may accept both, but validators might be looking for specific field names.

**Recommended action:** Implement hybrid approach with BOTH fields plus enriched metadata (name, skills, domains) to maximize compatibility and score potential.

**Priority:** Medium - Our current structure should work, but enriching it could improve service dimension scoring.
