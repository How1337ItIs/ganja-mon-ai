// Ganjafy V2 HTML Template - exported as string constant
// Preserves ALL V1 aesthetic (colors, fonts, glassmorphism, login, gallery)
// Adds Irie Alchemist recipe controls

export const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🌿 Ganjafy V2 - Powered by Irie Alchemist</title>
  <meta name="description" content="Transform any image with authentic Jamaican Rasta vibes - powered by the Irie Alchemist engine">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --rasta-red: #C8102E;
      --rasta-gold: #FFB81C;
      --rasta-green: #009639;
      --rasta-black: #0D0D0D;
      --bg-dark: #0a0f0a;
      --bg-card: #141a14;
      --text-primary: #f0f5f0;
      --text-secondary: #8fa88f;
      --text-muted: #5a6b5a;
      --rasta-gradient: linear-gradient(135deg, var(--rasta-green), var(--rasta-gold), var(--rasta-red));
      --glow-green: rgba(0, 150, 57, 0.4);
      --border-radius: 16px;
      --font-display: 'Permanent Marker', cursive;
      --font-body: 'Outfit', sans-serif;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: var(--font-body); background: var(--bg-dark); color: var(--text-primary); min-height: 100vh; }
    .screen { display: none; min-height: 100vh; }
    .screen.active { display: block; }
    .hidden { display: none !important; }

    /* ═══ LOGIN (preserved from V1) ═══ */
    .login-container {
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
      background: radial-gradient(ellipse at 20% 80%, var(--glow-green) 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 20%, rgba(255, 184, 28, 0.3) 0%, transparent 50%),
                  var(--bg-dark);
    }
    .login-card {
      background: var(--bg-card); border: 1px solid rgba(0, 150, 57, 0.3);
      border-radius: var(--border-radius); padding: 3rem; width: 100%; max-width: 420px;
      box-shadow: 0 0 60px rgba(0, 150, 57, 0.2), 0 20px 40px rgba(0, 0, 0, 0.5);
    }
    .login-header { text-align: center; margin-bottom: 2rem; }
    .login-header h1 {
      font-family: var(--font-display); font-size: 2.5rem;
      background: var(--rasta-gradient); -webkit-background-clip: text;
      -webkit-text-fill-color: transparent; background-clip: text;
    }
    .login-header .v2-badge {
      display: inline-block; background: linear-gradient(135deg, #6E54FF, #9F7AEA);
      color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px;
      font-family: var(--font-body); font-weight: 600; margin-left: 4px; vertical-align: super;
    }
    .tagline { color: var(--text-secondary); font-size: 1.1rem; }
    .cannabis-decoration { display: flex; justify-content: center; gap: 1.5rem; margin-bottom: 2rem; font-size: 2rem; animation: sway 3s ease-in-out infinite; }
    @keyframes sway { 0%, 100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
    .input-group { margin-bottom: 1rem; }
    .input-group input {
      width: 100%; padding: 1rem; font-size: 1rem; font-family: var(--font-body);
      background: rgba(0, 0, 0, 0.4); border: 2px solid rgba(0, 150, 57, 0.3);
      border-radius: 8px; color: var(--text-primary); transition: all 0.3s ease;
    }
    .input-group input:focus { outline: none; border-color: var(--rasta-green); box-shadow: 0 0 20px rgba(0, 150, 57, 0.3); }
    .login-btn {
      width: 100%; padding: 1rem; font-size: 1.1rem; font-family: var(--font-body); font-weight: 600;
      background: var(--rasta-gradient); border: none; border-radius: 8px; color: white; cursor: pointer; transition: all 0.3s ease;
    }
    .login-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(0, 150, 57, 0.4); }
    .error-msg { color: var(--rasta-red); text-align: center; margin-top: 1rem; min-height: 1.5rem; }

    /* ═══ DASHBOARD (preserved + enhanced) ═══ */
    #dashboard-screen {
      background: radial-gradient(ellipse at 20% 30%, rgba(0, 150, 57, 0.12) 0%, transparent 50%),
                  radial-gradient(ellipse at 80% 70%, rgba(255, 184, 28, 0.08) 0%, transparent 50%),
                  radial-gradient(ellipse at 50% 100%, rgba(200, 16, 46, 0.06) 0%, transparent 40%),
                  var(--bg-dark);
    }
    .dashboard-header {
      background: rgba(20, 26, 20, 0.9); border-bottom: 1px solid rgba(0, 150, 57, 0.3);
      padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center;
      flex-wrap: wrap; gap: 1rem; position: sticky; top: 0; z-index: 100; backdrop-filter: blur(20px);
    }
    .header-content h1 { font-family: var(--font-display); font-size: 1.8rem; background: var(--rasta-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .header-content p { color: var(--text-secondary); font-size: 0.9rem; }
    .logout-btn { background: transparent; border: 2px solid var(--rasta-red); color: var(--rasta-red); padding: 0.5rem 1rem; border-radius: 8px; font-family: var(--font-body); font-weight: 500; cursor: pointer; transition: all 0.3s ease; }
    .logout-btn:hover { background: var(--rasta-red); color: white; transform: translateY(-2px); }
    .dashboard-main { max-width: 1200px; margin: 0 auto; padding: 2rem; }

    /* ═══ RECIPE SELECTOR (NEW V2) ═══ */
    .recipe-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
      gap: 0.75rem; margin-bottom: 2rem; max-width: 700px; margin-left: auto; margin-right: auto;
    }
    .recipe-card {
      background: var(--bg-card); border: 2px solid rgba(255,255,255,0.1); border-radius: 12px;
      padding: 0.75rem; text-align: center; cursor: pointer; transition: all 0.3s ease;
    }
    .recipe-card:hover { border-color: var(--rasta-gold); transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,150,57,0.2); }
    .recipe-card.active { border-color: var(--rasta-green); background: rgba(0,150,57,0.15); box-shadow: 0 0 20px rgba(0,150,57,0.3); }
    .recipe-icon { font-size: 1.8rem; margin-bottom: 0.25rem; }
    .recipe-name { font-size: 0.75rem; font-weight: 600; color: var(--text-primary); }
    .recipe-desc { font-size: 0.65rem; color: var(--text-muted); margin-top: 2px; }

    /* ═══ ALCHEMY CONTROLS (NEW V2) ═══ */
    .alchemy-controls {
      max-width: 700px; margin: 0 auto 2rem; background: var(--bg-card);
      border: 1px solid rgba(0,150,57,0.2); border-radius: var(--border-radius); padding: 1.5rem;
    }
    .alchemy-section { margin-bottom: 1.25rem; }
    .alchemy-section:last-child { margin-bottom: 0; }
    .alchemy-label { font-size: 0.85rem; font-weight: 600; color: var(--rasta-gold); margin-bottom: 0.5rem; display: block; }
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .chip {
      padding: 0.4rem 0.85rem; border-radius: 20px; font-size: 0.8rem; font-family: var(--font-body);
      background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15); color: var(--text-secondary);
      cursor: pointer; transition: all 0.25s ease; user-select: none;
    }
    .chip:hover { border-color: var(--rasta-gold); color: var(--text-primary); }
    .chip.active { background: rgba(0,150,57,0.2); border-color: var(--rasta-green); color: var(--rasta-green); }
    .intensity-bar { display: flex; gap: 0.5rem; align-items: center; }
    .intensity-dot {
      width: 28px; height: 28px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.2);
      background: rgba(0,0,0,0.3); cursor: pointer; transition: all 0.25s ease;
      display: flex; align-items: center; justify-content: center; font-size: 0.65rem; color: var(--text-muted);
    }
    .intensity-dot:hover { border-color: var(--rasta-gold); }
    .intensity-dot.active { background: var(--rasta-green); border-color: var(--rasta-green); color: white; }
    .intensity-label { font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem; }
    .alchemy-select {
      background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15); color: var(--text-primary);
      padding: 0.5rem 1rem; border-radius: 8px; font-family: var(--font-body); font-size: 0.85rem;
      cursor: pointer; width: 100%; max-width: 300px;
    }
    .alchemy-select option { background: var(--bg-dark); }
    .alchemy-input {
      width: 100%; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15);
      color: var(--text-primary); padding: 0.5rem 1rem; border-radius: 8px;
      font-family: var(--font-body); font-size: 0.85rem; resize: vertical; min-height: 50px;
    }
    .alchemy-input:focus, .alchemy-select:focus { outline: none; border-color: var(--rasta-green); box-shadow: 0 0 10px rgba(0,150,57,0.2); }
    .alchemy-toggle { display: none; }
    .alchemy-toggle-btn {
      display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 8px;
      background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: var(--text-secondary);
      cursor: pointer; font-family: var(--font-body); font-size: 0.85rem; transition: all 0.3s; margin-bottom: 1rem;
    }
    .alchemy-toggle-btn:hover { border-color: var(--rasta-gold); }
    .help-text { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; margin-bottom: 0.4rem; line-height: 1.4; font-style: italic; }
    /* ═══ MULTI-IMAGE UPLOAD (V2) ═══ */
    .image-slots { max-width: 760px; margin: 0 auto 2rem; }
    .image-slots-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
    @media (max-width: 768px) { .image-slots-grid { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 480px) { .image-slots-grid { grid-template-columns: 1fr; } }
    .image-slot {
      border: 2px dashed rgba(0, 150, 57, 0.4); border-radius: 12px;
      background: rgba(20, 26, 20, 0.6); padding: 1rem; text-align: center;
      cursor: pointer; transition: all 0.3s ease; min-height: 170px;
      display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative;
    }
    .image-slot:hover { border-color: var(--rasta-green); background: rgba(0, 150, 57, 0.1); }
    .image-slot.has-image { border-style: solid; border-color: var(--rasta-green); }
    .image-slot.primary { border-color: var(--rasta-gold); border-width: 3px; }
    .image-slot.primary.has-image { border-color: var(--rasta-gold); background: rgba(255,184,28,0.05); }
    .slot-icon { font-size: 2.2rem; margin-bottom: 0.4rem; }
    .slot-label { font-weight: 600; font-size: 0.8rem; color: var(--text-primary); margin-bottom: 0.2rem; }
    .slot-desc { font-size: 0.65rem; color: var(--text-muted); line-height: 1.3; }
    .slot-badge { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.2rem; }
    .slot-badge.required { color: var(--rasta-gold); }
    .slot-badge.optional { color: var(--text-muted); }
    .slot-preview { width: 100%; max-height: 110px; object-fit: contain; border-radius: 8px; margin-bottom: 0.4rem; }
    .slot-remove { position: absolute; top: 6px; right: 8px; background: rgba(200,16,46,0.7); color: white; border: none; border-radius: 50%; width: 22px; height: 22px; font-size: 0.75rem; cursor: pointer; display: none; align-items: center; justify-content: center; z-index: 5; }
    .image-slot.has-image .slot-remove { display: flex; }
    .slot-role-select {
      background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.15); color: var(--text-primary);
      padding: 0.25rem 0.5rem; border-radius: 6px; font-family: var(--font-body); font-size: 0.7rem; margin-top: 0.4rem; width: 100%;
    }
    .slot-role-select option { background: var(--bg-dark); }
    .add-slot-btn {
      border: 2px dashed rgba(255,255,255,0.15); border-radius: 12px; background: transparent;
      color: var(--text-muted); font-family: var(--font-body); font-size: 0.85rem;
      cursor: pointer; transition: all 0.3s; min-height: 170px; display: flex;
      flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem;
    }
    .add-slot-btn:hover { border-color: var(--rasta-gold); color: var(--rasta-gold); background: rgba(255,184,28,0.05); }
    .add-slot-icon { font-size: 2rem; }
    .no-image-note { text-align: center; color: var(--rasta-gold); font-size: 0.9rem; margin-bottom: 1.5rem; padding: 0.75rem; background: rgba(255,184,28,0.1); border-radius: 8px; max-width: 760px; margin-left: auto; margin-right: auto; }
    .upload-icon { font-size: 3.5rem; margin-bottom: 0.75rem; }

    /* ═══ PREVIEW (preserved from V1) ═══ */
    .preview-container { display: grid; grid-template-columns: 1fr auto 1fr; gap: 1.5rem; align-items: center; margin-bottom: 2rem; }
    .preview-card { background: var(--bg-card); border-radius: var(--border-radius); padding: 1rem; border: 1px solid rgba(255, 255, 255, 0.1); }
    .preview-card h3 { text-align: center; margin-bottom: 0.75rem; font-size: 1rem; color: var(--text-secondary); }
    .preview-card.transformed h3 { color: var(--rasta-gold); }
    .image-wrapper { border-radius: 8px; overflow: hidden; background: rgba(0, 0, 0, 0.3); min-height: 250px; display: flex; align-items: center; justify-content: center; }
    .image-wrapper img { max-width: 100%; max-height: 350px; object-fit: contain; }
    .transform-arrow { text-align: center; }
    .transform-arrow .arrow { font-size: 2.5rem; color: var(--rasta-green); }
    .transform-text { font-size: 0.8rem; color: var(--text-muted); display: block; }

    /* ═══ LOADING (preserved from V1) ═══ */
    .loading { text-align: center; padding: 2rem; }
    .loading-smoke { font-size: 2rem; margin-bottom: 0.5rem; }
    .loading-smoke span { display: inline-block; animation: float-smoke 1.5s ease-in-out infinite; }
    .loading-smoke span:nth-child(2) { animation-delay: 0.2s; }
    .loading-smoke span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes float-smoke { 0%, 100% { transform: translateY(0) scale(1); opacity: 0.7; } 50% { transform: translateY(-10px) scale(1.2); opacity: 1; } }
    .loading p { color: var(--rasta-gold); }
    .loading-sub { color: var(--text-muted); font-size: 0.9rem; }

    /* ═══ BUTTONS (preserved from V1) ═══ */
    .btn-container { text-align: center; margin-bottom: 2rem; }
    .transform-btn {
      background: var(--rasta-gradient); border: none; padding: 1rem 2.5rem; font-size: 1.2rem;
      font-family: var(--font-body); font-weight: 600; color: white; border-radius: 8px;
      cursor: pointer; transition: all 0.3s ease; display: inline-flex; align-items: center; gap: 0.75rem;
    }
    .transform-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(0, 150, 57, 0.4); }
    .transform-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .download-btn {
      background: var(--bg-card); border: 2px solid var(--rasta-gold); color: var(--rasta-gold);
      padding: 0.75rem 1.5rem; font-size: 1rem; font-weight: 600; border-radius: 8px; cursor: pointer;
      transition: all 0.3s ease; text-decoration: none; display: inline-flex; align-items: center; margin-left: 1rem;
    }
    .download-btn:hover { background: var(--rasta-gold); color: var(--bg-dark); }

    /* ═══ MODEL SELECTOR (preserved from V1) ═══ */
    .model-selector { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
    .model-selector label { color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; }
    .model-selector select {
      background: var(--bg-card); border: 2px solid var(--rasta-green); color: var(--text-primary);
      padding: 0.5rem 1rem; font-size: 0.9rem; border-radius: 8px; font-family: var(--font-body); cursor: pointer; transition: all 0.3s ease;
    }
    .model-selector select:hover { border-color: var(--rasta-gold); box-shadow: 0 0 15px rgba(255, 184, 28, 0.2); }
    .model-selector select:focus { outline: none; border-color: var(--rasta-gold); box-shadow: 0 0 20px rgba(255, 184, 28, 0.3); }
    .model-selector select option { background: var(--bg-dark); color: var(--text-primary); }

    /* ═══ INFO + GALLERY + MODAL + FOOTER (preserved from V1) ═══ */
    .info-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
    .info-card { background: var(--bg-card); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: var(--border-radius); padding: 1.25rem; }
    .info-card h3 { color: var(--rasta-gold); margin-bottom: 0.75rem; font-size: 1.1rem; }
    .info-card ul { list-style: none; }
    .info-card li { padding: 0.4rem 0; color: var(--text-secondary); border-bottom: 1px solid rgba(255,255,255,0.05); }
    .info-card li:last-child { border-bottom: none; }
    .info-card p { color: var(--text-secondary); line-height: 1.6; }
    .info-card .small { font-size: 0.85rem; color: var(--text-muted); }
    .gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; padding: 1rem 0; }
    .gallery-item { background: var(--bg-card); border-radius: var(--border-radius); overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); transition: all 0.3s ease; cursor: pointer; }
    .gallery-item:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0, 150, 57, 0.2); border-color: var(--rasta-gold); }
    .gallery-img-container { width: 100%; height: 250px; overflow: hidden; background: #000; }
    .gallery-img-container img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease; }
    .gallery-item:hover img { transform: scale(1.05); }
    .gallery-info { padding: 1rem; }
    .gallery-date { font-size: 0.8rem; color: var(--rasta-gold); margin-bottom: 0.25rem; }
    .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.3s; }
    .modal.active { opacity: 1; pointer-events: all; }
    .modal-content { max-width: 90%; max-height: 90vh; position: relative; }
    .modal-img { max-width: 100%; max-height: 85vh; border-radius: 8px; box-shadow: 0 0 30px rgba(0,0,0,0.5); }
    .modal-close { position: absolute; top: -40px; right: 0; color: white; font-size: 2rem; cursor: pointer; }
    .modal-close:hover { color: var(--rasta-red); }
    .dashboard-footer { text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.9rem; }
    .dashboard-footer a { color: var(--rasta-green); text-decoration: none; }
    .dashboard-footer a:hover { text-decoration: underline; }

    /* ═══ METADATA DISPLAY (NEW V2) ═══ */
    .transmission-card {
      background: var(--bg-card); border: 1px solid rgba(0,150,57,0.3); border-radius: var(--border-radius);
      padding: 1.25rem; margin-top: 1rem; max-width: 700px; margin-left: auto; margin-right: auto;
    }
    .transmission-card h4 { color: var(--rasta-gold); font-family: var(--font-display); font-size: 1rem; margin-bottom: 0.5rem; }
    .transmission-text { color: var(--text-secondary); font-size: 0.85rem; font-style: italic; line-height: 1.5; }
    .meta-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
    .meta-chip { font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; background: rgba(0,150,57,0.15); color: var(--rasta-green); border: 1px solid rgba(0,150,57,0.3); }

    @media (max-width: 768px) {
      .preview-container { grid-template-columns: 1fr; }
      .transform-arrow { transform: rotate(90deg); padding: 1rem 0; }
      .dashboard-header { flex-direction: column; text-align: center; }
      .recipe-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
    }
  </style>
