#!/usr/bin/env python3
"""
Live Transcript Dashboard (Localhost Only)

Shows real-time transcripts from rasta_live.py:
- What you said (original English)
- Patois translation
"""

import json
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import asyncio

app = FastAPI()

TRANSCRIPT_FILE = Path(__file__).parent / "live_transcripts.jsonl"

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Live Transcript - Ganja Mon</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #0f0;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 255, 0, 0.1);
            border: 2px solid #0f0;
            border-radius: 10px;
        }
        h1 { color: #0f0; margin-bottom: 10px; }
        .subtitle { color: #0a0; }
        .transcript-container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .entry {
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0, 255, 0, 0.05);
            border-left: 4px solid #0f0;
            border-radius: 5px;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .timestamp {
            color: #0a0;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .original {
            margin-bottom: 15px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
        }
        .label {
            color: #0a0;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .text {
            color: #fff;
            font-size: 1.1em;
            line-height: 1.6;
        }
        .patois {
            padding: 10px;
            background: rgba(0, 255, 0, 0.1);
            border-radius: 3px;
        }
        .patois .text {
            color: #0f0;
        }
        .emotion-tag {
            color: #ff0;
            font-weight: bold;
        }
        .status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: rgba(0, 255, 0, 0.2);
            border: 1px solid #0f0;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .pulse {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #0f0;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="status"><span class="pulse"></span>LIVE</div>

    <div class="header">
        <h1>GANJA MON - LIVE TRANSCRIPT</h1>
        <div class="subtitle">Real-time voice pipeline monitoring</div>
    </div>

    <div class="transcript-container" id="transcripts"></div>

    <script>
        let lastId = 0;

        function highlightEmotions(text) {
            return text.replace(/\[([^\]]+)\]/g, '<span class="emotion-tag">[$1]</span>');
        }

        async function fetchTranscripts() {
            const res = await fetch('/api/transcripts?since=' + lastId);
            const data = await res.json();

            if (data.entries.length > 0) {
                const container = document.getElementById('transcripts');

                data.entries.forEach(entry => {
                    const div = document.createElement('div');
                    div.className = 'entry';
                    div.innerHTML = `
                        <div class="timestamp">${entry.timestamp}</div>
                        <div class="original">
                            <div class="label">YOU SAID:</div>
                            <div class="text">${entry.original}</div>
                        </div>
                        <div class="patois">
                            <div class="label">GANJA MON:</div>
                            <div class="text">${highlightEmotions(entry.patois)}</div>
                        </div>
                    `;
                    container.insertBefore(div, container.firstChild);
                    lastId = entry.id;
                });
            }
        }

        // Poll every 500ms
        setInterval(fetchTranscripts, 500);
        fetchTranscripts(); // Initial load
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

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("LIVE TRANSCRIPT DASHBOARD")
    print("="*60)
    print("Open: http://localhost:8081")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8081)
