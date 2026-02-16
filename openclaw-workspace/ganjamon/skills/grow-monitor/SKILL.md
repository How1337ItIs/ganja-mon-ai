---
name: grow-monitor
description: Read sensors and control actuators via the Python HAL API (localhost:8000)
metadata:
  openclaw:
    emoji: "\U0001F331"
    requires:
      env:
        - HAL_BASE_URL
---

# Grow Monitor

## Overview

Interfaces with the Python Hardware Abstraction Layer (FastAPI on localhost:8000) to read sensors, control actuators, and monitor plant health. All hardware interaction goes through the HAL — never touch hardware directly.

## Commands

### `get_metrics`
Fetch current sensor readings.

**Usage:**
```
grow-monitor get_metrics
```

**Calls:**
```bash
curl -s ${HAL_BASE_URL}/api/sensors
```

**Returns:** Temperature, humidity, VPD, soil moisture, CO2 level, light status.

### `vpd_check`
Check VPD against growth stage targets.

**Usage:**
```
grow-monitor vpd_check
```

**Flow:**
1. `GET /api/sensors` → current VPD
2. `GET /api/grow/stage` → current stage + target VPD range
3. Compare and report: in-range, too high, or too low
4. Suggest adjustments if out of range

### `check_moisture`
Check soil moisture and determine if watering is needed.

**Usage:**
```
grow-monitor check_moisture
```

**Flow:**
1. `GET /api/sensors` → soil moisture %
2. `GET /api/grow/stage` and `GET /api/grow/parameters/{stage}` → stage-specific soil targets
3. Compare moisture against stage lower bound (+ small buffer)
4. Report: needs water now, monitor, or adequately moist

### `water`
Trigger watering via HAL API (SafetyGuardian enforced).

**Usage:**
```bash
grow-monitor water [--duration 2]
```

**Calls:**
```bash
curl -s -X POST ${HAL_BASE_URL}/api/actuator/control \
  -H "Content-Type: application/json" \
  -d '{"device": "water_pump", "action": "on", "duration": 2}'
```

**Recommended automation:** run `python3 ../scripts/gentle_daily_watering.py --apply` from the heartbeat loop.
It enforces a gentle daily cadence with stage-aware thresholds and records state in `data/gentle_watering_state.json`.

### `inject_co2`
Trigger CO2 injection via HAL API.

**Usage:**
```
grow-monitor inject_co2 [--duration 15]
```

**Calls:**
```bash
curl -s -X POST ${HAL_BASE_URL}/api/actuator/control \
  -H "Content-Type: application/json" \
  -d '{"device": "co2_injector", "action": "on", "duration": 15}'
```

### `growth_report`
Generate a comprehensive growth report for the past N hours.

**Usage:**
```
grow-monitor growth_report [--hours 24]
```

**Flow:**
1. `GET /api/sensors/history?hours=N` → sensor history
2. `GET /api/grow/history?hours=N` → decision history
3. `GET /api/grow/stage` → current stage info
4. Compile report with trends, averages, and anomalies

### `device_status`
Check current state of all actuator devices.

**Usage:**
```
grow-monitor device_status
```

**Calls:**
```bash
curl -s ${HAL_BASE_URL}/api/actuator/status
```

## HAL API Endpoints

```
GET  /api/sensors              → Current readings
GET  /api/sensors/history      → Historical data (?hours=N)
GET  /api/grow/stage           → Growth stage + targets
GET  /api/grow/history         → Decision history (?hours=N)
GET  /api/actuator/status      → Device states
POST /api/actuator/control     → Control devices
GET  /api/health               → System health
```

## Safety Notes

- SafetyGuardian is enforced at the API level — cannot be bypassed
- Minimum 4 hours between waterings
- Dark period protection: no actuator commands during lights-off
- Kill switch: operator can disable all actuators remotely
- Always use `lobster` approval pipeline for watering actions
