# 🗺️ Sol Cannabis Implementation Plan

## Overview

This document outlines the phased approach to building a fully autonomous AI-controlled cannabis grow system.

---

## Phase 0: Foundation (Week 1-2)
**Goal**: Basic infrastructure and proof of concept

### 0.1 Development Environment
- [ ] Set up Python 3.11+ virtual environment
- [ ] Install core dependencies (anthropic, fastapi, rich, etc.)
- [ ] Configure Anthropic API key and test connection
- [ ] Set up Git repository with proper .gitignore

### 0.2 Hardware Procurement
- [ ] Order Raspberry Pi 4 (4GB+) + power supply + SD card
- [ ] Order temperature/humidity sensor (DHT22 or SHT31)
- [ ] Order USB webcam for initial vision testing
- [ ] Order smart plugs (2-3 Kasa HS103 for testing)

### 0.3 Baseline Claude Integration
- [ ] Create simple Claude API wrapper
- [ ] Test structured output parsing (JSON mode)
- [ ] Implement basic conversation memory
- [ ] Test image analysis with plant photos

**Deliverable**: Can send sensor data + image to Claude and receive structured recommendations

---

## Phase 1: Sensor Layer (Week 2-3)
**Goal**: Reliable environmental monitoring

### 1.1 Core Sensors
- [ ] Implement DHT22/SHT31 temperature/humidity reader
- [ ] Calculate VPD from temp/humidity readings
- [ ] Set up data logging to SQLite/JSON files
- [ ] Create sensor polling loop (every 1 minute)

### 1.2 Camera System
- [ ] Implement USB camera capture
- [ ] Set up timelapse capture (every 30 min)
- [ ] Create image storage with timestamps
- [ ] Test Claude vision API with captured images

### 1.3 Data Pipeline
- [ ] Design time-series data schema
- [ ] Implement rolling 7-day data retention
- [ ] Create basic data visualization (terminal/web)
- [ ] Set up alerting for out-of-range conditions

**Deliverable**: 24/7 environmental monitoring with camera captures and data logging

---

## Phase 2: Control Layer (Week 3-4)
**Goal**: Ability to control grow environment

### 2.1 Smart Plug Integration
- [ ] Implement python-kasa for Kasa smart plug control
- [ ] Create abstraction layer for plug on/off
- [ ] Test light on/off control
- [ ] Test fan on/off control

### 2.2 Light Control
- [ ] Implement light scheduling (18/6, 12/12 modes)
- [ ] Add sunrise/sunset dimming simulation (if LED supports)
- [ ] Create photoperiod state machine
- [ ] Test automated light transitions

### 2.3 Climate Control
- [ ] Implement exhaust fan control for temp/humidity
- [ ] Create VPD-based climate controller
- [ ] Add safety limits (max temp, min humidity)
- [ ] Test closed-loop climate control

**Deliverable**: Fully automated environmental control maintaining target VPD

---

## Phase 3: AI Brain (Week 4-6)
**Goal**: Claude-driven autonomous decision making

### 3.1 MCP Server Setup
- [ ] Create MCP server with FastMCP or custom implementation
- [ ] Define all sensor reading tools
- [ ] Define all actuator control tools
- [ ] Test tool calling from Claude

### 3.2 Decision Engine
- [ ] Design main Agent loop (observe → analyze → decide → act)
- [ ] Create growth stage state machine
- [ ] Implement decision logging with rationale
- [ ] Add safety overrides (human-in-the-loop for critical actions)

### 3.3 Prompt Engineering
- [ ] Create system prompt with cannabis cultivation knowledge
- [ ] Design stage-specific sub-prompts
- [ ] Implement context window management
- [ ] Test decision quality across scenarios

### 3.4 Memory & Learning
- [ ] Implement episodic memory (recent events)
- [ ] Create semantic memory (learned patterns)
- [ ] Store successful/failed intervention outcomes
- [ ] Enable cross-grow learning accumulation

**Deliverable**: Claude autonomously managing grow with human oversight

---

## Phase 4: Web Dashboard (Week 6-7)
**Goal**: Real-time monitoring and control interface

### 4.1 Backend API
- [ ] Create FastAPI REST endpoints
- [ ] Implement WebSocket for real-time updates
- [ ] Add authentication (basic API key)
- [ ] Create historical data endpoints

### 4.2 Frontend Interface
- [ ] Design responsive dashboard layout
- [ ] Implement real-time sensor gauges
- [ ] Add live camera feed
- [ ] Create growth stage timeline visualization

### 4.3 Control Panel
- [ ] Add manual override controls
- [ ] Implement growth stage transition buttons
- [ ] Create alert acknowledgment system
- [ ] Add AI decision log viewer

