# 🤖 Arduino-Based Alternatives & Expansions Guide

**Date:** January 14, 2026  
**Purpose:** Explore Arduino/ESP32-based alternatives and expansions to complement or replace Raspberry Pi automation

---

## 🎯 Why Consider Arduino/ESP32?

| Feature | Raspberry Pi | Arduino/ESP32 | Best For |
|---------|--------------|---------------|----------|
| **Cost** | $55-75 | $3-30 | ESP32 wins for distributed nodes |
| **Power Use** | 3-5W idle | 0.02-0.5W | ESP32 for battery/solar backup |
| **Boot Time** | 30-60 seconds | Instant | Arduino for critical safety loops |
| **Analog Inputs** | None (needs ADC) | 6-18 native | Arduino for analog sensors |
| **PWM Channels** | Limited software PWM | 16+ hardware PWM | ESP32 for dimmer control |
| **Real-time** | No (Linux overhead) | Yes (bare metal) | Arduino for time-critical control |
| **WiFi Built-in** | Yes | ESP32/ESP8266 yes | Both capable |
| **Python Support** | Native | MicroPython only | Pi for AI integration |
| **Community** | Large | Massive | Both excellent |

**Recommended Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI (BRAIN)                         │
│   - Grok AI Agent                                               │
│   - Database/Logging                                            │
│   - Web Dashboard                                               │
│   - High-level Decision Making                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ MQTT / Serial / I2C
         ┌───────────────┼───────────────────┐
         ▼               ▼                   ▼
┌─────────────┐  ┌─────────────┐     ┌─────────────┐
│  ESP32 #1   │  │  ESP32 #2   │     │ Arduino Nano│
│ Environment │  │  Irrigation │     │ Safety Loop │
│ Sensors     │  │  Control    │     │ (Failsafe)  │
└─────────────┘  └─────────────┘     └─────────────┘
```

---

## 📋 Option Categories

### 1. **SENSOR NODES** - Replace/Supplement Pi Sensor Reading
### 2. **ACTUATOR CONTROLLERS** - Direct PWM/Relay Control
### 3. **SAFETY FAILSAFE** - Hardware-level Emergency Shutdown
### 4. **COMPLETE REPLACEMENT** - Full Arduino-only System
### 5. **SPECIALIZED MODULES** - pH/EC Dosing, CO2, etc.

---

## 🛒 Board Comparison & Shopping

### ESP32 Family (Recommended for WiFi Nodes)

| Board | Price | WiFi | Analog Pins | PWM | Best For |
|-------|-------|------|-------------|-----|----------|
| **ESP32-WROOM-32** | $5-8 | ✅ | 18 | 16 | General purpose, most versatile |
| **ESP32-S3** | $8-12 | ✅ | 20 | 8 | Camera support, AI acceleration |
| **ESP32-C3** | $3-5 | ✅ | 6 | 6 | Ultra low cost nodes |
| **Wemos D1 Mini** (ESP8266) | $3-4 | ✅ | 1 | 4 | Cheapest WiFi node |
| **ESP32 DevKit** | $8-10 | ✅ | 18 | 16 | Best for prototyping |

**Amazon Links:**
- [ESP32 DevKit (2-pack)](https://www.amazon.com/s?k=esp32+devkit+2+pack) ~$12-15
- [Wemos D1 Mini (3-pack)](https://www.amazon.com/s?k=wemos+d1+mini+3+pack) ~$12-15
- [ESP32-S3 DevKit](https://www.amazon.com/s?k=esp32-s3+devkit) ~$10-15

### Arduino Family (For Reliability/Real-time)

| Board | Price | Analog | Digital | PWM | Best For |
|-------|-------|--------|---------|-----|----------|
| **Arduino Nano** | $3-5 | 8 | 14 | 6 | Small form factor, reliable |
| **Arduino Uno R4 WiFi** | $27 | 6 | 14 | 6 | Official WiFi Arduino |
| **Arduino Nano 33 IoT** | $25 | 8 | 14 | 11 | Pro-grade WiFi+BLE |
| **Arduino Nano Every** | $12 | 8 | 14 | 5 | Budget official Arduino |
| **Arduino Mega 2560** | $15-20 | 16 | 54 | 15 | Maximum I/O |

**Amazon Links:**
- [Arduino Nano Clone (3-pack)](https://www.amazon.com/s?k=arduino+nano+v3+3+pack) ~$12-15
- [Arduino Nano Every](https://www.amazon.com/s?k=arduino+nano+every) ~$12
- [Arduino Uno R4 WiFi](https://www.amazon.com/s?k=arduino+uno+r4+wifi) ~$27

---

## 🌡️ OPTION 1: Environment Sensor Node

**Purpose:** Offload sensor reading from Pi, add redundancy, enable multiple zones

### Bill of Materials

| Component | Purpose | Price | Link |
|-----------|---------|-------|------|
| ESP32 DevKit | Main controller | $6 | [Amazon](https://www.amazon.com/s?k=esp32+devkit) |
| DHT22/AM2302 | Temp/Humidity | $5 | [Amazon](https://www.amazon.com/s?k=dht22) |
| SCD40 | CO2 Sensor | $35 | [Amazon](https://www.amazon.com/s?k=scd40+co2) |
| BH1750 | Light Sensor | $3 | [Amazon](https://www.amazon.com/s?k=bh1750) |
| Capacitive Soil Sensor | Moisture | $2 | [Amazon](https://www.amazon.com/s?k=capacitive+soil+moisture) |
| 5V USB Power | Power supply | $5 | Already have |
| Project Box | Enclosure | $5 | [Amazon](https://www.amazon.com/s?k=project+box+electronics) |
| **TOTAL** | | **~$61** | |

### Wiring Diagram

```
ESP32 DevKit
├── 3.3V ─────┬─── DHT22 VCC
│             ├─── SCD40 VCC
│             ├─── BH1750 VCC
│             └─── Soil Sensor VCC
│
├── GND ──────┬─── DHT22 GND
│             ├─── SCD40 GND
│             ├─── BH1750 GND
│             └─── Soil Sensor GND
│
├── GPIO 4 ───── DHT22 DATA (with 10K pullup)
│
├── GPIO 21 (SDA) ─┬─ SCD40 SDA
│                  └─ BH1750 SDA
│
├── GPIO 22 (SCL) ─┬─ SCD40 SCL
│                  └─ BH1750 SCL
│
└── GPIO 34 (ADC) ─── Soil Sensor AOUT
```

### Sample Code (PlatformIO/Arduino)

```cpp
// ESP32 Environment Sensor Node
// Publishes to MQTT for Pi consumption

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <Wire.h>
#include <BH1750.h>
#include <SensirionI2CScd4x.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* mqtt_server = "192.168.1.100"; // Your Pi's IP

