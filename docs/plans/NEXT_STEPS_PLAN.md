# Next Steps Plan - Grok & Mon
**Generated:** 2026-01-21  
**Status:** Strategic Planning Document

---

## Executive Summary

After reviewing the codebase, the project is in excellent shape with most core systems operational. The immediate priority is **completing the Dub Playlist feature** (95% done, needs deployment), followed by **website polish** and **advanced feature development**.

---

## Current System Status

### ✅ Fully Operational
- **AI Brain** - Grok decision loop running every 2 hours
- **Hardware Integration** - Govee sensors, Kasa plugs, Ecowitt soil sensors
- **API Server** - FastAPI running on Chromebook (port 8000)
- **Database** - SQLite storing sensor data, AI decisions, grow history
- **Website Core** - Live at grokandmon.com with webcam, sensors, chat
- **Webamp Player** - Functional with 7 reggae tracks
- **Chat System** - WebSocket-enabled public chat working
- **Streaming Setup** - OBS overlays, rasta voice pipeline ready

### ⏳ In Progress (95% Complete)
- **Dub Playlist Feature** - R2 infrastructure ready, tracks uploaded, API code written, **needs deployment to Chromebook**

### 📋 Planned/Incomplete
- Website visual polish (particle effects, animations)
- Mobile optimization
- Advanced AI features (plant health vision, auto-detection)
- Notification system (Discord/Telegram)
- Token launch preparation

---

## Priority 1: Complete Dub Playlist Deployment (IMMEDIATE)

### Current Status
- ✅ R2 bucket created: `grokmon-dub-tracks`
- ✅ Cloudflare Worker deployed: `grokmon-dub-stream`
- ✅ Route configured: `grokandmon.com/api/playlist/dub/stream/*`
- ✅ 38 tracks uploaded to R2 (~3 GB)
- ✅ API code written: `src/api/playlist.py` (R2-enabled)
- ✅ Frontend loader: `src/web/playlist-loader.js`
- ⚠️ **API not deployed to Chromebook** (returns HTML instead of JSON)

### Action Items

#### 1.1 Deploy API to Chromebook (15 minutes)
```bash
# Option A: Use deploy script (if exists)
./deploy.sh --restart

# Option B: Manual deployment
scp src/api/playlist.py chromebook.lan:/home/natha/projects/sol-cannabis/src/api/playlist.py
scp src/api/app.py chromebook.lan:/home/natha/projects/sol-cannabis/src/api/app.py
ssh chromebook.lan "systemctl --user restart grokmon"

# Verify deployment
ssh chromebook.lan "systemctl --user status grokmon --no-pager"
curl https://grokandmon.com/api/playlist/list
```

#### 1.2 Verify R2 Upload Complete (5 minutes)
```bash
# Test streaming endpoint with a known track
curl -I "https://grokandmon.com/api/playlist/dub/stream/King%20Tubby%20-%20Dub%20From%20The%20Roots.mp3"

# Should return 200 or 206 (Partial Content)
# If 404, re-run upload script:
export CLOUDFLARE_API_TOKEN="055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"
python scripts/upload_dub_to_r2.py
```

#### 1.3 Browser Testing (10 minutes)
- [ ] Visit https://grokandmon.com
- [ ] Verify playlist selector appears (bottom-right)
- [ ] Select "Ultimate Chill Dub" playlist
- [ ] Verify tracks load in Webamp
- [ ] Test playback (play, pause, skip)
- [ ] Check browser console for errors
- [ ] Test on mobile device

#### 1.4 Documentation Update (5 minutes)
- [ ] Update `research/dub_playlist_HANDOFF.md` with completion status
- [ ] Mark deployment steps as complete
- [ ] Note any issues found during testing

**Estimated Time:** 35 minutes  
**Priority:** CRITICAL (feature is 95% complete, just needs deployment)

---

## Priority 2: Website Visual Polish (HIGH)

