# 🌿 IRIE DESIGN BRIEF: Ganja Mon Rasta-Dub Aesthetic

**Date:** 2026-01-18
**Parallel Research by:** Antigravity (supporting Claude in vibes terminal)

---

## 🎨 CORE COLOR PALETTE

### Rasta Foundation (Ethiopian Flag)
| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Diablo Red** | `#D00F00` | 208, 15, 0 | Accents, CTAs, warnings |
| **Verse Green** | `#178C14` | 23, 140, 20 | Cannabis, growth, health |
| **Philippine Yellow/Gold** | `#FFCA00` | 255, 202, 0 | Highlights, badges, solar |
| **Deep Black** | `#0E0C0B` | 14, 12, 11 | Base backgrounds |

### Secondary Palette
| Name | Hex | Usage |
|------|-----|-------|
| Rasta Red (Alt) | `#C8102E` | Current site uses this |
| Rasta Green (Bright) | `#009B3A` | Neon vibes |
| Rasta Gold (Pure) | `#FFD700` | Current site uses this |
| Monad Purple | `#6E54FF` | Blockchain accent |

### Extended Dub Palette (For gradients/effects)
- **Dub Echo Blue**: `#85E6FF` (echo effect, delay vibes)
- **Herb Smoke**: `#4a4a6a` (atmospheric overlay)
- **Ganja Leaf Bright**: `#4ade80` (currently used)
- **Psychedelic Orange**: `#FF6B35` (dancehall energy)
- **Deep Roots Brown**: `#3D2914` (earthy grounding)

---

## 🔤 TYPOGRAPHY RECOMMENDATIONS

### Primary Font Stack
1. **Headlines**: Bold, expressive display fonts
   - Consider: **Bebas Neue**, **Righteous**, **Russo One**
   - Fallback: Current `Space Grotesk` (bold weight)
   
2. **Body Text**: Keep clean for legibility
   - Keep: `JetBrains Mono` for data
   - Keep: `Space Grotesk` for UI
   
3. **Accent/Cultural Text**: Hand-drawn or distressed
   - Consider loading: **Permanent Marker**, **Rye**, **Bungee**
   - Use sparingly for "IRIE", "JAH", "ONE LOVE" callouts

### Typography Effects
- **Stretched/Compressed** display text for headings
- **Outline/Stroke** text for contrast
- **Gradient fills** using Rasta colors
- **Subtle text-shadow** with glow effects

---

## 🎭 VISUAL MOTIFS & PATTERNS

### Essential Elements
1. **Lion of Judah** - Power, Rastafari, sovereignty
2. **Cannabis Leaf** - Already have great logo
3. **Ethiopian Star** - Cultural heritage
4. **Soundsystem Speaker Stacks** - Dub culture
5. **Echo/Delay Waves** - Visual representation of dub effect
6. **Sun Rays** - Radial golden emanations

### Pattern Types
- **Repeating cannabis leaf patterns** (subtle, watermark style)
- **Rasta stripe bands** (horizontal or diagonal)
- **Concentric circles** (soundwave/echo)
- **Geometric African patterns** (Kente-inspired)
- **Halftone dots** (vintage poster aesthetic)

### Texture Overlays
- **Noise/grain** (vintage warmth)
- **Paper texture** (hand-made feel)
- **VHS/distortion lines** (dub production aesthetic)
- **Smoke/haze effects** (atmospheric)

---

## 🌊 ANIMATION & MICRO-INTERACTIONS

### Dub-Inspired Effects
1. **Echo Pulse** - Elements that "pulse" outward like echo
2. **Delay Fade** - Multiple ghost copies with delay
3. **Vinyl Wobble** - Subtle rotation/wobble
4. **Bass Drop** - Scale bounce on interactions
5. **Smoke Drift** - Floating particle animations