// Pins
#define DHT_PIN 4
#define SOIL_PIN 34

// Objects
WiFiClient espClient;
PubSubClient mqtt(espClient);
DHT dht(DHT_PIN, DHT22);
BH1750 lightMeter;
SensirionI2CScd4x scd4x;

// Timing
unsigned long lastPublish = 0;
const long publishInterval = 30000; // 30 seconds

void setup() {
  Serial.begin(115200);
  
  // Initialize sensors
  dht.begin();
  Wire.begin();
  lightMeter.begin();
  scd4x.begin(Wire);
  scd4x.startPeriodicMeasurement();
  
  // Connect WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  
  // Connect MQTT
  mqtt.setServer(mqtt_server, 1883);
}

void loop() {
  if (!mqtt.connected()) {
    reconnect();
  }
  mqtt.loop();
  
  if (millis() - lastPublish > publishInterval) {
    publishSensorData();
    lastPublish = millis();
  }
}

void publishSensorData() {
  // Read DHT22
  float temp_f = dht.readTemperature(true);
  float humidity = dht.readHumidity();
  
  // Read BH1750 (lux)
  float lux = lightMeter.readLightLevel();
  
  // Read SCD40 (CO2)
  uint16_t co2;
  float scd_temp, scd_humidity;
  scd4x.readMeasurement(co2, scd_temp, scd_humidity);
  
  // Read soil moisture (0-4095 on ESP32)
  int soilRaw = analogRead(SOIL_PIN);
  float soilPercent = map(soilRaw, 4095, 1500, 0, 100); // Calibrate these values!
  
  // Calculate VPD
  float vpd = calculateVPD(temp_f, humidity);
  
  // Build JSON
  StaticJsonDocument<512> doc;
  doc["temperature_f"] = temp_f;
  doc["humidity"] = humidity;
  doc["vpd_kpa"] = vpd;
  doc["co2_ppm"] = co2;
  doc["lux"] = lux;
  doc["soil_moisture"] = soilPercent;
  doc["node_id"] = "env_node_1";
  
  char buffer[512];
  serializeJson(doc, buffer);
  
  mqtt.publish("grok/sensors/environment", buffer);
  Serial.println("Published sensor data");
}

