# Ganja Mon Character Image Prompts

## Files Created
- ✅ `ganja_mon_conversation.wav` (13MB, original)
- ✅ `ganja_mon_conversation.mp3` (1.7MB, compressed)
- Duration: 2 minutes 17 seconds

---

## Character 1: Ganja Mon (Operator/Host)

### Midjourney Prompt
```
Portrait of a wise Jamaican Rasta AI character named Ganja Mon, friendly smile, long dreadlocks with red gold and green beads, warm brown skin, kind eyes, wearing colorful traditional Rasta clothing with cannabis leaf patterns, tech-forward vibe mixing traditional and futuristic elements, green and gold color scheme, headshot portrait style, professional lighting, neutral background, 4K, highly detailed, friendly and approachable expression --ar 1:1 --style raw
```

### Alternative Styles
**Animated/Cartoon:**
```
3D animated character, Jamaican Rasta man with dreadlocks, friendly cartoon style, wearing colorful shirt with cannabis motifs, big warm smile, Pixar-style rendering, vibrant colors (green, gold, red), tech-savvy look, headshot portrait, neutral gradient background --ar 1:1 --v 6
```

**Photorealistic:**
```
Professional headshot portrait, Jamaican man with long dreadlocks, traditional Rasta tam hat, wise and friendly expression, tech entrepreneur aesthetic, 40s, warm lighting, blurred background, cannabis cultivation expert, approachable demeanor, 8K photography, Canon EOS R5 --ar 1:1
```

---

## Character 2: Natural Guest (Response Speaker)

### Midjourney Prompt
```
Portrait of a natural Jamaican Rasta speaker, genuine smile, medium-length dreadlocks with natural styling, warm dark skin, authentic traditional Rasta clothing, red gold green color accents, welcoming and knowledgeable expression, cannabis cultivation enthusiast, headshot portrait, professional lighting, neutral background, 4K, highly detailed --ar 1:1 --style raw
```

### Alternative Styles
**Animated/Cartoon:**
```
3D animated character, young Jamaican Rasta with natural locs, enthusiastic friendly expression, casual colorful style, excited listener pose, Pixar-style rendering, vibrant warm colors, authentic vibe, headshot portrait, neutral gradient background --ar 1:1 --v 6
```

**Photorealistic:**
```
Professional headshot portrait, young Jamaican man with natural dreadlocks, authentic traditional dress, enthusiastic expression, cannabis enthusiast, 30s, natural lighting, blurred green background, genuine and engaged demeanor, 8K photography --ar 1:1
```

---

## Quick Generation Options

### DALL-E 3 Prompts (Free with ChatGPT Plus)

**Ganja Mon:**
```
Create a friendly portrait of a Jamaican Rasta character with long dreadlocks decorated with colorful beads (red, gold, green), warm smile, wearing traditional Rasta clothing with a modern tech-forward twist. The character should look wise, approachable, and knowledgeable about AI and cannabis cultivation. Vibrant colors, professional lighting, neutral background. Portrait orientation.
```

**Natural Guest:**
```
Create a portrait of an authentic Jamaican Rasta speaker with natural dreadlocks, genuine friendly smile, wearing traditional Rasta clothing with red, gold, and green colors. The character should look enthusiastic, knowledgeable about cannabis, and engaged in conversation. Vibrant natural colors, professional lighting, neutral background. Portrait orientation.
```

---

## Using With AI Video Platforms

### Hedra (Character.ai + Animation)
1. Go to: https://hedra.com
2. Upload character image (generate from prompts above)
3. Upload audio: `ganja_mon_conversation.mp3`
4. NOTE: Max 60 seconds per clip
5. **Split audio into 2-3 segments:**
   - Segment 1: 0:00 - 1:00
   - Segment 2: 1:00 - 2:17
6. Generate separate videos for each segment
7. Combine in video editor (CapCut, iMovie, DaVinci Resolve)

### HeyGen (Professional Avatars)
1. Go to: https://heygen.com
2. Create custom avatar:
   - Upload Ganja Mon image
   - Upload Natural Guest image
3. Create 2 videos:
   - Video 1: Operator speaking segments (upload matching audio)
   - Video 2: Guest speaking segments (upload matching audio)
4. Combine videos with cuts between speakers

### D-ID (Talking Portraits)
1. Go to: https://d-id.com
2. Upload character image
3. Upload audio segment
4. Generate video
5. Repeat for second character
6. Combine in video editor

---

## Audio Segmentation Guide

### Split Audio by Speaker

You can split the audio file to match each speaker's segments:

**Operator Segments (Ganja Mon):**
- Turn 1: 0:00 - 0:17
- Turn 3: 0:35 - 0:52
- Turn 5: 1:10 - 1:27
- Turn 7: 1:45 - 2:02

**Guest Segments (Natural Speaker):**
- Turn 2: 0:18 - 0:34
- Turn 4: 0:53 - 1:09
- Turn 6: 1:28 - 1:44
- Turn 8: 2:03 - 2:17

Use this ffmpeg command to split:
```bash
# Extract operator segments
ffmpeg -i ganja_mon_conversation.mp3 -ss 0:00 -to 0:17 operator_1.mp3
ffmpeg -i ganja_mon_conversation.mp3 -ss 0:35 -to 0:52 operator_2.mp3
ffmpeg -i ganja_mon_conversation.mp3 -ss 1:10 -to 1:27 operator_3.mp3
ffmpeg -i ganja_mon_conversation.mp3 -ss 1:45 -to 2:02 operator_4.mp3

# Extract guest segments
ffmpeg -i ganja_mon_conversation.mp3 -ss 0:18 -to 0:34 guest_1.mp3
ffmpeg -i ganja_mon_conversation.mp3 -ss 0:53 -to 1:09 guest_2.mp3
ffmpeg -i ganja_mon_conversation.mp3 -ss 1:28 -to 1:44 guest_3.mp3
ffmpeg -i ganja_mon_conversation.mp3 -ss 2:03 -to 2:17 guest_4.mp3
```

---

## Final Video Assembly

### Option A: Simple Cut Between Speakers
1. Generate Ganja Mon animated video with operator audio
2. Generate Guest animated video with guest audio
3. Use video editor to cut between them on speaker changes
4. Add transition effects (crossfade, cut)

### Option B: Side-by-Side/Split Screen
1. Generate both character videos
2. Use video editor to create split-screen layout
3. Highlight active speaker with glow/border
4. Professional podcast-style presentation

### Option C: Full Scene Animation
1. Use Runway Gen-3 or Kling AI
2. Input: Character images + full audio
3. Prompt: "Two Jamaican Rasta characters having a conversation about AI cannabis cultivation in a modern grow room"
4. Generate cinematic video with AI

---

## Recommended Workflow

**EASIEST:**
1. Generate 2 character images (DALL-E or Midjourney)
2. Upload to HeyGen with full audio
3. Let HeyGen handle lip sync automatically
4. Export and share!

**BEST QUALITY:**
1. Generate high-quality character images (Midjourney v6)
2. Split audio by speaker
3. Create separate animated videos for each segment
4. Assemble in DaVinci Resolve with professional transitions
5. Add background music and effects
6. Export in 4K

---

## Next Steps

1. ✅ Audio files ready
2. ⏳ Generate character images
3. ⏳ Upload to animation platform
4. ⏳ Generate animated videos
5. ⏳ Assemble final video
6. ⏳ Share on Twitter/YouTube!
