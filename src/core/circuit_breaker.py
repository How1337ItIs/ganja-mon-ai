"""
Circuit Breaker
===============

Pure-Python async circuit breaker for external service calls.
Prevents cascade failures when APIs go down.

States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED

Usage:
    breaker = get_breaker("grok_api")

    async with breaker:
        response = await call_grok_api()

    # Or as decorator:
    @circuit_breaker("grok_api")
    async def call_grok(prompt):
        ...
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional


class BreakerState(str, Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing — reject all calls
    HALF_OPEN = "half_open"  # Testing — allow one call through


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""
    def __init__(self, service: str, reset_in: float):
        self.service = service
        self.reset_in = reset_in
        super().__init__(f"Circuit open for {service}, resets in {reset_in:.0f}s")


@dataclass
class BreakerConfig:
    """Configuration for a single circuit breaker."""
    fail_max: int = 3             # Failures before opening
    reset_timeout: float = 60.0   # Seconds before trying half-open
    half_open_max: int = 1        # Successes needed to close


@dataclass
class BreakerStats:
    """Runtime statistics for a breaker."""
    state: BreakerState = BreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    total_calls: int = 0
    total_failures: int = 0
    total_rejections: int = 0


class CircuitBreaker:
    """
    Async circuit breaker for a single service.

    Use as async context manager or decorator.
    """

    def __init__(self, service: str, config: Optional[BreakerConfig] = None):
        self.service = service
        self.config = config or BreakerConfig()
        self.stats = BreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> BreakerState:
        return self.stats.state

    @property
    def is_available(self) -> bool:
        """Check if calls can go through without acquiring lock."""
        if self.stats.state == BreakerState.CLOSED:
            return True
        if self.stats.state == BreakerState.OPEN:
            elapsed = time.time() - self.stats.last_failure_time
            return elapsed >= self.config.reset_timeout
        return True  # HALF_OPEN allows trial calls

    async def _check_state(self) -> None:
        """Transition state if needed. Must be called under lock."""
        if self.stats.state == BreakerState.OPEN:
            elapsed = time.time() - self.stats.last_failure_time
            if elapsed >= self.config.reset_timeout:
                self.stats.state = BreakerState.HALF_OPEN
                self.stats.success_count = 0

    async def record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self.stats.last_success_time = time.time()
            self.stats.total_calls += 1

            if self.stats.state == BreakerState.HALF_OPEN:
                self.stats.success_count += 1
                if self.stats.success_count >= self.config.half_open_max:
                    self.stats.state = BreakerState.CLOSED
                    self.stats.failure_count = 0
            else:
                self.stats.failure_count = 0

    async def record_failure(self) -> None:
        """Record a failed call."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.total_calls += 1
            self.stats.last_failure_time = time.time()

            if self.stats.state == BreakerState.HALF_OPEN:
                # Failed during test — reopen
                self.stats.state = BreakerState.OPEN
            elif self.stats.failure_count >= self.config.fail_max:
                self.stats.state = BreakerState.OPEN

            # Emit event (lazy import to avoid circular)
            try:
                from src.core.events import get_event_bus, CircuitBreakerEvent
                bus = get_event_bus()
                bus.emit_nowait(CircuitBreakerEvent(
                    source="circuit_breaker",
                    service=self.service,
                    state=self.stats.state.value,
                    failure_count=self.stats.failure_count,
                ))
            except Exception:
                pass

    async def __aenter__(self):
        async with self._lock:
            await self._check_state()

            if self.stats.state == BreakerState.OPEN:
                self.stats.total_rejections += 1
                reset_in = self.config.reset_timeout - (
                    time.time() - self.stats.last_failure_time
                )
                raise CircuitOpenError(self.service, max(0, reset_in))

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.record_success()
        elif exc_type is not CircuitOpenError:
            await self.record_failure()
        return False  # Don't suppress exceptions

    def get_status(self) -> Dict[str, Any]:
        """Snapshot of current breaker state."""
        return {
            "service": self.service,
            "state": self.stats.state.value,
            "failures": self.stats.failure_count,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_rejections": self.stats.total_rejections,
            "available": self.is_available,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Default configs per service (from plan)
DEFAULT_CONFIGS: Dict[str, BreakerConfig] = {
    "grok_api":         BreakerConfig(fail_max=3, reset_timeout=120),
    "govee_api":        BreakerConfig(fail_max=5, reset_timeout=60),
    "kasa_lan":         BreakerConfig(fail_max=5, reset_timeout=30),
    "ecowitt_lan":      BreakerConfig(fail_max=5, reset_timeout=30),
    "farcaster_api":    BreakerConfig(fail_max=3, reset_timeout=180),
    "dexscreener_api":  BreakerConfig(fail_max=3, reset_timeout=60),
    "dexscreener_ws":   BreakerConfig(fail_max=3, reset_timeout=30),
    "hyperliquid_api":  BreakerConfig(fail_max=3, reset_timeout=60),
    "gmgn_api":         BreakerConfig(fail_max=5, reset_timeout=120),
    "polymarket_api":   BreakerConfig(fail_max=3, reset_timeout=60),
    "nadfun_api":       BreakerConfig(fail_max=3, reset_timeout=30),
    "jupiter_api":      BreakerConfig(fail_max=3, reset_timeout=60),
    "coinbase_cdp":     BreakerConfig(fail_max=3, reset_timeout=120),
}

_breakers: Dict[str, CircuitBreaker] = {}


def get_breaker(service: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a service."""
    if service not in _breakers:
        config = DEFAULT_CONFIGS.get(service, BreakerConfig())
        _breakers[service] = CircuitBreaker(service, config)
    return _breakers[service]


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered breakers."""
    return dict(_breakers)


def circuit_breaker(service: str) -> Callable:
    """Decorator that wraps an async function with a circuit breaker."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = get_breaker(service)
            async with breaker:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
