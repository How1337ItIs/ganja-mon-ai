# Hardware & Integration Technology Guide - Sol Cannabis

## Overview

This guide details the hardware components, sensors, actuators, and integration technologies needed to replicate and fork the SOLTOMATO project for cannabis cultivation. While SOLTOMATO doesn't publicly disclose exact hardware specifications, this guide provides industry-standard implementations.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE AI (Cloud/API)                     │
│  - Processes sensor data                                     │
│  - Generates care instructions                               │
│  - Makes autonomous decisions                                │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS/REST API / MCP Protocol
┌───────────────────────────▼─────────────────────────────────┐
│              CONTROL SERVER (Raspberry Pi/PC)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Data Collection Service                              │   │
│  │  - Reads sensors every 30-60 seconds                  │   │
│  │  - Formats data for AI                                │   │
│  │  - Sends to Claude API                                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Actuator Control Service                              │   │
│  │  - Receives AI instructions                            │   │
│  │  - Controls relays/smart switches                     │   │
│  │  - Executes watering, lighting, climate control      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Data Storage                                         │   │
│  │  - Local database (SQLite/PostgreSQL)                │   │
│  │  - Blockchain integration (Solana)                    │   │
│  │  - Historical logs                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ GPIO / I2C / SPI / WiFi / Serial
┌───────────────────────────▼─────────────────────────────────┐
│                    HARDWARE LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   SENSORS    │  │  ACTUATORS   │  │  COMMUNICATION   │  │
│  │              │  │              │  │                  │  │
│  │ - Temp/RH    │  │ - Relays     │  │ - WiFi Module    │  │
│  │ - CO2        │  │ - Smart Plugs│  │ - Bluetooth      │  │
│  │ - Soil       │  │ - Pumps      │  │ - Ethernet       │  │
│  │ - Light      │  │ - Fans       │  │                  │  │
│  │ - pH/EC      │  │ - Lights     │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Hardware Components

### 1. Control Unit (Microcontroller/Computer)

#### Option A: Raspberry Pi 4 (Recommended)
- **Model**: Raspberry Pi 4 Model B (4GB or 8GB RAM)
- **Price**: ~$55-75
- **Pros**: 
  - Full Linux OS (Raspberry Pi OS)
  - Multiple GPIO pins (40-pin header)
  - Built-in WiFi/Bluetooth
  - USB ports for cameras
  - Can run Python, Node.js, etc.
- **Cons**: Requires external power supply, SD card
- **Use Case**: Full-featured control server

#### Option B: Arduino + ESP32
- **Arduino**: For sensor reading
- **ESP32**: For WiFi connectivity
- **Price**: ~$10-20
- **Pros**: Lower cost, lower power
- **Cons**: More limited, requires programming in C++
- **Use Case**: Minimal setup, basic monitoring

#### Option C: PC/Laptop
- **Requirements**: Linux/Windows/Mac with Python/Node.js
- **Use Case**: Development, testing, or if you already have one

### 2. Environmental Sensors

#### Temperature & Humidity Sensor
**Recommended: DHT22 (AM2302)**
- **Interface**: Digital (single-wire)
- **Range**: 
  - Temperature: -40°C to 80°C (-40°F to 176°F)
  - Humidity: 0-100% RH
- **Accuracy**: 
  - Temperature: ±0.5°C
  - Humidity: ±2% RH
- **Price**: ~$5-10
- **GPIO Pins**: 1 digital pin
- **Python Library**: `Adafruit_DHT` or `dht22-python`

**Alternative: DHT11**
- Cheaper (~$2-5) but less accurate
- Temperature: ±2°C, Humidity: ±5% RH

**Alternative: SHT30/SHT31 (I2C)**
- More accurate, I2C interface
- Price: ~$10-15

#### CO₂ Sensor
**Recommended: SCD30 or SCD40**
- **Interface**: I2C
- **Range**: 400-10,000 ppm
- **Accuracy**: ±(30 ppm + 3% of reading)
- **Price**: ~$30-50
- **Python Library**: `adafruit-circuitpython-scd30`

**Alternative: MH-Z19 (Serial/UART)**
- Lower cost (~$15-25)
- Less accurate but functional
- Serial interface

#### Soil Moisture Sensor
**Recommended: Capacitive Soil Moisture Sensor v1.2**
- **Interface**: Analog (ADC required)
- **Output**: 0-3.3V (dry to wet)
- **Price**: ~$5-10
- **Note**: Requires ADC (MCP3008 or built-in on some boards)

**Alternative: Resistive Sensor**
- Cheaper but corrodes over time
- Not recommended for long-term use

