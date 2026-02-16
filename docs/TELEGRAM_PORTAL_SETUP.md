# Telegram Portal Setup - Anti-Bot Access
## Web Portal → CAPTCHA → Secure Invite Link

This creates a public portal where users prove they're human, then get a one-time invite link to your private Telegram.

---

## How It Works

```
User visits: grokandmon.com/telegram
   ↓
Solves hCaptcha (proves human)
   ↓
Backend generates one-time Telegram invite link
   ↓
User clicks link → Joins private Telegram
   ↓
Link expires (1 use or 24 hours)
```

**Result:** Only humans can join, bots can't spam

---

## Setup Steps

### 1. Get Telegram Bot Token

```bash
# Talk to @BotFather on Telegram
/newbot
# Name: Grok & Mon Portal Bot
# Username: grokmon_portal_bot

# BotFather gives you token like:
# 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Save it:
export TELEGRAM_BOT_TOKEN="your-token-here"
```

### 2. Get Your Chat ID

```bash
# Add your bot to your PRIVATE Telegram group
# Make it admin (need permission to create invite links)
# Send a message in the group, then:

curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"

# Find "chat":{"id":-1001234567890}
# Save it:
export TELEGRAM_CHAT_ID="-1001234567890"
```

### 3. Get hCaptcha Keys

```
1. Sign up: https://www.hcaptcha.com/
2. Add site: grokandmon.com
3. Get:
   - Site Key (public, goes in HTML)
   - Secret Key (private, goes in .env)
```

### 4. Configure Environment

```bash
# On Chromebook, add to .env:
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHAT_ID="-1001234567890"
HCAPTCHA_SITE_KEY="your-site-key"
HCAPTCHA_SECRET_KEY="your-secret-key"
```

### 5. Update HTML with Site Key

```javascript
// In telegram-portal.html line 83:
<div class="h-captcha" data-sitekey="YOUR_ACTUAL_SITE_KEY"></div>
```

### 6. Add Route to FastAPI

```python
# In src/api/app.py, add:
from .telegram_portal import router as telegram_router
app.include_router(telegram_router)

# Add static route:
@app.get("/telegram")
async def telegram_portal():
    return FileResponse("src/web/telegram-portal.html")
```

### 7. Deploy

```bash
./deploy.sh --restart
```

### 8. Test

```
Visit: https://grokandmon.com/telegram
Solve captcha
Get invite link
Join Telegram!
```

---

## Security Features

✅ **hCaptcha** - Industry standard, better than reCAPTCHA
✅ **One-time links** - Expire after 1 use
✅ **24-hour expiry** - Links auto-expire
✅ **Bot API generated** - Secure Telegram native links
✅ **No database needed** - Stateless
✅ **Rate limiting** - Already have this in app

---

## Alternative: Use Existing Bots

If you don't want to build custom:

**Option 1: @shieldy_bot**
```
1. Add to group as admin
2. /captcha simple
3. New users get CAPTCHA in group
4. Fails → kicked
```

**Option 2: Portal + @shieldy_bot**
```
1. Use custom portal (above)
2. ALSO add @shieldy_bot in group
3. Double protection!
```

---

## Recommended Setup

**For your launch TODAY:**

**Quick (5 minutes):**
```
1. Add @shieldy_bot to Telegram
2. Make it admin
3. /captcha simple
4. Done!
```

**Complete (30 minutes):**
```
1. Set up web portal (custom HTML above)
2. Get Telegram bot token
3. Get hCaptcha keys
4. Deploy portal
5. Share grokandmon.com/telegram link
```

**I recommend Quick for today's launch, Complete after launch!**

---

## Your Telegram Invite Flow

**Public announcement:**
> "Join di Grok & Mon Telegram! Verify yuhself at grokandmon.com/telegram - one click, no bots, pure irie vibes. 🌿"

**User experience:**
1. Clicks grokandmon.com/telegram
2. Sees: "Prove yuh human mon"
3. Solves simple captcha
4. Gets: "Here's yuh link - join now!"
5. Clicks → In Telegram ✅

**Bot experience:**
1. Tries to access portal
2. Can't solve captcha (it's a bot)
3. Never gets invite link
4. Can't join ❌

**Perfect!** 🎯

---

## Quick Start for Launch TODAY

```bash
# Option 1: Just use @shieldy_bot (5 min setup)
1. Open your Telegram group
2. Search @shieldy_bot
3. Add to group
4. Make admin
5. Type: /captcha simple
6. Done!

# Option 2: Build portal later
# (After launch when you have time)
```

**For your 4:20 PM launch, I recommend Option 1!**

Custom portal can be added tonight. 🚀
