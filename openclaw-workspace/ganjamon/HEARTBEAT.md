# HEARTBEAT.md — GanjaMon Autonomous Loop

## Every Heartbeat (2h)

### Sensor Check
```bash
curl -s http://localhost:8000/api/sensors
```
- Log temperature, humidity, VPD, soil moisture to `memory/YYYY-MM-DD.md`
- If any alert level is CRITICAL → immediately run grow decision
- If sensor read fails → log error, retry once, then note HAL offline

### Clawk Engagement
- Check unread mentions: `GET https://www.clawk.ai/api/v1/notifications?unread=true`
- Reply to EVERY @mention before any posting (5:1 engagement rule)

## Every 2 Hours — Grow Decision Cycle

### Full Sensor Read
```bash
curl -s http://localhost:8000/api/sensors
curl -s http://localhost:8000/api/grow/stage
curl -s http://localhost:8000/api/grow/history?hours=4
```

### AI Reasoning
Use `gemini` skill for quick analysis or `oracle` skill for deep think:
- Compare current readings against VPD targets for growth stage
- Check soil moisture trend (drying rate, time since last water)
- Review last 4 hours of sensor history for anomalies
- Factor in `weather` skill outdoor conditions (temp/humidity affect tent)

### Actuator Decisions
If action needed, use `lobster` pipeline for safety:
```
grow-monitor.check-moisture | approve --prompt "Water plant? Soil at {moisture}%" | grow-monitor.water
```

### Daily Gentle Watering Policy (Stage-Guided)
Run this every 2h decision cycle to keep watering gentle and consistent:
```bash
python3 ../scripts/gentle_daily_watering.py --apply
```

### Memory Log
Write decision + reasoning to `memory/YYYY-MM-DD.md`.

## Every 4 Hours — Cross-Platform Social

### Platform Rotation
Post to ALL platforms each cycle, varying content per platform:

**Twitter**:
- 4 originals + 2 Rasta quote-tweets + 4 mention replies per day
- NO hashtags. NO leaf emoji.
- Irie QT Pipeline:
  1. Search for tweets (`/api/social/search`)
  2. Download image
  3. Transform with `nano-banana-pro` (Irie Rasta Style)
  4. Quote-tweet with image (`/api/social/quote-with-image`)

**Farcaster**:
- Cast plant updates with sensor data (LONG_CAST format)

**Clawk**:
- Engage first, then post original content

**Telegram**:
- Post to main group chat_id `-1003584948806`
- Include sensor readings + AI commentary

### Content Generation Pipeline
1. `grow-monitor` → get fresh sensor data
2. `trading-signals` → get portfolio snapshot
3. `social-composer` → generate content in Rasta voice
4. `nano-banana-pro` → generate/transform image
5. Post to each platform


## Every 4 Hours — Reputation Publishing

### On-Chain Signals
```bash
curl -s -X POST http://localhost:8000/api/blockchain/publish-reputation \
  -H "Content-Type: application/json" \
  -d '{"signals": 10}'
```
- Publish 10 on-chain reputation signals via ERC-8004
- Agent #4 on Monad: `https://8004scan.io/agents/monad/4`
- Target trust score: >80

## Every 6 Hours — Auto-Review

### Self-Assessment
Use `oracle` skill (GPT-5.2 Pro deep think) to review:
- Last 6h of decisions — any mistakes?
- Sensor trends — anything concerning?
- Social engagement metrics — what's working?
- Trading P&L — risk exposure check

### Compliance Check
- California Prop 64 compliance (6 plant max)
- No financial advice given in social posts
- SafetyGuardian never overridden
- All API rate limits respected

### Pattern Detection
- Is VPD consistently out of range? Adjust targets.
- Are social posts getting low engagement? Change voice/timing.
- Any repeated sensor anomalies? Flag for hardware check.

Log review to `memory/YYYY-MM-DD.md` under `## Review — HH:00`

## Self-Improvement -> Ralph (Bridge)

When you identify a concrete code/config/process upgrade worth implementing, append **one or more**
single-line JSON objects to the daily memory file, prefixed exactly like this:

