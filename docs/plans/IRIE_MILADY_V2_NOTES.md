# Irie Milady V2 — Planning Notes

**Status:** Pre-planning. V1 (420 NFTs on Scatter.art) must mint out first.

## V2 "Rebase" Concept

Drop 710 additional Irie Miladys:

| Allocation | Count | Mechanism |
|------------|-------|-----------|
| **Original holders airdrop** | 420 | Free to all V1 holders (1:1) |
| **Public sale** | 290 | New mint on Scatter.art (or equivalent) |
| **Total V2 supply** | 710 | |
| **Combined V1+V2 supply** | 1,130 | |

### Precondition
V1 (420/420) must fully mint out before V2 launches.

---

## V2 Feature Ideas

### Sensor-Enriched NFT Metadata

Each V2 Irie Milady bakes **live grow room sensor data** into its on-chain metadata at mint time. The NFT carries a permanent snapshot of the plant's state at the moment of creation.

**Metadata fields (proposed):**

```json
{
  "sensor_snapshot": {
    "vpd_kpa": 1.08,
    "temperature_f": 72.3,
    "humidity_pct": 58.0,
    "co2_ppm": 847,
    "soil_moisture_pct": 42.1,
    "grow_day": 45,
    "grow_stage": "vegetative",
    "light_status": "on",
    "strain": "Granddaddy Purple Runtz",
    "timestamp_utc": "2026-04-15T18:30:00Z"
  }
}
```

**Why this matters:**
- Provenance no other NFT collection can replicate — each piece is tied to a living organism's real-time state
- Creates a time-series across the collection — mint #1 might be early veg, #710 might be late flower
- Verifiable via on-chain grow log (ERC-8004 agent #4 already publishes sensor data to Monad)
- Collectors can say: "My Irie Milady was born when the plant was at peak VPD"
- Pairs with the existing narrative metadata (manifestation type, egregore function, etc.)

**Implementation:** Pull from `data/latest_reading.json` (already exists) at mint time. Inject into metadata JSON before IPFS upload. Could also include a SHA-256 hash pointing to the corresponding on-chain grow log entry for full verifiability.

### Other V2 Directions to Consider

- **Grow-stage-themed manifestations**: Different visual styles depending on whether the plant is in seedling/veg/flower/harvest at mint time
- **Dynamic metadata**: Post-mint sensor data updates (ERC-6551 token-bound accounts could enable this)
- **Cross-pollination with Paperclip Game**: V2 mint revenue or NFTs used as starting capital for the autonomous trading experiment
- **Community co-creation**: Let holders submit source images that get Ganjafied into V2 pieces

---

*Created: 2026-02-09. Pre-planning only — V1 mint-out is the gate.*
