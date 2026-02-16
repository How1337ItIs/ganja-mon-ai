#!/bin/bash
# Quick monitoring commands for the Rasta Megaphone Pi
# Usage: bash monitor.sh [command]
# Commands: status, logs, test, restart, ssh, devices, update

PI_HOST="${PI_HOST:-192.168.125.222}"
PI_USER="${PI_USER:-midaswhale}"
PI_PASS="${PI_PASS:-newpass1337**}"
SSH="sshpass -p '${PI_PASS}' ssh -o StrictHostKeyChecking=no"
SCP="sshpass -p '${PI_PASS}' scp -o StrictHostKeyChecking=no"

CMD="${1:-status}"

case "$CMD" in
    status)
        echo "Checking megaphone status..."
        ${SSH} ${PI_USER}@${PI_HOST} "
            echo '=== Service ==='
            sudo systemctl status rasta-megaphone --no-pager 2>/dev/null | head -10
            echo ''
            echo '=== Audio Devices ==='
            aplay -l 2>/dev/null | head -10
            echo ''
            echo '=== System ==='
            uptime
            free -h | head -2
            vcgencmd measure_temp 2>/dev/null || echo 'temp: N/A'
        "
        ;;
    logs)
        echo "Streaming megaphone logs (Ctrl+C to stop)..."
        ${SSH} ${PI_USER}@${PI_HOST} "sudo journalctl -u rasta-megaphone -f"
        ;;
    test)
        echo "Running component test..."
        ${SSH} ${PI_USER}@${PI_HOST} "cd /home/pi/megaphone && source venv/bin/activate && python3 megaphone.py --test"
        ;;
    restart)
        echo "Restarting megaphone..."
        ${SSH} ${PI_USER}@${PI_HOST} "sudo systemctl restart rasta-megaphone"
        sleep 2
        ${SSH} ${PI_USER}@${PI_HOST} "sudo systemctl status rasta-megaphone --no-pager | head -5"
        ;;
    ssh)
        ${SSH} ${PI_USER}@${PI_HOST}
        ;;
    devices)
        echo "Audio devices on Pi:"
        ${SSH} ${PI_USER}@${PI_HOST} "cd /home/pi/megaphone && source venv/bin/activate && python3 megaphone.py --list-devices"
        ;;
    update)
        echo "Updating megaphone code on Pi..."
        SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
        ${SCP} ${SCRIPT_DIR}/megaphone.py ${PI_USER}@${PI_HOST}:/home/midaswhale/megaphone/
        ${SCP} ${SCRIPT_DIR}/.env ${PI_USER}@${PI_HOST}:/home/midaswhale/megaphone/
        ${SCP} ${SCRIPT_DIR}/voice_config.json ${PI_USER}@${PI_HOST}:/home/midaswhale/megaphone/
        ${SSH} ${PI_USER}@${PI_HOST} "sudo systemctl restart rasta-megaphone"
        echo "Updated and restarted!"
        ;;
    *)
        echo "Usage: bash monitor.sh [status|logs|test|restart|ssh|devices|update]"
        ;;
esac
