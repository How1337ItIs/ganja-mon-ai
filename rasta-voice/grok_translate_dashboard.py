#!/usr/bin/env python3
"""
Simple web dashboard for Grok API translation using Ganja Mon persona.

Usage:
    python grok_translate_dashboard.py

Then open http://localhost:8086 in your browser.
"""

from __future__ import annotations

import os
import re
import sys
import time
import socket
from pathlib import Path
from typing import Optional

# Ensure dependencies are available
try:
    from dotenv import load_dotenv
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from openai import OpenAI
    from pydantic import BaseModel
    import uvicorn
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please run: pip install fastapi uvicorn python-dotenv openai pydantic")
    sys.exit(1)

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Initialize FastAPI
app = FastAPI(title="Ganja Mon Translator Dashboard")

# Prompt (Text-Only Version)
RASTA_SYSTEM_PROMPT = """
You are "Ganja Mon".

Task: Translate the user's English into Jamaican Patois / Western Rasta-flavored dialect while preserving the EXACT meaning.

Hard rules:
- Preserve meaning IDENTICALLY. Questions remain questions. Statements remain statements. Do NOT answer questions.
- Keep technical terms and proper nouns unchanged.
- Output ONLY the translated text. No explanations. No quotes.
- ABSOLUTELY NO emotion tags ([laughs], etc).

Style (Twitter/Telegram Optimized):
- **Clean & Natural:** No excessive dots (...) or drawn-out vowels. Keep it readable and crisp.
- **Social Flow:** Write as if posting on Twitter or chatting on Telegram. Short, punchy, engaging.
- **Patois:** Use "mon", "di", "dem", "ting", "wah gwaan" naturally.
- **Variety:** Use "seen" occasionally for emphasis, but don't overuse it.

Language of Consciousness (Iyaric):
- **First Person:** Strong preference for "I and I", "I-man". Avoid "me/mi".
- **Word Power:** "Overstand" (understand), "Apprecilove" (appreciate), "Downpress" (oppress).

=== GANJA OBSESSION (The Sacrament) ===
- Ganja is your life, your medicine, and your connection to Jah.
- NATURALLY weave references to di herb into translations (50-70% of the time).
- **Spiritual Depth:** Reference "Di chalice", "Reasoning", "Di holy herb", "Sacrament", "Healing of di nations".
- Weave these references naturally, but ALWAYS preserve the original meaning first.

Examples:
- "I need more money" -> "I and I need more funds to keep di chalice burning, mon."
- "The code is broken" -> "Di code mash up, mon. We haffi fix it ASAP."
- "What do you think?" -> "Wah yuh a pree, mon? Tell I and I di truth, overstand? 🤔"
- "It's beautiful outside" -> "It look wicked outside today, mon. Jah bless di creation. 🙏"

Remember: Translate meaning exactly. Keep it clean, social-media ready, and spiritually elevated.
""".strip()

_BRACKET_TAG_RE = re.compile(r"[^\]]+")


def clean_translation(text: str) -> str:
    """Defensive cleanup in case the model leaks quotes (but keep emotion tags!)."""
    s = (text or "").strip()
    
    # Remove wrapping quotes (common leakage)
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1].strip()
    
    # DO NOT remove emotion tags like [laughs] - they're part of the prompt!
    # Just clean up extra whitespace
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    
    return s


def build_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")


