#!/usr/bin/env python3
"""
Standalone Voice Dashboard Server
=================================

Lightweight server for controlling the Rasta voice pipeline.
Run with: python voice_server.py
Access at: http://localhost:8000/voice
"""

import asyncio
import os
import re
import subprocess
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Callable

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# ============================================================================
# Voice Pipeline Manager (inline from src/voice/manager.py)
# ============================================================================

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
    """Manages the Rasta Voice Pipeline subprocess."""

    def __init__(self, script_path: Optional[str] = None):
        # Find the rasta pipeline script
        if script_path:
            self.script_path = Path(script_path)
        else:
            # Look in common locations
            base = Path(__file__).parent
            candidates = [
                base / "rasta-voice" / "rasta_live.py",  # Production: Deepgram + xAI + ElevenLabs
            ]
            self.script_path = None
            for candidate in candidates:
                if candidate.exists():
                    self.script_path = candidate
                    break

        self.process: Optional[subprocess.Popen] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.status = VoiceStatus()
        self.events: deque[VoiceEvent] = deque(maxlen=100)
        self.latencies: deque[float] = deque(maxlen=50)
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[VoiceEvent], None]] = []

    def add_callback(self, callback: Callable[[VoiceEvent], None]):
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[VoiceEvent], None]):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, event: VoiceEvent):
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Voice callback error: {e}")

    def _parse_output_line(self, line: str) -> Optional[VoiceEvent]:
        """Parse a line of output from the voice pipeline (supports both rasta_live.py and rasta_pipeline_eleven.py)"""
        now = datetime.utcnow()

        # Match transcript line (rasta_live.py format: 'Input: "text"')
        transcript_match = re.match(r'.*Input:\s*"(.+)"', line)
        if transcript_match:
            text = transcript_match.group(1)
            self.status.last_transcript = text
            self.status.last_activity = now
            return VoiceEvent(now, "transcript", text)

        # Match transcript line (old format: '📝 You: "text"')
        transcript_match2 = re.match(r'📝\s*You:\s*"(.+)"', line)
        if transcript_match2:
            text = transcript_match2.group(1)
            self.status.last_transcript = text
            self.status.last_activity = now
            return VoiceEvent(now, "transcript", text)

        # Match rasta output line (rasta_live.py format: 'Rasta: "text" (123ms)')
        rasta_match = re.match(r'.*Rasta:\s*"(.+)"\s*\((\d+)ms\)', line)
        if rasta_match:
            text = rasta_match.group(1)
            latency = float(rasta_match.group(2))
            self.status.last_rasta = text
            self.status.last_activity = now
            self.latencies.append(latency)
            self.status.avg_latency_ms = sum(self.latencies) / len(self.latencies)
            return VoiceEvent(now, "rasta", text, latency)

        # Match rasta output line (old format: '🌿 Mon: "text" (123ms)')
        rasta_match2 = re.match(r'🌿\s*Mon:\s*"(.+)"\s*\((\d+)ms\)', line)
        if rasta_match2:
            text = rasta_match2.group(1)
            latency = float(rasta_match2.group(2))
            self.status.last_rasta = text
            self.status.last_activity = now
            self.latencies.append(latency)
            self.status.avg_latency_ms = sum(self.latencies) / len(self.latencies)
            return VoiceEvent(now, "rasta", text, latency)

        # Match total latency line (rasta_live.py format: 'Total: 123ms')
        total_match = re.match(r'.*Total:\s*(\d+)ms', line)
        if total_match:
            latency = float(total_match.group(1))
            return VoiceEvent(now, "latency", f"Total latency: {latency}ms", latency)

        # Match connection success (Deepgram or AssemblyAI)
        if "Connected to Deepgram" in line or "Connected to AssemblyAI" in line:
            self.status.connected = True
            return VoiceEvent(now, "status", "Connected to STT service")

        # Match microphone active
        if "Microphone active" in line:
            return VoiceEvent(now, "status", "Microphone active - listening")

        # Match errors (both formats)
        if "❌" in line or "[ERROR]" in line or "error" in line.lower():
            self.status.error = line
            return VoiceEvent(now, "error", line)

        # Match latency report (rasta_live.py format: 'Latency (ms) - STT:...')
        latency_report_match = re.match(r'.*Latency\s*\(ms\)\s*-\s*(.+)', line)
        if latency_report_match:
            return VoiceEvent(now, "latency", latency_report_match.group(1))

        # Match old latency report format
        latency_report_match2 = re.match(r'📊\s*Latency\s*-\s*(.+)', line)
        if latency_report_match2:
            return VoiceEvent(now, "latency", latency_report_match2.group(1))

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
                        self.status.running = False
                        self.status.connected = False
                        break
                    continue

                line = line.decode('utf-8', errors='replace').strip()
                if line:
                    print(f"[Voice] {line}")
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
        """Start the voice pipeline"""
        if self.status.running:
            return {"success": False, "error": "Already running"}

        if not self.script_path or not self.script_path.exists():
            return {"success": False, "error": f"Voice script not found at {self.script_path}"}

        # Check for required environment variables (for rasta_live.py)
        missing = []
        if not os.environ.get("DEEPGRAM_API_KEY"):
            missing.append("DEEPGRAM_API_KEY")
        if not os.environ.get("XAI_API_KEY"):
            missing.append("XAI_API_KEY")
        if not os.environ.get("ELEVENLABS_API_KEY"):
            missing.append("ELEVENLABS_API_KEY")

        if missing:
            return {"success": False, "error": f"Missing API keys: {', '.join(missing)}"}

        try:
            # Use rasta-voice venv (check both Linux and Windows paths)
            base = Path(__file__).parent
            venv_linux = base / "rasta-voice" / "venv" / "bin" / "python"
            venv_windows = base / "rasta-voice" / "venv" / "Scripts" / "python.exe"

            script_path_str = str(self.script_path)

            if venv_linux.exists():
                python_cmd = str(venv_linux)
            elif venv_windows.exists():
                python_cmd = str(venv_windows)
                # Convert WSL path to Windows path for Windows python.exe
                if script_path_str.startswith('/mnt/'):
                    # /mnt/c/... -> C:\...
                    drive = script_path_str[5].upper()
                    script_path_str = drive + ":" + script_path_str[6:].replace('/', '\\')
            else:
                python_cmd = "python3"

            # Set UTF-8 encoding for Windows subprocess (handles emojis)
            env = {
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",  # Force UTF-8 mode (Python 3.7+)
            }

            # Build command with -X utf8 flag for Windows to handle emojis
            cmd = [python_cmd]
            if venv_windows.exists():
                cmd.extend(["-X", "utf8"])  # Force UTF-8 mode on Windows
            cmd.append(script_path_str)

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                cwd=str(self.script_path.parent),
                env=env
            )

            self.status.running = True
            self.status.error = None
            self._stop_event.clear()

            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

            await asyncio.sleep(2)

            return {
                "success": True,
                "message": "Voice pipeline started",
                "pid": self.process.pid
            }

        except Exception as e:
            self.status.running = False
            self.status.error = str(e)
            return {"success": False, "error": str(e)}

    async def stop(self) -> dict:
        """Stop the voice pipeline"""
        if not self.status.running:
            return {"success": False, "error": "Not running"}

        try:
            self._stop_event.set()

            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.process = None

            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=2)

            self.status.running = False
            self.status.connected = False

            return {"success": True, "message": "Voice pipeline stopped"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        """Get current pipeline status"""
        if self.process and self.process.poll() is not None:
            self.status.running = False
            self.status.connected = False

        return self.status.to_dict()

    def get_recent_events(self, limit: int = 20) -> List[dict]:
        """Get recent voice events"""
        events = list(self.events)[-limit:]
        return [e.to_dict() for e in events]

    def clear_events(self):
        """Clear event history"""
        self.events.clear()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="Voice Dashboard", description="Control the Rasta Voice Pipeline")
