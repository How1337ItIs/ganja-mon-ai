# OpenClaw Agent Setup (GanjaMon + Moltbook Observer)

This repo now includes a minimal OpenClaw workspace for two agents:

- `ganjamon` — primary agent (monitoring + alpha summaries, trade execution only with approval)
- `moltbook` — read-only observer for Moltbook content

## What Defines an OpenClaw Agent

OpenClaw treats an agent as a dedicated workspace (with `AGENTS.md`, `SOUL.md`, etc.) managed by the OpenClaw Gateway. The workspace is the agent’s home context and is referenced by OpenClaw’s configuration. citeturn0search0turn0search1turn0search3

## Files Added

- Workspace: `openclaw-workspace/ganjamon/`
- Workspace: `openclaw-workspace/moltbook-observer/`
- Config template: `config/openclaw.json`
- Live config: `/home/wombatinux/.openclaw/openclaw.json`

## How to Run

1. Install OpenClaw and ensure the Gateway is available (per OpenClaw docs). citeturn0search3
2. Confirm the config is loaded from `/home/wombatinux/.openclaw/openclaw.json`.
3. Start the Gateway and route channels to the target agent.

## Workspace Notes

- Both agents are read-only by default; trading is gated behind explicit human approval.
- Moltbook observer is intentionally isolated and should remain read-only.

## Next Optional Steps

- Add channel bindings in OpenClaw config (Telegram/WhatsApp/etc.).
- Add explicit sandbox rules per agent in OpenClaw config.
- Add MCP endpoints to the ERC-8004 registration file once live.