### Current Status
- ✅ Core functionality complete (webcam, chat, Webamp, stream announcements)
- ✅ Basic styling with Rasta theme
- ⏳ Visual effects pending (particle effects, animations)
- ⏳ Mobile optimization incomplete

### Action Items

#### 2.1 Visual Effects (2-3 hours)
- [ ] **Smoke/Haze Particles**
  - Add CSS/JS particle system for background smoke effect
  - Subtle animation, not distracting
  - Toggle on/off option
  
- [ ] **Color Transitions**
  - Smooth psychedelic color transitions on background
  - Sync with music tempo (if possible)
  - Respect user's motion preferences (prefers-reduced-motion)
  
- [ ] **Vinyl Record Animation**
  - Animated vinyl record spinning when music plays
  - Position near Webamp player
  - Pause animation when music paused
  
- [ ] **Trichome Sparkle Effects**
  - Subtle sparkle/glitter effects on plant imagery
  - Cannabis-themed visual enhancement
  - Performance-optimized (use CSS transforms, not JS)

- [ ] **CRT Scanline Overlay**
  - Optional retro CRT effect toggle
  - Subtle scanlines for nostalgic vibe
  - User preference saved to localStorage

#### 2.2 Mobile Optimization (2-3 hours)
- [ ] **Responsive Layout Testing**
  - Test on iOS Safari (iPhone 12/13/14)
  - Test on Chrome Android
  - Fix any layout breaks
  
- [ ] **Touch Interactions**
  - Ensure all buttons work on touch
  - Add touch-friendly spacing (min 44x44px)
  - Test drag interactions (Webamp window)
  
- [ ] **Performance Optimization**
  - Reduce animations on mobile (battery saving)
  - Lazy load heavy assets
  - Optimize image sizes for mobile
  
- [ ] **Mobile-Specific Features**
  - Collapsible sections for small screens
  - Bottom navigation bar (if needed)
  - Swipe gestures for navigation

#### 2.3 Accessibility (1 hour)
- [ ] **Keyboard Navigation**
  - All interactive elements keyboard-accessible
  - Focus indicators visible
  - Tab order logical
  
- [ ] **Screen Reader Support**
  - ARIA labels on interactive elements
  - Alt text for images
  - Semantic HTML structure
  
- [ ] **Color Contrast**
  - Verify WCAG AA compliance
  - Test with color blindness simulators
  - Ensure text is readable on all backgrounds

**Estimated Time:** 5-7 hours  
**Priority:** HIGH (improves user experience significantly)

---

## Priority 3: Advanced AI Features (MEDIUM)

### Current Status
- ✅ Basic AI decision loop working
- ✅ Vision analysis endpoint exists (`/api/vision/analyze`)
- ⏳ Plant health auto-detection not fully integrated
- ⏳ Growth stage auto-detection pending

### Action Items

#### 3.1 Plant Health Vision Integration (3-4 hours)
- [ ] **Automated Health Checks**
  - Integrate vision analysis into decision loop
  - Run health check every 6 hours (not every decision cycle)
  - Store results in database
  
- [ ] **Health Alert System**
  - Detect common issues: nutrient deficiency, pests, mold
  - Generate alerts when issues detected
  - Include recommendations in AI output
  
- [ ] **Visual Health Dashboard**
  - Add health status widget to website
  - Show recent health check results
  - Display confidence scores

#### 3.2 Growth Stage Auto-Detection (2-3 hours)
- [ ] **Stage Detection Logic**
  - Use vision to detect flowering onset
  - Analyze plant structure (node spacing, bud formation)
  - Compare against expected timeline
  
- [ ] **Automatic Stage Transitions**
  - Auto-advance stage when detected
  - Update photoperiod automatically (18/6 → 12/12)
  - Log stage transitions with confidence scores
  
- [ ] **Manual Override**
  - Allow manual stage setting (admin)
  - Keep auto-detection as suggestion
  - Log manual overrides

