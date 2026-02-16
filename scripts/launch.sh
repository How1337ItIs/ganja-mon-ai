#!/bin/bash
# Grok & Mon - Launch Script
# ==========================
# Starts all services for the Grok & Mon cannabis cultivation system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║         🌿 GROK & MON LAUNCHER 🌿         ║"
echo "  ║     AI-Autonomous Cannabis Cultivation    ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check for .env
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Copy .env.example to .env and configure your API keys"
    exit 1
fi

# Load environment
export $(grep -v '^#' .env | xargs)

# Check XAI_API_KEY
if [ -z "$XAI_API_KEY" ]; then
    echo -e "${RED}ERROR: XAI_API_KEY not set in .env${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} XAI_API_KEY configured"

# Check for venv
VENV_PATH=""
if [ -d "venv-wsl" ]; then
    VENV_PATH="venv-wsl"
elif [ -d "venv-linux" ]; then
    VENV_PATH="venv-linux"
elif [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    VENV_PATH="venv"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv-wsl
    VENV_PATH="venv-wsl"
    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt
fi

source "$VENV_PATH/bin/activate"
echo -e "${GREEN}[OK]${NC} Virtual environment: $VENV_PATH"

# Parse arguments
MODE="${1:-all}"
GROW_DAY="${2:-1}"

case "$MODE" in
    "agent")
        echo -e "\n${CYAN}Starting AI Agent (Decision Loop)...${NC}"
        echo "Grow Day: $GROW_DAY"
        echo ""
        python -m src.brain.agent --day "$GROW_DAY" --hardware
        ;;

    "agent-mock")
        echo -e "\n${CYAN}Starting AI Agent (Mock Mode)...${NC}"
        echo "Grow Day: $GROW_DAY"
        echo ""
        python -m src.brain.agent --day "$GROW_DAY"
        ;;

    "api")
        echo -e "\n${CYAN}Starting API Server...${NC}"
        echo "Visit: http://localhost:8000"
        echo ""
        python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
        ;;

    "api-prod")
        echo -e "\n${CYAN}Starting API Server (Production)...${NC}"
        echo ""
        python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4
        ;;

    "test-vision")
        echo -e "\n${CYAN}Testing Vision System...${NC}"
        python test_vision.py
        ;;

    "test-camera")
        echo -e "\n${CYAN}Testing Webcam...${NC}"
        python test_webcam.py
        ;;

    "all")
        echo -e "\n${CYAN}Starting Full System...${NC}"
        echo ""
        echo "This will start:"
        echo "  1. API Server (port 8000)"
        echo "  2. AI Agent (30 min cycles)"
        echo ""
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        echo ""

        # Start API in background
        python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &
        API_PID=$!
        echo -e "${GREEN}[OK]${NC} API started (PID: $API_PID)"

        sleep 2

        # Start Agent in foreground
        python -m src.brain.agent --day "$GROW_DAY" --hardware

        # Cleanup on exit
        kill $API_PID 2>/dev/null
        ;;

    *)
        echo "Usage: ./scripts/launch.sh [mode] [grow_day]"
        echo ""
        echo "Modes:"
        echo "  all         - Start API + Agent (default)"
        echo "  agent       - Start AI Agent with hardware"
        echo "  agent-mock  - Start AI Agent in mock mode"
        echo "  api         - Start API server (dev mode)"
        echo "  api-prod    - Start API server (production)"
        echo "  test-vision - Test Grok vision API"
        echo "  test-camera - Test USB webcam"
        echo ""
        echo "Examples:"
        echo "  ./scripts/launch.sh all 15       # Start with grow day 15"
        echo "  ./scripts/launch.sh agent-mock   # Test without hardware"
        ;;
esac
