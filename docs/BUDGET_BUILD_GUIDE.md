# Budget Build Guide - Chromebook-Based Cannabis Cultivation System

*Optimized for East Bay Area, California - with local pickup sources*

This guide is specifically designed for using a **Chromebook** instead of Raspberry Pi, focusing on the **cheapest effective build** with local East Bay sources.

---

## Architecture: Chromebook + WiFi Sensors

Since Chromebooks don't have GPIO pins like Raspberry Pi, we use a **WiFi-based architecture**:

```
[ESP32 Sensor Nodes] --WiFi--> [Chromebook Running Linux] --WiFi--> [Smart Plugs]
         |                              |                              |
    DHT22, SCD40,                  Python Agent                   Kasa HS103/105
    Soil Moisture                  + Grok AI API                  (Lights, Fans)
```

**Key Benefits:**
- Use your existing Chromebook (free!)
- ESP32 boards are $3-5 each
- Sensors connect to ESP32 via simple wires
- All communication over WiFi - no wiring to Chromebook
- ESPHome or custom firmware for ESP32
- `python-kasa` library controls smart plugs locally

---

## Chromebook Setup

### Enable Linux (Crostini)
1. Go to **Settings > Advanced > Developers > Linux development environment**
2. Turn it on and wait for installation
3. Open the Linux terminal

### Install Required Software
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install ESPHome for programming ESP32
pip3 install esphome

# Install Kasa smart plug control
pip3 install python-kasa

# Clone your project
git clone https://github.com/yourusername/sol-cannabis.git
```

### USB Serial for ESP32 Programming
To program ESP32 boards from Chromebook:
1. Go to `chrome://flags/#crostini-usb-support`
2. Enable "Crostini Usb Allow Unsupported"
3. Restart Chromebook
4. When plugging in ESP32, ChromeOS will ask to connect it to Linux - say yes

