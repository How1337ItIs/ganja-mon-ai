# OASF Valid Categories Reference

**Source:** https://schema.oasf.outshift.com (v1.0.0)
**Date:** 2026-02-07
**Status:** Official OASF taxonomy

## Summary

The Open Agentic Schema Framework (OASF) defines:
- **15 skill categories** containing 100+ distinct skills
- **24 domain categories** containing 110+ distinct domains

## Valid Skill Categories

Skills should reference the **full path** format: `category/subcategory/skill_name`

### 1. Natural Language Processing [1]
- Text understanding and generation
- Retrieval, classification, ethical interaction

### 2. Images / Computer Vision [2]
Skills:
- `images_computer_vision/object_detection` [204]
- `images_computer_vision/image_segmentation`
- `images_computer_vision/depth_estimation`

### 3. Audio [3]
- Speech recognition, text-to-speech

### 4. Tabular / Text [4]
- Data classification and regression

### 5. Analytical Skills [5]
- Mathematical reasoning, coding, theorem proving

### 6. Retrieval Augmented Generation [6]
- Information retrieval and synthesis

### 7. Multi-modal [7]
- Cross-modality transformations

### 8. Security & Privacy [8]
Skills:
- `security_privacy/vulnerability_analysis` [802]
- `security_privacy/privacy_risk_assessment` [804]

### 9. Data Engineering [9]
Skills:
- `data_engineering/data_cleaning` [901]
- `data_engineering/feature_engineering` [903]
- `data_engineering/data_transformation_pipeline` [904]

### 10. Agent Orchestration [10]
- Multi-agent coordination, task decomposition, negotiation

### 11. Evaluation & Monitoring [11]
Skills:
- `evaluation_monitoring/anomaly_detection` [1104]
- `evaluation_monitoring/monitoring_alerting` [1205]

### 12. DevOps / MLOps [12]
- Infrastructure, deployment, CI/CD, model versioning

### 13. Governance & Compliance [13]
Skills:
- `governance_compliance/risk_classification` [1304]

### 14. Tool Interaction [14]
- API understanding, workflow automation, script integration

### 15. Advanced Reasoning & Planning [15]
Skills:
- `advanced_reasoning_planning/strategic_planning` [1501]
- `advanced_reasoning_planning/long_horizon_reasoning` [1502]
- `advanced_reasoning_planning/hypothesis_generation` [1504]

---

## Valid Domain Categories

Domains should reference the **full path** format: `category/subcategory/domain_name`

### 1. Technology [1]
Domains:
- `technology/cloud_computing` [105]
- `technology/blockchain` [109]
- `technology/internet_of_things` [101]
  - `technology/internet_of_things/iot_devices` [10101]
  - `technology/internet_of_things/iot_security` [10102]
  - `technology/internet_of_things/iot_networks` [10103]
  - `technology/internet_of_things/industrial_iot` [10105]
- `technology/blockchain/defi` [10902] — "Decentralized Finance (DeFi)"

### 2. Finance and Business [2]
Domains:
- `finance_and_business/banking` [201]
- `finance_and_business/finance` [202]

### 3. Life Science [3]
Domains:
- `life_science/biotechnology` [301]
- `life_science/bioinformatics` [304]

### 4. Trust and Safety [4]

### 5. Human Resources [5]

### 6. Education [6]

### 7. Industrial Manufacturing [7]
Domains:
- `industrial_manufacturing/automation` [701]
- `industrial_manufacturing/robotics` [702]

### 8. Transportation [8]
Domains:
- `transportation/automotive` [802]
- `transportation/autonomous_vehicles` [806]

### 9. Healthcare [9]

### 10. Legal [10]

### 11. Agriculture [11]
Domains:
- `agriculture/agricultural_technology` [1101]
- `agriculture/precision_agriculture` [1104]

### 12. Energy [12]

### 13. Media and Entertainment [13]
Domains:
- `media_and_entertainment/broadcasting` [1301]

### 14. Real Estate [14]

### 15. Hospitality and Tourism [15]

### 16. Telecommunications [16]
Domains:
- `telecommunications/iot_connectivity` [1602]

### 17. Environmental Science [17]
Domains:
- `environmental_science/climate_science` [1701]

### 18. Government and Public Sector [18]
Domains:
- `government_and_public_sector/civic_engagement` [1801]

### 19. Research and Development [19]

### 20. Retail and E-commerce [20]

### 21. Social Services [21]
Domains:
- `social_services/case_management` [2101]
- `social_services/child_and_family_services` [2102]

### 22. Sports and Fitness [22]
Domains:
- `sports_and_fitness/athletic_training` [2201]

### 23. Insurance [23]
Domains:
- `insurance/actuarial_science` [2301]
- `insurance/claims_processing` [2302]

### 24. Marketing and Advertising [24]
Domains:
- `marketing_and_advertising/advertising` [2401]
- `marketing_and_advertising/brand_management` [2402]

---

## Recommended Mapping for GanjaMon

Based on our agent's capabilities (IoT horticulture, trading/DeFi, community management, sensor data, AI decision-making):

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

## Key Differences from Our Old Categories

### OLD (Invalid) Skills
- ❌ `advanced_reasoning_planning/strategic_planning` — **VALID** (keep)
- ❌ `decision_making` — NOT a valid skill path
- ❌ `risk_assessment` — Should be `governance_compliance/risk_classification`
- ❌ `data_engineering/data_transformation_pipeline` — **VALID** (keep)
- ❌ `images_computer_vision/object_detection` — **VALID** (keep)
- ❌ `evaluation_monitoring/anomaly_detection` — **VALID** (keep)

### OLD (Invalid) Domains
- ❌ `agriculture/precision_agriculture` — **VALID** (keep)
- ❌ `agriculture/agriculture_optimization` — NOT a valid domain
- ❌ `iot/sensor_networks` — Should be `technology/internet_of_things/iot_networks`
- ❌ `iot/automation` — Should be `industrial_manufacturing/automation`
- ❌ `finance/crypto` — Should be `technology/blockchain/defi`
- ❌ `finance/trading` — Should be `finance_and_business/finance`
- ❌ `technology/ai_decision_systems` — NOT a valid domain

### Corrections Needed
1. **Skills:** Replace `risk_assessment` → `governance_compliance/risk_classification`
2. **Domains:**
   - Replace `agriculture/agriculture_optimization` → `agriculture/agricultural_technology`
   - Replace `iot/sensor_networks` → `technology/internet_of_things/iot_networks`
   - Replace `iot/automation` → `industrial_manufacturing/automation`
   - Replace `finance/crypto` → `technology/blockchain/defi`
   - Replace `finance/trading` → `finance_and_business/finance`
   - Remove `technology/ai_decision_systems` (not valid)

---

## Usage Notes

1. **Full paths required:** Skills and domains use slash-separated paths like `category/subcategory/item`
2. **Numeric IDs available:** Each has a numeric identifier (e.g., `[1104]`) but strings are preferred
3. **Multiple valid:** Agents can declare multiple skills and domains
4. **Case sensitive:** Use exact case as shown in taxonomy
5. **No custom categories:** Must use predefined OASF categories only

---

## References

- OASF Schema: https://schema.oasf.outshift.com
- Skill Categories: https://schema.oasf.outshift.com/1.0.0/skill_categories
- Domain Categories: https://schema.oasf.outshift.com/1.0.0/domain_categories
- Version: 1.0.0
