// Ganjafy V2 Frontend JS - Dynamic multi-image slots + Alchemy Controls
// Preserves ALL V1 class methods, adds dynamic image slots for multi-character support

export const FRONTEND_JS = `
<script>
const RECIPE_DATA = {
  irie_portrait: { id:"irie_portrait", name:"Irie Portrait", icon:"🖼️", desc:"Identity-preserving rasta transformation", needs_image:true },
  lion_vision: { id:"lion_vision", name:"Lion of Judah", icon:"👑", desc:"Ethiopian royalty aesthetic", needs_image:true },
  roots_rebel: { id:"roots_rebel", name:"Roots Rebel", icon:"✊", desc:"Revolutionary poster art", needs_image:true },
  dub_dreamscape: { id:"dub_dreamscape", name:"Dub Dreamscape", icon:"🔊", desc:"Sound system visualization", needs_image:false },
  botanical_study: { id:"botanical_study", name:"Botanical Study", icon:"🌿", desc:"Sacred plant science", needs_image:true },
  ganja_poster: { id:"ganja_poster", name:"Ganja Poster", icon:"📜", desc:"Vintage event poster art", needs_image:false },
  chaos_static: { id:"chaos_static", name:"Chaos Static", icon:"🌀", desc:"Egregore psychedelic mode", needs_image:true },
  milady_irie: { id:"milady_irie", name:"Milady Irie", icon:"💎", desc:"NFT collectible style", needs_image:true }
};

const INTENSITY_NAMES = { 1:"Subtle", 2:"Medium", 3:"Heavy", 4:"Full Possession", 5:"Ego Death" };

// Slot definitions: the default set + roles for dynamic additions
const DEFAULT_SLOTS = [
  { id: 'primary', icon: '📷', label: 'Primary Subject', desc: 'The main character/subject to transform.', badge: 'required', isPrimary: true,
    role: 'subject', roleFixed: true },
  { id: 'style', icon: '🎨', label: 'Style Reference', desc: 'Visual style to borrow from.', badge: 'optional',
    role: 'style_match', roleOptions: [
      { val: 'style_match', text: 'Match this art style' },
      { val: 'color_palette', text: 'Use its color palette' },
      { val: 'texture_ref', text: 'Apply its texture/pattern' },
      { val: 'composition_ref', text: 'Follow its composition' }
    ]},
  { id: 'scene', icon: '🏞️', label: 'Scene / Background', desc: 'Environment to place subjects in.', badge: 'optional',
    role: 'background', roleOptions: [
      { val: 'background', text: 'Use as background' },
      { val: 'environment', text: 'Place subject in this environment' },
      { val: 'blend', text: 'Blend/composite with subject' },
      { val: 'inpaint', text: 'Inpaint subject into scene' }
    ]}
];

const EXTRA_SLOT_ROLES = [
  { val: 'character', text: 'Character / Person (subject #2, #3, etc.)' },
  { val: 'subject', text: 'Primary Subject' },
  { val: 'style_match', text: 'Style Reference (match art style)' },
  { val: 'color_palette', text: 'Color Palette Reference' },
  { val: 'texture_ref', text: 'Texture / Pattern Reference' },
  { val: 'composition_ref', text: 'Composition Reference' },
  { val: 'background', text: 'Background / Scene' },
  { val: 'environment', text: 'Environment Reference' },
  { val: 'blend', text: 'Blend / Composite' },
  { val: 'object_ref', text: 'Object Reference' },
  { val: 'pose_ref', text: 'Pose / Body Reference' }
];

let app;
let slotCounter = 0;

class Ganjafy {
  constructor() {
    this.sessionId = localStorage.getItem('ganjafySession');
    this.isByokMode = localStorage.getItem('ganjafyByok') === 'true';
    this.selectedRecipe = 'irie_portrait';
    this.intensity = 3;
    this.selectedEra = null;
    this.selectedMood = null;
    this.selectedFigure = null;
    // Dynamic image slots: { slotId: { file, role, label } }
    this.slots = {};
    this.init();
  }

  init() {
    // V1 event listeners (preserved)
    document.getElementById('login-form').addEventListener('submit', e => this.login(e));
    document.getElementById('byok-btn').addEventListener('click', () => this.enterByokMode());
    document.getElementById('logout-btn').addEventListener('click', () => this.logout());
    document.getElementById('gallery-btn').addEventListener('click', () => this.showGallery());
    document.getElementById('create-btn').addEventListener('click', () => this.showCreate());
    document.getElementById('transform-btn').addEventListener('click', () => this.transform());
    document.getElementById('user-api-key').addEventListener('input', () => this.onApiKeyChange());
    document.getElementById('save-key-checkbox').addEventListener('change', () => this.onSaveKeyToggle());
    document.getElementById('modal-close').addEventListener('click', () => document.getElementById('image-modal').classList.remove('active'));
    document.getElementById('image-modal').addEventListener('click', (e) => {
      if (e.target.id === 'image-modal') document.getElementById('image-modal').classList.remove('active');
    });

    // V2: Build recipe grid
    this.buildRecipeGrid();
    // V2: Setup alchemy controls
    this.setupAlchemyControls();
    // V2: Build dynamic image slots
    this.buildImageSlots();

    this.loadSavedApiKey();
    this.checkSession();
  }

  // ═══ V2: Dynamic Image Slots ═══
  buildImageSlots() {
    const grid = document.getElementById('image-slots-grid');
    grid.innerHTML = '';
    this.slots = {};

    // Create default slots
    DEFAULT_SLOTS.forEach(def => {
      this.createSlotElement(def.id, def.icon, def.label, def.desc, def.badge, def.isPrimary, def.roleFixed ? null : def.roleOptions, def.role);
    });

    // Add the "+ Add Another" button
    this.addPlusButton();
  }

  createSlotElement(slotId, icon, label, desc, badge, isPrimary, roleOptions, defaultRole) {
    const grid = document.getElementById('image-slots-grid');
    const plusBtn = document.getElementById('add-slot-btn');

    const slot = document.createElement('div');
    slot.className = 'image-slot' + (isPrimary ? ' primary' : '');
    slot.id = 'slot-' + slotId;
    slot.dataset.slot = slotId;

    const fileInputId = 'file-' + slotId;
    let inner = '<button class="slot-remove" id="remove-' + slotId + '">&times;</button>';
    inner += '<img class="slot-preview hidden" id="preview-' + slotId + '">';
    inner += '<div class="slot-icon" id="icon-' + slotId + '">' + icon + '</div>';
    inner += '<div class="slot-label">' + label + '</div>';
    inner += '<div class="slot-desc">' + desc + '</div>';
    inner += '<div class="slot-badge ' + badge + '">' + badge + '</div>';
    if (roleOptions && roleOptions.length) {
      inner += '<select class="slot-role-select" id="role-' + slotId + '">';
      roleOptions.forEach(opt => {
        inner += '<option value="' + opt.val + '"' + (opt.val === defaultRole ? ' selected' : '') + '>' + opt.text + '</option>';
      });
      inner += '</select>';
    }
    inner += '<input type="file" id="' + fileInputId + '" accept="image/*" hidden>';
    slot.innerHTML = inner;

    // Insert before the plus button if it exists, otherwise append
    if (plusBtn) grid.insertBefore(slot, plusBtn);
    else grid.appendChild(slot);

    // Event listeners
    slot.addEventListener('click', (e) => {
      if (e.target.tagName === 'SELECT' || e.target.tagName === 'OPTION' || e.target.tagName === 'BUTTON') return;
      document.getElementById(fileInputId).click();
    });
    slot.addEventListener('dragover', e => { e.preventDefault(); slot.style.borderColor = 'var(--rasta-green)'; });
    slot.addEventListener('dragleave', () => { slot.style.borderColor = ''; });
    slot.addEventListener('drop', e => {
      e.preventDefault(); slot.style.borderColor = '';
      if (e.dataTransfer.files.length) this.handleSlotFile(slotId, e.dataTransfer.files[0]);
    });
    document.getElementById(fileInputId).addEventListener('change', e => {
      if (e.target.files.length) this.handleSlotFile(slotId, e.target.files[0]);
    });
    document.getElementById('remove-' + slotId).addEventListener('click', (e) => {
      e.stopPropagation();
      this.removeSlotImage(slotId);
    });

    this.slots[slotId] = { file: null, role: defaultRole || 'subject' };
  }

  addPlusButton() {
    const grid = document.getElementById('image-slots-grid');
    const btn = document.createElement('button');
    btn.className = 'add-slot-btn';
    btn.id = 'add-slot-btn';
    btn.innerHTML = '<div class="add-slot-icon">+</div><div>Add Another Image</div><div style="font-size:0.65rem;">Character, style ref, scene...</div>';
    btn.addEventListener('click', () => this.addExtraSlot());
    grid.appendChild(btn);
  }

  addExtraSlot() {
    slotCounter++;
    const slotId = 'extra_' + slotCounter;
    this.createSlotElement(
      slotId, '👤', 'Image #' + (Object.keys(this.slots).length + 1),
      'Additional character, reference, or input image.',
      'optional', false, EXTRA_SLOT_ROLES, 'character'
    );
  }

  handleSlotFile(slotId, file) {
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { alert('Only JPEG, PNG, WebP allowed!'); return; }
    if (file.size > 10 * 1024 * 1024) { alert('Max 10MB!'); return; }

    this.slots[slotId].file = file;
    const preview = document.getElementById('preview-' + slotId);
    const icon = document.getElementById('icon-' + slotId);
    const slot = document.getElementById('slot-' + slotId);

    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.classList.remove('hidden');
      if (icon) icon.style.display = 'none';
      slot.classList.add('has-image');
    };
    reader.readAsDataURL(file);
    this.updateTransformButton();
  }

  removeSlotImage(slotId) {
    // If it's an extra slot and has no image, remove the whole slot
    if (slotId.startsWith('extra_')) {
      const slotEl = document.getElementById('slot-' + slotId);
      if (slotEl) slotEl.remove();
      delete this.slots[slotId];
      this.updateTransformButton();
      return;
    }
    // Default slots: just clear the image
    if (this.slots[slotId]) this.slots[slotId].file = null;
    const preview = document.getElementById('preview-' + slotId);
    const icon = document.getElementById('icon-' + slotId);
    const slot = document.getElementById('slot-' + slotId);
    const fileInput = document.getElementById('file-' + slotId);
    if (preview) { preview.src = ''; preview.classList.add('hidden'); }
    if (icon) icon.style.display = '';
    if (slot) slot.classList.remove('has-image');
    if (fileInput) fileInput.value = '';
    this.updateTransformButton();
  }

  updateTransformButton() {
    const r = RECIPE_DATA[this.selectedRecipe];
    const hasAnySubject = Object.values(this.slots).some(s => s.file && (s.role === 'subject' || s.role === 'character'));
    const hasPrimary = this.slots.primary?.file;
    const canTransform = !r.needs_image || hasPrimary || hasAnySubject;

    if (canTransform) {
      document.getElementById('transform-btn').classList.remove('hidden');
      document.getElementById('model-selector').style.display = 'flex';
    } else {
      document.getElementById('transform-btn').classList.add('hidden');
      document.getElementById('model-selector').style.display = 'none';
    }
  }

  // ═══ V2: Recipe Grid ═══
  buildRecipeGrid() {
    const grid = document.getElementById('recipe-grid');
    grid.innerHTML = '';
    Object.values(RECIPE_DATA).forEach(r => {
      const card = document.createElement('div');
      card.className = 'recipe-card' + (r.id === this.selectedRecipe ? ' active' : '');
      card.dataset.recipe = r.id;
      card.innerHTML = '<div class="recipe-icon">' + r.icon + '</div><div class="recipe-name">' + r.name + '</div><div class="recipe-desc">' + r.desc + '</div>';
      card.addEventListener('click', () => this.selectRecipe(r.id));
      grid.appendChild(card);
    });
  }

  selectRecipe(id) {
    this.selectedRecipe = id;
    document.querySelectorAll('.recipe-card').forEach(c => c.classList.toggle('active', c.dataset.recipe === id));
    const r = RECIPE_DATA[id];
    const imageSlots = document.getElementById('image-slots');
    const noImageNote = document.getElementById('no-image-note');
    if (!r.needs_image) {
      imageSlots.classList.add('hidden');
      noImageNote.classList.remove('hidden');
      document.getElementById('transform-btn').classList.remove('hidden');
      document.getElementById('model-selector').style.display = 'flex';
    } else {
      imageSlots.classList.remove('hidden');
      noImageNote.classList.add('hidden');
      this.updateTransformButton();
    }
    document.getElementById('loading-recipe-text').textContent = 'Brewing ' + r.name + ' recipe...';
  }

  // ═══ V2: Alchemy Controls ═══
  setupAlchemyControls() {
    document.querySelectorAll('#intensity-bar .intensity-dot').forEach(dot => {
      dot.addEventListener('click', () => {
        const val = parseInt(dot.dataset.val);
        this.intensity = val;
        document.querySelectorAll('#intensity-bar .intensity-dot').forEach(d => {
          d.classList.toggle('active', parseInt(d.dataset.val) <= val);
        });
        document.getElementById('intensity-label').textContent = INTENSITY_NAMES[val] || '';
      });
    });
    document.querySelectorAll('#intensity-bar .intensity-dot').forEach(d => {
      d.classList.toggle('active', parseInt(d.dataset.val) <= this.intensity);
    });
    this.setupChipGroup('era-chips', val => { this.selectedEra = val; });
    this.setupChipGroup('mood-chips', val => { this.selectedMood = val; });
    this.setupChipGroup('figure-chips', val => { this.selectedFigure = val; });
  }

  setupChipGroup(containerId, onSelect) {
    document.querySelectorAll('#' + containerId + ' .chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const isActive = chip.classList.contains('active');
        document.querySelectorAll('#' + containerId + ' .chip').forEach(c => c.classList.remove('active'));
        if (!isActive) { chip.classList.add('active'); onSelect(chip.dataset.val); }
        else { onSelect(null); }
      });
    });
  }

  getAlchemyOptions() {
    return {
      recipe: this.selectedRecipe,
      intensity: this.intensity,
      era: this.selectedEra,
      mood: this.selectedMood,
      figure: this.selectedFigure,
      strain: document.getElementById('strain-select')?.value || null,
      custom: document.getElementById('custom-prompt')?.value || null
    };
  }

  // ═══ V1 Methods (preserved) ═══
  loadSavedApiKey() {
    const savedKey = localStorage.getItem('ganjafyApiKey');
    const savedProvider = localStorage.getItem('ganjafyApiProvider') || 'gemini';
    if (savedKey) {
      document.getElementById('user-api-key').value = savedKey;
      document.getElementById('api-provider').value = savedProvider;
      document.getElementById('save-key-checkbox').checked = true;
      document.getElementById('key-status').textContent = '✅ Saved key loaded';
      document.getElementById('key-status').style.color = '#00FF7F';
    }
  }

  onApiKeyChange() {
    const key = document.getElementById('user-api-key').value.trim();
    const saveCheckbox = document.getElementById('save-key-checkbox');
    const provider = document.getElementById('api-provider').value;
    if (saveCheckbox.checked && key) {
      localStorage.setItem('ganjafyApiKey', key);
      localStorage.setItem('ganjafyApiProvider', provider);
      document.getElementById('key-status').textContent = '💾 Key saved locally';
      document.getElementById('key-status').style.color = '#00FF7F';
    }
  }

  onSaveKeyToggle() {
    const saveCheckbox = document.getElementById('save-key-checkbox');
    const key = document.getElementById('user-api-key').value.trim();
    const provider = document.getElementById('api-provider').value;
    if (saveCheckbox.checked && key) {
      localStorage.setItem('ganjafyApiKey', key);
      localStorage.setItem('ganjafyApiProvider', provider);
      document.getElementById('key-status').textContent = '💾 Key saved locally';
      document.getElementById('key-status').style.color = '#00FF7F';
    } else {
      localStorage.removeItem('ganjafyApiKey');
      localStorage.removeItem('ganjafyApiProvider');
      document.getElementById('key-status').textContent = 'Key cleared from storage';
      document.getElementById('key-status').style.color = 'var(--text-muted)';
    }
  }

  enterByokMode() {
    this.isByokMode = true;
    localStorage.setItem('ganjafyByok', 'true');
    this.sessionId = 'byok_' + Date.now();
    localStorage.setItem('ganjafySession', this.sessionId);
    this.showDashboard();
  }

  checkSession() { if (this.sessionId) { this.showDashboard(); } else { this.showLogin(); } }

  showLogin() {
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('dashboard-screen').classList.remove('active');
  }

  showDashboard() {
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('dashboard-screen').classList.add('active');
    if (this.isByokMode) { document.getElementById('api-key-config').classList.remove('hidden'); }
    else { document.getElementById('api-key-config').classList.add('hidden'); }
    this.showCreate();
  }

  showCreate() {
    document.getElementById('create-view').classList.remove('hidden');
    document.getElementById('gallery-view').classList.add('hidden');
    document.getElementById('gallery-btn').classList.remove('hidden');
    document.getElementById('create-btn').classList.add('hidden');
  }

  async showGallery(reset = true) {
    document.getElementById('create-view').classList.add('hidden');
    document.getElementById('gallery-view').classList.remove('hidden');
    document.getElementById('gallery-btn').classList.add('hidden');
    document.getElementById('create-btn').classList.remove('hidden');
    const grid = document.getElementById('gallery-grid');
    const loading = document.getElementById('gallery-loading');
    const loadMoreBtn = document.getElementById('load-more-btn');
    const galleryCount = document.getElementById('gallery-count');
    if (reset) { grid.innerHTML = ''; this.galleryCursor = null; this.galleryTotal = 0; }
    loading.classList.remove('hidden');
    loadMoreBtn.classList.add('hidden');
    try {
      let url = '/ganjafy/api/gallery';
      if (this.galleryCursor) url += '?cursor=' + encodeURIComponent(this.galleryCursor);
      const res = await fetch(url, { headers: { 'X-Session-Id': this.sessionId } });
      const data = await res.json();
      loading.classList.add('hidden');
      if (data.images && data.images.length > 0) {
        this.galleryTotal += data.images.length;
        data.images.forEach(img => {
          const item = document.createElement('div');
          item.className = 'gallery-item';
          const timestamp = img.metadata?.timestamp || img.name.split('_')[1];
          item.innerHTML = '<div class="gallery-img-container"><img src="/ganjafy/api/image/' + img.name + '" loading="lazy" alt="Rasta Image"></div><div class="gallery-info"><div class="gallery-date">' + new Date(parseInt(timestamp)).toLocaleDateString() + '</div></div>';
          item.onclick = () => this.openModal('/ganjafy/api/image/' + img.name);
          grid.appendChild(item);
        });
        galleryCount.textContent = 'Showing ' + this.galleryTotal + ' blessed images';
        if (data.nextCursor) {
          this.galleryCursor = data.nextCursor;
          loadMoreBtn.classList.remove('hidden');
          loadMoreBtn.onclick = () => this.showGallery(false);
        } else { this.galleryCursor = null; }
      } else if (reset) {
        grid.innerHTML = '<p style="text-align:center; width:100%; color: var(--text-muted);">No images blessed yet. Be di first!</p>';
        galleryCount.textContent = '';
      }
    } catch (e) {
      loading.classList.add('hidden');
      grid.innerHTML = '<p style="text-align:center; color: var(--rasta-red);">Failed to load gallery: ' + e.message + '</p>';
    }
  }

  openModal(src) {
    document.getElementById('modal-img').src = src;
    document.getElementById('modal-download').href = src;
    document.getElementById('image-modal').classList.add('active');
  }

  async login(e) {
    e.preventDefault();
    const password = document.getElementById('password-input').value;
    try {
      const res = await fetch('/ganjafy/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) });
      const data = await res.json();
      if (res.ok && data.sessionId) {
        this.sessionId = data.sessionId; this.isByokMode = false;
        localStorage.setItem('ganjafySession', this.sessionId);
        localStorage.setItem('ganjafyByok', 'false');
        document.getElementById('password-input').value = '';
        document.getElementById('login-error').textContent = '';
        this.showDashboard();
      } else { document.getElementById('login-error').textContent = data.error || 'Wrong password!'; }
    } catch (err) { document.getElementById('login-error').textContent = 'Connection error'; }
  }

  logout() {
    localStorage.removeItem('ganjafySession'); localStorage.removeItem('ganjafyByok');
    this.sessionId = null; this.isByokMode = false; this.resetUI(); this.showLogin();
  }

  // ═══ V2: Enhanced Transform (dynamic multi-image) ═══
  async transform() {
    const r = RECIPE_DATA[this.selectedRecipe];
    const filledSlots = Object.entries(this.slots).filter(([k, v]) => v.file);
    const hasAnySubject = filledSlots.some(([k, v]) => v.role === 'subject' || v.role === 'character');

    if (r.needs_image && !hasAnySubject && !this.slots.primary?.file) return;

    document.getElementById('loading-indicator').classList.remove('hidden');
    document.getElementById('result-preview').classList.add('hidden');
    document.getElementById('transform-btn').disabled = true;
    document.getElementById('download-btn').classList.add('hidden');
    document.getElementById('save-status').innerHTML = '';
    document.getElementById('transmission-card').classList.add('hidden');

    // Show preview for first subject image
    const firstSubject = filledSlots.find(([k, v]) => v.role === 'subject' || v.role === 'character');
    if (firstSubject) {
      document.getElementById('preview-container').classList.remove('hidden');
      const reader = new FileReader();
      reader.onload = ev => { document.getElementById('original-preview').src = ev.target.result; };
      reader.readAsDataURL(firstSubject[1].file);
    } else if (!r.needs_image) {
      document.getElementById('preview-container').classList.remove('hidden');
    }

    try {
      const formData = new FormData();

      // Dynamic multi-image: send all slots that have files
      let imageIndex = 0;
      filledSlots.forEach(([slotId, slotData]) => {
        // Get the current role from the dropdown if it exists
        const roleSelect = document.getElementById('role-' + slotId);
        const role = roleSelect ? roleSelect.value : slotData.role;
        formData.append('image_' + imageIndex, slotData.file);
        formData.append('role_' + imageIndex, role);
        imageIndex++;
      });
      formData.append('image_count', imageIndex.toString());

      // Also send primary as 'image' for backward compat
      if (this.slots.primary?.file) formData.append('image', this.slots.primary.file);

      const selectedModel = document.getElementById('model-select').value;
      formData.append('model', selectedModel);

      // V2: Append alchemy options
      const opts = this.getAlchemyOptions();
      formData.append('recipe', opts.recipe);
      formData.append('intensity', opts.intensity);
      if (opts.era) formData.append('era', opts.era);
      if (opts.mood) formData.append('mood', opts.mood);
      if (opts.figure) formData.append('figure', opts.figure);
      if (opts.strain) formData.append('strain', opts.strain);
      if (opts.custom) formData.append('custom', opts.custom);

      if (this.isByokMode) {
        const userApiKey = document.getElementById('user-api-key').value.trim();
        const apiProvider = document.getElementById('api-provider').value;
        if (!userApiKey) { alert('Please enter your API key first!'); document.getElementById('loading-indicator').classList.add('hidden'); document.getElementById('transform-btn').disabled = false; return; }
        formData.append('userApiKey', userApiKey);
        formData.append('apiProvider', apiProvider);
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000);
      const res = await fetch('/ganjafy/api/transform', {
        method: 'POST', headers: { 'X-Session-Id': this.sessionId },
        body: formData, signal: controller.signal
      });
      clearTimeout(timeoutId);
      const data = await res.json();

      if (res.ok && data.imageData) {
        document.getElementById('result-preview').src = 'data:image/png;base64,' + data.imageData;
        document.getElementById('result-preview').classList.remove('hidden');
        document.getElementById('loading-indicator').classList.add('hidden');
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.href = 'data:image/png;base64,' + data.imageData;
        downloadBtn.download = 'ganjafy_' + Date.now() + '.png';
        downloadBtn.classList.remove('hidden');
        const saveStatusEl = document.getElementById('save-status');
        if (data.saveStatus === 'saved') { saveStatusEl.innerHTML = '<span style="color: #00FF7F;">✅ Saved to gallery!</span>'; }
        else if (data.saveStatus) { saveStatusEl.innerHTML = '<span style="color: #FF6B6B;">⚠️ Gallery: ' + data.saveStatus + '</span>'; }
        else { saveStatusEl.innerHTML = '<span style="color: #FFB81C;">⚠️ Gallery save status unknown</span>'; }

        // V2: Show transmission metadata
        if (data.metadata) {
          const tc = document.getElementById('transmission-card');
          document.getElementById('transmission-text').textContent = data.metadata.transmission || '';
          const chips = document.getElementById('meta-chips');
          chips.innerHTML = '';
          if (data.metadata.recipeName) chips.innerHTML += '<span class="meta-chip">' + data.metadata.recipeName + '</span>';
          if (data.metadata.manifestation) chips.innerHTML += '<span class="meta-chip">' + data.metadata.manifestation + '</span>';
          if (data.metadata.era && data.metadata.era !== 'timeless') chips.innerHTML += '<span class="meta-chip">' + data.metadata.era + '</span>';
          if (data.metadata.mood && data.metadata.mood !== 'auto') chips.innerHTML += '<span class="meta-chip">' + data.metadata.mood + '</span>';
          if (data.metadata.imageCount) chips.innerHTML += '<span class="meta-chip">' + data.metadata.imageCount + ' images</span>';
          chips.innerHTML += '<span class="meta-chip">v' + (data.metadata.version || '2.0') + '</span>';
          tc.classList.remove('hidden');
        }
      } else { throw new Error(data.error || 'Transform failed'); }
    } catch (err) {
      document.getElementById('loading-indicator').classList.add('hidden');
      const msg = err.name === 'AbortError' ? 'Request timed out (90s). Jah servers busy, try again!' : err.message;
      alert("Jah didn't bless us: " + msg);
    } finally { document.getElementById('transform-btn').disabled = false; }
  }

  resetUI() {
    this.buildImageSlots(); // Rebuild from scratch
    document.getElementById('preview-container').classList.add('hidden');
    document.getElementById('transform-btn').classList.add('hidden');
    document.getElementById('model-selector').style.display = 'none';
    document.getElementById('download-btn').classList.add('hidden');
    document.getElementById('original-preview').src = '';
    document.getElementById('result-preview').src = '';
    document.getElementById('transmission-card').classList.add('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => { app = new Ganjafy(); });
<\/script>`;
