"""
Safety Guardian
===============

Hardware-level safety enforcement for cannabis cultivation.
These rules CANNOT be overridden by AI - they protect the plant.

Critical Protections:
1. Dark Period Lock - NO lights during flowering dark period (hermaphrodite prevention)
2. Emergency Kill Switch - Instant shutdown of all devices
3. Water Limits - Prevent overwatering (root rot prevention)
4. Temperature Bounds - Emergency cooling/heating triggers
5. CO2 Safety - Prevent dangerous CO2 levels
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import asyncio

# Current growth stage (set by orchestrator)
_current_growth_stage: str = "veg"

def set_growth_stage(stage: str) -> None:
    """Set current growth stage for stage-aware safety limits"""
    global _current_growth_stage
    _current_growth_stage = stage.lower()

def get_growth_stage() -> str:
    """Get current growth stage"""
    return _current_growth_stage


def safe_print(msg: str):
    """Print with Windows-safe encoding"""
    try:
        print(msg)
    except UnicodeEncodeError:
        ascii_msg = msg.encode('ascii', 'replace').decode('ascii')
        print(ascii_msg)


class SafetyViolation(Exception):
    """Raised when AI attempts a forbidden action"""
    pass


class ViolationType(str, Enum):
    DARK_PERIOD_LIGHT = "dark_period_light"
    OVERWATER = "overwater"
    TEMP_CRITICAL = "temp_critical"
    CO2_DANGEROUS = "co2_dangerous"
    KILL_SWITCH = "kill_switch"


@dataclass
class SafetyLimits:
    """
    Configurable safety limits.
    These are HARD limits that the AI cannot exceed.

    WATER LIMITS UNIFIED WITH WateringSafeguard:
    - clone: 500ml/day (target 300ml + 200ml buffer)
    - seedling: 300ml/day
    - veg: 1500ml/day
    - flower: 1500ml/day
    - late_flower: 1000ml/day
    """
    # Water limits - stage-specific daily limits
    max_water_per_event_ml: int = 50           # Max single watering (conservative for young plant)
    min_water_interval_minutes: int = 240      # Min 4 hours between waterings

    # Stage-specific daily water limits (unified with WateringSafeguard)
    water_daily_limits: Dict[str, int] = field(default_factory=lambda: {
        "clone": 500,
        "seedling": 200,
        "early_veg": 200,
        "veg": 400,
        "vegetative": 400,
        "flower": 800,
        "flowering": 800,
        "late_flower": 600,
    })

    # Default fallback if stage not recognized
    max_water_per_day_ml: int = 300            # Fallback daily limit

    # Temperature limits (Celsius)
    temp_critical_low: float = 10.0            # Emergency heat on
    temp_critical_high: float = 35.0           # Emergency exhaust on
    temp_warning_low: float = 18.0
    temp_warning_high: float = 30.0

    # Humidity limits
    humidity_critical_high: float = 80.0       # Mold risk
    humidity_warning_high: float = 70.0

    # CO2 limits (ppm)
    co2_max_safe: int = 1200                   # Warning threshold
    co2_dangerous: int = 1800                  # Alert threshold (human comfort)

    # VPD limits (kPa)
    vpd_critical_low: float = 0.2              # Edema risk
    vpd_critical_high: float = 1.8             # Stress risk

    # Photoperiod (for dark period enforcement)
    light_on_hour: int = 6                     # 6 AM
    light_off_hour: int = 18                   # 6 PM (12/12 for flowering)


@dataclass
class DarkPeriodConfig:
    """
    Dark period configuration for flowering cannabis.

    CRITICAL: Light leaks during dark period can cause:
    - Hermaphroditism (plant grows male flowers)
    - Reversion to vegetative growth
    - Severely reduced yields

    This is the MOST important safety feature.
    """
    enabled: bool = True
    hours_dark: int = 12
    dark_start: time = field(default_factory=lambda: time(18, 0))  # 6 PM
    dark_end: time = field(default_factory=lambda: time(6, 0))     # 6 AM

    # Grace period at transitions (equipment cooldown)
    transition_grace_minutes: int = 5

    def is_dark_period(self, current_time: Optional[datetime] = None) -> bool:
        """Check if we're currently in dark period"""
        if not self.enabled:
            return False

        now = current_time or datetime.now()
        current = now.time()

        # Handle overnight dark period (e.g., 6 PM to 6 AM)
        if self.dark_start > self.dark_end:
            # Dark period spans midnight
            return current >= self.dark_start or current < self.dark_end
        else:
            # Dark period within same day
            return self.dark_start <= current < self.dark_end

    def time_until_light(self, current_time: Optional[datetime] = None) -> timedelta:
        """Get time remaining until lights can come on"""
        now = current_time or datetime.now()

        if not self.is_dark_period(now):
            return timedelta(0)

        # Calculate time until dark_end
        today_end = datetime.combine(now.date(), self.dark_end)

        if now.time() >= self.dark_start:
            # Dark period started today, ends tomorrow
            tomorrow_end = today_end + timedelta(days=1)
            return tomorrow_end - now
        else:
            # Dark period started yesterday, ends today
            return today_end - now


