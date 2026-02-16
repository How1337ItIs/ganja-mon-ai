#!/bin/bash
# Deploy megaphone files to Raspberry Pi
# Usage: bash deploy.sh [pi-hostname-or-ip] [pi-user]
# Example: bash deploy.sh raspberrypi.local pi
#          bash deploy.sh 192.168.1.105 pi

PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PI_DIR="/home/${PI_USER}/megaphone"

echo "Deploying to ${PI_USER}@${PI_HOST}:${PI_DIR}"

# Create directory on Pi
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${PI_DIR}"

# Copy all files
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scp ${SCRIPT_DIR}/megaphone.py ${PI_USER}@${PI_HOST}:${PI_DIR}/
scp ${SCRIPT_DIR}/requirements.txt ${PI_USER}@${PI_HOST}:${PI_DIR}/
scp ${SCRIPT_DIR}/.env ${PI_USER}@${PI_HOST}:${PI_DIR}/
scp ${SCRIPT_DIR}/voice_config.json ${PI_USER}@${PI_HOST}:${PI_DIR}/
scp ${SCRIPT_DIR}/rasta-megaphone.service ${PI_USER}@${PI_HOST}:${PI_DIR}/
scp ${SCRIPT_DIR}/setup_pi.sh ${PI_USER}@${PI_HOST}:${PI_DIR}/

echo ""
echo "Files deployed! Now SSH in and run setup:"
echo "  ssh ${PI_USER}@${PI_HOST}"
echo "  cd ${PI_DIR}"
echo "  bash setup_pi.sh"
