# Grok & Mon Functionality Audit (Read-Only)

Date: 2026-02-09  
Repo: `/mnt/c/Users/natha/sol-cannabis`

Scope: Runtime functionality of the unified system (`python run.py all`) including FastAPI, orchestrator, social subsystem(s), and trading agent subprocess integration. This report intentionally deprioritizes security except where it breaks functionality (auth gates, process isolation, etc.).

No code changes were made for this audit.

## Sources Of Truth Consulted

- `CLAUDE.md`
- `docs/SYSTEM_ATLAS.md`
- `.claude/rules/*.md`

## What I Looked At (Code Paths)

- Entrypoint + process model: `run.py`
- Grow loop: `src/orchestrator.py`, `src/orchestrator_resilient.py`
- API: `src/api/app.py` (+ routers)
- Health infra: `src/core/health.py`, `src/core/watchdog.py`, `src/core/circuit_breaker.py`
- Social: `src/social/engagement_daemon.py`, `src/social/engagement.py`, `src/social/__init__.py`
- Trading agent integration + plant sync client:
  - `cloned-repos/ganjamon-agent/src/main.py`
  - `cloned-repos/ganjamon-agent/src/clients/grokmon.py`
- Hardware hub keying: `src/hardware/base.py`, `src/hardware/kasa.py`

## Smoke Test Result

The repo’s built-in smoke test passes after dependencies are present:

Command:

```bash
.venv/bin/python run.py test
```

Result: **4/4 passed** (DB init, mock sensors, cultivation/VPD import, GrokBrain import). (`run.py`)

Note: In this environment `python` is not on PATH, so `python run.py ...` fails; `python3` or `.venv/bin/python` works.

## Findings (Ordered By Impact)

### 1) Social Subsystem Is Started Twice, And AI→Social Handoff Is Not Cross-Process

**What happens**

- `run.py all` starts a **social daemon** in its own process. (`run.py`: `run_all()` around lines reported by `rg` near 100; social target is `run_social()`).
- Separately, the **orchestrator** starts an **EngagementEngine** as an async task via `_start_unified_subsystems()`. (`src/orchestrator.py:399`, `src/orchestrator.py:512`, `src/orchestrator.py:541`)
- After every AI decision, the orchestrator queues decisions into `get_engagement_daemon().queue_decision(...)`. (`src/orchestrator.py` near the `queue_decision` call; `src/social/engagement_daemon.py:346`)

**Why this is a functional problem**

- If social is running in a different OS process than orchestrator, `queue_decision` is only an in-memory list inside that other process instance. There is no IPC mechanism (DB/file/queue) for decision payloads.
- Because orchestrator also starts a social engine inside its own process, you can end up with **two independent posting loops** with unclear ownership (double posts, race conditions, non-deterministic rate limiting, etc.).

**Expected outcome for a robust “unified agent”**

- Exactly one social runner should be authoritative.
- If social is a separate process, the AI decision handoff should be via a shared medium (SQLite table, JSONL append, Redis/MQTT topic, etc.), not an in-memory queue.

### 2) Health/Readiness Do Not Represent The 4-Process System

**What exists**

- Core “health router” provides:
  - `GET /health` (liveness + watchdog + circuit breaker snapshot)
  - `GET /ready` (readiness based on watchdog staleness)
  (`src/core/health.py`, included in API via `src/api/app.py:371`)
- API also defines `GET /api/health` with a different shape. (`src/api/app.py:1064`)

**Why this is a functional problem**

- `Watchdog` and circuit breakers are **in-process singletons**. (`src/core/watchdog.py`, `src/core/circuit_breaker.py`)
- The API server process cannot observe orchestrator/social/trading process status via those singletons.
- `/ready` can return `ready: true` even when nothing is running/registered (because “no components registered” is treated as “no stale components”).

**Net effect**

- Operators may see “healthy/ready” while a subprocess is dead, stuck, or repeatedly restarting.

### 3) Kasa Device Mapping Drift: API Uses `plug_1`..`plug_4`, Hardware Layer Expects Semantic Names

**What happens**

