# Twitter Auto-Posting Implementation Plan

## Current Status: What Exists ✅

Your Twitter system is **90% built**! Here's what's already complete:

### 1. Voice & Personality ✅
**Location:** `src/brain/prompts/system_prompt.md`
- Grok's Jamaican AI persona fully defined
- Catchphrases: "Grok grows your herb, mon", "Irie vibes only"
- Tone: Laid-back but professional, cannabis culture references
- Social posts included in agent responses: `"social_post": "witty tweet"`

### 2. Content Generation ✅
**Location:** `src/social/xai_native.py`
- `generate_mon_post()` - Grok generates posts with:
  - Day, stage, VPD, health, special events
  - Jamaican vibes, natural "mon" usage
  - 1-2 hashtags, max 280 chars
  - Temperature: 0.8 (creative)
- Fallback posts if API fails

### 3. Engagement Tools ✅
**Location:** `src/social/xai_native.py` & `manager.py`
- `find_engagement_opportunities()` - Searches #AICannabis, #Monad, #AutonomousGrow, #AIGrow
- `analyze_sentiment()` - Analyzes X sentiment around topics
- `generate_reply()` - Creates replies in Mon's voice

### 4. Scheduler Framework ✅
**Location:** `src/social/scheduler.py`
- Morning update: 8 AM
- Evening update: 6 PM
- Post-decision auto-tweets
- Milestone posts (bypass rate limiting)
- Queue management
- Rate limiting: 30 min between posts

### 5. Compliance System ✅
**Location:** `src/social/compliance.py`
- **Posting windows** optimized for global Crypto Twitter:
  - 5-6 AM PST = Catches US East + Europe lunch
  - 9-10 AM PST = PEAK (US lunch + Europe evening)
  - 1-2 PM PST = US afternoon + Asia waking
  - 5-6 PM PST = US evening + Asia morning
  - 9-10 PM PST = US night + Asia afternoon
- **Rate limits**: Max 4 posts/day, min 4 hours between
- **Post validation**: 50-280 chars, #GrokAndMon required, max 3 hashtags
- **Tracking**: Persists history to disk

### 6. Post Templates ✅
**Location:** `src/social/compliance.py`
- 10+ preset templates for variety
- Health emojis: 🌿 (EXCELLENT), ✅ (GOOD), ⚠️ (FAIR), etc.
- Morning/evening/milestone-specific templates
- Auto-truncation to 280 chars