float calculateVPD(float temp_f, float humidity) {
  float temp_c = (temp_f - 32.0) * 5.0 / 9.0;
  float leaf_temp_c = temp_c - 2.0; // Leaf temp offset
  float svp_leaf = 0.6108 * exp((17.27 * leaf_temp_c) / (leaf_temp_c + 237.3));
  float svp_air = 0.6108 * exp((17.27 * temp_c) / (temp_c + 237.3));
  float avp = svp_air * (humidity / 100.0);
  return svp_leaf - avp;
}

void reconnect() {
  while (!mqtt.connected()) {
    if (mqtt.connect("ESP32_EnvNode")) {
      Serial.println("MQTT connected");
    } else {
      delay(5000);
    }
  }
}
```

---

## 💧 OPTION 2: Irrigation & Dosing Controller

**Purpose:** Precise pump control for watering, nutrients, pH adjustment

### Bill of Materials

| Component | Purpose | Price | Link |
|-----------|---------|-------|------|
| Arduino Nano | Controller | $4 | [Amazon](https://www.amazon.com/s?k=arduino+nano+v3) |
| 4-Channel Relay Module | Pump control | $6 | [Amazon](https://www.amazon.com/s?k=4+channel+relay+module+5v) |
| Peristaltic Pump 12V (x3) | pH Up/Down/Nutrients | $30 | [Amazon](https://www.amazon.com/s?k=peristaltic+pump+12v) |
| 12V 3A Power Supply | Pump power | $10 | [Amazon](https://www.amazon.com/s?k=12v+3a+power+supply) |
| Float Switch (x2) | Water level | $6 | [Amazon](https://www.amazon.com/s?k=float+switch+water+level) |
| Flow Sensor | Volume tracking | $8 | [Amazon](https://www.amazon.com/s?k=water+flow+sensor+arduino) |
| **TOTAL** | | **~$64** | |

### Wiring Diagram

```
Arduino Nano
├── VIN (12V) ────── 12V Power Supply
├── GND ──────────── Common Ground
│
├── D2 ───────────── Relay 1 (Main Pump)
├── D3 ───────────── Relay 2 (pH Up Pump)
├── D4 ───────────── Relay 3 (pH Down Pump)
├── D5 ───────────── Relay 4 (Nutrient Pump)
│
├── D6 ───────────── Float Switch Low (NC)
├── D7 ───────────── Float Switch High (NC)
│
├── D8 ───────────── Flow Sensor Signal
│
└── RX/TX ─────────── To Raspberry Pi Serial
```

### Sample Code

```cpp
// Arduino Irrigation Controller
// Receives commands from Pi via Serial

#include <ArduinoJson.h>

// Relay pins (active LOW)
#define RELAY_MAIN_PUMP 2
#define RELAY_PH_UP 3
#define RELAY_PH_DOWN 4
#define RELAY_NUTRIENTS 5

// Float switches
#define FLOAT_LOW 6
#define FLOAT_HIGH 7

// Flow sensor
#define FLOW_SENSOR 8
volatile int flowPulses = 0;
float flowRate = 0;

// Safety limits
const unsigned long MAX_PUMP_RUNTIME = 120000; // 2 minutes max
unsigned long pumpStartTime = 0;
bool pumpRunning = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize relays (HIGH = OFF for active-low relays)
  pinMode(RELAY_MAIN_PUMP, OUTPUT);
  pinMode(RELAY_PH_UP, OUTPUT);
  pinMode(RELAY_PH_DOWN, OUTPUT);
  pinMode(RELAY_NUTRIENTS, OUTPUT);
  
  digitalWrite(RELAY_MAIN_PUMP, HIGH);
  digitalWrite(RELAY_PH_UP, HIGH);
  digitalWrite(RELAY_PH_DOWN, HIGH);
  digitalWrite(RELAY_NUTRIENTS, HIGH);
  
  // Float switches with pullup
  pinMode(FLOAT_LOW, INPUT_PULLUP);
  pinMode(FLOAT_HIGH, INPUT_PULLUP);
  
  // Flow sensor interrupt
  pinMode(FLOW_SENSOR, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR), flowPulse, RISING);
  
  Serial.println("Irrigation Controller Ready");
}

