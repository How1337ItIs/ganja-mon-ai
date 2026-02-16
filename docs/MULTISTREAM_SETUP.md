# Ganja Mon Launch: Multi-Platform Streaming Setup 🎬🌿

**Last Updated:** January 16, 2026

This guide covers streaming simultaneously to **X (Twitter)**, **YouTube**, and **Twitch** for the Ganja Mon launch.

---

## 🔧 Software Stack (Recommended for 2026)

### Core Broadcasting Software: **OBS Studio**
OBS Studio remains the gold standard for streaming in 2026. It's free, open-source, and extremely powerful.

- **Download:** https://obsproject.com/download
- **Version:** Latest (31.x+)
- **Why OBS?** 
  - Free and open-source
  - Hardware-accelerated encoding (NVENC for NVIDIA GPUs)
  - Massive plugin ecosystem
  - Industry standard reliability

### Multistreaming Solution: **Aitum Multistream Plugin** (FREE)
This is the best local solution for simultaneous streaming without paying for cloud services.

- **Download:** https://aitum.tv/
- **Features:**
  - Free unlimited multistreaming
  - Native OBS integration
  - Multi-platform chat aggregation
  - Stream title/category management from OBS
  - Vertical streaming support (for TikTok/Shorts if needed)

### Alternative: **OBS Multi-RTMP Plugin** (FREE)
If you want something simpler:
- **GitHub:** https://github.com/sorayuki/obs-multi-rtmp
- Lightweight, just adds multiple RTMP outputs

### Backup Cloud Option: **Restream.io**
If local multistreaming causes issues (bandwidth, CPU), Restream is a reliable cloud fallback.
- Free tier: 2 channels
- Paid: Unlimited channels + analytics

---

## 📋 Platform Requirements

### 1. X (Twitter) - RTMP Streaming
⚠️ **IMPORTANT: Requires X Premium or Premium+ subscription for desktop streaming!**

**Setup Steps:**
1. Subscribe to X Premium at https://twitter.com/i/premium_sign_up
2. Go to **Media Studio Producer**: https://studio.x.com/producer
3. Click **Create Source** → Select **RTMP**
4. Choose region closest to you
5. Copy your **RTMP URL** and **Stream Key**

**Recommended Settings for X:**
- Resolution: 1920x1080 (1080p)
- Frame Rate: 30 FPS
- Video Bitrate: 4000-4500 Kbps
- Audio Bitrate: 160 Kbps
- Keyframe Interval: 2 seconds

### 2. YouTube Live
**Setup Steps:**
1. Go to **YouTube Studio**: https://studio.youtube.com
2. Click **Create** → **Go Live**
3. Select **Stream** tab
4. Copy your **Stream URL** and **Stream Key**
5. Enable "Ultra low-latency" for engagement

**Recommended Settings:**
- Resolution: 1920x1080 (1080p) or 2560x1440 (1440p)
- Frame Rate: 30 or 60 FPS
- Video Bitrate: 4500-9000 Kbps
- Audio Bitrate: 128-256 Kbps
- Keyframe Interval: 2 seconds

### 3. Twitch
**Setup Steps:**
1. Go to **Twitch Dashboard**: https://dashboard.twitch.tv
2. Click **Settings** → **Stream**
3. Copy your **Primary Stream Key**
4. Server: Auto or closest to your location

**Recommended Settings:**
- Resolution: 1920x1080 (1080p)
- Frame Rate: 60 FPS (Twitch loves 60fps)
- Video Bitrate: 6000 Kbps (max for non-partners)
- Audio Bitrate: 160 Kbps
- Keyframe Interval: 2 seconds

---

## 🖥️ OBS Configuration for Multi-Platform

### Optimal Unified Settings (Compromise for all platforms)
Use these settings to stream to all three platforms simultaneously:

```
Resolution: 1920x1080 (1080p)
Frame Rate: 30 FPS (X cap, saves bandwidth)
Video Bitrate: 5000 Kbps per stream
Audio Bitrate: 160 Kbps
Encoder: NVENC (Hardware - if NVIDIA GPU) or x264 (CPU)
Keyframe Interval: 2 seconds
Rate Control: CBR (Constant Bitrate)
```

