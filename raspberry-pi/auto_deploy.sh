#!/bin/bash
# Auto-deploy megaphone to Raspberry Pi Zero 2 W
# Finds Pi on network, deploys files, runs setup, starts service
# Usage: bash auto_deploy.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PI_USER="midaswhale"
PI_PASS='newpass1337**'
PI_DIR="/home/midaswhale/megaphone"

SSH_CMD="sshpass -p '${PI_PASS}' ssh -o StrictHostKeyChecking=no"
SCP_CMD="sshpass -p '${PI_PASS}' scp -o StrictHostKeyChecking=no"

echo "=========================================="
echo "  RASTA MEGAPHONE AUTO-DEPLOY"
echo "=========================================="

# Step 1: Find Pi on network
echo ""
echo "[1/5] Scanning for Raspberry Pi on network..."

PI_IP=""

# Try mDNS first
for host in rasta-megaphone.local raspberrypi.local; do
    if ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
        PI_IP=$(ping -c 1 -W 2 "$host" 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+\.\d+')
        if [ -n "$PI_IP" ]; then
            echo "  Found via mDNS: $host -> $PI_IP"
            break
        fi
    fi
done

# If not found via mDNS, scan the 192.168.125.x subnet
if [ -z "$PI_IP" ]; then
    echo "  mDNS not found, scanning 192.168.125.0/24 for SSH..."
    for ip in $(seq 2 254); do
        target="192.168.125.$ip"
        [ "$target" = "192.168.125.1" ] && continue
        [ "$target" = "192.168.125.127" ] && continue
        [ "$target" = "192.168.125.128" ] && continue

        if sshpass -p "${PI_PASS}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=1 ${PI_USER}@${target} "echo ok" 2>/dev/null | grep -q "ok"; then
            PI_IP="$target"
            echo "  Found Pi at: $PI_IP"
            break
        fi
    done
fi

if [ -z "$PI_IP" ]; then
    echo ""
    echo "  Pi not found on network!"
    echo ""
    echo "  Make sure:"
    echo "  1. SD card is flashed with Pi OS (SSH enabled, WiFi configured)"
    echo "  2. Pi is powered on and connected to WiFi 'no more mr wifi'"
    echo "  3. Wait 2-3 minutes after first boot for WiFi to connect"
    echo ""
    echo "  Once Pi is online, run this script again."
    exit 1
fi

# Step 2: Deploy files
echo ""
echo "[2/5] Deploying files to Pi ($PI_IP)..."
${SSH_CMD} ${PI_USER}@${PI_IP} "mkdir -p ${PI_DIR}"
${SCP_CMD} ${SCRIPT_DIR}/megaphone.py ${PI_USER}@${PI_IP}:${PI_DIR}/
${SCP_CMD} ${SCRIPT_DIR}/requirements.txt ${PI_USER}@${PI_IP}:${PI_DIR}/
${SCP_CMD} ${SCRIPT_DIR}/.env ${PI_USER}@${PI_IP}:${PI_DIR}/
${SCP_CMD} ${SCRIPT_DIR}/voice_config.json ${PI_USER}@${PI_IP}:${PI_DIR}/
${SCP_CMD} ${SCRIPT_DIR}/rasta-megaphone.service ${PI_USER}@${PI_IP}:${PI_DIR}/
${SCP_CMD} ${SCRIPT_DIR}/setup_pi.sh ${PI_USER}@${PI_IP}:${PI_DIR}/
echo "  Files deployed!"

# Step 3: Run setup
echo ""
echo "[3/5] Running setup on Pi (this takes a few minutes on Pi Zero)..."
${SSH_CMD} ${PI_USER}@${PI_IP} "cd ${PI_DIR} && bash setup_pi.sh"

# Step 4: Start service
echo ""
echo "[4/5] Starting megaphone service..."
${SSH_CMD} ${PI_USER}@${PI_IP} "sudo systemctl start rasta-megaphone"
sleep 3

# Step 5: Verify
echo ""
echo "[5/5] Verifying..."
STATUS=$(${SSH_CMD} ${PI_USER}@${PI_IP} "sudo systemctl is-active rasta-megaphone 2>/dev/null || echo 'inactive'")

if [ "$STATUS" = "active" ]; then
    echo ""
    echo "=========================================="
    echo "  MEGAPHONE IS LIVE!"
    echo "=========================================="
    echo ""
    echo "  Pi IP: $PI_IP"
    echo "  SSH:   sshpass -p '${PI_PASS}' ssh pi@$PI_IP"
    echo "  Logs:  bash monitor.sh logs"
    echo "  Test:  bash monitor.sh test"
    echo ""
    echo "  Speak into the mic - Rasta Mon comes out the speaker!"
else
    echo ""
    echo "  Service not active yet. Check logs:"
    echo "  bash monitor.sh logs"
    echo ""
    echo "  Try manual test:"
    echo "  bash monitor.sh test"
fi