void loop() {
  // Safety check - auto-shutoff
  if (pumpRunning && (millis() - pumpStartTime > MAX_PUMP_RUNTIME)) {
    emergencyStop();
    Serial.println("{\"error\":\"MAX_RUNTIME_EXCEEDED\"}");
  }
  
  // Check for commands
  if (Serial.available()) {
    processCommand();
  }
  
  // Calculate flow rate every second
  static unsigned long lastFlowCalc = 0;
  if (millis() - lastFlowCalc > 1000) {
    // Typical flow sensor: 7.5 pulses per liter
    flowRate = (flowPulses / 7.5) * 60; // L/min
    flowPulses = 0;
    lastFlowCalc = millis();
  }
}

void processCommand() {
  StaticJsonDocument<256> doc;
  String input = Serial.readStringUntil('\n');
  
  DeserializationError error = deserializeJson(doc, input);
  if (error) {
    Serial.println("{\"error\":\"PARSE_ERROR\"}");
    return;
  }
  
  const char* action = doc["action"];
  
  if (strcmp(action, "irrigate") == 0) {
    int duration = doc["duration_ms"] | 10000;
    startPump(RELAY_MAIN_PUMP, min(duration, (int)MAX_PUMP_RUNTIME));
  }
  else if (strcmp(action, "dose_ph_up") == 0) {
    int ml = doc["ml"] | 5;
    doseVolume(RELAY_PH_UP, ml);
  }
  else if (strcmp(action, "dose_ph_down") == 0) {
    int ml = doc["ml"] | 5;
    doseVolume(RELAY_PH_DOWN, ml);
  }
  else if (strcmp(action, "dose_nutrients") == 0) {
    int ml = doc["ml"] | 10;
    doseVolume(RELAY_NUTRIENTS, ml);
  }
  else if (strcmp(action, "status") == 0) {
    sendStatus();
  }
  else if (strcmp(action, "stop") == 0) {
    emergencyStop();
  }
}

void startPump(int relay, unsigned long duration) {
  // Safety: Check water level first
  if (digitalRead(FLOAT_LOW) == LOW) {
    Serial.println("{\"error\":\"LOW_WATER_LEVEL\"}");
    return;
  }
  
  digitalWrite(relay, LOW); // Active low
  pumpRunning = true;
  pumpStartTime = millis();
  
  // Non-blocking delay - pump will auto-stop in loop()
  Serial.print("{\"status\":\"PUMP_STARTED\",\"duration_ms\":");
  Serial.print(duration);
  Serial.println("}");
}

void doseVolume(int relay, int ml) {
  // Calibrate: typical peristaltic pump ~1.5ml/sec
  unsigned long duration = ml * 667; // ms per ml
  startPump(relay, duration);
}

void emergencyStop() {
  digitalWrite(RELAY_MAIN_PUMP, HIGH);
  digitalWrite(RELAY_PH_UP, HIGH);
  digitalWrite(RELAY_PH_DOWN, HIGH);
  digitalWrite(RELAY_NUTRIENTS, HIGH);
  pumpRunning = false;
  Serial.println("{\"status\":\"ALL_PUMPS_STOPPED\"}");
}

void sendStatus() {
  StaticJsonDocument<256> doc;
  doc["water_low"] = digitalRead(FLOAT_LOW) == LOW;
  doc["water_high"] = digitalRead(FLOAT_HIGH) == LOW;
  doc["flow_rate_lpm"] = flowRate;
  doc["pump_running"] = pumpRunning;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}

