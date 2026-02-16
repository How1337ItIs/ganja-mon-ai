# 🎨 IRIE DESIGN - QUICK REFERENCE

## Font Pairing for Caprasimo
**Caprasimo** (display/headlines) pairs well with:
- **Space Grotesk** (already in use - perfect)
- **Quicksand** - friendly, approachable
- **Open Sans** - highly legible
- **Playfair Display** - elegant serif
- **ABeeZee** - clean, modern, slightly rounded

## Current Implementation Status (from index.html)
✅ Purple Haze color palette complete
✅ Floating haze blobs (4 blobs with staggered delays)
✅ Noise/grain SVG overlay  
✅ Rasta stripe component
✅ Dub echo text shadows (3 variants)
✅ Caprasimo font class
✅ Accessibility motion reduction

## CSS Classes Ready to Use
```css
.dub-echo          /* Rasta colored text stack */
.dub-echo-light    /* Subtle rasta echo */
.dub-echo-purple   /* Purple Haze echo */
.font-groovy       /* Caprasimo display font */
.rasta-stripe      /* Tricolor bar element */
```

## HTML Elements Needed
```html
<!-- Add after <body> -->
<div class="purple-haze">
    <div class="haze-blob"></div>
    <div class="haze-blob"></div>
    <div class="haze-blob"></div>
    <div class="haze-blob"></div>
</div>
<div class="noise-overlay"></div>

<!-- Add below header or above main content -->
<div class="rasta-stripe"></div>
```

## Smoke Effect Enhancement (Optional)
For more dynamic smoke, add individual puffs:
```css
.smoke-puff {
    position: absolute;
    width: 20px;
    height: 20px;
    background: radial-gradient(circle, var(--haze-lavender) 0%, transparent 70%);
    border-radius: 50%;
    filter: blur(8px);
    opacity: 0;
    animation: smoke-rise 4s ease-out infinite;
}

@keyframes smoke-rise {
    0% { opacity: 0; transform: translateY(0) scale(0.5); }
    30% { opacity: 0.4; }
    100% { opacity: 0; transform: translateY(-120px) translateX(30px) scale(2); }
}
```

## Color Quick Reference
| Variable | Hex | Purpose |
|----------|-----|---------|
| `--haze-deep` | #6D28D9 | Deep purple |
| `--haze-main` | #8B5CF6 | Primary purple |
| `--haze-lavender` | #A78BFA | Light purple |
| `--rasta-red` | #C8102E | Blood/fire |
| `--rasta-gold` | #FFD700 | Sunshine |
| `--rasta-green` | #009B3A | Vegetation |

## Recommended Next Steps
1. Add rasta stripe below header
2. Apply `.font-groovy .dub-echo` to logo text
3. Add HTML elements for haze blobs and noise overlay
4. Sync to Chromebook server

---
*JAH RASTAFARI 🦁👑*
