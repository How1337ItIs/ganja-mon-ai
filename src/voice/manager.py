"""
Voice Pipeline Manager
======================

Controls the Rasta Voice Pipeline via API.
Runs the pipeline as a subprocess and captures output for monitoring.

NOTE: The voice pipeline requires Windows (VB-Cable, microphone, ElevenLabs).
On non-Windows platforms all operations return graceful "not available" responses.
"""

import asyncio
import logging
import os
import platform
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Callable
from collections import deque

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows" or "microsoft" in platform.release().lower()


@dataclass
class VoiceEvent:
    """A single voice event (transcript or rasta output)"""
    timestamp: datetime
    event_type: str  # "transcript", "rasta", "latency", "error"
    text: str
    latency_ms: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.event_type,
            "text": self.text,
            "latency_ms": self.latency_ms
        }


@dataclass
class VoiceStatus:
    """Current voice pipeline status"""
    running: bool = False
    connected: bool = False
    last_transcript: Optional[str] = None
    last_rasta: Optional[str] = None
    last_activity: Optional[datetime] = None
    avg_latency_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "running": self.running,
            "connected": self.connected,
            "last_transcript": self.last_transcript,
            "last_rasta": self.last_rasta,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "error": self.error
        }


class VoicePipelineManager:
    """
    Manages the Rasta Voice Pipeline subprocess.

    Usage:
        manager = VoicePipelineManager()
        await manager.start()
        status = manager.get_status()
        events = manager.get_recent_events()
        await manager.stop()
    """

    def __init__(self, script_path: Optional[str] = None):
        # Find the rasta pipeline script
        if script_path:
            self.script_path = Path(script_path)
        else:
            # Look in common locations
            base = Path(__file__).parent.parent.parent
            candidates = [
                base / "rasta-voice" / "rasta_pipeline_eleven.py",
                base / "rasta-voice" / "rasta_live.py",
            ]
            self.script_path = None
            for candidate in candidates:
                if candidate.exists():
                    self.script_path = candidate
                    break

        self.process: Optional[subprocess.Popen] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.status = VoiceStatus()
        self.events: deque[VoiceEvent] = deque(maxlen=100)  # Keep last 100 events
        self.latencies: deque[float] = deque(maxlen=50)  # For averaging
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[VoiceEvent], None]] = []

    def add_callback(self, callback: Callable[[VoiceEvent], None]):
        """Add a callback to be called when new events occur"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[VoiceEvent], None]):
        """Remove a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, event: VoiceEvent):
        """Notify all callbacks of a new event"""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Voice callback error: {e}")

    def _parse_output_line(self, line: str) -> Optional[VoiceEvent]:
        """Parse a line of output from the voice pipeline"""
        now = datetime.utcnow()

        # Match transcript line: 📝 You: "text"
        transcript_match = re.match(r'📝\s*You:\s*"(.+)"', line)
        if transcript_match:
            text = transcript_match.group(1)
            self.status.last_transcript = text
            self.status.last_activity = now
            return VoiceEvent(now, "transcript", text)

        # Match rasta output line: 🌿 Mon: "text" (123ms)
        rasta_match = re.match(r'🌿\s*Mon:\s*"(.+)"\s*\((\d+)ms\)', line)
        if rasta_match:
            text = rasta_match.group(1)
            latency = float(rasta_match.group(2))
            self.status.last_rasta = text
            self.status.last_activity = now
            self.latencies.append(latency)
            self.status.avg_latency_ms = sum(self.latencies) / len(self.latencies)
            return VoiceEvent(now, "rasta", text, latency)

        # Match total latency line:    ⏱️  Total: 1234ms
        total_match = re.match(r'\s*⏱️\s*Total:\s*(\d+)ms', line)
        if total_match:
            latency = float(total_match.group(1))
            return VoiceEvent(now, "latency", f"Total latency: {latency}ms", latency)

        # Match connection success: ✅ Connected to AssemblyAI
        if "Connected to AssemblyAI" in line:
            self.status.connected = True
            return VoiceEvent(now, "status", "Connected to AssemblyAI")

        # Match microphone active: 🎙️  Microphone active
        if "Microphone active" in line:
            return VoiceEvent(now, "status", "Microphone active - listening")

        # Match errors: ❌
        if "❌" in line:
            self.status.error = line
            return VoiceEvent(now, "error", line)

        # Match latency report: 📊 Latency - STT: ...
        latency_report_match = re.match(r'📊\s*Latency\s*-\s*(.+)', line)
        if latency_report_match:
            return VoiceEvent(now, "latency", latency_report_match.group(1))

        return None

    def _read_output(self):
        """Background thread to read subprocess output"""
        if not self.process or not self.process.stdout:
            return

        while not self._stop_event.is_set():
            try:
                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        # Process has ended
                        self.status.running = False
                        self.status.connected = False
                        break
                    continue

                line = line.decode('utf-8', errors='replace').strip()
                if line:
                    print(f"[Voice] {line}")  # Log to server console
                    event = self._parse_output_line(line)
                    if event:
                        self.events.append(event)
                        self._notify_callbacks(event)

            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"Voice reader error: {e}")
                break

        print("[Voice] Reader thread stopped")

    async def start(self) -> dict:
        """
        Start the voice pipeline.

        The Rasta voice pipeline only runs on Windows because it
        requires VB-Cable virtual audio, a physical microphone, and
        ElevenLabs real-time TTS.  On other platforms this returns
        a clear error instead of crashing.
        """
        if not IS_WINDOWS:
            msg = (
                "Voice pipeline requires Windows (VB-Cable, microphone, "
                "ElevenLabs). Current platform: " + platform.system()
            )
            logger.warning(msg)
            return {"success": False, "error": msg}

        if self.status.running:
            return {"success": False, "error": "Already running"}

        if not self.script_path or not self.script_path.exists():
            return {"success": False, "error": f"Voice script not found at {self.script_path}"}

        # Check for required environment variables
        missing = []
        if not os.environ.get("ASSEMBLYAI_API_KEY"):
            missing.append("ASSEMBLYAI_API_KEY")
        if not os.environ.get("GROQ_API_KEY"):
            missing.append("GROQ_API_KEY")
        if not os.environ.get("ELEVENLABS_API_KEY"):
            missing.append("ELEVENLABS_API_KEY")

        if missing:
            return {"success": False, "error": f"Missing API keys: {', '.join(missing)}"}

        try:
            # Resolve Python interpreter: prefer venv, handle Windows paths
            base = Path(__file__).parent.parent.parent
            venv_candidates = [
                base / "venv" / "Scripts" / "python.exe",   # Windows venv
                base / "venv" / "bin" / "python",            # Linux/WSL venv
            ]
            python_cmd = sys.executable  # fallback to current interpreter
            for candidate in venv_candidates:
                if candidate.exists():
                    python_cmd = str(candidate)
                    break

            self.process = subprocess.Popen(
                [python_cmd, str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                cwd=str(self.script_path.parent),
                env={**os.environ}  # Pass through all env vars
            )

            self.status.running = True
            self.status.error = None
            self._stop_event.clear()

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

            logger.info(f"Voice pipeline started (PID {self.process.pid})")

            # Wait a moment for connection
            await asyncio.sleep(2)

            return {
                "success": True,
                "message": "Voice pipeline started",
                "pid": self.process.pid
            }

        except Exception as e:
            self.status.running = False
            self.status.error = str(e)
            logger.error(f"Voice pipeline start failed: {e}")
            return {"success": False, "error": str(e)}

    async def stop(self) -> dict:
        """
        Stop the voice pipeline gracefully.

        Sends SIGTERM first and waits up to 5 seconds.  If the process
        does not exit, it is killed with SIGKILL.
        """
        if not self.status.running:
            return {"success": False, "error": "Not running"}

        try:
            self._stop_event.set()

            if self.process:
                pid = self.process.pid
                logger.info(f"Terminating voice pipeline (PID {pid})")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Voice pipeline PID {pid} did not exit, killing")
                    self.process.kill()
                    self.process.wait()
                self.process = None

            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=2)

            self.status.running = False
            self.status.connected = False

            logger.info("Voice pipeline stopped")
            return {"success": True, "message": "Voice pipeline stopped"}

        except Exception as e:
            logger.error(f"Voice pipeline stop failed: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        """
        Get current pipeline status.

        Includes a ``platform_ok`` flag indicating whether the current
        platform can run the voice pipeline.
        """
        # Check if process is still running
        if self.process and self.process.poll() is not None:
            self.status.running = False
            self.status.connected = False
            exit_code = self.process.returncode
            if exit_code and exit_code != 0:
                self.status.error = f"Process exited with code {exit_code}"

        result = self.status.to_dict()
        result["platform_ok"] = IS_WINDOWS
        result["script_found"] = self.script_path is not None and self.script_path.exists()
        return result

    def get_recent_events(self, limit: int = 20) -> List[dict]:
        """Get recent voice events"""
        events = list(self.events)[-limit:]
        return [e.to_dict() for e in events]

    def clear_events(self):
        """Clear event history"""
        self.events.clear()


# Singleton instance
_manager: Optional[VoicePipelineManager] = None


def get_voice_manager() -> VoicePipelineManager:
    """Get or create the voice pipeline manager singleton"""
    global _manager
    if _manager is None:
        _manager = VoicePipelineManager()
    return _manager
