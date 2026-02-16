"""
Ecowitt Soil Moisture Sensor Driver

Integrates with Ecowitt GW1100/GW1106 gateway and WH51 soil moisture sensors.
Uses the local API (no cloud dependency) for real-time soil moisture data.

The Ecowitt system uses:
- GW1100 WiFi Gateway: Receives data from sensors and exposes local API
- WH51 Sensors: 915MHz capacitive soil moisture probes (supports up to 8)

Setup:
1. Install the gateway and connect to your WiFi via Ecowitt app
2. Place WH51 sensor(s) in your soil
3. Find gateway IP address (check router or use mDNS)
4. Configure the IP below

API Documentation:
- Ecowitt exposes data at http://<gateway_ip>/get_livedata_info
- Returns JSON with all sensor readings
- Updates every 72 seconds

Usage:
    from src.hardware.ecowitt import EcowittSoilHub
    
    hub = EcowittSoilHub("192.168.125.XXX")
    data = await hub.read()
    print(f"Soil moisture: {data['sensors'][0]['moisture_percent']}%")
"""

import asyncio
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class EcowittSoilReading:
    """Single soil sensor reading from WH51."""
    channel: int  # Sensor channel 1-8
    moisture_percent: float  # 0-100%
    battery_status: str  # "Normal" or "Low"
    signal_strength: int  # 0-4 bars
    timestamp: Optional[str] = None


@dataclass 
class EcowittHubData:
    """Complete data from Ecowitt gateway."""
    sensors: List[EcowittSoilReading] = field(default_factory=list)
    average_moisture: float = 0.0
    needs_water: bool = False
    gateway_model: str = ""
    firmware_version: str = ""
    timestamp: str = ""
    source: str = "ecowitt_gw1100"


class EcowittSoilHub:
    """
    Ecowitt GW1100/GW1106 soil moisture hub driver.
    
    Communicates with the gateway's local API to retrieve soil moisture
    data from connected WH51 sensors without cloud dependency.
    
    Attributes:
        host: IP address of GW1100 gateway
        port: HTTP port (default 80)
        timeout: Request timeout in seconds
        watering_threshold: Percentage below which needs_water is True
    """
    
    DEFAULT_PORT = 80
    DEFAULT_TIMEOUT = 10.0
    DEFAULT_WATERING_THRESHOLD = 30.0
    
    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        watering_threshold: float = DEFAULT_WATERING_THRESHOLD
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.watering_threshold = watering_threshold
        self._base_url = f"http://{host}:{port}" if port != 80 else f"http://{host}"
    
    async def read(self) -> Optional[EcowittHubData]:
        """
        Read all soil moisture sensors from Ecowitt gateway.
        
        Returns:
            EcowittHubData with all sensor readings, or None if failed.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Ecowitt local API endpoint
                response = await client.get(f"{self._base_url}/get_livedata_info")
                response.raise_for_status()
                data = response.json()
                
                return self._parse_response(data)
                
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Ecowitt gateway at {self._base_url}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout reading Ecowitt gateway at {self._base_url}")
            return None
        except Exception as e:
            logger.error(f"Ecowitt error: {e}")
            return None
    
    def _parse_response(self, data: dict) -> EcowittHubData:
        """Parse Ecowitt API response into structured data."""
        sensors = []

        # Format 1: ch_soil array (GW1100 local API)
        # {'ch_soil': [{'channel': '1', 'battery': '5', 'humidity': '31%'}]}
        if 'ch_soil' in data:
            for sensor in data['ch_soil']:
                channel = int(sensor.get('channel', 1))
                moisture_str = sensor.get('humidity', '0%')
                moisture_val = float(moisture_str.replace('%', ''))

                # Battery: 0-5 scale, 5 = full
                battery_level = int(sensor.get('battery', 5))
                battery_status = "Normal" if battery_level >= 2 else "Low"

                sensors.append(EcowittSoilReading(
                    channel=channel,
                    moisture_percent=moisture_val,
                    battery_status=battery_status,
                    signal_strength=battery_level,
                    timestamp=datetime.now().isoformat()
                ))

        # Format 2: soilmoisture1, soilmoisture2, etc. (alternative format)
        if not sensors:
            for i in range(1, 9):  # Up to 8 channels
                moisture_key = f"soilmoisture{i}"
                battery_key = f"soilbatt{i}"

                if moisture_key in data:
                    moisture_val = data[moisture_key]
                    if isinstance(moisture_val, str):
                        moisture_val = float(moisture_val.replace('%', ''))
                    else:
                        moisture_val = float(moisture_val)

                    battery = data.get(battery_key, 1)
                    battery_status = "Normal" if battery == 1 else "Low"

                    sensors.append(EcowittSoilReading(
                        channel=i,
                        moisture_percent=moisture_val,
                        battery_status=battery_status,
                        signal_strength=4,
                        timestamp=datetime.now().isoformat()
                    ))

        # Calculate average across all sensors
        avg_moisture = 0.0
        if sensors:
            avg_moisture = sum(s.moisture_percent for s in sensors) / len(sensors)

        return EcowittHubData(
            sensors=sensors,
            average_moisture=round(avg_moisture, 1),
            needs_water=avg_moisture < self.watering_threshold,
            gateway_model=data.get("model", "GW1100"),
            firmware_version=data.get("version", "unknown"),
            timestamp=datetime.now().isoformat(),
            source="ecowitt_gw1100"
        )
    
    async def read_dict(self) -> Optional[Dict[str, Any]]:
        """
        Read soil moisture and return as dictionary (for JSON serialization).
        """
        hub_data = await self.read()
        if hub_data:
            return {
                "sensors": [
                    {
                        "channel": s.channel,
                        "moisture_percent": s.moisture_percent,
                        "battery": s.battery_status,
                    }
                    for s in hub_data.sensors
                ],
                "average_moisture": hub_data.average_moisture,
                "needs_water": hub_data.needs_water,
                "gateway_model": hub_data.gateway_model,
                "timestamp": hub_data.timestamp,
                "source": hub_data.source
            }
        return None
    
    async def health_check(self) -> bool:
        """Check if Ecowitt gateway is responding."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/get_livedata_info")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_all_data(self) -> Optional[Dict[str, Any]]:
        """
        Get complete raw data from gateway (all sensors, not just soil).
        
        Useful for debugging or accessing additional sensors like
        temperature, humidity, rain gauge, etc.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self._base_url}/get_livedata_info")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get all data: {e}")
            return None
    
    def __repr__(self) -> str:
        return f"EcowittSoilHub(host='{self.host}', port={self.port})"


# Mock implementation for testing
class MockEcowittSoilHub(EcowittSoilHub):
    """Mock Ecowitt hub for testing without hardware."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_moisture = [45.0]  # Start with one sensor
        self._depletion_rate = 0.5
    
    async def read(self) -> EcowittHubData:
        """Return simulated soil moisture reading."""
        import random
        
        sensors = []
        for i, base_moisture in enumerate(self._mock_moisture, 1):
            noise = random.uniform(-2, 2)
            moisture = max(0, min(100, base_moisture + noise))
            sensors.append(EcowittSoilReading(
                channel=i,
                moisture_percent=round(moisture, 1),
                battery_status="Normal",
                signal_strength=4,
                timestamp=datetime.now().isoformat()
            ))
        
        avg = sum(s.moisture_percent for s in sensors) / len(sensors) if sensors else 0
        
        return EcowittHubData(
            sensors=sensors,
            average_moisture=round(avg, 1),
            needs_water=avg < self.watering_threshold,
            gateway_model="GW1100 (Mock)",
            firmware_version="1.0.0",
            timestamp=datetime.now().isoformat(),
            source="mock_ecowitt"
        )
    
    def add_sensor(self, initial_moisture: float = 50.0):
        """Add another mock sensor."""
        self._mock_moisture.append(initial_moisture)
    
    def simulate_watering(self, ml_added: int = 200):
        """Simulate watering - increases all sensor moisture."""
        increase = ml_added / 20.0
        self._mock_moisture = [min(100, m + increase) for m in self._mock_moisture]


