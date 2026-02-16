# Codebase Deep Dive — Observations & Discrepancy Log

**Purpose:** Systematic observation of the entire codebase (documentation + code). No edits. Single living document.

**Started:** 2026-02-09  
**Verification pass:** 2026-02-09 — all claims below reviewed against the codebase; corrections and verification notes applied.

---

## 1. Root Structure & Top-Level Docs

### 1.1 Root directory
- **Notable dirs:** `.claude/`, `acquisition-pipeline/`, `cloned-repos/`, `config/`, `data/`, `docs/`, `dashboard/`, `hyperliquid-*`, `irie-milady/`, `openclaw/`, `openclaw-trading-assistant/`, `openclaw-workspace/`, `rasta-voice/`, `src/`, `systemd/`, `ntt-deployment/`, `mon-bridge/`, `base-migration/`, `website-ralph-loop/`, `stability-ralph-loop/`.
- **raspberry-pi/:** **Exists at project root** (10 files: auto_deploy.sh, configure_sd.ps1, deploy.sh, firstboot.sh, megaphone.py, monitor.sh, rasta-megaphone.service, requirements.txt, setup_pi.sh, voice_config.json). Earlier glob search had missed it. **No discrepancy.**
- Many root-level `.md` and `.py` scripts (e.g. `add_browser_live.py`, `analyze_growth_log.py`, `blink-plugs.py`) outside `src/`.

### 1.2 CLAUDE.md vs AGENTS.md
- **CLAUDE.md:** 15 principles (11 hard, 4 soft); 10 pitfalls; 82+ endpoints; 14 grow tools; 26 MCP tools; 4 subprocesses for `run.py all`.
- **AGENTS.md:** Same machine roles; references `SYSTEM_OVERVIEW.md`. **Verified:** SYSTEM_OVERVIEW.md exists at repo root.
- **Discrepancy (minor):** CLAUDE dev commands use `python`; AGENTS says "Prefer `python3` on WSL/Linux".

---

## 2. Config & Principles/Pitfalls Counts

- **config/ contents:** `pitfalls.yaml`, `principles.yaml`, `openclaw.json`, `hardware.yaml.example`. No `hardware.yaml` in tree (only `.example`). Docs refer to `config/hardware.yaml` for device mapping — likely runtime-copied or .gitignored; **discrepancy:** file not present in repo.
- **principles.yaml:** 15 principles total. Hard: 11 (safety-first, prop64-compliance, dark-period-sacred, max-water-daily, sensor-grounding, no-phantom-actions, no-hashtags, no-leaf-emoji, human-approval-gate, daily-spend-limit, never-impersonate). Soft: 4 (stateless-restart, patois-voice, quality-over-quantity, agent-identity). **Matches** CLAUDE “15 (11 hard, 4 soft)”.
- **pitfalls.yaml:** 10 entries. **Matches** CLAUDE “10 machine-readable gotchas”.

---

## 3. Run Entrypoints & Subprocesses

- **run.py:** Entrypoint is `main()`; commands: `server`, `orchestrator`, `social`, `all`, `init`, `test`. Docstring says “Run both” for `all` but actually runs four components.
- **run_all():** Starts (1) server as `multiprocessing.Process`, (2) social daemon as Process, (3) trading agent as Process; (4) runs **orchestrator in the main process** (not a subprocess). Watchdog respawns social/trading every 30s check if dead.
- **Discrepancy:** CLAUDE and SYSTEM_ATLAS say “4 subprocesses” and “launches 4 subprocesses (FastAPI, social daemon, orchestrator, trading agent)”. In code, only **3** are subprocesses; the orchestrator runs in the main process. So “4 components” is accurate; “4 subprocesses” is not.
- **Resilient orchestrator:** run.py tries `orchestrator_resilient.ResilientOrchestrator` first, else `orchestrator.GrokMonOrchestrator`. Not mentioned in CLAUDE module table; SYSTEM_ATLAS does mention `orchestrator_resilient.py`.
- **run.sh:** Referenced as “Legacy convenience wrapper for archived agent” (SYSTEM_ATLAS). Not yet inspected for actual usage of `agent_legacy`.

---

## 4. API Endpoint Count

