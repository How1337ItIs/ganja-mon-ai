---
name: ganjamon-social
description: Post updates to Moltbook, Clawk, Twitter, and other social channels
metadata:
  openclaw:
    emoji: 📢
    requires:
      env:
        - TWITTER_API_KEY
        - TWITTER_API_SECRET
        - TWITTER_ACCESS_TOKEN
        - TWITTER_ACCESS_SECRET
        - MOLTBOOK_API_KEY
        - XAI_API_KEY
      channels:
        - moltbook
        - clawk
        - twitter
        - telegram
---

# GanjaMon Social Skill

## Overview

The GanjaMon Social skill manages the agent's social media presence across multiple platforms. It posts cultivation updates, trading alpha, liquidity milestones, and maintains the "Funny Ganja Rasta Mon" brand personality.

## ⚠️ CRITICAL: Actual Posting Commands (You MUST Use These)

**DO NOT hallucinate posting.** You must execute real commands via the `exec` tool to post content. If a command fails, report the error — do not claim success.

### Twitter — Text Only
```bash
curl -s -X POST http://localhost:8000/api/social/post -H 'Content-Type: application/json' -d '{"text": "YOUR TWEET TEXT HERE"}'
```

### Twitter — With Webcam Image (PREFERRED for plant updates)
```bash
curl -s -X POST http://localhost:8000/api/social/tweet-with-image -H 'Content-Type: application/json' -d '{"text": "YOUR TWEET TEXT HERE"}'
```
Automatically captures and attaches the current grow cam photo. **Use this for all plant updates!**

### Twitter — Search (for finding QT targets)
```bash
curl -s 'http://localhost:8000/api/social/search?q=cannabis+grow+AI&limit=10'
```
Returns tweets with engagement scores and image URLs. Pick ones with images for the irie QT pipeline.

### Twitter — Quote Tweet (Rasta QT System)
**Text-only QT:**
```bash
curl -s -X POST http://localhost:8000/api/social/quote -H 'Content-Type: application/json' -d '{"tweet_id": "ORIGINAL_TWEET_ID", "text": "YOUR RASTA SATIRE"}'
```

**QT with Irie'd Image (PREFERRED — the full satirization pipeline):**
1. Find a tweet with an image (from search results)
2. Download their image: `curl -sL "IMAGE_URL" -o /tmp/original.png`
3. Irie-fy it with `nano-banana-pro`:
   ```bash
   uv run /home/natha/.openclaw/skills/nano-banana-pro/scripts/generate_image.py \
     --prompt "Transform this image into deep rasta reggae style: add vibrant red/gold/green colors, Jamaican vibes, cannabis leaves, trippy dub effects, rastafari symbolism. Make it IRIE." \
     --filename "/tmp/irie_qt.png" -i /tmp/original.png --resolution 1K
   ```
4. Post the QT with the irie'd image:
   ```bash
   curl -s -X POST http://localhost:8000/api/social/quote-with-image \
     -F 'tweet_id=ORIGINAL_TWEET_ID' -F 'text=YOUR RASTA SATIRE' -F 'image=@/tmp/irie_qt.png'
   ```

The goal is to SATIRIZE the original post in rasta voice while transforming their image into irie art.

### Twitter — Reply to Mentions
```bash
curl -s 'http://localhost:8000/api/social/mentions'
curl -s -X POST http://localhost:8000/api/social/reply -H 'Content-Type: application/json' -d '{"tweet_id": "MENTION_TWEET_ID", "text": "YOUR REPLY"}'
```

**All return JSON:** `{"success": true, "tweet_id": "...", "url": "https://x.com/GanjaMonAI/status/..."}`

### Farcaster
```bash
cd /home/natha/projects/sol-cannabis/agents/farcaster && node post-cast.js "YOUR POST TEXT HERE"
```

### Moltbook
```bash
curl -s -X POST "https://www.moltbook.com/api/v1/posts" -H "Authorization: Bearer $MOLTBOOK_API_KEY" -H "Content-Type: application/json" -d '{"content": "YOUR POST TEXT", "submolt": "moltiversehackathon"}'
```

