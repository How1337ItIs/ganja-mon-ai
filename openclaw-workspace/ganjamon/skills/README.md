# GanjaMon Agent Skills

This directory contains OpenClaw skill definitions for the GanjaMon autonomous agent.

## Available Skills

| Skill | Emoji | Description |
|-------|-------|-------------|
| **ganjamon-trading** | 🍃 | Execute alpha hunting and trading operations on Monad/Base chains |
| **ganjamon-cultivation** | 🌱 | Monitor cannabis grow metrics and environmental data from IoT sensors |
| **ganjamon-mon-liquidity** | 💧 | Monitor $MON token liquidity across Monad and Base chains |
| **ganjamon-social** | 📢 | Post updates to Moltbook, Clawk, Twitter, and other social channels |

## Skill Structure

Each skill follows the OpenClaw framework conventions:

```markdown
---
name: skill-name
description: Short description
metadata:
  openclaw:
    emoji: 🔧
    requires:
      env: [ENV_VAR_1, ENV_VAR_2]
      tools: [tool_1, tool_2]
---

# Skill Name

## Overview
...

## Commands
...
```

## Usage

Skills are invoked via OpenClaw's skill system:

```bash
# List available skills
openclaw skills list

# Invoke a skill
openclaw skill ganjamon-trading alpha_scan --chain monad
```

## Integration

These skills integrate with:
- **OpenClaw Framework** - Core agent platform
- **Moltbook** - Social platform for AI agents
- **Chromebook Server** - IoT hardware and sensors
- **Grok AI** - Decision-making and personality
- **Wormhole NTT** - Cross-chain bridge for $MON

## Related Documentation

- `../SOUL.md` - Agent core personality and purpose
- `../AGENTS.md` - A2A (Agent-to-Agent) configuration
- `../TOOLS.md` - Available tools and capabilities
- `../HEARTBEAT.md` - Autonomous execution loop
- `../IDENTITY.md` - Agent identity and credentials

---

**Last Updated:** 2026-02-06
**OpenClaw Version:** 2.0+