@dataclass
class SafetyState:
    """Current safety system state"""
    kill_switch_active: bool = False
    kill_switch_reason: Optional[str] = None
    kill_switch_time: Optional[datetime] = None

    last_water_time: Optional[datetime] = None
    water_today_ml: int = 0
    water_today_date: Optional[datetime] = None

    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)


class SafetyGuardian:
    """
    Hardware-level safety enforcement.

    This guardian sits between the AI and actuators.
    ALL commands pass through here and can be BLOCKED.

    The AI cannot disable or bypass these protections.
    """

    def __init__(
        self,
        limits: Optional[SafetyLimits] = None,
        dark_config: Optional[DarkPeriodConfig] = None,
    ):
        self.limits = limits or SafetyLimits()
        self.dark_config = dark_config or DarkPeriodConfig()
        self.state = SafetyState()

        # Callbacks for emergency actions
        self._emergency_callbacks: List[Callable] = []

    # =========================================================================
    # Dark Period Protection (MOST CRITICAL)
    # =========================================================================

    def can_turn_on_light(self, current_time: Optional[datetime] = None) -> tuple[bool, str]:
        """
        Check if lights can be turned on.

        Returns:
            (allowed, reason)
        """
        if self.state.kill_switch_active:
            return False, f"Kill switch active: {self.state.kill_switch_reason}"

        if self.dark_config.is_dark_period(current_time):
            time_left = self.dark_config.time_until_light(current_time)
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            return False, f"DARK PERIOD - Light forbidden for {hours}h {minutes}m. Turning on light would cause hermaphroditism."

        return True, "Light allowed"

    def enforce_light_command(self, turn_on: bool, current_time: Optional[datetime] = None) -> bool:
        """
        Enforce light command through safety layer.

        Args:
            turn_on: Whether AI wants to turn light on
            current_time: Optional override for testing

        Returns:
            True if command is allowed

        Raises:
            SafetyViolation if command is forbidden
        """
        if not turn_on:
            # Turning off is always allowed
            return True

        allowed, reason = self.can_turn_on_light(current_time)

        if not allowed:
            self._log_violation(ViolationType.DARK_PERIOD_LIGHT, reason)
            raise SafetyViolation(reason)

        return True

    # =========================================================================
    # Water Protection
    # =========================================================================

    def can_water(self, amount_ml: int, current_time: Optional[datetime] = None) -> tuple[bool, str]:
        """Check if watering is allowed"""
        now = current_time or datetime.now()

        if self.state.kill_switch_active:
            return False, f"Kill switch active: {self.state.kill_switch_reason}"

        # Check single event limit
        if amount_ml > self.limits.max_water_per_event_ml:
            return False, f"Amount {amount_ml}ml exceeds max single watering of {self.limits.max_water_per_event_ml}ml"

        # Reset daily counter if new day
        if self.state.water_today_date is None or self.state.water_today_date.date() != now.date():
            self.state.water_today_ml = 0
            self.state.water_today_date = now

        # Check daily limit (stage-specific)
        stage = get_growth_stage()
        daily_limit = self.limits.max_water_per_day_ml  # Default fallback
        for key, val in self.limits.water_daily_limits.items():
            if key in stage:
                daily_limit = val
                break

        if self.state.water_today_ml + amount_ml > daily_limit:
            remaining = daily_limit - self.state.water_today_ml
            return False, f"Would exceed daily limit ({stage}). Today: {self.state.water_today_ml}ml, Limit: {daily_limit}ml, Remaining: {remaining}ml"

        # Check minimum interval
        if self.state.last_water_time:
            elapsed = now - self.state.last_water_time
            min_interval = timedelta(minutes=self.limits.min_water_interval_minutes)
            if elapsed < min_interval:
                wait = min_interval - elapsed
                return False, f"Too soon since last watering. Wait {wait.seconds // 60} minutes."

        return True, "Watering allowed"

    def enforce_water_command(self, amount_ml: int, current_time: Optional[datetime] = None) -> bool:
        """Enforce water command through safety layer"""
        now = current_time or datetime.now()

        allowed, reason = self.can_water(amount_ml, now)

        if not allowed:
            self._log_violation(ViolationType.OVERWATER, reason)
            raise SafetyViolation(reason)

        # Update tracking
        self.state.last_water_time = now
        self.state.water_today_ml += amount_ml

        return True

    # =========================================================================
    # Environmental Protection
    # =========================================================================

    def check_environment(
        self,
        temp: float,
        humidity: float,
        co2: float,
        vpd: float
    ) -> Dict[str, Any]:
        """
        Check environmental readings for safety issues.

        Returns dict with:
            - ok: bool - Whether environment is safe
            - critical: list - Critical issues requiring immediate action
            - warnings: list - Issues to monitor
            - actions: list - Recommended automatic actions
        """
        result = {
            "ok": True,
            "critical": [],
            "warnings": [],
            "actions": []
        }

        # Temperature checks
        if temp <= self.limits.temp_critical_low:
            result["ok"] = False
            result["critical"].append(f"CRITICAL: Temperature {temp}°C below {self.limits.temp_critical_low}°C")
            result["actions"].append({"device": "heat_mat", "state": True, "reason": "Emergency heating"})
        elif temp >= self.limits.temp_critical_high:
            result["ok"] = False
            result["critical"].append(f"CRITICAL: Temperature {temp}°C above {self.limits.temp_critical_high}°C")
            result["actions"].append({"device": "exhaust_fan", "state": True, "reason": "Emergency cooling"})
            result["actions"].append({"device": "grow_light", "state": False, "reason": "Reduce heat"})
        elif temp <= self.limits.temp_warning_low:
            result["warnings"].append(f"Warning: Temperature {temp}°C is low")
        elif temp >= self.limits.temp_warning_high:
            result["warnings"].append(f"Warning: Temperature {temp}°C is high")

        # Humidity checks
        if humidity >= self.limits.humidity_critical_high:
            result["ok"] = False
            result["critical"].append(f"CRITICAL: Humidity {humidity}% - high mold risk")
            result["actions"].append({"device": "exhaust_fan", "state": True, "reason": "Emergency dehumidify"})
            result["actions"].append({"device": "dehumidifier", "state": True, "reason": "Emergency dehumidify"})
        elif humidity >= self.limits.humidity_warning_high:
            result["warnings"].append(f"Warning: Humidity {humidity}% is elevated")

        # CO2 checks
        if co2 >= self.limits.co2_dangerous:
            result["ok"] = False
            result["critical"].append(f"CRITICAL: CO2 {co2}ppm is dangerous")
            result["actions"].append({"device": "exhaust_fan", "state": True, "reason": "Emergency ventilation"})
            result["actions"].append({"device": "co2_solenoid", "state": False, "reason": "Stop CO2 injection"})
        elif co2 >= self.limits.co2_max_safe:
            result["warnings"].append(f"Warning: CO2 {co2}ppm approaching limit")

        # VPD checks
        if vpd <= self.limits.vpd_critical_low:
            result["warnings"].append(f"Warning: VPD {vpd} kPa too low - edema risk")
        elif vpd >= self.limits.vpd_critical_high:
            result["warnings"].append(f"Warning: VPD {vpd} kPa too high - plant stress")

        return result

    # =========================================================================
    # Kill Switch
    # =========================================================================

    async def activate_kill_switch(self, reason: str) -> None:
        """
        Emergency shutdown of all devices.

        This should turn off everything except:
        - Circulation fan (prevent stagnant air)
        - Emergency systems
        """
        self.state.kill_switch_active = True
        self.state.kill_switch_reason = reason
        self.state.kill_switch_time = datetime.now()

        self._log_violation(ViolationType.KILL_SWITCH, reason)

        # Notify all emergency callbacks
        for callback in self._emergency_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason)
                else:
                    callback(reason)
            except Exception as e:
                safe_print(f"[ERR] Emergency callback failed: {e}")

    def deactivate_kill_switch(self, authorization: str) -> bool:
        """
        Deactivate kill switch.

        Requires explicit authorization string to prevent accidental reactivation.
        """
        if authorization != "CONFIRMED_SAFE_TO_RESUME":
            return False

        self.state.kill_switch_active = False
        self.state.kill_switch_reason = None
        self.state.kill_switch_time = None
        return True

    def register_emergency_callback(self, callback: Callable) -> None:
        """Register callback to be called on emergency"""
        self._emergency_callbacks.append(callback)

    # =========================================================================
    # Logging
    # =========================================================================

    def _log_violation(self, violation_type: ViolationType, message: str) -> None:
        """Log a safety violation"""
        violation = {
            "type": violation_type.value,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.state.violations.append(violation)

        # Keep last 100 violations
        if len(self.state.violations) > 100:
            self.state.violations = self.state.violations[-100:]

        safe_print(f"[WARN] SAFETY VIOLATION: [{violation_type.value}] {message}")

    def _log_warning(self, message: str) -> None:
        """Log a safety warning"""
        warning = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.state.warnings.append(warning)

        # Keep last 100 warnings
        if len(self.state.warnings) > 100:
            self.state.warnings = self.state.warnings[-100:]

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        now = datetime.now()
        daily_limit = self._get_stage_daily_limit()

        return {
            "kill_switch": {
                "active": self.state.kill_switch_active,
                "reason": self.state.kill_switch_reason,
                "since": self.state.kill_switch_time.isoformat() if self.state.kill_switch_time else None,
            },
            "dark_period": {
                "enabled": self.dark_config.enabled,
                "currently_dark": self.dark_config.is_dark_period(now),
                "dark_start": self.dark_config.dark_start.isoformat(),
                "dark_end": self.dark_config.dark_end.isoformat(),
                "time_until_light": str(self.dark_config.time_until_light(now)),
            },
            "water_today": {
                "total_ml": self.state.water_today_ml,
                "limit_ml": daily_limit,
                "remaining_ml": max(0, daily_limit - self.state.water_today_ml),
                "last_water": self.state.last_water_time.isoformat() if self.state.last_water_time else None,
            },
            "recent_violations": self.state.violations[-10:],
            "recent_warnings": self.state.warnings[-10:],
        }

    def _get_stage_daily_limit(self) -> int:
        """Get current stage-specific daily water limit."""
        stage = get_growth_stage()
        daily_limit = self.limits.max_water_per_day_ml
        for key, val in self.limits.water_daily_limits.items():
            if key in stage:
                daily_limit = val
                break
        return daily_limit


# =============================================================================
# Safe Actuator Wrapper
# =============================================================================

class SafeActuatorHub:
    """
    Wrapper around ActuatorHub that enforces safety rules.

    ALL actuator commands should go through this wrapper.
    Direct actuator access should be prevented in production.
    """

    def __init__(self, actuator_hub, guardian: SafetyGuardian):
        self._actuators = actuator_hub
        self._guardian = guardian
        self._lock = asyncio.Lock()  # Prevent race conditions

        # Register emergency handler
        guardian.register_emergency_callback(self._emergency_shutdown)

    async def _emergency_shutdown(self, reason: str) -> None:
        """Emergency shutdown handler"""
        safe_print(f"[!!!] EMERGENCY SHUTDOWN: {reason}")

        # Turn off dangerous devices
        await self._actuators.set_device("grow_light", False)
        await self._actuators.set_device("heat_mat", False)
        await self._actuators.set_device("water_pump", False)
        await self._actuators.set_device("co2_solenoid", False)
        await self._actuators.set_device("humidifier", False)

        # Keep circulation for air quality
        await self._actuators.set_device("circulation_fan", True)

    async def set_device(self, device: str, state: bool) -> bool:
        """Set device state with safety enforcement"""
        async with self._lock:
            # Special handling for grow light
            if device == "grow_light" and state:
                self._guardian.enforce_light_command(True)

            # Check kill switch
            if self._guardian.state.kill_switch_active:
                if device != "circulation_fan":  # Allow circulation fan during kill switch
                    raise SafetyViolation(f"Kill switch active: {self._guardian.state.kill_switch_reason}")

            return await self._actuators.set_device(device, state)

    async def set_grow_light(self, state: bool) -> bool:
        """Set grow light state (convenience method for photoperiod scheduler)"""
        return await self.set_device("grow_light", state)

    async def water(self, amount_ml: int) -> bool:
        """Water with safety enforcement"""
        async with self._lock:
            self._guardian.enforce_water_command(amount_ml)
            return await self._actuators.water(amount_ml)

    async def inject_co2(self, duration_seconds: int = 60) -> bool:
        """Inject CO2 with safety check"""
        async with self._lock:
            if self._guardian.state.kill_switch_active:
                raise SafetyViolation(f"Kill switch active: {self._guardian.state.kill_switch_reason}")

            # Limit max injection time
            max_duration = 120  # 2 minutes max
            if duration_seconds > max_duration:
                duration_seconds = max_duration

            return await self._actuators.inject_co2(duration_seconds)

    async def get_state(self):
        """Get device state"""
        return await self._actuators.get_state()

    async def is_connected(self) -> bool:
        """Check connection"""
        return await self._actuators.is_connected()

    # Convenience methods
    async def light_on(self) -> bool:
        return await self.set_device("grow_light", True)

    async def light_off(self) -> bool:
        return await self.set_device("grow_light", False)

    async def exhaust_on(self) -> bool:
        return await self.set_device("exhaust_fan", True)

    async def exhaust_off(self) -> bool:
        return await self.set_device("exhaust_fan", False)
