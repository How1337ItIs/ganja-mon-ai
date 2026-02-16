"""
Arduino/ESP32 Node Integration
==============================
Handles communication with distributed Arduino and ESP32 sensor/actuator nodes.

Supports:
- MQTT for WiFi-enabled ESP32 nodes
- Serial for directly-connected Arduino nodes
- Automatic discovery and health monitoring
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional

# Optional imports with graceful fallback
try:
    import aiomqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

try:
    import serial_asyncio
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """Types of Arduino/ESP32 nodes"""
    ENVIRONMENT = "environment"      # Sensor node (temp, humidity, CO2, etc.)
    IRRIGATION = "irrigation"        # Pump/valve controller
    SAFETY = "safety"                # Hardware failsafe
    DIMMER = "dimmer"                # LED light controller
    FAN = "fan"                      # Fan speed controller
    PH_EC = "ph_ec"                  # Hydroponic pH/EC controller


class NodeStatus(str, Enum):
    """Node health status"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass
class NodeReading:
    """Sensor reading from a node"""
    node_id: str
    node_type: NodeType
    timestamp: datetime
    data: dict[str, Any]
    valid: bool = True
    error: Optional[str] = None


@dataclass
class Node:
    """Represents an Arduino/ESP32 node"""
    node_id: str
    node_type: NodeType
    connection_type: str  # "mqtt" or "serial"
    address: str  # MQTT topic prefix or serial port
    
    # State
    status: NodeStatus = NodeStatus.OFFLINE
    last_seen: Optional[datetime] = None
    last_reading: Optional[NodeReading] = None
    
    # Config
    timeout_seconds: int = 120  # Mark offline after this
    
    def is_online(self) -> bool:
        if self.last_seen is None:
            return False
        age = datetime.now() - self.last_seen
        return age < timedelta(seconds=self.timeout_seconds)
    
    def update_seen(self):
        self.last_seen = datetime.now()
        self.status = NodeStatus.ONLINE