#### 3.3 Trichome Analysis (Future - Requires Macro Camera)
- [ ] **Harvest Timing Detection**
  - Analyze trichome color (cloudy vs amber)
  - Recommend harvest window
  - Track trichome development over time
  
**Estimated Time:** 5-7 hours  
**Priority:** MEDIUM (enhances AI capabilities, but system works without it)

---

## Priority 4: Notification System (MEDIUM)

### Current Status
- ✅ Twitter integration exists (`src/social/twitter.py`)
- ⏳ Discord/Telegram notifications not implemented
- ⏳ Alert system not automated

### Action Items

#### 4.1 Discord Integration (2-3 hours)
- [ ] **Discord Webhook Setup**
  - Create Discord webhook in server
  - Add webhook URL to environment variables
  - Test webhook connection
  
- [ ] **Alert Types**
  - Critical alerts (sensor failures, extreme temps)
  - Daily summaries (growth progress, VPD trends)
  - Weekly reports (growth photos, stats)
  - AI decision highlights (interesting decisions)
  
- [ ] **Message Formatting**
  - Rich embeds with sensor data
  - Plant photos attached
  - Links to website dashboard

#### 4.2 Telegram Integration (2-3 hours)
- [ ] **Telegram Bot Setup**
  - Create bot via @BotFather
  - Get bot token, add to environment
  - Set up webhook or polling
  
- [ ] **Command Interface**
  - `/status` - Current sensor readings
  - `/photo` - Latest plant photo
  - `/ai` - Latest AI decision
  - `/stage` - Current growth stage
  
- [ ] **Push Notifications**
  - Same alert types as Discord
  - Optional: User can subscribe/unsubscribe

#### 4.3 Email Notifications (Optional - 1-2 hours)
- [ ] **SMTP Configuration**
  - Set up email service (SendGrid, Mailgun, or Gmail SMTP)
  - Add credentials to environment
  
- [ ] **Email Templates**
  - Daily digest template
  - Alert template
  - Weekly report template
  
**Estimated Time:** 5-8 hours  
**Priority:** MEDIUM (nice-to-have, improves monitoring but not critical)

---

## Priority 5: Token Launch Preparation (FUTURE)

### Current Status
- ✅ Token concept defined ($MON on Monad)
- ✅ Launch platform identified (LFJ Token Mill)
- ⏳ Smart contracts not written
- ⏳ Tokenomics not finalized
- ⏳ Launch marketing not planned

### Action Items (When Ready)

#### 5.1 Smart Contract Development
- [ ] ERC-20 token contract (Monad/EVM compatible)
- [ ] Token distribution logic
- [ ] Vesting schedules (if applicable)
- [ ] Security audit

#### 5.2 Tokenomics
- [ ] Total supply determination
- [ ] Allocation breakdown
- [ ] Launch strategy (fair launch vs presale)
- [ ] Liquidity pool planning

#### 5.3 Marketing & Launch
- [ ] Launch day content calendar
- [ ] Social media campaign
- [ ] Community building (Discord/Telegram)
- [ ] Influencer outreach

**Estimated Time:** 20-40 hours (when ready)  
**Priority:** FUTURE (not urgent, focus on core system first)

---

## Priority 6: Infrastructure Improvements (LOW)

### Current Status
- ✅ Core infrastructure stable
- ✅ Chromebook server running reliably
- ⏳ Some optimization opportunities

### Action Items

#### 6.1 Performance Optimization
- [ ] **Database Optimization**
  - Add indexes for common queries
  - Implement data archiving (move old data to cold storage)
  - Optimize sensor history queries
  
- [ ] **API Response Times**
  - Add response caching where appropriate
  - Optimize database queries
  - Implement pagination for large datasets
  
- [ ] **Image Optimization**
  - Compress webcam images (reduce quality slightly)
  - Implement progressive JPEG loading
  - Cache processed images

#### 6.2 Monitoring & Logging
- [ ] **Enhanced Logging**
  - Structured logging (JSON format)
  - Log rotation and archival
  - Error tracking (Sentry or similar)
  
