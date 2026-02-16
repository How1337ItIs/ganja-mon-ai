"""
Grow Agent Learning Loop
========================

Mirrors the trading agent's learning pattern for cultivation decisions.
Logs every grow decision + outcome, adaptive sensor weighting,
stage-specific pattern extraction.

Integrates with existing episodic memory in src/brain/memory.py.

Learning targets:
    - Watering effectiveness (amount → soil moisture change)
    - VPD response to environmental controls
    - Light schedule → growth rate correlation
    - CO2 injection → growth response
    - Stage-specific optimal conditions
"""

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.learning.grimoire import get_grimoire

log = structlog.get_logger("grow_learning")

DB_PATH = Path("data/grow_learning.db")


@dataclass
class GrowDecision:
    """A recorded grow decision with outcome tracking."""
    id: int = 0
    timestamp: float = field(default_factory=time.time)
    grow_day: int = 0
    stage: str = ""             # seedling, veg, flower, harvest
    decision_type: str = ""     # water, light, co2, exhaust, temperature
    action: str = ""            # e.g., "water:200ml", "light:on", "co2:15s"
    conditions_before: Dict[str, Any] = field(default_factory=dict)
    conditions_after: Dict[str, Any] = field(default_factory=dict)
    outcome_measured: bool = False
    effectiveness: float = 0.0  # -1 to +1 (negative = made things worse)
    notes: str = ""


@dataclass
class SensorReliability:
    """Track how reliable each sensor is for decision-making."""
    sensor: str
    readings_total: int = 0
    readings_valid: int = 0     # Within expected range
    readings_outlier: int = 0   # Outside expected range
    weight: float = 1.0         # Decision weight (0.1 - 1.5)
    last_reading_at: float = 0.0


@dataclass
class StagePattern:
    """Optimal conditions learned for a grow stage."""
    stage: str
    optimal_temp: float = 25.0
    optimal_humidity: float = 55.0
    optimal_vpd: float = 1.0
    optimal_co2: float = 800.0
    optimal_soil_moisture: float = 40.0
    watering_amount_ml: float = 200.0
    watering_frequency_hours: float = 12.0
    light_hours: float = 18.0
    sample_size: int = 0
    confidence: float = 0.3


