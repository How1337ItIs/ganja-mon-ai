# Full Project Reorganization Plan

**Status:** Plan only — no changes made.  
**Goal:** Restructure the repo so layout matches purpose, reduce root clutter, and keep all references working.

This document proposes *file/directory* reorganization. It intentionally separates:
- **No-code-change reorg** (moves/renames that should not require Python/JS edits), vs
- **Code-change reorg** (path refactors like `src/core/paths.py`).

---

## 0. Decision Summary (Pick One)

### Option A (Recommended): Overlay Structure, No Code Changes

Use new “clean” directories as **aliases** (symlinks/junctions) pointing at the current locations, and only physically move things that have no runtime path coupling (docs, one-off scripts, screenshots, etc.).

- Pros: Lowest risk, immediate improvement, can be done incrementally.
- Cons: Requires symlinks/junctions (Windows caveats in §7.5), and the old layout still exists underneath.

### Option B: Full Move + Path Refactor (Code Changes)

Physically move `cloned-repos/ganjamon-agent` to `agents/ganjamon`, etc., and update every path consumer (ideally via a single shared path module).

- Pros: Clean final state, fewer “aliases”.
- Cons: Higher risk; must be executed as a coordinated change set (and tested on Windows + Chromebook).

### Success Criteria (Same For Both Options)

After the reorg, all of the following must still work from the repo root on the Chromebook and Windows/WSL:
- `python3 run.py test`
- `python3 run.py all` starts without missing-path errors (FastAPI + orchestrator + social + trading subprocess)
- `GET /api/health` succeeds and A2A endpoints load trading JSON/DB from the expected trading data directory
- Cloudflare Pages deploy still targets a `pages-deploy/` directory and the Worker router continues routing as before
- Ralph sync still works (Chromebook push + Windows pull) without manual path edits each time

### Hard Constraints / Invariants

- The **repo root path** used by systemd on the Chromebook (`/home/natha/projects/sol-cannabis`) should remain unchanged unless explicitly migrating the whole repo.
- The trading agent is a **subprocess** of `run.py all`; its working directory assumptions are part of the runtime contract.
- `pages-deploy/` is the **production Cloudflare Pages bundle** (keep the deploy target stable, even if the sources are reorganized).

### Preflight Inventory (Do This First)

Before moving anything, generate an “actual references” list so the checklist stays honest:
- `rg -n "cloned-repos/ganjamon-agent|cloned-repos/farcaster-agent|pages-deploy|rasta-voice" -S .`
- `rg -n "/home/natha/projects/sol-cannabis|/mnt/c/Users/natha/sol-cannabis" -S .`
- Confirm whether `dashboard/` has any build step that writes into `pages-deploy/` (if yes, capture the exact command and expected output paths).

## 1. Current Problems

### 1.1 Root is overloaded
- **40+ one-off scripts** at root (`add_browser_live.py`, `blink-plugs.py`, `capture_dashboard.py`, etc.) mixed with entrypoints (`run.py`, `run.sh`).
- **Many loose Markdown files** (AGENT_INDEX*.md, BRANDING_REFINEMENT.md, BRIDGING_TO_MONAD.md, etc.) that are docs/notes, not project config.
- **Multiple Cloudflare assets** at root: `cloudflare-worker-*.js`, `wrangler*.toml` (8+ files).
- **Dashboard** at root as a sibling to `src/web/` and `pages-deploy/`, so “frontend” is split across three places.

### 1.2 “cloned-repos” is a grab bag
- **70+ subdirs** including:
  - **First-party / integrated:** `ganjamon-agent` (run by `run.py all`), `farcaster-agent` (used by `src/social/farcaster.py`), `8004-contracts` (ABI used by ganjamon-agent script).
  - **Reference / research:** ERC-8004 examples, Hyperliquid/Solana/Polymarket bots, elizaos, langgraph, etc.
  - **Third-party mirrors:** openclaw skills, coinbase-agentkit, austintgriffith, zscole, etc.
