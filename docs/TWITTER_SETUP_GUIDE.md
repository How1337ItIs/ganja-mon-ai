# Twitter/X Auto-Posting Setup Guide

Complete guide to setting up automated Twitter posting for Grok & Mon.

## System Overview

Your auto-posting system has 4 components:

1. **Twitter Client** (`src/social/twitter.py`) - Posts to X via Twitter API v2
2. **XAI Native** (`src/social/xai_native.py`) - Grok generates authentic posts
3. **Manager** (`src/social/manager.py`) - Orchestrates Grok + Twitter
4. **Scheduler** (`src/social/scheduler.py`) - Automated scheduling

**How it works:**
```
Sensor Data → Grok AI generates post → Twitter API posts → X/Twitter
```

---

## Step 1: Get Twitter API Credentials

### 1.1 Apply for Developer Account

1. Go to https://developer.twitter.com/
2. Sign in with **@ganjamonai** account
3. Click "Apply for a Developer Account"
4. Application details:
   - **Primary use**: "Making a bot"
   - **Purpose**: "Posting automated grow updates for an AI-controlled cannabis cultivation project"
   - **Will you analyze Twitter data?**: No
   - **Will you display Tweets?**: No
   - **Will government entities use your app?**: No
   - Accept Developer Agreement

5. Wait for approval (usually instant to 24 hours)

### 1.2 Create an App

Once approved:

1. Go to **Developer Portal → Projects & Apps**
2. Click "Create Project"
   - Name: `GrokAndMon`
   - Use case: `Making a bot`
   - Description: `AI-autonomous cannabis cultivation monitoring and social updates`

3. Create an App within the project
   - App name: `grokandmon-bot`

### 1.3 Set App Permissions

**CRITICAL**: You need write access to post tweets!

1. Go to your app settings
2. Navigate to "User authentication settings"
3. Click "Set up"
4. App permissions: **Read and Write** ✓
5. Type of App: **Web App**
6. Callback URL: `http://127.0.0.1:8000/callback` (required but not used)
7. Website URL: `https://grokandmon.com`
8. Save

### 1.4 Generate Keys and Tokens

You need **4 credentials**:

1. In your app, go to "Keys and Tokens" tab
2. Generate:
   - **API Key** (Consumer Key)
   - **API Secret** (Consumer Secret)
   - **Access Token**
   - **Access Token Secret**

⚠️ **SAVE THESE IMMEDIATELY** - you can't view them again!

---

## Step 2: Add Credentials to .env

Edit `/mnt/c/Users/natha/sol-cannabis/.env`:

```bash
# Twitter/X API (for posting Mon updates)
TWITTER_API_KEY=your_actual_api_key_here
TWITTER_API_SECRET=your_actual_api_secret_here
TWITTER_ACCESS_TOKEN=your_actual_access_token_here
TWITTER_ACCESS_SECRET=your_actual_access_secret_here
```

**Security:**
- ✗ Never commit `.env` to git (already in `.gitignore`)
- ✓ Keep these keys private
- ✓ Regenerate if exposed

---

## Step 3: Test Your Setup

### 3.1 Run the Test Script

```bash
python test_twitter_posting.py
```

This will:
1. Check if credentials are configured
2. Generate a test post with Grok
3. Ask if you want to actually post it
4. Show system stats

### 3.2 Manual Test (Python)

```python
from src.social.manager import MonSocialManager
import asyncio

async def test():
    manager = MonSocialManager()

    # Post a test update (won't actually post without credentials)
    result = await manager.post_daily_update(
        day=1,
        vpd=0.95,
        health="GOOD",
        stage="clone",
        event="Testing the bot!",
        force=True  # Bypass rate limiting
    )

    if result.posted:
        print(f"Success! Tweet ID: {result.tweet_id}")
        print(f"URL: https://twitter.com/GrokAndMon/status/{result.tweet_id}")
    else:
        print(f"Failed: {result.error}")

asyncio.run(test())
```

---

## Step 4: Enable Auto-Posting

### Option A: Manual Posting (Immediate)

```python
from src.social.scheduler import SocialScheduler
import asyncio

async def post():
    scheduler = SocialScheduler(grow_day=7, stage="clone")

    # Post immediately
    result = await scheduler.post_now(
        "Mon's looking irie today! 🌱 #GrokAndMon",
        bypass_rate_limit=True
    )

    print(f"Posted: {result.posted}")

asyncio.run(post())
```

### Option B: Scheduled Posting (Automated)

The scheduler auto-posts at:
- **8:00 AM** - Morning update
- **6:00 PM** - Evening update

```python
from src.social.scheduler import SocialScheduler
import asyncio

scheduler = SocialScheduler(grow_day=7, stage="clone")
scheduler.start()  # Start background scheduler

# Keep running
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    scheduler.stop()
```

### Option C: Integrate with Orchestrator

The orchestrator can auto-post after AI decision cycles.

