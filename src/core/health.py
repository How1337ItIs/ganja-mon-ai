"""
Health Endpoints
================

FastAPI router for /health (liveness) and /ready (readiness).
Aggregates status from watchdog, circuit breakers, and supervisor.

Usage:
    from src.core.health import health_router
    app.include_router(health_router)
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Liveness probe. Returns 200 if process is alive.
    Includes component status for monitoring.
    """
    from src.core.watchdog import get_watchdog
    from src.core.circuit_breaker import get_all_breakers

    wd = get_watchdog()
    breakers = get_all_breakers()

    # Signal source status (handled by trading agent subprocess)
    signals = {}

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": wd.get_status(),
        "circuit_breakers": {
            name: cb.get_status() for name, cb in breakers.items()
        },
        "signals": signals,
    }


@health_router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe. Returns 200 only if critical components are healthy.
    Use for load balancers / service mesh.
    """
    from src.core.watchdog import get_watchdog

    wd = get_watchdog()
    stale = wd.get_stale()
    has_components = len(wd.get_status()) > 0
    ready = has_components and len(stale) == 0

    return {
        "ready": ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stale_components": stale,
        "no_components_registered": not has_components,
    }