**Advanced: Teros 12 (Professional)**
- Measures moisture, temperature, EC
- Price: ~$100-200
- More accurate, longer lasting

#### Light Sensor (PAR/PPFD)
**Recommended: BH1750 (Lux Meter)**
- **Interface**: I2C
- **Range**: 1-65535 lux
- **Price**: ~$3-5
- **Note**: Converts to PAR/PPFD with calibration

**Professional: Apogee MQ-500 Quantum Sensor**
- Direct PAR measurement
- Price: ~$200-300
- Most accurate for grow lights

**Alternative: TSL2591**
- Higher resolution
- Price: ~$10-15

#### pH Sensor (for Hydroponics)
**Recommended: Atlas Scientific pH Kit**
- **Interface**: I2C/UART
- **Range**: 0-14 pH
- **Accuracy**: ±0.002 pH
- **Price**: ~$50-80
- **Note**: Requires calibration solutions

**Alternative: Gravity Analog pH Sensor**
- Lower cost (~$20-30)
- Less accurate but functional

#### EC (Electrical Conductivity) Sensor
**Recommended: Atlas Scientific EC Kit**
- **Interface**: I2C/UART
- **Range**: 0-5000 µS/cm
- **Price**: ~$50-80
- **For**: Nutrient solution monitoring

### 3. Actuators (Control Devices)

#### Relay Modules
**Recommended: 8-Channel Relay Module**
- **Voltage**: 5V or 12V
- **Switching**: AC/DC up to 10A per channel
- **Interface**: GPIO pins
- **Price**: ~$10-15
- **Use**: Control lights, pumps, fans, heaters

**Alternative: Solid State Relays (SSR)**
- For high-power devices (grow lights)
- Price: ~$15-30 per unit

#### Smart Plugs (WiFi)
**Recommended: TP-Link Kasa HS103/HS105**
- **Interface**: WiFi (cloud API)
- **Control**: On/off, scheduling
- **Price**: ~$15-25 each
- **Python Library**: `python-kasa` or REST API
- **Use**: Control lights, fans, pumps remotely

**Alternative: Sonoff Basic**
- Lower cost (~$8-12)
- Requires flashing with Tasmota/ESPHome

#### Water Pumps
**Recommended: Peristaltic Pump (12V)**
- **Flow Rate**: Adjustable (ml/min)
- **Control**: PWM or relay
- **Price**: ~$20-40
- **Use**: Precise nutrient/water delivery

**Alternative: Submersible Pump**
- Higher flow rate
- Price: ~$10-20
- Less precise

#### Grow Light Control
**Recommended: 0-10V Dimmer Module**
- **Interface**: Analog output or PWM
- **Compatibility**: Most LED drivers support 0-10V
- **Price**: ~$10-20
- **Use**: Dim grow lights based on AI recommendations

**Alternative: Smart Grow Light**
- Built-in WiFi/app control
- Price: Varies ($100-500+)
- Easier integration

#### Fan Control
**Recommended: AC Infinity Controller 67/69**
- **Interface**: Proprietary (may need reverse engineering)
- **Features**: Speed control, scheduling
- **Price**: ~$50-100

**Alternative: Variable Speed Controller + Relay**
- DIY solution
- Price: ~$20-40

#### Humidifier/Dehumidifier
**Recommended: Smart Humidifier (WiFi)**
- **Brands**: Levoit, TaoTronics
- **Interface**: WiFi/app
- **Price**: ~$50-100
- **Control**: On/off via smart plug or API

### 4. Communication Modules

#### WiFi Module (if not built-in)
- **ESP8266**: ~$3-5
- **ESP32**: ~$5-8
- **Use**: Add WiFi to Arduino projects

#### Ethernet (for Raspberry Pi)
- **USB to Ethernet**: Built-in on Pi 4
- **Use**: More reliable than WiFi

#### Bluetooth (optional)
- **HC-05/HC-06**: ~$5-10
- **Use**: Local device communication

### 5. Additional Components

#### Analog-to-Digital Converter (ADC)
**MCP3008** (if using analog sensors with Pi)
- **Interface**: SPI
- **Channels**: 8 channels, 10-bit resolution
- **Price**: ~$5-10

#### Power Supply
- **Raspberry Pi**: 5V 3A USB-C power supply
- **Sensors/Relays**: 5V or 12V depending on components
- **Recommendation**: Use a quality power supply to avoid issues

#### Enclosure
- **Waterproof box**: For outdoor/moisture protection
- **Price**: ~$10-30

#### Camera (for Visual Monitoring)
**Recommended: Raspberry Pi Camera Module v2**
- **Resolution**: 8MP
- **Interface**: CSI (Camera Serial Interface)
- **Price**: ~$25-35
- **Use**: Timelapse, health monitoring, growth tracking

