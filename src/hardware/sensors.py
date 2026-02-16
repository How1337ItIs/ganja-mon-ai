"""
Sensor Utilities for Grok & Mon
================================
VPD calculation, data validation, and sensor data processing.
Based on SmartGrow DataControl patterns.

Key lessons from SmartGrow:
1. Calculate VPD at sensor level (not in backend)
2. Validate data before storage (filter outliers)
3. Pre-calculate derived metrics
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from enum import Enum


class ValidationResult(Enum):
    """Result of sensor data validation"""
    VALID = "valid"
    OUT_OF_RANGE = "out_of_range"
    IMPOSSIBLE = "impossible"
    SENSOR_ERROR = "sensor_error"


@dataclass
class ValidatedReading:
    """Validated sensor reading with quality info"""
    value: float
    is_valid: bool
    validation_result: ValidationResult
    original_value: float
    corrected: bool = False
    error_message: Optional[str] = None


# =============================================================================
# VPD Calculation
# Based on research and SmartGrow's implementation
# =============================================================================

def calculate_vpd(
    temp_c: float,
    humidity_percent: float,
    leaf_temp_offset_c: float = -2.0
) -> float:
    """
    Calculate Vapor Pressure Deficit (VPD) in kPa.

    VPD is the difference between how much moisture the air can hold
    at saturation vs how much it currently holds. Higher VPD = more
    transpiration potential.

    Formula:
        VPD = SVP_leaf - AVP_air
        SVP = saturation vapor pressure
        AVP = actual vapor pressure

    Args:
        temp_c: Air temperature in Celsius
        humidity_percent: Relative humidity (0-100)
        leaf_temp_offset_c: Leaf temp offset from air (usually -1 to -3°C)

    Returns:
        VPD in kPa (kilopascals)

    Cannabis VPD targets by stage:
        Seedling: 0.4-0.8 kPa
        Vegetative: 0.8-1.2 kPa
        Flowering: 1.0-1.5 kPa
    """
    # Leaf temperature (typically 1-3°C below air temp due to transpiration)
    leaf_temp_c = temp_c + leaf_temp_offset_c

    # Saturation Vapor Pressure at leaf temperature (Tetens formula)
    # SVP = 0.6108 * exp((17.27 * T) / (T + 237.3))
    svp_leaf = 0.6108 * math.exp((17.27 * leaf_temp_c) / (leaf_temp_c + 237.3))

    # Saturation Vapor Pressure at air temperature
    svp_air = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))

    # Actual Vapor Pressure (based on humidity)
    avp = svp_air * (humidity_percent / 100.0)

    # VPD = SVP at leaf - AVP at air
    vpd = svp_leaf - avp

    return round(vpd, 3)


def calculate_vpd_from_fahrenheit(
    temp_f: float,
    humidity_percent: float,
    leaf_temp_offset_c: float = -2.0
) -> float:
    """Calculate VPD from Fahrenheit temperature"""
    temp_c = (temp_f - 32) * 5 / 9
    return calculate_vpd(temp_c, humidity_percent, leaf_temp_offset_c)


def calculate_dew_point(temp_c: float, humidity_percent: float) -> float:
    """
    Calculate dew point temperature.

    The dew point is the temperature at which air becomes saturated
    and condensation begins. Important for preventing mold.

    Args:
        temp_c: Air temperature in Celsius
        humidity_percent: Relative humidity (0-100)

    Returns:
        Dew point in Celsius
    """
    # Magnus formula approximation
    a = 17.27
    b = 237.7

    alpha = ((a * temp_c) / (b + temp_c)) + math.log(humidity_percent / 100.0)
    dew_point = (b * alpha) / (a - alpha)

    return round(dew_point, 2)


def vpd_to_humidity(temp_c: float, target_vpd: float) -> float:
    """
    Calculate required humidity to achieve target VPD.

    Useful for determining humidifier/dehumidifier setpoints.

    Args:
        temp_c: Air temperature in Celsius
        target_vpd: Desired VPD in kPa

    Returns:
        Required humidity percentage (0-100)
    """
    leaf_temp_c = temp_c - 2.0  # Assume standard leaf offset

    svp_leaf = 0.6108 * math.exp((17.27 * leaf_temp_c) / (leaf_temp_c + 237.3))
    svp_air = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))

    # VPD = SVP_leaf - AVP
    # AVP = SVP_leaf - VPD
    avp = svp_leaf - target_vpd

    # AVP = SVP_air * (RH / 100)
    # RH = (AVP / SVP_air) * 100
    humidity = (avp / svp_air) * 100

    return round(max(0, min(100, humidity)), 1)


# =============================================================================
# Data Validation (based on SmartGrow's datasee.ipynb patterns)
# =============================================================================

# Physical limits for sensors
SENSOR_LIMITS = {
    "temperature_c": {"min": -10, "max": 60, "impossible_min": -40, "impossible_max": 80},
    "temperature_f": {"min": 14, "max": 140, "impossible_min": -40, "impossible_max": 176},
    "humidity": {"min": 5, "max": 100, "impossible_min": 0, "impossible_max": 100},
    "vpd": {"min": 0.1, "max": 3.5, "impossible_min": -1, "impossible_max": 10},
    "co2": {"min": 200, "max": 2500, "impossible_min": 0, "impossible_max": 10000},
    "soil_moisture": {"min": 0, "max": 100, "impossible_min": -1, "impossible_max": 101},
    "ph": {"min": 3, "max": 10, "impossible_min": 0, "impossible_max": 14},
    "ec": {"min": 0, "max": 5, "impossible_min": -1, "impossible_max": 20},
    "ppfd": {"min": 0, "max": 2500, "impossible_min": -1, "impossible_max": 5000},
}


def validate_reading(
    value: float,
    sensor_type: str,
    strict: bool = False
) -> ValidatedReading:
    """
    Validate a sensor reading against physical limits.

    Based on SmartGrow's data cleaning patterns:
    - Filter impossible values (sensor errors)
    - Flag out-of-range values (unusual but possible)

    Args:
        value: The sensor reading value
        sensor_type: Type of sensor (e.g., "temperature_c", "vpd")
        strict: If True, reject out-of-range values

    Returns:
        ValidatedReading with validation status
    """
    if sensor_type not in SENSOR_LIMITS:
        return ValidatedReading(
            value=value,
            is_valid=True,
            validation_result=ValidationResult.VALID,
            original_value=value,
        )

    limits = SENSOR_LIMITS[sensor_type]

    # Check for impossible values (sensor malfunction)
    if value < limits["impossible_min"] or value > limits["impossible_max"]:
        return ValidatedReading(
            value=value,
            is_valid=False,
            validation_result=ValidationResult.IMPOSSIBLE,
            original_value=value,
            error_message=f"{sensor_type} value {value} is physically impossible",
        )

    # Check for sensor error indicators (common patterns)
    # SmartGrow found many 0.0 readings that were sensor errors
    if sensor_type in ["co2", "temperature_c", "humidity"] and value == 0:
        return ValidatedReading(
            value=value,
            is_valid=False,
            validation_result=ValidationResult.SENSOR_ERROR,
            original_value=value,
            error_message=f"{sensor_type} reading of 0 indicates sensor error",
        )

    # Check for out-of-range (unusual but not impossible)
    if value < limits["min"] or value > limits["max"]:
        if strict:
            return ValidatedReading(
                value=value,
                is_valid=False,
                validation_result=ValidationResult.OUT_OF_RANGE,
                original_value=value,
                error_message=f"{sensor_type} value {value} outside normal range [{limits['min']}-{limits['max']}]",
            )
        else:
            # Accept but flag
            return ValidatedReading(
                value=value,
                is_valid=True,
                validation_result=ValidationResult.OUT_OF_RANGE,
                original_value=value,
            )

    # Valid reading
    return ValidatedReading(
        value=value,
        is_valid=True,
        validation_result=ValidationResult.VALID,
        original_value=value,
    )


def filter_vpd_outliers(
    vpd_values: list[float],
    min_vpd: float = 0.0,
    max_vpd: float = 3.5
) -> list[float]:
    """
    Filter VPD outliers from a list of readings.

    Based on SmartGrow's Jupyter notebook analysis:
        df = df[df['VPD'] <= 3]
        df = df[df['VPD'] > 0]

    Args:
        vpd_values: List of VPD readings
        min_vpd: Minimum valid VPD (default 0.0)
        max_vpd: Maximum valid VPD (default 3.5)

    Returns:
        Filtered list with outliers removed
    """
    return [v for v in vpd_values if min_vpd < v <= max_vpd]


@dataclass
class SensorReading:
    """
    Complete sensor reading with all calculated values.

    This is what gets stored in the database and published via MQTT.
    VPD and dew point are pre-calculated at sensor read time.
    """
    timestamp: datetime
    sensor_id: str

    # Raw readings
    temperature_c: float
    humidity: float
    co2: Optional[float] = None
    soil_moisture: Optional[float] = None

    # Calculated values (done at read time, not in backend)
    vpd: Optional[float] = None
    dew_point: Optional[float] = None

    # Validation status
    is_valid: bool = True
    validation_errors: list[str] = None

    def __post_init__(self):
        """Calculate derived values and validate"""
        if self.validation_errors is None:
            self.validation_errors = []

        # Calculate VPD if not provided
        if self.vpd is None and self.temperature_c and self.humidity:
            self.vpd = calculate_vpd(self.temperature_c, self.humidity)

        # Calculate dew point if not provided
        if self.dew_point is None and self.temperature_c and self.humidity:
            self.dew_point = calculate_dew_point(self.temperature_c, self.humidity)

        # Validate all readings
        self._validate()

    def _validate(self):
        """Validate all readings"""
        validations = [
            ("temperature_c", self.temperature_c),
            ("humidity", self.humidity),
            ("vpd", self.vpd),
        ]

        if self.co2 is not None:
            validations.append(("co2", self.co2))
        if self.soil_moisture is not None:
            validations.append(("soil_moisture", self.soil_moisture))

        for sensor_type, value in validations:
            if value is not None:
                result = validate_reading(value, sensor_type)
                if not result.is_valid:
                    self.is_valid = False
                    self.validation_errors.append(result.error_message)

    @property
    def temperature_f(self) -> float:
        """Temperature in Fahrenheit"""
        return round(self.temperature_c * 9 / 5 + 32, 2)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "sensor_id": self.sensor_id,
            "temperature_c": self.temperature_c,
            "temperature_f": self.temperature_f,
            "humidity": self.humidity,
            "vpd": self.vpd,
            "dew_point": self.dew_point,
            "co2": self.co2,
            "soil_moisture": self.soil_moisture,
            "is_valid": self.is_valid,
        }


# =============================================================================
# Convenience functions for common operations
# =============================================================================

def process_sensor_data(
    temp_c: float,
    humidity: float,
    co2: Optional[float] = None,
    soil_moisture: Optional[float] = None,
    sensor_id: str = "main"
) -> SensorReading:
    """
    Process raw sensor data into a validated reading.

    This is the main entry point for sensor data processing.
    Calculates VPD, validates data, and returns a complete reading.

    Args:
        temp_c: Temperature in Celsius
        humidity: Relative humidity percentage
        co2: CO2 in ppm (optional)
        soil_moisture: Soil moisture percentage (optional)
        sensor_id: Identifier for the sensor

    Returns:
        Validated SensorReading with all calculated values
    """
    return SensorReading(
        timestamp=datetime.now(),
        sensor_id=sensor_id,
        temperature_c=temp_c,
        humidity=humidity,
        co2=co2,
        soil_moisture=soil_moisture,
    )
