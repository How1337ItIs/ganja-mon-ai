#!/bin/bash
# Rasta Mon Megaphone - Raspberry Pi Auto-Setup Script
# Run this ON the Pi after first boot:
#   curl -sSL https://raw.githubusercontent.com/.../setup_pi.sh | bash
# Or: scp this file to Pi and run: bash setup_pi.sh
set -e

echo "=========================================="
echo "  RASTA MON MEGAPHONE - Pi Setup"
echo "=========================================="

# 1. System updates
echo "[1/6] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Audio dependencies
echo "[2/6] Installing audio dependencies..."
sudo apt install -y \
    python3-pip python3-venv python3-dev \
    portaudio19-dev libasound2-dev libportaudio2 libportaudiocpp0 \
    ffmpeg alsa-utils \
    libopenblas-dev libatlas-base-dev \
    pulseaudio pulseaudio-module-bluetooth bluez  # BT audio

# 3. Python venv
echo "[3/6] Setting up Python virtual environment..."
cd /home/midaswhale/megaphone
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools

# 4. Install Python packages
echo "[4/6] Installing Python packages..."
# Install numpy with system BLAS for performance on Pi Zero
pip install numpy
pip install sounddevice websockets openai elevenlabs python-dotenv
# RPi.GPIO is usually system-installed, but just in case
# RPi.GPIO not needed - we use --no-gpio for BT audio setup

# 5. Audio configuration
echo "[5/6] Configuring audio..."
# Unblock and enable Bluetooth for audio output
sudo rfkill unblock bluetooth 2>/dev/null || true
sudo systemctl enable bluetooth
sudo systemctl restart bluetooth
sleep 2

# Start PulseAudio for the user (needed for BT audio sink)
pulseaudio --start 2>/dev/null || true

# 6. Install systemd service
echo "[6/6] Installing systemd service..."
sudo cp rasta-megaphone.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rasta-megaphone.service

echo ""
echo "=========================================="
echo "  SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Test audio devices:"
echo "  python3 megaphone.py --list-devices"
echo ""
echo "Test everything:"
echo "  source venv/bin/activate"
echo "  python3 megaphone.py --test"
echo ""
echo "Run live:"
echo "  python3 megaphone.py"
echo ""
echo "Auto-start on boot:"
echo "  sudo systemctl start rasta-megaphone"
echo "  sudo journalctl -u rasta-megaphone -f"
echo ""
