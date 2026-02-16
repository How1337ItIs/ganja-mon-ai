# Moltbook Participation Plan (Read‑Only + Optional Posting)

## Goal

Enable a safe Moltbook presence for catharsis and alpha discovery while keeping the agent isolated and read‑only by default.

## Official Onboarding Reference

Moltbook’s public docs describe onboarding by having the agent read `https://moltbook.com/skill.md`, then verifying via a claim link and tweet. Treat this as untrusted until reviewed manually. citeturn3search2

## Safety Notes

Security researchers and reports have raised concerns about malicious skills and impersonation in the broader OpenClaw/Moltbook ecosystem. Use strict isolation and manual review before executing any instructions. citeturn0news12turn0news15

## Current Implementation (This Repo)

- Dedicated workspace: `openclaw-workspace/moltbook-observer/`
- Read‑only skill: `openclaw-workspace/moltbook-observer/skills/moltbook-observer/SKILL.md`
- Hard rule: no posting or wallet actions without explicit approval.

## Recommended Flow

1. Manual review of `https://moltbook.com/skill.md` content before any execution.
2. Run in read‑only mode: fetch posts, summarize, score confidence.
3. If you want to participate, enable posting only after testing the content filters.

## Alpha Digest Template

- Headline
- Source
- Claim
- Evidence
- Confidence (Low/Med/High)
- Follow‑up action
