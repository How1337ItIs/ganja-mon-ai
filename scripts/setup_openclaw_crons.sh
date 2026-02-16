#!/usr/bin/env bash
# Deterministic OpenClaw cron reconciler for GanjaMon.
# - Writes the ACTIVE cron store under openclaw-workspace/cron/cron.json atomically
# - Avoids `openclaw cron add/rm` hangs that can leave a partial schedule
# - Rebuilds a canonical schedule with explicit models (no implicit fallback ambiguity)

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/natha/projects/sol-cannabis}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$PROJECT_ROOT/openclaw-workspace}"
CONFIG_PATH="${CONFIG_PATH:-$WORKSPACE_ROOT/config/openclaw.json}"
AGENT="${AGENT:-ganjamon}"
TZ="${TZ:-America/Los_Angeles}"

# NOTE: OpenClaw model registry has historically been stricter than the raw xAI API.
# Prefer Gemini by default; override via env when xAI credits/models are known-good.
FAST_MODEL="${FAST_MODEL:-google/gemini-3-flash-preview}"
SMART_MODEL="${SMART_MODEL:-google/gemini-3-flash-preview}"

cd "$PROJECT_ROOT"

echo "=== OpenClaw Cron Reconcile ==="
echo "Project:   $PROJECT_ROOT"
echo "Workspace: $WORKSPACE_ROOT"
echo "Config:    $CONFIG_PATH"
echo "Agent:     $AGENT"
echo "TZ:        $TZ"
echo "Fast:      $FAST_MODEL"
echo "Smart:     $SMART_MODEL"

if ! ss -ltn 2>/dev/null | grep -q ':18789'; then
  echo "[ERROR] OpenClaw gateway is not listening on :18789"
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "[ERROR] Missing OpenClaw config at $CONFIG_PATH"
  exit 1
fi

CRON_STORE="$(python3 - <<'PY'
import json
from pathlib import Path
cfg = Path('/home/natha/projects/sol-cannabis/openclaw-workspace/config/openclaw.json')
try:
    data = json.loads(cfg.read_text())
    rel = (data.get('cron') or {}).get('store') or 'cron/cron.json'
except Exception:
    rel = 'cron/cron.json'
print(str((Path('/home/natha/projects/sol-cannabis/openclaw-workspace') / rel).resolve()))
PY
)"

echo "Cron store: $CRON_STORE"

if [[ ! -f "$CRON_STORE" ]]; then
  echo "[WARN] Cron store missing; creating empty store at $CRON_STORE"
  mkdir -p "$(dirname "$CRON_STORE")"
  printf '{\n  "version": 1,\n  "jobs": []\n}\n' > "$CRON_STORE"
fi

echo "[*] Writing canonical cron store (atomic, no OpenClaw CLI)..."
FAST_MODEL="$FAST_MODEL" SMART_MODEL="$SMART_MODEL" \
PROJECT_ROOT="$PROJECT_ROOT" WORKSPACE_ROOT="$WORKSPACE_ROOT" CONFIG_PATH="$CONFIG_PATH" \
python3 scripts/reconcile_openclaw_cron_store.py >/dev/null

# ---------------------------------------------------------------------------
# Verify store state
# ---------------------------------------------------------------------------

echo "[=] Verifying cron store..."
python3 - "$CRON_STORE" <<'PY'
import json, sys
from collections import Counter

store = sys.argv[1]
obj = json.load(open(store))
jobs = obj.get('jobs', [])
required = [
  'Grow Decision Cycle',
  'Cross-Platform Social',
  'Reputation Publishing',
  'Auto-Review',
  'Research and Intelligence',
  'Daily Comprehensive Update',
  'Daily NFT Creation',
  'Skill Library Check',
  'Self-Improvement Reflection',
  'Weekly Deep Analysis',
]

names = [j.get('name') for j in jobs]
counts = Counter(names)
missing = [n for n in required if counts.get(n, 0) == 0]
duplicates = [n for n,c in counts.items() if c > 1]

print(f'jobs_total={len(jobs)}')
for n in required:
  print(f'  {n}: {counts.get(n,0)}')

if missing:
  print('MISSING:', ', '.join(missing))
if duplicates:
  print('DUPLICATES:', ', '.join(duplicates))

if missing or duplicates:
  raise SystemExit(1)
PY

echo "[OK] Cron reconciliation complete."