**Deliverable**: Professional web dashboard for monitoring and control

---

## Phase 5: Advanced Features (Week 7-8+)
**Goal**: Production-ready autonomous system

### 5.1 Advanced Sensing
- [ ] Add CO2 sensor integration
- [ ] Add PAR/PPFD meter integration
- [ ] Add soil moisture probe
- [ ] Add pH/EC probe (if hydro)

### 5.2 Advanced Vision
- [ ] Implement plant health detection
- [ ] Add growth stage auto-detection
- [ ] Add pest/deficiency identification
- [ ] Add trichome analysis (macro camera for harvest timing)

### 5.3 Notifications
- [ ] Add Discord/Telegram alerts
- [ ] Implement daily summary reports
- [ ] Create anomaly detection alerts
- [ ] Add weekly growth reports with photos

### 5.4 Strain Profiles
- [ ] Create strain profile YAML schema
- [ ] Import community strain data
- [ ] Test strain-specific adaptations
- [ ] Implement strain recommendation based on performance

**Deliverable**: Production-grade autonomous cannabis cultivation system

---

## Phase 6: Optional Extensions

### 6.1 Irrigation Automation
- [ ] Peristaltic pump integration
- [ ] Nutrient dosing (A/B + additives)
- [ ] pH adjustment automation
- [ ] Drain-to-waste or recirculating support

### 6.2 Multi-Zone Support
- [ ] Support multiple grow tents/zones
- [ ] Individual zone environmental control
- [ ] Shared resource scheduling
- [ ] Cross-zone AI coordination

### 6.3 Crypto Integration (Full Circle 🍅→🌿)
- [ ] Optional: Create $SOLCANNABIS token for lulz
- [ ] Live stream with token-gated access
- [ ] Community voting on grow decisions
- [ ] NFT certificates for harvests

---

## Hardware Shopping List

### Phase 0-2 Minimum Viable Hardware (~$400)

| Item | Price | Link |
|------|-------|------|
| Raspberry Pi 4 (4GB) | ~$55 | Amazon/PiShop |
| Pi Power Supply | ~$15 | Official |
| 32GB microSD | ~$10 | Samsung EVO |
| DHT22 Sensor | ~$8 | Amazon |
| USB Webcam | ~$30 | Logitech C270 |
| Kasa Smart Plugs (4-pack) | ~$25 | Amazon |
| Grow Tent 2x4 | ~$70 | AC Infinity |
| LED Light (SF1000) | ~$100 | Spider Farmer |
| Exhaust Fan (T4) | ~$80 | AC Infinity |
| Misc (wires, breadboard) | ~$20 | Amazon |

### Phase 3-5 Upgrades (~$300)

| Item | Price | Note |
|------|-------|------|
| SCD40 CO2 Sensor | ~$60 | Adafruit |
| PPFD Meter (app) | $0-20 | Photone app |
| Soil Moisture Probe | ~$15 | Generic |
| Better Camera | ~$50 | Logitech C920 |
| Humidifier | ~$40 | Levoit |
| Oscillating Fan | ~$25 | Clip fan |
| Additional Plugs | ~$30 | As needed |
| pH/EC Pen | ~$50 | BlueLab Truncheon |

---

## Success Metrics

### Phase 1 Success
- [ ] Sensors read correctly 99%+ of time
- [ ] Data logged continuously for 7+ days
- [ ] Camera captures clear images

### Phase 2 Success  
- [ ] Maintain target VPD ±0.2 kPa
- [ ] Light schedule precise to ±1 minute
- [ ] No temperature spikes beyond safe range

### Phase 3 Success
- [ ] Claude makes sensible decisions
- [ ] AI explains reasoning in logs
- [ ] Minimal human intervention needed

### Phase 4 Success
- [ ] Dashboard loads in <2 seconds
- [ ] Real-time data updates <5 second latency
- [ ] Mobile-responsive design works

### Overall Success
- [ ] Complete successful grow cycle (seed to harvest)
- [ ] AI-managed grow performs equal or better than manual
- [ ] System runs reliably for weeks without intervention

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API costs spike | Monitor usage, implement rate limiting |
| Hardware failure | Fail-safe modes (lights stay on, fans on) |
| Network outage | Local fallback controller |
| Claude makes bad decision | Human approval for critical actions |
| Plant dies | Start with clone/seedling, document learnings |
| Legal issues | Stay under 6 plants, stay private |

---

## Next Steps

1. **Complete Phase 0.1-0.3** - Get development environment ready
2. **Order Phase 0-2 hardware** - Lead time for shipping
3. **Start Phase 1 in parallel** - Begin sensor integration
4. **Create GitHub repo** - Open source from day 1

*Let's grow! 🌿*
