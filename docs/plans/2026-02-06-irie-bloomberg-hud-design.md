# Irie Bloomberg HUD Design

**Date**: 2026-02-06
**Purpose**: Hackathon demo video - visual window into the GanjaMon AI agent brain

## Aesthetic Direction

**"Irie Bloomberg Terminal"** - A maximalist trading terminal meets Jamaican rasta culture meets Monad blockchain purple. Dense information overload that feels alive, organic, and slightly chaotic - like looking into the synapses of an AI brain.

### Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Background | Deep Monad purple-black | `#0d0515` |
| Panel bg | Elevated purple | `#1a0a2e` |
| Rasta Green | Growth, success | `#2ecc40` |
| Rasta Gold | Alerts, value | `#ffd700` |
| Rasta Red | Warnings | `#ff4136` |
| Monad Purple | Accent glow | `#836ef9` |
| Text Primary | White | `#ffffff` |
| Text Muted | Gray | `#888888` |

### Typography

- Headers: Bold, condensed
- Metrics: Large, monospace for numbers
- Stream: Monospace terminal feel
- Labels: Small caps, letter-spaced

## Layout Structure

```
┌──────────────────────────────────────────────────────────────────────────┐
│ HEADER: Logo │ Day/Stage │ Strain │ $MON Price │ Gas │ Status │ Clock   │
├─────────────────────┬─────────────────────┬──────────────────────────────┤
│   SLOT 1: PLANT     │  SLOT 2: ENVIRON    │                              │
│   (rotates 30s)     │  (rotates 30s)      │   NEURAL ACTIVITY STREAM     │
├─────────────────────┼─────────────────────┤   (always scrolling)         │
│   SLOT 3: MARKET    │  SLOT 4: BRAIN      │                              │
│   (rotates 30s)     │  (rotates 30s)      │                              │
├─────────────────────┴─────────────────────┴──────────────────────────────┤
│ BOTTOM TICKER: Recent events scrolling horizontally                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Panel Definitions

### Slot 1: Plant (3 panels)
1. **Live Cam** (40%) - Full webcam with health overlay
2. **Growth Dashboard** - Height chart, milestones, days to harvest
3. **Timelapse** - Animated recent growth

### Slot 2: Environment (3 panels)
1. **Climate Command** (50%) - All gauges: temp, humidity, VPD, CO2, soil
2. **Device Control** - Light, fans, pump with states and runtimes
3. **Environmental History** - 24hr sparkline charts

### Slot 3: Market (3 panels)
1. **$MON Dashboard** (40%) - Price chart, volume, liquidity, trades
2. **Trading Desk** - Positions, P&L, pending orders
3. **Multi-Chain** - Monad + Base balances, bridge status

### Slot 4: Brain (3 panels)
1. **Alpha Radar** (40%) - Animated scanner, recent signals
2. **Strategy Center** - Learning log, backtest stats
3. **Social Command** - Twitter posts, engagement

## Neural Activity Stream

Right column, always live. Event types with colors:

| Type | Icon | Color |
|------|------|-------|
| Thinking | 🧠 | Purple `#836ef9` |
| Signal | 📡 | Gold `#ffd700` |
| Action | ✅ | Green `#2ecc40` |
| Learning | 📊 | Cyan `#00d4ff` |
| Alert | ⚠️ | Red `#ff4136` |
| Decision | 🎯 | White |
| Social | 💬 | Blue `#1da1f2` |
| Plant | 🌱 | Leaf `#3d9970` |
| Trade | 💰 | Gold flash |
| Prediction | 🔮 | Soft purple |

## Animation Specs

- Panel transitions: 300ms fade + 0.98→1.0 scale
- Staggered rotation: Slots change at +0, +8, +15, +23 seconds
- Neural stream: Items appear every 2-4s, scroll down, fade out
- Bottom ticker: 50px/sec horizontal scroll
- Gauge fills: Smooth CSS transitions
- Purple glow pulse on transitions

## Technical Approach

- Single HTML file, vanilla JS
- CSS animations only (GPU accelerated)
- Staggered API polling (not simultaneous)
- Target 30fps
- Pause animations when tab hidden
- Works on old Chromebook

## Files

- `src/web/hud.html` - Complete HUD implementation
- Uses existing APIs from `src/api/app.py`