voice_manager = VoicePipelineManager()

# Load .env files - check rasta-voice/.env first (has voice API keys)
def load_env_file(path: Path):
    if path.exists():
        print(f"Loading environment from {path}")
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

base = Path(__file__).parent
load_env_file(base / "rasta-voice" / ".env")  # Voice API keys
load_env_file(base / ".env")  # Main project env


def check_localhost(request: Request):
    """Verify request is from localhost"""
    client_host = request.client.host if request.client else None
    if client_host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="Voice API is localhost only")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Voice Dashboard</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>Voice Dashboard Server</h1>
            <p>Go to <a href="/voice">/voice</a> for the dashboard.</p>
        </body>
    </html>
    """


@app.get("/voice")
async def serve_voice_dashboard(request: Request):
    """Serve the voice control dashboard"""
    check_localhost(request)
    voice_html = Path(__file__).parent / "src" / "web" / "voice.html"
    if voice_html.exists():
        return FileResponse(voice_html, media_type="text/html")
    raise HTTPException(status_code=404, detail="Voice dashboard not found")


@app.get("/api/voice/status")
async def get_voice_status(request: Request):
    """Get current voice pipeline status"""
    check_localhost(request)
    return voice_manager.get_status()


@app.post("/api/voice/start")
async def start_voice_pipeline(request: Request):
    """Start the voice pipeline"""
    check_localhost(request)
    return await voice_manager.start()


@app.post("/api/voice/stop")
async def stop_voice_pipeline(request: Request):
    """Stop the voice pipeline"""
    check_localhost(request)
    return await voice_manager.stop()


@app.get("/api/voice/events")
async def get_voice_events(request: Request, limit: int = Query(default=20, ge=1, le=100)):
    """Get recent voice events"""
    check_localhost(request)
    return voice_manager.get_recent_events(limit)


if __name__ == "__main__":
    print("=" * 50)
    print("Voice Dashboard Server")
    print("=" * 50)
    print(f"Voice script: {voice_manager.script_path}")
    print(f"Dashboard: http://localhost:8000/voice")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)
