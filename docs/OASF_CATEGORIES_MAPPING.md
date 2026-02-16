# OASF Categories Mapping for GanjaMon

**Status:** Ready to implement
**Date:** 2026-02-07

## Summary

The 8004scan validator flagged our OASF categories as unknown because we used invalid category paths. The official OASF v1.0.0 taxonomy defines 15 skill categories and 24 domain categories with specific naming conventions.

## Current (Invalid) Categories

### Skills - What We Had
```json
"skills": [
  "advanced_reasoning_planning/strategic_planning",  // ✅ VALID
  "decision_making",                                  // ❌ INVALID - not in taxonomy
  "risk_assessment",                                  // ❌ INVALID - should be governance_compliance/risk_classification
  "data_engineering/data_transformation_pipeline",    // ✅ VALID
  "images_computer_vision/object_detection",          // ✅ VALID
  "evaluation_monitoring/anomaly_detection"           // ✅ VALID
]
```

### Domains - What We Had
```json
"domains": [
  "agriculture/precision_agriculture",        // ✅ VALID
  "agriculture/agriculture_optimization",     // ❌ INVALID - should be agriculture/agricultural_technology
  "iot/sensor_networks",                      // ❌ INVALID - should be technology/internet_of_things/iot_networks
  "iot/automation",                           // ❌ INVALID - should be industrial_manufacturing/automation
  "finance/crypto",                           // ❌ INVALID - should be technology/blockchain/defi
  "finance/trading",                          // ❌ INVALID - should be finance_and_business/finance
  "technology/ai_decision_systems"            // ❌ INVALID - not in taxonomy
]
```

---

## Recommended (Valid) Categories

### Skills Array
```json
"skills": [
  "advanced_reasoning_planning/strategic_planning",
  "governance_compliance/risk_classification",
  "data_engineering/data_transformation_pipeline",
  "images_computer_vision/object_detection",
  "evaluation_monitoring/anomaly_detection",
  "evaluation_monitoring/monitoring_alerting"
]
```

### Domains Array
```json
"domains": [
  "agriculture/precision_agriculture",
  "agriculture/agricultural_technology",
  "technology/internet_of_things/iot_devices",
  "technology/internet_of_things/iot_networks",
  "industrial_manufacturing/robotics",
  "industrial_manufacturing/automation",
  "technology/blockchain/defi",
  "finance_and_business/finance"
]
```

---

## Detailed Mapping Rationale

### IoT / Horticulture Capabilities

| Our Capability | Invalid Category | Valid OASF Category | ID |
|----------------|------------------|---------------------|-----|
| Sensor networks | `iot/sensor_networks` | `technology/internet_of_things/iot_networks` | 10103 |
| IoT devices | `iot/automation` | `technology/internet_of_things/iot_devices` | 10101 |
| Actuator control | `iot/automation` | `industrial_manufacturing/automation` | 701 |
| Robotics (pumps, fans, lights) | (none) | `industrial_manufacturing/robotics` | 702 |
| Precision farming | `agriculture/precision_agriculture` | `agriculture/precision_agriculture` | 1104 |
| Cultivation tech | `agriculture/agriculture_optimization` | `agriculture/agricultural_technology` | 1101 |

### Trading / DeFi Capabilities

| Our Capability | Invalid Category | Valid OASF Category | ID |
|----------------|------------------|---------------------|-----|
| DeFi protocols | `finance/crypto` | `technology/blockchain/defi` | 10902 |
| Trading execution | `finance/trading` | `finance_and_business/finance` | 202 |
| Risk assessment | `risk_assessment` | `governance_compliance/risk_classification` | 1304 |

### AI / Decision-Making Capabilities

| Our Capability | Invalid Category | Valid OASF Category | ID |
|----------------|------------------|---------------------|-----|
| Strategic planning | `advanced_reasoning_planning/strategic_planning` | `advanced_reasoning_planning/strategic_planning` | 1501 |
| Decision-making | `decision_making` | `advanced_reasoning_planning/strategic_planning` | 1501 |
| AI decision systems | `technology/ai_decision_systems` | (REMOVED - not in taxonomy) | — |

### Data / Monitoring Capabilities

| Our Capability | Invalid Category | Valid OASF Category | ID |
|----------------|------------------|---------------------|-----|
| Data pipelines | `data_engineering/data_transformation_pipeline` | `data_engineering/data_transformation_pipeline` | 904 |
| Anomaly detection | `evaluation_monitoring/anomaly_detection` | `evaluation_monitoring/anomaly_detection` | 1104 |
| Monitoring/alerting | (none) | `evaluation_monitoring/monitoring_alerting` | 1205 |
| Computer vision | `images_computer_vision/object_detection` | `images_computer_vision/object_detection` | 204 |

---

## OASF Taxonomy Structure

### Top-Level Skill Categories (15)
1. Natural Language Processing [1]
2. Images / Computer Vision [2]
3. Audio [3]
4. Tabular / Text [4]
5. Analytical Skills [5]
6. Retrieval Augmented Generation [6]
7. Multi-modal [7]
8. Security & Privacy [8]
9. Data Engineering [9]
10. Agent Orchestration [10]
11. Evaluation & Monitoring [11]
12. DevOps / MLOps [12]
13. Governance & Compliance [13]
14. Tool Interaction [14]
15. Advanced Reasoning & Planning [15]

