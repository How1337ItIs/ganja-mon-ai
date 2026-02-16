#!/usr/bin/env python3
"""
Rasta Voice Testing Dashboard

Web interface for human-in-the-loop voice pipeline testing.
Real-time display of transcription, Patois transformation, and TTS playback.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

import numpy as np
import sounddevice as sd
from scipy import signal as scipy_signal
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
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
app = FastAPI(title="Rasta Voice Testing Dashboard")

def resample(audio, from_rate, to_rate):
    """Resample audio."""
    if from_rate == to_rate:
        return audio
    num_samples = int(len(audio) * to_rate / from_rate)
    return scipy_signal.resample(audio, num_samples)

async def transcribe_speech(websocket: WebSocket):
    """Listen and transcribe speech, send updates to browser."""
    url = f"wss://api.deepgram.com/v1/listen?model=nova-2&language=en&smart_format=true"

    await websocket.send_json({"stage": "listening", "message": "Listening for speech..."})

    async with ws_connect(url, extra_headers={"Authorization": f"Token {DEEPGRAM_KEY}"}) as ws:

        audio_data = []
        is_recording = False
        silence_count = 0

        def audio_callback(indata, frames, time_info, status):
            nonlocal is_recording, silence_count, audio_data
            energy = np.abs(indata).mean()

            if energy > 0.02:  # Speech detected
                is_recording = True
                silence_count = 0
                audio_data.append(indata.copy())
            elif is_recording:
                silence_count += 1
                audio_data.append(indata.copy())
                if silence_count > 30:  # 1 sec silence
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

            return transcription

def transform_to_patois(text, websocket_sync):
    """Transform to Patois and send update."""
    response = llm_client.chat.completions.create(
        model="grok-2-1212",
        messages=[
            {"role": "system", "content": RASTA_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.7
    )
    patois = response.choices[0].message.content.strip()
    return patois

def generate_and_play_tts(text):
    """Generate and play TTS."""
    audio_stream = tts_client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        model_id="eleven_turbo_v2_5",
        text=text,
        output_format="pcm_24000"
    )

    audio_bytes = b''.join(audio_stream)
    audio_24k = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    audio_48k = resample(audio_24k, ELEVENLABS_SAMPLE_RATE, VBCABLE_SAMPLE_RATE)

    # Play to both devices
    if CABLE_DEVICE is not None:
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=CABLE_DEVICE)
        sd.wait()

    if HEADPHONE_DEVICE is not None:
        sd.play(audio_48k, samplerate=VBCABLE_SAMPLE_RATE, device=HEADPHONE_DEVICE)
        sd.wait()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the dashboard HTML."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Rasta Voice Testing Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #feca57;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            margin-bottom: 40px;
            color: #a29bfe;
            font-size: 1.1em;
        }
        .status-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .status-text {
            font-size: 1.3em;
            color: #74b9ff;
        }
        .stages {
            display: grid;
            gap: 20px;
            margin-bottom: 30px;
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
        .controls {
            text-align: center;
            margin-top: 30px;
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
        .test-info {
            background: rgba(116, 185, 255, 0.1);
            border-left: 4px solid #74b9ff;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Rasta Voice Testing Dashboard</h1>
        <p class="subtitle">Human-in-the-loop voice pipeline analysis</p>

        <div class="test-info">
            <strong>Instructions:</strong> Click "Start Test" and speak a phrase. The system will show each pipeline stage in real-time.
        </div>

        <div class="status-bar">
            <div class="status-text" id="status">Ready to test</div>
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

        <div class="controls">
            <button class="btn" id="startBtn" onclick="startTest()">Start Test</button>
        </div>
    </div>

    <script>
        let ws = null;
        let testInProgress = false;

        function updateStatus(text) {
            document.getElementById('status').innerHTML = text;
        }

        function updateStage(stageNum, content, active = false) {
            const stageEl = document.getElementById(`stage${stageNum}`);
            const contentEl = stageEl.querySelector('.stage-content');
            contentEl.textContent = content;
            contentEl.classList.remove('empty');

            // Remove active from all
            document.querySelectorAll('.stage').forEach(s => s.classList.remove('active'));
            // Add active to current
            if (active) {
                stageEl.classList.add('active');
            }
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
            updateStatus('<span class="spinner"></span> Test in progress...');

            ws = new WebSocket(`ws://${window.location.host}/ws/test`);

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.stage === 'listening') {
                    updateStatus(data.message);
                    updateStage(1, 'Listening for your voice...', true);
                }
                else if (data.stage === 'transcribed') {
                    updateStage(1, `You said: "${data.transcription}"`, false);
                    updateStage(2, 'Transforming to Patois...', true);
                }
                else if (data.stage === 'transformed') {
                    updateStage(2, `Patois: "${data.patois}"`, false);
                    updateStage(3, 'Generating speech...', true);
                }
                else if (data.stage === 'playing') {
                    updateStage(3, `Playing audio (${data.duration}ms generation time)`, true);
                }
                else if (data.stage === 'complete') {
                    updateStage(3, 'Playback complete!', false);
                    updateStatus('✓ Test complete! Click "Start Test" to run another.');
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
                updateStatus('WebSocket error - check console');
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
        transcription = await transcribe_speech(websocket)

        if not transcription:
            await websocket.send_json({"stage": "error", "message": "No speech detected"})
            await websocket.close()
            return

        # Stage 2: Transform
        await websocket.send_json({"stage": "transforming", "message": "Transforming to Patois..."})
        patois = transform_to_patois(transcription, websocket)
        await websocket.send_json({"stage": "transformed", "patois": patois})

        # Stage 3: TTS
        await websocket.send_json({"stage": "generating", "message": "Generating speech..."})
        import time
        start = time.perf_counter()
        generate_and_play_tts(patois)
        duration = int((time.perf_counter() - start) * 1000)

        await websocket.send_json({"stage": "playing", "duration": duration})
        await asyncio.sleep(1)  # Give time for audio to finish
        await websocket.send_json({"stage": "complete"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"stage": "error", "message": str(e)})
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("RASTA VOICE TESTING DASHBOARD")
    print("="*60)
    print(f"VB-Cable Device: {CABLE_DEVICE}")
    print(f"Headphone Device: {HEADPHONE_DEVICE}")
    print("\nStarting server at http://localhost:8080")
    print("Open your browser and navigate to the URL above")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)