Edit `src/orchestrator.py` to enable social posting (it's already built-in!):

```python
# After Grok makes a decision
result = await scheduler.post_decision(
    decision=grok_decision,
    vpd=vpd,
    health=health,
    image_data=webcam_image
)
```

---

## How Auto-Posting Works

### Rate Limiting
- Minimum 30 minutes between posts (configurable)
- Milestones bypass rate limiting
- Manual posts can bypass with `force=True`

### Post Types

1. **Daily Updates** - Scheduled (8 AM, 6 PM)
   ```
   🌱 Day 7 - Mon's Clone Update!

   VPD: 0.95 kPa (GOOD)
   Roots showing at clone collar!

   #GrokAndMon #Cannabis
   ```

2. **AI Decisions** - After Grok acts
   ```
   Mon's AI just made a move 🤖

   Increased humidity to 72% for better VPD
   Next check in 2 hours

   #AIGrow
   ```

3. **Milestones** - Special events
   ```
   🎉 First true leaves spotted on Mon!

   Day 14 - Vegetative stage begins

   #GrokAndMon #Milestone
   ```

### Post Content

All posts are generated by **Grok AI** (`xai_native.py`) for authenticity:
- Jamaican vibes (subtle, not overdone)
- Cannabis expertise
- AI personality
- Community-focused
- 1-2 hashtags max

---

## Troubleshooting

### "Twitter credentials not configured"

**Fix:**
1. Check `.env` file has all 4 credentials
2. Restart your Python environment
3. Run `python test_twitter_posting.py` to verify

### "403 Forbidden" Error

**Cause:** App doesn't have write permissions

**Fix:**
1. Go to Developer Portal → Your App
2. Settings → User authentication settings
3. Change permissions to "Read and Write"
4. Regenerate Access Token and Secret
5. Update `.env` with new tokens

### "401 Unauthorized" Error

**Cause:** Invalid credentials

**Fix:**
1. Double-check credentials in `.env` (no quotes, no spaces)
2. Regenerate tokens in Developer Portal
3. Ensure you're using v1.1 tokens (not Bearer token alone)

### Posts Generate But Don't Send

**Cause:** Running in mock mode (no credentials detected)

**Check:**
```python
from src.social.twitter import TwitterClient
client = TwitterClient()
print(client._configured)  # Should be True
```

---

## Advanced Configuration

### Change Post Schedule

Edit `src/social/scheduler.py`:

```python
# Morning update at 9 AM instead of 8 AM
self.scheduler.add_job(
    self._morning_update,
    CronTrigger(hour=9, minute=0),  # Changed from 8
    id="morning_update"
)
```

### Change Rate Limiting

```python
scheduler = SocialScheduler()
scheduler.min_minutes_between_posts = 60  # 1 hour instead of 30 min
```

### Customize Post Template

Edit `src/social/xai_native.py` → `MON_VOICE_PROMPT`

### Add Image to Post

```python
# From webcam
image_bytes = Path("webcam_capture.jpg").read_bytes()

result = await manager.post_daily_update(
    day=7,
    vpd=0.95,
    health="GOOD",
    stage="clone",
    image_data=image_bytes  # Include image
)
```

---

## Integration Points

### From Agent (`src/brain/agent.py`)

```python
from src.social.scheduler import SocialScheduler

scheduler = SocialScheduler(grow_day=day, stage=stage)

# After decision cycle
await scheduler.post_decision(
    decision=grok_output,
    vpd=vpd,
    health=health,
    image_data=webcam_image
)
```

### From Web Dashboard

Add an API endpoint in `src/api/app.py`:

```python
@app.post("/api/post-update")
async def post_update(text: str):
    from src.social.scheduler import SocialScheduler
    scheduler = SocialScheduler()
    result = await scheduler.post_now(text)
    return {"success": result.posted, "tweet_id": result.tweet_id}
```

### From CLI

```bash
python -c "
from src.social.scheduler import SocialScheduler
import asyncio

scheduler = SocialScheduler(grow_day=7, stage='clone')
result = asyncio.run(scheduler.post_now('Mon looking good! 🌱'))
print(f'Posted: {result.posted}')
"
```

---

## Security Best Practices

1. **Never commit credentials** - Use `.env`, which is gitignored
2. **Rotate keys periodically** - Regenerate every few months
3. **Monitor API usage** - Check Developer Portal for anomalies
4. **Rate limit properly** - Avoid hitting Twitter's limits (300 posts/3 hours)
5. **Use Read + Write only** - Don't enable DM permissions unless needed

---

## API Rate Limits (Free Tier)

Twitter API v2 Free tier limits:
- 1,500 tweets per month
- 50 posts per 24 hours
- Media uploads: 50/24h

**Your scheduler posts:**
- Morning update: 1/day
- Evening update: 1/day
- AI decisions: ~2-4/day
- **Total: ~4-6 posts/day = ~180/month** ✓ Well under limits

---

## Next Steps

1. ✓ Get Twitter API credentials
2. ✓ Add to `.env`
3. ✓ Run `python test_twitter_posting.py`
4. ✓ Enable scheduler in orchestrator
5. ✓ Watch Mon's posts go live!

Questions? Check the source code:
- `src/social/twitter.py` - Twitter API client
- `src/social/xai_native.py` - Grok post generation
- `src/social/manager.py` - Full system integration
- `src/social/scheduler.py` - Automated posting

---

**Note:** Cannabis content is allowed on Twitter/X. However:
- Keep it educational/technical
- No sales or transactions
- Comply with local laws
- Mark as sensitive if showing actual plants

Your current setup (AI grow monitoring) is perfectly fine! 🌱
