#!/bin/bash
# First boot auto-setup for Rasta Megaphone Pi
# Place this on the boot partition as /boot/firmware/firstboot.sh
# Pi OS will execute it on first boot and then delete it
set -e

LOG="/var/log/megaphone-setup.log"
exec > >(tee -a "$LOG") 2>&1

echo "$(date): Starting Rasta Megaphone first-boot setup..."

# Wait for network
echo "Waiting for network..."
for i in $(seq 1 30); do
    if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
        echo "Network ready!"
        break
    fi
    sleep 2
done

# Install system dependencies
echo "Installing system packages..."
apt-get update
apt-get install -y \
    python3-pip python3-venv python3-dev \
    portaudio19-dev libasound2-dev libportaudio2 libportaudiocpp0 \
    ffmpeg alsa-utils \
    python3-rpi.gpio \
    libopenblas-dev libatlas-base-dev

# Create megaphone directory
MEGAPHONE_DIR="/home/pi/megaphone"
mkdir -p "$MEGAPHONE_DIR"

# Copy files from boot partition if they exist
BOOT_DIR="/boot/firmware"
for f in megaphone.py requirements.txt .env voice_config.json rasta-megaphone.service; do
    if [ -f "${BOOT_DIR}/${f}" ]; then
        cp "${BOOT_DIR}/${f}" "${MEGAPHONE_DIR}/"
        echo "Copied $f"
    fi
done

chown -R pi:pi "$MEGAPHONE_DIR"

# Setup Python venv
echo "Setting up Python virtual environment..."
su - pi -c "cd ${MEGAPHONE_DIR} && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip wheel && pip install numpy scipy sounddevice websockets openai elevenlabs python-dotenv RPi.GPIO 2>/dev/null || pip install numpy scipy sounddevice websockets openai elevenlabs python-dotenv"

# Set audio to 3.5mm jack
amixer cset numid=3 1 2>/dev/null || true
amixer set Master 100% 2>/dev/null || true

# Install and enable service
if [ -f "${MEGAPHONE_DIR}/rasta-megaphone.service" ]; then
    cp "${MEGAPHONE_DIR}/rasta-megaphone.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable rasta-megaphone.service
    systemctl start rasta-megaphone.service
    echo "Megaphone service installed and started!"
fi

echo "$(date): First-boot setup complete!"
