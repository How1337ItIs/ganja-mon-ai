# Rasta Mon Megaphone - Raspberry Pi Setup Guide

## Quick Start

### 1. Flash Raspberry Pi OS

```bash
# Download Raspberry Pi Imager
# Flash to microSD card with:
# - OS: Raspberry Pi OS (64-bit)
# - Enable SSH
# - Set WiFi credentials (or use Ethernet)
# - Set username/password
```

### 2. Initial Setup

```bash
# SSH into Pi
ssh pi@raspberrypi.local  # or use IP address

# Update system
sudo apt update && sudo apt upgrade -y

# Install audio dependencies
sudo apt install -y python3-pip python3-venv portaudio19-dev \
    libasound2-dev libportaudio2 libportaudiocpp0 ffmpeg \
    alsa-utils

# Install GPIO library (for hardware controls)
sudo apt install -y python3-rpi.gpio
```

### 3. Clone Repository

```bash
# Clone your repo (or copy files)
cd ~
git clone <your-repo-url> sol-cannabis
cd sol-cannabis/rasta-voice
```

### 4. Create Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install numpy sounddevice scipy websockets openai elevenlabs python-dotenv
```

### 5. Configure Audio

```bash
# List audio devices
python3 rasta_live_megaphone.py --list-devices

# Test microphone
arecord -d 5 -f cd test.wav
aplay test.wav

# Test speaker
speaker-test -t sine -f 1000 -l 1

# Set default audio device (optional)
# Edit /etc/asound.conf or use alsamixer
```

### 6. Set Environment Variables

```bash
# Create .env file
cat > .env << EOF
DEEPGRAM_API_KEY=your-deepgram-key
GROQ_API_KEY=your-groq-key
ELEVENLABS_API_KEY=your-elevenlabs-key
ELEVENLABS_VOICE_ID=dhwafD61uVd8h85wAZSE
EOF
```

### 7. Test Pipeline

```bash
# Activate venv
source venv/bin/activate

# Run with default devices
python3 rasta_live_megaphone.py

# Or specify devices
python3 rasta_live_megaphone.py --input-device 2 --output-device 0
```

### 8. Auto-Start on Boot (Optional)

```bash
# Create systemd service
sudo nano /etc/systemd/system/rasta-megaphone.service
```

**Service file content:**
```ini
[Unit]
Description=Rasta Mon Megaphone
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sol-cannabis/rasta-voice
Environment="PATH=/home/pi/sol-cannabis/rasta-voice/venv/bin"
ExecStart=/home/pi/sol-cannabis/rasta-voice/venv/bin/python3 rasta_live_megaphone.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable rasta-megaphone.service
sudo systemctl start rasta-megaphone.service

# Check status
sudo systemctl status rasta-megaphone.service

# View logs
journalctl -u rasta-megaphone.service -f
```

## Hardware Connections

### GPIO Pinout

| GPIO | Physical Pin | Function |
|------|--------------|----------|
| GPIO 3 | Pin 5 | Power Button (input, pull-up) |
| GPIO 18 | Pin 12 | Status LED (output) |
| GPIO 24 | Pin 18 | Battery Low (input, optional) |

### Power Button Wiring

```
Power Button:
  One side → GPIO 3 (Pin 5)
  Other side → GND (Pin 6)
  
(Internal pull-up: button press = LOW)
```

### Status LED Wiring

```
LED:
  Anode → 220Ω resistor → GPIO 18 (Pin 12)
  Cathode → GND (Pin 14)
```

### Battery Low Detection

```
Battery Pack Low Signal:
  → GPIO 24 (Pin 18)
  (If battery pack has low-battery output)
```

## Troubleshooting

### Audio Issues

**Problem:** No audio output
```bash
# Check audio devices
aplay -l
arecord -l

# Test default output
speaker-test -t sine -f 1000 -l 1

# Check volume
alsamixer
```

**Problem:** Microphone not detected
```bash
# List USB devices
lsusb

# Check audio input
arecord -l

# Test recording
arecord -d 5 -f cd test.wav && aplay test.wav
```

### Network Issues

**Problem:** Can't connect to APIs
```bash
# Test internet
ping -c 3 8.8.8.8

# Test DNS
nslookup api.deepgram.com

# Check firewall (if enabled)
sudo ufw status
```

### Performance Issues

**Problem:** High latency
- Use `--mode conversation` (already default)
- Check WiFi signal strength
- Consider using Ethernet instead
- Monitor CPU usage: `htop`

**Problem:** Audio stuttering
- Increase buffer size in code
- Use lower sample rate (16kHz instead of 48kHz)
- Close other applications

### GPIO Issues

**Problem:** GPIO not working
```bash
# Check if module is loaded
lsmod | grep gpio

# Test GPIO manually
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(18, GPIO.OUT); GPIO.output(18, GPIO.HIGH)"
```

## Optimization Tips

### 1. Reduce Latency

Edit `rasta_live_megaphone.py`:
```python
# Use lower sample rate for faster processing
config.sample_rate = 16000  # Instead of 48000

# Use smaller chunk size
config.chunk_size = 512  # Instead of 1024
```

### 2. Lower Power Consumption

```bash
# Disable HDMI (if headless)
sudo /usr/bin/tvservice -o

# Reduce CPU governor
echo "powersave" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable Bluetooth (if not needed)
sudo systemctl disable bluetooth
```

### 3. Improve Audio Quality

- Use USB audio interface instead of built-in audio
- Use higher quality microphone
- Adjust gain levels with `alsamixer`

## Battery Life Tips

- Use Raspberry Pi Zero 2 W for longer battery life
- Enable auto-sleep when idle (add to code)
- Use efficient battery pack (20,000mAh+)
- Disable unnecessary services
- Lower screen brightness (if using display)

## Next Steps

1. **Test basic functionality** - Verify audio in/out works
2. **Test API connections** - Make sure all APIs are accessible
3. **Add hardware controls** - Wire up GPIO buttons/LEDs
4. **Build enclosure** - 3D print or use case
5. **Optimize for your use case** - Adjust latency/quality trade-offs

## Support

If you run into issues:
1. Check logs: `journalctl -u rasta-megaphone.service -n 50`
2. Test components individually (mic, speaker, APIs)
3. Verify all environment variables are set
4. Check network connectivity
5. Review GPIO wiring if using hardware controls
