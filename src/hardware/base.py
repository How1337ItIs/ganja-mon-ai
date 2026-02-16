"""
Hardware Base Classes
=====================

Abstract interfaces for hardware components.
Implementations can be mock (for testing) or real (for production).

Based on SOLTOMATO's sensor/device structure:
- 6 core sensor readings
- 6 controllable devices
- Camera for visual monitoring
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class SensorReading:
    """
    Unified sensor reading for all sensor data.

    All fields default to None to indicate "no data" when sensors aren't connected.
    Fields only have values when real sensor data is available.
    """
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Core sensors - None means no data available
    air_temp: Optional[float] = None           # Celsius
    humidity: Optional[float] = None           # Percentage
    vpd: Optional[float] = None                # kPa (calculated)
    soil_moisture: Optional[float] = None      # Percentage (averaged)
    co2: Optional[float] = None                # ppm
    leaf_temp_delta: Optional[float] = None    # Celsius difference from air

    # Extended sensors
    soil_moisture_probe1: Optional[float] = None
    soil_moisture_probe2: Optional[float] = None
    soil_temp: Optional[float] = None
    leaf_temp: Optional[float] = None
    light_level: Optional[int] = None      # 0-1023 raw ADC
    light_ppfd: Optional[float] = None     # umol/m²/s
    dew_point: Optional[float] = None      # Celsius

    # Data source tracking
    source: Optional[str] = None  # "govee", "ecowitt", "mock_unavailable", etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (API-compatible format)"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "air_temp": self.air_temp,
            "humidity": self.humidity,
            "vpd": self.vpd,
            "soil_moisture": self.soil_moisture,
            "co2": self.co2,
            "leaf_temp_delta": self.leaf_temp_delta,
            "soil_moisture_probe1": self.soil_moisture_probe1,
            "soil_moisture_probe2": self.soil_moisture_probe2,
            "soil_temp": self.soil_temp,
            "light_level": self.light_level,
            "source": self.source,
        }

    @staticmethod
    def calculate_vpd(air_temp: Optional[float], humidity: Optional[float], leaf_temp: Optional[float] = None) -> Optional[float]:
        """
        Calculate Vapor Pressure Deficit.

        VPD = (1 - RH/100) * SVP(leaf_temp)
        Where SVP = 0.6108 * exp(17.27 * T / (T + 237.3))

        If leaf_temp not provided, assumes leaf is 2°C cooler than air.
        Returns None if required inputs are missing.
        """
        if air_temp is None or humidity is None:
            return None

        if leaf_temp is None:
            leaf_temp = air_temp - 2.0

        # Saturation vapor pressure at leaf temperature (kPa)
        svp_leaf = 0.6108 * (2.71828 ** (17.27 * leaf_temp / (leaf_temp + 237.3)))

        # Actual vapor pressure based on air temp and humidity
        svp_air = 0.6108 * (2.71828 ** (17.27 * air_temp / (air_temp + 237.3)))
        avp = svp_air * (humidity / 100)

        # VPD
        vpd = svp_leaf - avp
        return round(max(0, vpd), 2)

    @staticmethod
    def calculate_dew_point(air_temp: float, humidity: float) -> float:
        """Calculate dew point temperature"""
        a = 17.27
        b = 237.7
        alpha = ((a * air_temp) / (b + air_temp)) + (humidity / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        return round(dew_point, 1)


@dataclass
class DeviceState:
    """
    Device/actuator states matching SOLTOMATO's structure.

    Core devices:
    - grow_light, heat_mat, circulation_fan, exhaust_fan, water_pump, humidifier

    Cannabis additions:
    - dehumidifier, co2_solenoid
    - Dark period tracking
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Core devices (SOLTOMATO compatible)
    grow_light: bool = False
    heat_mat: bool = False
    circulation_fan: bool = False
    exhaust_fan: bool = False
    water_pump: bool = False
    humidifier: bool = False

    # Cannabis additions
    dehumidifier: bool = False
    co2_solenoid: bool = False

    # Dark period tracking (critical for flowering)
    is_dark_period: bool = False
    dark_period_start: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (API-compatible format)"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "grow_light": self.grow_light,
            "heat_mat": self.heat_mat,
            "circulation_fan": self.circulation_fan,
            "exhaust_fan": self.exhaust_fan,
            "water_pump": self.water_pump,
            "humidifier": self.humidifier,
            "dehumidifier": self.dehumidifier,
            "co2_solenoid": self.co2_solenoid,
            "is_dark_period": self.is_dark_period,
        }


