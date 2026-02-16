# Functional Fixes (2026-02-06)

This documents the changes made after the functional audit request. The goal was
to restore AI decision execution, make sensor data flow consistent to the UI,
and avoid crashes when sensors are unavailable.

## Summary of Changes

1. AI decision loop signature + prompt context
   - Files: `src/ai/brain.py`, `src/ai/prompts.py`
   - Added `sensor_context` to `GrokBrain.decide()` and the decision prompt.
   - Reason: Orchestrator was calling `decide(..., sensor_context=...)` and
     crashing due to a signature mismatch. This restores AI execution and
     exposes sensor reliability info in prompts.
   - Also hardened tool call parsing to accept dict arguments or invalid JSON.

2. Orchestrator safety and data logging behavior
   - File: `src/orchestrator.py`
   - Linked mock actuators only to mock sensors (avoids calling mock-only methods
     on real sensors).
   - Skips DB writes when any core sensor fields are missing (prevents inserting
     NULLs into non-null DB columns and avoids downstream crashes).
   - Added `_sync_dark_period_config()` to enable dark-period protection during
     flowering (or 12/12) and called it when stage data is loaded and before AI
     decisions. This keeps light safety consistent with stage.

3. Stage-aware daily water limits in safety status
   - File: `src/safety/guardian.py`
   - `get_status()` now reports the stage-specific daily water limit instead of
     the fallback default.

4. Consistent grow day reporting
   - File: `src/db/repository.py`
   - `get_current_stage()` and hourly aggregates now use
     `effective_day = max(stored_day, calculated_day)` to avoid drift between
     manual day increments and date-based calculation.

5. VPD endpoints use correct sensor fields
   - File: `src/api/app.py`
   - `/api/vpd/current` and `/api/grow/check` now compute VPD from
     `air_temp` + `humidity` (and convert to Fahrenheit as needed).

6. WebSocket payload compatibility for the UI
   - Files: `src/api/app.py`, `src/web/index.html`
   - WebSocket messages now include both legacy and UI-expected fields
     (`air_temp`/`humidity` + `temperature_f`/`humidity_percent`/`vpd_kpa`).
   - Frontend mapping now accepts either schema, improving live updates.

7. Camera health check robustness
   - File: `src/api/app.py`
   - Health check now detects mock camera by class name to avoid module alias
     mismatches between `src.hardware` and `hardware` imports.

## Notes

- DB schema was not changed. The orchestrator now avoids logging when core sensor
  values are missing to respect non-null columns in `src/db/models.py`.
- These changes do not alter external API routes or response shapes (only add
  compatibility fields in WebSocket payloads).

## Local Validation

- `python3 -m py_compile src/orchestrator.py src/ai/brain.py src/ai/prompts.py src/safety/guardian.py src/db/repository.py src/api/app.py`

## Local Environment Artifacts

- A WSL virtual environment was created at `.venv/` for local smoke testing.
- A Windows virtual environment was created at `.venv-win/` for Windows-run API checks.
  Remove them if you do not want local envs in this directory.
