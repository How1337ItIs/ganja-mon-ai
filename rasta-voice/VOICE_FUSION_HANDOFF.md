# VOICE FUSION PROJECT - Handoff for Cursor

**Goal:** Create custom "Funny Ganja Rasta Mon" ElevenLabs voice by fusing cartoonish/funny Jamaican character voices

**Target:** 30 minutes - 3 hours of clean audio for ElevenLabs Professional Voice Cloning

---

## CURRENT STATUS (as of 2026-01-24)

### ✅ SUCCESSFULLY DOWNLOADED:

| Source | File | Size | Quality | Notes |
|--------|------|------|---------|-------|
| **Rastamouse** | `rastamouse_Rastamouse Series 1.mp3` | 7.8MB | Good | BBC kids show - friendly, cartoonish |
| **Little Jacob (GTA IV)** | `little_jacob_All Little Jacob Cutscenes.mp3` | 11MB | Excellent | Funny gaming character - PERFECT! |
| **Hermes Conrad** | `hermes_Futurama Hermes' Curry Goat.mp3` | 584KB | Good | Short clip - need MORE |
| **Hermes Conrad** | `hermes_My Manwich!.mp3` | 700KB | Good | Short clip - need MORE |

**Total so far:** ~20MB audio (~10-15 minutes estimated)

**NEED:** 15-165 more minutes of audio!

---

## 🎯 PRIORITY DOWNLOADS NEEDED:

### HIGH PRIORITY (Cartoonish/Funny):

1. **More Hermes Conrad (Futurama)**
   - Search: "Hermes Conrad Futurama compilation"
   - Search: "Phil LaMarr Hermes best moments"
   - Search: "Futurama Hermes episode clips"
   - **Target:** 10-15 minutes of Phil LaMarr as Hermes

2. **More Rastamouse Episodes**
   - [Internet Archive - Season 1](https://archive.org/details/rastamouse-da-rhymin-teef)
   - Search for Season 2 and 3
   - **Target:** 20-30 minutes total

3. **Coolie Ranx Interviews** (Little Jacob voice actor)
   - [YouTube: The VŌC Podcast // Coolie Ranx Interview](https://www.youtube.com/watch?v=TSQmKtfzfg0)
   - Search: "Coolie Ranx interview"
   - **Target:** 15-20 minutes (his REAL voice doing the accent)

### MEDIUM PRIORITY (Authentic Base):

4. **Bob Marley Interviews**
   - Original URLs were unavailable, find alternatives:
   - Search: "Bob Marley interview 1979"
   - Search: "Bob Marley speaks interview"
   - [Spotify: Bob Marley Interviews compilation](https://open.spotify.com/album/00dJxx0qAkpU02A8OZvh82)
   - **Target:** 10-15 minutes of interview audio (NOT music!)

5. **Lee "Scratch" Perry**
   - Search: "Lee Scratch Perry interview"
   - Search: "Lee Perry speaking documentary"
   - **Target:** 10 minutes (for wild character energy)

### LOWER PRIORITY (Additional Character):

6. **Mutabaruka** (Dub poet - powerful delivery)
   - Search: "Mutabaruka dub poetry performance"
   - Search: "Mutabaruka speaks interview"

7. **Burning Spear Interviews**
   - Deep, deliberate cadence

---

## ❌ DOWNLOAD ISSUES ENCOUNTERED:

### YouTube 403 Errors:
- Bob Marley interview URLs from `voice_sources.json` are unavailable
- Some Hermes clips got 403 Forbidden
- **Solution:** Use yt-dlp with cookies or try alternative URLs

### Missing JavaScript Runtime:
- yt-dlp needs deno/node for some YouTube videos
- **Fix:** Install deno or use `--js-runtimes` flag

---

## 🔧 NEXT STEPS FOR CURSOR:

1. **Download more Hermes Conrad clips** (priority #1)
   - Find 5-10 compilations on YouTube
   - Extract audio to `voice_samples/hermes/`

2. **Download Coolie Ranx podcast** (The VŌC Podcast)
   - This is his REAL voice doing Little Jacob accent
   - High quality for voice cloning

3. **Find working Bob Marley interview links**
   - Replace unavailable URLs in voice_sources.json
   - Focus on SPEAKING interviews, not music

4. **Download Lee Scratch Perry**
   - Interviews and documentary clips

5. **Once we have 30+ minutes total:**
   - Run `build_voice_sample_dataset.py` to clean/segment
   - Prepare for ElevenLabs PVC upload

---

## 📋 VOICE CLONING REQUIREMENTS (ElevenLabs PVC):

- **Minimum:** 30 minutes clean audio
- **Optimal:** 3 hours
- **Format:** MP3 192kbps+ or WAV
- **Quality:** Clean, no background noise, single speaker per file
- **Content:** Expressive, emotional range, laughter, various moods

---

## 🎤 FUSION VOICE RECIPE:

**40%** - Little Jacob + Hermes (cartoonish, funny, gaming/TV energy)
**30%** - Rastamouse (friendly, kids show charm)
**20%** - Bob Marley (authentic credibility)
**10%** - Lee Scratch Perry (wild character, unpredictability)

---

## 📂 FILE LOCATIONS:

**Samples:** `/mnt/c/Users/natha/sol-cannabis/rasta-voice/voice_samples/`
**Scripts:**
- `build_voice_sample_dataset.py` - Clean and segment audio
- `clone_voice.py` - Upload to ElevenLabs
- `voice_sources.json` - Source manifest

**Windows Path:** `C:\Users\natha\sol-cannabis\rasta-voice\voice_samples\`

---

## ✅ COMPLETION CHECKLIST:

- [ ] 30+ minutes of cartoonish/funny samples (Hermes, Rastamouse, Little Jacob)
- [ ] 10+ minutes of authentic samples (Bob Marley)
- [ ] All audio cleaned (no music, no background noise)
- [ ] Segmented into 20-second clips
- [ ] Uploaded to ElevenLabs PVC
- [ ] Custom voice ID obtained
- [ ] Tested with improved system prompt

---

**Current Progress:** 10-15 minutes / 30 minutes minimum (~40% complete)

**Cursor - please help download MORE funny/cartoonish samples!** 🎤🌿
