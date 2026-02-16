"""
SQLAlchemy ORM Models for Grok & Mon
====================================

Data structures derived from SOLTOMATO's claudeandsol.com API:
- sensors_latest / sensors_history -> SensorReading
- devices_latest -> DeviceState
- ai_latest (output_text, sol_day) -> AIDecision, ActionLog
- Episodic memory format -> EpisodicMemory

Cannabis-specific additions:
- GrowthStage enum with photoperiod cannabis stages
- Photoperiod tracking (18/6 vs 12/12)
- Trichome observations for harvest timing
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# =============================================================================
# Enums
# =============================================================================

class GrowthStage(str, Enum):
    """
    Cannabis growth stages (photoperiod grow).
    Based on plan: Seedling -> Vegetative -> Transition -> Flowering -> Harvest

    SOLTOMATO used: seed, sprout, veg, flower, fruit
    We use cannabis-specific stages with photoperiod awareness.
    """
    SEEDLING = "seedling"      # Days 1-14, 18/6 light
    VEGETATIVE = "vegetative"  # Days 15-42, 18/6 light, training/topping
    TRANSITION = "transition"  # Days 43-49, switch to 12/12, pre-flower stretch
    FLOWERING = "flowering"    # Days 50-91, 12/12 light, bud development
    LATE_FLOWER = "late_flower"  # Final 2 weeks, flush period
    HARVEST = "harvest"        # Days 92+, trichome check, chop


class ActionType(str, Enum):
    """
    Types of actions the AI can take.
    Derived from SOLTOMATO's action format: [water:200ml], [co2:inject]
    """
    WATER = "water"
    CO2_INJECT = "co2_inject"
    LIGHT_ON = "light_on"
    LIGHT_OFF = "light_off"
    EXHAUST_ON = "exhaust_on"
    EXHAUST_OFF = "exhaust_off"
    FAN_ON = "fan_on"
    FAN_OFF = "fan_off"
    HEAT_ON = "heat_on"
    HEAT_OFF = "heat_off"
    HUMIDIFIER_ON = "humidifier_on"
    HUMIDIFIER_OFF = "humidifier_off"
    DEHUMIDIFIER_ON = "dehumidifier_on"
    DEHUMIDIFIER_OFF = "dehumidifier_off"
    CAMERA_CAPTURE = "camera_capture"
    STAGE_TRANSITION = "stage_transition"


class Photoperiod(str, Enum):
    """Light schedule for cannabis"""
    VEG_24_0 = "24/0"      # 24 hours light, 0 dark (clone/early veg - continuous light)
    VEG_20_4 = "20/4"      # 20 hours light, 4 dark (vegetative alternative)
    VEG_18_6 = "18/6"      # 18 hours light, 6 hours dark (standard vegetative)
    FLOWER_12_12 = "12/12"  # 12 hours light, 12 hours dark (flowering)
    DARK_48 = "48/0"       # 48 hours dark (pre-harvest stress technique)


# =============================================================================
# Core Models
# =============================================================================

class GrowSession(Base):
    """
    Represents a single grow cycle from seed to harvest.
    Equivalent to SOLTOMATO's "Day 49" tracking - sol_day field.

    One plant per session, tracks overall grow state.
    """
    __tablename__ = "grow_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Plant identification
    plant_name: Mapped[str] = mapped_column(String(100), default="Mon")
    strain_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    strain_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # indica/sativa/hybrid

    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_day: Mapped[int] = mapped_column(Integer, default=1)  # sol_day equivalent

    # Growth state
    current_stage: Mapped[GrowthStage] = mapped_column(
        SQLEnum(GrowthStage), default=GrowthStage.SEEDLING
    )
    photoperiod: Mapped[Photoperiod] = mapped_column(
        SQLEnum(Photoperiod, values_callable=lambda x: [e.value for e in x]),
        default=Photoperiod.VEG_18_6
    )

    # Cumulative stats (like "Day 49 watering total: 600ml")
    total_water_ml: Mapped[int] = mapped_column(Integer, default=0)
    total_co2_injections: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    sensor_readings: Mapped[List["SensorReading"]] = relationship(back_populates="session")
    device_states: Mapped[List["DeviceState"]] = relationship(back_populates="session")
    ai_decisions: Mapped[List["AIDecision"]] = relationship(back_populates="session")
    stage_transitions: Mapped[List["GrowthStageTransition"]] = relationship(back_populates="session")
    episodic_memories: Mapped[List["EpisodicMemory"]] = relationship(back_populates="session")
    reviews: Mapped[List["GrowReview"]] = relationship(back_populates="session")


class SensorReading(Base):
    """
    Time-series sensor data.

    Mirrors SOLTOMATO's sensors_latest/sensors_history structure:
    {
        "timestamp": "2026-01-12T22:03:46",
        "air_temp": 24.87,
        "humidity": 50.6,
        "vpd": 1.29,
        "soil_moisture": 28.205,
        "co2": 603.9,
        "leaf_temp_delta": -1.45
    }

    Additional fields for cannabis-specific tracking.
    """
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Timestamp (indexed for time-series queries)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Core sensors (matching SOLTOMATO exactly)
    air_temp: Mapped[float] = mapped_column(Float)  # Celsius
    humidity: Mapped[float] = mapped_column(Float)  # Percentage
    vpd: Mapped[float] = mapped_column(Float)       # kPa (calculated)
    soil_moisture: Mapped[float] = mapped_column(Float)  # Percentage (averaged)
    co2: Mapped[float] = mapped_column(Float)       # ppm
    leaf_temp_delta: Mapped[float] = mapped_column(Float)  # Celsius diff from air

    # Extended sensors (cannabis-specific)
    soil_moisture_probe1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soil_moisture_probe2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soil_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    leaf_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    light_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-1023 raw
    light_ppfd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # umol/m2/s

    # Dew point (calculated from temp/humidity)
    dew_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationship
    session: Mapped["GrowSession"] = relationship(back_populates="sensor_readings")

    # Indexes for efficient time-series queries
    __table_args__ = (
        Index('idx_sensor_session_time', 'session_id', 'timestamp'),
    )


class DeviceState(Base):
    """
    Device/actuator status snapshots.

    Mirrors SOLTOMATO's devices_latest structure:
    {
        "timestamp": "2026-01-12T22:03:46",
        "grow_light": true,
        "heat_mat": true,
        "circulation_fan": true,
        "exhaust_fan": false,
        "water_pump": false,
        "humidifier": false
    }
    """
    __tablename__ = "device_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Core devices (matching SOLTOMATO)
    grow_light: Mapped[bool] = mapped_column(Boolean, default=False)
    heat_mat: Mapped[bool] = mapped_column(Boolean, default=False)
    circulation_fan: Mapped[bool] = mapped_column(Boolean, default=False)
    exhaust_fan: Mapped[bool] = mapped_column(Boolean, default=False)
    water_pump: Mapped[bool] = mapped_column(Boolean, default=False)
    humidifier: Mapped[bool] = mapped_column(Boolean, default=False)

    # Cannabis-specific additions
    dehumidifier: Mapped[bool] = mapped_column(Boolean, default=False)
    co2_solenoid: Mapped[bool] = mapped_column(Boolean, default=False)

    # Dark period tracking (critical for cannabis flowering)
    is_dark_period: Mapped[bool] = mapped_column(Boolean, default=False)
    dark_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    session: Mapped["GrowSession"] = relationship(back_populates="device_states")


class AIDecision(Base):
    """
    AI decision record - stores Grok's full output.

    Based on SOLTOMATO's ai_latest structure:
    {
        "timestamp": "2026-01-12T22:03:46",
        "output_text": "[think]...[/think]...actions...",
        "sol_day": 49
    }

    We parse out the thinking, actions, and episodic memory.
    """
    __tablename__ = "ai_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Day tracking (sol_day equivalent)
    grow_day: Mapped[int] = mapped_column(Integer)

    # Full AI output (raw text for display)
    output_text: Mapped[str] = mapped_column(Text)

    # Parsed components
    thinking_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # [think] content
    commentary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Public-facing text

    # Sensor snapshot at decision time (for context)
    sensor_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    device_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Decision metadata
    model_used: Mapped[str] = mapped_column(String(50), default="grok-3")
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decision_duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Vision analysis (if camera was used)
    vision_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    session: Mapped["GrowSession"] = relationship(back_populates="ai_decisions")
    actions: Mapped[List["ActionLog"]] = relationship(back_populates="decision")


class ActionLog(Base):
    """
    Individual action record, extracted from AI decisions.

    SOLTOMATO uses inline format: [water:200ml], [co2:inject]
    We store each action separately for tracking and analytics.
    """
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("ai_decisions.id"))
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Action details
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType))
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # e.g., {"amount_ml": 200}
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Execution status
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    execution_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Outcome tracking (for feedback loop)
    # Did the action achieve its goal? (e.g., did temp actually drop after fan ON?)
    outcome_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    decision: Mapped["AIDecision"] = relationship(back_populates="actions")


class GrowthStageTransition(Base):
    """
    Records growth stage changes.

    Cannabis-specific: tracks when plant moves between stages,
    especially the critical veg->flower transition (photoperiod flip).
    """
    __tablename__ = "growth_stage_transitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Transition details
    from_stage: Mapped[GrowthStage] = mapped_column(SQLEnum(GrowthStage))
    to_stage: Mapped[GrowthStage] = mapped_column(SQLEnum(GrowthStage))
    grow_day: Mapped[int] = mapped_column(Integer)

    # Trigger info
    triggered_by: Mapped[str] = mapped_column(String(50))  # "ai", "manual", "schedule"
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cannabis-specific: photoperiod change
    photoperiod_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    new_photoperiod: Mapped[Optional[Photoperiod]] = mapped_column(
        SQLEnum(Photoperiod, values_callable=lambda x: [e.value for e in x]), nullable=True
    )

    # Relationship
    session: Mapped["GrowSession"] = relationship(back_populates="stage_transitions")


class EpisodicMemory(Base):
    """
    Structured episodic memory for AI context.

    Based on SOLTOMATO's format in ai_narratives.log:
    ```
    Episodic Memory Stored:
    ☀️ DAY 49 - MID-DAY UPDATE (11:31 AM) ☀️
    CONDITIONS: 25.72°C, 51.8% RH, 634.4 ppm CO2
    ACTIONS TAKEN: [water:200ml] ✓
    OBSERVATION: Probe 1 dropped from 26.45% → 19.87%
    NEXT: Read sensors, check thresholds...
    ```

    Stored structured for efficient retrieval and context injection.
    """
    __tablename__ = "episodic_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))
    decision_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ai_decisions.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    # Memory metadata
    grow_day: Mapped[int] = mapped_column(Integer)
    time_label: Mapped[str] = mapped_column(String(50))  # "MID-DAY UPDATE", "MORNING CHECK"

    # Structured content (JSON for flexibility)
    conditions: Mapped[dict] = mapped_column(JSON)  # {"temp": 25.72, "rh": 51.8, ...}
    actions_taken: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # ["water:200ml"]
    observations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    next_steps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Full formatted text (for display/AI context)
    formatted_text: Mapped[str] = mapped_column(Text)

    # Importance for context selection
    importance_score: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationship
    session: Mapped["GrowSession"] = relationship(back_populates="episodic_memories")


# =============================================================================
# Actuator State Tracking (SmartGrow Pattern)
# =============================================================================

class ActuatorType(str, Enum):
    """Types of actuators in the system"""
    GROW_LIGHT = "grow_light"
    EXHAUST_FAN = "exhaust_fan"
    INTAKE_FAN = "intake_fan"
    CIRCULATION_FAN = "circulation_fan"
    HUMIDIFIER = "humidifier"
    DEHUMIDIFIER = "dehumidifier"
    WATER_PUMP = "water_pump"
    HEAT_MAT = "heat_mat"
    CO2_SOLENOID = "co2_solenoid"


class ActuatorState(Base):
    """
    Individual actuator state tracking.

    Based on SmartGrow DataControl's Actuadores pattern:
    - Each actuator has its own state record
    - Tracks who/what changed the state
    - Enables independent tracking per device

    This supplements DeviceState which is a snapshot of all devices.
    """
    __tablename__ = "actuator_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Actuator identification
    actuator_type: Mapped[ActuatorType] = mapped_column(SQLEnum(ActuatorType))
    actuator_id: Mapped[str] = mapped_column(String(50), default="main")  # For multiple of same type

    # Current state
    is_on: Mapped[bool] = mapped_column(Boolean, default=False)
    intensity_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For dimmable devices

    # Timing
    state_changed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    on_since: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When turned on
    total_on_time_today_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Change tracking
    changed_by: Mapped[str] = mapped_column(String(50))  # "ai", "manual", "schedule", "safety"
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_actuator_type_time', 'actuator_type', 'state_changed_at'),
        Index('idx_actuator_session', 'session_id', 'actuator_type'),
    )


class Setpoint(Base):
    """
    Stored setpoints for growth stages.

    Based on SmartGrow's SetPoints pattern - stores target values
    that the AI compares sensor readings against.
    """
    __tablename__ = "setpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Which stage these setpoints apply to
    growth_stage: Mapped[GrowthStage] = mapped_column(SQLEnum(GrowthStage))

    # Environmental targets
    vpd_target: Mapped[float] = mapped_column(Float, default=1.0)
    vpd_min: Mapped[float] = mapped_column(Float, default=0.8)
    vpd_max: Mapped[float] = mapped_column(Float, default=1.2)

    temp_target_f: Mapped[float] = mapped_column(Float, default=77)
    temp_min_f: Mapped[float] = mapped_column(Float, default=70)
    temp_max_f: Mapped[float] = mapped_column(Float, default=85)

    humidity_target: Mapped[float] = mapped_column(Float, default=55)
    humidity_min: Mapped[float] = mapped_column(Float, default=40)
    humidity_max: Mapped[float] = mapped_column(Float, default=70)

    # Substrate targets
    moisture_target: Mapped[float] = mapped_column(Float, default=50)
    ec_target: Mapped[float] = mapped_column(Float, default=1.4)
    ph_target: Mapped[float] = mapped_column(Float, default=6.2)

    # Light targets
    ppfd_target: Mapped[int] = mapped_column(Integer, default=500)
    dli_target: Mapped[float] = mapped_column(Float, default=30)

    # CO2 targets
    co2_target: Mapped[int] = mapped_column(Integer, default=800)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(50), default="default")  # "default", "custom", "strain_profile"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_setpoint_stage', 'session_id', 'growth_stage'),
    )


class WateringPrediction(Base):
    """
    SOLTOMATO pattern: Track watering predictions and actual results.

    Enables learning from watering outcomes:
    - Predict expected moisture increase per probe
    - Verify actual results 2 hours later
    - Calculate accuracy for AI context

    Example from SOLTOMATO:
    "Predicted +10%, actual +9.55% - very accurate!"
    """
    __tablename__ = "watering_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # When prediction was made
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    grow_day: Mapped[int] = mapped_column(Integer)

    # Watering details
    amount_ml: Mapped[int] = mapped_column(Integer)

    # Before watering readings
    probe1_before: Mapped[float] = mapped_column(Float)
    probe2_before: Mapped[float] = mapped_column(Float)
    avg_before: Mapped[float] = mapped_column(Float)

    # Predictions (what we expect)
    predicted_probe1_after: Mapped[float] = mapped_column(Float)
    predicted_probe2_after: Mapped[float] = mapped_column(Float)
    predicted_avg_after: Mapped[float] = mapped_column(Float)

    # Actual results (filled in later)
    actual_probe1_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_probe2_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_avg_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Verification
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accuracy_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # How close prediction was

    # Learning - soil absorption rate (ml per % increase)
    calculated_absorption_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index('idx_prediction_session_time', 'session_id', 'timestamp'),
    )


class MetricExtreme(Base):
    """
    SOLTOMATO pattern: Track all-time high/low for each metric.

    Their API returns:
    - temp_ath: 28.6, temp_atl: 19.8
    - humidity_ath: 66.6, humidity_atl: 35.5
    etc.

    This enables "X vs ATH/ATL %" calculations for context.
    """
    __tablename__ = "metric_extremes"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Which metric
    metric_name: Mapped[str] = mapped_column(String(50))  # "temp", "humidity", "vpd", "soil", "co2"

    # All-time high
    ath_value: Mapped[float] = mapped_column(Float)
    ath_timestamp: Mapped[datetime] = mapped_column(DateTime)

    # All-time low
    atl_value: Mapped[float] = mapped_column(Float)
    atl_timestamp: Mapped[datetime] = mapped_column(DateTime)

    # Last updated
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_extreme_metric', 'session_id', 'metric_name', unique=True),
    )


class HourlyAggregate(Base):
    """
    SOLTOMATO pattern: Pre-computed hourly aggregates for /api/plant-progress.

    Their response includes:
    - period_start, period_end
    - avg_temp, avg_humidity, avg_vpd, avg_soil_moisture, avg_co2
    - temp_healthy, humidity_healthy, vpd_healthy, soil_healthy, co2_healthy
    - ATH/ATL per metric
    - icon, summary

    Pre-computing these makes the API fast.
    """
    __tablename__ = "hourly_aggregates"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Time period
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    grow_day: Mapped[int] = mapped_column(Integer)

    # Averages
    avg_temp: Mapped[float] = mapped_column(Float)
    avg_humidity: Mapped[float] = mapped_column(Float)
    avg_vpd: Mapped[float] = mapped_column(Float)
    avg_soil_moisture: Mapped[float] = mapped_column(Float)
    avg_co2: Mapped[float] = mapped_column(Float)

    # Health flags (is the metric in healthy range for current stage?)
    temp_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    humidity_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    vpd_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    soil_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    co2_healthy: Mapped[bool] = mapped_column(Boolean, default=True)

    # Change from previous hour
    temp_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vpd_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    soil_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co2_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Biggest change indicator
    biggest_change_metric: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    biggest_change_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    biggest_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Auto-generated summary
    icon: Mapped[str] = mapped_column(String(10), default="🌿")
    summary: Mapped[str] = mapped_column(Text, default="")

    # Sample count
    sample_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_hourly_session_time', 'session_id', 'period_start'),
    )


class StabilityMetric(Base):
    """
    Environmental stability metrics over time windows.

    Based on SmartGrow's Jupyter notebook analysis patterns:
    - Standard deviation from target
    - Coefficient of variation
    - Time in range percentages

    Calculated periodically to track control quality.
    """
    __tablename__ = "stability_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Time window
    window_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    window_end: Mapped[datetime] = mapped_column(DateTime)
    window_hours: Mapped[int] = mapped_column(Integer)  # 1, 6, 24

    # VPD stability
    vpd_mean: Mapped[float] = mapped_column(Float)
    vpd_std: Mapped[float] = mapped_column(Float)
    vpd_min: Mapped[float] = mapped_column(Float)
    vpd_max: Mapped[float] = mapped_column(Float)
    vpd_target: Mapped[float] = mapped_column(Float)
    vpd_deviation_ratio: Mapped[float] = mapped_column(Float)  # std / target
    vpd_in_range_percent: Mapped[float] = mapped_column(Float)  # % of readings in target range

    # Temperature stability
    temp_mean: Mapped[float] = mapped_column(Float)
    temp_std: Mapped[float] = mapped_column(Float)
    temp_in_range_percent: Mapped[float] = mapped_column(Float)

    # Humidity stability
    humidity_mean: Mapped[float] = mapped_column(Float)
    humidity_std: Mapped[float] = mapped_column(Float)
    humidity_in_range_percent: Mapped[float] = mapped_column(Float)

    # Overall score (0-100, higher = more stable)
    stability_score: Mapped[float] = mapped_column(Float)

    # Sample info
    sample_count: Mapped[int] = mapped_column(Integer)
    valid_sample_count: Mapped[int] = mapped_column(Integer)  # After outlier filtering

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_stability_window', 'session_id', 'window_start'),
    )


# =============================================================================
# Grow Reviews
# =============================================================================

class ReviewType(str, Enum):
    """Types of grow reviews"""
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


class GrowReview(Base):
    """
    Periodic review of cultivation performance.
    Analyzes historical sensor data, AI decisions, and actions
    to find problems and optimization opportunities.

    Contains both machine-parseable JSON results and human-readable markdown.
    """
    __tablename__ = "grow_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("grow_sessions.id"))

    # Review metadata
    review_type: Mapped[ReviewType] = mapped_column(SQLEnum(ReviewType))
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    growth_stage: Mapped[str] = mapped_column(String(50))
    grow_day_start: Mapped[int] = mapped_column(Integer)
    grow_day_end: Mapped[int] = mapped_column(Integer)

    # Scores (0-100)
    overall_score: Mapped[float] = mapped_column(Float)
    compliance_score: Mapped[float] = mapped_column(Float)
    stability_score: Mapped[float] = mapped_column(Float)
    decision_quality_score: Mapped[float] = mapped_column(Float)
    data_quality_score: Mapped[float] = mapped_column(Float)

    # Full structured results (machine-parseable)
    results_json: Mapped[dict] = mapped_column(JSON)

    # Human-readable markdown report
    report_markdown: Mapped[str] = mapped_column(Text)

    # Summary for quick display
    summary: Mapped[str] = mapped_column(Text)
    issues_found: Mapped[int] = mapped_column(Integer, default=0)
    optimizations_suggested: Mapped[int] = mapped_column(Integer, default=0)

    # AI feedback tracking
    fed_to_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    fed_to_ai_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    session: Mapped["GrowSession"] = relationship(back_populates="reviews")

    __table_args__ = (
        Index('idx_review_session_type', 'session_id', 'review_type'),
        Index('idx_review_period', 'session_id', 'period_start'),
    )


# =============================================================================
# Lead Capture
# =============================================================================

class Lead(Base):
    """
    Email list signups from the website.
    """
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Contact info
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    interest: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="website")

    # Status
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# =============================================================================
# Indexes for common query patterns
# =============================================================================

# Time-range queries for sensor history (like SOLTOMATO's /api/sensors/history?hours=24)
Index('idx_sensor_time_range', SensorReading.session_id, SensorReading.timestamp.desc())

# Latest device state lookup
Index('idx_device_latest', DeviceState.session_id, DeviceState.timestamp.desc())

# AI decision history
Index('idx_decision_day', AIDecision.session_id, AIDecision.grow_day)

# Episodic memory retrieval (most recent first)
Index('idx_memory_recent', EpisodicMemory.session_id, EpisodicMemory.timestamp.desc())


# =============================================================================
# User Authentication
# =============================================================================

class User(Base):
    """
    User authentication model for database-backed auth.
    Replaces the in-memory fake_users_db from auth.py.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
