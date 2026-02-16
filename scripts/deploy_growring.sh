#!/bin/bash
# ===========================================
# GrowRing NFT System — Deployment Script
# ===========================================
#
# Deploys the GrowRing Python modules and Solidity contracts
# to the Chromebook server, installs dependencies, and
# optionally compiles and deploys contracts to Monad.
#
# Usage:
#   ./scripts/deploy_growring.sh              # Deploy files only
#   ./scripts/deploy_growring.sh --compile    # Deploy + compile Solidity
#   ./scripts/deploy_growring.sh --deploy     # Deploy + compile + deploy to Monad
#   ./scripts/deploy_growring.sh --test       # Deploy + run tests on Chromebook

set -e

CHROMEBOOK_HOST="natha@chromebook.lan"
CHROMEBOOK_PATH="/home/natha/projects/sol-cannabis"
LOCAL_PATH="$(cd "$(dirname "$0")/.." && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   GrowRing NFT System Deploy       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
echo ""

# Check SSH connectivity
echo -e "${YELLOW}→ Testing Chromebook connection...${NC}"
if ! powershell.exe -Command "ssh -o ConnectTimeout=5 $CHROMEBOOK_HOST 'echo OK'" 2>/dev/null | grep -q OK; then
    echo -e "${RED}✗ Chromebook not reachable via SSH${NC}"
    echo "  Try: curl https://grokandmon.com/api/admin/ping"
    exit 1
fi
echo -e "${GREEN}✓ Connected${NC}"

# ─── Deploy Python Files ──────────────────────────────────────────
echo -e "${YELLOW}→ Deploying Python modules...${NC}"

# Create directories
powershell.exe -Command "ssh $CHROMEBOOK_HOST 'mkdir -p $CHROMEBOOK_PATH/src/onchain $CHROMEBOOK_PATH/contracts/grow/src $CHROMEBOOK_PATH/contracts/grow/script $CHROMEBOOK_PATH/tests'"

# Transfer src/onchain/ files
ONCHAIN_FILES=(
    "src/onchain/__init__.py"
    "src/onchain/art.py"
    "src/onchain/ipfs.py"
    "src/onchain/growring.py"
    "src/onchain/marketplace.py"
    "src/onchain/promote.py"
    "src/onchain/daily_mint.py"
)

for f in "${ONCHAIN_FILES[@]}"; do
    local_file="$LOCAL_PATH/$f"
    remote_file="$CHROMEBOOK_PATH/$f"
    if [ -f "$local_file" ]; then
        powershell.exe -Command "Get-Content '$local_file' -Raw | ssh $CHROMEBOOK_HOST 'cat > $remote_file'"
        echo "  ✓ $f"
    else
        echo "  ✗ $f (not found locally)"
    fi
done

# Transfer config
powershell.exe -Command "Get-Content '$LOCAL_PATH/src/core/config.py' -Raw | ssh $CHROMEBOOK_HOST 'cat > $CHROMEBOOK_PATH/src/core/config.py'"
echo "  ✓ src/core/config.py"

# Transfer test
powershell.exe -Command "Get-Content '$LOCAL_PATH/tests/test_growring_smoke.py' -Raw | ssh $CHROMEBOOK_HOST 'cat > $CHROMEBOOK_PATH/tests/test_growring_smoke.py'"
echo "  ✓ tests/test_growring_smoke.py"

# Transfer contracts
CONTRACT_FILES=(
    "contracts/grow/src/GrowOracle.sol"
    "contracts/grow/src/GrowRing.sol"
    "contracts/grow/src/GrowAuction.sol"
    "contracts/grow/script/Deploy.s.sol"
)

for f in "${CONTRACT_FILES[@]}"; do
    local_file="$LOCAL_PATH/$f"
    remote_file="$CHROMEBOOK_PATH/$f"
    if [ -f "$local_file" ]; then
        powershell.exe -Command "Get-Content '$local_file' -Raw | ssh $CHROMEBOOK_HOST 'cat > $remote_file'"
        echo "  ✓ $f"
    else
        echo "  ✗ $f (not found locally)"
    fi
done

echo -e "${GREEN}✓ Files deployed${NC}"

# ─── Install Dependencies ─────────────────────────────────────────
echo -e "${YELLOW}→ Checking Python deps...${NC}"
powershell.exe -Command "ssh $CHROMEBOOK_HOST 'cd $CHROMEBOOK_PATH && source venv/bin/activate && pip install -q pydantic-settings httpx web3 2>&1 | tail -3'"
echo -e "${GREEN}✓ Dependencies OK${NC}"

# ─── Handle Arguments ─────────────────────────────────────────────
case "$1" in
    --test)
        echo -e "${YELLOW}→ Running tests on Chromebook...${NC}"
        powershell.exe -Command "ssh $CHROMEBOOK_HOST 'cd $CHROMEBOOK_PATH && source venv/bin/activate && python tests/test_growring_smoke.py'"
        ;;

    --compile)
        echo -e "${YELLOW}→ Compiling Solidity contracts...${NC}"
        powershell.exe -Command "ssh $CHROMEBOOK_HOST 'export PATH=/home/natha/.foundry/bin:\$PATH && cd $CHROMEBOOK_PATH/contracts/grow && forge build 2>&1'"
        ;;

    --deploy)
        echo -e "${YELLOW}→ Compiling and deploying to Monad...${NC}"
        echo -e "${RED}⚠ This will spend real gas! Ctrl+C to cancel.${NC}"
        sleep 3
        powershell.exe -Command "ssh $CHROMEBOOK_HOST 'export PATH=/home/natha/.foundry/bin:\$PATH && cd $CHROMEBOOK_PATH/contracts/grow && source ../../.env && forge build && forge script script/Deploy.s.sol --rpc-url \$MONAD_RPC --broadcast --private-key \$MONAD_PRIVATE_KEY 2>&1'"
        ;;

    *)
        echo ""
        echo -e "${YELLOW}ℹ Use flags for more:${NC}"
        echo "  --test      Run tests on Chromebook"
        echo "  --compile   Compile Solidity contracts"
        echo "  --deploy    Deploy contracts to Monad (costs gas)"
        ;;
esac

echo ""
echo -e "${GREEN}╔════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   GrowRing Deploy Complete! 🌿    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════╝${NC}"