**Alternative: USB Webcam**
- Logitech C920/C930
- Price: ~$50-80
- Easier setup

---

## Integration Technologies

### 1. Claude AI Integration

#### Method A: REST API (Standard)
```python
from anthropic import Anthropic
import json

class ClaudePlantManager:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
    
    def analyze_plant_data(self, sensor_data):
        """Send sensor data to Claude for analysis"""
        prompt = f"""
        You are managing a cannabis plant. Current conditions:
        - Temperature: {sensor_data['temperature']}°F
        - Humidity: {sensor_data['humidity']}%
        - CO₂: {sensor_data['co2']} ppm
        - Soil Moisture: {sensor_data['soil_moisture']}%
        - Light: {sensor_data['light']} lux
        - Growth Stage: {sensor_data['growth_stage']}
        
        Analyze these conditions and provide:
        1. Health assessment
        2. Immediate actions needed (if any)
        3. Recommended adjustments
        4. Reasoning
        
        Respond in JSON format.
        """
        
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return json.loads(message.content[0].text)
```

#### Method B: Model Context Protocol (MCP) - Advanced
MCP allows Claude to directly access hardware through tools/resources.

**MCP Server Setup:**
```python
# mcp_server.py
from mcp.server import Server
from mcp.types import Tool, Resource

class PlantMCPServer:
    def __init__(self):
        self.server = Server("plant-control")
        self.setup_tools()
        self.setup_resources()
    
    def setup_tools(self):
        """Define tools Claude can use"""
        self.server.add_tool(
            Tool(
                name="read_sensors",
                description="Read current sensor values",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            handler=self.read_sensors_handler
        )
        
        self.server.add_tool(
            Tool(
                name="control_light",
                description="Control grow light intensity (0-100%)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "intensity": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["intensity"]
                }
            ),
            handler=self.control_light_handler
        )
    
    def read_sensors_handler(self, args):
        """Handle sensor reading request"""
        # Read actual sensors
        data = {
            "temperature": read_temperature(),
            "humidity": read_humidity(),
            "co2": read_co2(),
            "soil_moisture": read_soil_moisture()
        }
        return data
    
    def control_light_handler(self, args):
        """Handle light control request"""
        intensity = args["intensity"]
        set_light_intensity(intensity)
        return {"status": "success", "intensity": intensity}
```

### 2. Data Collection Service

#### Python Implementation
```python
# sensor_reader.py
import time
import Adafruit_DHT
import board
import adafruit_scd30
from gpiozero import MCP3008

class SensorReader:
    def __init__(self):
        # DHT22 (Temperature/Humidity)
        self.dht_sensor = Adafruit_DHT.DHT22
        self.dht_pin = 4
        
        # SCD30 (CO2)
        self.i2c = board.I2C()
        self.scd30 = adafruit_scd30.SCD30(self.i2c)
        
        # Soil Moisture (Analog via MCP3008)
        self.soil_moisture = MCP3008(channel=0)
        
        # BH1750 (Light)
        # Initialize I2C light sensor
        
    def read_all(self):
        """Read all sensors"""
        # Temperature & Humidity
        humidity, temperature = Adafruit_DHT.read_retry(
            self.dht_sensor, 
            self.dht_pin
        )
        
        # CO2
        co2 = self.scd30.CO2 if self.scd30.data_available else None
        
        # Soil Moisture (0-1.0, where 1.0 is wet)
        soil_raw = self.soil_moisture.value
        soil_percent = int(soil_raw * 100)
        
        # Light (convert to lux, then to PAR)
        light_lux = self.read_light()
        light_par = self.lux_to_par(light_lux)
        
        return {
            "timestamp": time.time(),
            "temperature": round(temperature * 9/5 + 32, 2),  # Celsius to Fahrenheit
            "humidity": round(humidity, 2),
            "co2": int(co2) if co2 else None,
            "soil_moisture": soil_percent,
            "light_lux": light_lux,
            "light_par": light_par
        }
    
    def read_light(self):
        """Read light sensor"""
        # Implementation depends on sensor
        # Example for BH1750:
        # return bh1750.read_lux()
        pass
    
    def lux_to_par(self, lux):
        """Convert lux to PAR (approximate)"""
        # Rough conversion: PAR ≈ lux / 70 (for white LEDs)
        return round(lux / 70, 2)
```

### 3. Actuator Control Service