- [ ] **Health Monitoring**
  - Uptime monitoring (UptimeRobot or similar)
  - Alert on API downtime
  - Track response times

#### 6.3 Backup & Recovery
- [ ] **Automated Backups**
  - Daily database backups
  - Backup to cloud storage (R2 or S3)
  - Test restore procedure
  
- [ ] **Disaster Recovery Plan**
  - Document recovery steps
  - Keep hardware spares list
  - Maintain off-site backups

**Estimated Time:** 8-12 hours  
**Priority:** LOW (system works fine, optimizations can wait)

---

## Recommended Workflow

### Week 1: Complete Dub Playlist + Quick Wins
1. **Day 1** - Deploy dub playlist API (35 min)
2. **Day 2-3** - Website visual polish (5-7 hours)
3. **Day 4-5** - Mobile optimization (2-3 hours)

### Week 2: Advanced Features
1. **Day 1-2** - Plant health vision integration (3-4 hours)
2. **Day 3-4** - Growth stage auto-detection (2-3 hours)
3. **Day 5** - Notification system setup (5-8 hours)

### Week 3+: Infrastructure & Polish
1. Performance optimization
2. Monitoring improvements
3. Token launch prep (when ready)

---

## Quick Reference: Key Files

### Dub Playlist
- `src/api/playlist.py` - API endpoints
- `src/api/app.py` - Main FastAPI app (includes playlist router)
- `src/web/playlist-loader.js` - Frontend loader
- `cloudflare-worker-dub-stream.js` - R2 streaming worker
- `scripts/upload_dub_to_r2.py` - Upload script

### Website
- `src/web/index.html` - Main website
- `src/web/dashboard.html` - Monitoring dashboard
- `src/api/app.py` - API server

### AI & Hardware
- `src/brain/agent.py` - AI decision loop
- `src/hardware/` - Hardware drivers
- `src/api/app.py` - API endpoints

### Documentation
- `CLAUDE.md` - Project overview and commands
- `research/dub_playlist_HANDOFF.md` - Dub playlist handoff
- `SYSTEM_OVERVIEW.md` - System architecture

---

## Success Metrics

### Dub Playlist (Priority 1)
- ✅ API returns JSON (not HTML)
- ✅ Tracks stream successfully from R2
- ✅ Playlist selector visible on website
- ✅ Webamp loads and plays tracks
- ✅ No console errors

### Website Polish (Priority 2)
- ✅ Visual effects enhance experience without distraction
- ✅ Mobile layout works on all tested devices
- ✅ Accessibility score > 90 (Lighthouse)
- ✅ Performance score > 90 (Lighthouse)

### Advanced Features (Priority 3)
- ✅ Health checks run automatically
- ✅ Stage transitions detected automatically
- ✅ Alerts sent to Discord/Telegram
- ✅ False positive rate < 10%

---

## Notes & Considerations

### Technical Debt
- Some security middleware disabled for stability (see `app.py` comments)
- Mock hardware fallbacks in place (good for development)
- Database could use optimization for large datasets

### Dependencies
- Cloudflare R2 for dub tracks (free tier sufficient)
- xAI Grok API for AI decisions (cost per request)
- Hardware sensors require network connectivity

### Risks
- **Chromebook stability** - Server runs on consumer hardware, monitor for crashes
- **API costs** - Grok API usage scales with decision frequency
- **Hardware failures** - Sensors/plugs can disconnect, system handles gracefully

---

## Conclusion

The project is in excellent shape. The immediate focus should be:

1. **Complete the dub playlist** (35 minutes) - It's 95% done!
2. **Polish the website** (5-7 hours) - Make it visually stunning
3. **Add advanced features** (5-7 hours) - Enhance AI capabilities

After these priorities, the system will be production-ready with a polished user experience and advanced AI features.

---

*Last updated: 2026-01-21*
