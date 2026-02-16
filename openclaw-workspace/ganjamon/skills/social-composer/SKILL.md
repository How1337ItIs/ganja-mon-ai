---
name: social-composer
description: Generate Rasta-voice content for all platforms using gemini + nano-banana-pro skills
metadata:
  openclaw:
    emoji: "\U0001F3A4"
    requires:
      env:
        - GEMINI_API_KEY
---

# Social Composer

## Overview

Generates platform-specific social content in the GanjaMon Rasta voice. Uses `gemini` skill for text generation and `nano-banana-pro` for image creation. Formats content for each platform's constraints.

## Commands

### `compose`
Generate a social post in Rasta voice.

**Usage:**
```
social-composer compose --topic "<subject>" --platform twitter|moltbook|farcaster|clawk|telegram [--with-image]
```

**Flow:**
1. Gather fresh data from `grow-monitor` and `trading-signals` if topic is plant/trade related
2. Use `gemini` skill to generate Rasta-voice content:
   - Apply personality from `SOUL.md`
   - Format for target platform's constraints
   - Include relevant sensor data or trading metrics
3. If `--with-image`, use `nano-banana-pro` to generate/edit plant image
4. Return formatted post ready for platform-specific poster skill

### `ganjafy`
Transform any text into Rasta voice.

**Usage:**
```
social-composer ganjafy --text "<input text>"
```

**Flow:**
1. Send to `gemini` with Rasta personality prompt
2. Transform formal/technical text into Jamaican patois
3. Add laughter, slang, vibes
4. Return ganjafied text

### `daily_brief`
Generate comprehensive daily update for all platforms.

**Usage:**
```
social-composer daily_brief
```

**Flow:**
1. `grow-monitor get_metrics` → current sensor data
2. `trading-signals portfolio` → P&L summary
3. `weather "Los Angeles"` → outdoor conditions
4. Generate 5 platform-specific posts (Twitter, Moltbook, Farcaster, Clawk, Telegram)
5. Generate plant image with `nano-banana-pro` (overlay sensor readings)
6. Return all posts ready for distribution

### `generate_image`
Create a plant-themed image using Gemini 3 Pro.

**Usage:**
```
social-composer generate_image --prompt "<description>" [--edit <source_image>]
```

**Flow:**
1. Use `nano-banana-pro` skill (Gemini 3 Pro image gen/edit)
2. If editing, overlay sensor data on plant photo
3. Return image path/URL

## Platform Formatting

| Platform | Max Length | Image | Special |
|----------|-----------|-------|---------|
| Twitter | 280 chars | JPEG/PNG 5MB | NO hashtags, NO leaf emoji |
| Moltbook | 5000 chars | URL | Submolt: `moltiversehackathon` |
| Farcaster | 1024 bytes | URL | LONG_CAST format |
| Clawk | 500 chars | URL | Cross-agent visible |
| Telegram | 4096 chars | Any | Markdown formatting |

## Voice Rules

- Jamaican patois: "ya mon", "bredren", "fi di plants", "nuff respect"
- Frequent laughter: "heh heh", "ha ha ha", "bwahahaha"
- Cannabis references: "di ganja", "di herb", "di plant dem"
- NO hashtags on any platform
- NO leaf emoji on any platform
- Chill vibes but sharp data underneath
