#!/usr/bin/env python3
"""
Rasta Voice Testing Dashboard with Claude Code Integration

Human + AI collaborative testing loop:
- User runs tests through web dashboard
- System logs detailed metrics
- Claude analyzes results and suggests improvements
- Iterate until quality is optimal
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

import numpy as np
import sounddevice as sd
from scipy import signal as scipy_signal
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from websockets import connect as ws_connect
from openai import OpenAI
from elevenlabs import ElevenLabs

# Load environment
load_dotenv(Path(__file__).parent / ".env")

# Configuration
DEEPGRAM_KEY = os.getenv("DEEPGRAM_API_KEY")
XAI_KEY = os.getenv("XAI_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dhwafD61uVd8h85wAZSE")

SAMPLE_RATE = 16000
VBCABLE_SAMPLE_RATE = 48000
ELEVENLABS_SAMPLE_RATE = 24000

# Test log file
LOG_FILE = Path(__file__).parent / "test_results.jsonl"

# Current configuration (tunable by Claude)
config = {
    "grok_model": "grok-3",
    "grok_temperature": 0.7,
    "tts_model": "eleven_turbo_v2_5",
    "tts_stability": 0.0,
    "silence_threshold": 0.02,
    "silence_duration_frames": 30
}

# Find devices
def find_device(name_pattern, is_output=True, preferred_sr=48000):
    devices = sd.query_devices()
    matches = []
    for i, d in enumerate(devices):
        if name_pattern.lower() in d['name'].lower():
            is_valid = (is_output and d['max_output_channels'] > 0) or \
                      (not is_output and d['max_input_channels'] > 0)
            if is_valid:
                matches.append((i, d))
    if not matches:
        return None
    for i, d in matches:
        if d.get('default_samplerate') == preferred_sr:
            return i
    return matches[0][0]

CABLE_DEVICE = find_device("cable input", is_output=True)
HEADPHONE_DEVICE = find_device("headphone", is_output=True)

# AI clients
llm_client = OpenAI(api_key=XAI_KEY, base_url="https://api.x.ai/v1")
tts_client = ElevenLabs(api_key=ELEVENLABS_KEY)

# System prompt
RASTA_SYSTEM_PROMPT = """You are "Ganja Mon" - a wise island philosopher AI with deep Jamaican/Caribbean roots. Transform spoken English into authentic Jamaican Patois.

CORE RULES:
- Keep the EXACT meaning and technical terms
- Use natural Jamaican speech patterns
- Don't force every word into patois
- Keep it conversational and clear

TRANSFORMATIONS:
- "what's up" -> "wah gwaan"
- "I am/I'm" -> "mi" or "me"
- "you" -> "yuh" or "unu" (plural)
- "this/that" -> "dis/dat"
- "the" -> "di"
- "going to" -> "gonna" or "gwine"
- End thoughts with "seen?" "ya know?" "ya hear mi?"