#### Python Implementation
```python
# actuator_controller.py
from gpiozero import OutputDevice
import RPi.GPIO as GPIO
from kasa import SmartPlug

class ActuatorController:
    def __init__(self, config):
        self.config = config
        self.setup_relays()
        self.setup_smart_plugs()
    
    def setup_relays(self):
        """Initialize relay modules"""
        self.relays = {}
        for name, pin in self.config['relays'].items():
            self.relays[name] = OutputDevice(pin, active_high=False)
    
    def setup_smart_plugs(self):
        """Initialize smart plugs"""
        self.smart_plugs = {}
        for name, ip in self.config['smart_plugs'].items():
            self.smart_plugs[name] = SmartPlug(ip)
            # Async initialization
            # await self.smart_plugs[name].update()
    
    def control_light(self, intensity):
        """Control grow light intensity (0-100%)"""
        if 'light_dimmer' in self.relays:
            # PWM control for dimmer
            pwm = GPIO.PWM(self.config['light_pwm_pin'], 1000)
            pwm.start(intensity)
        elif 'light' in self.smart_plugs:
            # Simple on/off for smart plug
            if intensity > 50:
                self.smart_plugs['light'].turn_on()
            else:
                self.smart_plugs['light'].turn_off()
    
    def control_pump(self, duration_seconds):
        """Run water pump for specified duration"""
        if 'pump' in self.relays:
            self.relays['pump'].on()
            time.sleep(duration_seconds)
            self.relays['pump'].off()
    
    def control_fan(self, speed_percent):
        """Control exhaust fan speed"""
        # Implementation depends on fan controller
        pass
    
    def control_humidifier(self, on):
        """Control humidifier"""
        if 'humidifier' in self.smart_plugs:
            if on:
                self.smart_plugs['humidifier'].turn_on()
            else:
                self.smart_plugs['humidifier'].turn_off()
```

### 4. Data Transmission

#### REST API (Sensor Data → AI)
```python
# api_client.py
import requests
import json

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def send_sensor_data(self, data):
        """Send sensor data to backend"""
        response = requests.post(
            f"{self.base_url}/api/sensors",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    
    def get_ai_instructions(self):
        """Get AI-generated instructions"""
        response = requests.get(f"{self.base_url}/api/instructions")
        return response.json()
```

#### MQTT (Alternative - Real-time)
```python
# mqtt_client.py
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port=1883):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("plant/instructions")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming AI instructions"""
        instructions = json.loads(msg.payload)
        self.execute_instructions(instructions)
    
    def publish_sensor_data(self, data):
        """Publish sensor data"""
        self.client.publish("plant/sensors", json.dumps(data))
```

### 5. Database Storage

#### SQLite (Local)
```python
# database.py
import sqlite3
from datetime import datetime

class PlantDatabase:
    def __init__(self, db_path="plant_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                temperature REAL,
                humidity REAL,
                co2 INTEGER,
                soil_moisture INTEGER,
                light_par REAL
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                decision_type TEXT,
                action_taken TEXT,
                reasoning TEXT
            )
        """)
        self.conn.commit()
    
    def save_sensor_reading(self, data):
        """Save sensor data"""
        self.conn.execute("""
            INSERT INTO sensor_readings 
            (timestamp, temperature, humidity, co2, soil_moisture, light_par)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['timestamp'],
            data['temperature'],
            data['humidity'],
            data['co2'],
            data['soil_moisture'],
            data['light_par']
        ))
        self.conn.commit()
```

### 6. Blockchain Integration (Solana)

#### Store Plant Data on-Chain
```python
# blockchain_integration.py
from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.keypair import Keypair
import json

class SolanaIntegration:
    def __init__(self, rpc_url, keypair_path):
        self.client = Client(rpc_url)
        self.keypair = Keypair.from_base58_string(
            open(keypair_path).read()
        )
    
    def store_plant_data_hash(self, sensor_data, ai_decision):
        """Store hash of plant data on Solana"""
        # Create data object
        data = {
            "timestamp": sensor_data['timestamp'],
            "sensors": sensor_data,
            "ai_decision": ai_decision
        }
        
        # Upload to IPFS (or similar)
        ipfs_hash = self.upload_to_ipfs(data)
        
        # Store hash on Solana (via custom program or account data)
        # This is a simplified example
        transaction = Transaction()
        # Add instruction to store hash
        # ...
        
        return ipfs_hash
```

---

## Complete System Integration Example

