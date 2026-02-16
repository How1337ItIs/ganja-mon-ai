# Telegram — Full Access

## CRITICAL: We Have Full Telegram API Access

We have **Telethon user API access** (not just bot API). This means we can:
- Talk to BotFather programmatically to manage ALL bots
- Read/send messages as the user account
- Join groups, manage members, create channels
- Do anything the Telegram mobile app can do

### Telethon Session

| Parameter | Value |
|-----------|-------|
| **Session file** | `/mnt/c/Users/natha/sol-cannabis/telegram_session.session` |
| **API ID** | `$TELEGRAM_API_ID` (in .env) |
| **API Hash** | `$TELEGRAM_API_HASH` (in .env) |
| **Phone** | `$TELEGRAM_PHONE` (in .env, session already authenticated) |

```python
# Quick Telethon usage — credentials from .env
from telethon import TelegramClient
import os
client = TelegramClient('telegram_session', int(os.getenv('TELEGRAM_API_ID')), os.getenv('TELEGRAM_API_HASH'))
await client.start()
```

## All 5 Bots (Owned by User)

| Bot | Username | Token | Role |
|-----|----------|-------|------|
| **Mon Garden Community** | @MonGardenBot | `$TELEGRAM_COMMUNITY_BOT_TOKEN` (in .env) | Community bot (main group) |
| **Mon Plant Bot** | @MonPlantBot | `$TELEGRAM_BOT_TOKEN` (in .env) | Plant monitoring (private/admin) |
| GanjaMonAI Bot | @GanjaMonAI_Bot | (get from BotFather if needed) | Unused |
| GanjaMonAI Bot | @GanjaMonAIBot | (get from BotFather if needed) | Unused |
| Ganja Mon Bot | @GanjaMonBot | (get from BotFather if needed) | Unused |

### Bot Roles (CRITICAL — Don't Mix These Up)

- **@MonGardenBot** = Community bot. Runs in main "Ganja $Mon AI" group. Rasta personality, all commands, community engagement. Code: `src/telegram/bot.py`. Service: `ganja-mon-bot.service`.
- **@MonPlantBot** = Plant monitoring bot. Private/admin channel only. Sensor alerts, grow updates. NOT for the main community group.

### Getting Bot Tokens via BotFather

```python
# Use Telethon to talk to BotFather — credentials from .env
from telethon import TelegramClient
import os
client = TelegramClient('telegram_session', int(os.getenv('TELEGRAM_API_ID')), os.getenv('TELEGRAM_API_HASH'))
await client.start()
await client.send_message('BotFather', '/mybots')
```

## Telegram Groups

| Group | Chat ID | Members | Bot |
|-------|---------|---------|-----|
| **Ganja $Mon AI** (Main) | `-1003584948806` | 174 | @MonGardenBot ACTIVE |
| Ganja Mon Warroom | `-5281228293` | 5 | Admin only |
| Ganja Mon community | `3526346421` | 12 | Small |

**NOTE**: The main group chat ID is `-1003584948806` (supergroup format with -100 prefix). The short form `3584948806` may not work with all API methods.

## Service Configuration

### Community Bot (@MonGardenBot)

```bash
# The community bot token must be in Chromebook .env as:
# TELEGRAM_COMMUNITY_BOT_TOKEN=$TELEGRAM_COMMUNITY_BOT_TOKEN

# Restart bot
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user restart ganja-mon-bot"

# Check bot logs
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "journalctl --user -u ganja-mon-bot -n 50 --no-pager"

# Check bot status
sshpass -p "$SSH_PASSWORD" ssh natha@chromebook.lan "systemctl --user status ganja-mon-bot"
```

## Bot Features

- Conversational AI (Grok-powered Rasta personality)
- Commands: `/status`, `/photo`, `/vibes`, `/strain`, `/token`, `/ca`, `/shill`, `/price`, `/suggest`, `/suggestions`, `/trading`, `/alpha`, `/brain`, `/signals`
- Spam/scam detection and roasting
- User profile tracking and memory (60+ OG profiles)
- Proactive engagement (occasionally joins conversations)
- Welcome messages for new members
- Deep member research (background Grok research every 6h)
- Live price lookups (DexScreener + CoinGecko)
- Community trade suggestions -> trading agent pipeline
