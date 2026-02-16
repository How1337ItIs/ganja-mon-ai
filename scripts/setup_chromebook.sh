#!/bin/bash
#
# Grok & Mon - Chromebook Setup Script
# =====================================
# Sets up the AI-automated cannabis grow system on Chromebook Linux (Crostini)
#
# Run this script after:
# 1. Enabling Linux: Settings > Advanced > Developers > Linux development environment
# 2. Opening Terminal
#
# Usage:
#   chmod +x scripts/setup_chromebook.sh
#   ./scripts/setup_chromebook.sh
#

set -e  # Exit on error

echo "=========================================="
echo "  Grok & Mon - Chromebook Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Chromebook Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Detected OS: $NAME $VERSION"
else
    echo -e "${YELLOW}Warning: Could not detect OS${NC}"
fi

# Step 1: Update system
echo ""
echo -e "${GREEN}[1/6] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python and dependencies
echo ""
echo -e "${GREEN}[2/6] Installing Python and development tools...${NC}"
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    build-essential \
    libffi-dev \
    libssl-dev

# Step 3: Install OpenCV dependencies (for webcam)
echo ""
echo -e "${GREEN}[3/6] Installing webcam/OpenCV dependencies...${NC}"
sudo apt install -y \
    libopencv-dev \
    python3-opencv \
    v4l-utils \
    ffmpeg

# Step 4: Create virtual environment
echo ""
echo -e "${GREEN}[4/6] Setting up Python virtual environment...${NC}"

cd "$(dirname "$0")/.."  # Go to project root

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created virtual environment"
else
    echo "Virtual environment already exists"
fi

source venv/bin/activate

# Step 5: Install Python packages
echo ""
echo -e "${GREEN}[5/6] Installing Python packages...${NC}"

# Upgrade pip first
pip install --upgrade pip

# Install core requirements (minimal for weekend launch)
pip install \
    httpx \
    python-kasa \
    opencv-python-headless \
    Pillow \
    rich \
    python-dotenv

# Optional: Full requirements if available
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt || echo -e "${YELLOW}Some packages failed - continuing with essentials${NC}"
fi

# Step 6: Create configuration
echo ""
echo -e "${GREEN}[6/6] Setting up configuration...${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Grok & Mon Configuration
# ========================

# xAI Grok API Key (required)
# Get your key at: https://console.x.ai
XAI_API_KEY=your-key-here

# Govee API Key (for WiFi temperature sensor)
# Get your key at: https://developer.govee.com/
GOVEE_API_KEY=your-govee-key-here

# Kasa Smart Plug IPs (set after pairing with Kasa app)
# Discover with: python -m src.hardware.kasa
KASA_LIGHT_IP=192.168.1.100
KASA_FAN_IP=192.168.1.101

# Grow Configuration
GROW_DAY=1
GROWTH_STAGE=SEEDLING
EOF
    echo "Created .env file - EDIT THIS with your API keys!"
else
    echo ".env file already exists"
fi

# Create data directories
mkdir -p data/timelapse
mkdir -p data/logs

# Test installations
echo ""
echo "=========================================="
echo "  Testing Installation"
echo "=========================================="

# Test Python
echo -n "Python: "
python3 --version

# Test key imports
echo -n "Kasa library: "
python3 -c "from kasa import SmartPlug; print('OK')" 2>/dev/null || echo "FAILED"

echo -n "OpenCV: "
python3 -c "import cv2; print('OK')" 2>/dev/null || echo "FAILED"

echo -n "httpx: "
python3 -c "import httpx; print('OK')" 2>/dev/null || echo "FAILED"

# Check for webcam
echo ""
echo "Checking for webcam..."
if [ -e /dev/video0 ]; then
    echo -e "${GREEN}Webcam found at /dev/video0${NC}"
    v4l2-ctl --list-devices 2>/dev/null || true
else
    echo -e "${YELLOW}No webcam detected at /dev/video0${NC}"
    echo "To enable USB webcam on Chromebook:"
    echo "  1. Connect webcam to USB port"
    echo "  2. Settings > Advanced > Developers > Linux"
    echo "  3. Click 'Manage USB devices'"
    echo "  4. Enable your webcam"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Test Kasa discovery: python -m src.hardware.kasa"
echo "  3. Test Govee sensor: python -m src.hardware.govee"
echo "  4. Test webcam: python -m src.hardware.webcam"
echo "  5. Run agent: python -m src.brain.agent --once"
echo ""
echo "Quick start:"
echo "  source venv/bin/activate"
echo "  export \$(cat .env | xargs)"
echo "  python -m src.brain.agent --once"
echo ""