- Naming doesn’t distinguish “we run this” vs “we read from this” vs “reference only.”

### 1.3 Sibling first-party projects are scattered
- **Trading:** `cloned-repos/ganjamon-agent` (core) vs `hyperliquid-trading-bot`, `hyperliquid-ai-trading-bot` at root.
- **OpenClaw:** `openclaw/`, `openclaw-trading-assistant/`, `openclaw-workspace/` at root; more OpenClaw-related stuff in `cloned-repos/`.
- **Voice:** `rasta-voice/` at root; `src/voice/`, `src/streaming/` in `src/`.
- **NFT/art:** `irie-milady/` at root; referenced by `src/tasks/irie_cache_warmer.py` and `src/web/iriemilady.html`.
- **Bridge/chain:** `ntt-deployment/`, `mon-bridge/` at root; token/bridge docs in `docs/`.

### 1.4 Paths are hardcoded in many places
- **Core app** assumes project root and `cloned-repos/ganjamon-agent` (see Reference Map below).
- **Ganjamon-agent** assumes it lives at `.../cloned-repos/ganjamon-agent` and references siblings like `cloned-repos/8004-contracts`, `cloned-repos/hyperliquid-sdk`, and absolute paths like `/home/natha/projects/sol-cannabis/...` and `/mnt/c/Users/natha/sol-cannabis/...`.
- **Systemd** uses fixed path: `WorkingDirectory=/home/natha/projects/sol-cannabis`.

---

## 2. Reference Map (Do Not Break)

All references that must continue to work after any reorg.

### 2.1 From project root / `run.py` / systemd
| Consumer | Path / usage |
|----------|----------------|
| `run.py` | `Path(__file__).parent / "cloned-repos" / "ganjamon-agent"` (agent dir + cwd for subprocess) |
| `systemd/grokmon.service` | `WorkingDirectory=/home/natha/projects/sol-cannabis`, `ExecStart=... run.py all` |
| Deploy (CLAUDE.md) | `pages-deploy/` for Cloudflare Pages |

