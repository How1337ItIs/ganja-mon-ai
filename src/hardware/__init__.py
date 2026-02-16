"""
Hardware Abstraction Layer
==========================

Provides interfaces for sensors, actuators, and cameras.
Supports both mock (simulation) and real hardware implementations.

Enhanced with SmartGrow DataControl patterns:
- VPD calculation at sensor level
- Data validation with outlier filtering
- Sensor data processing utilities

Usage:
    # For development/testing (no hardware)
    from src.hardware import MockSensorHub, MockActuatorHub

    sensors = MockSensorHub()
    reading = await sensors.read_all()

    # For production (with real hardware)
    from src.hardware import RealSensorHub, KasaActuatorHub

    sensors = RealSensorHub(config)
    actuators = KasaActuatorHub(config)

    # VPD calculation (SmartGrow pattern)
    from src.hardware import calculate_vpd, validate_reading

    vpd = calculate_vpd(temp_c=24.0, humidity=55.0)
"""

from .base import (
    SensorHub,
    ActuatorHub,
    CameraHub,
    SensorReading,
    DeviceState,
)
from .mock import (
    MockSensorHub,
    MockActuatorHub,
    MockCameraHub,
)
from .tapo import (
    TapoActuatorHub,
    TapoDeviceConfig,
    EnergyUsage,
    create_tapo_hub,
)
from .kasa import (
    KasaActuatorHub,
    KasaDeviceConfig,
    discover_kasa_devices,
)
from .govee import (
    GoveeSensorHub,
    GoveeCloudAPI,
    GoveeReading,
    discover_govee_sensors,
)
from .webcam import (
    USBWebcam,
    TimelapseController,
    list_cameras,
    get_logitech_index,
)
from .sensors import (
    calculate_vpd,
    calculate_vpd_from_fahrenheit,
    calculate_dew_point,
    vpd_to_humidity,
    validate_reading,
    filter_vpd_outliers,
    process_sensor_data,
    SensorReading as ProcessedSensorReading,
    ValidationResult,
    SENSOR_LIMITS,
)

__all__ = [
    # Base classes
    "SensorHub",
    "ActuatorHub",
    "CameraHub",
    "SensorReading",
    "DeviceState",
    # Mock implementations
    "MockSensorHub",
    "MockActuatorHub",
    "MockCameraHub",
    # Tapo smart plug implementations
    "TapoActuatorHub",
    "TapoDeviceConfig",
    "EnergyUsage",
    "create_tapo_hub",
    # Kasa smart plug implementations
    "KasaActuatorHub",
    "KasaDeviceConfig",
    "discover_kasa_devices",
    # Govee WiFi sensor
    "GoveeSensorHub",
    "GoveeCloudAPI",
    "GoveeReading",
    "discover_govee_sensors",
    # Webcam
    "USBWebcam",
    "TimelapseController",
    "list_cameras",
    "get_logitech_index",
    # Sensor utilities (SmartGrow patterns)
    "calculate_vpd",
    "calculate_vpd_from_fahrenheit",
    "calculate_dew_point",
    "vpd_to_humidity",
    "validate_reading",
    "filter_vpd_outliers",
    "process_sensor_data",
    "ProcessedSensorReading",
    "ValidationResult",
    "SENSOR_LIMITS",
]