void flowPulse() {
  flowPulses++;
}
```

---

## 🔴 OPTION 3: Hardware Safety Failsafe

**Purpose:** Independent watchdog that ensures critical safety even if Pi crashes

### Why This Matters
- Pi can crash, freeze, or lose power
- Software bugs can cause runaway conditions
- This Arduino acts as an independent safety layer
- **Cannot be overridden by AI** - hardware-level protection

### Bill of Materials

| Component | Purpose | Price | Link |
|-----------|---------|-------|------|
| Arduino Nano | Safety controller | $4 | [Amazon](https://www.amazon.com/s?k=arduino+nano+v3) |
| DHT22 | Independent temp reading | $5 | [Amazon](https://www.amazon.com/s?k=dht22) |
| 2-Channel Relay (NO) | Emergency shutoff | $4 | [Amazon](https://www.amazon.com/s?k=2+channel+relay+module) |
| Buzzer | Audio alarm | $2 | [Amazon](https://www.amazon.com/s?k=piezo+buzzer+arduino) |
| LED (Red/Green) | Status indicator | $1 | [Amazon](https://www.amazon.com/s?k=led+5mm+red+green) |
| **TOTAL** | | **~$16** | |

### Safety Rules (Hardcoded - AI Cannot Override)

```cpp
// SAFETY FAILSAFE CONTROLLER
// These limits are HARDCODED and cannot be changed by the AI

#include <DHT.h>

#define DHT_PIN 2
#define RELAY_LIGHTS 3      // Main power to lights
#define RELAY_MASTER 4      // Master power cutoff
#define BUZZER 5
#define LED_OK 6
#define LED_ALARM 7
#define HEARTBEAT_PIN 8     // Pulse from Pi

// === HARDCODED SAFETY LIMITS ===
const float TEMP_MAX_F = 95.0;        // Absolute max - thermal damage
const float TEMP_MIN_F = 50.0;        // Absolute min - cold damage
const float HUMIDITY_MAX = 90.0;      // Mold risk
const unsigned long HEARTBEAT_TIMEOUT = 120000; // 2 min without Pi heartbeat

DHT dht(DHT_PIN, DHT22);
unsigned long lastHeartbeat = 0;
bool alarmActive = false;

void setup() {
  Serial.begin(115200);
  
  pinMode(RELAY_LIGHTS, OUTPUT);
  pinMode(RELAY_MASTER, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(LED_OK, OUTPUT);
  pinMode(LED_ALARM, OUTPUT);
  pinMode(HEARTBEAT_PIN, INPUT);
  
  // Start with power ON (relay HIGH = power flows through NC contacts)
  digitalWrite(RELAY_LIGHTS, HIGH);
  digitalWrite(RELAY_MASTER, HIGH);
  
  dht.begin();
  
  Serial.println("SAFETY FAILSAFE ACTIVE");
  Serial.println("Limits: Temp 50-95F, Humidity <90%");
}

void loop() {
  // Check heartbeat from Pi
  if (digitalRead(HEARTBEAT_PIN) == HIGH) {
    lastHeartbeat = millis();
  }
  
  // Read environment
  float temp = dht.readTemperature(true); // Fahrenheit
  float humidity = dht.readHumidity();
  
  // === SAFETY CHECKS ===
  bool tempOK = (temp >= TEMP_MIN_F && temp <= TEMP_MAX_F);
  bool humidityOK = (humidity <= HUMIDITY_MAX);
  bool heartbeatOK = (millis() - lastHeartbeat < HEARTBEAT_TIMEOUT);
  
  if (!tempOK || !humidityOK) {
    triggerAlarm("ENVIRONMENT");
    
    // Over-temp: cut lights immediately
    if (temp > TEMP_MAX_F) {
      digitalWrite(RELAY_LIGHTS, LOW); // Cut lights
      Serial.println("LIGHTS CUT - OVER TEMP");
    }
  }
  
  if (!heartbeatOK && !alarmActive) {
    triggerAlarm("HEARTBEAT_LOST");
    // Don't cut power immediately - Pi might be rebooting
    // But enter safe mode
  }
  
  // All OK
  if (tempOK && humidityOK) {
    digitalWrite(LED_OK, HIGH);
    digitalWrite(LED_ALARM, LOW);
    alarmActive = false;
  }
  
  // Report status every 10 seconds
  static unsigned long lastReport = 0;
  if (millis() - lastReport > 10000) {
    Serial.print("SAFETY: Temp=");
    Serial.print(temp);
    Serial.print("F, Humidity=");
    Serial.print(humidity);
    Serial.print("%, Heartbeat=");
    Serial.println(heartbeatOK ? "OK" : "LOST");
    lastReport = millis();
  }
  
  delay(1000);
}

void triggerAlarm(const char* reason) {
  alarmActive = true;
  digitalWrite(LED_ALARM, HIGH);
  digitalWrite(LED_OK, LOW);
  
  // Audible alarm (3 beeps)
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER, HIGH);
    delay(200);
    digitalWrite(BUZZER, LOW);
    delay(200);
  }
  
  Serial.print("ALARM: ");
  Serial.println(reason);
}
```

---

## 💡 OPTION 4: LED Grow Light Dimmer Controller

**Purpose:** Precise PWM dimming for LED grow lights with 0-10V input

### Bill of Materials

| Component | Purpose | Price | Link |
|-----------|---------|-------|------|
| ESP32 DevKit | WiFi + 16-bit PWM | $6 | [Amazon](https://www.amazon.com/s?k=esp32+devkit) |
| MCP4725 DAC | 0-10V output | $5 | [Amazon](https://www.amazon.com/s?k=mcp4725+dac) |
| Op-Amp (LM358) | Voltage scaling | $2 | [Amazon](https://www.amazon.com/s?k=lm358+op+amp) |
| MOSFET (IRLZ44N) | PWM power stage | $2 | [Amazon](https://www.amazon.com/s?k=irlz44n+mosfet) |
| 12V Power Supply | For 0-10V output | $8 | [Amazon](https://www.amazon.com/s?k=12v+power+supply+1a) |
| Resistors | Voltage divider | $1 | Already have |
| **TOTAL** | | **~$24** | |

### Features
- **Sunrise/Sunset Simulation** - Gradual ramp up/down
- **PPFD Tracking** - Adjust based on light sensor feedback
- **DLI Calculation** - Track daily light integral
- **Schedule Integration** - Sync with Pi's grow schedule

### Sample Code

```cpp
// ESP32 LED Dimmer Controller
// Provides smooth dimming with 0-10V output

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_MCP4725.h>