def translate_text(
    client: OpenAI,
    text: str,
    model: str = "grok-3",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> tuple[str, float]:
    """Translate English text to Patois using Ganja Mon persona."""
    start = time.perf_counter()
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": RASTA_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        latency_ms = (time.perf_counter() - start) * 1000
        out = resp.choices[0].message.content or ""
        return clean_translation(out), latency_ms
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        raise e


class TranslateRequest(BaseModel):
    text: str
    model: Optional[str] = "grok-3"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500


class TranslateResponse(BaseModel):
    translated: str
    latency_ms: float
    original: str


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the translation dashboard."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦁 Ganja Mon Translator 🌿</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Permanent+Marker&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Roboto Mono', monospace;
            background-color: #111;
            /* Rasta Gradient Background */
            background: linear-gradient(135deg, #2b0808 0%, #1a1a1a 50%, #061806 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
            overflow-x: hidden;
            position: relative;
        }

        /* Subtle smoke effect */
        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: url('https://raw.githubusercontent.com/SochavaAG/example-assets/master/fog1.png') repeat-x;
            background-size: 200% auto;
            opacity: 0.15;
            animation: moveSmoke 60s linear infinite;
            z-index: -1;
            pointer-events: none;
        }

        @keyframes moveSmoke {
            0% { background-position: 0 0; }
            100% { background-position: -200% 0; }
        }
        
        .rasta-border-top {
            height: 8px;
            width: 100%;
            background: linear-gradient(to right, #CE1126 33%, #FCD116 33%, #FCD116 66%, #009B3A 66%);
        }

        .container {
            max-width: 900px;
            margin: 40px auto;
            background: rgba(30, 30, 30, 0.95);
            border: 1px solid #333;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            backdrop-filter: blur(10px);
            position: relative;
        }
        
        .header {
            background: #222;
            padding: 40px 20px;
            text-align: center;
            border-bottom: 2px solid #333;
            position: relative;
        }

        .header h1 {
            font-family: 'Permanent Marker', cursive;
            font-size: 42px;
            margin-bottom: 10px;
            /* Gradient Text */
            background: linear-gradient(to right, #CE1126, #FCD116, #009B3A);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 1px;
        }
        
        .header p {
            color: #aaa;
            font-size: 16px;
            font-style: italic;
        }

        .emoji-decoration {
            font-size: 24px;
            margin: 0 10px;
        }
        
        .content {
            padding: 40px;
        }
        
        .input-section, .output-section {
            margin-bottom: 30px;
        }
        
        label {
            display: block;
            font-weight: 700;
            margin-bottom: 12px;
            color: #FCD116; /* Rasta Yellow */
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 14px;
        }
        
        textarea {
            width: 100%;
            min-height: 140px;
            padding: 20px;
            border: 2px solid #444;
            border-radius: 8px;
            background: #111;
            color: #00FF9C; /* Neon Green Text */
            font-size: 18px;
            font-family: 'Roboto Mono', monospace;
            resize: vertical;
            transition: all 0.3s;
            outline: none;
        }
        
        textarea:focus {
            border-color: #009B3A;
            box-shadow: 0 0 15px rgba(0, 155, 58, 0.2);
        }

        textarea::placeholder {
            color: #444;
        }
        
        .output-box {
            width: 100%;
            min-height: 140px;
            padding: 20px;
            border: 2px solid #444;
            border-radius: 8px;
            background: #1a1a1a;
            color: #FCD116; /* Yellow Text */
            font-size: 18px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Roboto Mono', monospace;
        }
        
        .output-box.loading {
            color: #888;
            font-style: italic;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
        
        .output-box.error {
            border-color: #CE1126;
            color: #CE1126;
            background: #2a1111;
        }
        
        .button-group {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        
        button {
            flex: 1;
            padding: 18px;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            font-family: 'Roboto Mono', monospace;
        }
        
        .btn-translate {
            background: linear-gradient(135deg, #006400 0%, #009B3A 100%);
            color: white;
            border-bottom: 4px solid #004d00;
        }
        
        .btn-translate:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 0 20px rgba(0, 155, 58, 0.4);
            filter: brightness(1.1);
        }
        
        .btn-translate:active:not(:disabled) {
            transform: translateY(2px);
            border-bottom: none;
            margin-top: 4px;
        }
        
        .btn-translate:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            background: #333;
            border-bottom: 4px solid #222;
        }
        
        .btn-clear {
            background: #333;
            color: #aaa;
            border-bottom: 4px solid #222;
            flex: 0.3;
        }
        
        .btn-clear:hover {
            background: #CE1126; /* Red on hover */
            color: white;
            border-bottom-color: #800000;
        }

        .stats {
            display: flex;
            justify-content: space-between;
            padding: 20px;
            background: #111;
            border-top: 1px solid #333;
            font-size: 12px;
            color: #666;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .stat-label {
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
            color: #CE1126;
        }
        
        .stat-value {
            font-weight: 700;
            color: #FCD116;
            font-size: 16px;
        }
        
        .error-message {
            padding: 15px;
            background: rgba(206, 17, 38, 0.1);
            border: 1px solid #CE1126;
            border-radius: 8px;
            color: #CE1126;
            margin-bottom: 20px;
            display: none;
            text-align: center;
        }
        
        .error-message.show {
            display: block;
        }

        /* Fun Rasta Details */
        .ganja-icon {
            font-size: 100px;
            position: absolute;
            opacity: 0.03;
            pointer-events: none;
            animation: float 10s ease-in-out infinite;
        }
        
        @keyframes float {
            0% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(10deg); }
            100% { transform: translateY(0px) rotate(0deg); }
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            color: #444;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="rasta-border-top"></div>
    
    <!-- Background Decor -->
    <div class="ganja-icon" style="top: 10%; left: 5%;">🌿</div>
    <div class="ganja-icon" style="top: 20%; right: 10%;">💨</div>
    <div class="ganja-icon" style="bottom: 15%; left: 15%;">🦁</div>

    <div class="container">
        <div class="header">
            <h1><span class="emoji-decoration">🦁</span> Ganja Mon <span class="emoji-decoration">🌿</span></h1>
            <p>Iyaric Translator • Jah Guide • Respect di Herb</p>
        </div>
        
        <div class="content">
            <div class="error-message" id="errorMessage"></div>
            
            <div class="input-section">
                <label for="inputText">Babylon Speech (English)</label>
                <textarea id="inputText" placeholder="Type yuh message here, mon..."></textarea>
            </div>
            
            <div class="button-group">
                <button class="btn-translate" id="translateBtn" onclick="translate()">
                    🔥 Light It Up! (Translate)
                </button>
                <button class="btn-clear" onclick="clearAll()">Stub It Out</button>
            </div>
            
            <div class="output-section">
                <label for="outputText">Rasta Vibration (Patois)</label>
                <div class="output-box" id="outputText">Di wisdom gonna appear right here...</div>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-label">Vibes</span>
                    <span class="stat-value" id="status">Irie</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Time</span>
                    <span class="stat-value" id="latency">-</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Letters</span>
                    <span class="stat-value" id="charCount">0</span>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        Powered by Grok • Blessed by Jah • Made with ❤️ & 🌿
    </div>
    
    <script>
        const inputText = document.getElementById('inputText');
        const outputText = document.getElementById('outputText');
        const translateBtn = document.getElementById('translateBtn');
        const errorMessage = document.getElementById('errorMessage');
        const statusEl = document.getElementById('status');
        const latencyEl = document.getElementById('latency');
        const charCountEl = document.getElementById('charCount');
        
        // Update character count
        inputText.addEventListener('input', () => {
            charCountEl.textContent = inputText.value.length;
        });
        
        // Enter key to translate (Ctrl+Enter or Cmd+Enter)
        inputText.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                translate();
            }
        });
        
        async function translate() {
            const text = inputText.value.trim();
            
            if (!text) {
                showError('Yo bredren, type something first!');
                return;
            }
            
            // Disable button and show loading
            translateBtn.disabled = true;
            translateBtn.innerHTML = '💨 Rolling...';
            outputText.textContent = 'Seeking guidance from di Most High...';
            outputText.className = 'output-box loading';
            statusEl.textContent = 'Cooking...';
            hideError();
            
            try {
                const response = await fetch('/api/translate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        model: 'grok-3',
                        temperature: 0.7,
                        max_tokens: 500,
                    }),
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Translation failed');
                }
                
                const data = await response.json();
                
                outputText.textContent = data.translated;
                outputText.className = 'output-box';
                statusEl.textContent = 'Blessed';
                latencyEl.textContent = data.latency_ms.toFixed(0) + 'ms';
                
            } catch (error) {
                showError('Bummer: ' + error.message);
                outputText.textContent = 'Di system crash, mon. Too much smoke? Check di error above.';
                outputText.className = 'output-box error';
                statusEl.textContent = 'Error';
                latencyEl.textContent = '-';
            } finally {
                translateBtn.disabled = false;
                translateBtn.innerHTML = '🔥 Light It Up! (Translate)';
            }
        }
        
        function clearAll() {
            inputText.value = '';
            outputText.textContent = 'Di wisdom gonna appear right here...';
            outputText.className = 'output-box';
            statusEl.textContent = 'Irie';
            latencyEl.textContent = '-';
            charCountEl.textContent = '0';
            hideError();
        }
        
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.add('show');
        }
        
        function hideError() {
            errorMessage.classList.remove('show');
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_api(request: TranslateRequest):
    """API endpoint for translation."""
    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="XAI_API_KEY not set in environment")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        client = build_client(api_key)
        translated, latency_ms = translate_text(
            client,
            request.text,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        return TranslateResponse(
            translated=translated,
            latency_ms=latency_ms,
            original=request.text,
        )
    except Exception as e:
        print(f"Translation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "prompt_loaded": bool(RASTA_SYSTEM_PROMPT)}


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


if __name__ == "__main__":
    port = int(os.getenv("TRANSLATOR_PORT", "8086"))
    
    print("=" * 60)
    print("🌿 Ganja Mon Translator Dashboard")
    print("=" * 60)
    
    # Check prompt loaded
    if not RASTA_SYSTEM_PROMPT:
        print("⚠️  WARNING: Prompt file not found or empty!")
        print(f"   Looking for: {PROMPT_PATH}")
    else:
        print(f"✅ Prompt loaded ({len(RASTA_SYSTEM_PROMPT)} characters)")
    
    # Check API key
    api_key = os.getenv("XAI_API_KEY", "").strip()
    if not api_key:
        print("⚠️  WARNING: XAI_API_KEY not set in environment!")
        print("   Set it in .env file or environment variables.")
    else:
        print(f"✅ API key found ({len(api_key)} characters)")
    
    # Check if port is in use and increment if necessary
    original_port = port
    while is_port_in_use(port):
        print(f"⚠️  Port {port} is in use, trying {port + 1}...")
        port += 1
        if port > original_port + 10:
            print("❌ Could not find a free port.")
            sys.exit(1)

    print(f"\n🚀 Starting server on http://localhost:{port}")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        # Run uvicorn programmatically passing the app object directly
        # This avoids import string issues
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Give tanks, mon!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
