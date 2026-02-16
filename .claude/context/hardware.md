# API & Hardware Integration

## xAI Grok API

- Base URL: `https://api.x.ai/v1`
- Models: `grok-4-1-fast-non-reasoning` (text), `grok-4` (vision)
- Authentication: Bearer token via `XAI_API_KEY`

### UNSUPPORTED PARAMETERS (CRITICAL — causes 400 errors)
- **`presence_penalty`** — NOT supported by `grok-4-1-fast-non-reasoning`. NEVER send this parameter.
- **`frequency_penalty`** — Also NOT supported (as of Feb 2026). NEVER send this parameter.
- Both cause silent 400 errors that surface as "brain too foggy" fallbacks in the Telegram bot.
- When in doubt, only send: `model`, `messages`, `max_tokens`, `temperature`
- This has broken the Telegram bot THREE times — always check xAI model compatibility before adding API params

## Hardware Sensors

| Device | Purpose | Code |
|--------|---------|------|
| **Govee H5179** | Temp/humidity | `src/hardware/govee.py` |
| **Govee H5140** | CO2 (SCD4x NDIR sensor) | `src/hardware/govee.py` |
| **Ecowitt GW1100** | Soil moisture | `src/hardware/ecowitt.py` |
| **Kasa smart plugs** | Power control | `src/hardware/kasa.py` (via `python-kasa`) |

## Key Files

| File | Purpose |
|------|---------|
| `src/orchestrator.py` | Main grow agent loop (sensors + AI decisions + safety) |
| `src/ai/brain.py` | Grok AI decision engine (used by orchestrator) |
| `src/ai/tools.py` | 14 grow tools (water, CO2, email, Allium, etc.) |
| `src/brain/agent_legacy.py` | Archived standalone agent (not used in production) |
| `src/mcp/tools.py` | MCP tool definitions for external agents (26 tools) |
| `src/api/app.py` | FastAPI web server (82+ endpoints) |
| `rasta-voice/rasta_live.py` | Voice transformation pipeline |
