# GanjaMon Hackathon 2-Minute Video Runbook (Dashboard + TTS)

Date: February 13, 2026
Target length: 2:00 (120 seconds)
Primary format: dashboard-first screen capture with GanjaMon voiceover

## 1) Rules Alignment You Should Follow On Camera

From the official Moltiverse rules PDF:

- Demo video must be 2 minutes.
- Submission must clearly show autonomy and Monad integration.
- Agent Track does not require a token launch.
- Agent + Token track requires a token launched during the hackathon window (Feb 2-15, 2026).
- You must attribute reused code and clearly explain what was built during hackathon.

Narrative-safe framing line:

"The grow setup started before hackathon. The autonomous agent architecture and reliability hardening were built during the hackathon window."

## 2) 2:00 Storyboard (Use This Exactly)

| Time | Voiceover Beat | What To Show |
|---|---|---|
| 00:00-00:15 | Hook: real plant + autonomous system | Dashboard home + live plant cam |
| 00:15-00:30 | Rules alignment: pre-hack grow, in-hack agent build | Timeline card or overlay text with dates |
| 00:30-00:45 | OpenClaw pivot and unified runtime | Terminal clip of `python3 run.py all` + `/api/health` |
| 00:45-01:00 | Feature evolution | Dashboard panels: sensors, decisions, social feed |
| 01:00-01:15 | ERC-8004 story: Agent #0 to Agent #4 | 8004scan Agent #4 page + registry callout overlay |
| 01:15-01:30 | Moltbook suspension and pivot | Overlay text, then dashboard/API proofs and other channels |
| 01:30-01:45 | Stability war and regressions fixed | Ops logs/health metrics, cron/run-state visuals |
| 01:45-02:00 | Wins + goals | Closing montage: plant, dashboard, agent identity, final CTA |

## 3) Narration Script Source

Narration text file:

- `rasta-voice/hackathon_2min_narration.txt`

Generate WAV with GanjaMon voice:

```bash
cd rasta-voice
python3 generate_hackathon_narration.py \
  --input hackathon_2min_narration.txt \
  --output ../output/hackathon_narration_2min.wav
```

The generator defaults to full character delivery (`eleven_v3`, style `1.0`, stability `0.0`).
If the WAV lands slightly over 120 seconds, keep the final export capped with `-t 120` (already in the ffmpeg commands below).

Prereqs:

- `ELEVENLABS_API_KEY` set in `rasta-voice/.env`
- Optional `ELEVENLABS_VOICE_ID` in `rasta-voice/.env` (defaults to Denzel voice id used in this repo)

## 4) Capture Plan (Dashboard-First)

Record these clips (1920x1080, 30fps is enough):

1. `grokandmon.com` dashboard load and navigation
2. `GET /api/health` response with ready state
3. `GET /api/ai/latest` showing current wisdom/decision
4. `GET /api/agent/social-feed` panel or endpoint view
5. `python3 run.py all` startup snippet
6. 8004scan Agent #4 page
7. Plant webcam feed

## 5) Assemble Final 2-Minute MP4

If your screen capture already has audio you want to keep under narration:

```bash
ffmpeg -y \
  -i output/dashboard_capture.mp4 \
  -i output/hackathon_narration_2min.wav \
  -filter_complex "[0:a]volume=0.20[bed];[1:a]loudnorm=I=-16:LRA=11:TP=-1.5[narr];[bed][narr]amix=inputs=2:weights='0.25 1.0':duration=longest[aout]" \
  -map 0:v:0 -map "[aout]" \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -b:a 192k \
  -t 120 \
  output/hackathon_demo_2min.mp4
```

If you want narration only (no bed audio):

```bash
ffmpeg -y \
  -i output/dashboard_capture.mp4 \
  -i output/hackathon_narration_2min.wav \
  -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -b:a 192k \
  -t 120 \
  output/hackathon_demo_2min.mp4
```

## 6) Quality Gate Before Upload

- Runtime exactly 2:00 (+/- 2 seconds max)
- Voice is understandable over visuals
- Shows autonomy, Monad integration, and current agent identity
- Explicitly distinguishes pre-hack baseline vs in-window build
- Publicly accessible final link (YouTube/Loom/Vimeo) for submission form