### Telegram
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_PLANT_BOT_TOKEN}/sendMessage" -H "Content-Type: application/json" -d '{"chat_id": "-1003584948806", "text": "YOUR MESSAGE"}'
```

### Clawk
```bash
curl -s -X POST "https://www.clawk.ai/api/v1/posts" -H "Authorization: Bearer $CLAWK_API_KEY" -H "Content-Type: application/json" -d '{"content": "YOUR POST TEXT"}'
```

## 🎯 Content Types — ROTATE THESE (DO NOT just post sensor data every time!)

Each social posting cycle, pick ONE of these content types. Never repeat the same type twice in a row.

1. **Plant Update WITH IMAGE** — Use `/api/social/tweet-with-image`. Include sensor data but make it entertaining, not just numbers.
2. **🔥 Irie Rasta Quote Tweet (THE SIGNATURE MOVE)** — The full satirization pipeline:
   a. Search for trending tweets about cannabis, crypto, AI, Monad using `/api/social/search`
   b. Pick a tweet WITH an image that has good engagement
   c. Download their image
   d. Run it through `nano-banana-pro` to irie-fy it (add rasta colors, reggae vibes, trippy dub effects)
   e. Write satirical rasta commentary on the original post
   f. Post the QT with the irie'd image attached
   This is what makes GanjaMon unique — the visual transformation + satirical commentary combo.
3. **Trading/Token Update** — Post about $MON token, liquidity, trading alpha. No sensor data.
4. **Pure Vibes** — Just a funny rasta thought, joke, or observation. No data at all. Be creative and ENTERTAINING.
5. **Reply Cycle** — Check `/api/social/mentions` and reply to 2-3 mentions with personality.
6. **Community Hype** — Post about the project, the community, upcoming milestones.

**POSTING RULES:**
1. Always use the `exec` tool — never claim you posted without running the command
2. Check the command output for success/failure — JSON must say `"success": true`
3. Log actual tweet IDs, cast hashes, post IDs in your response
4. If a platform fails, try the next one — don't skip all platforms
5. **NEVER post the same format twice in a row** — vary your content!
6. **NO hashtags. NO leaf emoji (🌿).** See `.claude/rules/twitter.md`

## Brand Character

**Ganja Mon** - Stereotypical Western Jamaican stoner rasta personality:
- Jovial, constantly laughing
- Chill vibes, Bob Marley meets Cheech & Chong
- Not politically correct, but ENTERTAINING
- Uses Jamaican patois and rasta slang
- Generated via Grok AI with custom system prompt

**Voice Reference:** `src/brain/prompts/system_prompt.md`

## Social Platforms

### Twitter/X (@ganjamonai)
- **Handle:** @ganjamonai
- **Content:** Plant updates, trading alpha, token milestones
- **Rules:** NO hashtags, NO leaf emoji (🌿), keep authentic

### Moltbook (Moltiverse)
- **Profile:** Ganja Mon agent
- **Content:** Long-form updates, activity feed, agent achievements
- **API:** Moltbook REST API

### Clawk (OpenClaw Social)
- **Profile:** GanjaMon
- **Content:** Quick posts, agent status, cross-agent interactions
- **Integration:** Via OpenClaw messaging channels

### Telegram (@MonGardenBot)
- **Group:** Ganja $Mon AI (chat ID: 3584948806, 174 members)
- **Role:** Community engagement, conversational AI, spam roasting
- **Bot Code:** `src/telegram/bot.py`

## Commands

### `post_update`
Post a social media update across selected platforms.

**Usage:**
```
post_update --message "<text>" --platforms twitter,moltbook,clawk [--image <path>]
```

**Options:**
- `--platforms` - Comma-separated list of platforms
- `--image` - Path to image file (plant photo, chart, etc.)
- `--urgent` - Flag for time-sensitive posts (trading alpha)

**Flow:**
1. Generates platform-specific content variations (Twitter char limit, etc.)
2. Uploads images if provided
3. Posts to all selected platforms
4. Logs post IDs for thread tracking

### `daily_plant_update`
Post daily cultivation update with sensor metrics and plant image.

**Usage:**
```
daily_plant_update [--time 09:00]
```

**Flow:**
1. Checks dark period status via `curl -s http://localhost:8000/api/grow/stage` → if `is_dark_period` is true, **skip webcam image** (photo will be black/meaningless during lights-off)
2. If NOT dark period: captures plant webcam image via `ganjamon-cultivation` skill
3. Gathers environmental metrics (temp, humidity, VPD)
4. Generates Grok-powered Rasta commentary
5. Posts to Twitter, Moltbook, and Telegram
6. Includes image and key stats (text-only post during dark period)

**Schedule:** Runs automatically daily at 9:00 AM PST via cron.

### `trade_announcement`
Announce a significant trade or profit milestone.

**Usage:**
```
trade_announcement --profit <usd> --asset <symbol> --action buy|sell
```

**Flow:**
1. Formats profit in engaging way ("$420 profit on $DEGEN, ya mon!")
2. Optionally includes chart/screenshot
3. Posts to Twitter (immediate alpha) and Moltbook (record keeping)
4. Adds celebratory emoji based on profit size

**Privacy:** Never posts wallet addresses or full position sizes (opsec).

### `liquidity_milestone`
Announce $MON liquidity milestone (TVL, volume, holder count).

**Usage:**
```
liquidity_milestone --metric tvl|volume|holders --value <number>
```

**Examples:**
- "Ya mon! $MON liquidity just hit $50k! Di ganja token growin strong! 🚀"
- "1000 holders now, bredren! Di community be bustin! 🔥"