### Bandwidth Requirements
Streaming to 3 platforms at 5000 Kbps each:
- **Minimum Upload Speed:** 15 Mbps
- **Recommended Upload Speed:** 20+ Mbps (20% overhead)

---

## 🎨 Stream Overlay Concept for Ganja Mon

### Visual Elements to Create:
1. **Main Overlay Frame** - Rasta-themed border with "$MON" branding
2. **Webcam Feed** - Show the grow tent/plant
3. **Sensor Data Overlay** - Real-time temp, humidity, CO2
4. **AI Status Panel** - Show Grok's last decision
5. **Chat Integration** - Unified chat from all platforms
6. **$MON Token Ticker** - Live price feed

### Scene Ideas:
- **Full Screen Plant Cam** - Main focus on the plant
- **Dashboard View** - Web dashboard with commentary
- **AI Brain View** - Show terminal with Grok reasoning
- **Starting Soon** - Pre-stream hype screen
- **BRB** - Break screen with vibes

---

## 📦 Installation Checklist

### Software Downloaded ✅:
- [x] **OBS Studio 32.0.4** - `C:\Users\natha\Downloads\OBS-Studio-32.0.4-Windows-x64-Installer.exe` (157 MB)
- [x] **OBS Multi-RTMP Plugin 0.7.3.0** - `C:\Users\natha\Downloads\obs-multi-rtmp-0.7.3.0-installer.exe` (1.3 MB)

### Software to Download (Optional):
- [ ] **Aitum Multistream Plugin** - https://aitum.tv/ (Alternative to Multi-RTMP, more features)
- [ ] **StreamElements OBS Plugin** (optional, for alerts) - https://streamelements.com/obslive

### Accounts to Set Up:
- [ ] **X Premium** - Required for desktop streaming
- [ ] **YouTube Channel** - Enable live streaming (24hr wait for new channels)
- [ ] **Twitch Account** - Enable 2FA for streaming

### Hardware Considerations:
- [ ] Webcam (Logitech C920/C922 minimum, or your existing setup)
- [ ] Microphone (for commentary/voiceover)
- [ ] Good lighting for plant visibility
- [ ] Second monitor (highly recommended for managing streams)

---

## 🚀 Pre-Launch Checklist

### 1 Week Before:
- [ ] Install and configure OBS
- [ ] Set up all platform accounts and verify streaming access
- [ ] Create stream overlays and scenes
- [ ] Do test streams to each platform individually
- [ ] Test multistream to all three simultaneously

### 1 Day Before:
- [ ] Verify all stream keys are current
- [ ] Test internet speed and stability
- [ ] Prepare backup stream keys
- [ ] Set up stream titles/descriptions for all platforms
- [ ] Schedule the stream on YouTube (for notifications)

### 30 Minutes Before:
- [ ] Start OBS and verify all sources working
- [ ] Check audio levels
- [ ] Verify plant cam is showing correctly
- [ ] Load dashboard/sensor data overlays
- [ ] Test chat aggregation

---

## 🔗 Quick Links

| Platform | Dashboard | Stream Settings |
|----------|-----------|-----------------|
| X/Twitter | [Media Studio](https://studio.x.com/producer) | RTMP in Producer |
| YouTube | [YouTube Studio](https://studio.youtube.com/channel/UC/livestreaming) | Create → Go Live |
| Twitch | [Twitch Dashboard](https://dashboard.twitch.tv/settings/stream) | Settings → Stream |
| OBS | [Download](https://obsproject.com/download) | - |
| Aitum | [Download](https://aitum.tv/) | - |

---

## 💡 Pro Tips

1. **Stream to Twitch as Primary** - Set Twitch as your main output in OBS, then use the multistream plugin for X and YouTube
2. **Use Hardware Encoding** - NVENC (NVIDIA) or AMD VCE saves CPU for other tasks
3. **Monitor Chat from One Place** - Use Aitum's unified chat or Restream's chat aggregator
4. **Have Backup Plans** - If one platform fails, keep streaming to others
5. **Clip Highlights** - Have someone ready to clip for virality on X

---

*One love, one stream, three platforms* 🌿🎬
