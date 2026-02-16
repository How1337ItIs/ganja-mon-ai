#!/usr/bin/env python3
"""Working Rasta Voice Dashboard - FastAPI version.

Extended:
- Adds text-to-text translator endpoint (`/api/translate`)
- Implements endpoints referenced by `dashboard.html` (`/api/clear`, `/api/config`, `/api/nuke`)
- Uses `pipeline.pid` for start/stop/status (compatible with start_pipeline.py)
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")
PID_FILE = ROOT_DIR / "pipeline.pid"
TRANSCRIPTS_FILE = ROOT_DIR / "live_transcripts.jsonl"
VOICE_CONFIG_FILE = ROOT_DIR / "voice_config.json"

_XAI_CLIENT = None


def _read_pid() -> Optional[int]:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def _pid_running(pid: int) -> bool:
    """
    Windows-friendly process check without extra dependencies.
    """
    try:
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
            check=False,
        )
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        return str(pid) in out
    except Exception:
        return False


def _kill_pid(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/F", "/PID", str(pid), "/T"],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        check=False,
    )


def _kill_pipeline_from_pidfile() -> bool:
    pid = _read_pid()
    if pid is None:
        return False
    _kill_pid(pid)
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    return True


def _get_xai_client():
    """
    Lazy-init xAI client. Returns None if XAI_API_KEY isn't configured.
    """
    global _XAI_CLIENT
    if _XAI_CLIENT is not None:
        return _XAI_CLIENT

    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        return None

    from rasta_text_translate import build_client  # type: ignore

    _XAI_CLIENT = build_client(api_key)
    return _XAI_CLIENT


class TranslateRequest(BaseModel):
    text: str
    model: str = os.getenv("XAI_TEXT_MODEL", "grok-3")
    temperature: float = 0.7
    context: str = ""


class VoiceConfigRequest(BaseModel):
    stability: float = 0.0
    style: float = 0.8
    temperature: float = 0.7

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve dashboard"""
    html_file = ROOT_DIR / "dashboard.html"
    if html_file.exists():
        return FileResponse(html_file)
    return "<h1>Dashboard HTML not found</h1>"


@app.post("/api/translate")
async def translate(req: TranslateRequest):
    """
    Text-to-text translator endpoint (no emotion tags).
    """
    client = _get_xai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="Missing XAI_API_KEY (set it in rasta-voice/.env).")

    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    from rasta_text_translate import translate_once  # type: ignore

    translated, latency_ms = translate_once(
        client,
        model=req.model,
        text=text,
        temperature=req.temperature,
        context=req.context or "",
    )
    return {"translated": translated, "latency_ms": latency_ms, "model": req.model}


@app.post("/api/start")
async def start_pipeline():
    """Start rasta voice pipeline using start_pipeline.py (prevents duplicates)"""
    venv_python = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    starter_script = ROOT_DIR / "start_pipeline.py"

    # start_pipeline.py automatically kills any existing process before starting
    subprocess.Popen([str(venv_python), str(starter_script)])

    return {"status": "started"}

@app.post("/api/stop")
async def stop_pipeline():
    """Stop rasta voice pipeline (kills PID from pipeline.pid)."""
    killed = _kill_pipeline_from_pidfile()
    return {"status": "stopped" if killed else "not_running"}

@app.get("/api/status")
async def get_status():
    """Get pipeline status"""
    pid = _read_pid()
    if pid is None:
        return {"running": False, "pid": None}
    return {"running": _pid_running(pid), "pid": pid}


@app.post("/api/nuke")
async def nuke():
    """
    Kill pipeline using the PID file.
    (Deliberately conservative; does NOT kill unrelated Python processes.)
    """
    killed = _kill_pipeline_from_pidfile()
    return {"status": "killed" if killed else "nothing_to_kill"}


@app.post("/api/clear")
async def clear_transcripts():
    """Clear transcript log file."""
    try:
        TRANSCRIPTS_FILE.write_text("", encoding="utf-8")
    except Exception:
        pass
    return {"status": "cleared"}


@app.post("/api/config")
async def save_config(req: VoiceConfigRequest):
    """
    Save voice config to voice_config.json.
    rasta_live.py reads this at runtime for LLM temperature + ElevenLabs settings.
    """
    # ElevenLabs only accepts 0.0, 0.5, or 1.0 for stability
    # Snap to nearest valid value
    valid_stabilities = [0.0, 0.5, 1.0]
    stability = min(valid_stabilities, key=lambda x: abs(x - req.stability))
    
    VOICE_CONFIG_FILE.write_text(
        (
            "{\n"
            f'  "stability": {stability:.1f},\n'
            f'  "style": {float(req.style):.3f},\n'
            f'  "temperature": {float(req.temperature):.3f}\n'
            "}\n"
        ),
        encoding="utf-8",
    )
    return {"status": "saved", "stability_used": stability}

@app.get("/api/transcripts")
async def get_transcripts():
    """Get transcript log"""
    import json
    transcripts = []
    if TRANSCRIPTS_FILE.exists():
        with open(TRANSCRIPTS_FILE, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    data = json.loads(line)
                    data['id'] = i
                    transcripts.append(data)
    return {"entries": transcripts}

@app.get("/api/devices")
async def list_devices():
    """List available audio input devices"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = []
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': d['name'],
                    'channels': d['max_input_channels'],
                    'samplerate': int(d['default_samplerate'])
                })
        return {"devices": input_devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restart")
async def restart_pipeline(device_id: int = 21, monitor_device: int = 29):
    """Restart pipeline with specified input and monitor devices"""
    try:
        # Kill existing pipeline
        _kill_pipeline_from_pidfile()

        # Start new pipeline with selected device
        venv_python = ROOT_DIR / "venv" / "Scripts" / "python.exe"
        pipeline_script = ROOT_DIR / "rasta_live.py"

        # Start pipeline with specified input device and monitor output
        proc = subprocess.Popen([
            str(venv_python),
            str(pipeline_script),
            "--input-device", str(device_id),
            "--twitter-device", "18",
            "--monitor-device", str(monitor_device)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # Save PID
        PID_FILE.write_text(str(proc.pid), encoding="utf-8")

        return {"status": "restarted", "pid": proc.pid, "input_device": device_id, "monitor_device": monitor_device}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting Rasta Voice Dashboard on http://localhost:8085")
    uvicorn.run(app, host="0.0.0.0", port=8085)
