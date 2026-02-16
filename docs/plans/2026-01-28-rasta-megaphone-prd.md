# Rasta Mon Megaphone - Product Requirements Document

**Created:** January 28, 2026
**Status:** Planning
**Owner:** @ganjamonai

---

## 1. Overview & Goals

**Rasta Mon Megaphone** - A portable voice transformer for street performance and guerrilla marketing.

### What It Does

You speak into a clip-on mic → 1-2 second pause → the Jamaican rasta character's voice blasts out of a 50-watt bullhorn megaphone (1200 ft range). All processing happens in the cloud (Deepgram STT → Groq LLM → ElevenLabs TTS), so the hardware stays cheap and simple.

### Why Build It

- **Brand presence for @ganjamonai** - Instant recognition, memorable character
- **Street marketing** - Parks, events, dispensaries, 420 gatherings
- **Content creation** - Record performances for social media
- **Fun** - It's a talking megaphone with a stoner rasta AI

### Success Criteria

1. Speak naturally, hear rasta voice from megaphone within 2 seconds
2. 4+ hours battery life on a single charge
3. Fits in a backpack, one-person carry
4. Works anywhere with phone hotspot (no home WiFi needed)
5. Under 5 minutes from power-on to talking

---

## 2. Hardware

### Tier 1: MVP Build (~$80)