// WiFi/MQTT
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";  
const char* mqtt_server = "192.168.1.100";

// Objects
Adafruit_MCP4725 dac;
WiFiClient espClient;
PubSubClient mqtt(espClient);

// State
int currentIntensity = 0;      // 0-100%
int targetIntensity = 0;       // 0-100%
unsigned long sunriseStart = 0;
unsigned long sunsetStart = 0;
const int RAMP_DURATION = 1800000; // 30 min sunrise/sunset

void setup() {
  Serial.begin(115200);
  
  // Initialize DAC (I2C address 0x60)
  dac.begin(0x60);
  dac.setVoltage(0, false); // Start at 0V
  
  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  
  // MQTT
  mqtt.setServer(mqtt_server, 1883);
  mqtt.setCallback(mqttCallback);
  
  Serial.println("LED Dimmer Ready");
}

void loop() {
  if (!mqtt.connected()) reconnect();
  mqtt.loop();
  
  // Handle smooth transitions
  updateDimming();
  
  delay(100);
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  if (String(topic) == "grok/lights/intensity") {
    targetIntensity = message.toInt();
    Serial.print("Target intensity: ");
    Serial.println(targetIntensity);
  }
  else if (String(topic) == "grok/lights/sunrise") {
    sunriseStart = millis();
    targetIntensity = message.toInt();
  }
  else if (String(topic) == "grok/lights/sunset") {
    sunsetStart = millis();
    targetIntensity = 0;
  }
}

void updateDimming() {
  // Handle sunrise ramp
  if (sunriseStart > 0) {
    unsigned long elapsed = millis() - sunriseStart;
    if (elapsed < RAMP_DURATION) {
      currentIntensity = map(elapsed, 0, RAMP_DURATION, 0, targetIntensity);
    } else {
      currentIntensity = targetIntensity;
      sunriseStart = 0;
    }
  }
  // Handle sunset ramp
  else if (sunsetStart > 0) {
    unsigned long elapsed = millis() - sunsetStart;
    int startIntensity = currentIntensity;
    if (elapsed < RAMP_DURATION) {
      currentIntensity = map(elapsed, 0, RAMP_DURATION, startIntensity, 0);
    } else {
      currentIntensity = 0;
      sunsetStart = 0;
    }
  }
  // Instant transition
  else if (currentIntensity != targetIntensity) {
    // Smooth step toward target
    if (currentIntensity < targetIntensity) {
      currentIntensity++;
    } else {
      currentIntensity--;
    }
  }
  
  // Convert 0-100% to 0-4095 DAC value (0-10V output)
  uint16_t dacValue = map(currentIntensity, 0, 100, 0, 4095);
  dac.setVoltage(dacValue, false);
}

