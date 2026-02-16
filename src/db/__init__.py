"""
Grok & Mon Database Layer
=========================
SQLAlchemy models and data access for the cannabis cultivation system.

Modeled after SOLTOMATO's data structure:
- Sensor readings every 30-60 seconds
- Device state snapshots
- AI decision logs with episodic memory
- Growth stage tracking

Enhanced with SmartGrow DataControl patterns:
- Setpoints for target comparison
- Actuator state tracking
- Stability metrics
"""

from .models import (
    Base,
    GrowSession,
    SensorReading,
    DeviceState,
    AIDecision,
    ActionLog,
    GrowthStageTransition,
    EpisodicMemory,
    # SmartGrow pattern additions
    ActuatorState,
    ActuatorType,
    Setpoint,
    StabilityMetric,
    # Enums
    GrowthStage,
    ActionType,
    Photoperiod,
)
from .connection import DatabaseManager, get_db_session
from .repository import GrowRepository
from .setpoints import (
    get_setpoints,
    get_current_setpoints,
    GrowthStageSetpoints,
    STAGE_SETPOINTS,
)

__all__ = [
    # Base
    "Base",
    # Core models
    "GrowSession",
    "SensorReading",
    "DeviceState",
    "AIDecision",
    "ActionLog",
    "GrowthStageTransition",
    "EpisodicMemory",
    # SmartGrow pattern models
    "ActuatorState",
    "ActuatorType",
    "Setpoint",
    "StabilityMetric",
    # Enums
    "GrowthStage",
    "ActionType",
    "Photoperiod",
    # Connection
    "DatabaseManager",
    "get_db_session",
    "GrowRepository",
    # Setpoints
    "get_setpoints",
    "get_current_setpoints",
    "GrowthStageSetpoints",
    "STAGE_SETPOINTS",
]