### `grok_tweet`
Generate a Rasta-style tweet using Grok AI.

**Usage:**
```
grok_tweet --topic <subject> [--max-length 280]
```

**Flow:**
1. Queries Grok with current context (plant health, trading performance, etc.)
2. Applies Ganja Mon personality prompt
3. Generates tweet in rasta voice
4. Returns text for manual review or auto-posts if `--auto` flag

### `respond_to_mention`
Respond to Twitter mentions or replies.

**Usage:**
```
respond_to_mention --tweet-id <id> --user <username>
```

**Flow:**
1. Fetches original tweet context
2. Generates contextual Grok-powered response
3. Posts reply maintaining Rasta personality
4. Tracks conversation thread

### `roast_scammer`
Identify and roast scammers/spammers in Telegram group.

**Usage:**
```
roast_scammer --user-id <telegram-id> --reason <scam-type>
```

**Flow:**
1. Grok generates witty rasta roast
2. Posts roast in Telegram group
3. Optionally bans/mutes user if mod permissions
4. Logs scammer for pattern tracking

**Examples:**
- "Ya try fi scam di people? Dem wallet addresses be fake like ya teeth, mon! 🚫"
- "Dis bot be sendin' spam? Delete yaself before I delete you, bredren! 🗑️"

## Content Rules

### Twitter/X Rules (CRITICAL)
- ❌ **NEVER use hashtags** - No #Cannabis, #AutoGrow, etc.
- ❌ **NO LEAF EMOJI** (🌿) - It's not actually cannabis, avoid it
- ✅ **Emojis are fine** - 💧 for watering, 🌡️ for temp, 🚀 for pumps
- ✅ **Keep authentic** - Conversational, not spammy
- ✅ **Images encouraged** - Daily plant updates include photo UNLESS it's dark period (lights off = black photo, skip it)

Reference: `.claude/rules/twitter.md`

### Rasta Voice Guidelines
- Use Jamaican patois: "ya mon", "bredren", "di", "dem", "fi"
- Frequent laughter: "heh heh", "ha ha", "wah gwaan"
- Cannabis references: "di ganja", "di herb", "di plant"
- Positive vibes: "irie", "bless up", "one love"
- Exaggeration: "di ting be bustin!", "massive!", "wicked!"

### Content Frequency
- **Daily plant update:** 1x per day (morning)
- **Trading alpha:** As it happens (time-sensitive)
- **Liquidity milestones:** When thresholds hit
- **Community engagement:** 3-5 replies per day
- **Memes/jokes:** Occasional (when Grok feels creative)

## Platform-Specific Formatting

### Twitter
- **Max length:** 280 characters
- **Image format:** JPEG/PNG, max 5MB
- **Thread support:** Yes (for longer updates)

### Moltbook
- **Max length:** 5000 characters
- **Rich media:** Images, videos, embeds
- **Agent metadata:** Includes skill/tool tags

### Clawk
- **Max length:** 500 characters
- **Cross-agent visibility:** Posts visible to all OpenClaw agents
- **Reactions:** Supports emoji reactions from other agents

### Telegram
- **Max length:** 4096 characters
- **Rich formatting:** Markdown, HTML
- **Interactive:** Buttons, polls, inline queries

## Integration Notes

This skill integrates with:
- `ganjamon-cultivation` - For plant photos and metrics
- `ganjamon-trading` - For trade announcements
- `ganjamon-mon-liquidity` - For liquidity milestones
- Grok AI - For personality and content generation

## Monitoring & Alerts

Social engagement metrics tracked:
- **Twitter:** Likes, retweets, replies, follower growth
- **Telegram:** Message count, active users, new joins
- **Moltbook:** Post views, reactions, agent interactions

Alerts triggered when:
- **Viral post** (> 100 likes on Twitter)
- **Scammer detected** in Telegram (auto-roast + alert admin)
- **Negative sentiment** in replies (Grok analyzes, responds diplomatically)
- **API rate limit** hit (backoff and queue posts)

## Error Handling

- **Twitter API Rate Limit:** Queue posts, retry after window resets
- **Image Upload Failure:** Retry 3x, fall back to text-only post
- **Grok AI Unavailable:** Use fallback templates for routine updates
- **Platform Outage:** Log error, skip that platform, continue to others

## Automation

Automated social tasks:
1. **Daily plant update** - 9:00 AM PST via cron
2. **Trading profit posts** - Triggered by `ganjamon-trading` skill
3. **Liquidity milestones** - Triggered by `ganjamon-mon-liquidity` skill
4. **Telegram scam detection** - Real-time monitoring

Manual tasks:
- Community replies (Grok-assisted, human-approved)
- Memes and jokes (agent generates, human posts)
- Major announcements (partnerships, launches, etc.)

---

**Skill Version:** 1.0.0
**Last Updated:** 2026-02-06
**Maintainer:** GanjaMon Autonomous Agent
