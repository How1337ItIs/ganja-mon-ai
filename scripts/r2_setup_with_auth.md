# R2 Setup - Authentication Required

## 🔐 Quick Setup

Wrangler needs to be authenticated. You have two options:

### Option 1: Use API Token (Recommended for Automation)

```bash
# Set your Cloudflare API token (from update_webcam_kv.py)
export CLOUDFLARE_API_TOKEN="055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"

# Then run setup
python scripts/setup_cloudflare_r2_dub.py
```

### Option 2: Interactive Login

```bash
# Login interactively
wrangler login

# Then run setup
python scripts/setup_cloudflare_r2_dub.py
```

## 🚀 Complete Setup Steps

```bash
# 1. Authenticate
export CLOUDFLARE_API_TOKEN="055Z35I4Op1DH3aCLGY6HDWhj2-1fJuR1xlvlrNO"
# OR: wrangler login

# 2. Create bucket
wrangler r2 bucket create grokmon-dub-tracks

# 3. Upload tracks (33 files, ~3 GB)
python scripts/setup_cloudflare_r2_dub.py

# 4. Deploy worker
wrangler deploy cloudflare-worker-dub-stream.js --name grokmon-dub-stream

# 5. Add route in Cloudflare Dashboard:
#    Pattern: grokandmon.com/api/playlist/dub/stream/*
#    Worker: grokmon-dub-stream
```

## 📊 What Will Be Uploaded

- **33 MP3 files** = **2.95 GB**
- Fits comfortably in R2 free tier (10 GB)
- Upload time: ~5-10 minutes (depending on connection)

## ✅ After Setup

Your tracks will be:
- ✅ Hosted on R2 (free, unlimited bandwidth)
- ✅ Served via Cloudflare Worker (global edge)
- ✅ Cached at edge (fast worldwide)
- ✅ **100% FREE!**