### Top-Level Domain Categories (24)
1. Technology [1]
2. Finance and Business [2]
3. Life Science [3]
4. Trust and Safety [4]
5. Human Resources [5]
6. Education [6]
7. Industrial Manufacturing [7]
8. Transportation [8]
9. Healthcare [9]
10. Legal [10]
11. Agriculture [11]
12. Energy [12]
13. Media and Entertainment [13]
14. Real Estate [14]
15. Hospitality and Tourism [15]
16. Telecommunications [16]
17. Environmental Science [17]
18. Government and Public Sector [18]
19. Research and Development [19]
20. Retail and E-commerce [20]
21. Social Services [21]
22. Sports and Fitness [22]
23. Insurance [23]
24. Marketing and Advertising [24]

---

## Implementation Checklist

- [ ] Update `src/web/.well-known/agent-registration.json` with valid OASF categories
- [ ] Upload new JSON to IPFS via Windows IPFS Desktop or Pinata
- [ ] Pin to Pinata cloud: `curl -X POST "https://api.pinata.cloud/pinning/pinByHash" ...`
- [ ] Deploy to Cloudflare Pages (`grokandmon-static` project)
- [ ] Update on-chain agentURI via `setAgentURI(4, "ipfs://NEW_CID")`
- [ ] Purge Cloudflare cache
- [ ] Wait for 8004scan re-index (minutes to hours)
- [ ] Verify no OASF warnings at https://8004scan.io/agents/monad/4

---

## Example Updated Metadata Snippet

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "GanjaMon",
  "description": "Autonomous agent for cultivation monitoring and crypto research; trading execution gated by human approval.",
  "image": "https://grokandmon.com/assets/MON_rasta_meme_logo.png",
  "services": [
    {
      "name": "Agent-to-Agent Protocol",
      "type": "a2a",
      "url": "https://grokandmon.com/a2a/v1",
      "endpoint": "https://grokandmon.com/a2a/v1",
      "version": "0.3.0",
      "skills": [
        "advanced_reasoning_planning/strategic_planning",
        "governance_compliance/risk_classification",
        "evaluation_monitoring/anomaly_detection"
      ],
      "domains": [
        "agriculture/precision_agriculture",
        "technology/internet_of_things/iot_devices",
        "technology/blockchain/defi"
      ]
    },
    {
      "name": "Model Context Protocol",
      "type": "mcp",
      "url": "https://grokandmon.com/mcp/v1",
      "endpoint": "https://grokandmon.com/mcp/v1",
      "version": "2025-06-18",
      "skills": [
        "data_engineering/data_transformation_pipeline",
        "images_computer_vision/object_detection",
        "evaluation_monitoring/monitoring_alerting"
      ],
      "domains": [
        "agriculture/agricultural_technology",
        "technology/internet_of_things/iot_networks",
        "industrial_manufacturing/automation"
      ]
    },
    {
      "name": "OASF Standard Record",
      "type": "oasf",
      "url": "https://grokandmon.com/.well-known/agent-registration.json",
      "endpoint": "https://grokandmon.com/.well-known/agent-registration.json",
      "version": "1.0.0",
      "skills": [
        "advanced_reasoning_planning/strategic_planning",
        "governance_compliance/risk_classification",
        "data_engineering/data_transformation_pipeline",
        "images_computer_vision/object_detection",
        "evaluation_monitoring/anomaly_detection",
        "evaluation_monitoring/monitoring_alerting"
      ],
      "domains": [
        "agriculture/precision_agriculture",
        "agriculture/agricultural_technology",
        "technology/internet_of_things/iot_devices",
        "technology/internet_of_things/iot_networks",
        "industrial_manufacturing/robotics",
        "industrial_manufacturing/automation",
        "technology/blockchain/defi",
        "finance_and_business/finance"
      ]
    },
    {
      "name": "Agent Wallet (Monad)",
      "type": "agentWallet",
      "endpoint": "eip155:143:0x870FE41c757fF858857587Fa3e68560876deF479",
      "url": "eip155:143:0x870FE41c757fF858857587Fa3e68560876deF479"
    }
  ],
  "x402Support": true,
  "active": true,
  "registrations": [
    {
      "agentId": 4,
      "agentRegistry": "eip155:143:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
      "chain": "monad"
    }
  ],
  "supportedTrust": ["reputation", "crypto-economic"],
  "pricing": {
    "x402": {
      "priceUSD": 0.001,
      "currency": "USDC",
      "chain": "base"
    }
  },
  "updatedAt": 1738905600
}
```

---

## References

- OASF Schema: https://schema.oasf.outshift.com
- OASF Skill Categories: https://schema.oasf.outshift.com/1.0.0/skill_categories
- OASF Domain Categories: https://schema.oasf.outshift.com/1.0.0/domain_categories
- Full taxonomy reference: `docs/OASF_VALID_CATEGORIES.md`
- 8004scan integration notes: `/home/wombatinux/.claude/projects/-mnt-c-Users-natha-sol-cannabis/memory/8004scan.md`
