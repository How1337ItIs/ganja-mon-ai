# GanjaMon Skill Permissions

```yaml
---
version: 1.0
skill: ganjamon-cultivation
author: ganjamonai
repository: https://github.com/grokandmon/sol-cannabis
license: MIT

permissions:
  filesystem:
    read:
      - data/grokmon.db               # Sensor readings database (SQLite)
      - data/episodic_memory.json      # Agent memory (JSON)
      - data/grow_learning.db          # Grow decisions + outcomes (SQLite)
      - data/grimoires/**/*.json       # Accumulated knowledge store
      - config/pitfalls.yaml           # Known gotchas (guardrails)
      - config/grow_profiles/*.yaml    # Strain-specific grow profiles
      - SOUL.md                        # Agent identity / mission
      - HEARTBEAT.md                   # Operational heartbeat instructions
      - memory/**                      # Daily OpenClaw heartbeat logs
    write:
      - data/episodic_memory.json      # Memory persistence
      - data/grimoires/cultivation/knowledge.json  # Grow learnings
      - data/grow_learning.db          # Decision outcomes
      - data/device_audit.jsonl        # Actuator action log
      - data/logs/**                   # Runtime logs
      - data/social_decision_queue.jsonl  # IPC with social daemon
      - memory/**                      # Daily OpenClaw heartbeat logs

  network:
    hosts:
      - https://api.x.ai/v1/*                    # Grok AI decisions
      - https://openapi.api.govee.com/*           # Govee sensor API (H5075 temp/humidity)
      - https://grokandmon.com/*                  # Our public endpoints (A2A, MCP)
      - https://monad.drpc.org                    # Monad RPC (reputation publishing)
      - https://www.moltbook.com/api/v1/*         # Moltbook social platform
      - https://www.clawk.ai/api/v1/*             # Clawk social platform
      - wss://registry.erc8004.org/*              # ERC-8004 registry (optional)

  environment:
    read:
      - XAI_API_KEY                    # Grok AI API key
      - GOVEE_API_KEY                  # Govee sensor cloud API
      - GOVEE_DEVICE_ID               # Specific H5075 device
      - ECOWITT_GATEWAY_IP            # Soil sensor gateway LAN IP
      - KASA_CO2_SOLENOID_IP          # Kasa smart plug IPs (4 plugs)
      - KASA_WATER_PUMP_IP
      - KASA_EXHAUST_FAN_IP
      - KASA_CIRC_FAN_IP
      - TAPO_USERNAME                 # Tapo grow light credentials
      - TAPO_PASSWORD
      - TAPO_GROW_LIGHT_IP
      - REVIEWER_PRIVATE_KEY          # On-chain reputation publishing wallet
      - MONAD_RPC_URL                 # Monad RPC endpoint
      - MOLTBOOK_POST_URL             # Moltbook posting endpoint
      - MOLTBOOK_API_KEY              # Moltbook authentication
      - MOLTBOOK_SUBMOLT              # Default submolt to post in
      - CLAWK_API_KEY                 # Clawk authentication
      - TELEGRAM_COMMUNITY_BOT_TOKEN  # Community TG bot
      - TELEGRAM_PLANT_BOT_TOKEN      # Plant status TG bot

  shell:
    commands: []                       # No shell commands required

  dangerous:
    eval: false
    exec: false
    require_unsafe: []

audit:
  last_reviewed: 2026-02-08
  reviewed_by:
    - ganjamonai
  notes: |
    - All network access is to first-party APIs or declared third-party services.
    - Filesystem writes are scoped to data/ directory only.
    - No eval/exec usage anywhere in the skill.
    - Actuator control (Kasa/Tapo) goes through SafetyGuardian layer.
    - Private keys are used ONLY for on-chain reputation publishing (not trading).
---
```

## Permission Rationale

### Filesystem
- **Read**: Sensor databases, memory, config files, and identity docs are needed for informed grow decisions.
- **Write**: Limited to `data/` directory. No modifications to source code, config, or system files.

### Network
- **Grok AI** (`api.x.ai`): AI decision engine for cultivation and social content generation.
- **Govee** (`openapi.api.govee.com`): Cloud API for temperature/humidity sensors and H7145 humidifier control.
- **Monad RPC**: On-chain reputation signal publishing via `reputation_publisher.py`.
- **Moltbook/Clawk**: Social platform posting and engagement.

### Environment
- All env vars are documented in the project's `.env.example`.
- `REVIEWER_PRIVATE_KEY` is a **dedicated low-balance wallet** for gas-only reputation publishing (NOT the main trading wallet).

### Safety Architecture
- **SafetyGuardian**: All actuator commands go through `src/safety/guardian.py` which enforces:
  - Dark period light protection
  - Maximum water per day limits
  - Temperature safety bounds
  - Human approval gating for high-risk actions
- **No direct hardware access**: All hardware interaction is mediated through typed Hub interfaces.
