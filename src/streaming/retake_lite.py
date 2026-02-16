#!/usr/bin/env python3
"""
Lightweight Retake.tv streaming for Chromebook.

Optimized for limited hardware while maintaining decent quality:
- 720p resolution (looks good, not too CPU heavy with ultrafast)
- 20 fps (smooth enough for plant cam)
- ultrafast preset (minimal encoding overhead)
- 1.5Mbps bitrate (decent quality for 720p)
- Simple text overlay (no heavy browser rendering)
- No TTS (that runs on Windows)

CPU target: ~60-70% on older Chromebook

For even lighter settings, override via env vars:
    STREAM_RESOLUTION=854x480 STREAM_FPS=15 STREAM_BITRATE=800k python retake_lite.py start

Usage:
    python retake_lite.py start
    python retake_lite.py stop
    python retake_lite.py status
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Lightweight HTTP client (no aiohttp needed)
import urllib.request
import urllib.error

# Config
RETAKE_API_BASE = os.getenv("RETAKE_API_BASE", "https://chat.retake.tv")
RETAKE_ACCESS_TOKEN = os.getenv("RETAKE_ACCESS_TOKEN", "")
RETAKE_USER_DB_ID = os.getenv("RETAKE_USER_DB_ID", "")

# Stream settings - Lightweight but decent quality
RESOLUTION = os.getenv("STREAM_RESOLUTION", "1280x720")  # 720p looks good
FPS = int(os.getenv("STREAM_FPS", "20"))  # 20fps is smooth for plant cam
BITRATE = os.getenv("STREAM_BITRATE", "1500k")  # 1.5Mbps for decent 720p
PRESET = "ultrafast"  # Fastest encoding, uses least CPU

# Webcam source (local to Chromebook)
WEBCAM_DEVICE = os.getenv("WEBCAM_DEVICE", "/dev/video0")
USE_HTTP_SOURCE = os.getenv("USE_HTTP_SOURCE", "false").lower() == "true"
HTTP_SOURCE_URL = "http://localhost:8000/api/webcam/stream"

# Status file for overlay
STATUS_FILE = Path("/tmp/ganjamon_status.txt")
PID_FILE = Path("/tmp/retake_lite.pid")
LOG_FILE = Path("/tmp/retake_lite.log")

# Stream overlay image (grokandmon.com + QR code)
OVERLAY_IMAGE = Path("/home/natha/projects/sol-cannabis/src/web/assets/stream_overlay.png")

# TTS Audio settings (requires PulseAudio with virtual sink)
USE_TTS_AUDIO = os.getenv("USE_TTS_AUDIO", "false").lower() == "true"
TTS_PULSE_SINK = os.getenv("TTS_PULSE_SINK", "tts_sink.monitor")


def _api_request(endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
    """Lightweight API request without aiohttp."""
    url = f"{RETAKE_API_BASE}{endpoint}"
    headers = {"Authorization": f"Bearer {RETAKE_ACCESS_TOKEN}"}

    try:
        if data:
            headers["Content-Type"] = "application/json"
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers=headers,
                method=method
            )
        else:
            req = urllib.request.Request(url, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                return json.loads(resp.read().decode())
    except Exception as e:
        print(f"API error: {e}")
    return None


def get_rtmp_creds() -> Optional[tuple]:
    """Get RTMP URL and key from Retake."""
    data = _api_request("/api/agent/rtmp")
    if not data:
        return None

    url = data.get("url") or data.get("rtmp_url")
    key = data.get("key") or data.get("stream_key")

    if url and key:
        return (url, key)
    return None


def start_retake_stream() -> bool:
    """Notify Retake we're starting."""
    return _api_request("/api/agent/stream/start", method="POST") is not None


def stop_retake_stream() -> bool:
    """Notify Retake we're stopping."""
    _api_request("/api/agent/stream/stop", method="POST")
    return True


def get_retake_status() -> dict:
    """Get stream status from Retake."""
    return _api_request("/api/agent/stream/status") or {}


def write_status_overlay():
    """Write simple status text for ffmpeg overlay."""
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")

    # Try to get sensor data (optional)
    sensor_text = ""
    try:
        with urllib.request.urlopen("http://localhost:8000/api/sensors", timeout=2) as resp:
            sensors = json.loads(resp.read().decode())
            temp = sensors.get("temperature", {}).get("value", "?")
            humidity = sensors.get("humidity", {}).get("value", "?")
            sensor_text = f"Temp: {temp}F | RH: {humidity}%"
    except:
        sensor_text = "Sensors: syncing..."

    status = f"""GANJAMON LIVE | {now}
{sensor_text}
Powered by Grok AI on Monad"""

    STATUS_FILE.write_text(status)


