# Setting Up Ultimate Dub Playlist on Website

## Overview

The ultimate dub playlist can be hosted on your website, but there are some considerations:

### Current Setup
- **FastAPI server** on Chromebook (port 8000)
- **Static file serving** via `/music` mount
- **Webamp player** already integrated
- **Playlist API** endpoints created

### File Size Considerations

**Current Status:**
- 17 MP3 files = ~1.5 GB
- Growing to 50+ tracks = ~5-10 GB estimated
- 24-hour mix alone = several GB

**Options:**

#### Option 1: Direct Hosting (Current Setup)
**Pros:**
- Simple - files served directly from Chromebook
- Full control
- No external dependencies

**Cons:**
- Large storage requirement (5-10 GB)
- Bandwidth usage on Chromebook
- Slower for users far from server

**Best for:** Small collection, local network users

#### Option 2: Cloudflare R2 Storage (Recommended)
**Pros:**
- Unlimited storage
- Global CDN (fast worldwide)
- Free tier: 10 GB storage, 1M requests/month
- Integrates with existing Cloudflare setup

**Cons:**
- Requires Cloudflare account setup
- Need to upload files to R2

**Best for:** Production, global audience

#### Option 3: Hybrid Approach
**Pros:**
- Host small tracks locally
- Stream large mixes from external source
- Best of both worlds

**Cons:**
- More complex setup

## Implementation Steps

### Step 1: Sync Tracks to Website

```bash
# Sync dub tracks to web/music directory
cd scripts
python sync_dub_playlist.py

# This will:
# - Copy/symlink tracks to src/web/music/ultimate_dub/
# - Generate playlist.json
```

### Step 2: Test API Endpoints

```bash
# List playlists
curl http://localhost:8000/api/playlist/list

# Get ultimate dub playlist
curl http://localhost:8000/api/playlist/ultimate_dub

# Stream a track (with range support)
curl -H "Range: bytes=0-1023" http://localhost:8000/api/playlist/dub/stream/King%20Tubby%20-%20Dub%20From%20The%20Roots.mp3
```

### Step 3: Update Website

The website will automatically load playlists via the API. The playlist loader script (`playlist-loader.js`) handles:
- Loading playlist metadata
- Converting to Webamp format
- Streaming tracks with range requests

### Step 4: Deploy to Chromebook

```bash
# Deploy updated API
./deploy.sh --restart

# Sync tracks (run on Chromebook)
ssh chromebook.lan "cd ~/projects/sol-cannabis && python3 scripts/sync_dub_playlist.py"
```

## Storage Requirements

**Estimated Storage:**
- Current: 1.5 GB (17 tracks)
- Target: 5-10 GB (50+ tracks + long mixes)
- 24-hour mix: ~2-3 GB alone

**Chromebook Storage:**
- Check available space: `df -h`
- Consider external drive if needed
- Or use Cloudflare R2 for large files

## Bandwidth Considerations

**Per User:**
- Average track: 50-100 MB
- Full playlist stream: 5-10 GB
- With caching: Much less (browser caches)

**Server Load:**
- Range requests = efficient streaming
- Cloudflare CDN = reduces server load
- Static file serving = low CPU usage

## Recommended Setup

1. **Small tracks (< 50 MB)**: Host locally on Chromebook
2. **Large mixes (> 100 MB)**: Use Cloudflare R2 or external CDN
3. **API endpoints**: Serve metadata from Chromebook (lightweight)
4. **Streaming**: Use range requests for efficient playback

## Testing Checklist

- [ ] API endpoints respond correctly
- [ ] Playlist metadata loads
- [ ] Tracks stream with range requests
- [ ] Webamp player loads tracks
- [ ] Playback works smoothly
- [ ] Large files don't crash server
- [ ] CDN caching works (if using Cloudflare)

## Next Steps

1. Run sync script to copy tracks
2. Test API endpoints locally
3. Update website to use playlist loader
4. Deploy and test on production
5. Monitor storage and bandwidth usage
