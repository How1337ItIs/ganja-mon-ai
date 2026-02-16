# 🌿 Ganjafy - Rasta Image Transformer

> **Status: DEPLOYED & WORKING** ✅  
> **URL**: https://grokandmon.com/ganjafy  
> **Password**: `JahBlessings420`

## Overview
Ganjafy is a Cloudflare Worker-powered web app that transforms images with rasta vibes using **Gemini 3 Pro Image Generation**. Users can upload photos and the AI adds Jamaican-themed elements like rasta tams, dreadlocks, joints, and ganja plants.

---

## 🗂️ Project Files (in sol-cannabis)

| File | Purpose |
|------|---------|
| `cloudflare-worker-ganjafy.js` | Complete worker (HTML + CSS + JS + API) |
| `wrangler-ganjafy.toml` | Wrangler deployment config |
| `GANJAFY_DOCUMENTATION.md` | This file |
| `GANJAFY_DEPLOY_HANDOFF.md` | Original handoff notes |

---

## 🚀 Deployment

### Deploy Command
```bash
cd c:\Users\natha\sol-cannabis
wrangler deploy -c wrangler-ganjafy.toml
```

### Wrangler Config (`wrangler-ganjafy.toml`)
```toml
name = "grokmon-ganjafy"
main = "cloudflare-worker-ganjafy.js"
account_id = "a33a705d5aebbca59de7eb146029869a"
zone_id = "97e79defaee450aa65217568dbf2f835"
route = "grokandmon.com/ganjafy*"
compatibility_date = "2024-01-01"

[vars]
DASHBOARD_PASSWORD = "JahBlessings420"

kv_namespaces = [
  { binding = "GALLERY_KV", id = "b83f3be2df3d4ecc9c7b0bd1bb693dcf" }
]
```

### Secrets
```bash
# Gemini API Key (already set)
echo "YOUR_API_KEY" | wrangler secret put GEMINI_API_KEY -c wrangler-ganjafy.toml
```

---

## 🔐 Authentication System

### Token-Based Stateless Auth
Cloudflare Workers are **stateless** - they don't persist in-memory data across requests. The original session-based approach (`sessions.set()`) was replaced with **HMAC-signed tokens**.

#### How It Works:
1. **Login**: User submits password or API key
2. **Token Creation**: Server creates a signed token with:
   - `exp`: Expiration timestamp (24 hours)
   - `userApiKey`: User's own Gemini key (if provided)
   - `canUseServerKey`: Whether user can use server's API key
3. **Token Signing**: HMAC-SHA256 signature using password as secret
4. **Token Verification**: Each request verifies the token signature

#### Token Format:
```
base64(payload).base64(signature)
```

#### Auth Methods:
1. **Password Login**: Full access with server's API key
2. **BYOK (Bring Your Own Key)**: User provides their own Gemini API key

---

## 🖼️ Image Transformation

### API Flow
1. User uploads image via `/ganjafy/api/transform`
2. Backend verifies auth token
3. Image converted to base64
4. Request sent to Gemini API with rasta prompt
5. Generated image returned to user
6. Image saved to Gallery KV

### Gemini Configuration
```javascript
model: "gemini-3-pro-image-preview"
endpoint: "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"
config: {
  responseModalities: ["Text", "Image"],
  responseMimeType: "text/plain"
}
```

### The Rasta Prompt
```
Transform this image with authentic Jamaican rasta vibes:
- Add a colorful knit rasta tam (red, gold, green stripes)
- Add dreadlocks flowing naturally
- Optional: Add ganja plants, joints, smoke effects
- Keep the image natural and photorealistic
- Preserve the original subject's essence
```

---

## 📸 Gallery System

### KV Storage
- **Namespace**: `GALLERY_KV` 
- **ID**: `b83f3be2df3d4ecc9c7b0bd1bb693dcf`

### Gallery API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/ganjafy/api/gallery` | List all gallery items |
| GET | `/ganjafy/api/gallery/:id` | Get specific image |
| POST | `/ganjafy/api/transform` | Create & save new image |

### Image Storage Format
```javascript
{
  key: "ganjafy-{timestamp}",
  value: base64ImageData,
  metadata: { timestamp, type }
}
```

---

## 🔧 Troubleshooting

### 401 Unauthorized on Transform
**Cause**: Old session-based auth with in-memory Map  
**Fix**: Now uses stateless signed tokens (implemented)

### "No image generated" Error
**Cause**: Wrong Gemini model  
**Fix**: Use `gemini-3-pro-image-preview` with `responseModalities: ["Text", "Image"]`

### Check Available Models
```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY" | grep -i image
```

### View Logs
```bash
wrangler tail -c wrangler-ganjafy.toml
```

---

## 📊 Architecture

```
┌─────────────────┐
│  Browser/User   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Cloudflare     │
│  Worker         │
│  (ganjafy.js)   │
└────────┬────────┘
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌──────────┐
│Gallery│  │ Gemini   │
│  KV   │  │ API      │
└───────┘  └──────────┘
```

---

## ✅ Features Working

- [x] Login with password
- [x] Login with user's own API key (BYOK)
- [x] Stateless token auth (persists across Worker instances)
- [x] Image upload (JPEG, PNG, WebP)
- [x] Gemini 3 Pro image generation
- [x] Gallery storage in KV
- [x] Gallery viewing
- [x] Image download
- [x] Lightbox preview
- [x] Rasta-themed UI with animations

---

## 🎨 UI Features

- **Gradient Background**: Animated rasta colors
- **Glassmorphism**: Frosted glass effects
- **Cannabis Icons**: Decorative leaf elements
- **Reggae Typography**: Bob Marley-inspired fonts
- **Responsive Design**: Works on mobile and desktop
- **Loading Animation**: Cannabis leaf spinner

---

## 🔄 Recent Changes Log

### 2026-01-26
- Fixed 401 Unauthorized error on transform
- Replaced in-memory session Map with HMAC-signed tokens
- Tokens now work across Worker instances (stateless)
- Verified gallery save functionality works

### Previous
- Switched to `gemini-3-pro-image-preview` model
- Added Gallery KV storage
- Implemented BYOK (Bring Your Own Key) auth option

---

## 📞 Quick Reference

| What | Value |
|------|-------|
| **Live URL** | https://grokandmon.com/ganjafy |
| **Password** | `JahBlessings420` |
| **Deploy** | `wrangler deploy -c wrangler-ganjafy.toml` |
| **Logs** | `wrangler tail -c wrangler-ganjafy.toml` |
| **KV ID** | `b83f3be2df3d4ecc9c7b0bd1bb693dcf` |

---

**One Love! 🌿💚💛❤️**
