# Technical Summary - Sol Cannabis Fork

## Overview

This document summarizes all technical findings and implementation details for forking the SOLTOMATO project into a cannabis-themed version.

---

## SOLTOMATO Technical Details

### Token Information
- **Contract Address**: `jk1T35eWK41MBMM8AWoYVaNbjHEEQzMDetTsfnqpump`
- **Network**: Solana Mainnet
- **Token Standard**: SPL Token
- **Launch Platform**: pump.fun
- **Website**: https://soltomato.fun / https://claudeandsol.com

### Core Architecture
1. **Solana Token**: Meme coin on Solana blockchain
2. **Claude AI**: Autonomous plant management via Anthropic API
3. **IoT Hardware**: Sensors monitoring environmental conditions
4. **Website/Dashboard**: Live plant status and token information

---

## Hardware Components

### Control Unit
- **Recommended**: Raspberry Pi 4 (4GB+)
- **Alternatives**: Arduino + ESP32, PC/Laptop
- **Purpose**: Central control server for sensors and actuators

### Sensors
1. **Temperature & Humidity**: DHT22 (AM2302) - $5-10
2. **CO₂**: SCD30 or SCD40 - $30-50
3. **Soil Moisture**: Capacitive sensor v1.2 - $5-10
4. **Light (PAR/PPFD)**: BH1750 or Apogee MQ-500 - $3-300
5. **pH** (optional): Atlas Scientific pH Kit - $50-80
6. **EC** (optional): Atlas Scientific EC Kit - $50-80

### Actuators
1. **Relay Modules**: 8-channel relay - $10-15
2. **Smart Plugs**: TP-Link Kasa HS103 - $15-25 each
3. **Water Pumps**: Peristaltic pump (12V) - $20-40
4. **Grow Light Control**: 0-10V dimmer module - $10-20
5. **Fan Control**: Variable speed controller - $20-40
6. **Humidifier**: Smart WiFi humidifier - $50-100

### Communication
- **WiFi**: Built-in (Raspberry Pi) or ESP8266/ESP32 module
- **GPIO**: 40-pin header on Raspberry Pi
- **I2C/SPI**: For sensor communication
- **USB**: For cameras and peripherals

**Total Cost Estimate**: 
- Minimum: ~$117
- Recommended: ~$390
- Professional: ~$800

---

## Integration Technologies

### 1. Claude AI Integration

#### Method A: REST API (Standard)
```python
from anthropic import Anthropic

client = Anthropic(api_key="your-key")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}]
)
```

#### Method B: Model Context Protocol (MCP)
- Allows Claude to directly access hardware
- Tools and resources for sensor reading/actuator control
- More advanced, enables true autonomous control

### 2. Data Flow

```
Sensors → Control Server → Claude AI API
                ↓
         AI Instructions
                ↓
         Actuator Control
                ↓
         Database Storage
                ↓
         Blockchain (Solana)
```

### 3. Communication Protocols

- **REST API**: HTTP/HTTPS for AI communication
- **MQTT**: Real-time pub/sub (optional)
- **WebSocket**: Real-time updates to frontend
- **GPIO**: Direct hardware control
- **I2C/SPI**: Sensor communication

### 4. Data Storage

- **Local Database**: SQLite or PostgreSQL
- **Blockchain**: Solana (store hashes/IPFS links)
- **IPFS**: Decentralized storage for full data
- **Cloud**: Optional backup/storage

---

## Software Stack

### Core
- **Python 3.11+**: Main language
- **Raspberry Pi OS**: Operating system
- **SQLite/PostgreSQL**: Database

### Key Libraries
```python
anthropic              # Claude AI
Adafruit_DHT          # DHT sensors
adafruit-circuitpython-scd30  # CO2 sensor
gpiozero              # GPIO control
RPi.GPIO             # Raspberry Pi GPIO
python-kasa          # Smart plugs
solana               # Solana integration
```

### Frontend (Optional)
- **Next.js/React**: Website framework
- **@solana/web3.js**: Blockchain integration
- **Chart.js**: Data visualization

---

## Implementation Steps

### Phase 1: Token Creation
1. Install Solana CLI
2. Create wallet
3. Create SPL token (via pump.fun or CLI)
4. Set up metadata
5. Deploy to devnet (test) → mainnet

### Phase 2: Hardware Setup
1. Assemble Raspberry Pi
2. Install sensors
3. Connect actuators
4. Test individual components
5. Calibrate sensors

