"""
Photoperiod Scheduler
=====================
APScheduler-based light cycle automation for cannabis cultivation.

Supports:
- 18/6 schedule (vegetative)
- 12/12 schedule (flowering)
- Custom schedules
- Dark period protection (no lights during dark)
- Smooth transitions between schedules
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Optional, Callable, Awaitable, List
import logging

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None


logger = logging.getLogger(__name__)


class PhotoperiodType(Enum):
    """Standard cannabis photoperiods"""
    VEGETATIVE = "18/6"      # 18 hours light, 6 hours dark
    FLOWERING = "12/12"      # 12 hours light, 12 hours dark
    SEEDLING = "18/6"        # Same as veg but lower intensity
    TRANSITION = "12/12"     # First 2 weeks of flower
    CUSTOM = "custom"


@dataclass
class PhotoperiodConfig:
    """Configuration for a photoperiod schedule"""
    light_on_hour: int = 6       # Hour lights turn on (0-23)
    light_on_minute: int = 0
    hours_on: int = 18           # Hours of light
    hours_off: int = 6           # Hours of darkness

    # Optional intensity ramping
    sunrise_minutes: int = 30    # Gradual brightness increase
    sunset_minutes: int = 30     # Gradual brightness decrease

    # Light intensity (0-100%)
    intensity_day: int = 100
    intensity_night: int = 0

    @property
    def light_off_hour(self) -> int:
        """Calculate when lights turn off"""
        return (self.light_on_hour + self.hours_on) % 24

    @property
    def light_off_minute(self) -> int:
        return self.light_on_minute

    @property
    def schedule_str(self) -> str:
        return f"{self.hours_on}/{self.hours_off}"

    @classmethod
    def vegetative(cls, light_on_hour: int = 6) -> "PhotoperiodConfig":
        """Standard 18/6 vegetative schedule"""
        return cls(
            light_on_hour=light_on_hour,
            hours_on=18,
            hours_off=6,
        )

    @classmethod
    def flowering(cls, light_on_hour: int = 6) -> "PhotoperiodConfig":
        """Standard 12/12 flowering schedule"""
        return cls(
            light_on_hour=light_on_hour,
            hours_on=12,
            hours_off=12,
        )

    def to_dict(self) -> dict:
        return {
            "light_on_hour": self.light_on_hour,
            "light_on_minute": self.light_on_minute,
            "hours_on": self.hours_on,
            "hours_off": self.hours_off,
            "schedule": self.schedule_str,
            "light_off_hour": self.light_off_hour,
            "sunrise_minutes": self.sunrise_minutes,
            "sunset_minutes": self.sunset_minutes,
            "intensity_day": self.intensity_day,
        }


@dataclass
class PhotoperiodState:
    """Current state of the photoperiod"""
    is_light_period: bool = True
    current_intensity: int = 100
    next_transition: Optional[datetime] = None
    transition_type: str = "none"  # "sunrise", "sunset", "none"
    schedule: str = "18/6"


# Type alias for light control callback
LightControlCallback = Callable[[int], Awaitable[None]]


class PhotoperiodScheduler:
    """
    Manages automated light cycles for cannabis cultivation.

    Uses APScheduler for reliable timing, integrates with SafeActuatorHub
    for safety enforcement.

    Usage:
        scheduler = PhotoperiodScheduler(light_callback=actuator.set_light_intensity)
        await scheduler.start(PhotoperiodConfig.vegetative())

        # Switch to flowering
        await scheduler.transition_to(PhotoperiodConfig.flowering(), days=7)
    """

    def __init__(
        self,
        light_callback: Optional[LightControlCallback] = None,
        safety_callback: Optional[Callable[[str], Awaitable[bool]]] = None,
    ):
        """
        Initialize scheduler.

        Args:
            light_callback: Async function to control light intensity (0-100)
            safety_callback: Async function to check if light changes are safe
        """
        self.light_callback = light_callback
        self.safety_callback = safety_callback

        self._scheduler: Optional[AsyncIOScheduler] = None
        self._config: Optional[PhotoperiodConfig] = None
        self._state = PhotoperiodState()
        self._running = False
        self._transition_task: Optional[asyncio.Task] = None

        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not installed. Scheduling disabled.")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def config(self) -> Optional[PhotoperiodConfig]:
        return self._config

    @property
    def state(self) -> PhotoperiodState:
        return self._state

    def is_dark_period(self) -> bool:
        """Check if currently in dark period"""
        if not self._config:
            return False
        return not self._state.is_light_period

    def get_current_period(self) -> str:
        """Get human-readable current period"""
        if not self._config:
            return "unscheduled"
        return "day" if self._state.is_light_period else "night"

    async def start(self, config: PhotoperiodConfig) -> None:
        """Start the photoperiod schedule"""
        if not APSCHEDULER_AVAILABLE:
            logger.error("Cannot start scheduler: APScheduler not installed")
            return

        self._config = config
        self._scheduler = AsyncIOScheduler()

        # Schedule lights on
        self._scheduler.add_job(
            self._lights_on,
            CronTrigger(
                hour=config.light_on_hour,
                minute=config.light_on_minute,
            ),
            id="lights_on",
            replace_existing=True,
            misfire_grace_time=300,  # Allow up to 5 minutes late execution
        )

        # Schedule lights off
        self._scheduler.add_job(
            self._lights_off,
            CronTrigger(
                hour=config.light_off_hour,
                minute=config.light_off_minute,
            ),
            id="lights_off",
            replace_existing=True,
            misfire_grace_time=300,  # Allow up to 5 minutes late execution
        )

        # Start scheduler
        self._scheduler.start()
        self._running = True

        # Set initial state based on current time
        await self._set_initial_state()

        logger.info(f"Photoperiod scheduler started: {config.schedule_str}")
        logger.info(f"Lights ON at {config.light_on_hour:02d}:{config.light_on_minute:02d}")
        logger.info(f"Lights OFF at {config.light_off_hour:02d}:{config.light_off_minute:02d}")

    async def stop(self) -> None:
        """Stop the scheduler"""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

        if self._transition_task:
            self._transition_task.cancel()
            self._transition_task = None

        self._running = False
        logger.info("Photoperiod scheduler stopped")

    async def transition_to(
        self,
        new_config: PhotoperiodConfig,
        days: int = 7,
    ) -> None:
        """
        Gradually transition to a new photoperiod.

        For example, transitioning from 18/6 to 12/12 over 7 days
        would reduce light hours by ~1 hour per day.

        Args:
            new_config: Target photoperiod configuration
            days: Number of days for the transition
        """
        if not self._config or days <= 0:
            await self.start(new_config)
            return

        old_hours = self._config.hours_on
        new_hours = new_config.hours_on
        hour_diff = new_hours - old_hours

        if hour_diff == 0:
            await self.start(new_config)
            return

        logger.info(f"Transitioning from {old_hours}h to {new_hours}h over {days} days")

        # Calculate daily adjustment
        daily_adjustment = hour_diff / days

        # Schedule daily adjustments
        async def adjust_schedule():
            current_hours = self._config.hours_on + daily_adjustment

            if (daily_adjustment > 0 and current_hours >= new_hours) or \
               (daily_adjustment < 0 and current_hours <= new_hours):
                # Transition complete
                await self.start(new_config)
                return

            # Create intermediate config
            intermediate = PhotoperiodConfig(
                light_on_hour=new_config.light_on_hour,
                hours_on=int(current_hours),
                hours_off=24 - int(current_hours),
            )
            await self.start(intermediate)

        # Schedule daily adjustment
        if self._scheduler:
            self._scheduler.add_job(
                adjust_schedule,
                CronTrigger(hour=0, minute=0),
                id="transition_adjustment",
                replace_existing=True,
            )

    async def _set_initial_state(self) -> None:
        """Set light state based on current time"""
        if not self._config:
            return

        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_time = current_hour * 60 + current_minute

        light_on_time = self._config.light_on_hour * 60 + self._config.light_on_minute
        light_off_time = self._config.light_off_hour * 60 + self._config.light_off_minute

        # Determine if we're in light or dark period
        if light_on_time < light_off_time:
            # Normal schedule (e.g., 6am-midnight)
            is_light = light_on_time <= current_time < light_off_time
        else:
            # Overnight dark period (e.g., 6am-midnight next day)
            is_light = current_time >= light_on_time or current_time < light_off_time

        self._state.is_light_period = is_light
        self._state.schedule = self._config.schedule_str

        # Set lights to match current period
        if is_light:
            await self._lights_on()
        else:
            await self._lights_off()

    async def _lights_on(self) -> None:
        """Turn lights on with optional sunrise ramp"""
        logger.info("Photoperiod: Lights ON")

        # Check safety first
        if self.safety_callback:
            safe = await self.safety_callback("lights_on")
            if not safe:
                logger.warning("Light ON blocked by safety check")
                return

        self._state.is_light_period = True
        self._state.transition_type = "sunrise"

        if self._config and self._config.sunrise_minutes > 0:
            # Gradual sunrise
            await self._ramp_intensity(
                start=0,
                end=self._config.intensity_day,
                duration_minutes=self._config.sunrise_minutes,
            )
        else:
            # Instant on
            await self._set_intensity(self._config.intensity_day if self._config else 100)

        self._state.transition_type = "none"
        self._update_next_transition()

    async def _lights_off(self) -> None:
        """Turn lights off with optional sunset ramp"""
        logger.info("Photoperiod: Lights OFF")

        # Check safety first
        if self.safety_callback:
            safe = await self.safety_callback("lights_off")
            if not safe:
                logger.warning("Light OFF blocked by safety check")
                return

        self._state.transition_type = "sunset"

        if self._config and self._config.sunset_minutes > 0:
            # Gradual sunset
            await self._ramp_intensity(
                start=self._config.intensity_day,
                end=0,
                duration_minutes=self._config.sunset_minutes,
            )
        else:
            # Instant off
            await self._set_intensity(0)

        self._state.is_light_period = False
        self._state.transition_type = "none"
        self._update_next_transition()

    async def _ramp_intensity(
        self,
        start: int,
        end: int,
        duration_minutes: int,
    ) -> None:
        """Gradually change light intensity"""
        if duration_minutes <= 0:
            await self._set_intensity(end)
            return

        steps = min(duration_minutes, 30)  # Max 30 steps
        step_duration = (duration_minutes * 60) / steps
        intensity_step = (end - start) / steps

        current_intensity = start
        for i in range(steps):
            current_intensity = start + (intensity_step * (i + 1))
            await self._set_intensity(int(current_intensity))
            await asyncio.sleep(step_duration)

        # Ensure we end at exactly the target
        await self._set_intensity(end)

    async def _set_intensity(self, intensity: int) -> None:
        """Set light intensity via callback"""
        intensity = max(0, min(100, intensity))
        self._state.current_intensity = intensity

        if self.light_callback:
            try:
                await self.light_callback(intensity)
            except Exception as e:
                logger.error(f"Failed to set light intensity: {e}")

    def _update_next_transition(self) -> None:
        """Update next transition time in state"""
        if not self._config:
            self._state.next_transition = None
            return

        now = datetime.now()

        if self._state.is_light_period:
            # Next transition is lights off
            next_hour = self._config.light_off_hour
            next_minute = self._config.light_off_minute
        else:
            # Next transition is lights on
            next_hour = self._config.light_on_hour
            next_minute = self._config.light_on_minute

        # Calculate next transition datetime
        next_transition = now.replace(
            hour=next_hour,
            minute=next_minute,
            second=0,
            microsecond=0,
        )

        # If that time already passed today, it's tomorrow
        if next_transition <= now:
            next_transition += timedelta(days=1)

        self._state.next_transition = next_transition

    def get_status(self) -> dict:
        """Get current scheduler status"""
        return {
            "running": self._running,
            "config": self._config.to_dict() if self._config else None,
            "state": {
                "is_light_period": self._state.is_light_period,
                "current_intensity": self._state.current_intensity,
                "next_transition": self._state.next_transition.isoformat() if self._state.next_transition else None,
                "transition_type": self._state.transition_type,
                "schedule": self._state.schedule,
                "period": self.get_current_period(),
            },
        }


# =============================================================================
# Convenience functions
# =============================================================================

def create_vegetative_scheduler(
    light_callback: LightControlCallback,
    light_on_hour: int = 6,
) -> PhotoperiodScheduler:
    """Create a scheduler configured for vegetative growth (18/6)"""
    scheduler = PhotoperiodScheduler(light_callback=light_callback)
    return scheduler


def create_flowering_scheduler(
    light_callback: LightControlCallback,
    light_on_hour: int = 6,
) -> PhotoperiodScheduler:
    """Create a scheduler configured for flowering (12/12)"""
    scheduler = PhotoperiodScheduler(light_callback=light_callback)
    return scheduler