def build_ffmpeg_cmd(rtmp_url: str, stream_key: str) -> list:
    """Build ultra-lightweight ffmpeg command with branded overlay."""

    # Input source
    if USE_HTTP_SOURCE:
        input_args = [
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i", HTTP_SOURCE_URL,
        ]
    else:
        # Direct webcam capture (lighter than HTTP)
        input_args = [
            "-f", "v4l2",
            "-framerate", str(FPS),
            "-video_size", RESOLUTION,
            "-i", WEBCAM_DEVICE,
        ]

    # Build video filter with branded overlay
    # If overlay image exists, use it; otherwise fall back to text
    if OVERLAY_IMAGE.exists():
        # For filter_complex with overlay, use proper input labeling
        video_filter = (
            f"[0:v]scale={RESOLUTION}[scaled];"
            f"movie={OVERLAY_IMAGE}[overlay];"
            "[scaled][overlay]overlay=0:0[out]"
        )
        filter_complex = True
    else:
        # Fallback to text-only
        video_filter = (
            f"scale={RESOLUTION},"
            f"drawtext=textfile={STATUS_FILE}:reload=1:"
            "fontcolor=white:fontsize=16:x=10:y=10:"
            "borderw=1:bordercolor=black,"
            "drawtext=text='grokandmon.com':fontcolor=white:fontsize=28:"
            "x=w-tw-20:y=20:borderw=2:bordercolor=black"
        )
        filter_complex = False

    # Audio input args
    if USE_TTS_AUDIO:
        # Capture from PulseAudio TTS virtual sink
        audio_args = ["-f", "pulse", "-i", TTS_PULSE_SINK]
    else:
        # Silent audio (no mic needed)
        audio_args = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono"]

    # Full command
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",

        # Video input
        *input_args,

        # Audio input (TTS or silent)
        *audio_args,
    ]

    # Add filter (complex or simple)
    if filter_complex:
        cmd.extend(["-filter_complex", video_filter, "-map", "[out]", "-map", "1:a"])
    else:
        cmd.extend(["-vf", video_filter])

    cmd.extend([
        # Efficient encoding with decent quality
        "-c:v", "libx264",
        "-preset", PRESET,
        "-tune", "zerolatency",
        "-b:v", BITRATE,
        "-maxrate", BITRATE,
        "-bufsize", "3000k",  # 2x bitrate for buffer
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),  # Keyframe every 2 seconds

        # Audio (silent but proper format)
        "-c:a", "aac",
        "-b:a", "96k",  # Decent audio quality
        "-ar", "44100",
        "-ac", "2",  # Stereo for compatibility

        # Output
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        f"{rtmp_url}/{stream_key}",
    ])

    return cmd


def start_stream():
    """Start the lightweight stream."""
    print("Starting ultra-light Retake stream...")

    # Check if already running
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            print(f"Stream already running (PID {pid})")
            return False
        except OSError:
            PID_FILE.unlink()  # Stale PID file

    # Get RTMP credentials
    creds = get_rtmp_creds()
    if not creds:
        print("ERROR: Could not get RTMP credentials")
        return False

    rtmp_url, stream_key = creds
    print(f"RTMP: {rtmp_url} (key: {stream_key[:6]}...)")

    # Notify Retake
    start_retake_stream()

    # Write initial status
    write_status_overlay()

    # Build command
    cmd = build_ffmpeg_cmd(rtmp_url, stream_key)
    print(f"Command: {' '.join(cmd[:10])}...")

    # Start ffmpeg in background
    with open(LOG_FILE, "w") as log:
        proc = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    PID_FILE.write_text(str(proc.pid))
    print(f"Stream started (PID {proc.pid})")
    print(f"Log: {LOG_FILE}")

    # Start status updater in background
    subprocess.Popen(
        [sys.executable, __file__, "_update_status"],
        start_new_session=True,
    )

    return True


def stop_stream():
    """Stop the stream."""
    print("Stopping stream...")

    if PID_FILE.exists():
        pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Sent SIGTERM to PID {pid}")
        except OSError:
            pass
        PID_FILE.unlink(missing_ok=True)

    # Kill any stray ffmpeg processes
    subprocess.run(
        ["pkill", "-f", "ffmpeg.*flv"],
        capture_output=True,
    )

    # Notify Retake
    stop_retake_stream()

    print("Stream stopped")


def get_status():
    """Get stream status."""
    local_running = False
    local_pid = None

    if PID_FILE.exists():
        local_pid = int(PID_FILE.read_text().strip())
        try:
            os.kill(local_pid, 0)
            local_running = True
        except OSError:
            local_running = False

    retake_status = get_retake_status()

    status = {
        "local": {
            "running": local_running,
            "pid": local_pid,
            "resolution": RESOLUTION,
            "fps": FPS,
            "bitrate": BITRATE,
        },
        "retake": retake_status,
    }

    print(json.dumps(status, indent=2))
    return status


def update_status_loop():
    """Background loop to update status overlay."""
    while PID_FILE.exists():
        try:
            write_status_overlay()
        except:
            pass

        import time
        time.sleep(30)


def main():
    if len(sys.argv) < 2:
        print("""
Ultra-Light Retake Streamer for Chromebook

Usage:
    python retake_lite.py start   - Start streaming
    python retake_lite.py stop    - Stop streaming
    python retake_lite.py status  - Check status

Settings (via env vars):
    STREAM_RESOLUTION=640x480  (default, saves CPU)
    STREAM_FPS=15              (default, saves CPU)
    STREAM_BITRATE=600k        (default)
    USE_HTTP_SOURCE=false      (use /dev/video0 directly)
""")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "start":
        success = start_stream()
        sys.exit(0 if success else 1)
    elif cmd == "stop":
        stop_stream()
    elif cmd == "status":
        get_status()
    elif cmd == "_update_status":
        update_status_loop()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
