#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# activate_claude_max.sh — Wire Claude Max subscription into OpenClaw
# ──────────────────────────────────────────────────────────────────────
# Run this ONLY when you're ready to use Claude Max credits.
# It generates a setup-token via the Claude Code CLI on this machine
# and deploys it to the Chromebook OpenClaw gateway.
#
# Usage:
#   bash scripts/activate_claude_max.sh              # Add as fallback (default)
#   bash scripts/activate_claude_max.sh --primary    # Promote to primary model
#   bash scripts/activate_claude_max.sh --token TOKEN # Skip generation, paste existing token
#   bash scripts/activate_claude_max.sh --status      # Check current auth status
#   bash scripts/activate_claude_max.sh --deactivate  # Remove Claude from fallback chain
#
# Prerequisites:
#   - Claude Code CLI installed and authenticated (claude --version)
#   - SSH access to chromebook.lan
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

CHROMEBOOK="natha@chromebook.lan"
PROJECT_DIR="/home/natha/projects/sol-cannabis"
CONFIG_SRC="openclaw-workspace/config/openclaw.json"
CONFIG_DEST="$PROJECT_DIR/openclaw-workspace/config/openclaw.json"
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; }
info() { echo -e "${CYAN}[i]${NC} $*"; }

# ── Parse args ──────────────────────────────────────────────────────
MODE="fallback"  # default: add as fallback, don't make primary
TOKEN=""
ACTION="activate"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --primary)    MODE="primary"; shift ;;
    --token)      TOKEN="$2"; shift 2 ;;
    --status)     ACTION="status"; shift ;;
    --deactivate) ACTION="deactivate"; shift ;;
    -h|--help)
      echo "Usage: bash scripts/activate_claude_max.sh [--primary] [--token TOKEN] [--status] [--deactivate]"
      exit 0
      ;;
    *) err "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── Status check ────────────────────────────────────────────────────
if [[ "$ACTION" == "status" ]]; then
  info "Checking Claude auth status on Chromebook..."
  powershell.exe -Command "ssh $CHROMEBOOK 'cd $PROJECT_DIR && export PATH=\$PATH:/home/natha/.npm-global/bin && openclaw models status 2>&1 | grep -i -A5 anthropic || echo No Anthropic auth found'"
  exit 0
fi

# ── Deactivate ──────────────────────────────────────────────────────
if [[ "$ACTION" == "deactivate" ]]; then
  warn "Deactivating Claude from OpenClaw fallback chain..."
  info "This removes anthropic/claude-sonnet-4-5 from the fallbacks list in config."
  info "(The auth credentials remain on the Chromebook — only the model config changes.)"
  
  # Use python to remove from fallbacks in local config
  python3 -c "
import json, sys
with open('$CONFIG_SRC', 'r') as f:
    cfg = json.load(f)
fallbacks = cfg.get('agents', {}).get('defaults', {}).get('model', {}).get('fallbacks', [])
fallbacks = [m for m in fallbacks if 'anthropic' not in m]
cfg['agents']['defaults']['model']['fallbacks'] = fallbacks
# If primary is anthropic, swap back to grok
if 'anthropic' in cfg['agents']['defaults']['model'].get('primary', ''):
    cfg['agents']['defaults']['model']['primary'] = 'xai/grok-4'
with open('$CONFIG_SRC', 'w') as f:
    json.dump(cfg, f, indent=2)
print('Config updated.')
"
  
  # Deploy to Chromebook
  powershell.exe -Command "Get-Content '$CONFIG_SRC' -Raw | ssh $CHROMEBOOK 'cat > ~/.openclaw/openclaw.json'"
  log "Claude deactivated. Gateway will pick up new config on next heartbeat/restart."
  exit 0
fi