</head>
<body>
  <!-- Modal -->
  <div id="image-modal" class="modal">
    <div class="modal-content">
      <div class="modal-close" id="modal-close">&times;</div>
      <img id="modal-img" class="modal-img" src="">
      <div style="text-align: center; margin-top: 1rem;">
        <a id="modal-download" class="download-btn" href="#" download style="display: inline-flex;">Download High Res</a>
      </div>
    </div>
  </div>

  <!-- Login Screen (preserved from V1) -->
  <div id="login-screen" class="screen active">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1>🌿 Ganjafy <span class="v2-badge">V2</span></h1>
          <p class="tagline">Powered by the Irie Alchemist</p>
        </div>
        <div class="cannabis-decoration"><span>🍃</span><span>🌿</span><span>🍃</span></div>
        <form id="login-form">
          <div class="input-group">
            <input type="password" id="password-input" placeholder="Secret Password (uses our AI)" autocomplete="off">
          </div>
          <button type="submit" class="login-btn"><span>Enter di Vibes</span> <span>💨</span></button>
        </form>
        <div style="text-align: center; margin: 1.5rem 0 0.5rem; color: var(--text-muted); font-size: 0.9rem;">— OR —</div>
        <button id="byok-btn" class="login-btn" style="background: linear-gradient(135deg, #6B46C1, #9F7AEA); margin-top: 0;">
          <span>🔑 Bring Your Own API Key</span>
        </button>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.75rem; text-align: center;">Use your own Gemini or OpenRouter key</p>
        <p id="login-error" class="error-msg"></p>
      </div>
    </div>
  </div>

  <!-- Dashboard -->
  <div id="dashboard-screen" class="screen">
    <header class="dashboard-header">
      <div class="header-content">
        <h1>🌿 Ganjafy V2</h1>
        <p>Powered by Irie Alchemist • NETSPI-BINGHI Engine</p>
      </div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;">
        <button id="gallery-btn" class="logout-btn" style="border-color: var(--rasta-gold); color: var(--rasta-gold);">Gallery 🖼️</button>
        <button id="create-btn" class="logout-btn hidden" style="border-color: var(--rasta-green); color: var(--rasta-green);">Create 🎨</button>
        <button id="text-translator-btn" class="logout-btn" onclick="window.location.href='https://grokandmon.com/ganjamontexttranslator'">Text Translator 💬</button>
        <button id="logout-btn" class="logout-btn">Bless Out 🚪</button>
      </div>
    </header>

    <main class="dashboard-main" id="create-view">
      <!-- Recipe Selector (NEW V2) -->
      <div class="recipe-grid" id="recipe-grid"></div>

      <!-- No-image recipe note -->
      <div id="no-image-note" class="no-image-note hidden">✨ This recipe generates from text only - no image needed! Adjust alchemy controls below or hit Transmit.</div>

      <!-- Multi-Image Upload (V2 - Dynamic Slots) -->
      <div class="image-slots" id="image-slots">
        <div class="image-slots-grid" id="image-slots-grid">
          <!-- Slots are built dynamically by JS -->
        </div>
        <p style="text-align: center; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.75rem;">JPEG, PNG, WebP • Max 10MB each • Drop or click to add • Multiple subjects supported</p>
      </div>

      <!-- Alchemy Controls (NEW V2) -->
      <button class="alchemy-toggle-btn" id="alchemy-toggle-btn" onclick="document.getElementById('alchemy-controls').classList.toggle('hidden'); this.querySelector('.toggle-arrow').textContent = document.getElementById('alchemy-controls').classList.contains('hidden') ? '▶' : '▼';">
        <span class="toggle-arrow">▶</span> 🔮 Alchemy Controls <span style="font-size:0.7rem; color:var(--text-muted);">(optional)</span>
      </button>
      <div class="alchemy-controls hidden" id="alchemy-controls">
        <div class="alchemy-section">
          <span class="alchemy-label">⚡ Intensity</span>
          <p class="help-text">How heavily the recipe transforms the image. Low = subtle accents, High = full visual possession.</p>
          <div class="intensity-bar" id="intensity-bar">
            <div class="intensity-dot active" data-val="1">1</div>
            <div class="intensity-dot active" data-val="2">2</div>
            <div class="intensity-dot active" data-val="3">3</div>
            <div class="intensity-dot" data-val="4">4</div>
            <div class="intensity-dot" data-val="5">5</div>
            <span class="intensity-label" id="intensity-label">Heavy</span>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">🕰️ Era</span>
          <p class="help-text">Sets the visual time period. Affects color grading, film grain, typography, and cultural references in the output.</p>
          <div class="chip-row" id="era-chips">
            <div class="chip" data-val="1930s" title="Sepia tone, Pinnacle commune era, early Rasta movement. Hand-tinted photography aesthetic.">1930s</div>
            <div class="chip" data-val="1960s" title="Civil rights era, Ska music, independence movement. Vintage Kodachrome colors.">1960s</div>
            <div class="chip" data-val="1970s" title="Peak roots reggae, dub experiments, Haile Selassie imagery. Warm analog film tones.">1970s</div>
            <div class="chip" data-val="1980s" title="Dancehall emergence, digital riddims, international spread. VHS aesthetic.">1980s</div>
            <div class="chip" data-val="modern" title="Contemporary clean look, digital art fusion, modern Rasta culture.">Modern</div>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">🎭 Mood</span>
          <p class="help-text">Emotional tone that shapes the color palette, atmosphere, and symbolic elements in your transformation.</p>
          <div class="chip-row" id="mood-chips">
            <div class="chip" data-val="ital" title="Pure, natural, earth-connected. Clean greens, meditation, farm-to-table sacrament. Peaceful vibration.">🌿 Ital</div>
            <div class="chip" data-val="militant" title="Righteous anger, revolution, resistance. High contrast, bold reds, raised fists, fire imagery.">⚡ Militant</div>
            <div class="chip" data-val="conscious" title="Awareness, education, reasoning. Warm gold tones, books, scrolls, third-eye symbolism.">🕊️ Conscious</div>
            <div class="chip" data-val="royal" title="Ethiopian royalty, Lion of Judah, imperial majesty. Purple, gold, crowns, velvet texture.">👑 Royal</div>
            <div class="chip" data-val="dub" title="Sound system culture, bass frequencies made visible. Echo effects, speaker stacks, reverb trails.">🔊 Dub</div>
            <div class="chip" data-val="chaos" title="Egregore mode. Unhinged visual static, psychedelic distortion, glitch aesthetics, Black Ark madness.">🌀 Chaos</div>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">👤 Figure Grounding</span>
          <p class="help-text">Anchors the visual language to a specific Rasta prophet or figure. Their iconography, era, and philosophy influences the output.</p>
          <div class="chip-row" id="figure-chips">
            <div class="chip" data-val="selassie" title="Emperor Haile Selassie I — Ethiopian imperial regalia, Lion of Judah, Orthodox cross, formal portraiture.">👑 Selassie</div>
            <div class="chip" data-val="marley" title="Bob Marley — Trench Town roots, One Love energy, natural dreads, concert stage presence, acoustic warmth.">🎸 Marley</div>
            <div class="chip" data-val="perry" title="Lee 'Scratch' Perry — Black Ark studio chaos, hand-painted walls, sonic experimentation, raw DIY madness.">🔊 Perry</div>
            <div class="chip" data-val="tosh" title="Peter Tosh — Militant equal rights, machete imagery, Legalize It activism, uncompromising resistance.">⚔️ Tosh</div>
            <div class="chip" data-val="garvey" title="Marcus Garvey — Pan-African prophecy, UNIA movement, black star liner, formal oratory, nation-building.">📜 Garvey</div>
            <div class="chip" data-val="howell" title="Leonard Howell — The First Rasta, Pinnacle commune founder, ganja farmer prophet, colonial resistance.">🏔️ Howell</div>
          </div>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">🌿 Strain Context</span>
          <p class="help-text">Infuses strain-specific color palette and terpene symbolism into the visual output. Each strain has unique visual DNA.</p>
          <select class="alchemy-select" id="strain-select">
            <option value="">None (no strain influence)</option>
            <option value="gdp_runtz" selected>GDP Runtz — Deep purples, dense trichomes, indica calm (Current Grow)</option>
            <option value="jamaican_lambsbread">Jamaican Lamb's Bread — Golden sativa glow, tropical energy, Marley's choice</option>
            <option value="durban_poison">Durban Poison — African landrace, bright sativa clarity, sharp greens</option>
            <option value="blue_dream">Blue Dream — Hazy blue-violet tones, dreamy clouds, balanced energy</option>
            <option value="og_kush">OG Kush — Earth tones, West Coast sunset, heavy resin, deep forest</option>
          </select>
        </div>
        <div class="alchemy-section">
          <span class="alchemy-label">📝 Custom Incantation</span>
          <p class="help-text">Free-form text appended to the prompt. Describe a scene, reference an artist, or add specific visual instructions.</p>
          <textarea class="alchemy-input" id="custom-prompt" placeholder="Additional prophecy... (e.g., 'walking through Bull Bay at dawn' or 'in the style of a 1970s Jamaican dancehall poster')"></textarea>
        </div>
      </div>

      <!-- Preview (preserved from V1) -->
      <div id="preview-container" class="preview-container hidden">
        <div class="preview-card original">
          <h3>Original Babylon Version</h3>
          <div class="image-wrapper"><img id="original-preview" src="" alt="Original"></div>
        </div>
        <div class="transform-arrow"><span class="arrow">→</span><span class="transform-text">Irie Transformation</span></div>
        <div class="preview-card transformed">
          <h3>Blessed Rasta Version</h3>
          <div class="image-wrapper" id="result-wrapper">
            <div id="loading-indicator" class="loading hidden">
              <div class="loading-smoke"><span>💨</span><span>💨</span><span>💨</span></div>
              <p>Jah is blessing your image...</p>
              <p class="loading-sub" id="loading-recipe-text">Adding tams, dreads & ganja vibes</p>
            </div>
            <img id="result-preview" src="" alt="Transformed" class="hidden">
          </div>
        </div>
      </div>

      <!-- Buttons (preserved from V1 + enhanced) -->
      <div class="btn-container">
        <div id="api-key-config" class="hidden" style="background: var(--bg-card); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; max-width: 500px; margin-left: auto; margin-right: auto;">
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
            <span>🔑</span><label style="color: var(--text-secondary); font-weight: 500;">Your API Key</label>
          </div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <select id="api-provider" style="background: var(--bg-dark); border: 2px solid var(--rasta-green); color: var(--text-primary); padding: 0.5rem; border-radius: 8px; font-family: var(--font-body);">
              <option value="gemini">Google Gemini</option>
              <option value="openrouter">OpenRouter</option>
            </select>
            <input type="password" id="user-api-key" placeholder="Paste your API key here" style="flex: 1; min-width: 200px; background: var(--bg-dark); border: 2px solid rgba(255,255,255,0.2); color: var(--text-primary); padding: 0.5rem 1rem; border-radius: 8px; font-family: var(--font-body);">
          </div>
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem;">
            <input type="checkbox" id="save-key-checkbox" style="width: 18px; height: 18px; accent-color: var(--rasta-green);">
            <label for="save-key-checkbox" style="color: var(--text-muted); font-size: 0.85rem;">Save key locally (browser only)</label>
          </div>
          <p id="key-status" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;"></p>
        </div>

        <div class="model-selector" id="model-selector" style="display: none;">
          <label for="model-select">🧠 AI Model:</label>
          <select id="model-select">
            <optgroup label="Direct Google API">
              <option value="gemini-3-pro-image-preview">Gemini 3 Pro (Best Quality)</option>
              <option value="gemini-2.5-flash-image">Gemini 2.5 Flash (Reliable)</option>
              <option value="imagen-4.0-generate-001">Imagen 4 (Text-to-Image)</option>
            </optgroup>
            <optgroup label="🌐 OpenRouter - Google">
              <option value="openrouter-gemini-3-pro">Nano Banana Pro 🍌</option>
              <option value="openrouter-gemini-2.5-flash">Nano Banana (2.5 Flash)</option>
              <option value="openrouter-gemini-2.0-free">Gemini 2.0 Flash (FREE) 🆓</option>
            </optgroup>
            <optgroup label="🌐 OpenRouter - FLUX">
              <option value="openrouter-flux-pro">FLUX.2 Pro (High Quality)</option>
              <option value="openrouter-flux-max">FLUX.2 Max (Best) 💰</option>
              <option value="openrouter-flux-klein">FLUX.2 Klein (Fast & Cheap)</option>
            </optgroup>
          </select>
        </div>
        <button id="transform-btn" class="transform-btn hidden">
          <span>🌿</span><span id="transform-btn-text">Transmit to Jah!</span><span>🌿</span>
        </button>
        <a id="download-btn" class="download-btn hidden" download><span>⬇️ Download Blessed Image</span></a>
        <div id="save-status" style="margin-top: 0.75rem; font-size: 0.9rem; text-align: center;"></div>
      </div>

      <!-- Transmission Metadata (NEW V2) -->
      <div id="transmission-card" class="transmission-card hidden">
        <h4>📡 Transmission Received</h4>
        <p class="transmission-text" id="transmission-text"></p>
        <div class="meta-chips" id="meta-chips"></div>
      </div>

      <section class="info-section">
        <div class="info-card">
          <h3>🔮 Recipe Guide</h3>
          <ul>
            <li><strong>🖼️ Irie Portrait</strong> — Identity-preserving rasta transformation. Adds dreads, tam, ganja, and cultural elements while keeping the subject's face intact.</li>
            <li><strong>👑 Lion of Judah</strong> — Ethiopian royalty aesthetic. Imperial regalia, Lion imagery, Solomonic dynasty styling.</li>
            <li><strong>✊ Roots Rebel</strong> — Revolutionary poster art. Protest energy, raised fists, militant typography, liberation movement vibes.</li>
            <li><strong>🔊 Dub Dreamscape</strong> — Sound system culture visualized. No input image needed. Generates speaker stacks, echo trails, bass frequencies.</li>
            <li><strong>🌿 Botanical Study</strong> — Sacred plant science. Transforms images with botanical illustration style, trichome details, and medicinal documentation aesthetic.</li>
            <li><strong>📜 Ganja Poster</strong> — Event/concert poster art. No input image needed. Generates vintage reggae show posters and promotional art.</li>
            <li><strong>🌀 Chaos Static</strong> — Egregore mode. Maximum psychedelic distortion, glitch art, Lee Perry Black Ark chaos energy.</li>
            <li><strong>💎 Milady Irie</strong> — NFT-style output. Combines Milady/Remilia aesthetic with Rasta elements for collectible digital art.</li>
          </ul>
        </div>
        <div class="info-card">
          <h3>📸 Multi-Image Input</h3>
          <p><strong>Primary / Character Images</strong> — The main subjects. Add one per person/character you want in the scene. Each gets transformed with the selected recipe.</p>
          <p style="margin-top: 0.5rem;"><strong>Style Reference</strong> — Optional. Upload any image whose visual style you want to borrow. Choose: match style, steal palette, apply texture, or follow composition.</p>
          <p style="margin-top: 0.5rem;"><strong>Scene / Background</strong> — Optional. An environment to place subjects in. Choose: use as background, place in environment, blend, or inpaint.</p>
          <p style="margin-top: 0.5rem;"><strong>+ Add Another</strong> — Need more? Add extra character refs, additional style refs, or more scene images. No limit.</p>
          <p class="small" style="margin-top: 0.75rem;">Irie Alchemist V2 • NETSPI-BINGHI Engine • Inspired by Irie Milady + Visual Alchemist</p>
        </div>
      </section>
    </main>

    <main class="dashboard-main hidden" id="gallery-view">
      <h2 style="font-family: var(--font-display); color: var(--rasta-gold); margin-bottom: 1.5rem; text-align: center;">Blessed Gallery</h2>
      <div id="gallery-grid" class="gallery-grid"></div>
      <div id="gallery-loading" class="loading hidden"><p>Loading di gallery...</p></div>
      <div id="pagination-container" style="text-align: center; margin-top: 2rem;">
        <button id="load-more-btn" class="transform-btn hidden" style="padding: 0.75rem 2rem; font-size: 1rem;">🌿 Load More Blessings 🌿</button>
        <p id="gallery-count" style="color: var(--text-muted); margin-top: 1rem;"></p>
      </div>
    </main>

    <footer class="dashboard-footer">
      <p>💚💛❤️ One Love • <a href="https://grokandmon.com">grokandmon.com</a> • Jah Bless 💚💛❤️</p>
    </footer>
  </div>
</body>
</html>`;