| Component | Recommendation | Price | Link |
|-----------|---------------|-------|------|
| Computer | Raspberry Pi Zero 2 W | $15 | [RPi Foundation](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) |
| Storage | MicroSD 16GB (any) | $5 | Amazon |
| Microphone | Generic USB lavalier clip-on | $8 | Amazon |
| Megaphone | **5 CORE 66SF** (50W, AUX input, rechargeable) | $36 | [Amazon](https://www.amazon.com/CORE-Rechargeable-Professional-Adjustable-66SF/dp/B08VF5V5H5) |
| USB Adapter | Micro-USB OTG adapter | $3 | Amazon |
| Audio Cable | 3.5mm male-to-male (1ft) | $3 | Amazon |
| Power | USB power bank 5000mAh | $10 | Amazon |

**Total: ~$80**

### Tier 2: Upgraded Build (~$130)

Adds better audio quality and longer runtime:

| Upgrade | Why | Price |
|---------|-----|-------|
| **Rode Lavalier GO** | Broadcast-quality mic, less background noise | +$80 |
| **20,000mAh power bank** | 12+ hours runtime | +$25 |
| **Pi Zero 2 W case** | Protection, heat dissipation | +$8 |

**Total: ~$130-150**

### Tier 3: Premium Build (~$250+)

For serious street performance:

| Upgrade | Why | Price |
|---------|-----|-------|
| **Rode Wireless GO II** | Wireless mic, 200m range, backup recording | +$200 |
| **Weatherproof enclosure** | Rain/dust protection | +$30 |
| **Bluetooth megaphone (Pyle PMP52BT)** | Eliminates aux cable | +$5 vs 66SF |

### Critical Note: Megaphone Selection

**MUST have 3.5mm AUX input.** Many cheap megaphones only have a built-in mic with no way to feed external audio. Verified options:

- ✅ **5 CORE 66SF** ($36) - Best value, rechargeable
- ✅ **Pyle PMP57LIA** ($45) - Larger, rechargeable + backup batteries
- ✅ **Pyle PMP52BT** ($40) - Bluetooth option
- ❌ Pyle PMP30/PMP50 - NO AUX INPUT, won't work

---

## 3. Assembly

### Physical Connections (No Soldering)

```
┌─────────────────────────────────────────────────────────────┐
│                      MEGAPHONE (5 CORE 66SF)                │
│                                                             │
│   ┌─────────────┐                                          │
│   │  AUX INPUT  │◄──── 3.5mm cable ────┐                   │
│   │   (3.5mm)   │                      │                   │
│   └─────────────┘                      │                   │
│                                        │                   │
│   Built-in rechargeable battery        │                   │
│   (charge via included USB cable)      │                   │
└─────────────────────────────────────────│───────────────────┘
                                         │
┌────────────────────────────────────────┴───────────────────┐
│                  RASPBERRY PI ZERO 2 W                      │
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────────────────┐ │
│   │ 3.5mm    │    │ Micro-USB│    │ Micro-USB (power)    │ │
│   │ Audio Out│    │ + OTG    │    │                      │ │
│   └────┬─────┘    └────┬─────┘    └──────────┬───────────┘ │
│        │               │                     │             │
│        │ to megaphone  │ USB Lavalier Mic    │ Power Bank  │
└────────┴───────────────┴─────────────────────┴─────────────┘
```

### Step-by-Step Assembly

1. **Insert MicroSD** into Pi (after flashing - covered in next section)
2. **Plug OTG adapter** into Pi's data USB port (the one closer to center)
3. **Plug USB mic** into OTG adapter
4. **Plug 3.5mm cable** from Pi's audio jack → megaphone's AUX input
5. **Plug power bank** into Pi's power USB port (the one on the edge)
6. **Charge megaphone** separately via its included USB cable

### Mounting Options

**Simple (backpack carry):**
- Pi + power bank in pants pocket or backpack pouch
- Mic clipped to shirt collar
- Megaphone in hand
- Cables routed under jacket/shirt

**Integrated (one unit):**
- Velcro-strap Pi + power bank to megaphone handle
- Short cables (1ft max) to keep tidy
- Everything in one hand

---

## 4. Software Setup

### Step 1: Flash the SD Card (on your Windows laptop)

**Download Raspberry Pi Imager:**
https://www.raspberrypi.com/software/

**Flash process:**
1. Insert MicroSD into laptop (use adapter if needed)
2. Open Raspberry Pi Imager
3. Click **"Choose OS"** → Raspberry Pi OS (other) → **Raspberry Pi OS Lite (64-bit)**
   - "Lite" = no desktop, command-line only (smaller, faster)
4. Click **"Choose Storage"** → select your MicroSD
5. Click the **gear icon** (bottom right) for advanced options:

```
✅ Set hostname: rastamegaphone
✅ Enable SSH: Use password authentication
✅ Set username and password:
   Username: pi
   Password: [pick something you'll remember]
✅ Configure wireless LAN:
   SSID: [your phone's hotspot name]
   Password: [your hotspot password]
   Country: US
✅ Set locale settings:
   Time zone: America/Los_Angeles
   Keyboard layout: us
```

6. Click **Save**, then **Write**
7. Wait for flash + verification (~5 min)
8. Eject SD card, insert into Pi

### Step 2: First Boot & SSH Connection

**Power on the Pi:**
1. Plug power bank into Pi
2. Wait 60-90 seconds for boot + WiFi connection
3. Green LED will flicker during boot, then settle

**Connect from Windows (using PowerShell):**

```powershell
# Find Pi on network
ping rastamegaphone.local

# SSH in (accept fingerprint prompt, enter your password)
ssh pi@rastamegaphone.local
```

**If `rastamegaphone.local` doesn't work:**
- Check your phone's hotspot connected devices for the Pi's IP
- Use `ssh pi@192.168.x.x` with that IP instead

### Step 3: Install System Dependencies

Once SSH'd into the Pi, run these commands:

```bash
# Update system (takes 2-3 min)
sudo apt update && sudo apt upgrade -y

# Install audio + Python dependencies (takes 3-5 min)
sudo apt install -y python3-pip python3-venv \
    portaudio19-dev libasound2-dev libportaudio2 \
    ffmpeg alsa-utils git

# Force audio output to 3.5mm jack (not HDMI)
sudo raspi-config nonint do_audio 1
```

### Step 4: Clone Code & Setup Python

```bash
# Clone the repo
cd ~
git clone https://github.com/YOUR_USERNAME/sol-cannabis.git
cd sol-cannabis/rasta-voice

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages (takes 2-3 min)
pip install --upgrade pip
pip install numpy sounddevice scipy websockets openai elevenlabs python-dotenv
```

### Step 5: Configure API Keys

```bash
# Create environment file
cat > .env << 'EOF'
DEEPGRAM_API_KEY=your-deepgram-key-here
GROQ_API_KEY=your-groq-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE
EOF

# Edit with your actual keys
nano .env
# (Ctrl+X, Y, Enter to save)
```

**Where to get API keys:**

| Service | URL | Free Tier |
|---------|-----|-----------|
| Deepgram | https://console.deepgram.com | $200 credit |
| Groq | https://console.groq.com | Free (rate limited) |
| ElevenLabs | https://elevenlabs.io | 10k chars/month |

### Step 6: Test Audio Devices

```bash
# List audio devices
python3 rasta_live_megaphone.py --list-devices

# Test microphone (speak for 5 sec, should play back through megaphone)
arecord -d 5 -f cd test.wav && aplay test.wav

# Test speaker output
speaker-test -t sine -f 1000 -l 1
```

### Step 7: Run the Pipeline

```bash
# Make sure you're in the right directory with venv activated
cd ~/sol-cannabis/rasta-voice
source venv/bin/activate

# Run it!
python3 rasta_live_megaphone.py
```

**What you should see:**
```
============================================================
RASTA MON MEGAPHONE
============================================================
Speak naturally. Press Ctrl+C to stop.
[INFO] GPIO initialized
[INFO] Connected to Deepgram
[INFO] Microphone active - speak into megaphone!
```

**Test it:** Say "Hello, how are you today?" → 1-2 sec pause → Rasta voice from megaphone: *"Wah gwaan, how yuh stay today, bredren?"*

Press `Ctrl+C` to stop.

### Step 8: Auto-Start on Boot

So you don't need to SSH in every time - just power on and go:

```bash
# Create systemd service
sudo tee /etc/systemd/system/rasta-megaphone.service << 'EOF'
[Unit]
Description=Rasta Mon Megaphone
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sol-cannabis/rasta-voice
Environment="PATH=/home/pi/sol-cannabis/rasta-voice/venv/bin:/usr/bin"
EnvironmentFile=/home/pi/sol-cannabis/rasta-voice/.env
ExecStart=/home/pi/sol-cannabis/rasta-voice/venv/bin/python3 rasta_live_megaphone.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable rasta-megaphone.service
sudo systemctl start rasta-megaphone.service

# Check status
sudo systemctl status rasta-megaphone.service
```

**Now on every boot:**
1. Power on Pi
2. Wait ~60 seconds for boot + WiFi
3. Start talking - rasta voice comes out

---

## 5. Field Operations

### Pre-Performance Checklist

**Night before:**
- [ ] Charge megaphone (USB cable, ~4 hours)
- [ ] Charge power bank (full charge)
- [ ] Charge phone (for hotspot)

**Before heading out:**
- [ ] Phone hotspot ON with correct SSID/password
- [ ] Power bank connected to Pi
- [ ] Mic clipped to shirt/collar
- [ ] 3.5mm cable connected Pi → megaphone
- [ ] Megaphone powered ON, volume at ~50% to start

### Startup Sequence (Field)

1. **Turn on phone hotspot** (Pi will auto-connect)
2. **Plug power bank into Pi** (boots automatically)
3. **Wait 60-90 seconds** (LED will flicker, then steady)
4. **Turn on megaphone**, set to AUX input mode
5. **Test with "Check, check"** → should hear rasta voice
6. **Adjust megaphone volume** as needed

### Performance Tips

| Tip | Why |
|-----|-----|
| **Pause between sentences** | Gives the AI clean breaks to process |
| **Speak clearly, not fast** | Better transcription accuracy |
| **Project your voice** | USB mics aren't great at picking up quiet speech |
| **Face away from megaphone** | Prevents feedback loop |
| **Keep 1-2 second delay in mind** | Don't talk over yourself |

### Quick Commands (If You Need to SSH In)

```bash
# Check if running
sudo systemctl status rasta-megaphone

# Restart if stuck
sudo systemctl restart rasta-megaphone

# View live logs
journalctl -u rasta-megaphone -f

# Stop completely
sudo systemctl stop rasta-megaphone

# Safe shutdown (do this before unplugging power)
sudo shutdown -h now
```

---

## 6. Troubleshooting

### Problem: Pi Won't Connect to WiFi

**Symptoms:** Can't ping or SSH to Pi after boot

**Fixes:**
```bash
# On your phone: verify hotspot is ON and visible
# Check hotspot name matches EXACTLY what you configured (case-sensitive)

# If you need to reconfigure WiFi:
# 1. Remove SD card from Pi, put in laptop
# 2. Open "bootfs" drive
# 3. Create file called "wpa_supplicant.conf" with:

country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourHotspotName"
    psk="YourHotspotPassword"
    key_mgmt=WPA-PSK
}
```

### Problem: No Sound from Megaphone

| Check | Fix |
|-------|-----|
| Megaphone on AUX mode? | Some have a mode switch - set to AUX/LINE IN |
| Volume up? | Start at 50%, increase from there |
| 3.5mm cable seated? | Unplug and replug both ends |
| Pi audio output set to 3.5mm? | `sudo raspi-config` → Advanced → Audio → Force 3.5mm |

**Test without the pipeline:**
```bash
# Generate a test tone directly
speaker-test -t sine -f 440 -l 1
# Should hear 440Hz tone through megaphone
```

### Problem: Mic Not Picking Up Voice

```bash
# List recording devices
arecord -l

# Test recording (5 seconds)
arecord -d 5 -f cd test.wav
aplay test.wav  # Should hear yourself

# If no USB mic detected:
lsusb  # Should show your mic
# Try unplugging/replugging the OTG adapter
```

### Problem: Pipeline Starts But No Rasta Output

**Check API keys:**
```bash
cat ~/sol-cannabis/rasta-voice/.env
# Verify all 3 keys are set (not placeholder text)
```

**Check logs:**
```bash
journalctl -u rasta-megaphone -n 50
# Look for errors like "401 Unauthorized" (bad API key)
# or "Connection refused" (no internet)
```

**Test internet:**
```bash
ping -c 3 api.deepgram.com
# Should get responses, not "Network unreachable"
```

### Problem: High Latency (>3 seconds)

| Cause | Fix |
|-------|-----|
| Weak WiFi signal | Move closer to phone / use 5GHz hotspot if available |
| Phone on battery saver | Disable battery optimization for hotspot |
| API throttling | Check if you've exceeded free tier limits |

### Problem: Audio Cuts Out Mid-Sentence

Usually Deepgram WebSocket disconnect. Check logs:
```bash
journalctl -u rasta-megaphone -f
# Look for "WebSocket closed" or "Connection error"
```

**Fix:** The service auto-restarts, but if persistent:
- Check phone hotspot stability
- Reduce distance between Pi and phone
- Consider Ethernet-to-USB adapter for more stable connection

---

## 7. Future Enhancements

### Quick Wins (Software Only)

| Enhancement | Effort | Description |
|-------------|--------|-------------|
| **Push-to-talk mode** | 1 hour | Only process audio when button held (saves API costs, cleaner output) |
| **Status LED patterns** | 30 min | Blink = booting, solid = ready, fast blink = speaking |
| **Battery low warning** | 30 min | Announce "Battery low, bredren!" when power bank dying |
| **Offline phrase bank** | 2 hours | Pre-recorded rasta phrases for no-WiFi situations |

### Hardware Upgrades

| Upgrade | Cost | Benefit |
|---------|------|---------|
| **Momentary button (GPIO)** | $2 | Push-to-talk, cleaner activation |
| **RGB LED** | $3 | Visual status (green=ready, blue=processing, red=error) |
| **USB audio adapter** | $10 | Better audio quality than Pi's built-in 3.5mm |
| **Rode Wireless GO II** | $200 | Broadcast quality, wireless, 200m range |

### Stretch Goals

**Offline mode (no internet required):**
- Replace Deepgram with Whisper.cpp (local STT)
- Replace Groq with Llama 3 8B quantized (local LLM)
- Keep ElevenLabs or use Piper TTS (local)
- Requires Pi 4/5 (more compute), higher latency (~5 sec)

**Recording mode:**
- Save all performances to SD card
- Auto-upload to cloud when back on home WiFi
- Content for social media clips

**Multi-character:**
- Config file to switch voices/personalities
- Button to cycle: Rasta Mon → Robot → Valley Girl → etc.

---

## 8. Summary

| Phase | What | Cost | Time |
|-------|------|------|------|
| **1. Order parts** | MVP build from Amazon | ~$80 | 10 min |
| **2. Flash & assemble** | SD card + physical connections | $0 | 30 min |
| **3. Software setup** | SSH, install, configure | $0 | 1-2 hours |
| **4. Test at home** | Verify full pipeline works | $0 | 30 min |
| **5. Hit the streets** | Guerrilla marketing time | $0 | ∞ |

---

## Appendix: Shopping List (Copy-Paste for Amazon)

```
[ ] Raspberry Pi Zero 2 W                           ~$15
[ ] MicroSD card 16GB+                               ~$5
[ ] Micro-USB OTG adapter                            ~$3
[ ] USB lavalier clip-on microphone                  ~$8
[ ] 3.5mm male-to-male audio cable (short, 1ft)      ~$3
[ ] 5 CORE 66SF megaphone (50W, AUX input)          ~$36
[ ] USB power bank (5000mAh+)                       ~$10
                                             TOTAL: ~$80
```

---

*Generated: 2026-01-28*