# Factory function for unified interface
def get_soil_sensor(
    sensor_type: str = "ecowitt",
    host: str = "192.168.125.100",
    use_mock: bool = False,
    **kwargs
) -> EcowittSoilHub:
    """
    Factory function to get appropriate soil sensor.
    
    Args:
        sensor_type: "ecowitt" or "esp32"
        host: Gateway/sensor IP address
        use_mock: Return mock for testing
        **kwargs: Additional arguments for sensor
        
    Returns:
        Soil sensor hub instance
    """
    if use_mock:
        return MockEcowittSoilHub(host, **kwargs)
    return EcowittSoilHub(host, **kwargs)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    async def main():
        host = sys.argv[1] if len(sys.argv) > 1 else "192.168.125.100"
        use_mock = "--mock" in sys.argv
        
        print(f"Testing Ecowitt gateway at {host} (mock={use_mock})")
        
        hub = get_soil_sensor("ecowitt", host, use_mock=use_mock)
        
        # Health check
        if not use_mock:
            healthy = await hub.health_check()
            print(f"Health check: {'✓' if healthy else '✗'}")
            if not healthy:
                print("Gateway not responding. Check:")
                print("  1. Gateway is powered on and connected to WiFi")
                print("  2. IP address is correct (check router)")
                print("  3. You're on the same network")
                return
        
        # Read soil data
        data = await hub.read()
        if data:
            print(f"\n📊 Ecowitt Soil Moisture Readings:")
            print(f"   Gateway: {data.gateway_model}")
            for sensor in data.sensors:
                status = "🔋" if sensor.battery_status == "Normal" else "⚠️ LOW"
                print(f"   Channel {sensor.channel}: {sensor.moisture_percent}% {status}")
            print(f"   Average: {data.average_moisture}%")
            print(f"   Needs water: {'Yes 💧' if data.needs_water else 'No ✓'}")
        else:
            print("Failed to read sensors")
    
    asyncio.run(main())
