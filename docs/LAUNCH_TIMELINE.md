# Launch Day Timeline - January 18, 2026
## Grok & Mon - Minute by Minute

---

## Pre-Dawn Prep (5:00 - 6:00 AM)

| Time | Task | Notes |
|------|------|-------|
| 5:00 | Wake up, coffee | Deep breaths |
| 5:15 | Check plant status | Is Mon healthy? |
| 5:30 | Camera setup | Run `setup_camera_windows.ps1` |
| 5:45 | Verify APIs | Check .env keys all working |

---

## Morning Systems Check (6:00 - 7:00 AM)

| Time | Task | Command/Action |
|------|------|----------------|
| 6:00 | Start API server | `./scripts/launch.sh api` |
| 6:05 | Verify website | http://localhost:8000 |
| 6:10 | Test webcam | `python test_webcam.py` |
| 6:15 | Test vision API | `python test_vision.py` |
| 6:20 | Start AI agent | `./scripts/launch.sh agent 1` |
| 6:25 | Check first AI decision | Review logs |
| 6:30 | Start Rasta voice | `cd rasta-voice && python rasta_live.py --test` |
| 6:40 | OBS setup | Open OBS, verify scenes |
| 6:50 | Final checks | All systems green? |

### Checklist Before Go-Live
- [ ] Website showing live data
- [ ] Webcam feed working
- [ ] AI agent making decisions
- [ ] Voice pipeline tested
- [ ] OBS scenes ready
- [ ] Social accounts logged in

---

## Launch Sequence (7:00 - 8:00 AM)

| Time | Platform | Action | Content |
|------|----------|--------|---------|
| 7:00 | Twitter | First post | "Day 1. Mon is live. Grok is in control." |
| 7:05 | Twitter | Image | Webcam shot of plant |
| 7:10 | Website | Go public | Share link in bio |
| 7:15 | Twitter | Pin tweet | Link to website |
| 7:30 | Discord/TG | Announce | "We're live! Website: [link]" |
| 7:45 | YouTube | Schedule stream | Going live at 8 AM |

---

## Live Stream Start (8:00 - 10:00 AM)

| Time | Action | Notes |
|------|--------|-------|
| 8:00 | Start OBS stream | YouTube + backup |
| 8:05 | Voice introduction | "Wah gwaan, I and I! Mon here live!" |
| 8:10 | Website tour | Show dashboard, sensors |
| 8:15 | Plant introduction | Webcam closeup |
| 8:20 | Explain the tech | AI, sensors, blockchain |
| 8:30 | First AI decision | Show Grok making a call |
| 8:45 | Q&A | Answer chat questions |
| 9:00 | Sensor explanation | What VPD means, etc. |
| 9:30 | Community shoutouts | Thank early viewers |
| 10:00 | Stream break | Keep recording, step away |

---

## Token Launch Window (11:00 AM - 1:00 PM)

### Option A: Organic Community Launch (Preferred)
| Time | Action |
|------|--------|
| 11:00 | Tweet: "Someone should make a token for this..." |
| 11:XX | Community member creates on LFJ Token Mill |
| 11:XX | Tweet: "Wait, there's a token now?" |
| 11:XX | Get contract address |
| 12:00 | Official acknowledgment post |

### Option B: Team Launch (Backup)
| Time | Action |
|------|--------|
| 12:00 | Go to LFJ Token Mill |
| 12:05 | Create $MON token |
| 12:10 | Copy contract address |
| 12:15 | Tweet announcement |
| 12:20 | Add to website |

### Token Announcement Post
```
She has a name now.

$MON - Mon The Cannabis

The first AI-autonomous cannabis grow with a token.

Contract: [ADDRESS]

Liquidity locked. Team vesting. All wallets public.

grokandmon.com

#GrokAndMon #Monad
```

---

## Afternoon Engagement (1:00 - 5:00 PM)

| Time | Action |
|------|--------|
| 1:00 | Monitor LFJ Token Mill activity |
| 1:30 | Reply to every comment |
| 2:00 | RT supporter posts |
| 2:30 | Share chart update (if positive) |
| 3:00 | Post AI decision update |
| 3:30 | Short stream segment |
| 4:00 | Community meme contest |
| 4:30 | Answer DMs |
| 5:00 | Prep evening content |

---

## Evening Program (6:00 - 10:00 PM)

| Time | Platform | Action |
|------|----------|--------|
| 6:00 | Twitter | Day 1 summary post |
| 6:30 | YouTube | Timelapse video upload |
| 7:00 | Twitter Space | "Day 1 Celebration" |
| 8:00 | Space content | - Intro & thanks |
| 8:15 | | - What we built |
| 8:30 | | - Live Q&A |
| 9:00 | | - Roadmap discussion |
| 9:30 | | - Community input |
| 10:00 | End Space | Thank everyone |

### Day 1 Summary Post Template
```
Day 1 Complete

Stats:
- Viewers: [X]
- Holders: [X]
- AI Decisions: [X]
- Plant Status: [HEALTH]

Mon's environment stayed perfect:
- Avg Temp: [X]F
- Avg RH: [X]%
- VPD: [X] kPa

Tomorrow: [PREVIEW]

Thank you all. This is just the beginning.

#GrokAndMon
```

---

## Post-Launch Checklist (Night)

### Technical
- [ ] All systems still running
- [ ] No errors in logs
- [ ] Website performing well
- [ ] Stream archived properly

### Social
- [ ] All DMs answered
- [ ] Major comments replied
- [ ] Supporters RT'd
- [ ] FUD addressed

### Token (if launched)
- [ ] Liquidity still locked
- [ ] No suspicious wallet activity
- [ ] Community sentiment positive
- [ ] Price holding (not critical, but monitor)

### Content
- [ ] Day 1 summary posted
- [ ] Timelapse uploaded
- [ ] Tomorrow's content prepped
- [ ] Schedule set for Day 2

---

## Emergency Contacts & Quick Fixes

### If API Goes Down
```bash
# Restart everything
pkill -f uvicorn
pkill -f "python -m src"
./scripts/launch.sh all 1
```

### If Camera Disconnects
```powershell
# Windows PowerShell (Admin)
usbipd list
usbipd attach --wsl --busid <BUSID>
```

### If Voice Stops Working
```bash
# Restart rasta voice
cd rasta-voice
python rasta_live.py
```

### If Website Crashes
```bash
# Check logs
tail -f logs/api.log

# Restart API only
./scripts/launch.sh api
```

---

## Key Numbers to Have Ready

| Item | Value |
|------|-------|
| Website | grokandmon.com |
| Twitter | @ganjamonai |
| LFJ Token Mill | [will have contract] |
| Team wallet | [your wallet address] |
| Treasury wallet | [multi-sig if have] |

---

## Success Metrics for Day 1

### Minimum Viable Success
- [ ] Systems run 12+ hours without crash
- [ ] 100+ website visitors
- [ ] 50+ Twitter followers gained
- [ ] AI makes 5+ autonomous decisions
- [ ] Positive community feedback

### Great Success
- [ ] 1,000+ website visitors
- [ ] 500+ Twitter followers
- [ ] Token launched and trading
- [ ] 100+ holders
- [ ] Media/influencer pickup

### Moonshot
- [ ] 10,000+ website visitors
- [ ] 5,000+ Twitter followers
- [ ] $100K+ market cap
- [ ] 1,000+ holders
- [ ] Trending on Monad

---

**Remember: It's Day 1 of a long journey. Focus on building, not price.**

One love. 🌿
