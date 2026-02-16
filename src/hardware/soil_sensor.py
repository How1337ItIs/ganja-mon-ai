"""
Soil Moisture Sensor Hub Driver

Communicates with an ESP32-based soil moisture sensor over WiFi.
The ESP32 runs a simple HTTP server that returns JSON with moisture readings.

Setup:
1. Flash the ESP32 with the firmware in esp32_firmware/soil_sensor_server/
2. Configure the ESP32's IP address below or use mDNS (soil.local)
3. Mount the capacitive soil sensors in your grow medium

Usage:
    from src.hardware.soil_sensor import SoilSensorHub
    
    hub = SoilSensorHub("192.168.125.200")  # or "soil.local"
    data = await hub.read()
    print(f"Soil moisture: {data['average']}%")
"""

import asyncio
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SoilReading:
    """Soil moisture reading from sensor hub."""
    probe1: float  # Percentage 0-100
    probe2: float  # Percentage 0-100
    average: float  # Average of both probes
    needs_water: bool  # True if below threshold
    raw_probe1: Optional[int] = None  # Raw ADC value
    raw_probe2: Optional[int] = None  # Raw ADC value
    timestamp: Optional[str] = None


class SoilSensorHub:
    """
    ESP32-based soil moisture sensor hub.
    
    The ESP32 exposes a simple HTTP API:
    - GET /soil - Returns JSON with moisture readings
    - GET /health - Returns sensor health status
    - POST /calibrate - Trigger calibration routine
    
    Attributes:
        host: IP address or hostname of ESP32 (e.g., "192.168.125.200" or "soil.local")
        port: HTTP port (default 80)
        timeout: Request timeout in seconds
        watering_threshold: Percentage below which needs_water is True
    """
    
    DEFAULT_HOST = "soil.local"
    DEFAULT_PORT = 80
    DEFAULT_TIMEOUT = 5.0
    DEFAULT_WATERING_THRESHOLD = 30.0  # Flowering stage threshold
    
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        watering_threshold: float = DEFAULT_WATERING_THRESHOLD
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.watering_threshold = watering_threshold
        self._base_url = f"http://{host}:{port}" if port != 80 else f"http://{host}"
    
    async def read(self) -> Optional[SoilReading]:
        """
        Read soil moisture from ESP32 sensor hub.
        
        Returns:
            SoilReading object with moisture data, or None if read failed.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self._base_url}/soil")
                response.raise_for_status()
                data = response.json()
                
                return SoilReading(
                    probe1=data.get("probe1", 0),
                    probe2=data.get("probe2", 0),
                    average=data.get("average", 0),
                    needs_water=data.get("needs_water", False),
                    raw_probe1=data.get("raw1"),
                    raw_probe2=data.get("raw2"),
                    timestamp=data.get("timestamp")
                )
        except httpx.ConnectError:
            logger.error(f"Cannot connect to soil sensor at {self._base_url}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout reading soil sensor at {self._base_url}")
            return None
        except Exception as e:
            logger.error(f"Soil sensor error: {e}")
            return None
    
    async def read_dict(self) -> Optional[Dict[str, Any]]:
        """
        Read soil moisture and return as dictionary (for JSON serialization).
        
        Returns:
            Dict with moisture data, or None if read failed.
        """
        reading = await self.read()
        if reading:
            return {
                "probe1_percent": reading.probe1,
                "probe2_percent": reading.probe2,
                "average_percent": reading.average,
                "needs_water": reading.needs_water,
                "raw_probe1": reading.raw_probe1,
                "raw_probe2": reading.raw_probe2,
                "timestamp": reading.timestamp
            }
        return None
    
    async def health_check(self) -> bool:
        """
        Check if sensor hub is responding.
        
        Returns:
            True if sensor is healthy, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self._base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def calibrate(self, dry_value: int, wet_value: int) -> bool:
        """
        Send calibration values to ESP32.
        
        Args:
            dry_value: ADC reading when sensor is in dry air
            wet_value: ADC reading when sensor is submerged in water
            
        Returns:
            True if calibration was accepted, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/calibrate",
                    json={"dry": dry_value, "wet": wet_value}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return False
    
    def __repr__(self) -> str:
        return f"SoilSensorHub(host='{self.host}', port={self.port})"


# Synchronous wrapper for non-async code
class SoilSensorHubSync:
    """Synchronous wrapper for SoilSensorHub."""
    
    def __init__(self, *args, **kwargs):
        self._async_hub = SoilSensorHub(*args, **kwargs)
    
    def read(self) -> Optional[SoilReading]:
        """Read soil moisture synchronously."""
        return asyncio.run(self._async_hub.read())
    
    def read_dict(self) -> Optional[Dict[str, Any]]:
        """Read soil moisture as dict synchronously."""
        return asyncio.run(self._async_hub.read_dict())
    
    def health_check(self) -> bool:
        """Check sensor health synchronously."""
        return asyncio.run(self._async_hub.health_check())


# Mock implementation for testing without hardware
class MockSoilSensorHub(SoilSensorHub):
    """Mock sensor for testing without ESP32 hardware."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_moisture = 45.0
        self._depletion_rate = 0.5  # % per hour
    
    async def read(self) -> SoilReading:
        """Return simulated soil moisture reading."""
        import random
        
        # Simulate gradual moisture depletion with some noise
        noise1 = random.uniform(-2, 2)
        noise2 = random.uniform(-2, 2)
        
        probe1 = max(0, min(100, self._mock_moisture + noise1))
        probe2 = max(0, min(100, self._mock_moisture + noise2))
        average = (probe1 + probe2) / 2
        
        return SoilReading(
            probe1=round(probe1, 1),
            probe2=round(probe2, 1),
            average=round(average, 1),
            needs_water=average < self.watering_threshold,
            raw_probe1=int(3200 - (probe1 * 18)),  # Simulated raw
            raw_probe2=int(3200 - (probe2 * 18)),
        )
    
    def simulate_watering(self, ml_added: int = 200):
        """Simulate adding water - increases moisture level."""
        # Roughly 20ml = 1% moisture for a 3-gallon pot
        increase = ml_added / 20.0
        self._mock_moisture = min(100, self._mock_moisture + increase)
    
    def simulate_time_passing(self, hours: float = 1.0):
        """Simulate moisture depletion over time."""
        self._mock_moisture = max(0, self._mock_moisture - (self._depletion_rate * hours))