void reconnect() {
  while (!mqtt.connected()) {
    if (mqtt.connect("ESP32_Dimmer")) {
      mqtt.subscribe("grok/lights/#");
    } else {
      delay(5000);
    }
  }
}
```

---

## 🧪 OPTION 5: pH/EC Dosing Controller (Hydroponics)

**Purpose:** Automated nutrient and pH management for hydroponic systems

### Bill of Materials

| Component | Purpose | Price | Link |
|-----------|---------|-------|------|
| Arduino Mega | More pins for complex system | $15 | [Amazon](https://www.amazon.com/s?k=arduino+mega+2560) |
| Atlas Scientific pH Kit | pH sensing | $70 | [Atlas Scientific](https://atlas-scientific.com/kits/ph-kit/) |
| Atlas Scientific EC Kit | EC sensing | $70 | [Atlas Scientific](https://atlas-scientific.com/kits/ec-kit/) |
| Peristaltic Pump (x4) | pH+/-, A/B nutrients | $40 | [Amazon](https://www.amazon.com/s?k=peristaltic+pump+12v) |
| 4-Channel Relay | Pump control | $6 | [Amazon](https://www.amazon.com/s?k=4+channel+relay+module) |
| DS18B20 | Water temperature | $3 | [Amazon](https://www.amazon.com/s?k=ds18b20+waterproof) |
| LCD 20x4 I2C | Local display | $10 | [Amazon](https://www.amazon.com/s?k=lcd+20x4+i2c) |
| **TOTAL** | | **~$214** | |

### Features
- Real-time pH/EC monitoring
- Automatic dosing with safety limits
- Temperature compensation
- MQTT reporting to Pi/Grok
- Local LCD display for at-a-glance status

---

## 📊 Complete System Architecture

### Hybrid Pi + Arduino/ESP32 Setup

```
┌────────────────────────────────────────────────────────────────────┐
│                      RASPBERRY PI 4 (BRAIN)                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • Grok AI Agent (decision making)                           │  │
│  │  • SQLite Database (history/logging)                         │  │
│  │  • Web Dashboard (Flask/FastAPI)                             │  │
│  │  • MQTT Broker (Mosquitto)                                   │  │
│  │  • Camera Processing (grok-4 vision)                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                    MQTT / Serial / I2C                              │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   ESP32 #1    │      │   ESP32 #2    │      │ Arduino Nano  │
│   TENT ZONE   │      │  IRRIGATION   │      │ SAFETY FAILSF │
├───────────────┤      ├───────────────┤      ├───────────────┤
│ • DHT22       │      │ • Pump relays │      │ • DHT22       │
│ • SCD40 CO2   │      │ • Flow sensor │      │ • Watchdog    │
│ • BH1750 Lux  │      │ • Float sw    │      │ • Emergency   │
│ • Soil moist  │      │ • pH dosing   │      │   cutoff      │
│ • WiFi→MQTT   │      │ • Serial→Pi   │      │ • Buzzer      │
└───────────────┘      └───────────────┘      └───────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌───────────────┐      ┌───────────────┐
            │   ESP32 #3    │      │   ESP32 #4    │
            │  LED DIMMER   │      │  FAN CONTROL  │
            ├───────────────┤      ├───────────────┤
            │ • MCP4725 DAC │      │ • PWM fans    │
            │ • 0-10V out   │      │ • Exhaust     │
            │ • Sunrise/set │      │ • Intake      │
            │ • WiFi→MQTT   │      │ • Circulation │
            └───────────────┘      └───────────────┘
