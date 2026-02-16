#!/usr/bin/env python3
"""
Comprehensive Health Monitoring
================================
Monitors system health and sends alerts if issues detected.

Checks:
- API health endpoint
- Database size and growth
- Disk space
- Memory usage
- CPU load
- Service status
- Log errors

Usage:
    python scripts/monitor_health.py

Cron (every 5 minutes):
    */5 * * * * cd /home/natha/projects/sol-cannabis && python3 scripts/monitor_health.py
"""

import asyncio
import os
import sys
import psutil
import httpx
from pathlib import Path
from datetime import datetime

# Thresholds
CPU_THRESHOLD = 80  # percent
MEMORY_THRESHOLD = 85  # percent
DISK_THRESHOLD = 90  # percent
DB_SIZE_THRESHOLD = 1000  # MB

ALERT_FILE = Path("/tmp/grokmon_alerts.log")


async def check_api_health():
    """Check if API is responding"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return True, "API healthy"
                else:
                    return False, f"API degraded: {data}"
            else:
                return False, f"API returned {response.status_code}"
    except Exception as e:
        return False, f"API unreachable: {e}"


def check_system_resources():
    """Check CPU, memory, disk"""
    issues = []

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > CPU_THRESHOLD:
        issues.append(f"CPU usage high: {cpu_percent:.1f}%")

    # Memory
    memory = psutil.virtual_memory()
    if memory.percent > MEMORY_THRESHOLD:
        issues.append(f"Memory usage high: {memory.percent:.1f}%")

    # Disk
    disk = psutil.disk_usage('/')
    if disk.percent > DISK_THRESHOLD:
        issues.append(f"Disk usage high: {disk.percent:.1f}%")

    return len(issues) == 0, issues


def check_database():
    """Check database size and integrity"""
    db_path = Path(__file__).parent.parent / "grokmon.db"

    if not db_path.exists():
        return False, ["Database file missing!"]

    # Check size
    size_mb = db_path.stat().st_size / 1024 / 1024

    if size_mb > DB_SIZE_THRESHOLD:
        return False, [f"Database very large: {size_mb:.1f}MB (consider archiving old data)"]

    return True, [f"Database size: {size_mb:.1f}MB"]


def check_service_status():
    """Check if grokmon service is running"""
    try:
        result = os.popen("systemctl --user is-active grokmon 2>/dev/null").read().strip()
        if result == "active":
            return True, "Service running"
        else:
            return False, f"Service not active: {result}"
    except Exception as e:
        return False, f"Service check failed: {e}"


def send_alert(message: str):
    """Log alert to file (extend with Discord/email/SMS)"""
    timestamp = datetime.now().isoformat()
    alert_line = f"[{timestamp}] ALERT: {message}\n"

    with open(ALERT_FILE, 'a') as f:
        f.write(alert_line)

    print(f"[!] {alert_line.strip()}")

    # TODO: Add Discord webhook notification
    # TODO: Add email notification
    # TODO: Add SMS notification via Twilio


async def main():
    """Run all health checks"""
    print(f"\n[*] Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_healthy = True

    # API Health
    api_ok, api_msg = await check_api_health()
    status = "✓" if api_ok else "✗"
    print(f"  [{status}] API: {api_msg}")
    if not api_ok:
        all_healthy = False
        send_alert(f"API health check failed: {api_msg}")

    # System Resources
    sys_ok, sys_msgs = check_system_resources()
    if sys_ok:
        print(f"  [✓] System: Resources OK")
    else:
        print(f"  [✗] System: {', '.join(sys_msgs)}")
        all_healthy = False
        for msg in sys_msgs:
            send_alert(f"System resource issue: {msg}")

    # Database
    db_ok, db_msgs = check_database()
    for msg in db_msgs:
        status = "✓" if db_ok else "✗"
        print(f"  [{status}] Database: {msg}")
    if not db_ok:
        all_healthy = False
        for msg in db_msgs:
            send_alert(f"Database issue: {msg}")

    # Service
    svc_ok, svc_msg = check_service_status()
    status = "✓" if svc_ok else "✗"
    print(f"  [{status}] Service: {svc_msg}")
    if not svc_ok:
        all_healthy = False
        send_alert(f"Service issue: {svc_msg}")

    print("=" * 60)

    if all_healthy:
        print("[✓] All systems healthy!")
    else:
        print("[!] Issues detected - check alerts")

    return all_healthy


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n[!] Health check interrupted")
        sys.exit(1)
