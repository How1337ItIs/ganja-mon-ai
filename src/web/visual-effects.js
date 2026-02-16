/**
 * Grok & Mon Visual Effects Module
 * Smoke particles, color transitions, vinyl animation, trichome sparkles, CRT overlay
 */

class VisualEffectsManager {
    constructor() {
        this.settings = this.loadSettings();
        this.particles = [];
        this.animationFrameId = null;
        this.colorPhase = 0;
        this.vinylAngle = 0;
        this.isPlaying = false;
        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        this.init();
    }

    loadSettings() {
        const defaults = {
            smokeEnabled: true,
            colorTransitionsEnabled: true,
            vinylAnimationEnabled: false,  // Disabled by default
            trichomeSparklesEnabled: true,
            crtOverlayEnabled: false,
            particleDensity: 30 // number of particles
        };

        try {
            const saved = localStorage.getItem('grokmon_visual_settings');
            return saved ? { ...defaults, ...JSON.parse(saved) } : defaults;
        } catch {
            return defaults;
        }
    }

    saveSettings() {
        try {
            localStorage.setItem('grokmon_visual_settings', JSON.stringify(this.settings));
        } catch (e) {
            console.warn('Could not save visual settings:', e);
        }
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.createSmokeCanvas();
        this.createCRTOverlay();
        this.createVinylRecord();
        this.createTrichomeContainer();
        // this.createSettingsPanel(); // REMOVED - user doesn't want star button
        this.bindMusicEvents();

        // Start animation loop if not reduced motion
        if (!this.reducedMotion) {
            this.startAnimationLoop();
        }

        // Listen for reduced motion preference changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.reducedMotion = e.matches;
            if (this.reducedMotion) {
                this.stopAnimationLoop();
            } else {
                this.startAnimationLoop();
            }
        });
    }

    // ============================================
    // SMOKE PARTICLE SYSTEM
    // ============================================
    createSmokeCanvas() {
        const canvas = document.createElement('canvas');
        canvas.id = 'smoke-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 2;
            opacity: 0.4;
        `;
        document.body.insertBefore(canvas, document.body.firstChild);

        this.smokeCanvas = canvas;
        this.smokeCtx = canvas.getContext('2d');
        this.resizeCanvas();

        window.addEventListener('resize', () => this.resizeCanvas());

        // Initialize particles
        this.initParticles();
    }

    resizeCanvas() {
        if (this.smokeCanvas) {
            this.smokeCanvas.width = window.innerWidth;
            this.smokeCanvas.height = window.innerHeight;
        }
    }

    initParticles() {
        this.particles = [];
        const count = this.settings.particleDensity;

        for (let i = 0; i < count; i++) {
            this.particles.push(this.createParticle());
        }
    }

    createParticle() {
        return {
            x: Math.random() * window.innerWidth,
            y: window.innerHeight + Math.random() * 100,
            radius: Math.random() * 80 + 40,
            vx: (Math.random() - 0.5) * 0.5,
            vy: -Math.random() * 0.8 - 0.2,
            opacity: Math.random() * 0.3 + 0.1,
            hue: Math.random() > 0.5 ? 280 : 130, // Purple or green haze
            life: Math.random()
        };
    }

    updateParticles() {
        if (!this.settings.smokeEnabled) return;

        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];

            p.x += p.vx + Math.sin(p.life * 2) * 0.3;
            p.y += p.vy;
            p.life += 0.002;
            p.opacity = Math.max(0, p.opacity - 0.001);

            // Reset particle if it goes off screen or fades out
            if (p.y < -p.radius || p.opacity <= 0) {
                this.particles[i] = this.createParticle();
            }
        }
    }

    renderParticles() {
        if (!this.smokeCtx || !this.settings.smokeEnabled) {
            if (this.smokeCanvas) this.smokeCanvas.style.display = 'none';
            return;
        }

        this.smokeCanvas.style.display = 'block';
        this.smokeCtx.clearRect(0, 0, this.smokeCanvas.width, this.smokeCanvas.height);

        for (const p of this.particles) {
            const gradient = this.smokeCtx.createRadialGradient(
                p.x, p.y, 0,
                p.x, p.y, p.radius
            );

            gradient.addColorStop(0, `hsla(${p.hue}, 50%, 50%, ${p.opacity})`);
            gradient.addColorStop(0.5, `hsla(${p.hue}, 40%, 40%, ${p.opacity * 0.5})`);
            gradient.addColorStop(1, `hsla(${p.hue}, 30%, 30%, 0)`);

            this.smokeCtx.fillStyle = gradient;
            this.smokeCtx.beginPath();
            this.smokeCtx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.smokeCtx.fill();
        }
    }

    // ============================================
    // PSYCHEDELIC COLOR TRANSITIONS
    // ============================================
    updateColorTransitions() {
        if (!this.settings.colorTransitionsEnabled) return;

        this.colorPhase += 0.002;

        const hue1 = (280 + Math.sin(this.colorPhase) * 30) % 360;
        const hue2 = (130 + Math.cos(this.colorPhase * 0.7) * 20) % 360;
        const hue3 = (45 + Math.sin(this.colorPhase * 1.3) * 15) % 360;

        document.documentElement.style.setProperty('--haze-deep', `hsl(${hue1}, 76%, 32%)`);
        document.documentElement.style.setProperty('--haze-main', `hsl(${hue1 + 10}, 61%, 66%)`);
        document.documentElement.style.setProperty('--haze-leaf', `hsl(${hue2}, 67%, 58%)`);
    }

    // ============================================
    // VINYL RECORD ANIMATION
    // ============================================
    createVinylRecord() {
        const container = document.createElement('div');
        container.id = 'vinyl-record';
        container.innerHTML = `
            <div class="vinyl-disc">
                <div class="vinyl-label">
                    <div class="vinyl-label-text">G&M</div>
                </div>
                <div class="vinyl-grooves"></div>
            </div>
            <div class="vinyl-arm"></div>
        `;
        // Hide by default if disabled in settings
        if (!this.settings.vinylAnimationEnabled) {
            container.style.display = 'none';
        }
        document.body.appendChild(container);

        this.vinylElement = container;
    }

    updateVinylAnimation() {
        if (!this.settings.vinylAnimationEnabled || !this.vinylElement) return;

        const disc = this.vinylElement.querySelector('.vinyl-disc');
        if (!disc) return;

        if (this.isPlaying) {
            this.vinylAngle += 2;
            disc.style.transform = `rotate(${this.vinylAngle}deg)`;
            this.vinylElement.classList.add('playing');
        } else {
            this.vinylElement.classList.remove('playing');
        }
    }

    // ============================================
    // TRICHOME SPARKLE EFFECTS
    // ============================================
    createTrichomeContainer() {
        const container = document.createElement('div');
        container.id = 'trichome-sparkles';
        document.body.appendChild(container);

        this.trichomeContainer = container;

        // Create initial sparkles
        this.createSparkles();
    }

    createSparkles() {
        if (!this.trichomeContainer) return;

        // Clear existing sparkles
        this.trichomeContainer.innerHTML = '';

        if (!this.settings.trichomeSparklesEnabled) return;

        const sparkleCount = 50;

        for (let i = 0; i < sparkleCount; i++) {
            const sparkle = document.createElement('div');
            sparkle.className = 'trichome-sparkle';
            sparkle.style.cssText = `
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation-delay: ${Math.random() * 3}s;
                animation-duration: ${2 + Math.random() * 2}s;
            `;
            this.trichomeContainer.appendChild(sparkle);
        }
    }

    // ============================================
    // CRT SCANLINE OVERLAY
    // ============================================
    createCRTOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'crt-overlay';
        overlay.className = this.settings.crtOverlayEnabled ? 'active' : '';
        document.body.appendChild(overlay);

        this.crtOverlay = overlay;
    }

    toggleCRT(enabled) {
        this.settings.crtOverlayEnabled = enabled;
        if (this.crtOverlay) {
            this.crtOverlay.classList.toggle('active', enabled);
        }
        this.saveSettings();
    }

    // ============================================
    // SETTINGS PANEL
    // ============================================
    createSettingsPanel() {
        const panel = document.createElement('div');
        panel.id = 'effects-settings-panel';
        panel.innerHTML = `
            <button class="effects-toggle-btn" title="Visual Effects">
                <span class="effects-icon">&#10024;</span>
            </button>
            <div class="effects-menu">
                <div class="effects-menu-header">Visual Effects</div>
                <label class="effect-option">
                    <input type="checkbox" id="effect-smoke" ${this.settings.smokeEnabled ? 'checked' : ''}>
                    <span>Smoke Effects</span>
                </label>
                <label class="effect-option">
                    <input type="checkbox" id="effect-colors" ${this.settings.colorTransitionsEnabled ? 'checked' : ''}>
                    <span>Color Transitions</span>
                </label>
                <label class="effect-option">
                    <input type="checkbox" id="effect-vinyl" ${this.settings.vinylAnimationEnabled ? 'checked' : ''}>
                    <span>Vinyl Animation</span>
                </label>
                <label class="effect-option">
                    <input type="checkbox" id="effect-sparkles" ${this.settings.trichomeSparklesEnabled ? 'checked' : ''}>
                    <span>Trichome Sparkles</span>
                </label>
                <label class="effect-option">
                    <input type="checkbox" id="effect-crt" ${this.settings.crtOverlayEnabled ? 'checked' : ''}>
                    <span>CRT Scanlines</span>
                </label>
            </div>
        `;
        document.body.appendChild(panel);

        // Bind events
        const toggleBtn = panel.querySelector('.effects-toggle-btn');
        const menu = panel.querySelector('.effects-menu');

        toggleBtn.addEventListener('click', () => {
            menu.classList.toggle('open');
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!panel.contains(e.target)) {
                menu.classList.remove('open');
            }
        });

        // Bind checkbox events
        panel.querySelector('#effect-smoke').addEventListener('change', (e) => {
            this.settings.smokeEnabled = e.target.checked;
            this.saveSettings();
            if (!e.target.checked && this.smokeCtx) {
                this.smokeCtx.clearRect(0, 0, this.smokeCanvas.width, this.smokeCanvas.height);
            }
        });

        panel.querySelector('#effect-colors').addEventListener('change', (e) => {
            this.settings.colorTransitionsEnabled = e.target.checked;
            this.saveSettings();
            if (!e.target.checked) {
                // Reset to default colors
                document.documentElement.style.setProperty('--haze-deep', '#6D28D9');
                document.documentElement.style.setProperty('--haze-main', '#8B5CF6');
                document.documentElement.style.setProperty('--haze-leaf', '#4ADE80');
            }
        });

        panel.querySelector('#effect-vinyl').addEventListener('change', (e) => {
            this.settings.vinylAnimationEnabled = e.target.checked;
            this.saveSettings();
            if (this.vinylElement) {
                this.vinylElement.style.display = e.target.checked ? 'block' : 'none';
            }
        });

        panel.querySelector('#effect-sparkles').addEventListener('change', (e) => {
            this.settings.trichomeSparklesEnabled = e.target.checked;
            this.saveSettings();
            this.createSparkles();
        });

        panel.querySelector('#effect-crt').addEventListener('change', (e) => {
            this.toggleCRT(e.target.checked);
        });
    }

    // ============================================
    // MUSIC SYNC
    // ============================================
    bindMusicEvents() {
        // Listen for Webamp play/pause events
        const checkWebamp = setInterval(() => {
            if (window.webamp) {
                clearInterval(checkWebamp);

                // Subscribe to media status
                window.webamp.onTrackDidChange((track) => {
                    this.isPlaying = true;
                });

                // Check playing state periodically
                setInterval(() => {
                    if (window.webamp && window.webamp.store) {
                        const state = window.webamp.store.getState();
                        this.isPlaying = state?.media?.status === 'PLAYING';
                    }
                }, 500);
            }
        }, 1000);
    }

    // ============================================
    // ANIMATION LOOP
    // ============================================
    startAnimationLoop() {
        if (this.animationFrameId) return;

        const animate = () => {
            this.updateParticles();
            this.renderParticles();
            this.updateColorTransitions();
            this.updateVinylAnimation();

            this.animationFrameId = requestAnimationFrame(animate);
        };

        animate();
    }

    stopAnimationLoop() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    // ============================================
    // PUBLIC API
    // ============================================
    setMusicPlaying(playing) {
        this.isPlaying = playing;
    }

    toggleEffect(effectName, enabled) {
        const effectMap = {
            'smoke': 'smokeEnabled',
            'colors': 'colorTransitionsEnabled',
            'vinyl': 'vinylAnimationEnabled',
            'sparkles': 'trichomeSparklesEnabled',
            'crt': 'crtOverlayEnabled'
        };

        if (effectMap[effectName]) {
            this.settings[effectMap[effectName]] = enabled;
            this.saveSettings();
        }
    }
}

// Initialize on load
window.visualEffects = new VisualEffectsManager();