### 7. Social Campaign Strategy ✅
**Location:** `docs/SOCIAL_CAMPAIGN.md`
- Complete pre-launch to $1B roadmap
- Daily content calendar
- Weekly themes (#MonitorMonday, #TechTuesday, etc.)
- Engagement rules (DO/DON'T)
- Influencer strategy
- Crisis response playbook

---

## What Needs To Be Done: The Final 10% 🔧

### Task 1: Wire Compliance Into Scheduler
**Goal:** Make scheduler respect posting windows and rate limits

**Current issue:**
- `scheduler.py` has its own rate limiting (30 min)
- Doesn't use `compliance.py` posting windows or limits
- No integration with `PostingTracker`

**What to do:**
```python
# In scheduler.py, replace basic rate limiting with:
from .compliance import XComplianceConfig, PostingTracker

class SocialScheduler:
    def __init__(self):
        self.tracker = PostingTracker()  # Add tracker

    def _can_post(self) -> bool:
        # Replace current method with:
        can_post, reason = self.tracker.can_post_now()
        if not can_post:
            logger.info(f"Cannot post: {reason}")
        return can_post

    async def post_now(self, content, ...):
        # After successful post:
        if result.posted:
            self.tracker.record_post(result.tweet_id, content)
```

**Files to edit:**
- `src/social/scheduler.py` - lines 99-106, 254-260

---

### Task 2: Add Visual Observations To Posts
**Goal:** Include what Grok sees from camera in tweets

**Current status:**
- Agent (`src/brain/agent.py`) has `capture_image` tool
- Grok analyzes images and includes observations in response
- BUT: These visual observations aren't automatically included in social posts

**What to do:**
1. **In agent.py:** When Grok includes `social_post` in response, check if recent image analysis exists
2. **Enhance social_post:** Add visual observation to the tweet (e.g., "Leaves are praying nicely today!")
3. **Post with image:** Attach the webcam image to the tweet

**Example flow:**
```python
# In agent.py decision loop:
if grok_response.get("social_post"):
    # Get recent image analysis
    visual_obs = grok_response.get("analysis", {}).get("visual_observations", [])

    # Enhance post with observation
    enhanced_post = f"{grok_response['social_post']}"
    if visual_obs:
        enhanced_post += f" {visual_obs[0]}"  # Add first observation

    # Post with image
    await scheduler.post_now(
        content=enhanced_post,
        image_path="data/latest_webcam.jpg"
    )
```

**Files to create/edit:**
- Modify `src/brain/agent.py` decision loop to include visuals in posts

---

### Task 3: Implement Strategic Reply System
**Goal:** Auto-find and manually approve replies to relevant accounts

**Current status:**
- `find_engagement_opportunities()` exists and works
- Searches #AICannabis, #Monad, etc.
- `generate_reply()` can create responses
- BUT: No automation to actually reply

**What NOT to do:**
- ❌ Auto-reply to everything (gets banned)
- ❌ Reply to bots/spam
- ❌ Generic "nice project ser" replies

**What TO do:**
Build a **reply queue system** where:
1. AI finds 5-10 good engagement opportunities daily
2. Filters out bots/spam (check follower count, account age)
3. Generates reply suggestions
4. Saves to queue for **human approval**
5. Human reviews and approves 2-3 per day
6. System posts approved replies

**Implementation:**
```python
# In scheduler.py, add:

async def find_and_queue_replies(self):
    """Find engagement opportunities and queue for approval"""

    # Find opportunities
    opportunities = await self.xai.find_engagement_opportunities()

    # Filter out bots (basic heuristics)
    filtered = [
        opp for opp in opportunities
        if opp.get('follower_count', 0) > 100  # Real accounts
        and opp.get('account_age_days', 0) > 30  # Not brand new
        and not self._looks_like_spam(opp['text'])
    ]

    # Generate replies for top 5
    for opp in filtered[:5]:
        reply = await self.manager.generate_reply(
            tweet_text=opp['text'],
            context=f"User is discussing {opp['topic']}"
        )

        # Save to approval queue
        self._save_to_reply_queue({
            'tweet_id': opp['id'],
            'original_text': opp['text'],
            'suggested_reply': reply,
            'status': 'pending_approval'
        })

# Run daily at optimal time (e.g., 10 AM)
scheduler.add_job(
    find_and_queue_replies,
    CronTrigger(hour=10, minute=0),
    id="find_replies"
)
```

**Files to create:**
- `src/social/reply_queue.py` - Queue management
- Modify `src/social/scheduler.py` - Add reply finder job
- Create CLI tool: `python review_replies.py` - Human approval interface

---

### Task 4: Create Twitter Community
**Goal:** Set up @GanjaMonAI Community for holder chat

**What to do:**
1. Go to twitter.com/GanjaMonAI
2. Click "Communities" in sidebar
3. Create new Community:
   - **Name:** "Grok & Mon Growers"
   - **Description:** "AI-autonomous cannabis cultivation. Join the experiment. $MON holders welcome."
   - **Rules:**
     - Be respectful
     - No spam
     - Cannabis legal discussion only (21+)
     - No financial advice
   - **Topic:** Technology, Cannabis (if available)

4. Add to profile: "Join our Community: [link]"

5. **Auto-post to Community:**
```python
# In scheduler.py or manager.py:

async def post_to_community(self, text: str, image_data: Optional[bytes] = None):
    """Post to both main timeline AND community"""

    # Post to main timeline
    result = await self.twitter.tweet(text, image_data=image_data)

    # Also post to community (requires tweepy community support)
    # Note: May need to use Twitter API v2 directly
    # community_id = "YOUR_COMMUNITY_ID"
    # await self.twitter.post_to_community(community_id, text, image_data)

    return result
```

**Note:** Twitter API doesn't have great Community support yet. May need to:
- Post manually to Community at first
- Use Twitter's web interface
- Wait for API feature rollout

---

### Task 5: Wire Into Orchestrator
**Goal:** Auto-post after Grok makes decisions

**Current status:**
- `src/orchestrator.py` runs agent decision cycles
- Agent includes `social_post` in responses
- BUT: Orchestrator doesn't automatically post it

**What to do:**
```python
# In src/orchestrator.py, after Grok decision:

from src.social.scheduler import SocialScheduler

# Initialize scheduler
scheduler = SocialScheduler(grow_day=current_day, stage=current_stage)

# After agent.run_decision_cycle():
if 'social_post' in grok_response:
    # Get latest webcam image
    image_path = "data/webcam_latest.jpg"
    image_data = None
    if Path(image_path).exists():
        image_data = Path(image_path).read_bytes()

    # Post it!
    result = await scheduler.post_decision(
        decision=grok_response,
        vpd=current_vpd,
        health=grok_response['analysis']['overall_health'],
        image_data=image_data
    )

    if result and result.posted:
        logger.info(f"Posted to X: {result.tweet_id}")
    else:
        logger.warning(f"Post failed: {result.error if result else 'None'}")
```

**Files to edit:**
- `src/orchestrator.py` - Add social posting after decisions

---

### Task 6: Test End-to-End
**Goal:** Verify the complete flow works

**Test scenarios:**

1. **Manual Post Test:**
```bash
python -c "
from src.social.scheduler import SocialScheduler
import asyncio

async def test():
    s = SocialScheduler(grow_day=7, stage='clone')
    result = await s.post_now(
        'Test post with all systems integrated! 🌱 #GrokAndMon',
        bypass_rate_limit=True
    )
    print(f'Success: {result.posted}, ID: {result.tweet_id}')

asyncio.run(test())
"
```

2. **Scheduled Post Test:**
   - Set scheduler to post in 2 minutes
   - Verify it respects posting windows
   - Check compliance tracker updates

3. **Decision Post Test:**
   - Run orchestrator
   - Let Grok make a decision
   - Verify tweet gets posted
   - Check image is attached

4. **Rate Limit Test:**
   - Try posting 5 times rapidly
   - Verify 4th post gets rate limited
   - Check compliance tracker records correctly

---

## Implementation Priority

### Phase 1: Core Integration (Do First)
1. ✅ **Twitter API working** (DONE!)
2. 🔧 Wire compliance into scheduler (Task 1)
3. 🔧 Wire scheduler into orchestrator (Task 5)
4. 🔧 Test basic posting flow (Task 6)

### Phase 2: Enhanced Content (Do Second)
5. 🔧 Add visual observations to posts (Task 2)
6. 🔧 Test with real agent decisions
7. 🔧 Refine post templates based on results

### Phase 3: Community & Engagement (Do Third)
8. 🔧 Create Twitter Community (Task 4)
9. 🔧 Build reply queue system (Task 3)
10. 🔧 Test engagement workflow

---

## Files Summary

### Already Complete ✅
- `src/social/twitter.py` - Twitter API client
- `src/social/xai_native.py` - Grok post generation
- `src/social/manager.py` - Social manager
- `src/social/scheduler.py` - Scheduling framework
- `src/social/compliance.py` - Rate limiting & windows
- `src/brain/prompts/system_prompt.md` - Grok's personality
- `docs/SOCIAL_CAMPAIGN.md` - Complete strategy

### Need To Create 🔧
- `src/social/reply_queue.py` - Reply approval system
- `tools/review_replies.py` - CLI for human approval

### Need To Edit 🔧
- `src/social/scheduler.py` - Add compliance integration
- `src/orchestrator.py` - Add auto-posting after decisions
- `src/brain/agent.py` - Include visuals in social posts

---

## Content Strategy (Already Defined)

From `docs/SOCIAL_CAMPAIGN.md`:

### Daily Schedule
- **8 AM:** Morning check-in with vitals
- **12 PM:** Midday update or AI decision
- **4 PM:** Engagement (replies, RTs)
- **8 PM:** Evening wrap-up

### Post Types
1. **Vitals Posts** (40%) - "Day X: Mon's VPD at X.XX kPa, temp X°F..."
2. **Observations** (20%) - "Leaves praying nicely today, mon!"
3. **AI Decisions** (20%) - "Grok just adjusted humidity to 70% because..."
4. **Engagement** (10%) - Replies to community
5. **Milestones** (10%) - "First true leaves!" "$MON hit $X!"

### Voice Guidelines
- **DO:** Use "mon" naturally, cannabis knowledge, laid-back tone
- **DON'T:** Overdo Jamaican accent, sound robotic, spam hashtags
- **HASHTAGS:** Always #GrokAndMon, rotate #AIGrow #Cannabis #Monad

### Engagement Rules
- **DO:** Reply to genuine questions, RT quality content
- **DON'T:** Auto-reply everything, engage with bots, mass-reply

---

## Next Steps

Want me to start implementing? I recommend this order:

1. **Wire compliance into scheduler** (Task 1) - 10 min
2. **Wire scheduler into orchestrator** (Task 5) - 15 min
3. **Test basic flow** (Task 6) - 5 min
4. **Add visual observations** (Task 2) - 20 min
5. **Create Community** (Task 4) - 5 min (you do this on Twitter)
6. **Build reply system** (Task 3) - 30 min

Total implementation time: ~90 minutes of coding

Your system is **90% done** - just needs the final wiring! 🔌

Ready to start?
