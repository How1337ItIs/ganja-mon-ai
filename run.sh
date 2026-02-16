#!/bin/bash
#
# Grok & Mon - Quick Start Script
# ================================
# Run this to start the AI grow agent
#
# Usage:
#   ./run.sh           # Mock mode (no hardware)
#   ./run.sh --hw      # Hardware mode (Govee, Kasa, Webcam)
#   ./run.sh --once    # Single decision cycle
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║       🌿 GROK & MON 🌿                ║"
echo "  ║   AI-Automated Cannabis Cultivation   ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo -e "${YELLOW}Warning: No venv found. Run: python3 -m venv venv && pip install -r requirements.txt${NC}"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Environment loaded from .env"
else
    echo -e "${YELLOW}Warning: No .env file found. Create one with your API keys.${NC}"
fi

# Check API key
if [ -z "$XAI_API_KEY" ]; then
    echo ""
    echo -e "${YELLOW}ERROR: XAI_API_KEY not set!${NC}"
    echo ""
    echo "Set your Grok API key:"
    echo "  export XAI_API_KEY='your-key-here'"
    echo ""
    echo "Or add to .env file"
    echo "Get your key at: https://console.x.ai"
    exit 1
fi

# Parse arguments
HARDWARE=""
EXTRA_ARGS=""

for arg in "$@"; do
    case $arg in
        --hw|--hardware)
            HARDWARE="--hardware"
            shift
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
    esac
done

# Build command
CMD="python -m src.brain.agent"

if [ -n "$HARDWARE" ]; then
    CMD="$CMD --hardware"
    echo "Mode: HARDWARE (real sensors & actuators)"

    # Add Kasa IPs if configured
    if [ -n "$KASA_LIGHT_IP" ]; then
        CMD="$CMD --kasa-light $KASA_LIGHT_IP"
    fi
    if [ -n "$KASA_FAN_IP" ]; then
        CMD="$CMD --kasa-fan $KASA_FAN_IP"
    fi
else
    echo "Mode: MOCK (simulated hardware)"
fi

# Add grow day from env if set
if [ -n "$GROW_DAY" ]; then
    CMD="$CMD --day $GROW_DAY"
fi

# Add any extra arguments
CMD="$CMD $EXTRA_ARGS"

echo ""
echo "Running: $CMD"
echo ""
echo "Press Ctrl+C to stop"
echo "─────────────────────────────────────────"
echo ""

# Run the agent
$CMD