### Implementation Ideas
```css
/* Echo Pulse Animation */
@keyframes echo-pulse {
  0% { box-shadow: 0 0 0 0 var(--rasta-green); }
  70% { box-shadow: 0 0 0 20px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}

/* Delay Ghost Effect */
@keyframes delay-ghost {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; filter: blur(2px); }
}

/* Bass Drop Bounce */
@keyframes bass-drop {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

/* Smoke Drift */
@keyframes smoke-drift {
  0% { transform: translateY(0) translateX(0); opacity: 0.6; }
  100% { transform: translateY(-50px) translateX(20px); opacity: 0; }
}
```

---

## 🖼️ LAYOUT CONCEPTS

### Hero Section Ideas
1. **Rasta Stripe Header** - Horizontal bands of red/yellow/green
2. **Soundsystem Stack** - Tower of speakers as visual metaphor
3. **Dub Studio Console** - Vintage mixing board aesthetic
4. **Tropical Paradise** - Palm leaves, sun rays, ganja

### Card Styles
- **Glassmorphism** with Rasta color tints
- **Thick borders** in Rasta colors
- **Gradient backgrounds** (subtle red→yellow→green)
- **Vinyl record** shaped circular cards

### Footer/Bottom
- **Roots/smoke rising** from bottom
- **Record label** style circular badge
- **Sound wave** visualization

---

## 🎧 DUB AESTHETIC DEEP DIVE

### Lee Scratch Perry / King Tubby Era
- Marvel Comics-style distorted lettering
- Tribal/African primitivism imagery
- Comic book arrows and diagrams
- "Talismanic spookiness"
- Deliberate rawness

### Jamaican Dancehall Poster Style
- Hand-painted DIY aesthetic
- Chaotic but energetic color mixing
- Mixed typography (graffiti + bubble + stencil)
- Animated/swirling text
- Patois phrases and cultural references

### Modern Dub/Reggae Fusion
- Clean dark backgrounds
- Neon accent colors
- Parallax scrolling
- 3D elements and depth
- Immersive video backgrounds

---

## 🚀 IMPLEMENTATION PRIORITY

### Phase 1: Quick Wins (CSS Only)
1. Update color variables with richer Rasta palette
2. Add Rasta stripe accent elements
3. Add subtle pattern backgrounds (CSS gradients)
4. Enhance glow effects with gold/green

### Phase 2: Typography & Texture
1. Load display font for headlines
2. Add noise/grain overlay
3. Implement echo-pulse animations
4. Add smoke particle effects

### Phase 3: Layout Evolution
1. Redesign header with Rasta band
2. Add dub-style section transitions
3. Implement glassmorphism cards
4. Add Lion of Judah/cultural elements

### Phase 4: Full Irie Mode
1. Custom illustrations
2. Sound-reactive animations
3. Vintage poster sections
4. Immersive scrolling experience

---

## 📚 REFERENCE SOURCES

- **Color Codes**: flagcolorcodes.com, schemecolor.com, Adobe Color
- **Design Inspiration**: Dribbble (Rasta/Reggae tags), Behance
- **Typography**: Google Fonts, Font Squirrel
- **Dancehall Posters**: itsnicethat.com, islandoriginsmag.com
- **Dub History**: Smashing Magazine (album cover analysis)
- **Modern Cannabis UI**: Dribbble cannabis/dispensary designs

---

## 💡 KEY DESIGN PRINCIPLES

1. **IRIE OVER POLISHED** - Embrace rawness and authenticity
2. **RESPECT THE CULTURE** - Rasta colors have meaning (green=earth, gold=wealth, red=blood of martyrs)
3. **DUB = SPACE** - Let elements breathe, use negative space like echo
4. **ORGANIC CHAOS** - Not everything needs to be perfectly aligned
5. **BASS PRESENCE** - Heavy, grounded elements that anchor the design
6. **ONE LOVE** - Cohesive despite variety, unity in diversity

---

**JAH RASTAFARI 🦁👑**