**Alternative:** Use [ESP Web Tools](https://web.esphome.io/) to flash ESP32 directly from Chrome browser!

---

## Budget Component List (Cheapest Effective Build)

### Tier 1: Ultra-Budget (~$80-100)

| Component | Price | Source | Notes |
|-----------|-------|--------|-------|
| Chromebook | FREE | You have it! | Any model with Linux support |
| ESP32 DevKit (2x) | $6-10 | [AliExpress](https://www.aliexpress.com/w/wholesale-esp32-development-board.html) | One for sensors, one backup |
| DHT22 Sensor | $2-5 | [AliExpress](https://www.aliexpress.com/w/wholesale-dht22.html) | Temp + Humidity |
| Capacitive Soil Moisture | $2-3 | [AliExpress](https://www.aliexpress.com/w/wholesale-capacitive+soil+moisture+sensor.html) | Corrosion-resistant |
| Kasa Smart Plugs (4x) | $40-60 | Craigslist/Used | Control lights, fans |
| USB Webcam | $10-20 | Craigslist/Used | For timelapse |
| Grow Tent 2x2 | $30-50 | Craigslist | Check listings below |
| LED Grow Light | $20-60 | Craigslist | Check listings below |
| Basic Fan | $10-15 | Target/Walmart | Clip fan or PC fan |
| Jumper Wires | $5 | Amazon/AliExpress | Connect sensors to ESP32 |
| **TOTAL** | **~$125-230** | | Much less with used finds! |

### Tier 2: Recommended (~$200-350)

| Component | Price | Source | Notes |
|-----------|-------|--------|-------|
| Everything in Tier 1 | - | - | - |
| + MH-Z19 CO2 Sensor | $15-20 | [AliExpress](https://www.aliexpress.com/w/wholesale-mh-z19.html) | Good accuracy for price |
| + BH1750 Light Sensor | $3-5 | [AliExpress](https://www.aliexpress.com/w/wholesale-bh1750.html) | Lux measurement |
| + Peristaltic Pump | $10-15 | [Amazon](https://www.amazon.com/s?k=peristaltic+pump+12v) | Automated watering |
| + 12V Power Supply | $10 | Amazon | For pump |
| + Better Grow Light | $60-100 | Amazon/Used | Mars Hydro or Spider Farmer |
| + AC Infinity Fan Kit | $80-100 | Amazon/Used | With controller |
| **TOTAL** | **~$300-400** | | |

---

## Local East Bay Sources

### Hydroponic Stores (Pick Up Today!)

1. **Bay Area Garden Supply Hydroponics** - Oakland
   - Address: 1667 14th Street, Oakland, CA
   - [Yelp Listing](https://www.yelp.com/biz/bay-area-garden-supply-hydroponics-oakland)
   - Good for: Grow tents, lights, nutrients, fans

2. **3rd Street Hydroponics Warehouse** - Oakland/Jack London Square
   - 50+ year family business
   - Huge inventory: hydroponics, grow lights, nutrients, filtration
   - [East Bay Express Best Of](https://eastbayexpress.com/best-hydroponics-store-1/)

3. **Berkeley Indoor Garden** - Berkeley
   - Knowledgeable staff, quality equipment
   - [East Bay Express Best Of](https://eastbayexpress.com/best-indoor-growing-supply-store-1/)

4. **DS Urban Farm** - East Bay
   - Phone: 510-430-8889
   - Wholesale hydroponic supplier
   - [Website](https://dsurbanfarm.com/)

### Electronics Stores

1. **Micro Center Santa Clara** (NEW - Opened May 2025!)
   - Address: 5201 Stevens Creek Blvd, Santa Clara, CA
   - [Store Page](https://www.microcenter.com/site/stores/santa-clara.aspx)
   - Great for: ESP32, Arduino, sensors, cables, SD cards
   - 40,000 sq ft, 20,000+ products
   - ~45 min drive from Oakland but worth it for electronics

2. **Anchor Electronics** - Santa Clara
   - Bay Area fixture for 40+ years
   - [Website](https://anchor-electronics.com/)
   - Good for: Components, connectors, tools

3. **Excess Solutions** - South Bay
   - Electronics surplus (bought HSC/Halted inventory)
   - [Website](https://excesssolutions.com/)
   - Good for: Random deals, surplus components

---

## Craigslist East Bay - Live Search Links

**Bookmark these for daily checking!**

### Grow Equipment
- [Grow Tent - East Bay](https://sfbay.craigslist.org/search/eby/sss?query=grow+tent)
- [LED Grow Light - East Bay](https://sfbay.craigslist.org/search/eby/sss?query=led+grow+light)
- [Hydroponics - East Bay](https://sfbay.craigslist.org/search/eby/sss?query=hydroponics)
- [Gorilla Grow Tent - SF Bay](https://sfbay.craigslist.org/search/sss?query=gorilla+grow+tent&purveyor=owner)
- [Inline Fan - East Bay](https://sfbay.craigslist.org/search/eby/sss?query=inline+fan+carbon)
- [AC Infinity - SF Bay](https://sfbay.craigslist.org/search/sss?query=ac+infinity)

### Electronics
- [Raspberry Pi - SF Bay](https://sfbay.craigslist.org/search/sss?query=raspberry+pi)
- [Arduino/ESP32 - SF Bay](https://sfbay.craigslist.org/search/sss?query=arduino+OR+esp32)
- [Smart Plug - SF Bay](https://sfbay.craigslist.org/search/sss?query=smart+plug+kasa)
- [Webcam - SF Bay](https://sfbay.craigslist.org/search/sss?query=webcam+logitech)

### Current Great Deals Found (as of research date)

| Item | Price | Location | Link/Search |
|------|-------|----------|-------------|
| Complete 2x2 Tent + Light + Fan | **$40** | Oakland Hills | [Search](https://sfbay.craigslist.org/search/eby/sss?query=grow+tent) |
| Vivosun 3x3 Grow Tent | **$30** | Union City | [Search](https://sfbay.craigslist.org/search/eby/sss?query=vivosun+tent) |
| 24x24x48 Tent + Light + Filter | **$100** | Oakland Lake Merritt | [Search](https://sfbay.craigslist.org/search/eby/sss?query=grow+tent) |
| Vivosun Complete Setup | **$220** | El Cerrito | [Search](https://sfbay.craigslist.org/search/eby/sss?query=vivosun) |
| HLG 260W V2 LED (2x) | **$175** | Fremont | [Search](https://sfbay.craigslist.org/search/eby/sss?query=hlg+led) |
| 2x Phlizon LED 600W | **$20** | Union City | [Search](https://sfbay.craigslist.org/search/eby/sss?query=phlizon) |
| FREE Grow Equipment | **FREE** | Alameda | [Search](https://sfbay.craigslist.org/search/eby/sss?query=grow+equipment) |

---

## Other Marketplaces

### Facebook Marketplace
Direct search links (must be logged in):
- [Grow Tent - Oakland](https://www.facebook.com/marketplace/oakland/search?query=grow%20tent)
- [LED Grow Light - Oakland](https://www.facebook.com/marketplace/oakland/search?query=led%20grow%20light)
- [Smart Plug - Oakland](https://www.facebook.com/marketplace/oakland/search?query=smart%20plug)

### OfferUp
- [Oakland General](https://offerup.com/explore/sc/ca/oakland)
- [Free Items Oakland](https://offerup.com/explore/sck/ca/oakland/free/)
- Search "grow tent", "grow light", "hydroponics"

### Nextdoor
Check your local Nextdoor for neighbors selling grow equipment - often the best deals!

---

## ESP32 Sensor Node Setup

### Hardware Connections

```
ESP32 DevKit V1
├── 3.3V ──────── DHT22 VCC (pin 1)
├── GPIO 4 ────── DHT22 Data (pin 2) + 4.7kΩ to 3.3V
├── GND ───────── DHT22 GND (pin 4)
│
├── 3.3V ──────── Soil Sensor VCC
├── GPIO 34 ───── Soil Sensor Signal (Analog)
├── GND ───────── Soil Sensor GND
│
├── 3.3V ──────── BH1750 VCC
├── GPIO 21 ───── BH1750 SDA
├── GPIO 22 ───── BH1750 SCL
├── GND ───────── BH1750 GND
│
└── (Optional CO2: MH-Z19)
    ├── 5V ──────── MH-Z19 VIN
    ├── GPIO 16 ─── MH-Z19 TX
    ├── GPIO 17 ─── MH-Z19 RX
    └── GND ─────── MH-Z19 GND
```

### ESPHome Configuration

Create `grow-sensors.yaml`:

```yaml
esphome:
  name: grow-sensors
  platform: ESP32
  board: esp32dev

wifi:
  ssid: "YOUR_WIFI_SSID"
  password: "YOUR_WIFI_PASSWORD"

  # Enable fallback hotspot
  ap:
    ssid: "Grow-Sensors Fallback"
    password: "fallback123"

captive_portal:

# Enable logging
logger:

# Enable Home Assistant API (or use MQTT)
api:
  password: "your_api_password"

ota:
  password: "your_ota_password"

# Web server for direct access
web_server:
  port: 80

# Sensors
sensor:
  # DHT22 Temperature & Humidity
  - platform: dht
    pin: GPIO4
    model: DHT22
    temperature:
      name: "Grow Tent Temperature"
      id: temp
    humidity:
      name: "Grow Tent Humidity"
      id: humidity
    update_interval: 30s

  # Calculated VPD
  - platform: template
    name: "Grow Tent VPD"
    unit_of_measurement: "kPa"
    lambda: |-
      float t = id(temp).state;
      float h = id(humidity).state;
      float svp = 0.6108 * exp((17.27 * t) / (t + 237.3));
      float vpd = svp * (1 - h / 100);
      return vpd;
    update_interval: 30s

  # Soil Moisture (Analog)
  - platform: adc
    pin: GPIO34
    name: "Soil Moisture"
    update_interval: 60s
    unit_of_measurement: "%"
    filters:
      - calibrate_linear:
          - 0.0 -> 100.0  # Wet
          - 3.3 -> 0.0    # Dry

  # Light Sensor (BH1750)
  - platform: bh1750
    name: "Light Level"
    address: 0x23
    update_interval: 30s

  # Optional: MH-Z19 CO2
  # - platform: mhz19
  #   co2:
  #     name: "CO2 Level"
  #   uart_id: uart_co2
  #   update_interval: 60s

# uart:
#   id: uart_co2
#   tx_pin: GPIO17
#   rx_pin: GPIO16
#   baud_rate: 9600
```

### Flash ESP32 from Chromebook

**Option 1: ESPHome CLI**
```bash
# First time (USB required)
esphome run grow-sensors.yaml

# After first flash (over WiFi)
esphome run grow-sensors.yaml --device grow-sensors.local
```

**Option 2: ESP Web Tools (Browser-based)**
1. Go to [web.esphome.io](https://web.esphome.io/)
2. Connect ESP32 via USB
3. Click "Connect" and select the serial port
4. Flash directly from browser!

---

## Smart Plug Control

### python-kasa Setup

```bash
# Install
pip3 install python-kasa

# Discover devices on network
kasa discover

# Control specific device
kasa --host 192.168.1.100 on    # Turn on
kasa --host 192.168.1.100 off   # Turn off
kasa --host 192.168.1.100 state # Check status
```

### Python Script Example

```python
import asyncio
from kasa import SmartPlug

async def control_light(ip, state):
    plug = SmartPlug(ip)
    await plug.update()
    if state:
        await plug.turn_on()
    else:
        await plug.turn_off()
    print(f"Light is now {'ON' if state else 'OFF'}")

# Turn grow light on
asyncio.run(control_light("192.168.1.100", True))
```

### Recommended Kasa Plug Assignment

| Plug | IP (example) | Controls |
|------|--------------|----------|
| Plug 1 | 192.168.1.100 | Grow Light |
| Plug 2 | 192.168.1.101 | Exhaust Fan |
| Plug 3 | 192.168.1.102 | Circulation Fan |
| Plug 4 | 192.168.1.103 | Humidifier |

**Note:** Older Kasa plugs work locally without cloud credentials. Newer models may require initial setup via Kasa app + credentials for `python-kasa`.

---

## Best Value New Equipment (Amazon)

### Grow Tent Kits

| Kit | Price | Best For | Link |
|-----|-------|----------|------|
| Mars Hydro 2x2 + TS600 | ~$170 | Beginners, 1-2 plants | [Amazon](https://www.amazon.com/s?k=mars+hydro+2x2+kit) |
| Mars Hydro 3x3 + TS1000 | ~$250 | Best value, 2-4 plants | [Amazon](https://www.amazon.com/MARS-HYDRO-2-3x2-3ft-Hydroponics-Ventilation/dp/B088STYP1X) |
| IPOW 2x2 Complete | ~$180 | Budget complete kit | [Amazon](https://www.amazon.com/IPOW-Complete-3-3x3-3ft-Hydroponics-Ventilation/dp/B091CQQP1Y) |

### Individual LED Lights (if buying separately)

| Light | Wattage | Coverage | Price | Best For |
|-------|---------|----------|-------|----------|
| Mars Hydro TS600 | 100W | 2x2 veg, 1.5x1.5 flower | ~$70 | Budget 2x2 |
| Mars Hydro TS1000 | 150W | 3x3 veg, 2.5x2.5 flower | ~$90 | Best value |
| Spider Farmer SF1000 | 100W | 2x2 | ~$100 | Higher efficiency |
| Mars Hydro TSW2000 | 300W | 4x4 veg, 3x3 flower | ~$180 | Larger tent |
| Viparspectra P1000 | 100W | 2x2 | ~$60 | Cheapest decent |

### Ventilation

| Item | Price | Link |
|------|-------|------|
| AC Infinity CLOUDLINE T4 (4") | ~$90 | [Amazon](https://www.amazon.com/s?k=ac+infinity+cloudline+t4) |
| VIVOSUN 4" Inline Fan Kit | ~$40 | [Amazon](https://www.amazon.com/s?k=vivosun+4+inch+inline+fan) |
| AC Infinity Controller 67 | ~$60 | [AC Infinity](https://acinfinity.com/hydroponics-growers/controller-67-temperature-and-humidity-fan-controller-with-scheduling-cycles-dynamic-speed-data-app-ixy4/) |

**Pro Tip:** AC Infinity offers free Controller 67 upgrade if you ask support!

---

## AliExpress Budget Components

**Note:** 2-4 week shipping, but significant savings.

| Component | AliExpress Price | Amazon Price | Savings |
|-----------|------------------|--------------|---------|
| ESP32 DevKit | $3-5 | $8-12 | 50%+ |
| DHT22 | $2-4 | $8-10 | 60%+ |
| Capacitive Soil Sensor | $1-2 | $5-8 | 70%+ |
| BH1750 Light Sensor | $1-2 | $5-8 | 70%+ |
| MH-Z19 CO2 Sensor | $12-15 | $20-30 | 40%+ |
| 8-Ch Relay Module | $3-5 | $10-15 | 60%+ |
| Jumper Wires Kit | $2-3 | $8-10 | 70%+ |

**AliExpress Direct Links:**
- [ESP32 Boards](https://www.aliexpress.com/w/wholesale-esp32-development-board.html)
- [DHT22 Sensors](https://www.aliexpress.com/w/wholesale-dht22.html)
- [Soil Moisture Sensors](https://www.aliexpress.com/w/wholesale-capacitive+soil+moisture+sensor.html)
- [MH-Z19 CO2](https://www.aliexpress.com/w/wholesale-mh-z19.html)
- [LED Grow Lights](https://www.aliexpress.com/w/wholesale-led-grow-lights.html)

---

## CO2 Sensor Comparison

| Sensor | Price | Accuracy | Best For |
|--------|-------|----------|----------|
| **MH-Z19C** | $12-20 | ±50ppm | Budget choice, good enough |
| **Senseair S8 LP** | $25-35 | ±40ppm | Better accuracy, 15yr life |
| **SCD40** | $30-40 | ±50ppm | Compact, also has temp/humidity |
| **SCD30** | $45-55 | ±30ppm | Most accurate, larger |

**Recommendation:** Start with **MH-Z19C** ($15) - good enough for cannabis cultivation. Upgrade to SCD40 if you want temp/humidity in same package.

---

## Webcam Options for Timelapse

### Budget Options (Used/Craigslist)
- **Logitech C270** - $10-20 used, 720p, works great on Linux
- **Logitech C615** - $15-25 used, 1080p, good quality
- **Generic USB Webcam** - $5-15, check if Linux compatible

### New Budget Options
- **Wyze Cam** - ~$25, has built-in timelapse feature, stores to SD card
- **Generic 1080p USB** - $15-25 on Amazon

### Timelapse Setup on Chromebook Linux

```bash
# Install fswebcam
sudo apt install fswebcam

# Take a photo
fswebcam -r 1920x1080 --no-banner ~/timelapse/photo_$(date +%Y%m%d_%H%M%S).jpg

# Cron job for every 30 minutes
crontab -e
# Add: */30 * * * * fswebcam -r 1920x1080 --no-banner ~/timelapse/photo_$(date +\%Y\%m\%d_\%H\%M\%S).jpg

# Create timelapse video with ffmpeg
sudo apt install ffmpeg
ffmpeg -framerate 30 -pattern_type glob -i '*.jpg' -c:v libx264 timelapse.mp4
```

---

## Recommended Build Configurations

### Ultra-Budget: "The Scrounger" (~$80-150)

Focus on Craigslist/used equipment:

```
□ 2x2 Grow Tent (Craigslist) ........... $20-50
□ LED Light (Used/Craigslist) .......... $20-40
□ Clip Fan (Walmart) ................... $10-15
□ ESP32 DevKit (AliExpress) ............ $4
□ DHT22 Sensor (AliExpress) ............ $3
□ Capacitive Soil Sensor (AliExpress) .. $2
□ Kasa Smart Plug x2 (Used) ............ $15-25
□ Jumper Wires (Amazon) ................ $5
□ USB Webcam (Used) .................... $10-15
────────────────────────────────────────────────
TOTAL: ~$90-160
```

### Best Value: "The Smart Starter" (~$250-350)

New equipment with smart features:

```
□ Mars Hydro 2x2 or 3x3 Kit ............ $170-250
□ ESP32 DevKit x2 ...................... $10
□ DHT22 Sensor ......................... $8
□ MH-Z19 CO2 Sensor .................... $18
□ Capacitive Soil Sensor ............... $5
□ BH1750 Light Sensor .................. $5
□ Kasa Smart Plug x4 (New) ............. $50
□ 12V Peristaltic Pump ................. $15
□ USB Webcam ........................... $25
□ Jumper Wires + Misc .................. $15
────────────────────────────────────────────────
TOTAL: ~$320-400
```

### Recommended: "The Full AI Setup" (~$400-550)

Complete automation-ready setup:

```
□ 3x3 Grow Tent (Mars/AC Infinity) ..... $70-100
□ Mars Hydro TSW2000 or SF2000 ......... $150-180
□ AC Infinity T4 + Controller 67 ....... $140
□ ESP32 DevKit x2 ...................... $10
□ DHT22 + SHT31 (backup) ............... $20
□ SCD40 CO2 Sensor ..................... $40
□ Capacitive Soil Sensor x2 ............ $10
□ TSL2591 Light Sensor ................. $14
□ Kasa Smart Plug x4 ................... $50
□ 12V Peristaltic Pump ................. $20
□ Logitech C920 Webcam ................. $50
□ 12V Power Supply ..................... $15
□ Wiring + Enclosure ................... $25
────────────────────────────────────────────────
TOTAL: ~$615-735
```

---

## Daily Craigslist Search Routine

Set aside 5-10 minutes daily to check:

1. **Morning Check** - New listings from overnight
   - [Grow Tent East Bay](https://sfbay.craigslist.org/search/eby/sss?query=grow+tent&sort=date)
   - [LED Light East Bay](https://sfbay.craigslist.org/search/eby/sss?query=led+grow+light&sort=date)

2. **Set Alerts** - Craigslist doesn't have alerts, but use:
   - [IFTTT Craigslist Alerts](https://ifttt.com/craigslist)
   - Browser extensions like "Craigslist Notifier"

3. **Keywords to Search:**
   - "grow tent" / "grow kit" / "indoor grow"
   - "led grow light" / "mars hydro" / "spider farmer"
   - "ac infinity" / "inline fan" / "carbon filter"
   - "must go" / "moving sale" / "make offer"
   - "free" + "grow"

4. **Negotiation Tips:**
   - Offer 60-70% of asking price
   - Bundle multiple items for discount
   - "Can you do $X if I pick up today?"
   - Check seller history - multiple listings = motivated

---

## Quick Links Summary

### Craigslist East Bay
- [Grow Tent](https://sfbay.craigslist.org/search/eby/sss?query=grow+tent)
- [LED Grow Light](https://sfbay.craigslist.org/search/eby/sss?query=led+grow+light)
- [Hydroponics](https://sfbay.craigslist.org/search/eby/sss?query=hydroponics)
- [Smart Plug](https://sfbay.craigslist.org/search/sss?query=smart+plug+kasa)
- [Free Stuff](https://sfbay.craigslist.org/search/eby/zip)

### Facebook Marketplace
- [Search Oakland](https://www.facebook.com/marketplace/oakland)
- [Search Berkeley](https://www.facebook.com/marketplace/berkeley)

### OfferUp
- [Oakland](https://offerup.com/explore/sc/ca/oakland)
- [Berkeley](https://offerup.com/explore/sc/ca/berkeley)

### Local Stores
- [Bay Area Garden Supply](https://www.yelp.com/biz/bay-area-garden-supply-hydroponics-oakland) - Oakland
- [Berkeley Indoor Garden](https://eastbayexpress.com/best-hydroponics-store-1/) - Berkeley
- [Micro Center Santa Clara](https://www.microcenter.com/site/stores/santa-clara.aspx) - Electronics

### Online Budget
- [AliExpress ESP32](https://www.aliexpress.com/w/wholesale-esp32-development-board.html)
- [AliExpress Sensors](https://www.aliexpress.com/w/wholesale-dht22.html)
- [Amazon Grow Kits](https://www.amazon.com/s?k=grow+tent+kit+complete)

---

## HYDROPONICS: Cheapest & Fastest Setup

**RECOMMENDATION: Start with DWC (Deep Water Culture)**

DWC is the **cheapest**, **simplest**, and **most forgiving** hydroponic method. Perfect for beginners and AI automation.

### Why DWC for Cannabis?

| Factor | DWC Advantage |
|--------|---------------|
| **Cost** | $5-50 to start (DIY bucket) |
| **Complexity** | Low - just bucket, air pump, nutrients |
| **Setup Time** | 15-30 minutes |
| **Growth Speed** | 20-30% faster than soil |
| **AI Integration** | Easy - monitor pH/EC, control air pump |
| **Maintenance** | Weekly water changes, daily pH check |

---

### Ultra-Budget DIY DWC (~$5-15)

Based on the [MIGardener $5 setup](https://www.youtube.com/watch?v=BwfzlPIvGeU):

```
□ 5-gallon bucket + lid ......... FREE (bakeries, restaurants)
□ Air pump (aquarium) ........... $3-5 (Walmart fish section)
□ Air stone ..................... $1-2 (fish section)
□ Air tubing .................... FREE (comes with pump)
□ Net cups (2") ................. $2-3 or DIY from solo cups
□ Rockwool cubes ................ $2-5 (or hydroton)
□ 2" hole saw bit ............... $5-8 (reusable)
─────────────────────────────────────────────────────────
TOTAL: ~$15-25 (less if you have tools)
```

**Where to Get Free Buckets:**
- Bakeries (frosting buckets)
- Restaurants (pickle/sauce buckets)
- Home Depot paint section (ask for damaged)
- Craigslist "free" section

**DIY Steps (15 min):**
1. Drill 1-4 holes in lid with 2" hole saw (1 plant = 1 center hole, 4 plants = 4 holes)
2. Drill small hole in side for air tubing
3. Drop air stone to bottom, run tubing out
4. Fill with water + nutrients to just below net cups
5. Place rockwool/seedling in net cup
6. Plug in air pump - DONE!

---

### Budget Pre-Made DWC Kits

If you don't want to DIY:

| Kit | Price | Plants | Link |
|-----|-------|--------|------|
| **Atwater HydroPod DIY** | ~$25 | 1 | [Amazon](https://www.amazon.com/Atwater-HydroPod-Hydroponic-Nutrients-Included/dp/B0BTXPLFFR) (add your own bucket) |
| **PowerGrow 5-gal Single** | ~$35-45 | 1 | [Amazon](https://www.amazon.com/Deep-Water-Culture-DWC-Hydroponic/dp/B00CHAXYJA) |
| **Spider Farmer 2-Bucket** | ~$80 | 2 | [Spider Farmer](https://www.spider-farmer.com/products/dwc-2-buckets/) |
| **PowerGrow 4-Bucket** | ~$120 | 4 | [Amazon](https://www.amazon.com/Culture-Hydroponic-Bubbler-PowerGrow-Systems/dp/B00E5JZOZS) |

---

### Hydroponic Nutrients (Required)

**Cheapest Effective Option: General Hydroponics Flora Series**

| Size | Price | Lasts | Link |
|------|-------|-------|------|
| **16 oz 3-pack** | ~$20 | 2-3 grows | [Amazon](https://www.amazon.com/General-Hydroponics-Flora-Bloom-Fertilizer/dp/B01I4U0NYK) |
| **1 qt 3-pack** | ~$35 | 5-6 grows | [Amazon](https://www.amazon.com/General-Hydroponics-Flora-FloraMicro-FloraBloom/dp/B09M942WYB) |
| **w/ pH Kit** | ~$45 | + pH control | [Amazon](https://www.amazon.com/General-Hydroponics-Fertilizer-FloraMicro-FloraBloom/dp/B09HJSFS53) |

**Feeding by Stage (per gallon):**
| Stage | FloraGro | FloraMicro | FloraBloom |
|-------|----------|------------|------------|
| Seedling | 1/4 tsp | 1/4 tsp | 1/4 tsp |
| Veg (early) | 1 tsp | 1 tsp | 1/2 tsp |
| Veg (late) | 1.5 tsp | 1 tsp | 1/2 tsp |
| Transition | 1 tsp | 1 tsp | 1 tsp |
| Flower | 1/2 tsp | 1 tsp | 1.5 tsp |
| Late Flower | 0 | 1/2 tsp | 1.5 tsp |
| Flush | 0 | 0 | 0 |

---

### pH Control (Critical for Hydro!)

**Target pH: 5.5-6.2** (different from soil 6.0-7.0!)

| Stage | Optimal pH |
|-------|------------|
| Seedling | 5.5-6.0 |
| Vegetative | 5.5-6.5 |
| Flowering | 5.5-6.0 |

**Budget pH Options:**

| Item | Price | Notes | Link |
|------|-------|-------|------|
| **GH pH Test Kit** | ~$8 | Drops, 500 tests | [Amazon](https://www.amazon.com/s?k=general+hydroponics+ph+test+kit) |
| **pH Pen (cheap)** | ~$10-15 | Replace yearly | [Amazon](https://www.amazon.com/s?k=ph+meter+pen+hydroponics) |
| **VIVOSUN pH+TDS Kit** | ~$20 | Both meters! | [Amazon](https://www.amazon.com/VIVOSUN-Digital-TDS-Meter-Kits/dp/B0DW2PYVZ8) |
| **Apera PH20** | ~$50 | Lasts years | [Amazon](https://www.amazon.com/s?k=apera+ph20) |
| **pH Up/Down** | ~$10-15 | GH brand | [Amazon](https://www.amazon.com/s?k=general+hydroponics+ph+up+down) |

**Recommendation:** Start with the **VIVOSUN pH+TDS combo** (~$20) - gives you both pH and EC/PPM readings.

---

### EC/PPM Monitoring (Optional but Recommended)

**Target EC by Stage:**
| Stage | EC (mS/cm) | PPM (500 scale) |
|-------|------------|-----------------|
| Seedling | 0.4-0.6 | 200-300 |
| Vegetative | 1.2-1.8 | 600-900 |
| Flowering | 2.0-2.5 | 1000-1250 |
| Flush | 0.0-0.5 | 0-250 |

---

### Complete Budget Hydro Build (~$50-80)

```
□ 5-gallon bucket (free/bakery) ..... $0
□ Aquarium air pump ................ $5
□ Air stone + tubing ............... $3
□ Net cups 2" (4-pack) ............. $3
□ Hydroton clay pebbles (2L) ....... $8
□ GH Flora Series 16oz 3-pack ...... $20
□ VIVOSUN pH+TDS meter kit ......... $20
□ GH pH Up/Down kit ................ $12
□ 2" hole saw (Harbor Freight) ..... $5
─────────────────────────────────────────────
TOTAL: ~$76
```

**Or even cheaper with drops:**
```
□ DIY bucket setup ................. $10
□ GH Flora Trial Pack .............. $20
□ GH pH Test Kit (drops) ........... $8
□ GH pH Up/Down .................... $12
─────────────────────────────────────────────
TOTAL: ~$50
```

---

### Craigslist Hydro Searches

- [Hydroponics - East Bay](https://sfbay.craigslist.org/search/eby/sss?query=hydroponics)
- [DWC System - SF Bay](https://sfbay.craigslist.org/search/sss?query=dwc)
- [Air Pump - SF Bay](https://sfbay.craigslist.org/search/sss?query=air+pump+aquarium)
- [AeroGarden - SF Bay](https://sfbay.craigslist.org/search/sss?query=aerogarden)
- [Water Tank - SF Bay](https://sfbay.craigslist.org/search/sss?query=Water+tank)

---

### Hydroponic Automation with ESP32

Add these sensors for AI-controlled hydroponics:

**Water-Specific Sensors:**
| Sensor | Price | Purpose | Link |
|--------|-------|---------|------|
| **DS18B20 Waterproof** | $2-3 | Water temp | [AliExpress](https://www.aliexpress.com/w/wholesale-ds18b20-waterproof.html) |
| **Gravity pH Sensor** | $20-30 | pH monitoring | [Amazon](https://www.amazon.com/s?k=gravity+analog+ph+sensor) |
| **TDS/EC Sensor** | $8-15 | Nutrient strength | [AliExpress](https://www.aliexpress.com/w/wholesale-tds-sensor-arduino.html) |
| **Float Switch** | $3-5 | Water level | [Amazon](https://www.amazon.com/s?k=float+switch+water+level) |

**ESP32 Water Temp Setup:**
```yaml
# ESPHome config for DS18B20 water temp
sensor:
  - platform: dallas
    address: 0x1234567890ABCDEF  # Your sensor address
    name: "Reservoir Temperature"
    update_interval: 60s
```

**Ideal Reservoir Temp: 65-72°F (18-22°C)**

---

### Quick Hydro Comparison

| Method | Cost | Setup Time | Difficulty | Yield | AI Automation |
|--------|------|-----------|------------|-------|---------------|
| **DIY DWC Bucket** | $15-25 | 15 min | Easy | Good | Easy |
| **Pre-made DWC** | $35-80 | 5 min | Easiest | Good | Easy |
| **Kratky (Passive)** | $5-10 | 10 min | Easiest | Lower | N/A (no pump) |
| **NFT System** | $50-150 | 1-2 hrs | Medium | High | Medium |
| **Ebb & Flow** | $80-200 | 2-3 hrs | Medium | High | Medium |
| **Aeroponics** | $150-500 | 3-5 hrs | Hard | Highest | Complex |

**RECOMMENDATION:** Start with **DIY DWC bucket** or **Atwater HydroPod kit**. Cheapest, fastest, works great for 1-2 cannabis plants.

---

### Hydro vs Soil: Quick Decision

**Choose HYDRO if:**
- Want faster growth (20-30%)
- Have limited space
- Want to automate feeding
- Willing to check pH daily
- Want maximum yield

**Choose SOIL if:**
- First time grower
- Want lowest maintenance
- Less daily attention available
- Prefer "organic" approach
- Budget is extremely tight

**Hybrid Option:** Start seeds in soil, transplant to DWC at week 3-4 after roots establish.

---

## Resources

### Chromebook + Arduino/ESP32
- [Programming Arduino from Chromebook](https://abarry.org/programming-an-arduino-from-a-chromebook-with-crostini/)
- [ESP Web Tools](https://web.esphome.io/) - Flash ESP32 from browser
- [ESPHome Docs](https://esphome.io/)

### Smart Home Integration
- [python-kasa GitHub](https://github.com/python-kasa/python-kasa)
- [Home Assistant on Chromebook](https://www.makeuseof.com/linux-home-assistant-chromebook/)

### Cannabis Cultivation
- [Grow Weed Easy](https://www.growweedeasy.com/) - Comprehensive guides
- [VPD Chart](https://vpdchart.com/) - Target VPD by growth stage

### Hydroponics
- [MIGardener $5 DWC Video](https://www.youtube.com/watch?v=BwfzlPIvGeU) - DIY bucket setup
- [General Hydroponics Feed Charts](https://generalhydroponics.com/resources/floraseries-feedcharts/) - Official feeding schedules
- [Hydrobuilder pH Guide](https://hydrobuilder.com/learn/best-ph-testers-soil-hydroponics/) - pH meter reviews
- [Cocoforcannabis.com](https://www.cocoforcannabis.com/) - Great hydro/coco guides

---

*Last Updated: 2025-01-13*
*Prices and availability change frequently - always check current listings!*
