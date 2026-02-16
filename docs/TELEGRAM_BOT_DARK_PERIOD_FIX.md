# Telegram Bot "Dark Period" Hallucination Fix

**Date:** February 10, 2026
**Status:** FIXED and deployed
**Severity:** Medium (bot giving wrong information to community)

## The Problem

The Telegram community bot ("Mon Garden Community") was incorrectly telling users that Mon was in her "dark period" at 10:35 AM and 12:20 PM PST — solidly in the light period on an 18/6 schedule.

Example messages:
- 10:35 AM: "Mon di GDP Runtz queen chillin in her **dark period** at 69% humidity"
- 12:20 PM: "Right now di herb whispering it's dat deep dark period fi Mon—midnight vibes"

When asked "what time do you think it is?" the bot responded it was "midnight vibes" — at 12:20 PM.

## Root Cause

**The Telegram bot's system prompt had ZERO time awareness.** Grok was never told what time it was.

### The Chain of (Non-)Events

1. `personality.py` builds the system prompt with `{plant_status}` placeholder
2. `plant_data.py::get_plant_summary()` fetches sensor data and grow stage
3. **Neither injected the current time** into Grok's context
4. Grok was left to **guess** the time based on sensor readings
5. When sensor readings showed low CO2 (0) or absent light data (Tapo plug was disconnected), Grok inferred "dark period" / "midnight"

### What Was NOT the Problem

- **`_sync_dark_period_config()`** in `orchestrator.py` — correctly disables dark period for seedling/18/6
- **`/api/grow/stage`** endpoint — correctly reports `is_dark_period: false` for seedling stage
- **`guardian.py::DarkPeriodConfig`** — only enables for flowering/12:12 stages
- **`agent_legacy.py` "ZZZ SLEEP MODE"** — cosmetic message between decision cycles, unrelated
- **Timezone issues** — Chromebook correctly uses PST

## The Fix

### File 1: `src/telegram/plant_data.py`

Added current time and `is_dark_period` truth from the API:

```python
# Current time (CRITICAL: Grok has no time awareness without this)
now = datetime.now()
parts.append(f"Current time: {now.strftime('%I:%M %p')} PST ({now.strftime('%A, %B %d, %Y')})")

# Growth stage + dark period truth
if stage:
    photoperiod = stage.get('photoperiod', '18/6')
    is_dark = stage.get('is_dark_period', False)
    parts.append(f"Photoperiod: {photoperiod} (lights on {'NO - DARK PERIOD' if is_dark else 'YES'})")
```

### File 2: `src/telegram/personality.py`

Added explicit time awareness instructions to SYSTEM_PROMPT:

```
## TIME AWARENESS (CRITICAL)
The current time is included in the Plant Status below. ALWAYS reference it when discussing
light/dark periods. NEVER guess what time it is — use the data provided.
The plant status also tells you if it's currently a dark period or not. Trust THAT — don't infer
dark period from sensor values like low CO2 or absent light readings.
```

## Architecture Notes

### How the Telegram Bot Generates Responses

The "Mon Garden Community" Telegram messages are generated via Grok AI (xAI API):

1. **Direct replies** (`handle_message` → `generate_response`) — when someone @mentions or triggers the bot
2. **Proactive comments** (`proactive_engagement` → `generate_proactive_comment`) — random jumps into conversation every ~10 min (30% chance)
3. **Periodic status** (`periodic_status` → `generate_status_message`) — grows updates every 4 hours

All three paths use `SYSTEM_PROMPT` from `personality.py` which includes `{plant_status}` from `get_plant_summary()`.

### Dark Period Logic Locations (Reference)

| Component | File | Purpose |
|-----------|------|---------|
| **API endpoint** | `src/api/app.py` line 807 | `/api/grow/stage` calculates `is_dark_period` from photoperiod |
| **Guardian** | `src/safety/guardian.py` line 132 | `DarkPeriodConfig.is_dark_period()` — only enabled for flowering |
| **Orchestrator sync** | `src/orchestrator.py` line 437 | `_sync_dark_period_config()` — enables only for flowering/12:12 |
| **Orchestrator decision** | `src/orchestrator.py` line 1158 | Passes `is_dark` to brain's decision prompt |
| **AI decision prompt** | `src/ai/prompts.py` line 82 | Injects "⚠️ DARK PERIOD ACTIVE" warning when true |
| **Telegram plant data** | `src/telegram/plant_data.py` line 59 | **NOW includes time + is_dark_period** |
| **Telegram personality** | `src/telegram/personality.py` line 56 | **NOW instructs Grok to use real time data** |

### Telegram Bot Service

- **Service:** `ganja-mon-bot.service` (user-level systemd)
- **Restart:** `systemctl --user restart ganja-mon-bot.service`
- **Logs:** `journalctl --user -u ganja-mon-bot.service -n 50 --no-pager`
- **Process:** `python -m src.telegram.bot`
- **NOT** a system service — it's under `~/.config/systemd/user/`

## Key Gotcha for Future

**Any AI-generated Telegram message is only as accurate as the context injected into Grok's prompt.** If you see the bot making factually wrong claims about the plant, check `get_plant_summary()` first — it's the ground truth pipeline for the Telegram bot's perception of reality.
