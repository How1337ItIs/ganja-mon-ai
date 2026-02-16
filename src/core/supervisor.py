"""
Supervisor
==========

asyncio task manager with restart policies and backoff.
Manages long-running component tasks (orchestrator, signal feeds, etc.).

Usage:
    sup = get_supervisor()
    sup.add("orchestrator", orchestrator_coro, restart=True)
    sup.add("dexscreener_ws", dex_ws_coro, restart=True, max_restarts=10)
    await sup.start_all()
    ...
    await sup.stop_all()
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

import structlog

log = structlog.get_logger("supervisor")


class RestartPolicy(str, Enum):
    ALWAYS = "always"       # Always restart on failure
    NEVER = "never"         # Never restart
    ON_FAILURE = "on_failure"  # Restart only on exception (not clean exit)


@dataclass
class WorkerSpec:
    """Specification for a supervised worker."""
    name: str
    coro_factory: Callable[[], Coroutine]
    restart_policy: RestartPolicy = RestartPolicy.ON_FAILURE
    max_restarts: int = 5
    backoff_base: float = 2.0
    backoff_max: float = 300.0  # 5 min max backoff
    restart_budget_window: float = 3600.0  # Reset restart count after 1h of clean running


@dataclass
class WorkerState:
    """Runtime state for a supervised worker."""
    task: Optional[asyncio.Task] = None
    restart_count: int = 0
    last_start: float = 0.0
    last_failure: float = 0.0
    running: bool = False
    error: Optional[str] = None


class Supervisor:
    """
    Manages asyncio tasks with one-for-one restart strategy.

    Each worker runs independently. If one crashes, only that
    worker is restarted (with exponential backoff).
    """

    def __init__(self):
        self._specs: Dict[str, WorkerSpec] = {}
        self._states: Dict[str, WorkerState] = {}
        self._running = False

    def add(
        self,
        name: str,
        coro_factory: Callable[[], Coroutine],
        restart: bool = True,
        max_restarts: int = 5,
        backoff_base: float = 2.0,
    ) -> None:
        """Register a worker to be supervised."""
        policy = RestartPolicy.ON_FAILURE if restart else RestartPolicy.NEVER
        self._specs[name] = WorkerSpec(
            name=name,
            coro_factory=coro_factory,
            restart_policy=policy,
            max_restarts=max_restarts,
            backoff_base=backoff_base,
        )
        self._states[name] = WorkerState()

    async def start_all(self) -> None:
        """Start all registered workers."""
        self._running = True
        for name in self._specs:
            await self._start_worker(name)

    async def stop_all(self) -> None:
        """Gracefully stop all workers."""
        self._running = False
        tasks = []
        for name, state in self._states.items():
            if state.task and not state.task.done():
                state.task.cancel()
                tasks.append(state.task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        for state in self._states.values():
            state.running = False

    async def _start_worker(self, name: str) -> None:
        """Start a single worker task."""
        spec = self._specs[name]
        state = self._states[name]

        state.last_start = time.time()
        state.running = True
        state.error = None
        state.task = asyncio.create_task(
            self._run_worker(name),
            name=f"supervisor:{name}",
        )

    async def _run_worker(self, name: str) -> None:
        """Run a worker with restart logic."""
        spec = self._specs[name]
        state = self._states[name]

        try:
            await spec.coro_factory()
            # Clean exit
            state.running = False
            log.info("worker_exited", worker=name)

            if spec.restart_policy == RestartPolicy.ALWAYS and self._running:
                await self._schedule_restart(name)

        except asyncio.CancelledError:
            state.running = False
            log.info("worker_cancelled", worker=name)

        except Exception as e:
            state.running = False
            state.error = str(e)
            state.last_failure = time.time()
            log.error("worker_crashed", worker=name, error=str(e))

            if spec.restart_policy in (RestartPolicy.ALWAYS, RestartPolicy.ON_FAILURE):
                if self._running:
                    await self._schedule_restart(name)

    async def _schedule_restart(self, name: str) -> None:
        """Schedule a worker restart with backoff."""
        spec = self._specs[name]
        state = self._states[name]

        # Reset restart count if worker ran long enough
        if state.last_start > 0:
            uptime = time.time() - state.last_start
            if uptime > spec.restart_budget_window:
                state.restart_count = 0

        state.restart_count += 1

        if state.restart_count > spec.max_restarts:
            log.error(
                "worker_restart_limit",
                worker=name,
                restarts=state.restart_count,
                max=spec.max_restarts,
            )
            return

        # Exponential backoff
        delay = min(
            spec.backoff_base ** state.restart_count,
            spec.backoff_max,
        )
        log.warning(
            "worker_restarting",
            worker=name,
            attempt=state.restart_count,
            delay=delay,
        )

        await asyncio.sleep(delay)

        if self._running:
            await self._start_worker(name)

    def get_status(self) -> Dict[str, dict]:
        """Get status of all workers."""
        result = {}
        for name, state in self._states.items():
            spec = self._specs.get(name)
            result[name] = {
                "running": state.running,
                "restart_count": state.restart_count,
                "max_restarts": spec.max_restarts if spec else 0,
                "error": state.error,
                "uptime": round(time.time() - state.last_start, 1) if state.last_start > 0 else 0,
            }
        return result

    @property
    def all_running(self) -> bool:
        """True if all workers are currently running."""
        return all(s.running for s in self._states.values()) if self._states else True


# Singleton
_supervisor: Optional[Supervisor] = None


def get_supervisor() -> Supervisor:
    """Get global supervisor singleton."""
    global _supervisor
    if _supervisor is None:
        _supervisor = Supervisor()
    return _supervisor
