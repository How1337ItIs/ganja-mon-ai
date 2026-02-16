"""
Watchdog
========

Component liveness tracker. Components send heartbeats;
watchdog detects when they go stale.

Usage:
    wd = get_watchdog()
    wd.heartbeat("orchestrator")
    wd.heartbeat("trading_agent")

    stale = wd.get_stale(threshold=300)
    # → ["trading_agent"] if no heartbeat for 5 min
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ComponentInfo:
    """Tracking info for a single component."""
    last_heartbeat: float = 0.0
    status: str = "unknown"  # "healthy", "degraded", "stale", "unknown"
    message: str = ""
    heartbeat_count: int = 0


class Watchdog:
    """Track liveness of all agent components."""

    def __init__(self, default_threshold: float = 300.0):
        self._components: Dict[str, ComponentInfo] = {}
        self._thresholds: Dict[str, float] = {}
        self.default_threshold = default_threshold

    def register(self, name: str, threshold: Optional[float] = None) -> None:
        """Register a component to track."""
        self._components[name] = ComponentInfo()
        if threshold is not None:
            self._thresholds[name] = threshold

    def heartbeat(self, name: str, status: str = "healthy", message: str = "") -> None:
        """Record a heartbeat from a component."""
        if name not in self._components:
            self._components[name] = ComponentInfo()
        info = self._components[name]
        info.last_heartbeat = time.time()
        info.status = status
        info.message = message
        info.heartbeat_count += 1

    def get_stale(self, threshold: Optional[float] = None) -> List[str]:
        """Get list of components that haven't reported in."""
        t = threshold or self.default_threshold
        now = time.time()
        stale = []
        for name, info in self._components.items():
            comp_threshold = self._thresholds.get(name, t)
            if info.last_heartbeat == 0.0:
                stale.append(name)
            elif (now - info.last_heartbeat) > comp_threshold:
                stale.append(name)
        return stale

    def get_status(self) -> Dict[str, dict]:
        """Get status of all tracked components."""
        now = time.time()
        result = {}
        for name, info in self._components.items():
            threshold = self._thresholds.get(name, self.default_threshold)
            age = now - info.last_heartbeat if info.last_heartbeat > 0 else -1

            if info.last_heartbeat == 0.0:
                effective_status = "unknown"
            elif age > threshold:
                effective_status = "stale"
            else:
                effective_status = info.status

            result[name] = {
                "status": effective_status,
                "last_heartbeat_age": round(age, 1) if age >= 0 else None,
                "heartbeat_count": info.heartbeat_count,
                "message": info.message,
            }
        return result

    @property
    def all_healthy(self) -> bool:
        """True if no components are stale."""
        return len(self.get_stale()) == 0


# Singleton
_watchdog: Optional[Watchdog] = None


def get_watchdog() -> Watchdog:
    """Get global watchdog singleton."""
    global _watchdog
    if _watchdog is None:
        _watchdog = Watchdog()
    return _watchdog
