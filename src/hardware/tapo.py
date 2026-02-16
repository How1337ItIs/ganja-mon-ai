"""
Tapo Smart Plug Driver
======================

Control TP-Link Tapo smart plugs (P100, P105, P110, P115).
P110/P115 models include energy monitoring.

Requirements:
    pip install tapo

Configuration via environment variables:
    TAPO_USERNAME - TP-Link account email
    TAPO_PASSWORD - TP-Link account password

Device IPs via environment:
    TAPO_GROW_LIGHT_IP - IP address of grow light plug
    TAPO_HEAT_MAT_IP - IP address of heat mat plug
    TAPO_EXHAUST_FAN_IP - IP address of exhaust fan plug
    TAPO_CIRCULATION_FAN_IP - IP address of circulation fan plug
    TAPO_HUMIDIFIER_IP - IP address of humidifier plug
    TAPO_DEHUMIDIFIER_IP - IP address of dehumidifier plug

Usage:
    from src.hardware.tapo import TapoActuatorHub

    hub = TapoActuatorHub()
    await hub.connect()
    await hub.set_device("grow_light", True)
    energy = await hub.get_energy_usage("grow_light")
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .base import ActuatorHub, DeviceState

logger = logging.getLogger(__name__)


@dataclass
class TapoDeviceConfig:
    """Configuration for a single Tapo device"""
    name: str
    ip: str
    has_energy_monitoring: bool = True  # P110/P115 have this


@dataclass
class EnergyUsage:
    """Energy usage data from P110/P115"""
    current_power_w: float = 0.0      # Current power in watts
    today_energy_wh: float = 0.0      # Today's usage in watt-hours
    month_energy_wh: float = 0.0      # This month's usage
    today_runtime_min: int = 0        # Today's runtime in minutes


class TapoActuatorHub(ActuatorHub):
    """
    TP-Link Tapo smart plug actuator hub.

    Supports P100, P105, P110, P115, P300 devices.
    P110/P115 include energy monitoring for tracking grow light usage.
    """

    # Device name to environment variable mapping
    DEVICE_ENV_MAP = {
        "grow_light": "TAPO_GROW_LIGHT_IP",
        "heat_mat": "TAPO_HEAT_MAT_IP",
        "exhaust_fan": "TAPO_EXHAUST_FAN_IP",
        "circulation_fan": "TAPO_CIRCULATION_FAN_IP",
        "humidifier": "TAPO_HUMIDIFIER_IP",
        "dehumidifier": "TAPO_DEHUMIDIFIER_IP",
        "water_pump": "TAPO_WATER_PUMP_IP",
    }

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_ips: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize Tapo hub.

        Args:
            username: TP-Link account email (or TAPO_USERNAME env var)
            password: TP-Link account password (or TAPO_PASSWORD env var)
            device_ips: Optional dict mapping device names to IPs
        """
        self.username = username or os.environ.get("TAPO_USERNAME")
        self.password = password or os.environ.get("TAPO_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "Tapo credentials required. Set TAPO_USERNAME and TAPO_PASSWORD "
                "environment variables or pass username/password to constructor."
            )

        # Load device IPs from env or provided dict
        self.device_configs: Dict[str, TapoDeviceConfig] = {}
        device_ips = device_ips or {}

        for device_name, env_var in self.DEVICE_ENV_MAP.items():
            ip = device_ips.get(device_name) or os.environ.get(env_var)
            if ip:
                self.device_configs[device_name] = TapoDeviceConfig(
                    name=device_name,
                    ip=ip,
                    has_energy_monitoring=True,  # Assume P110/P115
                )
                logger.info(f"Tapo device configured: {device_name} @ {ip}")

        # Connected device clients
        self._clients: Dict[str, Any] = {}
        self._api_client = None
        self._state = DeviceState()
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> bool:
        """Connect to all configured Tapo devices"""
        try:
            from tapo import ApiClient
        except ImportError:
            raise ImportError(
                "tapo library not installed. Run: pip install tapo"
            )

        logger.info("Connecting to Tapo devices...")
        self._api_client = ApiClient(self.username, self.password)

        for device_name, config in self.device_configs.items():
            try:
                # Connect to device (P115 uses same API as P110)
                device = await self._api_client.p110(config.ip)
                self._clients[device_name] = device

                # Get initial state
                device_info = await device.get_device_info()
                is_on = device_info.device_on

                # Update state
                setattr(self._state, device_name, is_on)

                logger.info(f"Connected to {device_name} @ {config.ip} (on={is_on})")

            except Exception as e:
                logger.error(f"Failed to connect to {device_name} @ {config.ip}: {e}")

        self._connected = len(self._clients) > 0

        # SAFETY: Ensure water pump is OFF on startup
        if self._connected and "water_pump" in self._clients:
            try:
                await self.set_device("water_pump", False)
                logger.info("Safety: water_pump set to OFF on startup")
            except Exception as e:
                logger.error(f"Failed to ensure pump off on startup: {e}")

        return self._connected

    async def get_state(self) -> DeviceState:
        """Get current state of all devices"""
        async with self._lock:
            self._state.timestamp = datetime.utcnow()

            # Refresh state from devices
            for device_name, client in self._clients.items():
                try:
                    info = await client.get_device_info()
                    setattr(self._state, device_name, info.device_on)
                except Exception as e:
                    logger.warning(f"Failed to get state for {device_name}: {e}")

            return self._state

    async def _reconnect_device(self, device_name: str) -> bool:
        """Reconnect a single Tapo device (stale connection recovery)."""
        if device_name not in self.device_configs:
            return False

        config = self.device_configs[device_name]
        try:
            from tapo import ApiClient
            # Create a fresh API client each time to avoid stale auth
            api = ApiClient(self.username, self.password)
            device = await api.p110(config.ip)
            self._clients[device_name] = device
            logger.info(f"Tapo: reconnected {device_name} @ {config.ip}")
            return True
        except Exception as e:
            logger.error(f"Tapo: reconnect failed for {device_name} @ {config.ip}: {e}")
            return False

    async def set_device(self, device: str, state: bool) -> bool:
        """Set a device on/off with auto-reconnect on stale connection."""
        async with self._lock:
            if device not in self._clients:
                if device in self.device_configs:
                    logger.warning(f"Device {device} configured but not connected — attempting reconnect")
                    # Try to reconnect the device
                    if not await self._reconnect_device(device):
                        return False
                else:
                    logger.warning(f"Device {device} not configured")
                    return False

            # Try up to 2 times: first attempt, then reconnect + retry
            for attempt in range(2):
                try:
                    client = self._clients[device]

                    if state:
                        await client.on()
                    else:
                        await client.off()

                    # Update local state
                    setattr(self._state, device, state)
                    logger.info(f"Tapo: {device} -> {'ON' if state else 'OFF'}")
                    return True

                except Exception as e:
                    if attempt == 0:
                        logger.warning(f"Tapo: {device} command failed ({e}), reconnecting...")
                        reconnected = await self._reconnect_device(device)
                        if not reconnected:
                            logger.error(f"Tapo: reconnect failed for {device}, giving up")
                            return False
                        # Loop will retry with the fresh client
                    else:
                        logger.error(f"Tapo: {device} command failed after reconnect: {e}")
                        return False

            return False

    async def water(self, amount_ml: int) -> bool:
        """
        Dispense water using pump.

        Calculates pump runtime based on flow rate.
        Default: 100ml/min = 1.67ml/sec
        SAFETY: Hard limit of 10 seconds max runtime to prevent flooding.
        """
        FLOW_RATE_ML_PER_SEC = float(os.environ.get("PUMP_FLOW_RATE_ML_SEC", "1.67"))
        MAX_PUMP_RUNTIME_SEC = 10  # SAFETY: Hard limit - pump is powerful!

        duration_sec = amount_ml / FLOW_RATE_ML_PER_SEC

        # SAFETY: Enforce max runtime
        if duration_sec > MAX_PUMP_RUNTIME_SEC:
            logger.warning(f"Pump duration {duration_sec:.1f}s exceeds max {MAX_PUMP_RUNTIME_SEC}s - clamping")
            duration_sec = MAX_PUMP_RUNTIME_SEC

        if "water_pump" not in self._clients:
            logger.warning("Water pump not configured")
            return False

        try:
            # Turn on pump
            await self.set_device("water_pump", True)

            # Wait for calculated duration
            await asyncio.sleep(duration_sec)

            # Turn off pump
            await self.set_device("water_pump", False)

            logger.info(f"Watered {amount_ml}ml ({duration_sec:.1f}s)")
            return True

        except Exception as e:
            # Ensure pump is off on error
            await self.set_device("water_pump", False)
            logger.error(f"Watering failed: {e}")
            return False

    async def inject_co2(self, duration_seconds: int = 60) -> bool:
        """CO2 injection not supported via Tapo (requires relay/solenoid)"""
        logger.warning("CO2 injection not supported via Tapo plugs")
        return False

    async def is_connected(self) -> bool:
        """Check if any devices are connected"""
        return self._connected and len(self._clients) > 0

    async def get_energy_usage(self, device: str) -> Optional[EnergyUsage]:
        """
        Get energy usage for a device (P110/P115 only).

        Returns:
            EnergyUsage dataclass or None if not supported
        """
        if device not in self._clients:
            return None

        config = self.device_configs.get(device)
        if not config or not config.has_energy_monitoring:
            return None

        try:
            client = self._clients[device]
            usage = await client.get_energy_usage()

            # Handle both old and new tapo library attribute names
            current_power = getattr(usage, 'current_power', None)
            if current_power is None:
                current_power = getattr(usage, 'current_power_w', 0) * 1000  # W to mW

            return EnergyUsage(
                current_power_w=current_power / 1000,  # mW to W
                today_energy_wh=getattr(usage, 'today_energy', 0),
                month_energy_wh=getattr(usage, 'month_energy', 0),
                today_runtime_min=getattr(usage, 'today_runtime', 0),
            )
        except Exception as e:
            logger.warning(f"Failed to get energy usage for {device}: {e}")
            return None

    async def get_all_energy_usage(self) -> Dict[str, EnergyUsage]:
        """Get energy usage for all devices that support it"""
        results = {}
        for device_name in self._clients:
            usage = await self.get_energy_usage(device_name)
            if usage:
                results[device_name] = usage
        return results

    async def disconnect(self):
        """Disconnect from all devices"""
        self._clients.clear()
        self._connected = False
        logger.info("Disconnected from all Tapo devices")


# =============================================================================
# Factory function
# =============================================================================

def create_tapo_hub(
    grow_light_ip: Optional[str] = None,
    **extra_devices
) -> TapoActuatorHub:
    """
    Create a TapoActuatorHub with minimal configuration.

    Args:
        grow_light_ip: IP address of the grow light plug
        **extra_devices: Additional device_name=ip pairs

    Example:
        hub = create_tapo_hub(
            grow_light_ip="192.168.1.100",
            exhaust_fan="192.168.1.101",
        )
    """
    device_ips = {}

    if grow_light_ip:
        device_ips["grow_light"] = grow_light_ip

    device_ips.update(extra_devices)

    return TapoActuatorHub(device_ips=device_ips)
