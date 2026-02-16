#!/bin/bash
# Disable all watchdog services permanently
# Run this on the Chromebook with: sudo bash disable_watchdogs.sh

echo "Disabling grokmon-watchdog system service..."
systemctl stop grokmon-watchdog.service
systemctl disable grokmon-watchdog.service

echo "Removing system service file..."
rm -f /etc/systemd/system/grokmon-watchdog.service

echo "Killing any running watchdog processes..."
pkill -9 -f watchdog.sh

echo "Removing watchdog scripts..."
rm -f /home/natha/scripts/watchdog.sh
rm -f /home/natha/bin/healthcheck.sh

echo "Reloading systemd..."
systemctl daemon-reload

echo ""
echo "✅ All watchdogs disabled!"
echo "Grokmon will only restart if it actually crashes (via systemd Restart=always)"
