# Ganja Mon ($MON) Implementation Guide

## Technical Architecture Overview

### Core Components

1. **Monad Token (ERC-20)**
   - Standard: ERC-20 (Monad EVM-compatible)
   - Launch Platform: LFJ Token Mill
   - Network: Monad Mainnet

2. **AI Integration**
   - AI System: Grok (xAI)
   - Function: Autonomous plant management
   - Data Processing: Real-time environmental monitoring

3. **Hardware/IoT System**
   - Sensors: Temperature, Humidity, CO₂, Soil Moisture
   - Actuators: Automated environmental controls
   - Data Pipeline: Sensor → AI → Dashboard

4. **Website/Frontend**
   - Site: grokandmon.com
   - Purpose: Display plant status, token info, community engagement

---

## Step-by-Step Implementation Guide

### Phase 1: Token Creation on Monad

#### 1.1 Setup EVM Development Environment

```bash
# Install Node.js and npm if not already installed
# Then install Hardhat
npm install --save-dev hardhat

# Or use Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Create a new Hardhat project
npx hardhat init
```

#### 1.2 Create ERC-20 Token

**Option A: Using LFJ Token Mill (Recommended for Meme Coins)**

1. Visit: https://lfj.gg/monad
2. Connect EVM wallet (MetaMask, Rainbow, etc.)
3. Upload token image/logo (use assets/ganja_mon_token.png)
4. Set token details:
   - Name: Ganja Mon
   - Symbol: MON
   - Description: AI-powered cannabis cultivation on Monad
   - Initial liquidity: Set based on your budget
5. Launch token

**Option B: Programmatic Creation (Hardhat)**

```solidity
// contracts/GanjaMon.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract GanjaMon is ERC20 {
    constructor() ERC20("Ganja Mon", "MON") {
        // Mint 1 billion tokens to deployer
        _mint(msg.sender, 1_000_000_000 * 10 ** decimals());
    }
}
```

**Deploy Script:**