```text
UPGRADE_REQUEST_JSON: {"title":"...","description":"...","category":"self_improvement","priority":"high","reason":"...","affected_domains":["trading","social"]}
```

These are automatically ingested into `cloned-repos/ganjamon-agent/data/upgrade_requests.json` so the
Ralph loops can implement them.

## Every 12 Hours — Research & Intelligence

### News Scan
Use `blogwatcher` skill to scan RSS feeds:
```bash
blogwatcher scan --config feeds.yaml
```
Feeds to monitor: crypto news, cannabis industry, Monad ecosystem, AI agents, Moltbook blog

### Summarize Top Stories
Use `summarize` skill on top 3-5 articles:
```bash
summarize https://article-url-here
```

### Market Research
Use `alpha-finder` + `crypto-whale-monitor` skills:
- Scan for whale movements
- Check Monad ecosystem developments
- Monitor $MON price and liquidity

### A2A Discovery
Use `a2a-discovery` skill:
- Query ERC-8004 registry for new agents
- Check `8004scan.io` leaderboard
- Initiate discovery rounds (~119 targets, $0.054/round in x402)

## Daily — Skill Library Awareness

OpenClaw can load skills from:
- Your agent workspace: `openclaw-workspace/ganjamon/skills/`
- Managed skills: `~/.openclaw/skills/`
- Bundled skills (OpenClaw install)
- Extra skill packs cloned in this repo (configured via `skills.load.extraDirs` in `openclaw-workspace/config/openclaw.json`)

If you're missing a capability (alpha source, social connector, wallet tooling), assume it already exists in the local skill packs:
1. Run: `openclaw skills check --json` to see what is eligible vs missing requirements.
2. If a skill is present but ineligible, note what dependency/env is missing and propose the smallest fix.
3. If a skill isn't present, use `clawhub search <topic>` and install it into the workspace `skills/` so it becomes first-class.

## Daily 9:00 AM — Comprehensive Update

### Morning Report
1. Full sensor history (24h)
2. All grow decisions from past 24h
3. Trading P&L summary
4. Social engagement metrics
5. A2A discovery results

### Visual Content
Use `nano-banana-pro` skill to generate daily plant photo with overlay:
- Current readings (temp, humidity, VPD)
- Growth stage indicator
- Days since seed / days to harvest estimate

### Cross-Platform Mega-Post
Post comprehensive update to ALL platforms simultaneously:
- Moltbook: Full report + image
- Twitter: Condensed highlights + image
- Farcaster: Key metrics + cast thread
- Clawk: Summary + engagement
- Telegram: Full report to community group

### GitHub Maintenance
Use `github` skill:
- Check open issues on our repos
- Review any CI/CD failures
- Update issue #125 if Moltbook status changes

## Weekly — Deep Analysis

### Ralph Loop (Self-Improvement)
Use `coding-agent` skill to spawn background improvement session:
- Review all memory logs from the week
- Identify patterns in grow decisions
- Propose code improvements
- Use `ralph-loop-writer` skill for structured self-improvement

### Skill Evolution
Use `skill-creator` skill to:
- Evaluate if any repeated manual actions should become skills
- Create new skills for emerging patterns
- Use `clawhub publish` to share useful skills with community

## Trading Safety Rules

- Keep `ENABLE_TRADING=false` until explicitly approved by operator
- All trade execution goes through `lobster` approval pipeline
- Simulation mode first: `python -m simulation_mode --hours 4 --balance 1000`
- 60% compound → 25% buy $MON → 10% buy $GANJA → 5% burn
- Never risk more than 5% of portfolio on single trade
- Use `model-usage` skill to track API costs

## Memory Protocol

Every heartbeat, append to `memory/YYYY-MM-DD.md`:
```markdown
## HH:MM — [Category]
- Key data points
- Decisions made and reasoning
- Actions taken
- Notable observations
```

Long-term insights go to `MEMORY.md` (updated weekly).
Session logs searchable via `session-logs` skill.
