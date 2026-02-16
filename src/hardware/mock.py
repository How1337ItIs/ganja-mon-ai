"""
Mock Hardware Implementations
=============================

Fallback implementations when real hardware is not available.
These return None values to indicate no real data is available.

IMPORTANT: These do NOT generate fake sensor data.
If you see actual readings, they're from real sensors.
Mock sensors clearly indicate data is unavailable.
"""

import asyncio
import base64
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .base import (
    SensorHub,
    ActuatorHub,
    CameraHub,
    SensorReading,
    DeviceState,
)


class MockSensorHub(SensorHub):
    """
    Fallback sensor hub when real sensors aren't connected.

    Returns None values - NO FAKE DATA.
    This ensures the dashboard shows "--" instead of misleading fake readings.
    """

    def __init__(self):
        self._connected = False  # Mock is NOT connected to real sensors
        print("[MOCK] MockSensorHub initialized - NO REAL SENSOR DATA AVAILABLE")

    async def read_all(self) -> SensorReading:
        """Return empty reading with None values"""
        return SensorReading(
            timestamp=datetime.utcnow(),
            air_temp=None,
            humidity=None,
            vpd=None,
            soil_moisture=None,
            co2=None,
            leaf_temp_delta=None,
            soil_moisture_probe1=None,
            soil_moisture_probe2=None,
            soil_temp=None,
            leaf_temp=None,
            light_level=None,
            dew_point=None,
            source="mock_unavailable"
        )

    async def read_temperature(self) -> Optional[float]:
        return None

    async def read_humidity(self) -> Optional[float]:
        return None

    async def read_soil_moisture(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        return (None, None, None)

    async def read_co2(self) -> Optional[float]:
        return None

    async def read_leaf_temp(self) -> Optional[float]:
        return None

    async def is_connected(self) -> bool:
        return False  # Mock is never "connected" to real sensors

    def simulate_watering(self):
        """No-op for mock"""
        pass


class MockActuatorHub(ActuatorHub):
    """
    Simulated actuator control.

    Tracks device states and simulates delays.
    """

    def __init__(
        self,
        # Initial states (from SOLTOMATO patterns)
        initial_state: Optional[Dict[str, bool]] = None,
        # Timing
        water_ml_per_second: float = 50.0,  # 200ml takes 4 seconds
        # Failure injection
        failure_rate: float = 0.0,
    ):
        self._state = DeviceState(
            grow_light=True,
            heat_mat=True,
            circulation_fan=True,
            exhaust_fan=False,
            water_pump=False,
            humidifier=False,
        )

        if initial_state:
            for device, state in initial_state.items():
                if hasattr(self._state, device):
                    setattr(self._state, device, state)

        self.water_ml_per_second = water_ml_per_second
        self.failure_rate = failure_rate
        self._connected = True

        # Track operations
        self.water_dispensed_ml = 0
        self.co2_injections = 0

        # Linked sensor hub for soil moisture updates
        self._sensor_hub: Optional[MockSensorHub] = None

    def link_sensors(self, sensor_hub: MockSensorHub):
        """Link to sensor hub for realistic simulation"""
        self._sensor_hub = sensor_hub

    async def get_state(self) -> DeviceState:
        """Get current device states"""
        self._state.timestamp = datetime.utcnow()
        return self._state

    async def set_device(self, device: str, state: bool) -> bool:
        """Set a device on/off"""
        if random.random() < self.failure_rate:
            raise ConnectionError(f"Simulated failure setting {device}")

        if not hasattr(self._state, device):
            raise ValueError(f"Unknown device: {device}")

        setattr(self._state, device, state)

        # Simulate relay click delay
        await asyncio.sleep(0.1)

        return True

    async def water(self, amount_ml: int) -> bool:
        """Dispense water"""
        if random.random() < self.failure_rate:
            raise ConnectionError("Simulated pump failure")

        # Turn on pump
        self._state.water_pump = True

        # Simulate pumping time
        pump_time = amount_ml / self.water_ml_per_second
        await asyncio.sleep(min(pump_time, 2.0))  # Cap at 2s for testing

        # Turn off pump
        self._state.water_pump = False

        # Track
        self.water_dispensed_ml += amount_ml

        # Update linked sensors
        if self._sensor_hub:
            self._sensor_hub.simulate_watering()

        return True

    async def inject_co2(self, duration_seconds: int = 60) -> bool:
        """Inject CO2"""
        if random.random() < self.failure_rate:
            raise ConnectionError("Simulated CO2 failure")

        # Open solenoid
        self._state.co2_solenoid = True

        # Simulate injection (shortened for testing)
        await asyncio.sleep(min(duration_seconds, 1.0))

        # Close solenoid
        self._state.co2_solenoid = False

        # Track
        self.co2_injections += 1

        return True

    async def is_connected(self) -> bool:
        return self._connected

    async def enter_dark_period(self):
        """Enter dark period (flowering)"""
        await self.set_device("grow_light", False)
        self._state.is_dark_period = True
        self._state.dark_period_start = datetime.utcnow()

    async def exit_dark_period(self):
        """Exit dark period"""
        await self.set_device("grow_light", True)
        self._state.is_dark_period = False
        self._state.dark_period_start = None


class MockCameraHub(CameraHub):
    """
    Fallback camera when real webcam isn't connected.

    Returns a placeholder image - NO FAKE PLANT PHOTOS.
    """

    def __init__(
        self,
        test_image_path: Optional[Path] = None,
        resolution: tuple[int, int] = (1920, 1080),
    ):
        self.test_image_path = test_image_path
        self._resolution = resolution
        self._connected = False  # Mock is NOT connected
        print("[MOCK] MockCameraHub initialized - NO REAL CAMERA CONNECTED")

    async def capture(self, save_path: Optional[Path] = None) -> Optional[bytes]:
        """Return placeholder image indicating no camera"""
        # Generate placeholder - NOT a real photo
        image_data = self._generate_placeholder()

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(image_data)

        return image_data

    async def capture_for_analysis(self) -> tuple[Optional[bytes], Optional[str]]:
        """Return None for analysis when no camera connected"""
        # Return None to indicate no real image available
        return None, None

    async def is_connected(self) -> bool:
        return False  # Mock is never "connected"

    def get_resolution(self) -> tuple[int, int]:
        return self._resolution

    def _generate_placeholder(self) -> bytes:
        """Generate a minimal valid JPEG placeholder"""
        # Minimal 1x1 green JPEG
        return bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD3, 0x28, 0xA2, 0x80, 0x0A, 0x28, 0xA0,
            0x02, 0x8A, 0x28, 0x00, 0xFF, 0xD9
        ])


# =============================================================================
# Factory functions
# =============================================================================

def create_mock_hardware() -> tuple[MockSensorHub, MockActuatorHub, MockCameraHub]:
    """
    Create a linked set of mock hardware for testing.

    Returns:
        Tuple of (sensors, actuators, camera) with sensors linked to actuators
    """
    sensors = MockSensorHub()
    actuators = MockActuatorHub()
    camera = MockCameraHub()

    # Link so watering updates soil moisture
    actuators.link_sensors(sensors)

    return sensors, actuators, camera
