/**
 * Cloudflare Worker: Ganja Mon Translator
 * =======================================
 * Serves the Rasta Dashboard and handles API proxying to xAI.
 */

const SYSTEM_PROMPT = `You are "Ganja Mon".

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
- "What do you think?" -> "Wah yuh a pree, mon? Tell I and I di truth, overstand?"
- "It's beautiful outside" -> "It look wicked outside today, mon. Jah bless di creation."

Remember: Translate meaning exactly. Keep it clean, social-media ready, and spiritually elevated.
`;

// HTML Content (Minified logic, same Rasta theme)
const HTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦁 Ganja Mon Translator 🌿</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Permanent+Marker&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Roboto Mono', monospace;
            background-color: #111;
            background: linear-gradient(135deg, #2b0808 0%, #1a1a1a 50%, #061806 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
            overflow-x: hidden;
            position: relative;
        }
        body::before {
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: url('https://raw.githubusercontent.com/SochavaAG/example-assets/master/fog1.png') repeat-x;
            background-size: 200% auto; opacity: 0.15;
            animation: moveSmoke 60s linear infinite; z-index: -1; pointer-events: none;
        }
        @keyframes moveSmoke { 0% { background-position: 0 0; } 100% { background-position: -200% 0; } }
        .rasta-border-top { height: 8px; width: 100%; background: linear-gradient(to right, #CE1126 33%, #FCD116 33%, #FCD116 66%, #009B3A 66%); }
        .container {
            max-width: 900px; margin: 40px auto; background: rgba(30, 30, 30, 0.95);
            border: 1px solid #333; border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5); overflow: hidden; backdrop-filter: blur(10px);
        }
        .header { background: #222; padding: 40px 20px; text-align: center; border-bottom: 2px solid #333; }
        .header h1 {
            font-family: 'Permanent Marker', cursive; font-size: 42px; margin-bottom: 10px;
            background: linear-gradient(to right, #CE1126, #FCD116, #009B3A);
            -webkit-background-clip: text; background-clip: text; color: transparent;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3); letter-spacing: 1px;
        }
        .header p { color: #aaa; font-size: 16px; font-style: italic; }
        .content { padding: 40px; }
        .input-section, .output-section { margin-bottom: 30px; }
        label { display: block; font-weight: 700; margin-bottom: 12px; color: #FCD116; text-transform: uppercase; letter-spacing: 1px; font-size: 14px; }
        textarea {
            width: 100%; min-height: 140px; padding: 20px; border: 2px solid #444;
            border-radius: 8px; background: #111; color: #00FF9C; font-size: 18px;
            font-family: 'Roboto Mono', monospace; resize: vertical; transition: all 0.3s; outline: none;
        }
        textarea:focus { border-color: #009B3A; box-shadow: 0 0 15px rgba(0, 155, 58, 0.2); }
        .output-box {
            width: 100%; min-height: 140px; padding: 20px; border: 2px solid #444;
            border-radius: 8px; background: #1a1a1a; color: #FCD116; font-size: 18px;
            line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; font-family: 'Roboto Mono', monospace;
        }
        .output-box.loading { color: #888; font-style: italic; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        .output-box.error { border-color: #CE1126; color: #CE1126; background: #2a1111; }
        .button-group { display: flex; gap: 15px; margin-bottom: 30px; }
        button {
            flex: 1; padding: 18px; border: none; border-radius: 8px; font-size: 18px;
            font-weight: 700; cursor: pointer; transition: all 0.3s; text-transform: uppercase;
            font-family: 'Roboto Mono', monospace;
        }
        .btn-translate { background: linear-gradient(135deg, #006400 0%, #009B3A 100%); color: white; border-bottom: 4px solid #004d00; }
        .btn-translate:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 0 20px rgba(0, 155, 58, 0.4); filter: brightness(1.1); }
        .btn-translate:disabled { opacity: 0.5; cursor: not-allowed; background: #333; border-bottom: 4px solid #222; }
        .btn-clear { background: #333; color: #aaa; border-bottom: 4px solid #222; flex: 0.3; }
        .btn-clear:hover { background: #CE1126; color: white; border-bottom-color: #800000; }
        .stats { display: flex; justify-content: space-between; padding: 20px; background: #111; border-top: 1px solid #333; font-size: 12px; color: #666; }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-label { text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; color: #CE1126; }
        .stat-value { font-weight: 700; color: #FCD116; font-size: 16px; }
        .error-message { padding: 15px; background: rgba(206, 17, 38, 0.1); border: 1px solid #CE1126; border-radius: 8px; color: #CE1126; margin-bottom: 20px; display: none; text-align: center; }
        .error-message.show { display: block; }
        .ganja-icon { font-size: 100px; position: absolute; opacity: 0.03; pointer-events: none; animation: float 10s ease-in-out infinite; }
        @keyframes float { 0% { transform: translateY(0px) rotate(0deg); } 50% { transform: translateY(-20px) rotate(10deg); } 100% { transform: translateY(0px) rotate(0deg); } }
        .footer { text-align: center; margin-top: 40px; color: #444; font-size: 12px; }
    </style>
</head>
<body>
    <div class="rasta-border-top"></div>
    <div class="ganja-icon" style="top: 10%; left: 5%;">🌿</div>
    <div class="ganja-icon" style="top: 20%; right: 10%;">💨</div>
    <div class="ganja-icon" style="bottom: 15%; left: 15%;">🦁</div>
    <div class="container">
        <div class="header">
            <h1>🦁 Ganja Mon 🌿</h1>
            <p>Iyaric Translator • Jah Guide</p>
            <div style="margin-top: 20px;">
                <a href="https://grokandmon.com/ganjafy" style="display: inline-block; color: #FCD116; text-decoration: none; font-family: 'Roboto Mono', monospace; font-size: 14px; border: 1px solid #FCD116; padding: 8px 16px; border-radius: 4px; transition: all 0.3s; background: rgba(252, 209, 22, 0.05);">
                    📸 Open Image Transformer
                </a>
            </div>
            <style>
                a[href*="ganjafy"]:hover { background: rgba(252, 209, 22, 0.15) !important; box-shadow: 0 0 15px rgba(252, 209, 22, 0.2); transform: translateY(-1px); }
            </style>
        </div>
        <div class="content">
            <div class="error-message" id="errorMessage"></div>
            <div class="input-section">
                <label>Babylon Speech (English)</label>
                <textarea id="inputText" placeholder="Type yuh message here, mon..."></textarea>
            </div>
            <div class="button-group">
                <button class="btn-translate" id="translateBtn" onclick="translateText()">🔥 Light It Up!</button>
                <button class="btn-clear" onclick="clearAll()">Stub It Out</button>
            </div>
            <div class="output-section">
                <label>Rasta Vibration (Patois)</label>
                <div class="output-box" id="outputText">Di wisdom gonna appear right here...</div>
            </div>
            <div class="stats">
                <div class="stat-item"><span class="stat-label">Vibes</span><span class="stat-value" id="status">Irie</span></div>
                <div class="stat-item"><span class="stat-label">Time</span><span class="stat-value" id="latency">-</span></div>
            </div>
        </div>
    </div>
    <div class="footer">Powered by Grok • Blessed by Jah</div>
    <script>
        console.log("🦁 Ganja Mon Translator v2.1 Loaded - with Cross-Link");
        // Enter to submit (Shift+Enter for newline)
        document.getElementById('inputText').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                translateText();
            }
        });

        async function translateText() {
            const text = document.getElementById('inputText').value.trim();
            if (!text) return showError('Yo bredren, type something first!');
            
            const btn = document.getElementById('translateBtn');
            const out = document.getElementById('outputText');
            const status = document.getElementById('status');
            const latency = document.getElementById('latency');
            
            btn.disabled = true; btn.innerHTML = '💨 Rolling...';
            out.className = 'output-box loading'; out.textContent = 'Cooking...';
            status.textContent = 'Cooking...'; hideError();
            
            const start = Date.now();
            try {
                const res = await fetch('/ganjamontexttranslator/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                
                if (!res.ok) throw new Error((await res.json()).error || 'Failed');
                
                const data = await res.json();
                out.textContent = data.translated;
                out.className = 'output-box';
                status.textContent = 'Blessed';
                latency.textContent = (Date.now() - start) + 'ms';
            } catch (e) {
                showError('Bummer: ' + e.message);
                out.className = 'output-box error';
                status.textContent = 'Error';
            } finally {
                btn.disabled = false; btn.innerHTML = '🔥 Light It Up!';
            }
        }
        function clearAll() {
            document.getElementById('inputText').value = '';
            document.getElementById('outputText').textContent = 'Di wisdom gonna appear right here...';
            document.getElementById('outputText').className = 'output-box';
            document.getElementById('status').textContent = 'Irie';
            document.getElementById('latency').textContent = '-';
            hideError();
        }
        function showError(msg) {
            const el = document.getElementById('errorMessage');
            el.textContent = msg; el.classList.add('show');
        }
        function hideError() { document.getElementById('errorMessage').classList.remove('show'); }
    </script>
</body>
</html>
`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 1. API Translation Endpoint
    if (url.pathname.endsWith('/api/translate')) {
      if (request.method !== 'POST') return new Response('Method Not Allowed', { status: 405 });
      
      try {
        const body = await request.json();
        const text = body.text;
        
        if (!text) return new Response(JSON.stringify({ error: 'No text provided' }), { status: 400 });
        
        // Call xAI API
        const response = await fetch('https://api.x.ai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${env.XAI_API_KEY}`
            },
            body: JSON.stringify({
                model: 'grok-3',
                messages: [
                    { role: 'system', content: SYSTEM_PROMPT },
                    { role: 'user', content: text }
                ],
                temperature: 0.7,
                max_tokens: 500
            })
        });

        if (!response.ok) {
            const err = await response.text();
            return new Response(JSON.stringify({ error: `Upstream API error: ${err}` }), { status: 500 });
        }

        const data = await response.json();
        const translated = data.choices[0].message.content;

        return new Response(JSON.stringify({ translated }), {
            headers: { 'Content-Type': 'application/json' }
        });

      } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }

    // 2. Serve Dashboard HTML
    return new Response(HTML, {
      headers: {
        'Content-Type': 'text/html; charset=UTF-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate'
      }
    });
  }
};