```

---

## 💰 Cost Comparison

### Current Setup (Pi-Only)

| Component | Price |
|-----------|-------|
| Raspberry Pi 4 (4GB) | $55 |
| MCP3008 ADC | $10 |
| DHT22 | $8 |
| SCD40 | $45 |
| BH1750 | $4 |
| Soil Moisture | $8 |
| 8-Channel Relay | $12 |
| Kasa Smart Plugs (4) | $70 |
| **TOTAL** | **~$212** |

### Hybrid Pi + Arduino/ESP32

| Component | Price |
|-----------|-------|
| Raspberry Pi 4 (4GB) | $55 |
| ESP32 Sensor Node | $61 |
| Arduino Irrigation | $64 |
| Arduino Safety Failsafe | $16 |
| ESP32 LED Dimmer | $24 |
| **TOTAL** | **~$220** |

**Benefits of Hybrid:**
- ✅ Hardware safety layer (AI cannot override)
- ✅ Distributed processing (less Pi load)
- ✅ Redundant sensors (failover capability)
- ✅ Native PWM dimming (no smart plug hacks)
- ✅ Real-time irrigation control
- ✅ Easier expansion (add more ESP32 nodes)

---

## 🛒 Quick Shopping List (Budget Hybrid)

### Priority 1: Safety Failsafe (~$16)
- [ ] Arduino Nano Clone - $4
- [ ] DHT22 - $5
- [ ] 2-Channel Relay - $4
- [ ] Buzzer + LEDs - $3

### Priority 2: Environment Sensor Node (~$25 minimal)
- [ ] ESP32 DevKit - $6
- [ ] DHT22 - $5 (can share with failsafe)
- [ ] Capacitive Soil Sensor - $2
- [ ] BH1750 - $3
- [ ] Jumper Wires - $5
- [ ] Breadboard - $4

### Priority 3: LED Dimmer (~$24)
- [ ] ESP32 DevKit - $6
- [ ] MCP4725 DAC - $5
- [ ] LM358 Op-Amp - $2
- [ ] MOSFET + Resistors - $3
- [ ] 12V Power Supply - $8

### Priority 4: Irrigation Controller (~$64)
- [ ] Arduino Nano - $4
- [ ] 4-Channel Relay - $6
- [ ] Peristaltic Pumps (x3) - $30
- [ ] 12V 3A Power Supply - $10
- [ ] Float Switches (x2) - $6
- [ ] Flow Sensor - $8

---

## 📚 Resources

### Development Tools
- **Arduino IDE 2.0:** https://www.arduino.cc/en/software
- **PlatformIO:** https://platformio.org/ (recommended for ESP32)
- **ESPHome:** https://esphome.io/ (no-code ESP32 automation)

### Libraries Needed
```
# platformio.ini for ESP32 sensor node
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps = 
    adafruit/DHT sensor library
    claws/BH1750
    Sensirion/Sensirion I2C SCD4x
    knolleary/PubSubClient
    bblanchon/ArduinoJson
```

### MQTT Topics Structure
```
grok/
├── sensors/
│   ├── environment     # Temp, humidity, VPD, CO2
│   ├── substrate       # Soil moisture, pH, EC
│   └── light           # PPFD, DLI
├── actuators/
│   ├── lights          # On/off, intensity
│   ├── fans            # Exhaust, intake, circulation
│   ├── irrigation      # Pumps, valves
│   └── climate         # Humidifier, heater
├── safety/
│   ├── status          # OK, ALARM
│   ├── heartbeat       # Pi alive signal
│   └── alerts          # Critical notifications
└── commands/
    ├── lights/+        # Commands to light controller
    ├── irrigation/+    # Commands to irrigation
    └── override/+      # Manual overrides
```

---

## 🎯 Recommended Starting Point

**If you already have the Pi setup working:**

1. **Add Safety Failsafe first** (~$16) - Independent watchdog
2. **Add ESP32 Sensor Node** (~$25-61) - Offload sensors, add redundancy
3. **Add LED Dimmer** (~$24) - Better light control than smart plugs

**If starting fresh:**
- Consider an ESP32-only setup with ESPHome for simpler projects
- Use Home Assistant as the "brain" instead of custom Pi software
- Scale up to Pi + Grok AI when ready for advanced automation

---

*Last Updated: 2026-01-14*
*Guide created for Grok & Mon Cannabis Cultivation System*
