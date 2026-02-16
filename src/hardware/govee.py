"""
Govee WiFi Sensor Integration
=============================

Reads temperature and humidity from GoveeLife H5179 WiFi sensor.
Uses Govee's undocumented BLE API and/or local polling.

The H5179 sensor:
- Broadcasts via BLE (Bluetooth Low Energy)
- Syncs to cloud via WiFi for app/export
- Has local API access via Govee Home app integration

Methods supported:
1. BLE scanning (requires bluetooth adapter)
2. Cloud API polling (requires Govee API key)
3. Local network discovery (experimental)

For Chromebook without BLE, we use the Cloud API method.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .base import SensorHub, SensorReading

logger = logging.getLogger(__name__)


def safe_print(msg: str):
    """Print with Windows-safe encoding"""
    try:
        print(msg)
    except UnicodeEncodeError:
        ascii_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(ascii_msg)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GoveeReading:
    """Single reading from Govee sensor"""
    timestamp: datetime
    temperature_c: float
    temperature_f: float
    humidity: float
    battery_percent: Optional[int] = None
    device_name: Optional[str] = None
    device_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "temperature_c": self.temperature_c,
            "temperature_f": self.temperature_f,
            "humidity": self.humidity,
            "battery_percent": self.battery_percent,
            "device_name": self.device_name,
            "device_id": self.device_id,
        }


# =============================================================================
# Govee Cloud API Client
# =============================================================================

class GoveeCloudAPI:
    """
    Client for Govee Cloud API.

    Get your API key from: https://developer.govee.com/
    Or via Govee Home app → Settings → About Us → Apply for API Key

    Uses the newer OpenAPI endpoint which supports more devices.
    """

    # Use newer OpenAPI endpoint (supports more devices than v1)
    BASE_URL = "https://openapi.api.govee.com/router/api/v1"

    def __init__(self, api_key: str):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx required: pip install httpx")

        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={"Govee-API-Key": api_key},
            timeout=30.0,
        )
        self._devices_cache: List[Dict] = []
        self._last_cache_update: Optional[datetime] = None

    async def get_devices(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get list of Govee devices on account.

        Returns devices in OpenAPI format:
        {
            "sku": "H5179",
            "device": "XX:XX:XX:XX:XX:XX:XX:XX",
            "deviceName": "Wifi Thermometer",
            "type": "devices.types.thermometer",
            "capabilities": [...]
        }
        """
        # Use cache if available and fresh (< 5 minutes)
        if not force_refresh and self._devices_cache and self._last_cache_update:
            age = (datetime.now() - self._last_cache_update).total_seconds()
            if age < 300:
                return self._devices_cache

        try:
            response = await self.client.get(f"{self.BASE_URL}/user/devices")
            response.raise_for_status()
            data = response.json()

            # OpenAPI returns devices directly in data array
            self._devices_cache = data.get("data", [])
            self._last_cache_update = datetime.now()

            logger.info(f"Found {len(self._devices_cache)} Govee devices")
            return self._devices_cache

        except Exception as e:
            logger.error(f"Failed to get Govee devices: {e}")
            return self._devices_cache  # Return stale cache on error

    async def get_device_state(self, device_id: str, model: str) -> Optional[Dict]:
        """
        Get current state of a device using OpenAPI.

        For H5179 temperature sensor, requests state and returns parsed properties.
        """
        try:
            # OpenAPI uses POST with JSON body for device state
            payload = {
                "requestId": "grokmon-" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "payload": {
                    "sku": model,
                    "device": device_id
                }
            }
            response = await self.client.post(
                f"{self.BASE_URL}/device/state",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Parse capabilities from response
            result = {
                "device": device_id,
                "model": model,
                "properties": []
            }

            capabilities = data.get("payload", {}).get("capabilities", [])
            for cap in capabilities:
                instance = cap.get("instance", "")
                state = cap.get("state", {})
                value = state.get("value")

                if instance == "sensorTemperature" and value not in (None, ""):
                    try:
                        temp_f = float(value)
                        temp_c = (temp_f - 32) * 5 / 9
                        result["properties"].append({"temperatureC": temp_c})
                        result["properties"].append({"temperatureF": temp_f})
                    except (ValueError, TypeError):
                        logger.debug(f"Invalid temperature value: {value!r}")
                elif instance == "sensorHumidity" and value not in (None, ""):
                    try:
                        humidity = float(value)
                        result["properties"].append({"humidity": humidity})
                    except (ValueError, TypeError):
                        logger.debug(f"Invalid humidity value: {value!r}")
                elif instance == "carbonDioxideConcentration" and value not in (None, ""):
                    try:
                        co2_ppm = int(float(value))
                        result["properties"].append({"co2_ppm": co2_ppm})
                    except (ValueError, TypeError):
                        logger.debug(f"Invalid CO2 value: {value!r}")
                elif instance == "online":
                    result["properties"].append({"online": value})

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Govee API rate limited - waiting...")
                await asyncio.sleep(60)
            logger.error(f"Failed to get device state: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get device state: {e}")
            return None

    async def find_temperature_sensor(self) -> Optional[Dict]:
        """Find first temperature sensor on account"""
        devices = await self.get_devices()

        for device in devices:
            # OpenAPI uses "sku" instead of "model"
            sku = device.get("sku", "")
            device_type = device.get("type", "")

            # Check for thermometer type or known SKUs
            if "thermometer" in device_type.lower() or sku in ["H5179", "H5075", "H5074", "H5072", "H5101", "H5102", "H5100"]:
                logger.info(f"Found temperature sensor: {device.get('deviceName')} ({sku})")
                return device

        logger.warning("No Govee temperature sensor found on account")
        return None

    async def find_co2_sensor(self) -> Optional[Dict]:
        """Find CO2/air quality monitor on account"""
        devices = await self.get_devices()

        for device in devices:
            sku = device.get("sku", "")
            device_type = device.get("type", "")

            # Check for air quality monitor type or known CO2 SKUs
            if "air_quality" in device_type.lower() or sku in ["H5140", "H5141", "H5142"]:
                logger.info(f"Found CO2 sensor: {device.get('deviceName')} ({sku})")
                return device

        logger.warning("No Govee CO2 sensor found on account")
        return None

    async def find_humidifier(self) -> Optional[Dict]:
        """Find humidifier on account"""
        devices = await self.get_devices()

        for device in devices:
            sku = device.get("sku", "")
            device_type = device.get("type", "")

            # Check for humidifier type or known SKUs
            if "humidifier" in device_type.lower() or sku in ["H7141", "H7142", "H7143", "H7145", "H7160"]:
                logger.info(f"Found humidifier: {device.get('deviceName')} ({sku})")
                return device

        logger.warning("No Govee humidifier found on account")
        return None

    async def send_command(self, device_id: str, model: str, capability: str, instance: str, value: Any) -> bool:
        """
        Send a control command to a Govee device.

        Args:
            device_id: Device ID
            model: Device SKU/model
            capability: Capability type (e.g., 'devices.capabilities.on_off')
            instance: Instance name (e.g., 'powerSwitch')
            value: Value to set

        Returns:
            True if successful
        """
        try:
            payload = {
                "requestId": "grokmon-cmd-" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "payload": {
                    "sku": model,
                    "device": device_id,
                    "capability": {
                        "type": capability,
                        "instance": instance,
                        "value": value
                    }
                }
            }

            response = await self.client.post(
                f"{self.BASE_URL}/device/control",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 200:
                logger.info(f"Command sent successfully: {instance}={value}")
                return True
            else:
                logger.error(f"Command failed: {data}")
                return False

        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# =============================================================================
# Govee Sensor Hub (implements SensorHub interface)
# =============================================================================

class GoveeSensorHub(SensorHub):
    """
    SensorHub implementation for Govee WiFi sensors.

    Primary sensor: GoveeLife H5179 for temp/humidity

    Usage:
        hub = GoveeSensorHub(api_key="your-govee-api-key")
        await hub.connect()
        reading = await hub.read_all()
        print(f"Temp: {reading.air_temp}C, Humidity: {reading.humidity}%")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        device_id: Optional[str] = None,
        model: Optional[str] = None,
        poll_interval: int = 60,  # Govee API has rate limits
    ):
        """
        Initialize Govee sensor hub.

        Args:
            api_key: Govee API key (or set GOVEE_API_KEY env var)
            device_id: Specific device ID (auto-detects if not set)
            model: Device model (auto-detects if not set)
            poll_interval: Minimum seconds between API calls
        """
        import os
        self.api_key = api_key or os.environ.get("GOVEE_API_KEY")
        if not self.api_key:
            raise ValueError("Govee API key required. Set GOVEE_API_KEY env var or pass api_key")

        self.device_id = device_id
        self.model = model
        self.poll_interval = poll_interval

        # CO2 sensor (separate device)
        self.co2_device_id: Optional[str] = None
        self.co2_model: Optional[str] = None

        # Humidifier (controllable device)
        self.humidifier_device_id: Optional[str] = None
        self.humidifier_model: Optional[str] = None
        self._humidifier_on: bool = False

        self._client: Optional[GoveeCloudAPI] = None
        self._connected = False
        self._last_reading: Optional[GoveeReading] = None
        self._last_poll_time: Optional[datetime] = None
        self._last_co2_ppm: Optional[int] = None

    async def connect(self) -> bool:
        """Connect to Govee API and find sensors"""
        try:
            self._client = GoveeCloudAPI(self.api_key)

            # Auto-detect temperature sensor if not specified
            if not self.device_id:
                sensor = await self._client.find_temperature_sensor()
                if sensor:
                    self.device_id = sensor.get("device")
                    # OpenAPI uses "sku" instead of "model"
                    self.model = sensor.get("sku") or sensor.get("model")
                    logger.info(f"Auto-detected sensor: {self.device_id} ({self.model})")
                    safe_print(f"Govee sensor connected: {sensor.get('deviceName')} ({self.model})")
                else:
                    logger.error("No temperature sensor found on Govee account")
                    safe_print("No Govee temperature sensor found on account")
                    return False

            # Also look for CO2 sensor
            co2_sensor = await self._client.find_co2_sensor()
            if co2_sensor:
                self.co2_device_id = co2_sensor.get("device")
                self.co2_model = co2_sensor.get("sku") or co2_sensor.get("model")
                logger.info(f"Auto-detected CO2 sensor: {self.co2_device_id} ({self.co2_model})")
                safe_print(f"Govee CO2 monitor connected: {co2_sensor.get('deviceName')} ({self.co2_model})")

            # Also look for humidifier
            humidifier = await self._client.find_humidifier()
            if humidifier:
                self.humidifier_device_id = humidifier.get("device")
                self.humidifier_model = humidifier.get("sku") or humidifier.get("model")
                logger.info(f"Auto-detected humidifier: {self.humidifier_device_id} ({self.humidifier_model})")
                safe_print(f"Govee humidifier connected: {humidifier.get('deviceName')} ({self.humidifier_model})")

            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Govee: {e}")
            return False

    async def read_all(self) -> SensorReading:
        """Read all sensors (temp, humidity, CO2, calculate VPD)"""
        if not self._connected or not self._client:
            raise ConnectionError("Not connected to Govee API")

        # Rate limiting - don't poll too frequently
        if self._last_poll_time:
            elapsed = (datetime.now() - self._last_poll_time).total_seconds()
            if elapsed < self.poll_interval and self._last_reading:
                logger.debug(f"Using cached reading ({elapsed:.0f}s old)")
                return self._reading_to_sensor_reading(self._last_reading)

        # Fetch from temp/humidity sensor
        state = await self._client.get_device_state(self.device_id, self.model)

        if not state:
            if self._last_reading:
                logger.warning("API call failed, using last reading")
                return self._reading_to_sensor_reading(self._last_reading)
            raise ConnectionError("Failed to get sensor state from Govee")

        # Parse properties - each item is like {"temperatureC": 25.5}
        props = {}
        for p in state.get("properties", []):
            if p and isinstance(p, dict):
                props.update(p)

        # Handle different property name formats
        temp_c = props.get("temperatureC") or props.get("tem") or props.get("temperature")
        temp_f = props.get("temperatureF")
        humidity = props.get("humidity") or props.get("hum")

        if temp_c is None and temp_f:
            temp_c = (temp_f - 32) * 5 / 9
        elif temp_c and temp_f is None:
            temp_f = temp_c * 9 / 5 + 32

        if temp_c is None or humidity is None:
            logger.error(f"Invalid sensor data: {props}")
            if self._last_reading:
                return self._reading_to_sensor_reading(self._last_reading)
            raise ValueError("Could not parse sensor data from Govee")

        # Also fetch CO2 if we have a CO2 sensor
        if self.co2_device_id and self.co2_model:
            try:
                co2_state = await self._client.get_device_state(self.co2_device_id, self.co2_model)
                if co2_state:
                    for p in co2_state.get("properties", []):
                        if p and isinstance(p, dict) and "co2_ppm" in p:
                            self._last_co2_ppm = p["co2_ppm"]
                            logger.debug(f"CO2: {self._last_co2_ppm} ppm")
                            break
            except Exception as e:
                logger.warning(f"Failed to read CO2 sensor: {e}")

        self._last_reading = GoveeReading(
            timestamp=datetime.now(),
            temperature_c=float(temp_c),
            temperature_f=float(temp_f) if temp_f else float(temp_c) * 9/5 + 32,
            humidity=float(humidity),
            device_id=self.device_id,
            device_name=state.get("deviceName"),
        )
        self._last_poll_time = datetime.now()

        return self._reading_to_sensor_reading(self._last_reading)

    def _reading_to_sensor_reading(self, reading: GoveeReading) -> SensorReading:
        """Convert GoveeReading to base SensorReading"""
        vpd = SensorReading.calculate_vpd(reading.temperature_c, reading.humidity)
        dew_point = SensorReading.calculate_dew_point(reading.temperature_c, reading.humidity)

        return SensorReading(
            timestamp=reading.timestamp,
            air_temp=reading.temperature_c,
            humidity=reading.humidity,
            vpd=vpd,
            soil_moisture=0.0,  # Govee doesn't measure soil
            co2=float(self._last_co2_ppm) if self._last_co2_ppm else 0.0,
            leaf_temp_delta=-2.0,  # Assume standard
            dew_point=dew_point,
        )

    async def read_temperature(self) -> float:
        """Read air temperature (Celsius)"""
        reading = await self.read_all()
        return reading.air_temp

    async def read_humidity(self) -> float:
        """Read relative humidity (%)"""
        reading = await self.read_all()
        return reading.humidity

    async def read_soil_moisture(self) -> tuple[float, float, float]:
        """Govee doesn't measure soil - return zeros"""
        return (0.0, 0.0, 0.0)

    async def read_co2(self) -> float:
        """Read CO2 from H5140 sensor if available"""
        if self._last_co2_ppm:
            return float(self._last_co2_ppm)
        # Try to fetch fresh reading
        reading = await self.read_all()
        return reading.co2

    async def read_leaf_temp(self) -> float:
        """Estimate leaf temp (air temp - 2C)"""
        reading = await self.read_all()
        return reading.air_temp - 2.0

    async def is_connected(self) -> bool:
        """Check if connected to Govee API"""
        return self._connected and self._client is not None

    async def get_battery(self) -> Optional[int]:
        """Get battery percentage if available"""
        if self._last_reading:
            return self._last_reading.battery_percent
        return None

    # =========================================================================
    # Humidifier Control
    # =========================================================================

    async def set_humidifier_power(self, on: bool) -> bool:
        """Turn humidifier on or off"""
        if not self.humidifier_device_id or not self._client:
            logger.warning("No humidifier connected")
            return False

        success = await self._client.send_command(
            self.humidifier_device_id,
            self.humidifier_model,
            "devices.capabilities.on_off",
            "powerSwitch",
            1 if on else 0
        )

        if success:
            self._humidifier_on = on
            logger.info(f"Humidifier {'ON' if on else 'OFF'}")

        return success

    async def set_humidifier_target(self, target_humidity: int) -> bool:
        """
        Set target humidity level (40-80%).

        The humidifier will auto-regulate to maintain this level.
        H7145 API: Uses devices.capabilities.range with instance 'humidity'
        """
        if not self.humidifier_device_id or not self._client:
            logger.warning("No humidifier connected")
            return False

        # Clamp to valid range (H7145 supports 40-80%)
        target = max(40, min(80, target_humidity))

        # First set to Auto mode (workMode 3, modeValue 0)
        await self._client.send_command(
            self.humidifier_device_id,
            self.humidifier_model,
            "devices.capabilities.work_mode",
            "workMode",
            {"workMode": 3, "modeValue": 0}  # Auto mode
        )

        # Then set the target humidity via the range capability
        success = await self._client.send_command(
            self.humidifier_device_id,
            self.humidifier_model,
            "devices.capabilities.range",
            "humidity",
            target  # Just the integer value
        )

        if success:
            logger.info(f"Humidifier target set to {target}%")
        return success

    async def get_humidifier_status(self) -> dict:
        """Get current humidifier status"""
        if not self.humidifier_device_id or not self._client:
            return {"connected": False}

        state = await self._client.get_device_state(
            self.humidifier_device_id,
            self.humidifier_model
        )

        if not state:
            return {"connected": True, "online": False}

        props = {}
        for p in state.get("properties", []):
            if p and isinstance(p, dict):
                props.update(p)

        return {
            "connected": True,
            "online": props.get("online", False),
            "power_on": props.get("powerSwitch", 0) == 1,
            "work_mode": props.get("workMode", {}),
        }

    def has_humidifier(self) -> bool:
        """Check if humidifier is connected"""
        return self.humidifier_device_id is not None

    async def disconnect(self):
        """Disconnect from Govee API"""
        if self._client:
            await self._client.close()
        self._connected = False


# =============================================================================
# Convenience Functions
# =============================================================================

async def discover_govee_sensors(api_key: str) -> List[Dict]:
    """
    Discover all Govee sensors on an account.

    Usage:
        sensors = await discover_govee_sensors("your-api-key")
        for s in sensors:
            print(f"{s['deviceName']}: {s['model']}")
    """
    client = GoveeCloudAPI(api_key)
    try:
        devices = await client.get_devices()
        temp_sensors = [
            d for d in devices
            if d.get("model", "").startswith("H5")
        ]
        return temp_sensors
    finally:
        await client.close()


async def quick_read(api_key: str) -> GoveeReading:
    """
    Quick one-shot reading from Govee sensor.

    Usage:
        reading = await quick_read("your-api-key")
        print(f"Temp: {reading.temperature_f}F, Humidity: {reading.humidity}%")
    """
    hub = GoveeSensorHub(api_key=api_key)
    try:
        await hub.connect()
        base_reading = await hub.read_all()

        return GoveeReading(
            timestamp=base_reading.timestamp,
            temperature_c=base_reading.air_temp,
            temperature_f=base_reading.air_temp * 9/5 + 32,
            humidity=base_reading.humidity,
            device_id=hub.device_id,
        )
    finally:
        await hub.disconnect()


# =============================================================================
# CLI for Testing
# =============================================================================

if __name__ == "__main__":
    import sys
    import os

    async def main():
        api_key = os.environ.get("GOVEE_API_KEY")

        if not api_key:
            print("ERROR: Set GOVEE_API_KEY environment variable")
            print("Get your key from: https://developer.govee.com/")
            sys.exit(1)

        if len(sys.argv) > 1 and sys.argv[1] == "discover":
            print("Discovering Govee sensors...")
            sensors = await discover_govee_sensors(api_key)
            print(f"\nFound {len(sensors)} temperature sensor(s):\n")
            for s in sensors:
                print(f"  {s.get('deviceName', 'Unknown')}")
                print(f"    ID: {s.get('device')}")
                print(f"    Model: {s.get('model')}")
                print()
        else:
            print("Reading from Govee sensor...")
            reading = await quick_read(api_key)
            print(f"\nTemperature: {reading.temperature_f:.1f}F ({reading.temperature_c:.1f}C)")
            print(f"Humidity: {reading.humidity:.1f}%")
            print(f"Timestamp: {reading.timestamp}")

    asyncio.run(main())