### 2.2 From `src/` (Python)
| File | Path / usage |
|------|----------------|
| `src/brain/unified_context.py` | `PROJECT_ROOT / "cloned-repos" / "ganjamon-agent" / "data"` (TRADING_DATA) |
| `src/api/app.py` | `_PROJECT_ROOT / "cloned-repos" / "ganjamon-agent" / "data"` (_TRADING_DATA) |
| `src/api/a2a.py` | `"cloned-repos/ganjamon-agent/data/signal_feed.json"` (and validated_signals, consciousness) — relative to cwd |
| `src/blockchain/reputation_publisher.py` | `Path("cloned-repos/ganjamon-agent/data/experience.db")` |
| `src/social/engagement_daemon.py` | `... / "cloned-repos" / "ganjamon-agent"` (path to agent dir) |
| `src/social/farcaster.py` | `... / "cloned-repos" / "farcaster-agent"` (FARCASTER_AGENT_DIR) |
| `src/voice/personality.py` | `... / "cloned-repos" / "ganjamon-agent" / "SOUL.md"`, `... / "openclaw-workspace" / "ganjamon" / "SOUL.md" |
| `src/streaming/rasta_tts.py` | `... / "rasta-voice" / ".env"`, rasta-voice for voice_config.json |
| `src/voice/manager.py` | `base / "rasta-voice" / "rasta_pipeline_eleven.py"`, `rasta_live.py` |
| `src/media/ganjafy.py` | `... / "pages-deploy" / "assets" / "MON_official_logo.jpg"` |
| `src/telegram/agent_brain.py` | Hardcoded list: `Path("/home/natha/.../cloned-repos/ganjamon-agent/data")`, `Path("/mnt/c/Users/natha/...")` |
| `src/telegram/trading_context.py` | Same hardcoded list as agent_brain.py |
| `src/tasks/irie_cache_warmer.py` | Collection slug "irie-milady-maker" (no path; Scatter.art URL) |

All other `src/` references to `data/`, `src/web/`, etc. use `PROJECT_ROOT` or `Path(__file__).parent...`; if project root moves, a single `PROJECT_ROOT` (or env `GROKMON_ROOT`) would need to be set once.

### 2.3 From `cloned-repos/ganjamon-agent`
| File | Path / usage |
|------|----------------|
| `.ralph/ralph_sync.sh` | `REPO_DIR="/home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent"` |
| `.ralph/run-loop.sh` | `PROJECT_DIR="/mnt/c/Users/natha/sol-cannabis/cloned-repos/ganjamon-agent"` |
| `.ralph/scheduled_ralph.sh` | Same REPO_DIR / PROJECT_DIR pattern |
| `.ralph/upgrade_loop.sh` | Same |
| `start.sh` | `cd /home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent`, PYTHONPATH=.../ganjamon-agent/src |
| `scripts/register_erc8004_monad.py` | `parents[2] / "cloned-repos" / "8004-contracts" / "abis" / "IdentityRegistry.json"` (i.e. sol-cannabis root) |
| `src/learning/self_improvement.py` | `CLONED_REPOS_PATH = ...parent.parent.parent.parent` (cloned-repos/), `AGENT_DATA_PATH = .../data` |
| `src/clients/hyperliquid.py` | `HYPERLIQUID_SDK_PATH` env or `/mnt/c/Users/natha/sol-cannabis/cloned-repos/hyperliquid-sdk` |
| `src/clients/polymarket.py` | `POLYMARKET_AGENTS_PATH` env or `/mnt/c/Users/natha/sol-cannabis/cloned-repos/polymarket-agents` |

### 2.4 From `scripts/`
| File | Path / usage |
|------|----------------|
| `scripts/agent_doctor.py` | `PROJECT_ROOT / "cloned-repos" / "ganjamon-agent"` |

### 2.5 From root one-off scripts
| File | Path / usage |
|------|----------------|
| `clone_zscole_repos.py` | `"cloned-repos" / "zscole"` |

### 2.6 Docs / config
| File | Path / usage |
|------|----------------|
| CLAUDE.md, AGENTS.md, docs/SYSTEM_ATLAS*.md | Mention `cloned-repos/ganjamon-agent`, `pages-deploy/`, `rasta-voice/`, etc. — update after reorg. |
| config/ | hardware.yaml, openclaw.json, etc. — no cloned-repos path. |

### 2.7 Cloudflare / deploy
- Worker router and wrangler configs reference routes and `pages-deploy/` by name; no absolute paths.
- Deploy command: `npx wrangler pages deploy pages-deploy/ --project-name=grokandmon`.

---

## 3. Proposed New Layout

### 3.1 Principle
- **Single project root** remains the “Grok & Mon” app root (where `run.py`, `src/`, `data/`, `config/` live). No change to repo root path for systemd; only internal layout changes.
- **First-party vs third-party:** Group by “we run it / we read it” vs “reference only.”
- **One place for frontend build output:** Keep `pages-deploy/` as the only deploy target; optionally source from a single frontend app (e.g. move `dashboard/` into a unified app that builds to `pages-deploy/`).
- **One place for “agents we run”:** So `run.py` and docs point at one clear directory.

### 3.2 Proposed directory tree (high level)

```
sol-cannabis/                          # repo root (unchanged path for systemd)
├── run.py
├── run.sh
├── config/
├── data/
├── src/                               # unchanged
├── systemd/
├── .claude/, .env*, .gitignore
│
├── agents/                            # NEW: first-party agents we run or read from
│   ├── ganjamon/                      # was cloned-repos/ganjamon-agent
│   ├── farcaster/                     # was cloned-repos/farcaster-agent
│   └── (optional) shared refs used by agents, see below)
│
├── frontend/                          # NEW: all UI and deploy artifact
│   ├── app/                           # optional: unified app (e.g. dashboard + pages)
│   ├── pages-deploy/                  # build output for Cloudflare Pages (keep name for wrangler)
│   └── cloudflare/                   # workers + wrangler configs
│       ├── worker-router.js
│       ├── worker-ganjafy.js
│       └── wrangler*.toml
│
├── voice/                             # NEW: was rasta-voice/
│   └── (rasta pipeline, .env, voice_config.json)
│
├── projects/                          # NEW: other first-party subprojects (not “cloned”)
│   ├── openclaw/                      # was openclaw/
│   ├── openclaw-trading-assistant/
│   ├── openclaw-workspace/
│   ├── ntt-deployment/
│   ├── mon-bridge/
│   ├── irie-milady/
│   ├── hyperliquid-trading-bot/
│   ├── hyperliquid-ai-trading-bot/
│   ├── acquisition-pipeline/
│   ├── dxt-extension/
│   ├── esp32_firmware/
│   ├── raspberry-pi/
│   └── website-ralph-loop/
│   └── stability-ralph-loop/
│   └── streaming/                     # config only; code stays in src/streaming
│
├── refs/                              # NEW: was cloned-repos (reference only)
│   ├── 8004-contracts/                # keep; ganjamon script reads ABI from here
│   ├── hyperliquid-sdk/
│   ├── polymarket-agents/
│   ├── gmgn-api-wrapper/
│   ├── dexscreener-*/
│   ├── erc-8004-*/
│   ├── (all other current cloned-repos that we don’t “run”)
│   └── zscole/                        # clone_zscole_repos.py target
│
├── scripts/                           # keep; move root one-off scripts here
│   ├── agent_doctor.py
│   ├── add_browser_live.py
│   ├── blink-plugs.py
│   └── ...
│
├── docs/                              # keep; move root *.md here (except CLAUDE.md, AGENTS.md, README)
│   ├── PROJECT_REORGANIZATION_PLAN.md (this file)
│   ├── SYSTEM_ATLAS.md
│   ├── AGENT_INDEX*.md
│   ├── BRANDING_REFINEMENT.md
│   └── ...
│
├── gists/                             # keep (or move under refs/gists)
├── packages/                          # keep
├── reports/                           # keep
├── obs-config/                        # keep
├── CLAUDE.md
├── AGENTS.md
└── README.md (if any)
```

### 3.3 Optional variant: keep “cloned-repos” name, only subgroup
If you prefer not to rename the folder (to avoid churn in ganjamon-agent’s Ralph scripts and comments):
- Add **`agents/`** at root with `ganjamon` and `farcaster` as **symlinks** to `cloned-repos/ganjamon-agent` and `cloned-repos/farcaster-agent`.
- Then **gradually** change code to use `agents/ganjamon` and `agents/farcaster`; once done, you can physically move and remove the symlinks.
- **refs/** could stay as **`cloned-repos`** and only be reorganized inside (e.g. `cloned-repos/integrated/8004-contracts`, `cloned-repos/research/...`) so that `register_erc8004_monad.py` becomes `cloned-repos/integrated/8004-contracts` or we introduce one env var for “contracts root.”
- **Windows:** Creating directory symlinks usually requires Developer Mode or Administrator; prefer WSL or the copy-then-delete approach if on Windows. See §7.5.

---

## 4. Reference Updates Required (Checklist)

If you implement the **full** reorg (not symlink variant), every reference below must be updated (or guarded by a single root env var).

### 4.1 Core runtime
- [ ] **run.py:** `cloned-repos/ganjamon-agent` → `agents/ganjamon` (and cwd for subprocess).
- [ ] **systemd:** No path change if repo root stays same; only if you move repo.

### 4.2 src/
- [ ] **unified_context.py:** `cloned-repos/ganjamon-agent/data` → `agents/ganjamon/data`.
- [ ] **app.py:** _TRADING_DATA → `agents/ganjamon/data`.
- [ ] **a2a.py:** Use **paths.py** (TRADING_DATA, PROJECT_ROOT) for all data paths so resolution is cwd-independent. Paths → `agents/ganjamon/data/...` (see §7.1).
- [ ] **reputation_publisher.py:** Use **paths.py** TRADING_DATA for `experience.db` (e.g. `TRADING_DATA / "experience.db"`). See §7.1.
- [ ] **engagement_daemon.py:** path to agent dir → `agents/ganjamon`.
- [ ] **farcaster.py:** `cloned-repos/farcaster-agent` → `agents/farcaster`.
- [ ] **voice/personality.py:** `cloned-repos/ganjamon-agent/SOUL.md` → `agents/ganjamon/SOUL.md`; `openclaw-workspace/ganjamon` → `projects/openclaw-workspace/ganjamon`.
- [ ] **streaming/rasta_tts.py:** `rasta-voice` → `voice` (or keep `rasta-voice` as symlink to `voice`).
- [ ] **voice/manager.py:** `rasta-voice` → `voice`.
- [ ] **media/ganjafy.py:** `pages-deploy/assets/...` → if you move workers under `frontend/cloudflare`, keep `pages-deploy` path or use PROJECT_ROOT.
- [ ] **telegram/agent_brain.py** and **trading_context.py:** Replace hardcoded paths with `PROJECT_ROOT / "agents" / "ganjamon" / "data"` (and PROJECT_ROOT from env or `Path(__file__).parent.parent.parent`).

### 4.3 agents/ganjamon (ex ganjamon-agent)
- [ ] **.ralph/*.sh:** Set `REPO_DIR` / `PROJECT_DIR` to new path (or use `SCRIPT_DIR` resolution so it works from any clone location).
- [ ] **start.sh:** Same.
- [ ] **scripts/register_erc8004_monad.py:** After reorg, repo root is **parents[3]** (not parents[2]); use `parents[3] / "refs" / "8004-contracts" / "abis" / "IdentityRegistry.json"`. See §7.2 for current-bug fix.
- [ ] **src/clients/hyperliquid.py:** Default path or env to `refs/hyperliquid-sdk` (or keep under refs with same name).
- [ ] **src/clients/polymarket.py:** Default path or env to `refs/polymarket-agents`.
- [ ] **src/learning/self_improvement.py:** REPO root = **parents[4]**; set CLONED_REPOS_PATH = repo_root / `"refs"`; AGENT_DATA_PATH stays relative to agent. See §7.3.

### 4.4 Scripts and root
- [ ] **scripts/agent_doctor.py:** `cloned-repos/ganjamon-agent` → `agents/ganjamon`.
- [ ] **clone_zscole_repos.py:** `cloned-repos/zscole` → `refs/zscole`.

### 4.5 Docs and config
- [ ] **CLAUDE.md, AGENTS.md:** Update all paths (`cloned-repos/ganjamon-agent` → `agents/ganjamon`, `rasta-voice` → `voice`, `pages-deploy` → `frontend/pages-deploy` if moved, etc.).
- [ ] **docs/SYSTEM_ATLAS.md,** **docs/SYSTEM_ATLAS_SUBREPOS.md:** Same path updates and renames.
- [ ] **.claude/context/*.md**, **memory/** (if any): Same.

### 4.6 Sync and external
- [ ] **ganjamon sync_from_ralph.sh** (Windows pull): Documented in AGENTS.md; if agent moves to `agents/ganjamon`, path in that script (and any Windows shortcut) must match.
- [ ] **Ralph on Chromebook:** Pushes from `agents/ganjamon`; ensure `REPO_DIR` and git remote remain correct.

---

## 5. Safe Execution Order

### Option A: Overlay Structure (No Code Changes)

1. **Create alias directories (symlink/junction)**
   - Create `agents/ganjamon` aliasing `cloned-repos/ganjamon-agent`.
   - Create `agents/farcaster` aliasing `cloned-repos/farcaster-agent`.
   - (Optional) Create `refs` aliasing `cloned-repos` if you want new naming without moving anything yet.

   Example (WSL/Linux):

   ```bash
   mkdir -p agents
   ln -s ../cloned-repos/ganjamon-agent agents/ganjamon
   ln -s ../cloned-repos/farcaster-agent agents/farcaster
   ln -s cloned-repos refs
   ```

   Example (Windows junctions):

   ```bat
   mkdir agents
   mklink /J agents\\ganjamon cloned-repos\\ganjamon-agent
   mklink /J agents\\farcaster cloned-repos\\farcaster-agent
   mklink /J refs cloned-repos
   ```

2. **Physically move “safe” clutter out of root**
   - Move root `*.md` (except `CLAUDE.md`, `AGENTS.md`, `README.md`) into `docs/` (or a subfolder like `docs/notes/` if you want categorization).
   - Move one-off root scripts into `scripts/`.
   - Move screenshots/assets into `assets/` if they are currently loose in root.
   - Do **not** move `run.py`, `run.sh`, `src/`, `data/`, `config/`, `systemd/`, `pages-deploy/` in this option.

3. **Verify**
   - Run the Success Criteria checks in §0.

4. **Rollback**
   - Remove the aliases and revert the doc/script moves if anything unexpectedly depended on root-relative paths.

### Option B: Full Move + Path Refactor (Requires Code Changes)

1. **Introduce a single root variable (mandatory)**
   - Add **`src/core/paths.py`** (or equivalent) with `PROJECT_ROOT`, `AGENT_DIR`, `TRADING_DATA`, `REFS_ROOT` (see §7.1). Optionally allow `GROKMON_ROOT` env to override project root.
   - Have **a2a.py**, **reputation_publisher.py**, **app.py**, **unified_context.py**, and **run.py** use these instead of building paths inline.
   - Goal: future directory moves become “change one module or one env var,” not “hunt 20 call sites.”

2. **Create new structure without removing old**
   - Create `agents/`, `projects/`, `refs/`, `frontend/` (if used).
   - **Copy** (do not move) first-party agent dirs: `ganjamon-agent` → `agents/ganjamon`, `farcaster-agent` → `agents/farcaster`. Copy reference repos into `refs/` as needed. Move other first-party projects into `projects/`.
   - Optionally move Cloudflare files into `frontend/cloudflare/` (document new wrangler cwd; see §7.4).
   - Move root `*.md` (except `CLAUDE.md`, `AGENTS.md`, `README.md`) into `docs/`.
   - Move root one-off `*.py` / `*.js` into `scripts/`.

3. **Update references in batches**
   - Batch 1: `run.py`, `src/brain/unified_context.py`, `src/api/app.py`, `src/api/a2a.py`, `src/blockchain/reputation_publisher.py`, `src/social/engagement_daemon.py`, `src/social/farcaster.py`.
   - Batch 2: `src/voice/*`, `src/streaming/rasta_tts.py`, `src/media/ganjafy.py`, `src/telegram/agent_brain.py`, `src/telegram/trading_context.py`.
   - Batch 3: `agents/ganjamon` (ralph, start.sh, register_erc8004_monad.py, hyperliquid.py, polymarket.py, self_improvement.py).
   - Batch 4: `scripts/agent_doctor.py`, `clone_zscole_repos.py`, docs, `CLAUDE.md`, `AGENTS.md`.

4. **Switch and remove**
   - Point systemd (and any cron) at the same repo root; confirm `run.py all` and API and trading agent and social daemon all run.
   - **Then** delete `cloned-repos/ganjamon-agent` and `cloned-repos/farcaster-agent` (and later migrate remaining cloned-repos into `refs/`). Remove deprecated root scripts/docs that were moved.

5. **Verification**
   - Run the Success Criteria checks in §0.

6. **Rollback**
   - Keep the original directories until verification is complete; if anything fails, revert the path switch to the original locations (or re-introduce aliases as an emergency bridge).

---

## 6. Summary

| Area | Change | Risk if missed |
|------|--------|----------------|
| **Ganjamon agent** | `cloned-repos/ganjamon-agent` → `agents/ganjamon` | run.py, unified_context, app, a2a, reputation_publisher, engagement_daemon, personality, telegram, agent_doctor, ralph/start scripts, register_erc8004, HL/Polymarket paths |
| **Farcaster** | `cloned-repos/farcaster-agent` → `agents/farcaster` | farcaster.py |
| **8004-contracts** | Stay under refs (or cloned-repos) | register_erc8004_monad.py (path to abis) |
| **Rasta voice** | `rasta-voice` → `voice` | rasta_tts.py, voice/manager.py |
| **OpenClaw / others** | Into `projects/` | personality.py (openclaw-workspace), docs |
| **Cloudflare** | Optional `frontend/cloudflare/` | Deploy scripts, wrangler cwd |
| **Root scripts/docs** | Into `scripts/` and `docs/` | None (no code paths) |
| **Single PROJECT_ROOT** | Centralize in path module or env | Prevents future breakage when moving again |

This plan avoids changing behavior; it only reorganizes files and updates every reference listed above so nothing breaks.

---

## 7. Deep Analysis: Flaws and Corrections

The following issues were identified via sequential analysis. Apply these corrections when implementing.

### 7.1 Path resolution: use a single root (mandatory)

- **a2a.py** and **reputation_publisher.py** use bare `Path("...")` relative to CWD. If the server or a script is ever run from another directory (e.g. `scripts/` or `src/`), paths break.
- **Correction:** Introduce **`src/core/paths.py`** (or equivalent) with:
  - `PROJECT_ROOT` (from `Path(__file__).resolve().parents[2]` in that module, or from env `GROKMON_ROOT` if set)
  - `AGENT_DIR = PROJECT_ROOT / "agents" / "ganjamon"` (after reorg)
  - `TRADING_DATA = AGENT_DIR / "data"`
  - `REFS_ROOT = PROJECT_ROOT / "refs"`
- Have **a2a.py**, **reputation_publisher.py**, **app.py**, **unified_context.py** (and any other consumers) **import these from paths.py** instead of building paths inline. Then one change (or one env var) propagates everywhere.

### 7.2 register_erc8004_monad.py — parent depth and current bug

- **Current:** File is `cloned-repos/ganjamon-agent/scripts/register_erc8004_monad.py`. So `Path(__file__).resolve().parents[2]` = **cloned-repos** (the directory containing ganjamon-agent), not repo root. The code does `parents[2] / "cloned-repos" / "8004-contracts"`, which would resolve to **cloned-repos/cloned-repos/8004-contracts** — wrong.
- **Correct current behavior** (if script is under `.../cloned-repos/ganjamon-agent/scripts/`): use `parents[2] / "8004-contracts"` (sibling of ganjamon-agent under cloned-repos).
- **After reorg:** File is `agents/ganjamon/scripts/register_erc8004_monad.py`. Repo root = **parents[3]** (scripts → ganjamon → agents → root). Use:
  - `abi_path = Path(__file__).resolve().parents[3] / "refs" / "8004-contracts" / "abis" / "IdentityRegistry.json"`
- **Checklist fix:** Section 4.3 must say **parents[3]** (not parents[2]) for the post-reorg script.

### 7.3 self_improvement.py — CLONED_REPOS_PATH → REFS_ROOT

- **Current:** `CLONED_REPOS_PATH = Path(__file__).parent.parent.parent.parent` from `ganjamon-agent/src/learning/` = **cloned-repos** (parent of ganjamon-agent).
- **After reorg:** Same expression from `agents/ganjamon/src/learning/` = **agents** (parent of ganjamon). Refs live under **refs/**, not under agents.
- **Correction:** From `agents/ganjamon/src/learning/self_improvement.py`, repo root = **parents[4]** (learning → src → ganjamon → agents → root). Set:
  - `REPO_ROOT = Path(__file__).resolve().parents[4]`
  - `CLONED_REPOS_PATH = REPO_ROOT / "refs"`  
  (or import `REFS_ROOT` from a shared paths module if the main app has one.)

### 7.4 pages-deploy and Cloudflare deploy

- If **pages-deploy** moves to **frontend/pages-deploy**, the deploy command must change to either:
  - From repo root: `npx wrangler pages deploy frontend/pages-deploy/ --project-name=grokandmon`, or
  - From **frontend/**: `npx wrangler pages deploy pages-deploy/ --project-name=grokandmon`
- If **workers** move to **frontend/cloudflare/**, then `npx wrangler deploy` must be run from **frontend/cloudflare/** (or each wrangler*.toml must reference the correct worker script path). Existing CI or local habits that run wrangler from repo root will break unless documented and updated.
- **Recommendation:** Either keep workers and wrangler configs at repo root (minimal change), or document the new deploy cwd and all path assumptions in CLAUDE.md and this plan.

### 7.5 Symlink variant on Windows

- Creating directory symlinks (e.g. `agents/ganjamon` → `cloned-repos/ganjamon-agent`) on Windows typically requires **Developer Mode** or running as Administrator. WSL/Linux does not have this restriction.
- **Add to plan:** If using the symlink approach, note that Windows users may need Developer Mode or to run reorg/sync from WSL.

### 7.6 Execution order: copy vs move

- If we **move** first and then update code, the directory is gone and the service breaks until every reference is updated.
- **Safer sequence:**  
  1. Create **agents/** and **refs/** (and optionally **projects/**, **frontend/**).  
  2. **Copy** (do not move) **ganjamon-agent** → **agents/ganjamon** and **farcaster-agent** → **agents/farcaster**.  
  3. Update all references (via paths.py and checklist) to **agents/ganjamon** and **agents/farcaster**.  
  4. Run tests and confirm `run.py all` and API/trading/social use **agents/ganjamon/data**.  
  5. **Then** delete **cloned-repos/ganjamon-agent** and **cloned-repos/farcaster-agent** (and later migrate the rest of cloned-repos into **refs/**).  
- This avoids a half-broken state where the process cwd or data paths point at a missing directory.

### 7.7 sync_from_ralph.sh and ralph_sync.sh

- **sync_from_ralph.sh** uses `REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` — no reference to sol-cannabis or cloned-repos. After moving the script to **agents/ganjamon/sync_from_ralph.sh**, it will still work; REPO_DIR will be **agents/ganjamon**. No change needed inside the script.  
- **ralph_sync.sh** and other .ralph scripts use hardcoded paths like `/home/natha/projects/sol-cannabis/cloned-repos/ganjamon-agent`. Those must be updated to the new path (or derived from script location) when the agent dir moves. The plan’s checklist item 4.3 already covers .ralph/*.sh.

### 7.8 Dashboard and frontend build

- The plan does not list **dashboard/** in the reference map. If any script or doc assumes “run from dashboard/” or “build output goes to pages-deploy”, moving **dashboard/** to **frontend/app/** (or **projects/dashboard**) requires updating those build/deploy steps. When implementing, confirm whether dashboard builds into pages-deploy and document the new paths in this plan or in CLAUDE.md.

### 7.9 Summary of checklist corrections

| Item | Correction |
|------|------------|
| **4.3 register_erc8004_monad.py** | Use **parents[3]** (repo root) then `"refs" / "8004-contracts"`. Fix current bug: from current layout use `parents[2] / "8004-contracts"` (no extra `"cloned-repos"`). |
| **4.3 self_improvement.py** | Use **parents[4]** for repo root, then `REPO_ROOT / "refs"`. |
| **Execution order** | Use **copy** then update refs then test then **delete** old dirs; introduce **paths.py** before batch updates. |
| **a2a / reputation_publisher** | Use **paths.py** (PROJECT_ROOT / TRADING_DATA) instead of raw relative paths. |
| **Deploy / symlinks** | Document wrangler cwd if frontend/cloudflare is used; note Windows symlink caveat. |
