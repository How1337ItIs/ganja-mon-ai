"""
Kasa Smart Plug Integration
===========================

Real hardware implementation using TP-Link Kasa smart plugs.
Uses python-kasa library for local network control (no cloud required).

Install: pip install python-kasa

Compatible devices:
- HS103, HS105, HS110 (original, work best with local control)
- EP10, EP25, KP125 (newer models, may need Kasa app setup first)
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List
import logging
import os

try:
    from kasa import SmartPlug, Discover
    KASA_AVAILABLE = True
except ImportError:
    KASA_AVAILABLE = False
    SmartPlug = None
    Discover = None

from .base import ActuatorHub, DeviceState

logger = logging.getLogger(__name__)

# Timeout for network operations to prevent stalls
KASA_TIMEOUT_SECONDS = 10


@dataclass
class KasaDeviceConfig:
    """Configuration for a single Kasa device"""
    name: str           # Internal name (grow_light, exhaust_fan, etc.)
    ip: str             # Static IP address
    alias: str = ""     # Friendly name shown in Kasa app
    plug: Optional['SmartPlug'] = None  # Connected plug instance


class KasaActuatorHub(ActuatorHub):
    """
    Kasa smart plug controller for grow automation.

    Example usage:
        hub = KasaActuatorHub({
            "grow_light": "192.168.1.100",
            "exhaust_fan": "192.168.1.101",
            "circulation_fan": "192.168.1.102",
            "air_pump": "192.168.1.103",
        })
        await hub.connect()
        await hub.set_device("grow_light", True)
    """

    def __init__(self, device_ips: Dict[str, str]):
        """
        Initialize with device IP mapping.

        Args:
            device_ips: Dict mapping device names to IP addresses
                       e.g., {"grow_light": "192.168.1.100"}
        """
        if not KASA_AVAILABLE:
            raise ImportError("python-kasa not installed. Run: pip install python-kasa")

        self.devices: Dict[str, KasaDeviceConfig] = {}
        for name, ip in device_ips.items():
            self.devices[name] = KasaDeviceConfig(name=name, ip=ip)

        self._connected = False
        self._state = DeviceState()

    def _co2_solenoid_enabled(self) -> bool:
        # CO2 hardware is optional; when it's not physically hooked up, forcing
        # it OFF prevents confusing state and accidental activation.
        return os.getenv("ENABLE_CO2_SOLENOID", "true").strip().lower() == "true"

    async def connect(self) -> bool:
        """Connect to all configured Kasa devices"""
        success_count = 0

        for name, config in self.devices.items():
            try:
                plug = SmartPlug(config.ip)
                # Timeout to prevent hanging on unresponsive devices
                await asyncio.wait_for(plug.update(), timeout=KASA_TIMEOUT_SECONDS)
                config.plug = plug
                config.alias = plug.alias
                logger.info(f"Connected to {name} ({config.alias}) at {config.ip}")
                success_count += 1
            except asyncio.TimeoutError:
                logger.error(f"Timeout connecting to {name} at {config.ip} (>{KASA_TIMEOUT_SECONDS}s)")
                config.plug = None
            except Exception as e:
                logger.error(f"Failed to connect to {name} at {config.ip}: {e}")
                config.plug = None

        self._connected = success_count > 0

        # SAFETY: Ensure water pump is OFF on startup
        if self._connected and "water_pump" in self.devices:
            try:
                await self.set_device("water_pump", False)
                logger.info("Safety: water_pump set to OFF on startup")
            except Exception as e:
                logger.error(f"Failed to ensure pump off on startup: {e}")

        # SAFETY: If CO2 isn't enabled, force solenoid OFF on startup.
        if self._connected and "co2_solenoid" in self.devices and not self._co2_solenoid_enabled():
            try:
                await self.set_device("co2_solenoid", False)
                logger.info("Safety: co2_solenoid forced OFF (ENABLE_CO2_SOLENOID=false)")
            except Exception as e:
                logger.error(f"Failed to ensure CO2 solenoid off on startup: {e}")

        return self._connected

    async def discover_devices(self) -> List[Dict]:
        """Discover all Kasa devices on the network"""
        devices = await Discover.discover()
        result = []
        for ip, dev in devices.items():
            await dev.update()
            result.append({
                "ip": ip,
                "alias": dev.alias,
                "model": dev.model,
                "is_on": dev.is_on,
            })
        return result

    async def get_state(self) -> DeviceState:
        """Get current state of all connected devices"""
        state = DeviceState(timestamp=datetime.utcnow())

        for name, config in self.devices.items():
            if config.plug:
                try:
                    # Timeout to prevent hanging on unresponsive devices
                    await asyncio.wait_for(config.plug.update(), timeout=KASA_TIMEOUT_SECONDS)
                    is_on = config.plug.is_on

                    # Map to DeviceState fields
                    if hasattr(state, name):
                        setattr(state, name, is_on)
                except asyncio.TimeoutError:
                    logger.error(f"Timeout reading {name} (>{KASA_TIMEOUT_SECONDS}s) - device may be offline")
                except Exception as e:
                    logger.error(f"Error reading {name}: {e}")

        self._state = state
        return state

    async def set_device(self, device: str, state: bool) -> bool:
        """
        Turn a device on or off.

        Args:
            device: Device name (must match config key)
            state: True for on, False for off

        Returns:
            True if successful
        """
        if device not in self.devices:
            logger.error(f"Unknown device: {device}")
            return False

        # Hard safety gate: never allow CO2 to be turned ON if it's disabled.
        if device == "co2_solenoid" and state and not self._co2_solenoid_enabled():
            logger.warning("Refusing to turn ON co2_solenoid (ENABLE_CO2_SOLENOID=false)")
            try:
                # Best-effort: force it off in case some other process toggled it.
                cfg = self.devices.get(device)
                if cfg and cfg.plug:
                    await asyncio.wait_for(cfg.plug.turn_off(), timeout=KASA_TIMEOUT_SECONDS)
            except Exception:
                pass
            if hasattr(self._state, device):
                setattr(self._state, device, False)
            return False

        config = self.devices[device]
        if not config.plug:
            logger.error(f"Device {device} not connected")
            return False

        try:
            # Timeout to prevent hanging on unresponsive devices
            if state:
                await asyncio.wait_for(config.plug.turn_on(), timeout=KASA_TIMEOUT_SECONDS)
                logger.info(f"Turned ON: {device}")
            else:
                await asyncio.wait_for(config.plug.turn_off(), timeout=KASA_TIMEOUT_SECONDS)
                logger.info(f"Turned OFF: {device}")

            # Update internal state
            if hasattr(self._state, device):
                setattr(self._state, device, state)

            return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout setting {device} to {state} (>{KASA_TIMEOUT_SECONDS}s)")
            return False
        except Exception as e:
            logger.error(f"Error setting {device} to {state}: {e}")
            return False

    async def water(self, amount_ml: int) -> bool:
        """
        Run water pump for calculated duration.

        CALIBRATED Jan 26, 2026 with measuring cup:
        - 5 seconds = ~160ml (2/3 cup)
        - Flow rate: ~32 ml/sec at high pump power setting

        Previous 9ml/sec calibration was wrong and caused flooding!
        """
        PUMP_RATE_ML_PER_SEC = 32.0   # CALIBRATED Jan 26: ~160ml in 5sec (2/3 cup)
        MAX_PUMP_RUNTIME_SEC = 5      # SAFETY: Max 5 seconds = ~160ml

        if "water_pump" not in self.devices:
            logger.error("No water_pump configured")
            return False

        # HARD LIMIT: Never request more than 150ml at a time
        if amount_ml > 150:
            logger.warning(f"Requested {amount_ml}ml exceeds hard limit 150ml - clamping")
            amount_ml = 150

        duration = amount_ml / PUMP_RATE_ML_PER_SEC

        # SAFETY: Enforce max runtime - ABSOLUTE HARD CAP
        if duration > MAX_PUMP_RUNTIME_SEC:
            logger.warning(f"Pump duration {duration:.1f}s exceeds max {MAX_PUMP_RUNTIME_SEC}s - clamping")
            duration = MAX_PUMP_RUNTIME_SEC

        logger.info(f"PUMP: Requesting {amount_ml}ml -> {duration:.1f}s runtime (max {MAX_PUMP_RUNTIME_SEC}s)")

        try:
            await self.set_device("water_pump", True)
            await asyncio.sleep(duration)
            await self.set_device("water_pump", False)
            logger.info(f"Dispensed ~{amount_ml}ml in {duration:.1f}s")
            return True
        except Exception as e:
            # Safety: ensure pump is off
            await self.set_device("water_pump", False)
            logger.error(f"Water error: {e}")
            return False

    async def inject_co2(self, duration_seconds: int = 60) -> bool:
        """Inject CO2 by opening solenoid for duration"""
        if "co2_solenoid" not in self.devices:
            logger.error("No co2_solenoid configured")
            return False

        if not self._co2_solenoid_enabled():
            logger.warning("CO2 injection requested but ENABLE_CO2_SOLENOID=false; refusing")
            try:
                await self.set_device("co2_solenoid", False)
            except Exception:
                pass
            return False

        try:
            await self.set_device("co2_solenoid", True)
            await asyncio.sleep(duration_seconds)
            await self.set_device("co2_solenoid", False)
            logger.info(f"CO2 injected for {duration_seconds}s")
            return True
        except Exception as e:
            await self.set_device("co2_solenoid", False)
            logger.error(f"CO2 error: {e}")
            return False

    async def is_connected(self) -> bool:
        """Check if any devices are connected"""
        return self._connected and any(
            config.plug is not None for config in self.devices.values()
        )

    async def disconnect(self):
        """Cleanup connections"""
        self._connected = False
        for config in self.devices.values():
            config.plug = None


# =============================================================================
# Convenience functions for quick testing
# =============================================================================

async def discover_kasa_devices() -> list:
    """
    Quick discovery of all Kasa devices on network.

    Returns list of dicts with device info.
    Tapo devices (P115, etc.) that need auth will be listed but not fully accessible.
    """
    if not KASA_AVAILABLE:
        print("ERROR: python-kasa not installed. Run: pip install python-kasa")
        return []

    print("Discovering Kasa devices...")

    try:
        devices = await Discover.discover()
    except Exception as e:
        print(f"Discovery error: {e}")
        return []

    if not devices:
        print("No devices found. Make sure you're on the same network.")
        return []

    print(f"\nFound {len(devices)} device(s):\n")
    result = []

    for ip, dev in devices.items():
        try:
            await dev.update()
            info = {
                'ip': ip,
                'alias': dev.alias,
                'model': dev.model,
                'is_on': dev.is_on,
                'needs_auth': False,
            }
            print(f"  {dev.alias}")
            print(f"    IP: {ip}")
            print(f"    Model: {dev.model}")
            print(f"    State: {'ON' if dev.is_on else 'OFF'}")
            print()
            result.append(info)
        except Exception as e:
            # Tapo devices and newer models need authentication
            err_str = str(e).lower()
            if 'challenge' in err_str or 'auth' in err_str or 'credential' in err_str:
                info = {
                    'ip': ip,
                    'alias': f'[Tapo/Auth Required @ {ip}]',
                    'model': 'Unknown (needs auth)',
                    'is_on': None,
                    'needs_auth': True,
                }
                print(f"  [Auth Required]")
                print(f"    IP: {ip}")
                print(f"    (Tapo device - set TAPO_USERNAME/TAPO_PASSWORD in .env)")
                print()
                result.append(info)
            else:
                print(f"  [Error @ {ip}]: {e}")
                print()

    return result


async def test_plug(ip: str):
    """Quick test of a single plug"""
    if not KASA_AVAILABLE:
        print("ERROR: python-kasa not installed")
        return

    plug = SmartPlug(ip)
    await plug.update()

    print(f"Connected to: {plug.alias}")
    print(f"Current state: {'ON' if plug.is_on else 'OFF'}")

    # Toggle test
    print("\nToggling plug...")
    if plug.is_on:
        await plug.turn_off()
        print("Turned OFF")
    else:
        await plug.turn_on()
        print("Turned ON")

    await asyncio.sleep(2)

    # Toggle back
    if plug.is_on:
        await plug.turn_off()
        print("Turned OFF")
    else:
        await plug.turn_on()
        print("Turned ON")

    print("\nTest complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Test specific IP
        asyncio.run(test_plug(sys.argv[1]))
    else:
        # Discover all devices
        asyncio.run(discover_kasa_devices())
