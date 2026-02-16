"""
Sol Cannabis MCP Tools
======================
Tool definitions for Claude to interact with the grow environment.
These tools are exposed via Model Context Protocol (MCP) for AI control.

Enhanced with SmartGrow DataControl patterns:
- MQTT integration for real-time updates
- Setpoints for target comparison
- VPD calculation at sensor level
- Data validation
"""

from typing import Any, Literal, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio

# Import new modules (with graceful fallback for standalone use)
try:
    from src.hardware.sensors import (
        calculate_vpd_from_fahrenheit,
        process_sensor_data,
        validate_reading,
    )
    from src.db.setpoints import get_setpoints, get_current_setpoints
    from src.db.models import GrowthStage
    from src.mqtt.service import get_mqtt_service, MQTTMessage
    from src.mqtt.topics import Topics
    IMPORTS_AVAILABLE = True
except ImportError:
    # Fallback for when running standalone
    IMPORTS_AVAILABLE = False
    from enum import Enum

    class GrowthStage(str, Enum):
        SEEDLING = "seedling"
        VEGETATIVE = "vegetative"
        TRANSITION = "transition"
        FLOWERING = "flowering"
        LATE_FLOWER = "late_flower"
        HARVEST = "harvest"

    def calculate_vpd_from_fahrenheit(temp_f, humidity, offset=-2.0):
        """Fallback VPD calculation"""
        import math
        temp_c = (temp_f - 32) * 5 / 9
        leaf_temp_c = temp_c + offset
        svp_leaf = 0.6108 * math.exp((17.27 * leaf_temp_c) / (leaf_temp_c + 237.3))
        svp_air = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        avp = svp_air * (humidity / 100.0)
        return round(svp_leaf - avp, 3)

    def validate_reading(value, sensor_type):
        from dataclasses import dataclass
        @dataclass
        class Result:
            validation_result: type
            class validation_result:
                value = "valid"
        return Result()

    def get_current_setpoints(stage, is_day=True):
        return {
            "vpd_target": 1.0, "vpd_min": 0.8, "vpd_max": 1.2,
            "temp_target_f": 77, "temp_min_f": 70, "temp_max_f": 85,
            "humidity_target": 55, "humidity_min": 40, "humidity_max": 70,
        }

    class MockMQTT:
        async def publish_sensor_reading(self, *args, **kwargs): pass
        async def publish_actuator_state(self, *args, **kwargs): pass
        async def publish_ai_action(self, *args, **kwargs): pass

    def get_mqtt_service(): return MockMQTT()


# =============================================================================
# Tool Schemas (for MCP tool definitions)
# =============================================================================

TOOLS = [
    {
        "name": "get_environment",
        "description": "Read current environmental conditions including temperature, humidity, VPD, and CO2.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_substrate",
        "description": "Read root zone conditions including soil moisture, EC, and pH.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_light_levels",
        "description": "Read current light levels at canopy (PPFD) and calculate DLI.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "capture_image",
        "description": "Capture a photo from the grow camera(s) for visual analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "camera_id": {
                    "type": "string",
                    "description": "Which camera to use. Options: 'main', 'overhead', 'macro'. Default: 'main'",
                    "default": "main"
                }
            },
            "required": []
        }
    },
    {
        "name": "set_light_intensity",
        "description": "Control the grow light ON/OFF state. VIVOSUN VS1000 has manual dimming (25%/50%/75%/100%), currently set to 50%. Remote control via Tapo plug is ON/OFF only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "intensity_percent": {
                    "type": "integer",
                    "description": "Light state: 0 = OFF, any value 1-100 = ON (at current manual dimmer setting of 50%). Dimmer knob must be adjusted manually to change intensity.",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["intensity_percent"]
        }
    },
    {
        "name": "set_light_schedule",
        "description": "Configure the light on/off schedule.",
        "input_schema": {
            "type": "object",
            "properties": {
                "on_time": {
                    "type": "string",
                    "description": "Time to turn lights on in HH:MM format (24h). Example: '06:00'"
                },
                "off_time": {
                    "type": "string",
                    "description": "Time to turn lights off in HH:MM format (24h). Example: '00:00'"
                },
                "schedule_type": {
                    "type": "string",
                    "enum": ["18/6", "12/12", "20/4", "custom"],
                    "description": "Preset schedule or 'custom' for manual times"
                }
            },
            "required": ["schedule_type"]
        }
    },
    {
        "name": "control_exhaust",
        "description": "Control the exhaust fan speed for temperature and humidity regulation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "speed_percent": {
                    "type": "integer",
                    "description": "Fan speed from 0-100%. Higher = more air exchange.",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["speed_percent"]
        }
    },
    {
        "name": "control_intake",
        "description": "Control the intake fan speed for fresh air supply.",
        "input_schema": {
            "type": "object",
            "properties": {
                "speed_percent": {
                    "type": "integer",
                    "description": "Fan speed from 0-100%.",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["speed_percent"]
        }
    },
    {
        "name": "control_humidifier",
        "description": "Control the humidifier. Can turn on/off and set a target humidity percentage (30-80%). The humidifier will auto-regulate to maintain the target.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["on", "off"],
                    "description": "Turn humidifier 'on' or 'off'"
                },
                "target_humidity": {
                    "type": "integer",
                    "minimum": 40,
                    "maximum": 80,
                    "description": "Target humidity percentage (40-80%). Humidifier will auto-regulate to maintain this level."
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "control_circulation_fan",
        "description": "Control the oscillating circulation fan for air movement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["on", "off"],
                    "description": "Turn fan 'on' or 'off'"
                },
                "oscillate": {
                    "type": "boolean",
                    "description": "Enable oscillation (if supported)",
                    "default": True
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "trigger_irrigation",
        "description": "⚠️ CAREFUL: Run the water pump. Pump is VERY powerful! Normal: 3-5 seconds. NEW SOIL SATURATION (ONE TIME): Up to 20 seconds allowed to fully wet dry soil added today.",
        "input_schema": {
            "type": "object",
            "properties": {
                "duration_seconds": {
                    "type": "integer",
                    "description": "How long to run pump in seconds. NORMAL: 3-5 sec. NEW SOIL SATURATION: 15-20 sec OK (one time only). MAX: 20 sec.",
                    "minimum": 1,
                    "maximum": 20
                },
                "zone": {
                    "type": "string",
                    "description": "Which irrigation zone to water. Default: 'main'",
                    "default": "main"
                }
            },
            "required": ["duration_seconds"]
        }
    },
    {
        "name": "get_growth_stage",
        "description": "Get the current growth stage and how long the plant has been in this stage.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "set_growth_stage",
        "description": "Transition the plant to a new growth stage. This updates target parameters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": ["SEEDLING", "VEGETATIVE", "TRANSITION", "FLOWERING", "LATE_FLOWER", "HARVEST"],
                    "description": "The new growth stage to transition to"
                },
                "reason": {
                    "type": "string",
                    "description": "Explanation for why this transition is happening"
                }
            },
            "required": ["stage", "reason"]
        }
    },
    {
        "name": "get_history",
        "description": "Retrieve historical sensor data and AI decisions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "How many hours of history to retrieve. Max 168 (1 week).",
                    "minimum": 1,
                    "maximum": 168,
                    "default": 24
                },
                "data_type": {
                    "type": "string",
                    "enum": ["environment", "actions", "all"],
                    "description": "Type of data to retrieve",
                    "default": "all"
                }
            },
            "required": []
        }
    },
    {
        "name": "log_observation",
        "description": "Record an observation or note about the plant for future reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["health", "growth", "issue", "milestone", "general"],
                    "description": "Category of observation"
                },
                "observation": {
                    "type": "string",
                    "description": "The observation text to log"
                },
                "severity": {
                    "type": "string",
                    "enum": ["info", "warning", "critical"],
                    "description": "Severity level of the observation",
                    "default": "info"
                }
            },
            "required": ["category", "observation"]
        }
    },
    {
        "name": "get_strain_profile",
        "description": "Get the strain-specific growing parameters if a strain profile is configured.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "control_heat_mat",
        "description": "Control the heat mat for overnight warmth and seedling root zone heating. Critical for maintaining minimum temperatures during dark period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["on", "off"],
                    "description": "Turn heat mat 'on' or 'off'"
                },
                "target_temp_f": {
                    "type": "number",
                    "description": "Target root zone temperature in Fahrenheit (optional, for thermostatic mats)",
                    "minimum": 65,
                    "maximum": 85
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "control_dehumidifier",
        "description": "Control the dehumidifier for lowering humidity during flowering. Important for preventing mold and maintaining proper VPD in late flower.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["on", "off"],
                    "description": "Turn dehumidifier 'on' or 'off'"
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "get_watering_predictions",
        "description": "Get recent watering predictions and their accuracy for learning soil absorption rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of predictions to retrieve",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5
                }
            },
            "required": []
        }
    },
    {
        "name": "get_ai_decision_history",
        "description": "Get historical AI decisions and their outcomes. Use this when you need to review past decisions, learn from what worked, or understand trends over days/weeks. Returns summarized decisions to save context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "How many days of history to retrieve. Max 30 days.",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of decisions to return (most recent first)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "include_actions": {
                    "type": "boolean",
                    "description": "Include the actions taken in each decision",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "get_watering_history",
        "description": "Get historical watering events with before/after soil moisture readings. Use this to understand watering patterns and soil response over time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "How many days of history to retrieve. Max 30 days.",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of watering events to return",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "get_hourly_summary",
        "description": "Get aggregated hourly environmental summaries. Much more compact than raw sensor data - use this for trend analysis over days or weeks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "How many hours of history to retrieve. Max 720 (30 days).",
                    "minimum": 1,
                    "maximum": 720,
                    "default": 48
                }
            },
            "required": []
        }
    },
    {
        "name": "get_observations_log",
        "description": "Get logged observations and notes from previous sessions. Use this to review past issues, milestones, and learnings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "How many days of observations to retrieve. Max 30 days.",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7
                },
                "severity": {
                    "type": "string",
                    "enum": ["all", "info", "warning", "critical"],
                    "description": "Filter by severity level",
                    "default": "all"
                }
            },
            "required": []
        }
    }
]


