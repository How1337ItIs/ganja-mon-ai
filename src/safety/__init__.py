"""
Safety Layer
============

Hardware-level safety enforcement that the AI cannot bypass.

Critical protections:
- Dark period lock (prevents hermaphroditism)
- Water limits (prevents root rot)
- Temperature bounds (emergency actions)
- CO2 safety (prevents dangerous levels)
- Kill switch (emergency shutdown)

Usage:
    from src.safety import SafetyGuardian, SafeActuatorHub

    guardian = SafetyGuardian()
    safe_actuators = SafeActuatorHub(actuators, guardian)

    # AI can only use safe_actuators, not raw actuators
    await safe_actuators.light_on()  # Will be blocked during dark period
"""

from .guardian import (
    SafetyGuardian,
    SafeActuatorHub,
    SafetyLimits,
    DarkPeriodConfig,
    SafetyViolation,
    ViolationType,
)

__all__ = [
    "SafetyGuardian",
    "SafeActuatorHub",
    "SafetyLimits",
    "DarkPeriodConfig",
    "SafetyViolation",
    "ViolationType",
]