class SensorHub(ABC):
    """
    Abstract interface for sensor collection.

    Implementations:
    - MockSensorHub: Simulated readings for testing
    - RealSensorHub: Actual hardware (DHT22, SCD30, etc.)
    """

    @abstractmethod
    async def read_all(self) -> SensorReading:
        """Read all sensors and return unified reading"""
        pass

    @abstractmethod
    async def read_temperature(self) -> float:
        """Read air temperature (Celsius)"""
        pass

    @abstractmethod
    async def read_humidity(self) -> float:
        """Read relative humidity (%)"""
        pass

    @abstractmethod
    async def read_soil_moisture(self) -> tuple[float, float, float]:
        """Read soil moisture: (probe1, probe2, average)"""
        pass

    @abstractmethod
    async def read_co2(self) -> float:
        """Read CO2 level (ppm)"""
        pass

    @abstractmethod
    async def read_leaf_temp(self) -> float:
        """Read leaf surface temperature (Celsius)"""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if sensors are responding"""
        pass


class ActuatorHub(ABC):
    """
    Abstract interface for actuator/device control.

    Implementations:
    - MockActuatorHub: Simulated control for testing
    - KasaActuatorHub: TP-Link Kasa smart plugs
    - GPIOActuatorHub: Direct Raspberry Pi GPIO
    """

    @abstractmethod
    async def get_state(self) -> DeviceState:
        """Get current state of all devices"""
        pass

    @abstractmethod
    async def set_device(self, device: str, state: bool) -> bool:
        """
        Set a device on/off.

        Args:
            device: Device name (grow_light, exhaust_fan, etc.)
            state: True for on, False for off

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def water(self, amount_ml: int) -> bool:
        """
        Dispense water.

        Args:
            amount_ml: Amount in milliliters

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def inject_co2(self, duration_seconds: int = 60) -> bool:
        """
        Inject CO2 for specified duration.

        Args:
            duration_seconds: How long to open solenoid

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if actuators are responding"""
        pass

    # Convenience methods
    async def light_on(self) -> bool:
        return await self.set_device("grow_light", True)

    async def light_off(self) -> bool:
        return await self.set_device("grow_light", False)

    async def exhaust_on(self) -> bool:
        return await self.set_device("exhaust_fan", True)

    async def exhaust_off(self) -> bool:
        return await self.set_device("exhaust_fan", False)

    async def fan_on(self) -> bool:
        return await self.set_device("circulation_fan", True)

    async def fan_off(self) -> bool:
        return await self.set_device("circulation_fan", False)


class CameraHub(ABC):
    """
    Abstract interface for camera operations.

    Implementations:
    - MockCameraHub: Returns test images
    - USBCameraHub: USB webcam via OpenCV
    - PiCameraHub: Raspberry Pi Camera Module
    """

    @abstractmethod
    async def capture(self, save_path: Optional[Path] = None) -> bytes:
        """
        Capture an image.

        Args:
            save_path: Optional path to save image file

        Returns:
            Image bytes (JPEG)
        """
        pass

    @abstractmethod
    async def capture_for_analysis(self) -> tuple[bytes, str]:
        """
        Capture image optimized for AI analysis.

        Returns:
            Tuple of (image_bytes, base64_encoded)
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if camera is available"""
        pass

    @abstractmethod
    def get_resolution(self) -> tuple[int, int]:
        """Get camera resolution (width, height)"""
        pass