```javascript
// scripts/deploy.js
const hre = require("hardhat");

async function main() {
  const GanjaMon = await hre.ethers.getContractFactory("GanjaMon");
  const token = await GanjaMon.deploy();
  await token.waitForDeployment();
  console.log("Ganja Mon deployed to:", await token.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

**Hardhat Config for Monad:**

```javascript
// hardhat.config.js
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.20",
  networks: {
    monad: {
      url: "https://rpc.monad.xyz", // Replace with actual Monad RPC
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};
```

#### 1.3 Token Metadata

Create metadata JSON for token:

```json
{
  "name": "Ganja Mon",
  "symbol": "MON",
  "description": "Grok AI grows your herb, mon. AI-powered autonomous cannabis cultivation on Monad blockchain.",
  "image": "https://grokandmon.com/assets/token.png",
  "attributes": [
    {
      "trait_type": "Blockchain",
      "value": "Monad"
    },
    {
      "trait_type": "AI System",
      "value": "Grok (xAI)"
    },
    {
      "trait_type": "Location",
      "value": "California, USA"
    }
  ]
}
```

---

### Phase 2: AI Integration Setup

#### 2.1 Grok API Setup

```python
# Install httpx for API calls
pip install httpx

# Example: AI Plant Management System
import httpx
import json
import os
from datetime import datetime

class GrokPlantManager:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("XAI_API_KEY")
        self.api_base = "https://api.x.ai/v1"
        self.client = httpx.Client(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    def analyze_environment(self, sensor_data):
        """Analyze sensor data and provide care instructions"""
        prompt = f"""
        You are managing a cannabis plant named Mon in California. Current conditions:
        - Temperature: {sensor_data['temperature']}°F
        - Humidity: {sensor_data['humidity']}%
        - CO₂: {sensor_data['co2']} ppm
        - Soil Moisture: {sensor_data['soil_moisture']}%
        - Light Intensity: {sensor_data['light']} PPFD
        - Growth Stage: {sensor_data['growth_stage']}
        
        Analyze these conditions and provide:
        1. Health assessment (your vibe check on Mon)
        2. Immediate actions needed (if any)
        3. Recommended adjustments
        4. Your reasoning (keep it casual)
        
        Respond in JSON format with: commentary, analysis, actions, recommendations
        """
        
        response = self.client.post(
            "/chat/completions",
            json={
                "model": "grok-4.1",
                "messages": [
                    {"role": "system", "content": "You are Mon's Grok, a cannabis cultivation AI with attitude. Be helpful but have fun with it."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024
            }
        )
        
        result = response.json()
        return json.loads(result["choices"][0]["message"]["content"])
```

#### 2.2 Sensor Integration

**Hardware Requirements:**
- DHT22 or SHT31 (Temperature & Humidity)
- SCD30/SCD40 (CO₂ sensor)
- Capacitive Soil Moisture Sensor
- BH1750 (Light Sensor)
- Raspberry Pi 4

**Example Sensor Reading Code:**

```python
# sensor_reader.py (Raspberry Pi)
import Adafruit_DHT
import time
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
        
    def read_all(self):
        """Read all sensors"""
        humidity, temperature = Adafruit_DHT.read_retry(
            self.dht_sensor, 
            self.dht_pin
        )
        
        co2 = self.scd30.CO2 if self.scd30.data_available else None
        
        soil_raw = self.soil_moisture.value
        soil_percent = int(soil_raw * 100)
        
        return {
            "timestamp": time.time(),
            "temperature": round(temperature * 9/5 + 32, 2),
            "humidity": round(humidity, 2),
            "co2": int(co2) if co2 else None,
            "soil_moisture": soil_percent,
            "growth_stage": self.determine_growth_stage()
        }
    
    def determine_growth_stage(self):
        # Implement based on days since planting
        return "VEGETATIVE"
```

---

### Phase 3: Web Dashboard

#### 3.1 Tech Stack

- **Framework**: Next.js or React + Vite
- **Blockchain**: ethers.js, wagmi, viem
- **Styling**: Tailwind CSS with dark theme
- **Real-time**: WebSocket for live updates

#### 3.2 Key Features

1. **Live Plant Dashboard**
   - Real-time sensor data display
   - Grok's latest commentary
   - Plant health indicators
   - Growth timeline

2. **Token Information**
   - Price chart
   - Market cap
   - Trading links (DEX)
   - Wallet connection

3. **Grok's Log**
   - AI decision history
   - Commentary archive
   - Action timeline

#### 3.3 Example React Component

```jsx
import { useAccount, useConnect } from 'wagmi';
import { useEffect, useState } from 'react';

export default function PlantDashboard() {
  const { address, isConnected } = useAccount();
  const [plantData, setPlantData] = useState(null);
  const [grokCommentary, setGrokCommentary] = useState("");
  
  useEffect(() => {
    fetchPlantData();
    const interval = setInterval(fetchPlantData, 60000);
    return () => clearInterval(interval);
  }, []);
  
  async function fetchPlantData() {
    const res = await fetch('/api/plant-status');
    const data = await res.json();
    setPlantData(data.sensors);
    setGrokCommentary(data.grok_commentary);
  }
  
  return (
    <div className="min-h-screen bg-gray-950 text-green-400 p-8">
      <header className="flex items-center gap-4 mb-8">
        <span className="text-4xl">🌿</span>
        <div>
          <h1 className="text-3xl font-bold">Ganja Mon</h1>
          <p className="text-green-600">Powered by Grok & Monad</p>
        </div>
      </header>
      
      {grokCommentary && (
        <div className="bg-gray-900 rounded-lg p-4 mb-6 border border-green-800">
          <p className="text-green-300">🤖 Grok says: "{grokCommentary}"</p>
        </div>
      )}
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900 rounded-lg p-4">
          <label className="text-green-600 text-sm">Temperature</label>
          <p className="text-2xl">{plantData?.temperature}°F</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-4">
          <label className="text-green-600 text-sm">Humidity</label>
          <p className="text-2xl">{plantData?.humidity}%</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-4">
          <label className="text-green-600 text-sm">VPD</label>
          <p className="text-2xl">{plantData?.vpd} kPa</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-4">
          <label className="text-green-600 text-sm">Stage</label>
          <p className="text-2xl">{plantData?.growth_stage}</p>
        </div>
      </div>
    </div>
  );
}
```

---

### Phase 4: Legal Compliance (California)

#### 4.1 Cannabis Regulations

**Personal Cultivation (Prop 64):**
- Adults 21+ can grow up to 6 plants per residence
- Must be in a locked space, not visible from public
- For personal use only

**This Project Assumes:**
- You are 21+ years old
- Growing in your private California residence
- 1-6 plants for personal use
- Indoor locked grow space

#### 4.2 Cryptocurrency Considerations

- **Securities Law**: Token structured as meme coin with no utility
- **Disclaimers**: Use everywhere (see TOKEN_STRATEGY.md)
- **Tax Reporting**: Report crypto transactions to IRS

---

### Phase 5: Deployment Checklist

#### 5.1 Pre-Launch

- [ ] Token logo created (assets/ganja_mon_token.png) ✅
- [ ] Token metadata prepared
- [ ] Website developed and tested
- [ ] AI system integrated and tested
- [ ] Sensors calibrated and working
- [ ] Legal disclaimers ready
- [ ] Social media accounts created

#### 5.2 Launch

- [ ] Deploy token to Monad via LFJ Token Mill
- [ ] Launch website at grokandmon.com
- [ ] Start Grok plant monitoring
- [ ] Announce on social media

#### 5.3 Post-Launch

- [ ] Monitor plant health daily
- [ ] Share Grok's commentary
- [ ] Update community regularly
- [ ] Track token metrics

---

## Technical Resources

### Monad Development
- **Documentation**: https://docs.monad.xyz
- **Block Explorer**: Monad Explorer
- **RPC Endpoints**: Check official docs

### Grok/xAI Integration
- **API Docs**: https://docs.x.ai
- **Console**: https://console.x.ai
- **Pricing**: $1.50/M input, $7.50/M output (Grok 4.1)

### Hardware/IoT
- **Raspberry Pi Docs**: https://www.raspberrypi.com/documentation
- **Sensor Libraries**: Adafruit CircuitPython

### EVM Development
- **Hardhat**: https://hardhat.org
- **Foundry**: https://book.getfoundry.sh
- **ethers.js**: https://docs.ethers.org

---

## Cost Estimates

### Initial Setup
- **Token Creation (LFJ Token Mill)**: ~$10-50 (gas fees)
- **Initial Liquidity**: Your choice
- **Hardware Setup**: $400-800
- **Website Hosting**: $0-20/month
- **Domain**: $15/year

### Ongoing Costs
- **Grok API**: ~$0.01-0.10 per decision cycle
- **Hosting**: $0-20/month
- **Monad gas fees**: Very low (high-performance chain)

---

## Next Steps

1. **Order hardware** (see docs/IMPLEMENTATION_PLAN.md)
2. **Set up xAI account** and get API key
3. **Create social media accounts** (@ganjamonai)
4. **Plant the seed** and document Day 1
5. **Build website** with live status
6. **Launch $MON** on LFJ Token Mill after growth is visible

---

*"Grok grows your herb, mon" 🌿*
