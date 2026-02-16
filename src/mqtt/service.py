"""
MQTT Service for Grok & Mon
============================
Real-time pub/sub communication layer for IoT devices.
Based on SmartGrow DataControl's mqtt.service.ts pattern.

Features:
- Async MQTT client with automatic reconnection
- Topic-based message routing
- JSON message serialization
- Message handlers via callbacks
- Integration with database for persistence
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional, Any
from dataclasses import dataclass, field

try:
    import aiomqtt
    AIOMQTT_AVAILABLE = True
except ImportError:
    AIOMQTT_AVAILABLE = False

from .topics import Topics

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    """MQTT connection configuration"""
    host: str = "localhost"
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: str = "grokmon-backend"
    keepalive: int = 60
    reconnect_interval: int = 5
    # WebSocket support for browser clients
    websocket_port: int = 8083
    websocket_path: str = "/mqtt"


@dataclass
class MQTTMessage:
    """Structured MQTT message"""
    topic: str
    payload: dict
    timestamp: datetime = field(default_factory=datetime.now)
    qos: int = 0
    retain: bool = False

    def to_json(self) -> str:
        """Serialize message to JSON string"""
        data = {
            **self.payload,
            "_timestamp": self.timestamp.isoformat(),
            "_topic": self.topic,
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, topic: str, payload: bytes) -> "MQTTMessage":
        """Deserialize message from JSON bytes"""
        try:
            data = json.loads(payload.decode("utf-8"))
            timestamp = datetime.fromisoformat(data.pop("_timestamp", None) or datetime.now().isoformat())
            data.pop("_topic", None)
            return cls(topic=topic, payload=data, timestamp=timestamp)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse MQTT message: {e}")
            return cls(topic=topic, payload={"raw": payload.decode("utf-8", errors="replace")})


# Type alias for message handlers
MessageHandler = Callable[[MQTTMessage], None]


class MQTTService:
    """
    MQTT Service for real-time IoT communication.

    Based on SmartGrow DataControl's MqttService pattern:
    - Connects to MQTT broker on initialization
    - Subscribes to wildcard topics for sensors/actuators
    - Routes messages to registered handlers
    - Publishes actuator commands and AI decisions

    Usage:
        mqtt = MQTTService(config)
        mqtt.on_message(Topics.SENSORS_WILDCARD, handle_sensor_data)
        await mqtt.connect()
        await mqtt.publish(Topics.AI_DECISION, {"action": "water", "reason": "..."})
    """

    def __init__(self, config: Optional[MQTTConfig] = None):
        self.config = config or MQTTConfig()
        self._client: Optional[Any] = None
        self._connected = False
        self._running = False
        self._handlers: dict[str, list[MessageHandler]] = {}
        self._message_queue: asyncio.Queue[MQTTMessage] = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []

        if not AIOMQTT_AVAILABLE:
            logger.warning(
                "aiomqtt not installed. MQTT functionality disabled. "
                "Install with: pip install aiomqtt"
            )

    @property
    def connected(self) -> bool:
        """Check if connected to broker"""
        return self._connected

    # ==========================================================================
    # Simple start / stop / subscribe interface
    # ==========================================================================

    async def start(self) -> None:
        """
        Start the MQTT service.

        Launches the connection loop as a background task so the caller
        is not blocked.  Gracefully degrades if aiomqtt is missing.
        """
        if not AIOMQTT_AVAILABLE:
            logger.warning("MQTT disabled -- aiomqtt not installed. pip install aiomqtt")
            return

        if self._running:
            logger.debug("MQTT service already running")
            return

        task = asyncio.create_task(self.connect())
        self._tasks.append(task)
        logger.info("MQTT service started (background)")

    async def stop(self) -> None:
        """
        Stop the MQTT service and cancel background tasks.
        """
        await self.disconnect()

        for task in self._tasks:
            if not task.done():
                task.cancel()
        self._tasks.clear()
        logger.info("MQTT service stopped")

    async def subscribe(self, topic: str, handler: Optional[MessageHandler] = None) -> None:
        """
        Subscribe to a topic, optionally with a handler.

        If called while connected the subscription is sent immediately.
        Otherwise it is registered and will be subscribed on next connect.

        Args:
            topic: MQTT topic or wildcard pattern
            handler: Optional callback for messages on this topic
        """
        if handler:
            self.on_message(topic, handler)

        # If we are already connected, subscribe right away
        if self._connected and self._client:
            try:
                await self._client.subscribe(topic)
                logger.info(f"Live-subscribed to: {topic}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {topic}: {e}")
        else:
            logger.debug(f"Queued subscription for: {topic} (will subscribe on connect)")

    def on_message(self, topic_pattern: str, handler: MessageHandler) -> None:
        """
        Register a message handler for a topic pattern.

        Args:
            topic_pattern: MQTT topic or wildcard pattern (e.g., "grokmon/sensors/#")
            handler: Callback function to handle messages

        Example:
            def handle_sensor(msg: MQTTMessage):
                print(f"Sensor data: {msg.payload}")

            mqtt.on_message(Topics.SENSORS_WILDCARD, handle_sensor)
        """
        if topic_pattern not in self._handlers:
            self._handlers[topic_pattern] = []
        self._handlers[topic_pattern].append(handler)
        logger.debug(f"Registered handler for topic: {topic_pattern}")

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """
        Check if a topic matches a pattern with wildcards.

        MQTT wildcards:
        - # matches any number of levels
        - + matches exactly one level
        """
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")

        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == "#":
                return True  # # matches everything after
            if i >= len(topic_parts):
                return False
            if pattern_part == "+":
                continue  # + matches any single level
            if pattern_part != topic_parts[i]:
                return False

        return len(pattern_parts) == len(topic_parts)

    def _dispatch_message(self, message: MQTTMessage) -> None:
        """Route message to matching handlers"""
        for pattern, handlers in self._handlers.items():
            if self._topic_matches(pattern, message.topic):
                for handler in handlers:
                    try:
                        handler(message)
                    except Exception as e:
                        logger.error(f"Handler error for {message.topic}: {e}")

    async def connect(self) -> None:
        """Connect to MQTT broker and start message loop"""
        if not AIOMQTT_AVAILABLE:
            logger.warning("MQTT disabled - aiomqtt not installed")
            return

        self._running = True
        logger.info(f"Connecting to MQTT broker at {self.config.host}:{self.config.port}")

        while self._running:
            try:
                async with aiomqtt.Client(
                    hostname=self.config.host,
                    port=self.config.port,
                    username=self.config.username,
                    password=self.config.password,
                    identifier=self.config.client_id,
                    keepalive=self.config.keepalive,
                ) as client:
                    self._client = client
                    self._connected = True
                    logger.info("Connected to MQTT broker")

                    # Subscribe to all registered topic patterns
                    for pattern in self._handlers.keys():
                        await client.subscribe(pattern)
                        logger.info(f"Subscribed to: {pattern}")

                    # Also subscribe to default topics
                    await client.subscribe(Topics.SENSORS_WILDCARD)
                    await client.subscribe(Topics.ACTUATORS_STATE_WILDCARD)
                    logger.info("Subscribed to default sensor/actuator topics")

                    # Message receive loop
                    async for mqtt_message in client.messages:
                        topic = str(mqtt_message.topic)
                        message = MQTTMessage.from_json(topic, mqtt_message.payload)
                        self._dispatch_message(message)

            except aiomqtt.MqttError as e:
                self._connected = False
                logger.error(f"MQTT connection error: {e}")
                if self._running:
                    logger.info(f"Reconnecting in {self.config.reconnect_interval}s...")
                    await asyncio.sleep(self.config.reconnect_interval)
            except Exception as e:
                self._connected = False
                logger.error(f"Unexpected MQTT error: {e}")
                if self._running:
                    await asyncio.sleep(self.config.reconnect_interval)

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        self._running = False
        self._connected = False
        self._client = None
        logger.info("Disconnected from MQTT broker")

    async def publish(
        self,
        topic: str,
        payload: dict,
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """
        Publish a message to a topic.

        Args:
            topic: MQTT topic to publish to
            payload: Dict payload (will be JSON serialized)
            qos: Quality of Service (0, 1, or 2)
            retain: Whether to retain the message

        Returns:
            True if published successfully, False otherwise
        """
        if not AIOMQTT_AVAILABLE:
            logger.warning(f"MQTT disabled - would publish to {topic}: {payload}")
            return False

        if not self._connected or not self._client:
            logger.warning(f"Not connected - queuing message for {topic}")
            return False

        message = MQTTMessage(topic=topic, payload=payload, qos=qos, retain=retain)

        try:
            await self._client.publish(
                topic=topic,
                payload=message.to_json(),
                qos=qos,
                retain=retain,
            )
            logger.debug(f"Published to {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False

    # ==========================================================================
    # Convenience methods for common publish operations
    # ==========================================================================

    async def publish_sensor_reading(
        self,
        sensor_type: str,
        data: dict,
        sensor_id: str = "main"
    ) -> bool:
        """Publish a sensor reading"""
        topic = Topics.sensor_topic(sensor_type, sensor_id)
        return await self.publish(topic, data)

    async def publish_actuator_state(
        self,
        actuator_type: str,
        state: bool,
        extra_data: Optional[dict] = None
    ) -> bool:
        """Publish actuator state change"""
        topic = Topics.actuator_state_topic(actuator_type)
        payload = {"state": state, **(extra_data or {})}
        return await self.publish(topic, payload, retain=True)

    async def publish_actuator_command(
        self,
        actuator_type: str,
        command: str,
        parameters: Optional[dict] = None
    ) -> bool:
        """Send command to actuator"""
        topic = Topics.actuator_cmd_topic(actuator_type)
        payload = {"command": command, **(parameters or {})}
        return await self.publish(topic, payload)

    async def publish_ai_decision(self, decision: dict) -> bool:
        """Broadcast an AI decision"""
        return await self.publish(Topics.AI_DECISION, decision)

    async def publish_ai_action(self, action: dict) -> bool:
        """Broadcast an AI action"""
        return await self.publish(Topics.AI_ACTION, action)

    async def publish_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info"
    ) -> bool:
        """Publish a system alert"""
        payload = {
            "type": alert_type,
            "message": message,
            "severity": severity,
        }
        return await self.publish(Topics.SYSTEM_ALERT, payload)

    async def publish_growth_stage(self, stage: str, day: int, reason: str) -> bool:
        """Publish growth stage update"""
        payload = {
            "stage": stage,
            "day": day,
            "reason": reason,
        }
        return await self.publish(Topics.GROW_STAGE, payload, retain=True)


# =============================================================================
# Global MQTT service instance
# =============================================================================

_mqtt_service: Optional[MQTTService] = None


def get_mqtt_service(config: Optional[MQTTConfig] = None) -> MQTTService:
    """Get or create the global MQTT service instance"""
    global _mqtt_service
    if _mqtt_service is None:
        _mqtt_service = MQTTService(config)
    return _mqtt_service


async def init_mqtt(config: Optional[MQTTConfig] = None) -> MQTTService:
    """Initialize and connect the MQTT service"""
    service = get_mqtt_service(config)
    # Start connection in background task
    asyncio.create_task(service.connect())
    return service


async def close_mqtt() -> None:
    """Close the MQTT service"""
    global _mqtt_service
    if _mqtt_service:
        await _mqtt_service.disconnect()
        _mqtt_service = None