- API lifespan builds `kasa_ips` using env vars `KASA_PLUG_1_IP`..`KASA_PLUG_4_IP` and names them `plug_1`..`plug_4`. (`src/api/app.py:120`)
- Orchestrator uses semantic names (`co2_solenoid`, `water_pump`, `exhaust_fan`, `circulation_fan`, `grow_light`) sourced from `KASA_CO2_SOLENOID_IP`, etc. (`src/orchestrator.py:193`..`src/orchestrator.py:197`)
- `KasaActuatorHub.get_state()` only maps device names onto fields that exist on `DeviceState`. (`src/hardware/kasa.py`, `src/hardware/base.py` `DeviceState` fields)

**Why this is a functional problem**

- `DeviceState` does **not** have `plug_1`..`plug_4` fields. (`src/hardware/base.py`)
- So `KasaActuatorHub.get_state()` cannot populate `grow_light`, `exhaust_fan`, etc. when API uses `plug_1` naming.

**Practical impact**

- `/api/devices/latest` falls back to `app.state.actuators.get_state()` when DB has no rows; that fallback will return default/false fields even though plugs may be connected.
- Any future API endpoints that try to manipulate semantic devices will not line up with `plug_1` naming unless there is a mapping layer.

**Important nuance**

- Your `.env` currently defines BOTH naming schemes (`KASA_PLUG_*_IP` and `KASA_*_IP`). (`.env`, `.env.example`)
- That suggests a migration in progress, but the code currently behaves like two separate conventions.

### 4) Trading Agent Subprocess Environment Likely Ignores Its Own Venv

**What happens**

- `run.py` starts trading agent via `sys.executable -m main` with `PYTHONPATH` set to `cloned-repos/ganjamon-agent/src`. (`run.py:80`)
- `cloned-repos/ganjamon-agent/` contains its own `venv/` (observed on disk), but `run.py` does not use it.

**Why this is a functional problem**

- If the unified `.venv` lacks ganjamon-agent’s dependency set, the trading subprocess will crash even though its own `venv/` is present.
- This is easy to miss because `run.py` prints “Trading agent started” immediately after spawning.

### 5) Schedule Control Endpoints Are Not Wired Into The Live Orchestrator

**What exists**

- `/api/schedule/status` explicitly returns a mock placeholder. (`src/api/app.py`)
- `/api/schedule/set` returns “scheduled” but does not propagate to the orchestrator’s running `PhotoperiodScheduler` instance. (`src/api/app.py`)

**Why this matters**

- The trading agent’s `GrokMonClient` includes methods like `set_schedule()` and `advance_day()`, but schedule changes are not applied to the live system, so “control” APIs are not actually controlling anything end-to-end.

## “Works As Intended” Notes (Functionality Strengths)

- Orchestrator has explicit timeouts and reconnection attempts for sensors/DB operations and includes stall detection. (`src/orchestrator.py`)
- Camera contention is explicitly handled:
  - API uses a threaded `ContinuousWebcam` and retries at startup to let orchestrator release the device.
  - AI tool `take_photo` tries the API endpoint first (works if another component holds the camera).
  (`src/api/app.py`, `src/ai/tools.py`)
- Trading agent plant sync is clearly defined:
  - `GROKMON_BASE_URL` default `http://localhost:8000` (`cloned-repos/ganjamon-agent/src/main.py:381`)
  - Snapshot fetch uses `/api/grow/stage`, `/api/ai/latest`, `/api/sensors/latest`, `/api/plant-progress` (`cloned-repos/ganjamon-agent/src/clients/grokmon.py`)

## Recommendations (Functional, Not Security)

1. Pick one social topology and enforce it:
   - Option A: social is its own process, and orchestrator hands off decisions via a shared store (SQLite table or JSONL file) that the social process reads.
   - Option B: social runs only in-process with orchestrator; `run.py all` should not also spawn a second social daemon.

2. Make health reflect the multi-process system:
   - Prefer an API-visible shared heartbeat store (e.g., SQLite table updated by each process) over in-process singletons.

3. Unify Kasa naming:
   - Standardize on semantic names (`grow_light`, `exhaust_fan`, `water_pump`, `co2_solenoid`, etc.) end-to-end.
   - If `KASA_PLUG_1_IP` must remain, add a mapping layer rather than using `plug_1` as a device name.

4. Decide how the trading agent should be executed:
   - Either require its deps in the unified `.venv`, or explicitly execute using `cloned-repos/ganjamon-agent/venv/bin/python`.

5. Either wire `/api/schedule/set` into the live orchestrator or label it as “configuration-only” and remove control affordances from dependent clients until it is real.