# ── Activate ────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Claude Max → OpenClaw Activation                       ║${NC}"
echo -e "${CYAN}║  Mode: $(printf '%-49s' "$MODE")║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Get or generate the setup token
if [[ -z "$TOKEN" ]]; then
  info "Generating setup-token from Claude Code CLI..."
  info "This will invoke 'claude setup-token' — it does NOT consume API quota."
  echo ""
  
  # Check Claude CLI is available
  if ! command -v claude &>/dev/null; then
    # Try WSL
    if command -v wsl &>/dev/null && wsl which claude &>/dev/null 2>&1; then
      TOKEN=$(wsl claude setup-token 2>/dev/null | tail -1)
    else
      err "Claude Code CLI not found. Install it or pass --token TOKEN manually."
      exit 1
    fi
  else
    TOKEN=$(claude setup-token 2>/dev/null | tail -1)
  fi
  
  if [[ -z "$TOKEN" ]]; then
    err "Failed to generate setup-token. Run 'claude setup-token' manually and use --token."
    exit 1
  fi
  
  log "Setup token generated (${#TOKEN} chars)"
else
  log "Using provided token (${#TOKEN} chars)"
fi

# Step 2: Deploy token to Chromebook
info "Deploying setup-token to Chromebook OpenClaw..."
powershell.exe -Command "ssh $CHROMEBOOK 'cd $PROJECT_DIR && export PATH=\$PATH:/home/natha/.npm-global/bin && echo \"$TOKEN\" | openclaw models auth paste-token --provider anthropic 2>&1'"

if [[ $? -ne 0 ]]; then
  err "Failed to paste token on Chromebook. Try manually:"
  echo "  ssh natha@chromebook.lan"
  echo "  openclaw models auth paste-token --provider anthropic"
  exit 1
fi

log "Token deployed to Chromebook"

# Step 3: Update config if promoting to primary
if [[ "$MODE" == "primary" ]]; then
  info "Promoting Claude to primary model..."
  
  python3 -c "
import json
with open('$CONFIG_SRC', 'r') as f:
    cfg = json.load(f)

model = cfg['agents']['defaults']['model']
old_primary = model['primary']

# Move old primary to fallbacks (if not already there)
if old_primary not in model.get('fallbacks', []):
    model.setdefault('fallbacks', []).insert(0, old_primary)

# Set Claude as primary
model['primary'] = 'anthropic/claude-sonnet-4-5'

# Remove Claude from fallbacks (it's now primary)
model['fallbacks'] = [m for m in model['fallbacks'] if 'anthropic' not in m.lower() or 'claude' not in m.lower()]

# Also update heartbeat model
cfg['agents']['defaults']['heartbeat']['model'] = 'anthropic/claude-sonnet-4-5'

with open('$CONFIG_SRC', 'w') as f:
    json.dump(cfg, f, indent=2)
print(f'Primary: anthropic/claude-sonnet-4-5 (was {old_primary})')
print(f'Fallbacks: {model[\"fallbacks\"]}')
"
  
  # Deploy updated config
  powershell.exe -Command "Get-Content '$CONFIG_SRC' -Raw | ssh $CHROMEBOOK 'cat > ~/.openclaw/openclaw.json'"
  log "Config deployed with Claude as primary"
else
  info "Claude stays as fallback — no config change needed (already in fallbacks list)."
  info "To promote later: bash scripts/activate_claude_max.sh --primary"
fi

# Step 4: Verify
echo ""
info "Verifying auth on Chromebook..."
powershell.exe -Command "ssh $CHROMEBOOK 'cd $PROJECT_DIR && export PATH=\$PATH:/home/natha/.npm-global/bin && openclaw models status --check 2>&1; echo Exit: \$?'"

echo ""
log "Done! Claude Max is configured as $MODE."
echo ""
info "Quick reference:"
echo "  Check status:    bash scripts/activate_claude_max.sh --status"
echo "  Promote primary: bash scripts/activate_claude_max.sh --primary"
echo "  Deactivate:      bash scripts/activate_claude_max.sh --deactivate"
echo ""
warn "Remember: Claude subscription tokens can expire."
warn "If you get 401s, re-run this script to refresh the token."
