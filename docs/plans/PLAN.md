# Ganja Mon Telegram Chatbot - Implementation Plan

## Overview
A 24/7 AI chatbot that lives in the Telegram group, talks to people about $MON token and the plant, makes jokes, and has the Rasta personality.

## Architecture

### Where It Runs
**Chromebook server** - already always-on, has direct access to plant data API, sensor data, and webcam.

### Stack
- **Bot Framework**: `python-telegram-bot` (already in requirements.txt)
- **AI**: xAI Grok API (`grok-4.1-fast` for text, cheap and fast)
- **Plant Data**: Local FastAPI endpoints (`http://localhost:8000/api/...`)
- **Database**: SQLite (existing DB for conversation context)

### Bot Token
Need to create a bot via @BotFather on Telegram. User will need to do this step.

## Features

### 1. Conversational Chat (Core)
- Responds when mentioned (@bot) or when someone asks a question
- Uses Grok AI with Rasta personality system prompt
- Has context about Mon (live sensor data, growth stage, strain info)
- Makes jokes, uses Patois, stays in character

### 2. Plant Status Commands
- `/status` - Current plant conditions (temp, humidity, VPD, soil moisture)
- `/photo` - Latest webcam image of Mon
- `/vibes` - Grok's latest AI assessment/commentary
- `/strain` - Info about GDP Runtz strain

### 3. Token Info Commands
- `/token` - $MON token info, contract address, links
- `/website` - Links to grokandmon.com

### 4. Periodic Updates (Optional)
- Auto-post plant status every 4-6 hours
- Share when Grok makes interesting decisions (watering, etc.)

### 5. Fun Features
- Responds to weed/cannabis keywords with relevant commentary
- Roasts the wassie varmints if mentioned
- Random Rasta wisdom/quotes

## System Prompt (Telegram Bot)

Blend of:
- Grok AI personality (knowledgeable grower, chill)
- Rasta voice character (Patois, "mon", jokes, herb references)
- Token knowledge ($MON on Monad, grokandmon.com)
- Live plant data injected into context each message

## File Structure

```
src/telegram/
  bot.py          - Main bot loop (message handlers, commands)
  personality.py  - System prompt and AI response generation
  plant_data.py   - Fetches live data from local API
  config.py       - Bot settings, group IDs, rate limits
```

## Rate Limiting / Safety
- Don't respond to every single message (only mentions, commands, or relevant keywords)
- Max 1 response per 30 seconds to avoid spam
- Ignore messages from other bots
- Keep responses short (1-3 sentences for chat, longer for commands)

## Deployment
- Add as a systemd service on Chromebook (like grokmon)
- Or integrate into existing run.py as another subprocess
- Auto-restarts on crash

## Steps to Implement

1. User creates bot via @BotFather, gets bot token
2. Create `src/telegram/bot.py` with handlers
3. Create personality/system prompt
4. Wire up plant data fetching
5. Deploy to Chromebook
6. Add bot to Telegram group as admin
7. Test and iterate