# Factory function
def get_soil_sensor(
    host: str = "soil.local",
    use_mock: bool = False
) -> SoilSensorHub:
    """
    Get appropriate soil sensor implementation.
    
    Args:
        host: ESP32 hostname or IP
        use_mock: If True, return mock implementation for testing
        
    Returns:
        SoilSensorHub instance (real or mock)
    """
    if use_mock:
        return MockSoilSensorHub(host)
    return SoilSensorHub(host)


# CLI for testing
if __name__ == "__main__":
    import sys
    
    async def main():
        host = sys.argv[1] if len(sys.argv) > 1 else "soil.local"
        use_mock = "--mock" in sys.argv
        
        print(f"Testing soil sensor at {host} (mock={use_mock})")
        
        hub = get_soil_sensor(host, use_mock=use_mock)
        
        # Health check
        if not use_mock:
            healthy = await hub.health_check()
            print(f"Health check: {'✓' if healthy else '✗'}")
            if not healthy:
                print("Sensor not responding. Is the ESP32 powered on and connected to WiFi?")
                return
        
        # Read moisture
        reading = await hub.read()
        if reading:
            print(f"\n📊 Soil Moisture Readings:")
            print(f"   Probe 1: {reading.probe1}%")
            print(f"   Probe 2: {reading.probe2}%")
            print(f"   Average: {reading.average}%")
            print(f"   Needs water: {'Yes 💧' if reading.needs_water else 'No ✓'}")
        else:
            print("Failed to read sensor")
    
    asyncio.run(main())
