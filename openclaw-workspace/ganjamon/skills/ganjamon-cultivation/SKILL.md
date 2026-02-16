---
name: ganjamon-cultivation
description: Monitor cannabis grow metrics and environmental data from IoT sensors
metadata:
  openclaw:
    emoji: 🌱
    requires:
      env:
        # Use the Python HAL for sensor reads and any device control.
        # This skill should not depend on a separate external URL or LLM key.
        - HAL_BASE_URL
      sensors:
        - govee_h5179
        - govee_h5140
        - ecowitt_gw1100
        - kasa_plugs
---

# GanjaMon Cultivation Skill

## Overview

The GanjaMon Cultivation skill monitors real-time environmental data from IoT sensors in the cannabis grow operation and provides cultivation advice based on the HAL metrics and system constraints.

## Current Grow

| Field | Value |
|-------|-------|
| **Strain** | Granddaddy Purple Runtz (GDP x Runtz) |
| **Stage** | Veg (Feb 2026) |
| **Expected Harvest** | Late April / Early May 2026 |
| **Legal Status** | California Prop 64 (6 plants max) |

## Hardware Sensors

### Govee H5179 (Temp/Humidity)
- **Purpose:** Environmental monitoring
- **Metrics:** Temperature (°F/°C), Humidity (%), VPD calculation
- **API:** Bluetooth via `src/hardware/govee.py`

### Govee H5140 (CO2)
- **Purpose:** CO2 monitoring
- **Sensor:** SCD4x NDIR sensor
- **Metrics:** CO2 ppm, optimal range 1000-1500 ppm during lights-on
- **API:** Bluetooth via `src/hardware/govee.py`

### Ecowitt GW1100 (Soil Moisture)
- **Purpose:** Soil moisture tracking
- **Metrics:** Volumetric water content (%)
- **API:** Local gateway via `src/hardware/ecowitt.py`

### Kasa Smart Plugs (Power Control)
- **Purpose:** Light/fan/pump control
- **Control:** On/off, scheduling
- **API:** `python-kasa` library via `src/hardware/kasa.py`

## Commands

### `get_metrics`
Retrieve current environmental metrics from all sensors.

**Usage:**
```
get_metrics [--sensor all|temp|co2|soil] [--format json|summary]
```

**Returns:**
- Current readings from all sensors
- VPD calculation (Vapor Pressure Deficit)
- Status alerts (out-of-range warnings)

### `vpd_check`
Calculate and assess current VPD (Vapor Pressure Deficit) for plant stage.

**Usage:**
```
vpd_check --stage veg|flower [--target-vpd 0.8-1.2]
```

**Returns:**
- Current VPD value
- Target VPD for growth stage
- Recommendations for temp/humidity adjustments

### `watering_advice`
Get AI-driven watering recommendations from Grok.

**Usage:**
```
watering_advice [--include-image]
```

**Flow:**
1. Gathers soil moisture, temp, humidity, recent watering history
2. Optionally captures webcam image of plants
3. Queries Grok AI with full context
4. Returns watering recommendation with confidence score

**Safety:** Subject to constraints in `WATERING_SAFEGUARDS.md` - will NOT water if recently watered or soil already saturated.

### `capture_plant_image`
Capture webcam image of plants via Chromebook camera.

**Usage:**
```
capture_plant_image [--annotate]
```

**Returns:**
- Image URL from FastAPI server
- Optional: Grok vision analysis of plant health

### `device_control`
Control Kasa smart plugs (lights, fans, pumps).

**Usage:**
```
device_control --device <name> --action on|off|toggle
```

**Devices:**
- `grow_light` - Main LED grow light
- `exhaust_fan` - Exhaust ventilation
- `oscillating_fan` - Circulation fan
- `water_pump` - Irrigation pump (CRITICAL: auto-shutoff after 30s)

### `growth_report`
Generate comprehensive grow report with all metrics and AI insights.

**Usage:**
```
growth_report [--period 24h|7d|30d] [--include-images]
```

**Returns:**
- Time-series graphs of temp/humidity/VPD
- Watering events log
- Growth stage progress
- Grok AI assessment of plant health
- Recommendations for next week

## VPD Targets

| Growth Stage | Target VPD | Temp Range | RH Range |
|--------------|-----------|------------|----------|
| **Seedling** | 0.4-0.8 kPa | 68-77°F | 65-70% |
| **Veg** | 0.8-1.2 kPa | 70-85°F | 55-70% |
| **Early Flower** | 1.0-1.4 kPa | 68-79°F | 50-60% |
| **Late Flower** | 1.2-1.6 kPa | 64-75°F | 45-50% |

Reference: `docs/CULTIVATION_REFERENCE.md`

## Watering Safety

**CRITICAL:** AI watering decisions follow strict safety rules (see `WATERING_SAFEGUARDS.md`):

1. **Minimum Interval:** 24 hours between waterings
2. **Soil Moisture Threshold:** Never water if soil > 60% moisture
3. **Max Duration:** Auto-shutoff pump after 30 seconds
4. **Manual Override Required:** For emergency watering outside normal schedule
5. **Logging:** All watering events logged with timestamp, reason, soil moisture

## Integration Notes

This skill integrates with:
- `ganjamon-social` - For daily plant updates on Moltbook/Twitter
- Grok AI - For vision analysis and cultivation advice
- FastAPI Server - Running on Chromebook at `http://chromebook.lan:8000`

## Monitoring & Alerts

Environmental alerts triggered when:
- **Temperature** outside 60-90°F range
- **Humidity** < 40% or > 75%
- **VPD** outside target range for growth stage
- **CO2** < 400 ppm or > 2000 ppm
- **Soil Moisture** < 20% (needs water) or > 80% (overwatered)

Alerts posted to:
- Internal logs: `/var/log/ganjamon/cultivation.log`
- Telegram: @MonGardenBot DMs to admin
- Moltbook: Activity feed (if critical)

## Error Handling

- **Sensor Offline:** Log warning, use last known value, alert after 15 minutes
- **API Timeout:** Retry 3x with exponential backoff
- **Grok AI Unavailable:** Fall back to rule-based decisions
- **Device Control Failure:** Alert immediately, log for manual intervention

---

**Skill Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** GanjaMon Autonomous Agent
