#!/usr/bin/env python3
"""
Ganja Mon Voice Control Dashboard
Complete voice pipeline monitoring and control interface
"""

import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="Ganja Mon Voice Dashboard")

TRANSCRIPT_FILE = Path(__file__).parent / "live_transcripts.jsonl"
CONFIG_FILE = Path(__file__).parent / "voice_config.json"

# Default config
DEFAULT_CONFIG = {
    "stability": 0.0,
    "style": 0.8,
    "temperature": 0.7,
    "model": "eleven_v3",
    "endpointing": 800
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ganja Mon Voice Control</title>
    <link href="https://fonts.googleapis.com/css2?family=VT323&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'IBM Plex Mono', monospace;
            background: linear-gradient(135deg, #2d1b4e 0%, #8b4513 50%, #c41e3a 100%);
            color: #ffd700;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        /* CRT Scanline effect */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 0, 0, 0.15),
                rgba(0, 0, 0, 0.15) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 1000;
        }

        /* Cannabis leaf watermark */
        body::after {
            content: '🌿';
            position: fixed;
            bottom: 20px;
            right: 20px;
            font-size: 200px;
            opacity: 0.03;
            pointer-events: none;
            z-index: 0;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 30px;
            background: rgba(0, 0, 0, 0.4);
            border: 3px solid;
            border-image: linear-gradient(90deg, #c41e3a, #ffd700, #228b22) 1;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
            position: relative;
        }

        h1 {
            font-family: 'VT323', monospace;
            font-size: 4em;
            color: #ffd700;
            text-shadow: 0 0 20px #ffd700, 0 0 40px #ff8c00;
            margin-bottom: 10px;
            letter-spacing: 3px;
        }

        .tagline {
            font-size: 1.2em;
            color: #ff8c00;
            font-style: italic;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            background: rgba(0, 0, 0, 0.6);
            border: 2px solid #ffd700;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
        }

        .panel-title {
            font-family: 'VT323', monospace;
            font-size: 2em;
            color: #ffd700;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 215, 0, 0.3);
        }

        /* Transcript Feed */
        .transcript-feed {
            height: 500px;
            overflow-y: auto;
            padding-right: 10px;
        }

        .transcript-feed::-webkit-scrollbar {
            width: 8px;
        }

        .transcript-feed::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
        }

        .transcript-feed::-webkit-scrollbar-thumb {
            background: #ffd700;
            border-radius: 4px;
        }

        .transcript-entry {
            margin-bottom: 20px;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .timestamp {
            font-size: 0.9em;
            color: #ff8c00;
            margin-bottom: 5px;
        }

        .original, .patois {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 8px;
        }

        .original {
            background: rgba(139, 69, 19, 0.3);
            border-left: 4px solid #8b4513;
        }

        .patois {
            background: rgba(34, 139, 34, 0.3);
            border-left: 4px solid #228b22;
        }

        .label {
            font-weight: 600;
            font-size: 0.85em;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .original .label {
            color: #ff8c00;
        }

        .patois .label {
            color: #98fb98;
        }

        .text {
            line-height: 1.6;
            color: #fff;
        }

        .emotion-tag {
            background: #ffd700;
            color: #000;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.9em;
        }

        /* Status Panel */
        .status-grid {
            display: grid;
            gap: 15px;
        }

        .status-item {
            background: rgba(255, 215, 0, 0.1);
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #ffd700;
        }

        .status-label {
            font-size: 0.85em;
            color: #ff8c00;
            margin-bottom: 5px;
        }

        .status-value {
            font-size: 1.3em;
            color: #ffd700;
            font-weight: 600;
        }

        .status-value.good {
            color: #98fb98;
        }

        .status-value.warning {
            color: #ffa500;
        }

        .status-value.error {
            color: #ff6b6b;
        }

        /* Controls */
        .controls-section {
            margin-top: 20px;
        }

        .control-group {
            margin-bottom: 20px;
        }

        .control-label {
            display: block;
            margin-bottom: 8px;
            color: #ffd700;
            font-size: 0.95em;
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: rgba(255, 215, 0, 0.2);
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #ffd700;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }

        .range-value {
            display: inline-block;
            min-width: 40px;
            text-align: right;
            color: #ff8c00;
            font-weight: 600;
        }

        button {
            background: linear-gradient(135deg, #228b22, #32cd32);
            color: #fff;
            border: 2px solid #ffd700;
            padding: 12px 30px;
            font-family: 'VT323', monospace;
            font-size: 1.5em;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
            width: 100%;
        }

        button:hover {
            background: linear-gradient(135deg, #32cd32, #228b22);
            box-shadow: 0 0 25px rgba(255, 215, 0, 0.6);
            transform: translateY(-2px);
        }

        button:active {
            transform: translateY(0);
        }

        /* Metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }

        .metric-card {
            background: rgba(0, 0, 0, 0.4);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(255, 215, 0, 0.3);
            text-align: center;
        }

        .metric-label {
            font-size: 0.85em;
            color: #ff8c00;
            margin-bottom: 5px;
        }

        .metric-value {
            font-size: 1.8em;
            color: #ffd700;
            font-weight: 600;
        }

        /* Pulse animation for live indicator */
        .pulse {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #32cd32;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 1.5s infinite;
            box-shadow: 0 0 10px #32cd32;
        }

        @keyframes pulse {
            0%, 100% {
                opacity: 1;
                transform: scale(1);
            }
            50% {
                opacity: 0.5;
                transform: scale(1.2);
            }
        }

        @media (max-width: 1200px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎙️ GANJA MON VOICE CONTROL 🎙️</h1>
            <div class="tagline">Real-Time Rasta Voice Transformation System</div>
        </header>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Exchanges</div>
                <div class="metric-value" id="totalCount">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Latency</div>
                <div class="metric-value" id="avgLatency">--</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">System Status</div>
                <div class="metric-value" id="systemStatus"><span class="pulse"></span>LIVE</div>
            </div>
        </div>

        <div class="main-grid">
            <div class="panel">
                <div class="panel-title">LIVE TRANSCRIPT FEED</div>
                <div class="transcript-feed" id="transcriptFeed">
                    <div style="text-align: center; color: #ff8c00; padding: 40px;">
                        Waiting for voice input...
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">VOICE CONTROLS</div>

                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-label">Voice Model</div>
                        <div class="status-value">Eleven v3</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Audio Output</div>
                        <div class="status-value good">48kHz Stereo</div>
                    </div>
                </div>

                <div class="controls-section">
                    <div class="control-group">
                        <label class="control-label">
                            Expressiveness (Stability): <span class="range-value" id="stabilityValue">0.0</span>
                        </label>
                        <input type="range" id="stability" min="0" max="1" step="0.1" value="0.0">
                    </div>

                    <div class="control-group">
                        <label class="control-label">
                            Style Exaggeration: <span class="range-value" id="styleValue">0.8</span>
                        </label>
                        <input type="range" id="style" min="0" max="1" step="0.1" value="0.8">
                    </div>

                    <div class="control-group">
                        <label class="control-label">
                            LLM Temperature: <span class="range-value" id="tempValue">0.7</span>
                        </label>
                        <input type="range" id="temperature" min="0" max="1" step="0.1" value="0.7">
                    </div>

                    <div class="control-group">
                        <label class="control-label">
                            End Buffer (ms): <span class="range-value" id="endpointValue">800</span>
                        </label>
                        <input type="range" id="endpointing" min="300" max="1500" step="100" value="800">
                    </div>

                    <button onclick="applySettings()">APPLY SETTINGS</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let lastId = 0;
        let transcriptCount = 0;

        // Update range value displays
        document.getElementById('stability').oninput = function() {
            document.getElementById('stabilityValue').textContent = this.value;
        };
        document.getElementById('style').oninput = function() {
            document.getElementById('styleValue').textContent = this.value;
        };
        document.getElementById('temperature').oninput = function() {
            document.getElementById('tempValue').textContent = this.value;
        };
        document.getElementById('endpointing').oninput = function() {
            document.getElementById('endpointValue').textContent = this.value;
        };

        function highlightEmotions(text) {
            return text.replace(/\\[([^\\]]+)\\]/g, '<span class="emotion-tag">[$1]</span>');
        }

        async function fetchTranscripts() {
            try {
                const res = await fetch('/api/transcripts?since=' + lastId);
                const data = await res.json();

                if (data.entries.length > 0) {
                    const feed = document.getElementById('transcriptFeed');

                    // Clear placeholder if exists
                    if (feed.children.length === 1 && feed.textContent.includes('Waiting')) {
                        feed.innerHTML = '';
                    }

                    data.entries.forEach(entry => {
                        const div = document.createElement('div');
                        div.className = 'transcript-entry';
                        div.innerHTML = `
                            <div class="timestamp">${entry.timestamp}</div>
                            <div class="original">
                                <div class="label">You Said:</div>
                                <div class="text">${entry.original}</div>
                            </div>
                            <div class="patois">
                                <div class="label">Ganja Mon:</div>
                                <div class="text">${highlightEmotions(entry.patois)}</div>
                            </div>
                        `;
                        feed.insertBefore(div, feed.firstChild);
                        lastId = entry.id;
                        transcriptCount++;
                    });

                    // Update count
                    document.getElementById('totalCount').textContent = transcriptCount;

                    // Keep only last 20 entries
                    while (feed.children.length > 20) {
                        feed.removeChild(feed.lastChild);
                    }
                }
            } catch (e) {
                console.error('Fetch error:', e);
            }
        }

        async function applySettings() {
            const config = {
                stability: parseFloat(document.getElementById('stability').value),
                style: parseFloat(document.getElementById('style').value),
                temperature: parseFloat(document.getElementById('temperature').value),
                endpointing: parseInt(document.getElementById('endpointing').value)
            };

            await fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });

            alert('Settings applied! Restart voice pipeline for changes to take effect.');
        }

        // Load saved settings
        async function loadSettings() {
            const res = await fetch('/api/config');
            const data = await res.json();

            document.getElementById('stability').value = data.stability;
            document.getElementById('stabilityValue').textContent = data.stability;

            document.getElementById('style').value = data.style;
            document.getElementById('styleValue').textContent = data.style;

            document.getElementById('temperature').value = data.temperature;
            document.getElementById('tempValue').textContent = data.temperature;

            document.getElementById('endpointing').value = data.endpointing;
            document.getElementById('endpointValue').textContent = data.endpointing;
        }

        // Poll for updates
        setInterval(fetchTranscripts, 500);
        fetchTranscripts();
        loadSettings();
    </script>
</body>
</html>
    """)

@app.get("/api/transcripts")
async def get_transcripts(since: int = 0):
    """Get transcripts since ID."""
    if not TRANSCRIPT_FILE.exists():
        return {"entries": []}

    entries = []
    with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip() and line_num > since:
                try:
                    data = json.loads(line)
                    data["id"] = line_num
                    entries.append(data)
                except:
                    pass

    return {"entries": entries}

@app.get("/api/config")
async def get_config():
    """Get current config."""
    return load_config()

@app.post("/api/config")
async def update_config(config: dict):
    """Update config."""
    save_config(config)
    return {"status": "saved", "config": config}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("GANJA MON VOICE CONTROL DASHBOARD")
    print("="*60)
    print("Starting server at http://localhost:8080")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
