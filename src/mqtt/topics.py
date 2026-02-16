"""
MQTT Topic Definitions
======================
Centralized topic management for Grok & Mon IoT communication.

Topic Structure:
    grokmon/{category}/{device_type}/{device_id?}

Examples:
    grokmon/sensors/scd40/main      - CO2/Temp/Humidity sensor readings
    grokmon/sensors/soil/probe1     - Soil moisture probe 1
    grokmon/actuators/light/state   - Light on/off state
    grokmon/ai/decisions            - AI decision broadcasts
"""


class Topics:
    """MQTT topic definitions with wildcard support"""

    # Base prefix for all topics
    PREFIX = "grokmon"

    # ==========================================================================
    # Sensor Topics (sensors publish readings here)
    # ==========================================================================

    # Environment sensors
    SENSOR_SCD40 = f"{PREFIX}/sensors/scd40"           # CO2, temp, humidity, VPD
    SENSOR_BME680 = f"{PREFIX}/sensors/bme680"         # Temp, humidity, pressure, gas
    SENSOR_LIGHT = f"{PREFIX}/sensors/light"           # PPFD, light level

    # Substrate/soil sensors
    SENSOR_SOIL_MOISTURE = f"{PREFIX}/sensors/soil/moisture"
    SENSOR_SOIL_TEMP = f"{PREFIX}/sensors/soil/temp"
    SENSOR_PH_EC = f"{PREFIX}/sensors/phec"            # pH and EC readings

    # Aggregate sensor data (all sensors combined)
    SENSORS_ALL = f"{PREFIX}/sensors/all"

    # Wildcard for subscribing to all sensors
    SENSORS_WILDCARD = f"{PREFIX}/sensors/#"

    # ==========================================================================
    # Actuator Topics (control commands and state)
    # ==========================================================================

    # State broadcasts (actuators publish current state)
    ACTUATOR_LIGHT_STATE = f"{PREFIX}/actuators/light/state"
    ACTUATOR_FAN_EXHAUST_STATE = f"{PREFIX}/actuators/fan/exhaust/state"
    ACTUATOR_FAN_INTAKE_STATE = f"{PREFIX}/actuators/fan/intake/state"
    ACTUATOR_FAN_CIRCULATION_STATE = f"{PREFIX}/actuators/fan/circulation/state"
    ACTUATOR_HUMIDIFIER_STATE = f"{PREFIX}/actuators/humidifier/state"
    ACTUATOR_PUMP_STATE = f"{PREFIX}/actuators/pump/state"

    # Command topics (backend publishes commands here)
    ACTUATOR_LIGHT_CMD = f"{PREFIX}/actuators/light/cmd"
    ACTUATOR_FAN_EXHAUST_CMD = f"{PREFIX}/actuators/fan/exhaust/cmd"
    ACTUATOR_FAN_INTAKE_CMD = f"{PREFIX}/actuators/fan/intake/cmd"
    ACTUATOR_FAN_CIRCULATION_CMD = f"{PREFIX}/actuators/fan/circulation/cmd"
    ACTUATOR_HUMIDIFIER_CMD = f"{PREFIX}/actuators/humidifier/cmd"
    ACTUATOR_PUMP_CMD = f"{PREFIX}/actuators/pump/cmd"

    # Wildcard for all actuator topics
    ACTUATORS_WILDCARD = f"{PREFIX}/actuators/#"
    ACTUATORS_STATE_WILDCARD = f"{PREFIX}/actuators/+/state"
    ACTUATORS_CMD_WILDCARD = f"{PREFIX}/actuators/+/cmd"

    # ==========================================================================
    # AI/System Topics
    # ==========================================================================

    # AI decision broadcasts
    AI_DECISION = f"{PREFIX}/ai/decision"
    AI_ACTION = f"{PREFIX}/ai/action"
    AI_OBSERVATION = f"{PREFIX}/ai/observation"

    # System status
    SYSTEM_STATUS = f"{PREFIX}/system/status"
    SYSTEM_HEARTBEAT = f"{PREFIX}/system/heartbeat"
    SYSTEM_ALERT = f"{PREFIX}/system/alert"

    # Growth stage changes
    GROW_STAGE = f"{PREFIX}/grow/stage"
    GROW_DAY = f"{PREFIX}/grow/day"

    # ==========================================================================
    # Utility Methods
    # ==========================================================================

    @classmethod
    def sensor_topic(cls, sensor_type: str, sensor_id: str = "main") -> str:
        """Generate a sensor topic for a specific sensor"""
        return f"{cls.PREFIX}/sensors/{sensor_type}/{sensor_id}"

    @classmethod
    def actuator_state_topic(cls, actuator_type: str) -> str:
        """Generate an actuator state topic"""
        return f"{cls.PREFIX}/actuators/{actuator_type}/state"

    @classmethod
    def actuator_cmd_topic(cls, actuator_type: str) -> str:
        """Generate an actuator command topic"""
        return f"{cls.PREFIX}/actuators/{actuator_type}/cmd"

    @classmethod
    def parse_topic(cls, topic: str) -> dict:
        """
        Parse a topic string into its components.

        Args:
            topic: Full topic string like "grokmon/sensors/scd40/main"

        Returns:
            Dict with keys: prefix, category, type, id (optional)
        """
        parts = topic.split("/")
        result = {
            "prefix": parts[0] if len(parts) > 0 else None,
            "category": parts[1] if len(parts) > 1 else None,
            "type": parts[2] if len(parts) > 2 else None,
            "id": parts[3] if len(parts) > 3 else None,
        }
        return result
