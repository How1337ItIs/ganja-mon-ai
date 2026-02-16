"""
System Administration API
==========================

Admin endpoints for remote system management via Cloudflare Tunnel.
Provides reboot, service restart, shell execution, and log viewing
capabilities when SSH is unavailable.

Security:
- All endpoints require admin authentication (JWT)
- Shell exec is logged and sanitized
- Reboot requires confirmation parameter
"""

import os
import asyncio
import subprocess
import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

# Try both import styles
try:
    from .auth import get_current_admin, User
except ImportError:
    from auth import get_current_admin, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# =============================================================================
# Models
# =============================================================================

class ExecRequest(BaseModel):
    command: str
    timeout: int = 30  # max 60 seconds

class ExecResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration_ms: int

class ServiceStatus(BaseModel):
    name: str
    active: bool
    running: bool
    enabled: bool
    uptime: Optional[str] = None
    memory_mb: Optional[float] = None


# =============================================================================
# System Control Endpoints
# =============================================================================

@router.post("/reboot")
async def reboot_system(
    confirm: bool = Query(False, description="Must be True to confirm reboot"),
    delay_seconds: int = Query(5, ge=1, le=60, description="Delay before reboot"),
    current_user: User = Depends(get_current_admin),
):
    """
    Reboot the Chromebook server.
    Requires confirm=True to prevent accidental reboots.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Reboot not confirmed. Set confirm=True to proceed."
        )
    
    logger.warning(f"[ADMIN] Reboot requested by {current_user.username}, delay={delay_seconds}s")
    
    # Schedule reboot in background
    async def do_reboot():
        await asyncio.sleep(delay_seconds)
        os.system("sudo reboot")
    
    asyncio.create_task(do_reboot())
    
    return {
        "status": "rebooting",
        "delay_seconds": delay_seconds,
        "message": f"System will reboot in {delay_seconds} seconds",
        "requested_by": current_user.username,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/restart-service/{service_name}")
async def restart_service(
    service_name: str,
    current_user: User = Depends(get_current_admin),
):
    """
    Restart a systemd service.
    Common services: grokmon, cloudflared
    """
    # Whitelist of allowed services for safety
    ALLOWED_SERVICES = {"grokmon", "cloudflared", "ssh", "nginx"}
    
    if service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{service_name}' not in allowed list: {ALLOWED_SERVICES}"
        )
    
    logger.warning(f"[ADMIN] Service restart requested: {service_name} by {current_user.username}")
    
    try:
        # Try user service first, then system service
        result = subprocess.run(
            ["systemctl", "--user", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            # Try system service
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30,
            )
        
        success = result.returncode == 0
        
        return {
            "status": "restarted" if success else "failed",
            "service": service_name,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "requested_by": current_user.username,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Service restart timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service-status/{service_name}")
async def get_service_status(
    service_name: str,
    current_user: User = Depends(get_current_admin),
) -> ServiceStatus:
    """Get status of a systemd service."""
    try:
        # Try user service first
        result = subprocess.run(
            ["systemctl", "--user", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        is_user_service = result.returncode == 0
        
        if not is_user_service:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
        
        active = result.stdout.strip() == "active"
        
        # Get more status info
        prefix = ["systemctl", "--user"] if is_user_service else ["systemctl"]
        status_result = subprocess.run(
            prefix + ["show", service_name, "--property=ActiveState,SubState,UnitFileState"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        props = dict(
            line.split("=", 1)
            for line in status_result.stdout.strip().split("\n")
            if "=" in line
        )
        
        return ServiceStatus(
            name=service_name,
            active=props.get("ActiveState") == "active",
            running=props.get("SubState") == "running",
            enabled=props.get("UnitFileState") == "enabled",
        )
    except Exception as e:
        return ServiceStatus(
            name=service_name,
            active=False,
            running=False,
            enabled=False,
        )


@router.get("/services")
async def list_services(
    current_user: User = Depends(get_current_admin),
) -> List[ServiceStatus]:
    """List status of all important services."""
    services = ["grokmon", "cloudflared", "ssh"]
    statuses = []
    
    for svc in services:
        status = await get_service_status(svc, current_user)
        statuses.append(status)
    
    return statuses


# =============================================================================
# Shell Execution (with Safety)
# =============================================================================

# Commands that are explicitly allowed (safe patterns)
SAFE_COMMANDS = {
    "uptime", "df -h", "free -h", "ps aux", "top -bn1", "cat /etc/os-release",
    "ip addr", "systemctl --user status grokmon", "journalctl --user -u grokmon -n 50",
    "cloudflared tunnel list", "ls -la", "pwd", "whoami", "date",
}

# Patterns that are NEVER allowed
DANGEROUS_PATTERNS = [
    "rm -rf", "mkfs", "dd if=", ":(){ :|:& };:", "fork bomb",
    "> /dev/sd", "chmod 777 /", "curl | sh", "wget | sh",
]


@router.post("/exec")
async def execute_command(
    request: ExecRequest,
    current_user: User = Depends(get_current_admin),
) -> ExecResponse:
    """
    Execute a shell command on the server.
    
    Security:
    - Admin auth required
    - Dangerous patterns blocked
    - Timeout enforced (max 60s)
    - All executions are logged
    """
    command = request.command.strip()
    timeout = min(request.timeout, 60)  # Cap at 60s
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in command.lower():
            logger.error(f"[ADMIN] BLOCKED dangerous command from {current_user.username}: {command}")
            raise HTTPException(
                status_code=403,
                detail=f"Command blocked: contains dangerous pattern '{pattern}'"
            )
    
    logger.info(f"[ADMIN] Exec by {current_user.username}: {command}")
    
    start_time = datetime.utcnow()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/natha",
        )
        
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return ExecResponse(
            success=result.returncode == 0,
            stdout=result.stdout[-10000:],  # Limit output size
            stderr=result.stderr[-5000:],
            return_code=result.returncode,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail=f"Command timed out after {timeout}s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Log Viewing
# =============================================================================

@router.get("/logs/{service_name}")
async def get_logs(
    service_name: str,
    lines: int = Query(100, ge=10, le=1000),
    current_user: User = Depends(get_current_admin),
):
    """Get recent logs for a service."""
    ALLOWED_SERVICES = {"grokmon", "cloudflared", "ssh"}
    
    if service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{service_name}' not in allowed list: {ALLOWED_SERVICES}"
        )
    
    try:
        # Try user service first
        result = subprocess.run(
            ["journalctl", "--user", "-u", service_name, "-n", str(lines), "--no-pager"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if "No journal files" in result.stderr or result.returncode != 0:
            # Try system service
            result = subprocess.run(
                ["journalctl", "-u", service_name, "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        
        return {
            "service": service_name,
            "lines": lines,
            "logs": result.stdout,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Log fetch timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# System Info
# =============================================================================

@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(get_current_admin),
):
    """Get system information (uptime, memory, disk, etc.)"""
    info = {}
    
    # Uptime
    try:
        result = subprocess.run(["uptime", "-p"], capture_output=True, text=True, timeout=5)
        info["uptime"] = result.stdout.strip()
    except:
        info["uptime"] = "unknown"
    
    # Memory
    try:
        result = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        info["memory"] = result.stdout.strip()
    except:
        info["memory"] = "unknown"
    
    # Disk
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        info["disk"] = result.stdout.strip()
    except:
        info["disk"] = "unknown"
    
    # Load average
    try:
        with open("/proc/loadavg") as f:
            load = f.read().strip().split()[:3]
            info["load_average"] = {"1m": load[0], "5m": load[1], "15m": load[2]}
    except:
        info["load_average"] = "unknown"
    
    # Temperature (if available)
    try:
        result = subprocess.run(
            ["cat", "/sys/class/thermal/thermal_zone0/temp"],
            capture_output=True, text=True, timeout=5
        )
        temp_mc = int(result.stdout.strip())
        info["cpu_temp_c"] = temp_mc / 1000
    except:
        info["cpu_temp_c"] = None
    
    info["timestamp"] = datetime.utcnow().isoformat()
    
    return info


# =============================================================================
# Telegram Agent Session
# =============================================================================

_telegram_session = None

async def _get_telegram_session():
    """Lazy-init singleton for Telegram agent session."""
    global _telegram_session
    if _telegram_session is None:
        try:
            from ..telegram.agent_session import AgentTelegramSession
            _telegram_session = AgentTelegramSession()
            ok = await _telegram_session.start()
            if not ok:
                _telegram_session = None
                return None
        except Exception as e:
            logger.error(f"Failed to init Telegram agent session: {e}")
            return None
    return _telegram_session


class TelegramPostRequest(BaseModel):
    chat_id: int = -1003584948806
    message: str
    reply_to: Optional[int] = None


class TelegramDescriptionRequest(BaseModel):
    chat_id: int = -1003584948806
    description: str


@router.get("/telegram/status")
async def telegram_status(current_user: User = Depends(get_current_admin)):
    """Get Telegram agent session status and group info."""
    session = await _get_telegram_session()
    if not session:
        return {"status": "unavailable", "error": "Session not authorized"}

    count = await session.get_member_count()
    return {
        "status": "connected",
        "member_count": count,
        "stats": session.stats,
    }


@router.post("/telegram/post")
async def telegram_post(
    request: TelegramPostRequest,
    current_user: User = Depends(get_current_admin),
):
    """Post a message to a Telegram group as the user account."""
    session = await _get_telegram_session()
    if not session:
        raise HTTPException(503, "Telegram session unavailable")

    msg_id = await session.post(
        request.chat_id, request.message, reply_to=request.reply_to
    )
    if msg_id:
        return {"success": True, "message_id": msg_id}
    raise HTTPException(429, "Post failed — rate limit or daily cap reached")


@router.post("/telegram/set-description")
async def telegram_set_description(
    request: TelegramDescriptionRequest,
    current_user: User = Depends(get_current_admin),
):
    """Update Telegram group description."""
    session = await _get_telegram_session()
    if not session:
        raise HTTPException(503, "Telegram session unavailable")

    ok = await session.set_group_description(request.chat_id, request.description)
    return {"success": ok}


@router.get("/telegram/messages")
async def telegram_read_messages(
    chat_id: int = Query(-1003584948806),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
):
    """Read recent messages from a Telegram chat."""
    session = await _get_telegram_session()
    if not session:
        raise HTTPException(503, "Telegram session unavailable")

    msgs = await session.read_messages(chat_id, limit=limit)
    return {"messages": msgs, "count": len(msgs)}


@router.get("/ping")
async def ping():
    """Simple health check that doesn't require auth - useful for tunnel testing."""
    return {
        "status": "pong",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "chromebook",
    }
