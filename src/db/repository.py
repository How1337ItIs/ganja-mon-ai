"""
Data Access Repository
======================

High-level data access methods for the Grok & Mon system.
Methods designed to match SOLTOMATO's API patterns:
- /api/sensors/latest -> get_sensors_latest()
- /api/sensors/history?hours=N -> get_sensors_history(hours)
- /api/devices/latest -> get_devices_latest()
- /api/ai/latest -> get_ai_latest()

Plus cannabis-specific methods for growth tracking.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import re
import json

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    GrowSession,
    SensorReading,
    DeviceState,
    AIDecision,
    ActionLog,
    GrowthStageTransition,
    EpisodicMemory,
    GrowthStage,
    ActionType,
    Photoperiod,
    WateringPrediction,
    MetricExtreme,
    HourlyAggregate,
    GrowReview,
    ReviewType,
)


class GrowRepository:
    """
    Repository for grow session data access.

    Provides methods that mirror SOLTOMATO's API structure
    for easy frontend integration.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # Session Management
    # =========================================================================

    async def get_active_session(self) -> Optional[GrowSession]:
        """Get the currently active grow session"""
        result = await self.session.execute(
            select(GrowSession)
            .where(GrowSession.is_active == True)
            .order_by(desc(GrowSession.start_date))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_session(
        self,
        plant_name: str = "Mon",
        strain_name: Optional[str] = None,
        strain_type: Optional[str] = None,
    ) -> GrowSession:
        """Create a new grow session"""
        # Deactivate any existing active sessions
        existing = await self.get_active_session()
        if existing:
            existing.is_active = False
            existing.end_date = datetime.utcnow()

        session = GrowSession(
            plant_name=plant_name,
            strain_name=strain_name,
            strain_type=strain_type,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def increment_day(self, session_id: int) -> int:
        """
        Increment the grow day counter.
        Called at the start of each new day (like sol_day).
        """
        result = await self.session.execute(
            select(GrowSession).where(GrowSession.id == session_id)
        )
        grow_session = result.scalar_one()
        grow_session.current_day += 1
        return grow_session.current_day

    # =========================================================================
    # Sensor Data (mirrors /api/sensors/*)
    # =========================================================================

    async def get_sensors_latest(self, session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get latest sensor reading.
        Mirrors SOLTOMATO's /api/sensors/latest endpoint.

        Returns dict matching their format:
        {
            "timestamp": "2026-01-12T22:03:46",
            "air_temp": 24.87,
            "humidity": 50.6,
            "vpd": 1.29,
            "soil_moisture": 28.205,
            "co2": 603.9,
            "leaf_temp_delta": -1.45
        }
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return None
            session_id = active.id

        result = await self.session.execute(
            select(SensorReading)
            .where(SensorReading.session_id == session_id)
            .order_by(desc(SensorReading.timestamp))
            .limit(1)
        )
        reading = result.scalar_one_or_none()

        if not reading:
            return None

        return {
            "timestamp": reading.timestamp.isoformat(),
            "air_temp": reading.air_temp,
            "humidity": reading.humidity,
            "vpd": reading.vpd,
            "soil_moisture": reading.soil_moisture,
            "co2": reading.co2,
            "leaf_temp_delta": reading.leaf_temp_delta,
            # Extended fields
            "soil_moisture_probe1": reading.soil_moisture_probe1,
            "soil_moisture_probe2": reading.soil_moisture_probe2,
            "soil_temp": reading.soil_temp,
            "light_level": reading.light_level,
        }

    async def get_sensors_history(
        self,
        hours: int = 24,
        session_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get sensor history for time range.
        Mirrors SOLTOMATO's /api/sensors/history?hours=N endpoint.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(SensorReading)
            .where(
                and_(
                    SensorReading.session_id == session_id,
                    SensorReading.timestamp >= since,
                )
            )
            .order_by(SensorReading.timestamp)
        )
        readings = result.scalars().all()

        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "air_temp": r.air_temp,
                "humidity": r.humidity,
                "vpd": r.vpd,
                "soil_moisture": r.soil_moisture,
                "co2": r.co2,
                "leaf_temp_delta": r.leaf_temp_delta,
            }
            for r in readings
        ]

    async def add_sensor_reading(
        self,
        air_temp: float,
        humidity: float,
        vpd: float,
        soil_moisture: float,
        co2: float,
        leaf_temp_delta: float,
        session_id: Optional[int] = None,
        **kwargs,
    ) -> SensorReading:
        """Add a new sensor reading"""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        reading = SensorReading(
            session_id=session_id,
            air_temp=air_temp,
            humidity=humidity,
            vpd=vpd,
            soil_moisture=soil_moisture,
            co2=co2,
            leaf_temp_delta=leaf_temp_delta,
            **kwargs,
        )
        self.session.add(reading)
        await self.session.flush()
        return reading

    # =========================================================================
    # Device State (mirrors /api/devices/latest)
    # =========================================================================

    async def get_devices_latest(self, session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get latest device states.
        Mirrors SOLTOMATO's /api/devices/latest endpoint.

        Returns dict matching their format:
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
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return None
            session_id = active.id

        result = await self.session.execute(
            select(DeviceState)
            .where(DeviceState.session_id == session_id)
            .order_by(desc(DeviceState.timestamp))
            .limit(1)
        )
        state = result.scalar_one_or_none()

        if not state:
            return None

        return {
            "timestamp": state.timestamp.isoformat(),
            "grow_light": state.grow_light,
            "heat_mat": state.heat_mat,
            "circulation_fan": state.circulation_fan,
            "exhaust_fan": state.exhaust_fan,
            "water_pump": state.water_pump,
            "humidifier": state.humidifier,
            # Cannabis additions
            "dehumidifier": state.dehumidifier,
            "co2_solenoid": state.co2_solenoid,
            "is_dark_period": state.is_dark_period,
        }

    async def update_device_state(
        self,
        session_id: Optional[int] = None,
        **device_states,
    ) -> DeviceState:
        """
        Record a new device state snapshot.

        Args:
            session_id: Grow session ID (uses active if not provided)
            **device_states: Device states to record (grow_light=True, etc.)
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        state = DeviceState(session_id=session_id, **device_states)
        self.session.add(state)
        await self.session.flush()
        return state

    # =========================================================================
    # AI Decisions (mirrors /api/ai/latest)
    # =========================================================================

    async def get_ai_latest(self, session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get latest AI decision/output.
        Mirrors SOLTOMATO's /api/ai/latest endpoint.

        Returns dict matching their format:
        {
            "timestamp": "2026-01-12T22:03:46",
            "output_text": "...",
            "sol_day": 49  (we use "mon_day")
        }
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return None
            session_id = active.id

        result = await self.session.execute(
            select(AIDecision)
            .where(AIDecision.session_id == session_id)
            .order_by(desc(AIDecision.timestamp))
            .limit(1)
        )
        decision = result.scalar_one_or_none()

        if not decision:
            return None

        return {
            "timestamp": decision.timestamp.isoformat(),
            "output_text": decision.output_text,
            "mon_day": decision.grow_day,  # sol_day equivalent
        }

    async def get_ai_history(self, limit: int = 20, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get historical AI decisions.
        Returns list of past AI outputs for the history panel.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(AIDecision)
            .where(AIDecision.session_id == session_id)
            .order_by(desc(AIDecision.timestamp))
            .limit(limit)
        )
        decisions = result.scalars().all()

        return [
            {
                "timestamp": d.timestamp.isoformat(),
                "output_text": d.output_text,
                "mon_day": d.grow_day,
            }
            for d in decisions
        ]

    async def add_ai_decision(
        self,
        output_text: str,
        grow_day: int,
        session_id: Optional[int] = None,
        thinking_text: Optional[str] = None,
        sensor_snapshot: Optional[dict] = None,
        device_snapshot: Optional[dict] = None,
        **kwargs,
    ) -> AIDecision:
        """
        Record an AI decision.

        Automatically parses [think] blocks and extracts actions.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        # Parse thinking block if not provided
        if thinking_text is None:
            thinking_text = self._extract_thinking(output_text)

        # Extract commentary (non-thinking parts)
        commentary_text = self._extract_commentary(output_text)

        decision = AIDecision(
            session_id=session_id,
            grow_day=grow_day,
            output_text=output_text,
            thinking_text=thinking_text,
            commentary_text=commentary_text,
            sensor_snapshot=sensor_snapshot,
            device_snapshot=device_snapshot,
            **kwargs,
        )
        self.session.add(decision)
        await self.session.flush()

        # Parse and record actions
        actions = self._parse_actions(output_text)
        for action in actions:
            action_log = ActionLog(
                decision_id=decision.id,
                session_id=session_id,
                action_type=action["type"],
                parameters=action.get("params"),
                reason=action.get("reason"),
            )
            self.session.add(action_log)

        return decision

    def _extract_thinking(self, text: str) -> Optional[str]:
        """Extract [think]...[/think] content"""
        match = re.search(r'\[think\](.*?)\[/think\]', text, re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_commentary(self, text: str) -> str:
        """Extract non-thinking content"""
        # Remove think blocks
        text = re.sub(r'\[think\].*?\[/think\]', '', text, flags=re.DOTALL)
        # Remove system message blocks
        text = re.sub(r'┌.*?┘', '', text, flags=re.DOTALL)
        return text.strip()

    def _parse_actions(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse action commands from AI output.
        SOLTOMATO format: [water:200ml], [co2:inject]
        """
        actions = []

        # Water actions: [water:200ml]
        water_matches = re.findall(r'\[water:(\d+)ml?\]', text)
        for amount in water_matches:
            actions.append({
                "type": ActionType.WATER,
                "params": {"amount_ml": int(amount)},
            })

        # CO2 injection: [co2:inject]
        if '[co2:inject]' in text.lower():
            actions.append({"type": ActionType.CO2_INJECT})

        # Light controls
        if 'light on' in text.lower() or 'lights on' in text.lower():
            actions.append({"type": ActionType.LIGHT_ON})
        if 'light off' in text.lower() or 'lights off' in text.lower():
            actions.append({"type": ActionType.LIGHT_OFF})

        # Exhaust controls
        if 'exhaust on' in text.lower():
            actions.append({"type": ActionType.EXHAUST_ON})
        if 'exhaust off' in text.lower():
            actions.append({"type": ActionType.EXHAUST_OFF})

        return actions

    # =========================================================================
    # Growth Stage Management (Cannabis-specific)
    # =========================================================================

    async def get_current_stage(self, session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get current growth stage info"""
        from datetime import datetime, timezone

        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return None
            session_id = active.id
            grow_session = active
        else:
            result = await self.session.execute(
                select(GrowSession).where(GrowSession.id == session_id)
            )
            grow_session = result.scalar_one_or_none()

        if not grow_session:
            return None

        # Calculate current day dynamically from start_date
        # Day 1 = the day the grow started
        now = datetime.now(timezone.utc) if grow_session.start_date.tzinfo else datetime.now()
        start = grow_session.start_date
        days_elapsed = (now.date() - start.date()).days
        calculated_day = max(1, days_elapsed + 1)  # Day 1 on start date
        stored_day = grow_session.current_day or 1
        effective_day = max(stored_day, calculated_day)

        return {
            "current_stage": grow_session.current_stage.value,
            "current_day": effective_day,
            "photoperiod": grow_session.photoperiod.value,
            "total_water_ml": grow_session.total_water_ml,
        }

    async def transition_stage(
        self,
        to_stage: GrowthStage,
        triggered_by: str = "ai",
        reason: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> GrowthStageTransition:
        """
        Record a growth stage transition.

        Automatically handles photoperiod changes for cannabis:
        - Seedling/Veg: 18/6
        - Transition/Flower: 12/12
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id
            grow_session = active
        else:
            result = await self.session.execute(
                select(GrowSession).where(GrowSession.id == session_id)
            )
            grow_session = result.scalar_one()

        from_stage = grow_session.current_stage

        # Determine if photoperiod changes
        photoperiod_changed = False
        new_photoperiod = None

        if to_stage in [GrowthStage.TRANSITION, GrowthStage.FLOWERING, GrowthStage.LATE_FLOWER]:
            if grow_session.photoperiod != Photoperiod.FLOWER_12_12:
                photoperiod_changed = True
                new_photoperiod = Photoperiod.FLOWER_12_12
        elif to_stage in [GrowthStage.SEEDLING, GrowthStage.VEGETATIVE]:
            if grow_session.photoperiod != Photoperiod.VEG_18_6:
                photoperiod_changed = True
                new_photoperiod = Photoperiod.VEG_18_6

        # Record transition
        transition = GrowthStageTransition(
            session_id=session_id,
            from_stage=from_stage,
            to_stage=to_stage,
            grow_day=grow_session.current_day,
            triggered_by=triggered_by,
            reason=reason,
            photoperiod_changed=photoperiod_changed,
            new_photoperiod=new_photoperiod,
        )
        self.session.add(transition)

        # Update session
        grow_session.current_stage = to_stage
        if new_photoperiod:
            grow_session.photoperiod = new_photoperiod

        await self.session.flush()
        return transition

    # =========================================================================
    # Episodic Memory (for AI context)
    # =========================================================================

    async def add_episodic_memory(
        self,
        grow_day: int,
        time_label: str,
        conditions: dict,
        formatted_text: str,
        actions_taken: Optional[list] = None,
        observations: Optional[list] = None,
        next_steps: Optional[list] = None,
        importance_score: float = 1.0,
        session_id: Optional[int] = None,
        decision_id: Optional[int] = None,
    ) -> EpisodicMemory:
        """
        Store an episodic memory entry.

        Format based on SOLTOMATO:
        ☀️ DAY 49 - MID-DAY UPDATE (11:31 AM) ☀️
        CONDITIONS: 25.72°C, 51.8% RH, 634.4 ppm CO2
        ACTIONS TAKEN: [water:200ml] ✓
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        memory = EpisodicMemory(
            session_id=session_id,
            decision_id=decision_id,
            grow_day=grow_day,
            time_label=time_label,
            conditions=conditions,
            actions_taken=actions_taken,
            observations=observations,
            next_steps=next_steps,
            formatted_text=formatted_text,
            importance_score=importance_score,
        )
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def get_recent_memories(
        self,
        limit: int = 10,
        session_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent episodic memories for AI context injection.

        Returns most recent memories first, suitable for
        including in AI prompt context.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(EpisodicMemory)
            .where(EpisodicMemory.session_id == session_id)
            .order_by(desc(EpisodicMemory.timestamp))
            .limit(limit)
        )
        memories = result.scalars().all()

        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "grow_day": m.grow_day,
                "time_label": m.time_label,
                "conditions": m.conditions,
                "actions_taken": m.actions_taken,
                "observations": m.observations,
                "formatted_text": m.formatted_text,
            }
            for m in memories
        ]

    # =========================================================================
    # Statistics & Aggregates
    # =========================================================================

    async def get_daily_stats(
        self,
        grow_day: int,
        session_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get aggregated stats for a specific day.
        Like SOLTOMATO's "Day 49 watering total: 600ml"
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return {}
            session_id = active.id

        # Get all actions for the day
        result = await self.session.execute(
            select(ActionLog)
            .join(AIDecision)
            .where(
                and_(
                    ActionLog.session_id == session_id,
                    AIDecision.grow_day == grow_day,
                )
            )
        )
        actions = result.scalars().all()

        # Calculate totals
        # Parameters are stored as JSON strings, need to parse
        def get_water_amount(params):
            if params is None:
                return 0
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except (json.JSONDecodeError, TypeError):
                    return 0
            if isinstance(params, dict):
                return params.get("amount_ml", 0)
            return 0

        water_total = sum(
            get_water_amount(a.parameters)
            for a in actions
            if a.action_type == ActionType.WATER
        )

        co2_injections = sum(
            1 for a in actions if a.action_type == ActionType.CO2_INJECT
        )

        return {
            "grow_day": grow_day,
            "total_water_ml": water_total,
            "co2_injections": co2_injections,
            "total_actions": len(actions),
        }

    async def update_session_totals(
        self,
        water_ml: int = 0,
        co2_injections: int = 0,
        session_id: Optional[int] = None,
    ) -> None:
        """Update cumulative totals on the grow session"""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return
            session_id = active.id
            grow_session = active
        else:
            result = await self.session.execute(
                select(GrowSession).where(GrowSession.id == session_id)
            )
            grow_session = result.scalar_one()

        grow_session.total_water_ml += water_ml
        grow_session.total_co2_injections += co2_injections

    # =========================================================================
    # Logging Methods (for orchestrator)
    # =========================================================================

    async def log_sensor_reading(
        self,
        air_temp: float,
        humidity: float,
        vpd: float,
        soil_moisture: float,
        co2: float,
        leaf_temp_delta: float,
        soil_moisture_probe1: Optional[float] = None,
        soil_moisture_probe2: Optional[float] = None,
        session_id: Optional[int] = None,
    ) -> SensorReading:
        """
        Log a sensor reading to the database.

        Used by orchestrator to store readings from the sensor polling loop.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        reading = SensorReading(
            session_id=session_id,
            air_temp=air_temp,
            humidity=humidity,
            vpd=vpd,
            soil_moisture=soil_moisture,
            co2=co2,
            leaf_temp_delta=leaf_temp_delta,
            soil_moisture_probe1=soil_moisture_probe1,
            soil_moisture_probe2=soil_moisture_probe2,
        )
        self.session.add(reading)
        await self.session.commit()
        return reading

    async def log_device_state(
        self,
        grow_light: bool = False,
        heat_mat: bool = False,
        circulation_fan: bool = False,
        exhaust_fan: bool = False,
        water_pump: bool = False,
        humidifier: bool = False,
        dehumidifier: bool = False,
        co2_solenoid: bool = False,
        is_dark_period: bool = False,
        session_id: Optional[int] = None,
    ) -> DeviceState:
        """
        Log device state to the database.

        Used by orchestrator to store device states.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        state = DeviceState(
            session_id=session_id,
            grow_light=grow_light,
            heat_mat=heat_mat,
            circulation_fan=circulation_fan,
            exhaust_fan=exhaust_fan,
            water_pump=water_pump,
            humidifier=humidifier,
            dehumidifier=dehumidifier,
            co2_solenoid=co2_solenoid,
            is_dark_period=is_dark_period,
        )
        self.session.add(state)
        await self.session.commit()
        return state

    async def log_ai_decision(
        self,
        grow_day: int,
        output_text: str,
        actions_taken: Optional[list] = None,
        tokens_used: int = 0,
        session_id: Optional[int] = None,
    ) -> AIDecision:
        """
        Log an AI decision to the database.

        Used by orchestrator after Grok makes a decision.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        # Parse thinking from output
        thinking_text = None
        if "[think]" in output_text and "[/think]" in output_text:
            import re
            match = re.search(r'\[think\](.*?)\[/think\]', output_text, re.DOTALL)
            if match:
                thinking_text = match.group(1).strip()

        decision = AIDecision(
            session_id=session_id,
            grow_day=grow_day,
            output_text=output_text,
            thinking_text=thinking_text,
            tokens_used=tokens_used,
            model_used="grok-4-1-fast-non-reasoning",
        )
        self.session.add(decision)
        await self.session.commit()

        # Log actions if provided
        if actions_taken:
            for action in actions_taken:
                action_log = ActionLog(
                    session_id=session_id,
                    decision_id=decision.id,
                    action_type=self._parse_action_type(action.get("tool", "")),
                    parameters=json.dumps(action.get("arguments", {})),
                    success=action.get("success", False),
                    reason=action.get("message", ""),
                    executed=action.get("success", False),
                )
                self.session.add(action_log)
            await self.session.commit()

        return decision

    def _parse_action_type(self, tool_name: str) -> ActionType:
        """Parse tool name to ActionType enum"""
        mapping = {
            "water_plant": ActionType.WATER,
            "control_grow_light": ActionType.LIGHT_ON,
            "control_exhaust_fan": ActionType.EXHAUST_ON,
            "control_circulation_fan": ActionType.FAN_ON,
            "control_heat_mat": ActionType.HEAT_ON,
            "control_humidifier": ActionType.HUMIDIFIER_ON,
            "control_dehumidifier": ActionType.DEHUMIDIFIER_ON,
            "inject_co2": ActionType.CO2_INJECT,
            "take_photo": ActionType.CAMERA_CAPTURE,
        }
        return mapping.get(tool_name, ActionType.WATER)

    # =========================================================================
    # SOLTOMATO Pattern: Stats Endpoint
    # =========================================================================

    async def get_stats(self, session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get total record counts.
        Mirrors SOLTOMATO's /api/stats endpoint.

        Returns:
        {
            "total_records": {
                "sensor_readings": 8386,
                "device_states": 8386,
                "ai_outputs": 8386,
                "episodic_memories": 500
            },
            "data_range": {
                "oldest": "2026-01-06T00:57:28",
                "newest": "2026-01-16T09:23:52"
            }
        }
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return {"total_records": {}, "data_range": {}}
            session_id = active.id

        # Count sensor readings
        sensor_count = await self.session.execute(
            select(func.count(SensorReading.id))
            .where(SensorReading.session_id == session_id)
        )
        sensor_total = sensor_count.scalar() or 0

        # Count device states
        device_count = await self.session.execute(
            select(func.count(DeviceState.id))
            .where(DeviceState.session_id == session_id)
        )
        device_total = device_count.scalar() or 0

        # Count AI decisions
        ai_count = await self.session.execute(
            select(func.count(AIDecision.id))
            .where(AIDecision.session_id == session_id)
        )
        ai_total = ai_count.scalar() or 0

        # Count episodic memories
        memory_count = await self.session.execute(
            select(func.count(EpisodicMemory.id))
            .where(EpisodicMemory.session_id == session_id)
        )
        memory_total = memory_count.scalar() or 0

        # Get data range
        oldest_result = await self.session.execute(
            select(func.min(SensorReading.timestamp))
            .where(SensorReading.session_id == session_id)
        )
        oldest = oldest_result.scalar()

        newest_result = await self.session.execute(
            select(func.max(SensorReading.timestamp))
            .where(SensorReading.session_id == session_id)
        )
        newest = newest_result.scalar()

        return {
            "total_records": {
                "sensor_readings": sensor_total,
                "device_states": device_total,
                "ai_outputs": ai_total,
                "episodic_memories": memory_total,
            },
            "data_range": {
                "oldest": oldest.isoformat() if oldest else None,
                "newest": newest.isoformat() if newest else None,
            }
        }

    # =========================================================================
    # SOLTOMATO Pattern: Plant Progress (Hourly Aggregates)
    # =========================================================================

    async def get_plant_progress(
        self,
        limit: int = 50,
        session_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get hourly aggregated plant progress.
        Mirrors SOLTOMATO's /api/plant-progress endpoint.

        Returns periods with:
        - Hourly averages for all metrics
        - Health flags per metric
        - ATH/ATL values and percentages
        - Auto-generated icon and summary
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return {"periods": []}
            session_id = active.id

        # Get pre-computed aggregates
        result = await self.session.execute(
            select(HourlyAggregate)
            .where(HourlyAggregate.session_id == session_id)
            .order_by(desc(HourlyAggregate.period_start))
            .limit(limit)
        )
        aggregates = result.scalars().all()

        # Get current ATH/ATL values
        extremes = await self._get_metric_extremes(session_id)

        periods = []
        for agg in reversed(aggregates):  # Return chronologically
            period = {
                "period_start": agg.period_start.isoformat(),
                "period_end": agg.period_end.isoformat(),
                "sol_day": agg.grow_day,  # SOLTOMATO uses sol_day

                # Averages
                "avg_temp": round(agg.avg_temp, 2),
                "avg_humidity": round(agg.avg_humidity, 2),
                "avg_vpd": round(agg.avg_vpd, 3),
                "avg_soil_moisture": round(agg.avg_soil_moisture, 2),
                "avg_co2": round(agg.avg_co2, 2),

                # Health flags
                "temp_healthy": agg.temp_healthy,
                "humidity_healthy": agg.humidity_healthy,
                "vpd_healthy": agg.vpd_healthy,
                "soil_healthy": agg.soil_healthy,
                "co2_healthy": agg.co2_healthy,

                # Change percentages
                "temp_change_pct": agg.temp_change_pct,
                "humidity_change_pct": agg.humidity_change_pct,
                "vpd_change_pct": agg.vpd_change_pct,
                "soil_change_pct": agg.soil_change_pct,
                "co2_change_pct": agg.co2_change_pct,

                # Biggest change
                "biggest_change_metric": agg.biggest_change_metric,
                "biggest_change_emoji": agg.biggest_change_emoji,
                "biggest_change_pct": agg.biggest_change_pct,

                # Summary
                "icon": agg.icon,
                "summary": agg.summary,
            }

            # Add ATH/ATL data
            for metric in ["temp", "humidity", "vpd", "soil", "co2"]:
                if metric in extremes:
                    ext = extremes[metric]
                    period[f"{metric}_ath"] = ext["ath"]
                    period[f"{metric}_atl"] = ext["atl"]

                    # Calculate vs ATH/ATL percentages
                    avg_key = f"avg_{metric}" if metric != "soil" else "avg_soil_moisture"
                    avg_val = period.get(avg_key, 0)
                    if ext["ath"] != ext["atl"]:
                        period[f"{metric}_vs_ath_pct"] = round(
                            ((ext["ath"] - avg_val) / ext["ath"]) * 100, 2
                        ) if ext["ath"] else 0
                        period[f"{metric}_vs_atl_pct"] = round(
                            ((avg_val - ext["atl"]) / ext["atl"]) * 100, 2
                        ) if ext["atl"] else 0

            periods.append(period)

        return {"periods": periods}

    async def _get_metric_extremes(self, session_id: int) -> Dict[str, Dict[str, float]]:
        """Get ATH/ATL values for all metrics"""
        result = await self.session.execute(
            select(MetricExtreme)
            .where(MetricExtreme.session_id == session_id)
        )
        extremes = result.scalars().all()

        return {
            ext.metric_name: {
                "ath": ext.ath_value,
                "atl": ext.atl_value,
                "ath_timestamp": ext.ath_timestamp.isoformat(),
                "atl_timestamp": ext.atl_timestamp.isoformat(),
            }
            for ext in extremes
        }

    async def update_metric_extremes(
        self,
        reading: SensorReading,
        session_id: Optional[int] = None,
    ) -> None:
        """
        Update ATH/ATL values based on new sensor reading.
        Called after each sensor reading is stored.
        """
        if session_id is None:
            session_id = reading.session_id

        metrics = {
            "temp": reading.air_temp,
            "humidity": reading.humidity,
            "vpd": reading.vpd,
            "soil": reading.soil_moisture,
            "co2": reading.co2,
        }

        for metric_name, value in metrics.items():
            if value is None:
                continue

            # Check if extreme record exists
            result = await self.session.execute(
                select(MetricExtreme)
                .where(
                    and_(
                        MetricExtreme.session_id == session_id,
                        MetricExtreme.metric_name == metric_name,
                    )
                )
            )
            extreme = result.scalar_one_or_none()

            if extreme is None:
                # Create new record
                extreme = MetricExtreme(
                    session_id=session_id,
                    metric_name=metric_name,
                    ath_value=value,
                    ath_timestamp=reading.timestamp,
                    atl_value=value,
                    atl_timestamp=reading.timestamp,
                )
                self.session.add(extreme)
            else:
                # Update if new extreme
                if value > extreme.ath_value:
                    extreme.ath_value = value
                    extreme.ath_timestamp = reading.timestamp
                if value < extreme.atl_value:
                    extreme.atl_value = value
                    extreme.atl_timestamp = reading.timestamp

    async def compute_hourly_aggregate(
        self,
        hour_start: datetime,
        session_id: Optional[int] = None,
        growth_stage: str = "vegetative",
    ) -> Optional[HourlyAggregate]:
        """
        Compute hourly aggregate for a given hour.
        Called periodically by background task.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return None
            session_id = active.id

        hour_end = hour_start + timedelta(hours=1)

        # Get readings for this hour
        result = await self.session.execute(
            select(SensorReading)
            .where(
                and_(
                    SensorReading.session_id == session_id,
                    SensorReading.timestamp >= hour_start,
                    SensorReading.timestamp < hour_end,
                )
            )
        )
        readings = result.scalars().all()

        if not readings:
            return None

        # Calculate averages
        avg_temp = sum(r.air_temp for r in readings) / len(readings)
        avg_humidity = sum(r.humidity for r in readings) / len(readings)
        avg_vpd = sum(r.vpd for r in readings) / len(readings)
        avg_soil = sum(r.soil_moisture for r in readings) / len(readings)
        avg_co2 = sum(r.co2 for r in readings) / len(readings)

        # Determine health flags based on stage
        temp_healthy, humidity_healthy, vpd_healthy, soil_healthy, co2_healthy = \
            self._check_health_flags(avg_temp, avg_humidity, avg_vpd, avg_soil, avg_co2, growth_stage)

        # Get previous hour for change calculation
        prev_result = await self.session.execute(
            select(HourlyAggregate)
            .where(
                and_(
                    HourlyAggregate.session_id == session_id,
                    HourlyAggregate.period_end == hour_start,
                )
            )
        )
        prev_agg = prev_result.scalar_one_or_none()

        # Calculate changes
        temp_change = humidity_change = vpd_change = soil_change = co2_change = None
        if prev_agg:
            temp_change = ((avg_temp - prev_agg.avg_temp) / prev_agg.avg_temp * 100) if prev_agg.avg_temp else None
            humidity_change = ((avg_humidity - prev_agg.avg_humidity) / prev_agg.avg_humidity * 100) if prev_agg.avg_humidity else None
            vpd_change = ((avg_vpd - prev_agg.avg_vpd) / prev_agg.avg_vpd * 100) if prev_agg.avg_vpd else None
            soil_change = ((avg_soil - prev_agg.avg_soil_moisture) / prev_agg.avg_soil_moisture * 100) if prev_agg.avg_soil_moisture else None
            co2_change = ((avg_co2 - prev_agg.avg_co2) / prev_agg.avg_co2 * 100) if prev_agg.avg_co2 else None

        # Find biggest change
        changes = {
            "Temperature": (temp_change, "🌡️"),
            "Humidity": (humidity_change, "💧"),
            "VPD": (vpd_change, "🌿"),
            "Soil": (soil_change, "🪴"),
            "CO₂": (co2_change, "💨"),
        }
        biggest = max(changes.items(), key=lambda x: abs(x[1][0] or 0))

        # Generate summary and icon
        icon, summary = self._generate_summary(
            avg_temp, avg_humidity, avg_vpd, avg_soil, avg_co2,
            temp_healthy, humidity_healthy, vpd_healthy, soil_healthy, co2_healthy
        )

        # Get current grow day
        session_result = await self.session.execute(
            select(GrowSession).where(GrowSession.id == session_id)
        )
        grow_session = session_result.scalar_one()

        # Use effective day to avoid drift between stored and computed day
        now = datetime.now(timezone.utc) if grow_session.start_date.tzinfo else datetime.now()
        start = grow_session.start_date
        days_elapsed = (now.date() - start.date()).days
        calculated_day = max(1, days_elapsed + 1)
        stored_day = grow_session.current_day or 1
        effective_day = max(stored_day, calculated_day)

        # Create or update aggregate
        existing = await self.session.execute(
            select(HourlyAggregate)
            .where(
                and_(
                    HourlyAggregate.session_id == session_id,
                    HourlyAggregate.period_start == hour_start,
                )
            )
        )
        agg = existing.scalar_one_or_none()

        if agg is None:
            agg = HourlyAggregate(session_id=session_id, period_start=hour_start)
            self.session.add(agg)

        agg.period_end = hour_end
        agg.grow_day = effective_day
        agg.avg_temp = avg_temp
        agg.avg_humidity = avg_humidity
        agg.avg_vpd = avg_vpd
        agg.avg_soil_moisture = avg_soil
        agg.avg_co2 = avg_co2
        agg.temp_healthy = temp_healthy
        agg.humidity_healthy = humidity_healthy
        agg.vpd_healthy = vpd_healthy
        agg.soil_healthy = soil_healthy
        agg.co2_healthy = co2_healthy
        agg.temp_change_pct = round(temp_change, 2) if temp_change else None
        agg.humidity_change_pct = round(humidity_change, 2) if humidity_change else None
        agg.vpd_change_pct = round(vpd_change, 2) if vpd_change else None
        agg.soil_change_pct = round(soil_change, 2) if soil_change else None
        agg.co2_change_pct = round(co2_change, 2) if co2_change else None
        agg.biggest_change_metric = biggest[0]
        agg.biggest_change_emoji = biggest[1][1]
        agg.biggest_change_pct = round(biggest[1][0], 2) if biggest[1][0] else None
        agg.icon = icon
        agg.summary = summary
        agg.sample_count = len(readings)

        return agg

    def _check_health_flags(
        self, temp: float, humidity: float, vpd: float, soil: float, co2: float,
        stage: str = "vegetative"
    ) -> tuple[bool, bool, bool, bool, bool]:
        """Check if metrics are in healthy range for current growth stage"""
        # Stage-specific ranges (cannabis)
        ranges = {
            "seedling": {"temp": (20, 26), "humidity": (65, 75), "vpd": (0.4, 0.8), "soil": (60, 80), "co2": (400, 800)},
            "vegetative": {"temp": (22, 28), "humidity": (50, 70), "vpd": (0.8, 1.2), "soil": (50, 70), "co2": (600, 1200)},
            "flowering": {"temp": (20, 26), "humidity": (40, 55), "vpd": (1.0, 1.5), "soil": (40, 60), "co2": (600, 1000)},
            "late_flower": {"temp": (18, 24), "humidity": (35, 50), "vpd": (1.2, 1.6), "soil": (30, 50), "co2": (400, 800)},
        }
        r = ranges.get(stage, ranges["vegetative"])

        return (
            r["temp"][0] <= temp <= r["temp"][1],
            r["humidity"][0] <= humidity <= r["humidity"][1],
            r["vpd"][0] <= vpd <= r["vpd"][1],
            r["soil"][0] <= soil <= r["soil"][1],
            r["co2"][0] <= co2 <= r["co2"][1],
        )

    def _generate_summary(
        self, temp: float, humidity: float, vpd: float, soil: float, co2: float,
        temp_ok: bool, hum_ok: bool, vpd_ok: bool, soil_ok: bool, co2_ok: bool
    ) -> tuple[str, str]:
        """Generate icon and summary text based on conditions"""
        issues = []
        if not temp_ok:
            issues.append(f"Temperature at {temp:.1f}°C")
        if not hum_ok:
            issues.append(f"Humidity at {humidity:.1f}%")
        if not vpd_ok:
            issues.append(f"VPD at {vpd:.2f} kPa")
        if not soil_ok:
            issues.append(f"Soil moisture at {soil:.1f}%")
        if not co2_ok:
            issues.append(f"CO2 at {co2:.0f} ppm")

        if not issues:
            return "🌿", "Growing well with good core conditions. Minor adjustments may help optimize growth."
        elif len(issues) == 1:
            if not hum_ok:
                return "💧", f"Humidity at {humidity:.1f}%. Grok adjusting environmental controls."
            elif not temp_ok:
                return "🌡️", f"Temperature at {temp:.1f}°C. Grok monitoring heat management."
            elif not vpd_ok:
                return "🌿", f"VPD at {vpd:.2f} kPa. Grok optimizing transpiration conditions."
            elif not soil_ok:
                return "🪴", f"Soil at {soil:.1f}%. Grok managing irrigation."
            else:
                return "💨", f"CO2 at {co2:.0f} ppm. Grok adjusting ventilation."
        else:
            return "⚠️", f"Multiple parameters need attention: {', '.join(issues[:2])}."

    # =========================================================================
    # SOLTOMATO Pattern: Watering Predictions
    # =========================================================================

    async def add_watering_prediction(
        self,
        amount_ml: int,
        probe1_before: float,
        probe2_before: float,
        predicted_increase_pct: float = 10.0,  # Default: expect +10% per 200ml
        session_id: Optional[int] = None,
    ) -> WateringPrediction:
        """
        Record a watering prediction for later verification.

        Called when watering action is taken.
        Default prediction: +10% moisture increase for 200ml (scales linearly).
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                raise ValueError("No active grow session")
            session_id = active.id

        # Scale prediction based on amount (200ml = baseline)
        scale = amount_ml / 200.0
        predicted_increase = predicted_increase_pct * scale

        avg_before = (probe1_before + probe2_before) / 2

        prediction = WateringPrediction(
            session_id=session_id,
            grow_day=(await self.get_active_session()).current_day,
            amount_ml=amount_ml,
            probe1_before=probe1_before,
            probe2_before=probe2_before,
            avg_before=avg_before,
            predicted_probe1_after=probe1_before + predicted_increase,
            predicted_probe2_after=probe2_before + (predicted_increase * 0.5),  # Probe 2 typically less affected
            predicted_avg_after=avg_before + (predicted_increase * 0.75),
        )
        self.session.add(prediction)
        await self.session.flush()
        return prediction

    async def verify_watering_prediction(
        self,
        prediction_id: int,
        probe1_actual: float,
        probe2_actual: float,
    ) -> WateringPrediction:
        """
        Verify a watering prediction with actual results.

        Called ~2 hours after watering to check prediction accuracy.
        """
        result = await self.session.execute(
            select(WateringPrediction).where(WateringPrediction.id == prediction_id)
        )
        prediction = result.scalar_one()

        avg_actual = (probe1_actual + probe2_actual) / 2

        prediction.actual_probe1_after = probe1_actual
        prediction.actual_probe2_after = probe2_actual
        prediction.actual_avg_after = avg_actual
        prediction.verified_at = datetime.utcnow()

        # Calculate accuracy (how close was prediction to actual?)
        predicted_change = prediction.predicted_avg_after - prediction.avg_before
        actual_change = avg_actual - prediction.avg_before

        if predicted_change != 0:
            prediction.accuracy_pct = round(
                (1 - abs(predicted_change - actual_change) / abs(predicted_change)) * 100, 1
            )
        else:
            prediction.accuracy_pct = 100.0 if actual_change == 0 else 0.0

        # Calculate absorption rate (ml per % increase)
        if actual_change > 0:
            prediction.calculated_absorption_rate = round(
                prediction.amount_ml / actual_change, 2
            )

        return prediction

    async def get_recent_predictions(
        self,
        limit: int = 10,
        session_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent watering predictions for AI context"""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(WateringPrediction)
            .where(WateringPrediction.session_id == session_id)
            .order_by(desc(WateringPrediction.timestamp))
            .limit(limit)
        )
        predictions = result.scalars().all()

        return [
            {
                "timestamp": p.timestamp.isoformat(),
                "grow_day": p.grow_day,
                "amount_ml": p.amount_ml,
                "probe1_before": p.probe1_before,
                "probe2_before": p.probe2_before,
                "predicted_probe1_after": p.predicted_probe1_after,
                "actual_probe1_after": p.actual_probe1_after,
                "accuracy_pct": p.accuracy_pct,
                "verified": p.verified_at is not None,
            }
            for p in predictions
        ]

    async def get_average_absorption_rate(self, session_id: Optional[int] = None) -> float:
        """
        Get average soil absorption rate from verified predictions.
        Used to improve future predictions.
        """
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return 20.0  # Default: 20ml per 1% increase
            session_id = active.id

        result = await self.session.execute(
            select(func.avg(WateringPrediction.calculated_absorption_rate))
            .where(
                and_(
                    WateringPrediction.session_id == session_id,
                    WateringPrediction.calculated_absorption_rate.isnot(None),
                )
            )
        )
        avg = result.scalar()
        return avg if avg else 20.0  # Default

    # =========================================================================
    # Grow Reviews
    # =========================================================================

    async def get_sensor_readings_range(
        self,
        start: datetime,
        end: datetime,
        session_id: Optional[int] = None,
    ) -> List[SensorReading]:
        """Get raw SensorReading objects for a time range."""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(SensorReading)
            .where(
                and_(
                    SensorReading.session_id == session_id,
                    SensorReading.timestamp >= start,
                    SensorReading.timestamp <= end,
                )
            )
            .order_by(SensorReading.timestamp)
        )
        return list(result.scalars().all())

    async def get_decisions_range(
        self,
        start: datetime,
        end: datetime,
        session_id: Optional[int] = None,
    ) -> List[AIDecision]:
        """Get AIDecision objects with loaded actions for a time range."""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(AIDecision)
            .options(selectinload(AIDecision.actions))
            .where(
                and_(
                    AIDecision.session_id == session_id,
                    AIDecision.timestamp >= start,
                    AIDecision.timestamp <= end,
                )
            )
            .order_by(AIDecision.timestamp)
        )
        return list(result.scalars().all())

    async def get_watering_predictions_range(
        self,
        start: datetime,
        end: datetime,
        session_id: Optional[int] = None,
    ) -> List[WateringPrediction]:
        """Get watering predictions for a time range."""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(WateringPrediction)
            .where(
                and_(
                    WateringPrediction.session_id == session_id,
                    WateringPrediction.timestamp >= start,
                    WateringPrediction.timestamp <= end,
                )
            )
            .order_by(WateringPrediction.timestamp)
        )
        return list(result.scalars().all())

    async def store_review(self, review_data: dict) -> GrowReview:
        """Store a completed review."""
        review = GrowReview(**review_data)
        self.session.add(review)
        await self.session.flush()
        return review

    async def get_latest_review(
        self,
        review_type: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent review, optionally filtered by type."""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return None
            session_id = active.id

        query = (
            select(GrowReview)
            .where(GrowReview.session_id == session_id)
        )
        if review_type:
            query = query.where(GrowReview.review_type == review_type)
        query = query.order_by(desc(GrowReview.created_at)).limit(1)

        result = await self.session.execute(query)
        review = result.scalar_one_or_none()
        if not review:
            return None
        return self._review_to_dict(review)

    async def get_review_history(
        self,
        limit: int = 10,
        session_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get review history (summary only)."""
        if session_id is None:
            active = await self.get_active_session()
            if not active:
                return []
            session_id = active.id

        result = await self.session.execute(
            select(GrowReview)
            .where(GrowReview.session_id == session_id)
            .order_by(desc(GrowReview.created_at))
            .limit(limit)
        )
        reviews = result.scalars().all()
        return [self._review_to_dict(r, include_full=False) for r in reviews]

    async def get_review_by_id(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific review with full data."""
        result = await self.session.execute(
            select(GrowReview).where(GrowReview.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            return None
        return self._review_to_dict(review, include_full=True)

    async def mark_review_fed_to_ai(self, review_id: int) -> None:
        """Mark a review as having been fed to the AI."""
        result = await self.session.execute(
            select(GrowReview).where(GrowReview.id == review_id)
        )
        review = result.scalar_one_or_none()
        if review:
            review.fed_to_ai = True
            review.fed_to_ai_at = datetime.utcnow()

    def _review_to_dict(
        self, review: GrowReview, include_full: bool = True
    ) -> Dict[str, Any]:
        """Convert GrowReview to dict."""
        d = {
            "id": review.id,
            "review_type": review.review_type.value
            if hasattr(review.review_type, "value")
            else review.review_type,
            "period_start": review.period_start.isoformat(),
            "period_end": review.period_end.isoformat(),
            "growth_stage": review.growth_stage,
            "grow_day_start": review.grow_day_start,
            "grow_day_end": review.grow_day_end,
            "overall_score": review.overall_score,
            "compliance_score": review.compliance_score,
            "stability_score": review.stability_score,
            "decision_quality_score": review.decision_quality_score,
            "data_quality_score": review.data_quality_score,
            "summary": review.summary,
            "issues_found": review.issues_found,
            "optimizations_suggested": review.optimizations_suggested,
            "fed_to_ai": review.fed_to_ai,
            "created_at": review.created_at.isoformat(),
        }
        if include_full:
            d["results_json"] = review.results_json
            d["report_markdown"] = review.report_markdown
        return d
