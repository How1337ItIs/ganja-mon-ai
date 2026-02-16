"""
Resilient Orchestrator - Smart Recovery & Error Handling
=========================================================

This is a thin wrapper around the base orchestrator that adds:
1. Proper signal handling for graceful shutdown
2. Shutdown timeout to prevent stuck processes

The base orchestrator now includes:
- Timeouts on all hardware/database operations
- Automatic reconnection when hardware fails
- Stall detection and recovery
- Exponential backoff on failures
"""

import asyncio
import signal
import sys
from typing import Optional
from datetime import datetime

from src.orchestrator.orchestrator import GrokMonOrchestrator as BaseOrchestrator


class ResilientOrchestrator(BaseOrchestrator):
    """Enhanced orchestrator with signal handling and graceful shutdown"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Start with signal handling for graceful shutdown"""
        print("[*] Starting resilient orchestrator...")

        # Register signal handlers
        loop = asyncio.get_running_loop()

        def signal_handler(sig):
            print(f"\n[*] Received signal {sig}, initiating graceful shutdown...")
            self._shutdown_event.set()
            self._running = False

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

        try:
            # Call parent start - uses base sensor/AI loops with full resilience
            await super().start()
        except Exception as e:
            print(f"[ERR] Orchestrator start failed: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Graceful shutdown with timeout"""
        print("[*] Stopping orchestrator gracefully...")
        self._running = False

        try:
            # Wait up to 10 seconds for clean shutdown
            await asyncio.wait_for(self._shutdown_tasks(), timeout=10.0)
            print("[OK] Graceful shutdown complete")
        except asyncio.TimeoutError:
            print("[WARN] Shutdown timeout, forcing...")
            # Force cancel tasks
            if self._sensor_task:
                self._sensor_task.cancel()
            if self._ai_task:
                self._ai_task.cancel()

        await super().stop()

    async def _shutdown_tasks(self):
        """Cleanly shutdown async tasks"""
        tasks = []
        if self._sensor_task:
            self._sensor_task.cancel()
            tasks.append(self._sensor_task)
        if self._ai_task:
            self._ai_task.cancel()
            tasks.append(self._ai_task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Patch the imports to use resilient version
import src.orchestrator
src.orchestrator.GrokMonOrchestrator = ResilientOrchestrator