@dataclass
class ArduinoNodeManager:
    """
    Manages all Arduino/ESP32 nodes in the system.
    
    Example usage:
        manager = ArduinoNodeManager(mqtt_broker="192.168.1.100")
        
        # Register nodes
        manager.register_node("env_node_1", NodeType.ENVIRONMENT, "mqtt", "grok/sensors")
        manager.register_node("irrigation", NodeType.IRRIGATION, "serial", "/dev/ttyUSB0")
        manager.register_node("safety", NodeType.SAFETY, "serial", "/dev/ttyUSB1")
        
        # Start listening
        await manager.start()
        
        # Get latest readings
        env_data = manager.get_latest("env_node_1")
        
        # Send command to node
        await manager.send_command("irrigation", {"action": "irrigate", "duration_ms": 10000})
    """
    
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    
    # Internal state
    nodes: dict[str, Node] = field(default_factory=dict)
    _mqtt_client: Any = None
    _serial_connections: dict[str, Any] = field(default_factory=dict)
    _running: bool = False
    _callbacks: list[Callable[[NodeReading], None]] = field(default_factory=list)
    
    def register_node(
        self,
        node_id: str,
        node_type: NodeType,
        connection_type: str,
        address: str,
        timeout_seconds: int = 120
    ) -> Node:
        """Register a new node"""
        node = Node(
            node_id=node_id,
            node_type=node_type,
            connection_type=connection_type,
            address=address,
            timeout_seconds=timeout_seconds
        )
        self.nodes[node_id] = node
        logger.info(f"Registered node: {node_id} ({node_type.value}) via {connection_type}")
        return node
    
    def on_reading(self, callback: Callable[[NodeReading], None]):
        """Register callback for new readings"""
        self._callbacks.append(callback)
    
    async def start(self):
        """Start listening to all nodes"""
        self._running = True
        tasks = []
        
        # Start MQTT listener if any MQTT nodes
        mqtt_nodes = [n for n in self.nodes.values() if n.connection_type == "mqtt"]
        if mqtt_nodes and MQTT_AVAILABLE:
            tasks.append(self._mqtt_listener())
        
        # Start serial listeners
        serial_nodes = [n for n in self.nodes.values() if n.connection_type == "serial"]
        for node in serial_nodes:
            if SERIAL_AVAILABLE:
                tasks.append(self._serial_listener(node))
        
        # Health check task
        tasks.append(self._health_monitor())
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop all listeners"""
        self._running = False
        # Close connections
        for conn in self._serial_connections.values():
            conn.close()
        self._serial_connections.clear()
    
    async def _mqtt_listener(self):
        """Listen for MQTT messages from ESP32 nodes"""
        if not MQTT_AVAILABLE:
            logger.warning("aiomqtt not installed, MQTT nodes will not work")
            return
        
        try:
            async with aiomqtt.Client(self.mqtt_broker, self.mqtt_port) as client:
                self._mqtt_client = client
                
                # Subscribe to all registered node topics
                await client.subscribe("grok/#")
                logger.info(f"MQTT connected to {self.mqtt_broker}")
                
                async for message in client.messages:
                    if not self._running:
                        break
                    await self._handle_mqtt_message(message)
                    
        except Exception as e:
            logger.error(f"MQTT error: {e}")
    
    async def _handle_mqtt_message(self, message):
        """Process incoming MQTT message"""
        topic = str(message.topic)
        
        try:
            payload = json.loads(message.payload.decode())
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON on {topic}")
            return
        
        # Find matching node by topic
        node = self._find_node_by_topic(topic)
        if not node:
            return
        
        # Create reading
        reading = NodeReading(
            node_id=node.node_id,
            node_type=node.node_type,
            timestamp=datetime.now(),
            data=payload
        )
        
        # Update node state
        node.update_seen()
        node.last_reading = reading
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(reading)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def _find_node_by_topic(self, topic: str) -> Optional[Node]:
        """Find node matching MQTT topic"""
        for node in self.nodes.values():
            if node.connection_type == "mqtt" and topic.startswith(node.address):
                return node
        return None
    
    async def _serial_listener(self, node: Node):
        """Listen for serial messages from Arduino nodes"""
        if not SERIAL_AVAILABLE:
            logger.warning("serial_asyncio not installed, serial nodes will not work")
            return
        
        try:
            reader, writer = await serial_asyncio.open_serial_connection(
                url=node.address,
                baudrate=115200
            )
            self._serial_connections[node.node_id] = writer
            logger.info(f"Serial connected to {node.address} for {node.node_id}")
            
            while self._running:
                line = await reader.readline()
                if line:
                    await self._handle_serial_message(node, line.decode().strip())
                    
        except Exception as e:
            logger.error(f"Serial error for {node.node_id}: {e}")
            node.status = NodeStatus.ERROR
    
    async def _handle_serial_message(self, node: Node, message: str):
        """Process incoming serial message"""
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            # Not JSON, might be a log message
            logger.debug(f"[{node.node_id}] {message}")
            return
        
        # Create reading
        reading = NodeReading(
            node_id=node.node_id,
            node_type=node.node_type,
            timestamp=datetime.now(),
            data=payload
        )
        
        # Update node state
        node.update_seen()
        node.last_reading = reading
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(reading)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def _health_monitor(self):
        """Monitor node health and update status"""
        while self._running:
            for node in self.nodes.values():
                was_online = node.status == NodeStatus.ONLINE
                is_online = node.is_online()
                
                if was_online and not is_online:
                    node.status = NodeStatus.OFFLINE
                    logger.warning(f"Node {node.node_id} went OFFLINE")
                elif not was_online and is_online:
                    logger.info(f"Node {node.node_id} came ONLINE")
            
            await asyncio.sleep(10)
    
    def get_latest(self, node_id: str) -> Optional[dict]:
        """Get latest reading from a node"""
        node = self.nodes.get(node_id)
        if node and node.last_reading:
            return node.last_reading.data
        return None
    
    def get_all_readings(self) -> dict[str, dict]:
        """Get latest readings from all nodes"""
        readings = {}
        for node_id, node in self.nodes.items():
            if node.last_reading:
                readings[node_id] = {
                    "data": node.last_reading.data,
                    "timestamp": node.last_reading.timestamp.isoformat(),
                    "status": node.status.value
                }
        return readings
    
    async def send_command(self, node_id: str, command: dict) -> bool:
        """Send command to a node"""
        node = self.nodes.get(node_id)
        if not node:
            logger.error(f"Unknown node: {node_id}")
            return False
        
        message = json.dumps(command)
        
        if node.connection_type == "mqtt":
            return await self._send_mqtt_command(node, message)
        elif node.connection_type == "serial":
            return await self._send_serial_command(node, message)
        
        return False
    
    async def _send_mqtt_command(self, node: Node, message: str) -> bool:
        """Send command via MQTT"""
        if not self._mqtt_client:
            logger.error("MQTT not connected")
            return False
        
        topic = f"{node.address}/commands"
        try:
            await self._mqtt_client.publish(topic, message)
            logger.debug(f"Sent MQTT command to {topic}: {message}")
            return True
        except Exception as e:
            logger.error(f"MQTT send error: {e}")
            return False
    
    async def _send_serial_command(self, node: Node, message: str) -> bool:
        """Send command via serial"""
        writer = self._serial_connections.get(node.node_id)
        if not writer:
            logger.error(f"Serial not connected for {node.node_id}")
            return False
        
        try:
            writer.write(f"{message}\n".encode())
            await writer.drain()
            logger.debug(f"Sent serial command to {node.node_id}: {message}")
            return True
        except Exception as e:
            logger.error(f"Serial send error: {e}")
            return False
    
    def get_status_summary(self) -> dict:
        """Get status summary of all nodes"""
        return {
            "nodes": {
                node_id: {
                    "type": node.node_type.value,
                    "status": node.status.value,
                    "last_seen": node.last_seen.isoformat() if node.last_seen else None,
                    "connection": node.connection_type
                }
                for node_id, node in self.nodes.items()
            },
            "online_count": sum(1 for n in self.nodes.values() if n.is_online()),
            "total_count": len(self.nodes)
        }


# =============================================================================
# Integration with existing MCP Tools
# =============================================================================

class ArduinoEnhancedToolHandlers:
    """
    Enhanced tool handlers that use Arduino/ESP32 nodes.
    
    Extends the base ToolHandlers to source data from distributed nodes
    instead of (or in addition to) Pi-connected sensors.
    """
    
    def __init__(self, node_manager: ArduinoNodeManager):
        self.nodes = node_manager
    
    async def get_environment(self) -> dict:
        """Get environment data from ESP32 sensor node"""
        # Try to get from ESP32 node first
        esp_data = self.nodes.get_latest("env_node_1")
        
        if esp_data:
            return {
                "success": True,
                "source": "esp32_node",
                "data": esp_data
            }
        
        # Fall back to Pi sensors
        return {
            "success": False,
            "source": "none",
            "error": "No sensor data available"
        }
    
    async def trigger_irrigation(self, duration_seconds: int, zone: str = "main") -> dict:
        """Send irrigation command to Arduino controller"""
        command = {
            "action": "irrigate",
            "duration_ms": duration_seconds * 1000,
            "zone": zone
        }
        
        success = await self.nodes.send_command("irrigation", command)
        
        return {
            "success": success,
            "command": command
        }
    
    async def set_light_intensity(self, intensity_percent: int) -> dict:
        """Send dimmer command to ESP32 LED controller"""
        command = {
            "intensity": intensity_percent
        }
        
        # Publish to MQTT topic that dimmer listens to
        if self.nodes._mqtt_client:
            await self.nodes._mqtt_client.publish(
                "grok/lights/intensity",
                str(intensity_percent)
            )
            return {"success": True, "intensity": intensity_percent}
        
        return {"success": False, "error": "MQTT not connected"}
    
    async def trigger_sunrise(self, target_intensity: int = 100) -> dict:
        """Start sunrise ramp on LED controller"""
        if self.nodes._mqtt_client:
            await self.nodes._mqtt_client.publish(
                "grok/lights/sunrise",
                str(target_intensity)
            )
            return {"success": True, "target": target_intensity}
        
        return {"success": False, "error": "MQTT not connected"}
    
    async def trigger_sunset(self) -> dict:
        """Start sunset ramp on LED controller"""
        if self.nodes._mqtt_client:
            await self.nodes._mqtt_client.publish("grok/lights/sunset", "0")
            return {"success": True}
        
        return {"success": False, "error": "MQTT not connected"}
    
    async def get_safety_status(self) -> dict:
        """Get status from Arduino safety failsafe"""
        safety_data = self.nodes.get_latest("safety")
        
        if safety_data:
            return {
                "success": True,
                "source": "arduino_failsafe",
                "data": safety_data
            }
        
        return {
            "success": False,
            "error": "Safety node not responding"
        }


# =============================================================================
# Example Usage
# =============================================================================

async def main():
    """Example of setting up and using Arduino nodes"""
    
    # Create manager
    manager = ArduinoNodeManager(mqtt_broker="192.168.1.100")
    
    # Register nodes
    manager.register_node(
        "env_node_1",
        NodeType.ENVIRONMENT,
        "mqtt",
        "grok/sensors/environment"
    )
    
    manager.register_node(
        "irrigation",
        NodeType.IRRIGATION,
        "serial",
        "/dev/ttyUSB0"  # or "COM3" on Windows
    )
    
    manager.register_node(
        "safety",
        NodeType.SAFETY,
        "serial",
        "/dev/ttyUSB1"
    )
    
    manager.register_node(
        "dimmer",
        NodeType.DIMMER,
        "mqtt",
        "grok/lights"
    )
    
    # Add callback for new readings
    def on_reading(reading: NodeReading):
        print(f"[{reading.node_id}] {reading.data}")
    
    manager.on_reading(on_reading)
    
    # Start listening
    print("Starting Arduino node manager...")
    await manager.start()


if __name__ == "__main__":
    asyncio.run(main())
