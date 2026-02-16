#!/usr/bin/env bash
set -euo pipefail

# Chromebook remote admin helper for off-LAN operation via Cloudflare tunnels.
#
# Credential split (important):
# - main tunnel (grokandmon.com/api/*) uses ADMIN_JWT_PASSWORD
# - agent tunnel (agent.grokandmon.com/*) uses ADMIN_PASSWORD
#
# Usage examples:
#   scripts/chromebook_remote_admin.sh ping
#   scripts/chromebook_remote_admin.sh status
#   scripts/chromebook_remote_admin.sh exec "hostname && date -Is"
#   scripts/chromebook_remote_admin.sh restart grokmon

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env" >/dev/null 2>&1 || true
  set +a
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing dependency: $1" >&2
    exit 1
  }
}

require_cmd curl
require_cmd python3

MAIN_BASE="https://grokandmon.com"
AGENT_BASE="https://agent.grokandmon.com"

json_get() {
  local key="$1"
  python3 -c 'import json,sys
key=sys.argv[1]
obj=json.load(sys.stdin)
val=obj.get(key)
if val is None:
    raise SystemExit(2)
print(val)
' "$key"
}

auth_main() {
  : "${ADMIN_JWT_PASSWORD:?ADMIN_JWT_PASSWORD is required for main tunnel auth}"
  curl -fsS --retry 2 --retry-delay 1 --retry-all-errors --max-time 20 -X POST "$MAIN_BASE/api/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=$ADMIN_JWT_PASSWORD" \
    | json_get "access_token"
}

auth_agent() {
  : "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required for agent tunnel auth}"
  curl -fsS --retry 2 --retry-delay 1 --retry-all-errors --max-time 20 -X POST "$AGENT_BASE/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=$ADMIN_PASSWORD" \
    | json_get "access_token"
}

call() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local data="${4:-}"

  if [[ -n "$token" ]]; then
    if [[ "$method" == "GET" ]]; then
      curl -fsS --retry 2 --retry-delay 1 --retry-all-errors --max-time 30 -X GET "$url" -H "Authorization: Bearer $token"
    else
      curl -fsS --retry 2 --retry-delay 1 --retry-all-errors --max-time 30 -X "$method" "$url" -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d "$data"
    fi
  else
    curl -fsS --retry 2 --retry-delay 1 --retry-all-errors --max-time 30 -X "$method" "$url"
  fi
}

cmd="${1:-}"
if [[ -z "$cmd" ]]; then
  echo "usage: $0 {ping|status|exec|restart} [args...]" >&2
  exit 1
fi
shift || true

case "$cmd" in
  ping)
    echo "main tunnel ping:"
    call GET "$MAIN_BASE/api/admin/ping"
    echo
    echo "agent tunnel ping:"
    call GET "$AGENT_BASE/admin/ping"
    echo
    ;;

  status)
    main_token="$(auth_main)"
    agent_token="$(auth_agent)"
    echo "main services:"
    call GET "$MAIN_BASE/api/admin/services" "$main_token"
    echo
    echo "agent services:"
    call GET "$AGENT_BASE/admin/services" "$agent_token"
    echo
    ;;

  exec)
    if [[ $# -lt 1 ]]; then
      echo "usage: $0 exec \"<shell command>\"" >&2
      exit 1
    fi
    run_cmd="$*"
    agent_token="$(auth_agent)"
    payload="$(python3 - "$run_cmd" <<'PY'
import json, sys
print(json.dumps({"command": sys.argv[1], "timeout": 30}))
PY
)"
    call POST "$AGENT_BASE/admin/exec" "$agent_token" "$payload"
    echo
    ;;

  restart)
    service="${1:-}"
    if [[ -z "$service" ]]; then
      echo "usage: $0 restart {grokmon|cloudflared|ssh|ganja-mon-bot}" >&2
      exit 1
    fi
    agent_token="$(auth_agent)"
    call POST "$AGENT_BASE/admin/restart-service/$service" "$agent_token" "{}"
    echo
    ;;

  *)
    echo "unknown command: $cmd" >&2
    echo "valid: ping | status | exec | restart" >&2
    exit 1
    ;;
esac