class GrowLearning:
    """
    Learning loop for cannabis cultivation decisions.

    Flow:
    1. Record every decision + conditions before
    2. Next cycle: measure conditions after → compute effectiveness
    3. Extract stage-specific patterns
    4. Adjust sensor weights based on reliability
    5. Store learnings in cultivation grimoire
    """

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None
        self._sensor_weights: Dict[str, SensorReliability] = {}
        self._stage_patterns: Dict[str, StagePattern] = {}
        self._pending_decisions: List[int] = []  # IDs awaiting outcome measurement

    def _ensure_db(self) -> sqlite3.Connection:
        if self._db is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(str(DB_PATH))
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    grow_day INTEGER,
                    stage TEXT,
                    decision_type TEXT,
                    action TEXT,
                    conditions_before TEXT,
                    conditions_after TEXT,
                    outcome_measured INTEGER DEFAULT 0,
                    effectiveness REAL DEFAULT 0.0,
                    notes TEXT DEFAULT ''
                )
            """)
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS sensor_reliability (
                    sensor TEXT PRIMARY KEY,
                    readings_total INTEGER DEFAULT 0,
                    readings_valid INTEGER DEFAULT 0,
                    readings_outlier INTEGER DEFAULT 0,
                    weight REAL DEFAULT 1.0,
                    last_reading_at REAL DEFAULT 0.0
                )
            """)
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS stage_patterns (
                    stage TEXT PRIMARY KEY,
                    optimal_temp REAL,
                    optimal_humidity REAL,
                    optimal_vpd REAL,
                    optimal_co2 REAL,
                    optimal_soil_moisture REAL,
                    watering_amount_ml REAL,
                    watering_frequency_hours REAL,
                    light_hours REAL,
                    sample_size INTEGER,
                    confidence REAL
                )
            """)
            self._db.commit()

            # Load sensor weights
            for row in self._db.execute("SELECT * FROM sensor_reliability"):
                sr = SensorReliability(
                    sensor=row[0], readings_total=row[1], readings_valid=row[2],
                    readings_outlier=row[3], weight=row[4], last_reading_at=row[5],
                )
                self._sensor_weights[sr.sensor] = sr

            # Load stage patterns
            for row in self._db.execute("SELECT * FROM stage_patterns"):
                sp = StagePattern(
                    stage=row[0], optimal_temp=row[1], optimal_humidity=row[2],
                    optimal_vpd=row[3], optimal_co2=row[4], optimal_soil_moisture=row[5],
                    watering_amount_ml=row[6], watering_frequency_hours=row[7],
                    light_hours=row[8], sample_size=row[9], confidence=row[10],
                )
                self._stage_patterns[sp.stage] = sp

            # Load pending decisions
            for row in self._db.execute("SELECT id FROM decisions WHERE outcome_measured=0"):
                self._pending_decisions.append(row[0])

        return self._db

    def record_decision(
        self,
        grow_day: int,
        stage: str,
        decision_type: str,
        action: str,
        conditions: Dict[str, Any],
        notes: str = "",
    ) -> int:
        """Record a grow decision for outcome tracking."""
        db = self._ensure_db()
        cursor = db.execute(
            "INSERT INTO decisions (timestamp, grow_day, stage, decision_type, action, conditions_before, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (time.time(), grow_day, stage, decision_type, action, json.dumps(conditions), notes),
        )
        db.commit()
        decision_id = cursor.lastrowid
        self._pending_decisions.append(decision_id)

        # Track goal action
        from src.learning.strategy_tracker import get_strategy_tracker
        tracker = get_strategy_tracker()
        tracker.record_goal_action("G-2", f"grow_decision:{decision_type}", f"grow_{stage}", action)

        return decision_id

    def measure_outcome(
        self,
        decision_id: int,
        conditions_after: Dict[str, Any],
    ) -> float:
        """Measure the outcome of a previous decision."""
        db = self._ensure_db()

        row = db.execute(
            "SELECT decision_type, action, conditions_before FROM decisions WHERE id=?",
            (decision_id,),
        ).fetchone()

        if not row:
            return 0.0

        decision_type, action, conditions_before_json = row
        conditions_before = json.loads(conditions_before_json)

        # Calculate effectiveness based on decision type
        effectiveness = self._calculate_effectiveness(
            decision_type, conditions_before, conditions_after
        )

        db.execute(
            "UPDATE decisions SET conditions_after=?, outcome_measured=1, effectiveness=? WHERE id=?",
            (json.dumps(conditions_after), effectiveness, decision_id),
        )
        db.commit()

        if decision_id in self._pending_decisions:
            self._pending_decisions.remove(decision_id)

        # Update grimoire with learning
        if abs(effectiveness) > 0.1:
            grimoire = get_grimoire("cultivation")
            stage = db.execute("SELECT stage FROM decisions WHERE id=?", (decision_id,)).fetchone()
            stage_name = stage[0] if stage else "unknown"

            if effectiveness > 0.3:
                grimoire.add(
                    key=f"effective_{decision_type}_{stage_name}",
                    content=f"{action} during {stage_name} was effective (score: {effectiveness:.2f})",
                    confidence=min(0.5 + effectiveness * 0.3, 0.9),
                    source="grow_learning",
                    tags=[decision_type, stage_name, "effective"],
                )
            elif effectiveness < -0.3:
                grimoire.add(
                    key=f"ineffective_{decision_type}_{stage_name}",
                    content=f"{action} during {stage_name} was counterproductive (score: {effectiveness:.2f})",
                    confidence=min(0.5 + abs(effectiveness) * 0.3, 0.9),
                    source="grow_learning",
                    tags=[decision_type, stage_name, "ineffective"],
                )
            grimoire.save()

        return effectiveness

    def _calculate_effectiveness(
        self,
        decision_type: str,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> float:
        """Calculate how effective a decision was (-1 to +1)."""

        if decision_type == "water":
            # Good: soil moisture increased moderately (5-15%)
            soil_before = before.get("soil_moisture_avg", 0)
            soil_after = after.get("soil_moisture_avg", 0)
            change = soil_after - soil_before

            if 5 <= change <= 15:
                return 0.8  # Ideal increase
            elif 0 < change < 5:
                return 0.3  # Minimal effect
            elif change > 15:
                return -0.3  # Overwatered
            elif change <= 0:
                return -0.5  # No effect (sensor issue or drainage)

        elif decision_type == "co2":
            # Good: CO2 increased by 100-300 ppm
            co2_before = before.get("co2", 0)
            co2_after = after.get("co2", 0)
            change = co2_after - co2_before

            if 100 <= change <= 300:
                return 0.8
            elif 50 <= change < 100:
                return 0.4
            elif change > 300:
                return -0.2  # Too much
            elif change <= 0:
                return -0.5  # No effect

        elif decision_type == "exhaust":
            # Good: humidity decreased, temp stable
            rh_before = before.get("humidity", 0)
            rh_after = after.get("humidity", 0)
            rh_change = rh_after - rh_before

            if rh_change < -5:
                return 0.8  # Good dehumidification
            elif rh_change < 0:
                return 0.4
            else:
                return -0.3  # Didn't help

        elif decision_type == "light":
            # Just record, effectiveness measured over days
            return 0.0  # Neutral until we have growth rate data

        return 0.0

    def record_sensor_reading(
        self,
        sensor: str,
        value: float,
        expected_min: float,
        expected_max: float,
    ) -> None:
        """Track sensor reliability."""
        db = self._ensure_db()

        if sensor not in self._sensor_weights:
            self._sensor_weights[sensor] = SensorReliability(sensor=sensor)

        sr = self._sensor_weights[sensor]
        sr.readings_total += 1
        sr.last_reading_at = time.time()

        if expected_min <= value <= expected_max:
            sr.readings_valid += 1
        else:
            sr.readings_outlier += 1

        # Update weight based on reliability
        if sr.readings_total >= 10:
            reliability = sr.readings_valid / sr.readings_total
            sr.weight = max(0.1, min(reliability * 1.2, 1.5))

        db.execute(
            "INSERT OR REPLACE INTO sensor_reliability VALUES (?, ?, ?, ?, ?, ?)",
            (sr.sensor, sr.readings_total, sr.readings_valid, sr.readings_outlier, sr.weight, sr.last_reading_at),
        )
        db.commit()

    def get_sensor_weight(self, sensor: str) -> float:
        """Get decision weight for a sensor."""
        self._ensure_db()
        sr = self._sensor_weights.get(sensor)
        return sr.weight if sr else 1.0

    def extract_stage_patterns(self, stage: str) -> Optional[StagePattern]:
        """Extract optimal conditions from successful decisions for a stage."""
        db = self._ensure_db()

        rows = db.execute(
            "SELECT conditions_before, conditions_after, effectiveness FROM decisions WHERE stage=? AND outcome_measured=1 AND effectiveness > 0.3",
            (stage,),
        ).fetchall()

        if len(rows) < 5:
            return None

        # Average conditions where decisions were effective
        temps, humidities, vpds, co2s, soils = [], [], [], [], []
        for before_json, _, _ in rows:
            cond = json.loads(before_json)
            if "temp" in cond:
                temps.append(cond["temp"])
            if "humidity" in cond:
                humidities.append(cond["humidity"])
            if "vpd" in cond:
                vpds.append(cond["vpd"])
            if "co2" in cond:
                co2s.append(cond["co2"])
            if "soil_moisture_avg" in cond:
                soils.append(cond["soil_moisture_avg"])

        pattern = StagePattern(
            stage=stage,
            optimal_temp=sum(temps) / len(temps) if temps else 25.0,
            optimal_humidity=sum(humidities) / len(humidities) if humidities else 55.0,
            optimal_vpd=sum(vpds) / len(vpds) if vpds else 1.0,
            optimal_co2=sum(co2s) / len(co2s) if co2s else 800.0,
            optimal_soil_moisture=sum(soils) / len(soils) if soils else 40.0,
            sample_size=len(rows),
            confidence=min(0.3 + len(rows) * 0.05, 0.9),
        )

        self._stage_patterns[stage] = pattern

        # Persist
        db.execute(
            "INSERT OR REPLACE INTO stage_patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (pattern.stage, pattern.optimal_temp, pattern.optimal_humidity,
             pattern.optimal_vpd, pattern.optimal_co2, pattern.optimal_soil_moisture,
             pattern.watering_amount_ml, pattern.watering_frequency_hours,
             pattern.light_hours, pattern.sample_size, pattern.confidence),
        )
        db.commit()

        # Store in grimoire
        grimoire = get_grimoire("cultivation")
        grimoire.add(
            key=f"optimal_conditions:{stage}",
            content=(
                f"Optimal {stage} conditions (from {pattern.sample_size} decisions): "
                f"temp={pattern.optimal_temp:.1f}C, "
                f"RH={pattern.optimal_humidity:.0f}%, "
                f"VPD={pattern.optimal_vpd:.2f}, "
                f"CO2={pattern.optimal_co2:.0f}ppm"
            ),
            confidence=pattern.confidence,
            source="grow_learning",
            tags=["optimal", stage],
        )
        grimoire.save()

        log.info(
            "stage_pattern_extracted",
            stage=stage,
            samples=pattern.sample_size,
            temp=round(pattern.optimal_temp, 1),
            humidity=round(pattern.optimal_humidity, 0),
        )

        return pattern

    def get_stage_pattern(self, stage: str) -> Optional[StagePattern]:
        """Get learned optimal conditions for a stage."""
        self._ensure_db()
        return self._stage_patterns.get(stage)

    def get_pending_outcomes(self) -> List[int]:
        """Get decision IDs awaiting outcome measurement."""
        self._ensure_db()
        return list(self._pending_decisions)

    def get_status(self) -> Dict[str, Any]:
        db = self._ensure_db()
        total = db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        measured = db.execute("SELECT COUNT(*) FROM decisions WHERE outcome_measured=1").fetchone()[0]
        effective = db.execute("SELECT COUNT(*) FROM decisions WHERE effectiveness > 0.3").fetchone()[0]

        return {
            "total_decisions": total,
            "measured_outcomes": measured,
            "effective_decisions": effective,
            "pending_outcomes": len(self._pending_decisions),
            "sensor_weights": {
                k: round(v.weight, 2) for k, v in self._sensor_weights.items()
            },
            "stage_patterns": {
                k: {"confidence": round(v.confidence, 2), "samples": v.sample_size}
                for k, v in self._stage_patterns.items()
            },
        }


# Singleton
_instance: Optional[GrowLearning] = None


def get_grow_learning() -> GrowLearning:
    global _instance
    if _instance is None:
        _instance = GrowLearning()
    return _instance