```python
# main_controller.py
import time
from sensor_reader import SensorReader
from actuator_controller import ActuatorController
from claude_ai_manager import ClaudePlantManager
from database import PlantDatabase

class PlantController:
    def __init__(self, config):
        self.sensors = SensorReader()
        self.actuators = ActuatorController(config['actuators'])
        self.ai = ClaudePlantManager(config['anthropic_api_key'])
        self.db = PlantDatabase()
        self.running = True
    
    def run(self):
        """Main control loop"""
        while self.running:
            try:
                # 1. Read sensors
                sensor_data = self.sensors.read_all()
                print(f"Sensor Data: {sensor_data}")
                
                # 2. Save to database
                self.db.save_sensor_reading(sensor_data)
                
                # 3. Send to Claude AI
                ai_decision = self.ai.analyze_plant_data(sensor_data)
                print(f"AI Decision: {ai_decision}")
                
                # 4. Execute AI instructions
                self.execute_ai_instructions(ai_decision)
                
                # 5. Log decision
                self.db.save_ai_decision(ai_decision)
                
                # 6. Wait before next cycle
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def execute_ai_instructions(self, decision):
        """Execute actions based on AI decision"""
        if 'actions' in decision:
            for action in decision['actions']:
                action_type = action['type']
                value = action['value']
                
                if action_type == 'water':
                    self.actuators.control_pump(value)
                elif action_type == 'light':
                    self.actuators.control_light(value)
                elif action_type == 'humidifier':
                    self.actuators.control_humidifier(value == 'on')

if __name__ == "__main__":
    config = {
        'anthropic_api_key': 'your-api-key',
        'actuators': {
            'relays': {
                'pump': 18,
                'light': 19
            },
            'smart_plugs': {
                'humidifier': '192.168.1.100',
                'fan': '192.168.1.101'
            }
        }
    }
    
    controller = PlantController(config)
    controller.run()
```

---

## Cost Breakdown

### Minimum Viable Setup
| Component | Item | Cost |
|-----------|------|------|
| Control Unit | Raspberry Pi 4 (4GB) | $55 |
| Sensors | DHT22, Capacitive Soil, BH1750 | $20 |
| Actuators | 8-Channel Relay Module | $12 |
| Power Supply | 5V 3A + 12V 2A | $15 |
| Enclosure | Waterproof box | $15 |
| **Total** | | **~$117** |

### Recommended Setup
| Component | Item | Cost |
|-----------|------|------|
| Control Unit | Raspberry Pi 4 (8GB) | $75 |
| Sensors | DHT22, SCD30, Teros 12, BH1750 | $150 |
| Actuators | Relays + Smart Plugs (4x) | $80 |
| Camera | Raspberry Pi Camera v2 | $30 |
| Power Supply | Quality supplies | $25 |
| Enclosure | Professional box | $30 |
| **Total** | | **~$390** |

### Professional Setup
| Component | Item | Cost |
|-----------|------|------|
| Control Unit | Industrial PC or Pi 4 | $100 |
| Sensors | Professional sensors (Atlas Scientific) | $300 |
| Actuators | Smart devices + professional controllers | $200 |
| Camera | High-res USB camera | $80 |
| Infrastructure | UPS, networking, etc. | $100 |
| **Total** | | **~$800** |

---

## Software Stack Recommendations

### Core Services
- **Python 3.11+**: Main programming language
- **Raspberry Pi OS**: Operating system (if using Pi)
- **SQLite/PostgreSQL**: Database
- **Flask/FastAPI**: Web API (optional)

### Python Libraries
```bash
pip install anthropic          # Claude AI
pip install Adafruit_DHT      # DHT sensors
pip install adafruit-circuitpython-scd30  # CO2 sensor
pip install gpiozero           # GPIO control
pip install RPi.GPIO          # Raspberry Pi GPIO
pip install python-kasa        # Smart plugs
pip install paho-mqtt         # MQTT (optional)
pip install solana            # Solana integration
```

### Development Tools
- **VS Code**: Code editor
- **Git**: Version control
- **Docker**: Containerization (optional)

---

## Security Considerations

1. **API Keys**: Store in environment variables, never commit to git
2. **Network Security**: Use HTTPS, VPN, or local network only
3. **Access Control**: Implement authentication for web interfaces
4. **Data Privacy**: Encrypt sensitive data
5. **Physical Security**: Secure physical access to hardware

---

## Troubleshooting

### Common Issues

**Sensors not reading:**
- Check wiring connections
- Verify GPIO pin numbers
- Check power supply
- Test sensors individually

**AI API errors:**
- Verify API key
- Check rate limits
- Review API response format
- Test with sample data

**Actuators not responding:**
- Check relay connections
- Verify power supply
- Test with manual control
- Check smart plug connectivity

**Data not saving:**
- Check database permissions
- Verify disk space
- Check database connection
- Review error logs

---

This guide provides a comprehensive foundation for implementing the hardware and integration technology needed for your cannabis fork of SOLTOMATO!
