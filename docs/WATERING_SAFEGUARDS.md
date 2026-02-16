# Watering Safeguards System

Implemented Feb 4, 2026 to prevent over/under watering due to "finniky" soil sensors.

## 1. Code-Level Protection (`WateringSafeguard` class)
Originally in `src/brain/agent_legacy.py` (archived). Production watering safeguards are enforced by `src/safety/guardian.py` (SafetyGuardian) in the orchestrator. Hard limits that the AI cannot override.

### Cooldowns
- **Standard Watering (>50ml):** 45-minute cooldown. Prevents rapid re-triggering if sensor doesn't update immediately.
- **Micro-Dosing (<50ml):** 15-minute cooldown. Allows for "micro-irrigation" strategy for clones.

### Daily Volume Limits
Hard caps on total water dispensed per calendar day:
- **Seedling:** 300ml
- **Clone:** 500ml
- **Late Flower:** 1000ml
- **Veg/Flower:** 1500ml

If the AI tries to water when a limit is reached or cooldown is active, the action is **BLOCKED** and logged as an error.

## 2. AI Logic Updates (`system_prompt.md`)
The AI has been explicitly instructed to handle sensor noise and drainage characteristics:

### "Finniky Sensor" Protocol & Reality Check
- **0% (Flatline):** Likely DISCONNECTED or Error. Check cable.
- **< 15% (Low):** **ALARM - REAL DRY.** Unless 0%, assume this is real and urgent.
- **~32% (The "Sweet Spot"):** Soil drains quickly to ~32% and holds there. **This is HEALTHY.**
  - **Do NOT panic water at 32%.** That is "Field Capacity" (moist but drained).
  - Only water if it drops **BELOW 30%** or for scheduled micro-doses.
- **Rapid Drop:** It is NORMAL for reading to drop from saturation (>80%) to ~32% quickly. Gravity is working.

### "Trust Visuals"
- If leaves are praying/perky, do NOT water, even if sensor says <15% (could be air pocket).
- If leaves are drooping + low sensor = WATER.

## 3. How to Monitor
- Check logs for "🚫 BLOCKED by Safeguard" messages.
- Monitor `episodic_memory.json` to see if AI is correctly identifying sensor noise.