### Phase 3: Software Development
1. Set up Python environment
2. Implement sensor reading
3. Integrate Claude AI
4. Build actuator control
5. Create database schema
6. Develop API (optional)

### Phase 4: AI Integration
1. Get Anthropic API key
2. Implement data collection
3. Create AI prompts
4. Test decision-making
5. Implement action execution

### Phase 5: Blockchain Integration
1. Set up Solana connection
2. Store sensor data (IPFS + on-chain hash)
3. Create smart contracts (optional)
4. Link token to plant data

### Phase 6: Website/Dashboard
1. Set up Next.js project
2. Integrate Solana wallet
3. Display plant status
4. Show token information
5. Real-time updates

### Phase 7: Deployment
1. Test on devnet
2. Legal compliance check
3. Deploy to mainnet
4. Launch website
5. Community engagement

---

## Cannabis-Specific Considerations

### Environmental Parameters
- **Temperature**: 70-85°F (varies by stage)
- **Humidity**: 40-60% (vegetative), 40-50% (flowering)
- **CO₂**: 1000-1500 ppm (optimal)
- **Light Cycles**: 18/6 (veg), 12/12 (flower)
- **VPD**: Stage-specific optimization

### Additional Sensors Needed
- **PAR/PPFD Meter**: Critical for cannabis
- **pH Meter**: For hydroponic systems
- **EC Meter**: Nutrient monitoring
- **Camera**: Visual health monitoring

### Legal Compliance (California)
- **Age**: 21+ only
- **Max Plants**: 6 per residence
- **Licensing**: Required for commercial
- **METRC**: Track and trace (commercial)
- **Privacy**: Secure data handling

---

## Key Differences from SOLTOMATO

| Aspect | SOLTOMATO | Sol Cannabis |
|--------|-----------|--------------|
| **Plant** | Tomato | Cannabis |
| **Light Control** | Simple on/off | Photoperiod critical |
| **VPD** | Basic | Stage-specific |
| **Growth Stages** | Continuous | Distinct phases |
| **Nutrients** | Simple | Complex NPK ratios |
| **Legal** | N/A | State regulations |
| **Sensors** | Basic | More comprehensive |

---

## Cost Breakdown

### Development Costs
- **Token Creation**: $50-200
- **Initial Liquidity**: $1,000-10,000+
- **Hardware**: $117-800
- **Website Hosting**: $10-50/month
- **Legal Consultation**: $500-2,000+
- **Claude API**: ~$0.01-0.10 per call

### Ongoing Costs
- **Hosting**: $10-50/month
- **API Calls**: Variable
- **Maintenance**: Variable
- **Electricity**: ~$20-50/month (grow setup)

---

## Security Considerations

1. **API Keys**: Environment variables only
2. **Network**: HTTPS, VPN, or local network
3. **Access Control**: Authentication for web
4. **Data Privacy**: Encryption
5. **Physical Security**: Secure hardware access
6. **Smart Contracts**: Audit before mainnet

---

## Resources & Links

### Solana
- Docs: https://docs.solana.com
- SPL Token: https://spl.solana.com/token
- Explorer: https://explorer.solana.com
- pump.fun: https://pump.fun

### AI
- Claude API: https://docs.anthropic.com
- Anthropic Console: https://console.anthropic.com

### Hardware
- Raspberry Pi: https://www.raspberrypi.com
- Adafruit: https://www.adafruit.com
- SparkFun: https://www.sparkfun.com

### Development
- Solana Cookbook: https://solanacookbook.com
- Anchor Docs: https://www.anchor-lang.com

---

## Next Steps

1. **Review Documentation**: Read all guides thoroughly
2. **Choose Setup Level**: Minimum, Recommended, or Professional
3. **Order Hardware**: Based on chosen setup
4. **Set Up Dev Environment**: Solana CLI, Python, etc.
5. **Create Test Token**: On devnet first
6. **Build MVP**: Basic sensor reading + AI
7. **Iterate**: Add features incrementally
8. **Legal Review**: Before mainnet launch
9. **Deploy**: Mainnet launch
10. **Community**: Build and engage

---

## Documentation Files

- **IMPLEMENTATION_GUIDE.md**: Complete technical implementation
- **HARDWARE_INTEGRATION_GUIDE.md**: Hardware specs and integration
- **QUICK_REFERENCE.md**: Quick commands and links
- **PROJECT_STRUCTURE.md**: Project organization
- **SOLTOMATO_Research.md**: Original research

---

**Last Updated**: January 2026