# =============================================================================
# Tool Handler Stubs (to be implemented with actual hardware integration)
# =============================================================================

@dataclass
class ToolResult:
    """Standard result format for tool calls"""
    success: bool
    data: Any
    error: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": datetime.now().isoformat()
        }


class ToolHandlers:
    """
    Tool handler implementations.

    Enhanced with SmartGrow DataControl patterns:
    - Pre-calculates VPD at sensor level
    - Validates data before returning
    - Publishes to MQTT for real-time updates
    - Compares readings to setpoints
    """

    def __init__(self, sensors=None, actuators=None, database=None):
        self.sensors = sensors
        self.actuators = actuators
        self.database = database
        self._mqtt = get_mqtt_service()
        self._current_stage = GrowthStage.VEGETATIVE  # Track current stage

    async def get_environment(self) -> ToolResult:
        """
        Read environmental sensors with VPD calculation and validation.

        Uses REAL Govee sensors - no fake/stub data.
        """
        # Try to read from real Govee sensors
        temp_f = None
        humidity = None
        co2 = None
        vpd = None
        source = "unavailable"

        try:
            from src.hardware.govee import GoveeSensorHub
            govee = GoveeSensorHub()
            if await govee.is_connected():
                reading = await govee.read_all()
                temp_f = reading.air_temp * 9/5 + 32  # Convert C to F
                humidity = reading.humidity
                co2 = reading.co2 if reading.co2 and reading.co2 > 0 else None
                vpd = reading.vpd
                source = "govee"
        except Exception as e:
            print(f"Govee sensor error: {e}")

        if temp_f is None or humidity is None:
            return ToolResult(
                success=False,
                error="No environmental sensors connected. Connect Govee H5179/H5140 sensors."
            )

        # Calculate VPD if not provided by sensor
        if vpd is None:
            vpd = calculate_vpd_from_fahrenheit(temp_f, humidity)

        # Validate readings (SmartGrow pattern from datasee.ipynb)
        temp_valid = validate_reading(temp_f, "temperature_f")
        humidity_valid = validate_reading(humidity, "humidity")
        vpd_valid = validate_reading(vpd, "vpd")

        # Get current setpoints for comparison
        setpoints = get_current_setpoints(self._current_stage, is_day=True)

        # Build response with setpoint comparison
        data = {
            "temperature_f": temp_f,
            "temperature_c": round((temp_f - 32) * 5 / 9, 2),
            "humidity_percent": humidity,
            "vpd_kpa": vpd,
            "co2_ppm": co2,
            "timestamp": datetime.now().isoformat(),
            # Validation status
            "validation": {
                "temperature": temp_valid.validation_result.value,
                "humidity": humidity_valid.validation_result.value,
                "vpd": vpd_valid.validation_result.value,
            },
            # Setpoint comparison (SmartGrow pattern)
            "vs_setpoint": {
                "vpd_target": setpoints["vpd_target"],
                "vpd_deviation": round(vpd - setpoints["vpd_target"], 3),
                "vpd_in_range": setpoints["vpd_min"] <= vpd <= setpoints["vpd_max"],
                "temp_target": setpoints["temp_target_f"],
                "temp_in_range": setpoints["temp_min_f"] <= temp_f <= setpoints["temp_max_f"],
                "humidity_target": setpoints["humidity_target"],
                "humidity_in_range": setpoints["humidity_min"] <= humidity <= setpoints["humidity_max"],
            },
            "source": source
        }

        # Publish to MQTT for real-time dashboard (SmartGrow pattern)
        await self._mqtt.publish_sensor_reading("environment", data)

        return ToolResult(success=True, data=data)
    
    async def get_substrate(self) -> ToolResult:
        """
        Read substrate/soil sensors from connected sensor hub.
        
        Tries sensors in order of reliability:
        1. Ecowitt GW1100 (professional, local API)
        2. ESP32 DIY sensor (custom build)
        3. Stub data (fallback for development)
        """
        watering_threshold = 30.0 if self._current_stage in [GrowthStage.FLOWERING, GrowthStage.LATE_FLOWER] else 40.0
        
        # Try Ecowitt first (professional grade, most reliable)
        try:
            from src.hardware.ecowitt import EcowittSoilHub
            hub = EcowittSoilHub(host="192.168.125.100")  # Update with your gateway IP
            reading = await hub.read()
            
            if reading and reading.sensors:
                # Build probe data from Ecowitt sensors
                probe1 = reading.sensors[0].moisture_percent if len(reading.sensors) > 0 else 0
                probe2 = reading.sensors[1].moisture_percent if len(reading.sensors) > 1 else probe1
                
                data = {
                    "probe1_percent": probe1,
                    "probe2_percent": probe2,
                    "moisture_percent": reading.average_moisture,
                    "needs_water": reading.needs_water,
                    "watering_threshold": watering_threshold,
                    "sensor_count": len(reading.sensors),
                    "batteries": [s.battery_status for s in reading.sensors],
                    "ec_ms_cm": None,
                    "ph": None,
                    "timestamp": datetime.now().isoformat(),
                    "source": "ecowitt_gw1100"
                }
                await self._mqtt.publish_sensor_reading("substrate", data)
                return ToolResult(success=True, data=data)
        except ImportError:
            pass
        except Exception as e:
            print(f"Ecowitt sensor error: {e}")
        
        # Try ESP32 DIY sensor as fallback
        try:
            from src.hardware.soil_sensor import SoilSensorHub
            hub = SoilSensorHub(host="soil.local")
            reading = await hub.read()
            
            if reading:
                data = {
                    "probe1_percent": reading.probe1,
                    "probe2_percent": reading.probe2,
                    "moisture_percent": reading.average,
                    "needs_water": reading.average < watering_threshold,
                    "watering_threshold": watering_threshold,
                    "temperature_f": round(reading.raw_probe1 * 0.02 + 68, 1) if reading.raw_probe1 else 72.0,
                    "ec_ms_cm": None,
                    "ph": None,
                    "timestamp": datetime.now().isoformat(),
                    "source": "esp32_soil_hub"
                }
                await self._mqtt.publish_sensor_reading("substrate", data)
                return ToolResult(success=True, data=data)
        except ImportError:
            pass
        except Exception as e:
            print(f"ESP32 sensor error: {e}")
        
        # No sensors connected - return error (no fake data)
        return ToolResult(
            success=False,
            error="No soil sensors connected. Use visual meter reading via /api/meters/visual-read or connect Ecowitt GW1100 soil sensor.",
            data={
                "probe1_percent": None,
                "probe2_percent": None,
                "moisture_percent": None,
                "needs_water": None,
                "watering_threshold": watering_threshold,
                "timestamp": datetime.now().isoformat(),
                "source": "unavailable"
            }
        )
    
    async def get_light_levels(self) -> ToolResult:
        """Read light sensor - currently checks Kasa light state only"""
        lights_on = None
        source = "unavailable"

        # Try to read from Kasa smart plug
        try:
            from src.hardware.kasa import KasaController
            kasa = KasaController()
            if await kasa.is_connected():
                state = await kasa.get_state()
                lights_on = state.grow_light
                source = "kasa"
        except Exception as e:
            print(f"Kasa light state error: {e}")

        return ToolResult(
            success=True,
            data={
                "ppfd_umol": None,  # No PAR sensor connected
                "dli_mol": None,  # Cannot calculate without PAR sensor
                "lights_on": lights_on,
                "hours_on_today": None,  # Need timer tracking
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "note": "No PAR sensor connected. Only light on/off state available from Kasa plug."
            }
        )
    
    async def capture_image(self, camera_id: str = "main") -> ToolResult:
        """Capture camera image using USB webcam"""
        import base64
        from pathlib import Path

        try:
            from src.hardware.webcam import USBWebcam, get_logitech_index

            # Get camera index (use Logitech C270 if available)
            device_index = get_logitech_index()
            webcam = USBWebcam(device_index=device_index)

            # Create timelapse directory
            timelapse_dir = Path("data/timelapse")
            timelapse_dir.mkdir(parents=True, exist_ok=True)

            # Generate timestamp filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            save_path = timelapse_dir / filename

            # Capture image (release after to allow other processes to use camera)
            image_bytes = await webcam.capture(save_path=save_path, release_after=True)

            # Encode to base64 for AI analysis
            b64_string = base64.b64encode(image_bytes).decode('utf-8')

            return ToolResult(
                success=True,
                data={
                    "camera_id": camera_id,
                    "image_path": str(save_path),
                    "image_base64": b64_string,
                    "image_size_kb": len(image_bytes) / 1024,
                    "captured_at": datetime.now().isoformat(),
                    "source": "usb_webcam"
                }
            )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"Webcam module not available: {e}. Install opencv-python.",
                data={"camera_id": camera_id}
            )
        except ConnectionError as e:
            return ToolResult(
                success=False,
                error=f"Webcam not connected: {e}",
                data={"camera_id": camera_id}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Capture failed: {e}",
                data={"camera_id": camera_id}
            )
    
    async def set_light_intensity(self, intensity_percent: int) -> ToolResult:
        """
        Set light intensity via Tapo smart plug.

        Note: VIVOSUN VS1000 has manual dimming knob (25%/50%/75%/100%).
        Currently set to 50% (2nd of 4 settings) for clone phase.
        Smart plug controls ON/OFF only:
        - intensity > 0 = ON (at current manual dimmer setting)
        - intensity = 0 = OFF
        """
        # Safety bounds
        intensity_percent = max(0, min(100, intensity_percent))

        # Map intensity to on/off (Kasa plugs are not dimmable)
        light_on = intensity_percent > 0

        try:
            from src.hardware.kasa import KasaActuatorHub
            import os

            # Get Kasa light IP from environment
            light_ip = os.environ.get("KASA_GROW_LIGHT_IP")
            if not light_ip:
                # Try Tapo as fallback
                tapo_light = os.environ.get("TAPO_GROW_LIGHT_IP")
                if tapo_light:
                    from src.hardware import TapoActuatorHub
                    tapo = TapoActuatorHub()
                    if await tapo.connect():
                        await tapo.set_device("grow_light", light_on)
                        return ToolResult(
                            success=True,
                            data={
                                "intensity_percent": 100 if light_on else 0,
                                "actual_state": "ON" if light_on else "OFF",
                                "manual_dimmer_setting": "50% (2nd of 4 positions)",
                                "light_distance": "16 inches from plant top",
                                "note": "VIVOSUN VS1000 at 50% power, 16\" height. Tapo plug controls ON/OFF only.",
                                "applied_at": datetime.now().isoformat(),
                                "source": "tapo"
                            }
                        )

                return ToolResult(
                    success=False,
                    error="No grow light configured. Set KASA_GROW_LIGHT_IP or TAPO_GROW_LIGHT_IP in .env",
                    data={"intensity_percent": intensity_percent}
                )

            kasa = KasaActuatorHub({"grow_light": light_ip})
            if await kasa.connect():
                await kasa.set_device("grow_light", light_on)
                return ToolResult(
                    success=True,
                    data={
                        "intensity_percent": 100 if light_on else 0,
                        "actual_state": "ON" if light_on else "OFF",
                        "manual_dimmer_setting": "50% (2nd of 4 positions)",
                        "light_distance": "16 inches from plant top",
                        "note": "VIVOSUN VS1000 at 50% power, 16\" height. Smart plug controls ON/OFF only.",
                        "applied_at": datetime.now().isoformat(),
                        "source": "kasa"
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error="Failed to connect to Kasa plug",
                    data={"intensity_percent": intensity_percent}
                )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"Kasa module not available: {e}",
                data={"intensity_percent": intensity_percent}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Light control failed: {e}",
                data={"intensity_percent": intensity_percent}
            )
    
    async def set_light_schedule(
        self,
        schedule_type: str,
        on_time: str = None,
        off_time: str = None
    ) -> ToolResult:
        """
        Configure light schedule using PhotoperiodScheduler.

        schedule_type: "18/6" (vegetative), "12/12" (flowering), "20/4", or "custom"
        on_time: Time lights turn on (HH:MM format), e.g. "06:00"
        off_time: Time lights turn off (HH:MM format), e.g. "00:00"
        """
        try:
            from src.scheduling.photoperiod import PhotoperiodScheduler, PhotoperiodConfig

            # Parse on_time to get hour
            light_on_hour = 6  # Default
            if on_time:
                try:
                    parts = on_time.split(":")
                    light_on_hour = int(parts[0])
                except (ValueError, IndexError):
                    pass

            # Map schedule types to PhotoperiodConfig
            if schedule_type == "18/6" or schedule_type == "vegetative":
                config = PhotoperiodConfig.vegetative(light_on_hour=light_on_hour)
                schedule_name = "18/6 (vegetative)"
            elif schedule_type == "12/12" or schedule_type == "flowering":
                config = PhotoperiodConfig.flowering(light_on_hour=light_on_hour)
                schedule_name = "12/12 (flowering)"
            elif schedule_type == "20/4":
                config = PhotoperiodConfig(
                    light_on_hour=light_on_hour,
                    hours_on=20,
                    hours_off=4,
                )
                schedule_name = "20/4 (vegetative)"
            elif schedule_type == "24/0":
                config = PhotoperiodConfig(
                    light_on_hour=0,
                    hours_on=24,
                    hours_off=0,
                )
                schedule_name = "24/0 (clone/seedling)"
            elif schedule_type == "custom" and on_time and off_time:
                # Parse custom schedule
                try:
                    on_parts = on_time.split(":")
                    off_parts = off_time.split(":")
                    on_hour = int(on_parts[0])
                    off_hour = int(off_parts[0])

                    # Calculate hours on
                    if off_hour > on_hour:
                        hours_on = off_hour - on_hour
                    else:
                        hours_on = 24 - on_hour + off_hour

                    config = PhotoperiodConfig(
                        light_on_hour=on_hour,
                        hours_on=hours_on,
                        hours_off=24 - hours_on,
                    )
                    schedule_name = f"{hours_on}/{24 - hours_on} (custom)"
                except (ValueError, IndexError) as e:
                    return ToolResult(
                        success=False,
                        error=f"Invalid time format: {e}. Use HH:MM format.",
                        data={"schedule_type": schedule_type}
                    )
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown schedule type: {schedule_type}. Use 18/6, 12/12, 20/4, 24/0, or custom",
                    data={"schedule_type": schedule_type}
                )

            # Note: PhotoperiodScheduler is typically managed by the orchestrator
            # This tool returns the config that should be applied
            return ToolResult(
                success=True,
                data={
                    "schedule_type": schedule_type,
                    "schedule_name": schedule_name,
                    "light_on_hour": config.light_on_hour,
                    "light_off_hour": config.light_off_hour,
                    "hours_light": config.hours_on,
                    "hours_dark": config.hours_off,
                    "on_time": f"{config.light_on_hour:02d}:{config.light_on_minute:02d}",
                    "off_time": f"{config.light_off_hour:02d}:{config.light_off_minute:02d}",
                    "applied_at": datetime.now().isoformat(),
                    "note": "Schedule config generated. Orchestrator will apply on next cycle."
                }
            )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"PhotoperiodScheduler not available: {e}. Install apscheduler.",
                data={"schedule_type": schedule_type}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Schedule configuration failed: {e}",
                data={"schedule_type": schedule_type}
            )
    
    async def control_exhaust(self, speed_percent: int) -> ToolResult:
        """
        DEPRECATED: No exhaust fan in current hardware setup.

        The fan previously labeled "exhaust" is actually the INTAKE fan.
        Use control_intake() instead.
        """
        return ToolResult(
            success=False,
            error="No exhaust fan available. Use control_intake() to control the inline intake fan.",
            data={"speed_percent": speed_percent, "deprecated": True}
        )
    
    async def control_intake(self, speed_percent: int) -> ToolResult:
        """
        Control intake fan via Kasa smart plug.

        Note: Kasa plugs are ON/OFF only (not variable speed).
        - speed > 0 = ON
        - speed = 0 = OFF
        """
        speed_percent = max(0, min(100, speed_percent))

        # Map speed to on/off (Kasa plugs are not variable speed)
        fan_on = speed_percent > 0

        try:
            from src.hardware.kasa import KasaActuatorHub
            import os

            # HARDWARE REALITY: The fan labeled KASA_EXHAUST_FAN_IP is actually the INTAKE fan
            intake_ip = os.environ.get("KASA_EXHAUST_FAN_IP")  # Mislabeled in .env but correct hardware
            if not intake_ip:
                return ToolResult(
                    success=False,
                    error="Intake fan not configured. Set KASA_EXHAUST_FAN_IP in .env",
                    data={"speed_percent": speed_percent}
                )

            kasa = KasaActuatorHub({"intake_fan": intake_ip})
            if await kasa.connect():
                await kasa.set_device("intake_fan", fan_on)
                return ToolResult(
                    success=True,
                    data={
                        "device": "intake_fan",
                        "speed_percent": 100 if fan_on else 0,
                        "actual_state": "ON" if fan_on else "OFF",
                        "note": "Kasa plug is ON/OFF only, not variable speed",
                        "applied_at": datetime.now().isoformat(),
                        "source": "kasa"
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error="Failed to connect to Kasa plug for intake fan",
                    data={"speed_percent": speed_percent}
                )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"Kasa module not available: {e}",
                data={"speed_percent": speed_percent}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Intake fan control failed: {e}",
                data={"speed_percent": speed_percent}
            )
    
    async def control_humidifier(self, state: Literal["on", "off"]) -> ToolResult:
        """Control humidifier"""
        return ToolResult(
            success=True,
            data={
                "device": "humidifier",
                "state": state,
                "applied_at": datetime.now().isoformat()
            }
        )
    
    async def control_circulation_fan(
        self, 
        state: Literal["on", "off"],
        oscillate: bool = True
    ) -> ToolResult:
        """Control circulation fan"""
        return ToolResult(
            success=True,
            data={
                "device": "circulation_fan",
                "state": state,
                "oscillate": oscillate,
                "applied_at": datetime.now().isoformat()
            }
        )
    
    async def trigger_irrigation(
        self,
        duration_seconds: int,
        zone: str = "main"
    ) -> ToolResult:
        """
        Trigger watering pump.

        ⚠️  CRITICAL: The pump is VERY powerful and dispenses water fast!
        - Normal max: 10 seconds
        - NEW SOIL SATURATION (Jan 24, 2026): Up to 20 seconds allowed ONE TIME
        - Recommended normal: 3-5 seconds (~100-200ml)
        - Saturation burst: 15-20 seconds (~500-700ml)
        """
        # SAFETY LIMIT - temporarily raised to 20 sec for new soil saturation
        duration_seconds = max(1, min(20, duration_seconds))

        if duration_seconds > 5:
            print(f"⚠️  WARNING: Pump duration {duration_seconds}s is high. Pump is very powerful!")
        
        return ToolResult(
            success=True,
            data={
                "zone": zone,
                "duration_seconds": duration_seconds,
                "started_at": datetime.now().isoformat()
            }
        )
    
    async def get_growth_stage(self) -> ToolResult:
        """Get current growth stage from database"""
        try:
            from src.db.connection import get_db_session
            from src.db.models import GrowSession
            from sqlalchemy import select

            async with get_db_session() as session:
                result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=False,
                        error="No active grow session found. Create one via /api/grow/reset"
                    )

                stage = grow_session.current_stage.value if grow_session.current_stage else "UNKNOWN"
                setpoints = get_current_setpoints(GrowthStage(stage) if stage != "UNKNOWN" else GrowthStage.VEGETATIVE, is_day=True)

                return ToolResult(
                    success=True,
                    data={
                        "stage": stage,
                        "days_in_stage": grow_session.current_day or 1,
                        "started_at": grow_session.start_date.isoformat() if grow_session.start_date else None,
                        "plant_name": grow_session.plant_name,
                        "strain_name": grow_session.strain_name,
                        "photoperiod": grow_session.photoperiod.value if grow_session.photoperiod else None,
                        "target_parameters": {
                            "vpd_min": setpoints["vpd_min"],
                            "vpd_max": setpoints["vpd_max"],
                            "temp_min_f": setpoints["temp_min_f"],
                            "temp_max_f": setpoints["temp_max_f"],
                            "humidity_min": setpoints["humidity_min"],
                            "humidity_max": setpoints["humidity_max"]
                        }
                    }
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get growth stage from database: {e}"
            )
    
    async def set_growth_stage(self, stage: str, reason: str) -> ToolResult:
        """Transition to new growth stage - saves to database"""
        valid_stages = ["SEEDLING", "VEGETATIVE", "TRANSITION", "FLOWERING", "LATE_FLOWER", "HARVEST"]

        if stage not in valid_stages:
            return ToolResult(
                success=False,
                data=None,
                error=f"Invalid stage. Must be one of: {valid_stages}"
            )

        try:
            from src.db.connection import get_db_session
            from src.db.models import GrowSession, GrowthStage as GrowthStageEnum
            from sqlalchemy import select

            async with get_db_session() as session:
                result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=False,
                        error="No active grow session found"
                    )

                previous_stage = grow_session.current_stage.value if grow_session.current_stage else "UNKNOWN"
                grow_session.current_stage = GrowthStageEnum(stage)
                grow_session.notes = f"{grow_session.notes or ''}\n[{datetime.now().isoformat()}] Stage change to {stage}: {reason}"
                await session.commit()

                # Update local tracking
                self._current_stage = GrowthStage(stage)

                return ToolResult(
                    success=True,
                    data={
                        "previous_stage": previous_stage,
                        "new_stage": stage,
                        "reason": reason,
                        "transitioned_at": datetime.now().isoformat()
                    }
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to update growth stage: {e}"
            )
    
    async def get_history(
        self,
        hours: int = 24,
        data_type: str = "all"
    ) -> ToolResult:
        """Get historical data from database"""
        try:
            from src.db.connection import get_db_session
            from src.db.models import SensorReading, AIDecision
            from sqlalchemy import select, func
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(hours=hours)
            records = []
            summary = {"record_count": 0}

            async with get_db_session() as session:
                # Query sensor readings
                if data_type in ["all", "sensors"]:
                    result = await session.execute(
                        select(SensorReading)
                        .where(SensorReading.timestamp >= cutoff)
                        .order_by(SensorReading.timestamp.desc())
                        .limit(100)
                    )
                    readings = result.scalars().all()

                    for r in readings:
                        records.append({
                            "type": "sensor",
                            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                            "temperature_f": r.air_temp_f,
                            "humidity": r.humidity,
                            "vpd": r.vpd_kpa,
                            "co2": r.co2_ppm
                        })

                    # Calculate averages from real data
                    if readings:
                        temps = [r.air_temp_f for r in readings if r.air_temp_f]
                        humids = [r.humidity for r in readings if r.humidity]
                        vpds = [r.vpd_kpa for r in readings if r.vpd_kpa]
                        summary = {
                            "record_count": len(readings),
                            "avg_temp_f": round(sum(temps) / len(temps), 1) if temps else None,
                            "avg_humidity": round(sum(humids) / len(humids), 1) if humids else None,
                            "avg_vpd": round(sum(vpds) / len(vpds), 3) if vpds else None
                        }

            return ToolResult(
                success=True,
                data={
                    "hours_requested": hours,
                    "data_type": data_type,
                    "records": records,
                    "summary": summary
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get history from database: {e}"
            )
    
    async def log_observation(
        self,
        category: str,
        observation: str,
        severity: str = "info"
    ) -> ToolResult:
        """
        Log an observation to the EpisodicMemory table.

        category: "health", "growth", "issue", "milestone", "general"
        observation: The observation text
        severity: "info", "warning", "critical"
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import EpisodicMemory, GrowSession
            from sqlalchemy import select

            async with get_db_session() as session:
                # Get active grow session
                result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=False,
                        error="No active grow session found. Create one via /api/grow/reset",
                        data={"category": category, "observation": observation}
                    )

                # Map severity to importance score
                importance_map = {"info": 1.0, "warning": 2.0, "critical": 3.0}
                importance = importance_map.get(severity, 1.0)

                # Create time label based on current hour
                hour = datetime.now().hour
                if 5 <= hour < 12:
                    time_label = "MORNING OBSERVATION"
                elif 12 <= hour < 17:
                    time_label = "AFTERNOON OBSERVATION"
                elif 17 <= hour < 21:
                    time_label = "EVENING OBSERVATION"
                else:
                    time_label = "NIGHT OBSERVATION"

                # Build formatted text
                formatted = f"[{category.upper()}] ({severity}) {observation}"

                # Create episodic memory entry
                memory = EpisodicMemory(
                    session_id=grow_session.id,
                    grow_day=grow_session.current_day or 1,
                    time_label=time_label,
                    conditions={},  # No sensor data for manual observations
                    observations=[observation],
                    formatted_text=formatted,
                    importance_score=importance,
                )
                session.add(memory)
                await session.commit()

                return ToolResult(
                    success=True,
                    data={
                        "memory_id": memory.id,
                        "category": category,
                        "observation": observation,
                        "severity": severity,
                        "grow_day": grow_session.current_day,
                        "importance_score": importance,
                        "logged_at": datetime.now().isoformat()
                    }
                )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"Database module not available: {e}",
                data={"category": category, "observation": observation}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to log observation: {e}",
                data={"category": category, "observation": observation}
            )
    
    async def get_strain_profile(self) -> ToolResult:
        """
        Get strain-specific parameters.

        Loads strain name from GrowSession and returns hardcoded profile data
        for Granddaddy Purple Runtz (current grow).
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import GrowSession
            from sqlalchemy import select

            strain_name = "Granddaddy Purple Runtz"  # Default
            profile_loaded = True

            # Try to get strain from database
            try:
                async with get_db_session() as session:
                    result = await session.execute(
                        select(GrowSession).where(GrowSession.is_active == True)
                    )
                    grow_session = result.scalar_one_or_none()
                    if grow_session and grow_session.strain_name:
                        strain_name = grow_session.strain_name
            except Exception:
                pass  # Use default

            # Granddaddy Purple Runtz strain profile (hardcoded from CLAUDE.md)
            if strain_name.lower() in ["granddaddy purple runtz", "gdp runtz", "grandaddy purple runtz"]:
                return ToolResult(
                    success=True,
                    data={
                        "strain_name": "Granddaddy Purple Runtz",
                        "breeder": "Unknown",
                        "lineage": "Granddaddy Purple x Runtz",
                        "genetics": "Indica-dominant hybrid",
                        "flowering_time_days": "56-63",
                        "flowering_time_weeks": "8-9",
                        "yield_potential": "Medium-High",
                        "profile_loaded": True,
                        "characteristics": {
                            "mold_resistant": True,
                            "pest_resistant": True,
                            "purple_potential": True,
                        },
                        "cultivation_tips": [
                            "Responds well to LST (Low Stress Training)",
                            "Can handle topping",
                            "Drop temps in late flower to bring out purple coloration",
                            "Standard nutrient requirements",
                        ],
                        "vpd_preferences": {
                            "vegetative": {"min": 0.8, "max": 1.2, "target": 1.0},
                            "flowering": {"min": 1.0, "max": 1.5, "target": 1.2},
                            "late_flower": {"min": 1.2, "max": 1.6, "target": 1.4},
                        },
                        "temp_preferences_f": {
                            "vegetative": {"min": 70, "max": 85, "target": 78},
                            "flowering": {"min": 65, "max": 80, "target": 75},
                            "late_flower": {"min": 60, "max": 75, "target": 68},  # Cold for purple
                        },
                        "notes": "Granddaddy Purple Runtz is an indica-dominant hybrid. GDP genetics bring grape/berry flavors. Dropping temps in late flower helps express purple coloration."
                    }
                )
            else:
                # Generic profile for unknown strains
                return ToolResult(
                    success=True,
                    data={
                        "strain_name": strain_name,
                        "breeder": "Unknown",
                        "lineage": "Unknown",
                        "genetics": "Hybrid",
                        "flowering_time_days": "56-70",
                        "flowering_time_weeks": "8-10",
                        "yield_potential": "Varies",
                        "profile_loaded": False,
                        "characteristics": {},
                        "cultivation_tips": [
                            "Use standard cannabis cultivation practices",
                            "Monitor VPD closely",
                            "Adjust based on plant response",
                        ],
                        "vpd_preferences": {
                            "vegetative": {"min": 0.8, "max": 1.2, "target": 1.0},
                            "flowering": {"min": 1.0, "max": 1.5, "target": 1.2},
                        },
                        "temp_preferences_f": {
                            "vegetative": {"min": 70, "max": 85, "target": 77},
                            "flowering": {"min": 65, "max": 80, "target": 75},
                        },
                        "notes": f"No specific profile for {strain_name}. Using generic parameters."
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get strain profile: {e}",
                data={}
            )

    async def control_heat_mat(
        self,
        state: Literal["on", "off"],
        target_temp_f: Optional[float] = None
    ) -> ToolResult:
        """Control heat mat for overnight warmth"""
        # SOLTOMATO pattern: heat mat is critical for overnight temps
        return ToolResult(
            success=True,
            data={
                "device": "heat_mat",
                "state": state,
                "target_temp_f": target_temp_f,
                "applied_at": datetime.now().isoformat()
            }
        )

    async def control_dehumidifier(self, state: Literal["on", "off"]) -> ToolResult:
        """Control dehumidifier for flowering humidity management"""
        return ToolResult(
            success=True,
            data={
                "device": "dehumidifier",
                "state": state,
                "applied_at": datetime.now().isoformat()
            }
        )

    async def get_watering_predictions(self, limit: int = 5) -> ToolResult:
        """
        Get recent watering predictions from database for AI learning context.

        Returns prediction history with accuracy data and calculated
        average absorption rate.
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import WateringPrediction, GrowSession
            from sqlalchemy import select, desc

            async with get_db_session() as session:
                # Get active grow session
                session_result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = session_result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=True,
                        data={
                            "predictions": [],
                            "average_absorption_rate_ml_per_pct": 20.0,
                            "note": "No active grow session. Using default absorption rate of 20ml per 1%."
                        }
                    )

                # Query recent watering predictions
                result = await session.execute(
                    select(WateringPrediction)
                    .where(WateringPrediction.session_id == grow_session.id)
                    .order_by(desc(WateringPrediction.timestamp))
                    .limit(limit)
                )
                predictions = result.scalars().all()

                if not predictions:
                    return ToolResult(
                        success=True,
                        data={
                            "predictions": [],
                            "average_absorption_rate_ml_per_pct": 20.0,
                            "note": "No watering predictions recorded yet. Default: ~20ml water increases soil moisture by 1%."
                        }
                    )

                # Build prediction list
                prediction_list = []
                absorption_rates = []

                for p in predictions:
                    pred_data = {
                        "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                        "grow_day": p.grow_day,
                        "amount_ml": p.amount_ml,
                        "before": {
                            "probe1": p.probe1_before,
                            "probe2": p.probe2_before,
                            "average": p.avg_before,
                        },
                        "predicted_after": {
                            "probe1": p.predicted_probe1_after,
                            "probe2": p.predicted_probe2_after,
                            "average": p.predicted_avg_after,
                        },
                        "actual_after": {
                            "probe1": p.actual_probe1_after,
                            "probe2": p.actual_probe2_after,
                            "average": p.actual_avg_after,
                        } if p.actual_avg_after else None,
                        "verified": p.verified_at is not None,
                        "accuracy_pct": p.accuracy_pct,
                    }
                    prediction_list.append(pred_data)

                    # Collect absorption rates from verified predictions
                    if p.calculated_absorption_rate:
                        absorption_rates.append(p.calculated_absorption_rate)

                # Calculate average absorption rate
                if absorption_rates:
                    avg_rate = sum(absorption_rates) / len(absorption_rates)
                else:
                    avg_rate = 20.0  # Default: ~20ml per 1%

                return ToolResult(
                    success=True,
                    data={
                        "predictions": prediction_list,
                        "prediction_count": len(prediction_list),
                        "verified_count": sum(1 for p in prediction_list if p["verified"]),
                        "average_absorption_rate_ml_per_pct": round(avg_rate, 1),
                        "note": f"Based on {len(absorption_rates)} verified predictions. ~{avg_rate:.0f}ml water increases soil moisture by 1%."
                    }
                )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=f"Database module not available: {e}",
                data={"average_absorption_rate_ml_per_pct": 20.0}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get watering predictions: {e}",
                data={"average_absorption_rate_ml_per_pct": 20.0}
            )

    async def get_ai_decision_history(
        self,
        days: int = 7,
        limit: int = 20,
        include_actions: bool = True
    ) -> ToolResult:
        """
        Get historical AI decisions for learning and context.
        Returns summarized decisions to save context space.
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import AIDecision, GrowSession
            from sqlalchemy import select, desc
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)

            async with get_db_session() as session:
                # Get active session
                session_result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = session_result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=True,
                        data={"decisions": [], "note": "No active grow session"}
                    )

                # Query AI decisions
                result = await session.execute(
                    select(AIDecision)
                    .where(AIDecision.session_id == grow_session.id)
                    .where(AIDecision.timestamp >= cutoff)
                    .order_by(desc(AIDecision.timestamp))
                    .limit(limit)
                )
                decisions = result.scalars().all()

                decision_list = []
                for d in decisions:
                    entry = {
                        "timestamp": d.timestamp.isoformat() if d.timestamp else None,
                        "grow_day": d.mon_day,
                        "health_assessment": d.health_assessment,
                        "vpd": d.vpd_reading,
                        "conditions": {
                            "temp_c": d.air_temp,
                            "humidity": d.humidity,
                            "soil_moisture": d.soil_moisture,
                        },
                    }
                    if include_actions and d.actions_taken:
                        entry["actions"] = d.actions_taken[:3]  # Limit to 3 actions to save context
                    # Include short summary if available
                    if d.output_text:
                        # Extract first 200 chars as summary
                        entry["summary"] = d.output_text[:200] + "..." if len(d.output_text) > 200 else d.output_text

                    decision_list.append(entry)

                return ToolResult(
                    success=True,
                    data={
                        "decisions": decision_list,
                        "count": len(decision_list),
                        "days_covered": days,
                        "note": f"Retrieved {len(decision_list)} decisions from the last {days} days"
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get AI decision history: {e}",
                data={"decisions": []}
            )

    async def get_watering_history(
        self,
        days: int = 7,
        limit: int = 20
    ) -> ToolResult:
        """
        Get historical watering events with soil moisture changes.
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import WateringPrediction, GrowSession
            from sqlalchemy import select, desc
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)

            async with get_db_session() as session:
                session_result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = session_result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=True,
                        data={"events": [], "note": "No active grow session"}
                    )

                result = await session.execute(
                    select(WateringPrediction)
                    .where(WateringPrediction.session_id == grow_session.id)
                    .where(WateringPrediction.timestamp >= cutoff)
                    .order_by(desc(WateringPrediction.timestamp))
                    .limit(limit)
                )
                waterings = result.scalars().all()

                events = []
                total_water = 0
                for w in waterings:
                    total_water += w.amount_ml or 0
                    events.append({
                        "timestamp": w.timestamp.isoformat() if w.timestamp else None,
                        "grow_day": w.grow_day,
                        "amount_ml": w.amount_ml,
                        "soil_before": w.avg_before,
                        "soil_after": w.actual_avg_after,
                        "change_pct": round(w.actual_avg_after - w.avg_before, 1) if w.actual_avg_after and w.avg_before else None,
                    })

                return ToolResult(
                    success=True,
                    data={
                        "events": events,
                        "count": len(events),
                        "total_water_ml": total_water,
                        "days_covered": days,
                        "note": f"{len(events)} watering events, {total_water}ml total over {days} days"
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get watering history: {e}",
                data={"events": []}
            )

    async def get_hourly_summary(self, hours: int = 48) -> ToolResult:
        """
        Get aggregated hourly environmental summaries.
        Much more compact than raw data for trend analysis.
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import HourlyAggregate, GrowSession
            from sqlalchemy import select, desc

            async with get_db_session() as session:
                session_result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = session_result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=True,
                        data={"summaries": [], "note": "No active grow session"}
                    )

                result = await session.execute(
                    select(HourlyAggregate)
                    .where(HourlyAggregate.session_id == grow_session.id)
                    .order_by(desc(HourlyAggregate.period_start))
                    .limit(hours)
                )
                aggregates = result.scalars().all()

                summaries = []
                for a in reversed(aggregates):  # Chronological order
                    summaries.append({
                        "hour": a.period_start.isoformat() if a.period_start else None,
                        "day": a.grow_day,
                        "temp": round(a.avg_temp, 1),
                        "rh": round(a.avg_humidity, 1),
                        "vpd": round(a.avg_vpd, 2),
                        "soil": round(a.avg_soil_moisture, 1),
                        "co2": round(a.avg_co2, 0),
                        "healthy": all([a.temp_healthy, a.humidity_healthy, a.vpd_healthy]),
                        "icon": a.icon,
                    })

                # Calculate trends
                if len(summaries) >= 2:
                    first = summaries[0]
                    last = summaries[-1]
                    trends = {
                        "temp_trend": round(last["temp"] - first["temp"], 1),
                        "rh_trend": round(last["rh"] - first["rh"], 1),
                        "vpd_trend": round(last["vpd"] - first["vpd"], 2),
                    }
                else:
                    trends = {}

                return ToolResult(
                    success=True,
                    data={
                        "summaries": summaries,
                        "hours_covered": len(summaries),
                        "trends": trends,
                        "note": f"{len(summaries)} hourly summaries"
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get hourly summary: {e}",
                data={"summaries": []}
            )

    async def get_observations_log(
        self,
        days: int = 7,
        severity: str = "all"
    ) -> ToolResult:
        """
        Get logged observations and notes.
        """
        try:
            from src.db.connection import get_db_session
            from src.db.models import EpisodicMemory, GrowSession
            from sqlalchemy import select, desc
            from datetime import timedelta

            cutoff = datetime.utcnow() - timedelta(days=days)

            async with get_db_session() as session:
                session_result = await session.execute(
                    select(GrowSession).where(GrowSession.is_active == True)
                )
                grow_session = session_result.scalar_one_or_none()

                if not grow_session:
                    return ToolResult(
                        success=True,
                        data={"observations": [], "note": "No active grow session"}
                    )

                query = select(EpisodicMemory).where(
                    EpisodicMemory.session_id == grow_session.id,
                    EpisodicMemory.timestamp >= cutoff
                )

                # Filter by severity if specified
                if severity != "all":
                    severity_scores = {"info": 1.0, "warning": 2.0, "critical": 3.0}
                    if severity in severity_scores:
                        query = query.where(EpisodicMemory.importance_score >= severity_scores[severity])

                result = await session.execute(
                    query.order_by(desc(EpisodicMemory.timestamp)).limit(50)
                )
                memories = result.scalars().all()

                observations = []
                for m in memories:
                    observations.append({
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                        "day": m.grow_day,
                        "time_label": m.time_label,
                        "observations": m.observations,
                        "importance": m.importance_score,
                        "text": m.formatted_text[:300] if m.formatted_text else None,
                    })

                return ToolResult(
                    success=True,
                    data={
                        "observations": observations,
                        "count": len(observations),
                        "days_covered": days,
                        "filter": severity,
                        "note": f"{len(observations)} observations from the last {days} days"
                    }
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get observations: {e}",
                data={"observations": []}
            )


# =============================================================================
# Tool Router
# =============================================================================

async def handle_tool_call(
    tool_name: str, 
    tool_input: dict,
    handlers: ToolHandlers
) -> dict:
    """Route tool calls to appropriate handlers"""
    
    handler_map = {
        "get_environment": lambda: handlers.get_environment(),
        "get_substrate": lambda: handlers.get_substrate(),
        "get_light_levels": lambda: handlers.get_light_levels(),
        "capture_image": lambda: handlers.capture_image(**tool_input),
        "set_light_intensity": lambda: handlers.set_light_intensity(**tool_input),
        "set_light_schedule": lambda: handlers.set_light_schedule(**tool_input),
        "control_exhaust": lambda: handlers.control_exhaust(**tool_input),
        "control_intake": lambda: handlers.control_intake(**tool_input),
        "control_humidifier": lambda: handlers.control_humidifier(**tool_input),
        "control_circulation_fan": lambda: handlers.control_circulation_fan(**tool_input),
        "trigger_irrigation": lambda: handlers.trigger_irrigation(**tool_input),
        "get_growth_stage": lambda: handlers.get_growth_stage(),
        "set_growth_stage": lambda: handlers.set_growth_stage(**tool_input),
        "get_history": lambda: handlers.get_history(**tool_input),
        "log_observation": lambda: handlers.log_observation(**tool_input),
        "get_strain_profile": lambda: handlers.get_strain_profile(),
        # SOLTOMATO additions
        "control_heat_mat": lambda: handlers.control_heat_mat(**tool_input),
        "control_dehumidifier": lambda: handlers.control_dehumidifier(**tool_input),
        "get_watering_predictions": lambda: handlers.get_watering_predictions(**tool_input),
        # Extended history tools (optional context fetching)
        "get_ai_decision_history": lambda: handlers.get_ai_decision_history(**tool_input),
        "get_watering_history": lambda: handlers.get_watering_history(**tool_input),
        "get_hourly_summary": lambda: handlers.get_hourly_summary(**tool_input),
        "get_observations_log": lambda: handlers.get_observations_log(**tool_input),
    }
    
    if tool_name not in handler_map:
        return ToolResult(
            success=False,
            data=None,
            error=f"Unknown tool: {tool_name}"
        ).to_dict()
    
    result = await handler_map[tool_name]()
    return result.to_dict()


if __name__ == "__main__":
    # Print tool schemas for reference
    print(json.dumps(TOOLS, indent=2))