- **app.py:** Defines many routes via `@app.get(...)` and `@app.post(...)` (sensors, ai, grow, webcam, reviews, agent/*, timelapse, banner, auth, vpd, schedule, social, stats, plant-progress, predictions, etc.). Grep shows 90+ route decorators in app.py alone.
- **Routers:** admin.py has **12** route decorators (get/post), not 14; a2a.py, playlist.py, overlays.py, telegram_portal.py add more. **Verified:** grep @router.(get|post) in admin.py = 12.
- **Discrepancy:** CLAUDE says “82+ endpoints”. Actual count is likely **above 82** (app.py alone has ~90+ route definitions). So “82+” may be a conservative or outdated figure; no discrepancy if interpreted as minimum.

---

## 5. Source Module Map vs Docs

- **src/** layout matches CLAUDE table: orchestrator, ai/, brain/, api/, hardware/, core/, social/, telegram/, payments/, review/, learning/, streaming/, blockchain/, cultivation/, mailer/, mcp/, db/, safety/, media/, analytics/, mqtt/, voice/, collaboration/, notifications/, scheduling/, web/, tools/.
- **Extra not in CLAUDE table:** `src/a2a/` (10 .py files), `src/tasks/` (irie cache warmer), `src/orchestrator_resilient.py` (mentioned in SYSTEM_ATLAS only). **src/govee.py** exists at top level alongside `src/hardware/govee.py` — possible re-export or legacy; not documented.
- **raspberry-pi/:** CLAUDE and AGENTS say “See raspberry-pi/ directory” and “raspberry-pi/”. **No top-level `raspberry-pi/` directory.** Corrected: raspberry-pi/ exists at root (see §1.1).
- **SYSTEM_OVERVIEW.md:** Exists at repo root. Last Updated 2026-01-21. Says “Day 1 - Fresh clone in vegetative” and “Expected Harvest: Late April 2026”. CLAUDE “Current Grow” says “Veg (Feb 2026)”, “Late April / Early May 2026” — harvest window consistent; “Day 1” may be stale.

---

## 6. Documentation Cross-References

- **SYSTEM_ATLAS.md** references SYSTEM_OVERVIEW.md for “LIVE” status; references docker-compose.yml. **Verified:** docker-compose.yml exists at project root.
- **AGENTS.md** instruction hierarchy: “System map / reality: docs/SYSTEM_ATLAS.md and SYSTEM_OVERVIEW.md” — both files exist.

---

## 7. AI Tools vs MCP Tools (Counts)

- **src/ai/tools.py:** 35+ named tools. CLAUDE "14 grow tools" = cultivation subset; no discrepancy.
- **src/mcp/tools.py:** TOOLS list has 22 tool names. CLAUDE/SYSTEM_ATLAS say 26. **Discrepancy:** 22 vs 26.

## 8. run.sh and Legacy Agent

- run.sh line 76: `CMD="python -m src.brain.agent"`. No `src/brain/agent.py`; only `agent_legacy.py`. **Discrepancy:** run.sh would fail; legacy entrypoint broken.

## 9. KasaActuatorHub

- kasa.py: set_device, water, inject_co2 only. .cursorrules match.

## 10. Social & Cloudflare

- engagement_daemon.py: multiple channels/loops; consistent with "10 loops, 6+ platforms".
- cloudflare-worker-router.js: STATIC_PATHS include /.well-known/, /mcp/; API to origin. Matches docs.
- src/web/.well-known/ and pages-deploy/.well-known/ both have agent-card.json, agent-registration.json, agent.json, x402-pricing.json. Matches CLAUDE.

## 11. Systemd & Docker

- systemd/ contains: grokmon.service, ganjamon-endpoint.service, light-compensation.service, light-compensation.timer. No file named ganja-mon-bot.service. **Discrepancy:** SYSTEM_ATLAS and CLAUDE reference "systemd/ganja-mon-bot.service" (Telegram community bot); that file is not in systemd/. ganjamon-endpoint.service is for trading agent endpoint (port 8080), not the Telegram bot.
- docker-compose.yml exists at project root. SYSTEM_ATLAS reference to docker-compose.yml is valid.

## 12. AI Decision Interval

- orchestrator.py default ai_interval_seconds=7200 (2 hours). run.py run_orchestrator() passes ai_interval_seconds=1800 (30 minutes). **Discrepancy:** CLAUDE and orchestrator docstring say "every 2 hours" / "injected every 2h"; production when started via run.py all uses 30-minute AI cycle.

## 13. Safety & Watering Limits

- principles.yaml references "src/safety/guardian.py" and "guardian.validate_action()". **Verified:** guardian.py defines SafetyGuardian and SafeActuatorHub; there is **no** method named `validate_action`. Safety is enforced via SafeActuatorHub (set_device, water, inject_co2) calling guardian.enforce_light_command(), enforce_water_command(), etc. So the principle's *context* is slightly stale (wrong method name); the *rule* (SafetyGuardian approval) is implemented.
- WATERING_SAFEGUARDS.md: Seedling 300ml, Veg/Flower 1500ml, Late Flower 1000ml, Clone 500ml. guardian.py SafetyLimits.water_daily_limits: seedling 200, veg/vegetative 400, flower/flowering 800, late_flower 600, clone 500. **Discrepancy:** Doc and code daily limits differ (e.g. seedling 300 vs 200; veg 1500 vs 400).

## 14. Summary of Discrepancies (Consolidated)

| Item | Doc / Claim | Observed | Severity |
|------|-------------|----------|----------|
| 4 subprocesses | CLAUDE, SYSTEM_ATLAS, grokmon.service comment | 3 subprocesses + orchestrator in main process | Minor (wording) |
| raspberry-pi/ directory | CLAUDE, AGENTS | **Corrected:** raspberry-pi/ exists at root (10 files) | N/A (no discrepancy) |
| config/hardware.yaml | CLAUDE, SYSTEM_ATLAS | Only hardware.yaml.example in config/ | Low (may be generated) |
| run.sh legacy agent | run.sh | python -m src.brain.agent; no agent.py (only agent_legacy.py) | High (script broken) |
| ganja-mon-bot.service | SYSTEM_ATLAS, CLAUDE | Not in systemd/; ganjamon-endpoint.service is | Medium (wrong path or missing file) |
| AI interval "2h" | CLAUDE, orchestrator docstring | run.py passes 1800 (30 min) | Medium (docs stale) |
| MCP tools count | CLAUDE "26 tools" | 22 in TOOLS list in mcp/tools.py | Low (count or subset) |
| WATERING_SAFEGUARDS vs guardian | WATERING_SAFEGUARDS.md daily limits | guardian.py water_daily_limits differ | Medium (doc or code stale) |
| SECURITY_HARDENING*.md | SYSTEM_ATLAS "documents hardening steps" | No such file in docs/ or root | Low (missing doc) |
| Episodic memory path | Single store | Orchestrator: data/episodic_memory.json; app.py brain-activity: data/logs/episodic_memory.json | Medium (dashboard may miss data) |

## 15. Stale Docstrings / Cross-References

- **unified_context.py** module docstring: Refers to "Grow Brain (src/brain/agent.py)", "agent.py build_context_message()", and "GrokAndMonAgent". Production uses orchestrator + src/ai/brain.py; agent_legacy is archived. **Stale:** docstring describes legacy flow.
- **SYSTEM_ATLAS "Key Docs Index"** lists README.md, QUICKSTART.md, IMPLEMENTATION_GUIDE.md, IMPLEMENTATION_PLAN.md, TECHNICAL_SUMMARY.md. QUICKSTART.md exists at root; IMPLEMENTATION_PLAN.md in docs/; IMPLEMENTATION_GUIDE.md and TECHNICAL_SUMMARY.md not found in docs/ (only IMPLEMENTATION_PLAN.md and PROJECT_HISTORY.md reference them). **Possible missing or renamed docs.**

## 16. Trading Agent Integration

- run.py _run_trading_agent(): cwd=cloned-repos/ganjamon-agent, PYTHONPATH=agent_dir/src, command `python -m main`. ganjamon-agent has src/main.py; running with -m main and PYTHONPATH=src resolves to that main. **Consistent.**
- **GROKMON_BASE_URL:** Verified in ganjamon-agent. `src/main.py` uses ENABLE_GROKMON_SYNC, GROKMON_BASE_URL (default http://localhost:8000), GROKMON_SYNC_INTERVAL_SECONDS (300), GROKMON_TIMEOUT_SECONDS (10). `.env.example` documents same. Plant sync via GrokMonClient; PlantMaster in `intelligence/plant_master.py` uses client.fetch_snapshot() for plant status. **Matches** AGENTS.md.

## 17. Cultivation & DB

- src/cultivation: __init__.py, stages.py, vpd.py. Exports get_stage_parameters, calculate_vpd, GrowthStage, etc. **Matches** CLAUDE.
- guardian.py SafetyLimits use stage names: clone, seedling, early_veg, veg, vegetative, flower, flowering, late_flower. **cultivation/stages.py** GrowthStage enum: GERMINATION, SEEDLING, VEGETATIVE, TRANSITION, FLOWERING, LATE_FLOWER, HARVEST. Guardian has extra granularity (clone, early_veg, flower vs flowering) and no GERMINATION/HARVEST in water_daily_limits. **Minor mismatch:** stage name sets overlap but are not identical; guardian may need to map enum to its keys.

---

## 18. Govee Modules (Two Files)

- **src/govee.py:** Standalone module for Govee H5179 (BLE/cloud/local), 700+ lines. Not imported by orchestrator or API.
- **src/hardware/govee.py:** GoveeSensorHub used by app.py, orchestrator, agent_legacy, MCP tools, hardware/__init__.py. Same API-key docstring line as src/govee.py (suggesting copy or shared origin).
- **Observation:** Only hardware/govee.py is in the import graph. src/govee.py appears to be duplicate or legacy; could be consolidated or documented as alternate/standalone driver.

---

## 19. SECURITY_HARDENING and PERMISSIONS

- **SYSTEM_ATLAS** line 160: "SECURITY_HARDENING*.md documents hardening steps." No file matching SECURITY_HARDENING*.md in docs/ or project root. **Discrepancy:** Referenced docs missing (or in a different repo).
- **PERMISSIONS.md:** SYSTEM_ATLAS "Key Docs" and "Built" list "PERMISSIONS.md for OpenClaw skills." Found at openclaw-workspace/ganjamon/PERMISSIONS.md, not at project root. **No discrepancy** if doc means OpenClaw workspace.

---

## 20. README at Root

- **SYSTEM_ATLAS "Key Docs Index"** lists README.md at root. **Verified:** Root directory listing (with common ignores) does not include README.md; glob for README.md returns only paths under cloned-repos/, dashboard/, etc. **Conclusion:** No README.md at project root; Key Docs index is wrong or refers to a doc to be added.

---

## 21. Episodic Memory Path Mismatch

- **Orchestrator & brain/memory.py:** Episodic memory is persisted to `data/episodic_memory.json` (orchestrator passes `Path(__file__).parent.parent / "data" / "episodic_memory.json"`; memory.py DEFAULT_PERSIST_PATH = `"data/episodic_memory.json"`). a2a/skills.py also uses `"data/episodic_memory.json"`.
- **app.py (brain-activity / agent state):** Reads episodic memory from `Path("data/logs/episodic_memory.json")` (line 2371).
- **Discrepancy:** Dashboard/API reads from `data/logs/episodic_memory.json` while the orchestrator and EpisodicMemory class write to `data/episodic_memory.json`. The brain-activity endpoint may return empty or stale data unless something else writes to data/logs/. **Recommend:** Unify path (e.g. use same path as orchestrator) or document that data/logs/ is a separate/copy.

---

## 22. Principles & Pitfalls Loading

- **orchestrator.py:** Loads `config/pitfalls.yaml` and `config/principles.yaml` via `Path(__file__).parent.parent / "config" / "pitfalls.yaml"` (absolute from file). **Consistent** with repo layout.
- **a2a/skills.py:** Uses `Path("config/principles.yaml")` (relative to cwd). **Risk:** If server cwd is not project root, this can fail or load wrong file.

---

## 23. Health Endpoints

- **core/health.py:** health_router exposes `GET /health` and `GET /ready` (no prefix). Used for liveness/readiness.
- **app.py register_routes:** Also defines `GET /api/health` ("API health check — hardware-level status"). So two health endpoints: `/health` (core) and `/api/health` (app). **Intentional** (probes vs dashboard API).

---

## 24. API Router Mounting

- Routers included: overlay_router, playlist_router, admin_router (prefix `/api/admin`), health_router, a2a_router; then register_routes(app) adds all @app.get/post in app.py. Static: /.well-known, /static, /assets, /music. **Matches** CLAUDE description.

---

## 25. Orchestrator Resilient vs Base

- **orchestrator_resilient.py:** Thin wrapper; adds signal handlers (SIGTERM, SIGINT), 10s shutdown timeout, cancels _sensor_task and _ai_task on timeout. Base orchestrator has _sensor_task, _ai_task, _reactive_task. **Observation:** Resilient stop() does not cancel _reactive_task on timeout—only sensor and AI tasks. May leave reactive loop running until process exit.

---

## 26. Telegram Token Usage

- **TELEGRAM_BOT_TOKEN:** Used by telegram/bot.py, api/telegram_portal.py, notifications/alerts.py, core/config.py, telegram/bot_clean.py. **TELEGRAM_COMMUNITY_BOT_TOKEN:** Used by ai/tools.py, blockchain/reputation_publisher.py. **Matches** pitfalls and AGENTS.md (community bot vs plant/admin bot).

---

## 27. Reference Docs (CLAUDE Table)

- **OPENCLAW_FRAMEWORK_DEEP_DIVE.md** and **ERC8004_DEEP_DIVE.md** exist in docs/. **Matches** CLAUDE "Deep Dive Documentation" table.

---

## 28. DB GrowthStage vs Guardian Stages

- **db/models.py** GrowthStage enum: SEEDLING, VEGETATIVE, TRANSITION, FLOWERING, LATE_FLOWER, HARVEST (6 values; no GERMINATION). **cultivation/stages.py** GrowthStage enum: GERMINATION, SEEDLING, VEGETATIVE, TRANSITION, FLOWERING, LATE_FLOWER, HARVEST (7 values). **guardian.py** water_daily_limits keys: clone, seedling, early_veg, veg, vegetative, flower, flowering, late_flower. DB has no "clone" or "early_veg"; guardian has no GERMINATION or HARVEST in limits. **Verified.** Stage naming is split across three places; mapping required.

---

## 29. Learning / Grimoire in Orchestrator

- Grimoire: save_all_grimoires(), get_all_grimoire_context(min_confidence=0.4, limit_per_domain=8). Grow learning: get_grow_learning() used in AI context and learning loop. **Matches** CLAUDE "grimoire learnings (confidence ≥ 0.4)" and "grow pattern extraction."

---

## 30. Summary Additions (Discrepancies)

| Item | Doc / Claim | Observed | Severity |
|------|-------------|----------|----------|
| Episodic memory path | Single episodic memory store | Orchestrator writes data/episodic_memory.json; app.py reads data/logs/episodic_memory.json | Medium (dashboard may miss data) |
| Resilient shutdown | Graceful shutdown | _reactive_task not cancelled on timeout | Low |

---

## Final Note

This document is observation-only. No code or config was changed. Discrepancies are noted for future reconciliation (docs vs code, missing files, broken refs). Recommend: fix run.sh to use `src.brain.agent_legacy` or add a runnable agent shim; add or relocate ganja-mon-bot.service if the Telegram bot is deployed via systemd; align WATERING_SAFEGUARDS.md with guardian.py limits; update CLAUDE/SYSTEM_ATLAS "4 subprocesses" to "4 components (3 subprocesses + orchestrator in main)"; update "every 2h" to "every 30 min" when describing run.py all; add SECURITY_HARDENING*.md or remove reference from SYSTEM_ATLAS; unify episodic memory path (use data/episodic_memory.json in app.py brain-activity or document data/logs/).

---

## Verification Summary (2026-02-09)

**Verified as stated:** raspberry-pi/ (10 files at root); config principles 15/11 hard/4 soft and 10 pitfalls; run_all (3 subprocesses + orchestrator in main, watchdog 30s); run.sh invokes `python -m src.brain.agent` and no agent.py exists; KasaActuatorHub set_device/water/inject_co2 only; systemd contents (no ganja-mon-bot.service); docker-compose.yml and SYSTEM_OVERVIEW.md at root; orchestrator ai_interval 1800 in run.py; episodic memory paths (orchestrator data/, app.py data/logs/); a2a Path("config/principles.yaml"); health /health and /api/health; admin prefix /api/admin; orchestrator_resilient does not cancel _reactive_task on timeout; Telegram token split; OPENCLAW/ERC8004 deep dive docs exist; grimoire min_confidence=0.4 in orchestrator; WATERING_SAFEGUARDS vs guardian limits differ; unified_context docstring references legacy agent.py.

**Corrected:** Admin router has 12 route decorators (doc said 14). principles.yaml context "guardian.validate_action()" — no such method; safety is via SafeActuatorHub and enforce_* methods. README.md at root: confirmed absent (Key Docs index incorrect). §28: db/models GrowthStage has 6 values (no GERMINATION); cultivation/stages.py has 7 (includes GERMINATION); guardian dict is separate.

**Unchanged:** All discrepancy table entries and recommendations remain; no code or config was modified.