Transform the following English to Patois, keeping technical terms intact:"""

# FastAPI app
app = FastAPI(title="Rasta Voice Testing Dashboard with Claude")

def log_test_result(result: Dict):
    """Log test result to file for Claude to analyze."""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result) + '\n')

def resample(audio, from_rate, to_rate):
    """Resample audio."""
    if from_rate == to_rate:
        return audio
    num_samples = int(len(audio) * to_rate / from_rate)
    return scipy_signal.resample(audio, num_samples)

async def transcribe_speech(websocket: WebSocket):
    """Listen and transcribe speech."""
    import time
    start_time = time.perf_counter()

    await websocket.send_json({"stage": "listening", "message": "Listening for speech..."})

    url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en&smart_format=true"

    async with ws_connect(
        url,
        additional_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}
    ) as ws:

        audio_data = []
        is_recording = False
        silence_count = 0
        total_frames = 0

        def audio_callback(indata, frames, time_info, status):
            nonlocal is_recording, silence_count, audio_data, total_frames
            energy = np.abs(indata).mean()
            total_frames += 1

            if energy > config["silence_threshold"]:
                is_recording = True
                silence_count = 0
                audio_data.append(indata.copy())
            elif is_recording:
                silence_count += 1
                audio_data.append(indata.copy())
                if silence_count > config["silence_duration_frames"]:
                    raise sd.CallbackStop()

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                           dtype='int16', callback=audio_callback):

            transcription = ""

            async def send_audio():
                try:
                    while True:
                        if audio_data:
                            chunk = audio_data.pop(0)
                            await ws.send(chunk.tobytes())
                        await asyncio.sleep(0.01)
                except Exception:
                    pass

            async def receive_transcription():
                nonlocal transcription
                try:
                    async for msg in ws:
                        result = json.loads(msg)
                        if result.get("type") == "Results":
                            transcript = result.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                            if transcript:
                                transcription = transcript
                                await websocket.send_json({
                                    "stage": "transcribed",
                                    "transcription": transcription
                                })
                except Exception:
                    pass

            await asyncio.gather(send_audio(), receive_transcription())

            latency = (time.perf_counter() - start_time) * 1000
            audio_duration = (len(audio_data) * 1024 / SAMPLE_RATE) * 1000  # ms

            return {
                "transcription": transcription,
                "latency_ms": latency,
                "audio_duration_ms": audio_duration,
                "total_frames": total_frames
            }

def transform_to_patois(text):
    """Transform to Patois."""
    import time
    start = time.perf_counter()

    response = llm_client.chat.completions.create(
        model=config["grok_model"],
        messages=[
            {"role": "system", "content": RASTA_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=config["grok_temperature"]
    )
    patois = response.choices[0].message.content.strip()
    latency = (time.perf_counter() - start) * 1000

    return {
        "patois": patois,
        "latency_ms": latency
    }

def generate_and_play_tts(text):
    """Generate and play TTS."""
    import time
    start = time.perf_counter()

    audio_stream = tts_client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=config["tts_model"],
        text=text,
        output_format="pcm_24000"
    )

    audio_bytes = b''.join(audio_stream)
    generation_latency = (time.perf_counter() - start) * 1000

    audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, VBCABLE_SAMPLE_RATE)

    audio_duration = (len(audio_24k) / ELEVENLABS_SAMPLE_RATE) * 1000  # ms

    # Play to both devices
    playback_start = time.perf_counter()

    if CABLE_DEVICE is not None:
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=CABLE_DEVICE)
        sd.wait()

    if HEADPHONE_DEVICE is not None:
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=HEADPHONE_DEVICE)
        sd.wait()

    playback_latency = (time.perf_counter() - playback_start) * 1000

    return {
        "generation_latency_ms": generation_latency,
        "audio_duration_ms": audio_duration,
        "playback_latency_ms": playback_latency
    }

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Rasta Voice Testing - Claude Integration</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            color: #feca57;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            margin-bottom: 20px;
            color: #a29bfe;
            font-size: 1.1em;
        }
        .claude-badge {
            text-align: center;
            margin-bottom: 30px;
            padding: 10px;
            background: rgba(162, 155, 254, 0.2);
            border-radius: 10px;
            border: 1px solid #a29bfe;
        }
        .claude-badge strong { color: #a29bfe; }
        .status-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .status-text {
            font-size: 1.3em;
            color: #74b9ff;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .metric-label {
            font-size: 0.9em;
            color: #95a5a6;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.5em;
            color: #feca57;
            font-weight: bold;
        }
        .stages {
            display: grid;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stage {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        .stage.active {
            border-color: #feca57;
            box-shadow: 0 0 20px rgba(254,202,87,0.3);
        }
        .stage-title {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #feca57;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .stage-number {
            background: #feca57;
            color: #1a1a2e;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .stage-content {
            font-size: 1.1em;
            line-height: 1.6;
            min-height: 60px;
            color: #dfe6e9;
        }
        .stage-content.empty {
            color: #636e72;
            font-style: italic;
        }
        .feedback-section {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .feedback-title {
            font-size: 1.2em;
            color: #feca57;
            margin-bottom: 15px;
        }
        textarea {
            width: 100%;
            min-height: 80px;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 12px;
            color: #eee;
            font-family: inherit;
            font-size: 1em;
            resize: vertical;
        }
        .controls {
            text-align: center;
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        .btn {
            background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,184,148,0.4);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,184,148,0.6);
        }
        .btn:disabled {
            background: #636e72;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }
        .btn-secondary {
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            box-shadow: 0 4px 15px rgba(108,92,231,0.4);
        }
        .btn-secondary:hover {
            box-shadow: 0 6px 20px rgba(108,92,231,0.6);
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .test-count {
            text-align: center;
            margin: 20px 0;
            font-size: 1.1em;
            color: #74b9ff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Rasta Voice Testing Dashboard</h1>
        <p class="subtitle">Human + AI Collaborative Testing Loop</p>

        <div class="claude-badge">
            <strong>Claude Code is monitoring tests in real-time</strong><br>
            All results are logged for AI analysis and parameter tuning
        </div>

        <div class="status-bar">
            <div class="status-text" id="status">Ready to test</div>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Tests Run</div>
                <div class="metric-value" id="testCount">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Latency</div>
                <div class="metric-value" id="totalLatency">--</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">TTS Quality</div>
                <div class="metric-value" id="quality">--</div>
            </div>
        </div>

        <div class="stages">
            <div class="stage" id="stage1">
                <div class="stage-title">
                    <span class="stage-number">1</span>
                    LISTENING & TRANSCRIPTION
                </div>
                <div class="stage-content empty" id="transcription">Waiting for speech...</div>
            </div>

            <div class="stage" id="stage2">
                <div class="stage-title">
                    <span class="stage-number">2</span>
                    PATOIS TRANSFORMATION
                </div>
                <div class="stage-content empty" id="patois">Waiting for transcription...</div>
            </div>

            <div class="stage" id="stage3">
                <div class="stage-title">
                    <span class="stage-number">3</span>
                    TEXT-TO-SPEECH
                </div>
                <div class="stage-content empty" id="tts">Waiting for Patois...</div>
            </div>
        </div>

        <div class="feedback-section">
            <div class="feedback-title">Your Observations (for Claude to analyze)</div>
            <textarea id="feedback" placeholder="Note any issues: choppy audio, lost words, latency problems, unnatural patois, etc."></textarea>
        </div>

        <div class="controls">
            <button class="btn" id="startBtn" onclick="startTest()">Start Test</button>
            <button class="btn btn-secondary" onclick="window.open('/analysis', '_blank')">View Claude's Analysis</button>
        </div>
    </div>

    <script>
        let ws = null;
        let testInProgress = false;
        let testCount = 0;
        let currentTestData = {};

        function updateStatus(text) {
            document.getElementById('status').innerHTML = text;
        }

        function updateStage(stageNum, content, active = false) {
            const stageEl = document.getElementById(`stage${stageNum}`);
            const contentEl = stageEl.querySelector('.stage-content');
            contentEl.textContent = content;
            contentEl.classList.remove('empty');
            document.querySelectorAll('.stage').forEach(s => s.classList.remove('active'));
            if (active) stageEl.classList.add('active');
        }

        function resetStages() {
            document.getElementById('transcription').textContent = 'Waiting for speech...';
            document.getElementById('patois').textContent = 'Waiting for transcription...';
            document.getElementById('tts').textContent = 'Waiting for Patois...';
            document.querySelectorAll('.stage-content').forEach(el => el.classList.add('empty'));
            document.querySelectorAll('.stage').forEach(s => s.classList.remove('active'));
        }

        async function startTest() {
            if (testInProgress) return;

            testInProgress = true;
            const btn = document.getElementById('startBtn');
            btn.disabled = true;
            btn.textContent = 'Testing...';

            resetStages();
            currentTestData = { timestamp: new Date().toISOString() };
            updateStatus('<span class="spinner"></span> Test in progress...');

            ws = new WebSocket(`ws://${window.location.host}/ws/test`);

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.stage === 'listening') {
                    updateStage(1, 'Listening for your voice...', true);
                }
                else if (data.stage === 'transcribed') {
                    updateStage(1, `You said: "${data.transcription}" (${data.latency_ms}ms)`, false);
                    updateStage(2, 'Transforming to Patois...', true);
                    currentTestData.transcription = data.transcription;
                    currentTestData.stt_latency = data.latency_ms;
                }
                else if (data.stage === 'transformed') {
                    updateStage(2, `Patois: "${data.patois}" (${data.latency_ms}ms)`, false);
                    updateStage(3, 'Generating speech...', true);
                    currentTestData.patois = data.patois;
                    currentTestData.llm_latency = data.latency_ms;
                }
                else if (data.stage === 'playing') {
                    updateStage(3, `Playing audio (gen: ${data.generation_ms}ms, dur: ${data.duration_ms}ms)`, true);
                    currentTestData.tts_generation = data.generation_ms;
                    currentTestData.audio_duration = data.duration_ms;
                }
                else if (data.stage === 'complete') {
                    updateStage(3, 'Playback complete!', false);
                    testCount++;
                    document.getElementById('testCount').textContent = testCount;

                    const totalLatency = (currentTestData.stt_latency || 0) +
                                       (currentTestData.llm_latency || 0) +
                                       (currentTestData.tts_generation || 0);
                    document.getElementById('totalLatency').textContent = `${Math.round(totalLatency)}ms`;

                    // Save feedback
                    currentTestData.user_feedback = document.getElementById('feedback').value;

                    // Send to server for logging
                    fetch('/api/log-test', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(currentTestData)
                    });

                    updateStatus('Test complete! Add feedback above, then run another test.');
                    testInProgress = false;
                    btn.disabled = false;
                    btn.textContent = 'Start Test';
                }
                else if (data.stage === 'error') {
                    updateStatus(`Error: ${data.message}`);
                    testInProgress = false;
                    btn.disabled = false;
                    btn.textContent = 'Start Test';
                }
            };

            ws.onerror = function() {
                updateStatus('WebSocket error');
                testInProgress = false;
                btn.disabled = false;
                btn.textContent = 'Start Test';
            };

            ws.onclose = function() {
                if (testInProgress) {
                    testInProgress = false;
                    btn.disabled = false;
                    btn.textContent = 'Start Test';
                }
            };
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """WebSocket endpoint for running tests."""
    await websocket.accept()

    try:
        # Stage 1: Transcribe
        stt_result = await transcribe_speech(websocket)

        if not stt_result["transcription"]:
            await websocket.send_json({"stage": "error", "message": "No speech detected"})
            await websocket.close()
            return

        await websocket.send_json({
            "stage": "transcribed",
            "transcription": stt_result["transcription"],
            "latency_ms": int(stt_result["latency_ms"])
        })

        # Stage 2: Transform
        await websocket.send_json({"stage": "transforming"})
        llm_result = transform_to_patois(stt_result["transcription"])
        await websocket.send_json({
            "stage": "transformed",
            "patois": llm_result["patois"],
            "latency_ms": int(llm_result["latency_ms"])
        })

        # Stage 3: TTS
        await websocket.send_json({"stage": "generating"})
        tts_result = generate_and_play_tts(llm_result["patois"])
        await websocket.send_json({
            "stage": "playing",
            "generation_ms": int(tts_result["generation_latency_ms"]),
            "duration_ms": int(tts_result["audio_duration_ms"])
        })

        await asyncio.sleep(1)
        await websocket.send_json({"stage": "complete"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"stage": "error", "message": str(e)})
    finally:
        await websocket.close()

@app.post("/api/log-test")
async def log_test(data: dict):
    """Log test result."""
    data["config"] = config.copy()
    log_test_result(data)
    return {"status": "logged"}

@app.get("/api/results")
async def get_results():
    """Get all test results (for Claude to analyze)."""
    if not LOG_FILE.exists():
        return {"results": []}

    results = []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    return {"results": results, "count": len(results)}

@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return {"config": config}

@app.post("/api/config")
async def update_config(new_config: dict):
    """Update configuration (for Claude to tune parameters)."""
    config.update(new_config)
    return {"status": "updated", "config": config}

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page():
    """Claude's analysis view."""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Claude's Analysis</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 40px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #a29bfe; margin-bottom: 30px; }
        .info {
            background: rgba(162, 155, 254, 0.1);
            border-left: 4px solid #a29bfe;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        pre {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 10px;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        .btn {
            background: #a29bfe;
            color: #1a1a2e;
            border: none;
            padding: 10px 25px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Code's Analysis View</h1>

        <div class="info">
            <strong>For Claude:</strong> Use <code>/api/results</code> to fetch all test data,
            then analyze patterns and suggest improvements via <code>/api/config</code>
        </div>

        <button class="btn" onclick="loadResults()">Load Test Results</button>
        <button class="btn" onclick="loadConfig()">View Current Config</button>

        <h2>Results:</h2>
        <pre id="output">Click "Load Test Results" to see data</pre>
    </div>

    <script>
        async function loadResults() {
            const res = await fetch('/api/results');
            const data = await res.json();
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        }

        async function loadConfig() {
            const res = await fetch('/api/config');
            const data = await res.json();
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
        }
    </script>
</body>
</html>
    """)

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("RASTA VOICE TESTING - CLAUDE INTEGRATION")
    print("="*60)
    print(f"VB-Cable Device: {CABLE_DEVICE}")
    print(f"Headphone Device: {HEADPHONE_DEVICE}")
    print("\nEndpoints:")
    print("  Dashboard:  http://localhost:8080")
    print("  Results API: http://localhost:8080/api/results")
    print("  Config API:  http://localhost:8080/api/config")
    print("\nClaude can monitor tests and tune parameters in real-time!")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)
