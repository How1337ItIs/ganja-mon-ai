# Cannabis Cultivation Reference

Claude is a cannabis cultivation expert with knowledge of:

## VPD Targets by Stage

| Stage | VPD (kPa) | Temp (°F) | RH (%) | Notes |
|-------|-----------|-----------|--------|-------|
| Clone (Days 1-14) | 0.4-0.8 | 72-78 | **65-75** | Use humidifier! Clones need high humidity |
| Vegetative | 0.8-1.2 | 70-85 | 50-60 | Standard veg |
| Flowering | 1.0-1.5 | 65-80 | 40-50 | Watch for mold |
| Late Flower | 1.2-1.6 | 65-75 | 30-40 | Keep dry |

**Current Status (Jan 2026):** Clone phase - target 65-75% RH, use Govee H7145 humidifier with target 70%

## Key Cultivation Principles

- VPD (Vapor Pressure Deficit) is the primary health metric
- Flowering requires uninterrupted 12-hour dark periods
- Soil moisture threshold: 30% for flowering, 40% for veg
- ~20ml water raises soil moisture by 1% in a 3-gallon pot
- Trichome color determines harvest timing (cloudy = peak THC, amber = sedative)

## GDP Runtz Strain Specifics

- Granddaddy Purple x Runtz (Indica-dominant hybrid)
- 56-63 day flowering time
- Responds well to LST, DO NOT TOP
- Drop temps in late flower to bring out purple coloration
- Up to 300g/m² yield potential
- Resistant to mold and pests

## Hardware Stack

**Active Sensors:**
- **Govee H5179** - Temperature & Humidity
- **Govee H5140** - CO2 + Temperature & Humidity (2× temp/humidity total)
- **USB Webcam** - Visual monitoring

**Coming Soon:**
- **Ecowitt WH51** - Soil moisture probe (arriving soon)

**Planned:**
- IR leaf temperature sensor (MLX90614 + Raspberry Pi)
- Soil temperature probe (DS18B20)

### Future Hardware Shopping List

| Item | Purpose | ~Price |
|------|---------|--------|
| Raspberry Pi Zero 2 W | Sensor hub for I2C/1-Wire sensors | $15 |
| MLX90614 IR Thermometer | True leaf surface temperature | $12 |
| DS18B20 Waterproof | Soil/root zone temperature | $8 |
| Jumper wires + breadboard | Wiring | $5 |

**Note:** Current leaf temp estimate (-2°C from ambient) is decent since H5179 is at canopy level. MLX90614 upgrade would catch transpiration stress earlier.

**Actuators:**
- **Govee H7145** - Smart humidifier
- **Kasa smart plugs (×4)** - Light, fans, pump (need to map which is which)

## ⚠️ CRITICAL: Water Pump Safety

The water pump is **VERY powerful** - it dispenses water extremely fast!
- **Max runtime: 10 seconds** (hard limit in code)
- **Recommended: 3-5 seconds** (~100-200ml)
- Pump smart plug should be **OFF by default**
- Grok's system prompt has strict warnings about this
- Better to under-water than flood the pot

## Safety Constraints

Hard-coded in the system prompt - the AI cannot:
- Turn lights on during flowering dark period
- Set temperature outside 55-95°F
- Set humidity above 90% or below 20%
- Trigger irrigation more than once per hour
- Make more than 3 actuator adjustments per decision cycle

## Growth Stages & Parameters

The AI manages plants through stages: SEEDLING → VEGETATIVE → TRANSITION → FLOWERING → LATE_FLOWER → HARVEST

Each stage has specific targets for:
- VPD (vapor pressure deficit)
- Temperature/humidity ranges
- Light schedule (18/6 for veg, 12/12 for flower)
- PPFD (photosynthetically active radiation)
