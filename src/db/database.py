"""
SQLite Database for Sol Cannabis
================================

Stores sensor readings, AI decisions, growth logs, and system state.
Lightweight, no server required - perfect for Chromebook deployment.

Usage:
    db = Database("grow_data.db")
    await db.init()
    await db.log_sensor_reading(reading)
    await db.log_ai_decision(decision)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for grow system data"""

    def __init__(self, db_path: str = "data/grow_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Connect to database"""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def init(self):
        """Initialize database schema"""
        conn = self.connect()
        cursor = conn.cursor()

        # Sensor readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature_f REAL,
                temperature_c REAL,
                humidity REAL,
                vpd REAL,
                co2 INTEGER,
                soil_moisture REAL,
                soil_ph REAL,
                soil_ec REAL,
                light_ppfd REAL,
                water_temp_f REAL,
                raw_data TEXT
            )
        """)

        # AI decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT,
                prompt_summary TEXT,
                decision TEXT,
                actions_taken TEXT,
                reasoning TEXT,
                sensor_snapshot TEXT,
                tokens_used INTEGER
            )
        """)

        # Device state changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device TEXT NOT NULL,
                action TEXT NOT NULL,
                triggered_by TEXT,
                details TEXT
            )
        """)

        # Growth stage transitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS growth_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                stage TEXT NOT NULL,
                previous_stage TEXT,
                reason TEXT,
                triggered_by TEXT
            )
        """)

        # Observations/notes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT,
                observation TEXT,
                severity TEXT DEFAULT 'info',
                image_path TEXT
            )
        """)

        # System config/state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensor_timestamp
            ON sensor_readings(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_timestamp
            ON ai_decisions(timestamp)
        """)

        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # =========================================================================
    # Sensor Readings
    # =========================================================================

    def log_sensor_reading(
        self,
        temperature_f: float = None,
        humidity: float = None,
        vpd: float = None,
        co2: int = None,
        soil_moisture: float = None,
        soil_ph: float = None,
        soil_ec: float = None,
        light_ppfd: float = None,
        water_temp_f: float = None,
        raw_data: dict = None,
    ) -> int:
        """Log a sensor reading to database"""
        conn = self.connect()
        cursor = conn.cursor()

        temp_c = (temperature_f - 32) * 5 / 9 if temperature_f else None

        cursor.execute("""
            INSERT INTO sensor_readings
            (timestamp, temperature_f, temperature_c, humidity, vpd, co2,
             soil_moisture, soil_ph, soil_ec, light_ppfd, water_temp_f, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            temperature_f,
            temp_c,
            humidity,
            vpd,
            co2,
            soil_moisture,
            soil_ph,
            soil_ec,
            light_ppfd,
            water_temp_f,
            json.dumps(raw_data) if raw_data else None,
        ))

        conn.commit()
        return cursor.lastrowid

    def get_recent_readings(self, hours: int = 24) -> List[Dict]:
        """Get sensor readings from the last N hours"""
        conn = self.connect()
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        cursor.execute("""
            SELECT * FROM sensor_readings
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (since,))

        return [dict(row) for row in cursor.fetchall()]

    def get_latest_reading(self) -> Optional[Dict]:
        """Get most recent sensor reading"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        return dict(row) if row else None

    # =========================================================================
    # AI Decisions
    # =========================================================================

    def log_ai_decision(
        self,
        decision: str,
        actions_taken: List[str] = None,
        reasoning: str = None,
        sensor_snapshot: dict = None,
        model: str = "grok-2",
        prompt_summary: str = None,
        tokens_used: int = None,
    ) -> int:
        """Log an AI decision to database"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ai_decisions
            (timestamp, model, prompt_summary, decision, actions_taken,
             reasoning, sensor_snapshot, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            model,
            prompt_summary,
            decision,
            json.dumps(actions_taken) if actions_taken else None,
            reasoning,
            json.dumps(sensor_snapshot) if sensor_snapshot else None,
            tokens_used,
        ))

        conn.commit()
        return cursor.lastrowid

    def get_recent_decisions(self, hours: int = 24) -> List[Dict]:
        """Get AI decisions from the last N hours"""
        conn = self.connect()
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        cursor.execute("""
            SELECT * FROM ai_decisions
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (since,))

        results = []
        for row in cursor.fetchall():
            d = dict(row)
            # Parse JSON fields
            if d.get('actions_taken'):
                d['actions_taken'] = json.loads(d['actions_taken'])
            if d.get('sensor_snapshot'):
                d['sensor_snapshot'] = json.loads(d['sensor_snapshot'])
            results.append(d)

        return results

    # =========================================================================
    # Device Events
    # =========================================================================

    def log_device_event(
        self,
        device: str,
        action: str,
        triggered_by: str = "ai",
        details: dict = None,
    ) -> int:
        """Log a device state change"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO device_events
            (timestamp, device, action, triggered_by, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            device,
            action,
            triggered_by,
            json.dumps(details) if details else None,
        ))

        conn.commit()
        return cursor.lastrowid

    # =========================================================================
    # Growth Stages
    # =========================================================================

    def log_stage_change(
        self,
        new_stage: str,
        previous_stage: str = None,
        reason: str = None,
        triggered_by: str = "ai",
    ) -> int:
        """Log a growth stage transition"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO growth_stages
            (timestamp, stage, previous_stage, reason, triggered_by)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            new_stage,
            previous_stage,
            reason,
            triggered_by,
        ))

        conn.commit()
        return cursor.lastrowid

    def get_current_stage(self) -> Optional[str]:
        """Get current growth stage"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT stage FROM growth_stages
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        return row['stage'] if row else "SEEDLING"

    # =========================================================================
    # Observations
    # =========================================================================

    def log_observation(
        self,
        observation: str,
        category: str = "general",
        severity: str = "info",
        image_path: str = None,
    ) -> int:
        """Log an observation or note"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO observations
            (timestamp, category, observation, severity, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            category,
            observation,
            severity,
            image_path,
        ))

        conn.commit()
        return cursor.lastrowid

    # =========================================================================
    # System State
    # =========================================================================

    def set_state(self, key: str, value: Any):
        """Set a system state value"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO system_state (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, json.dumps(value), datetime.now().isoformat()))

        conn.commit()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a system state value"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT value FROM system_state WHERE key = ?
        """, (key,))

        row = cursor.fetchone()
        if row:
            return json.loads(row['value'])
        return default

    # =========================================================================
    # Stats & Summaries
    # =========================================================================

    def get_stats(self, hours: int = 24) -> Dict:
        """Get summary statistics for the last N hours"""
        conn = self.connect()
        cursor = conn.cursor()

        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Sensor averages
        cursor.execute("""
            SELECT
                AVG(temperature_f) as avg_temp,
                AVG(humidity) as avg_humidity,
                AVG(vpd) as avg_vpd,
                MIN(temperature_f) as min_temp,
                MAX(temperature_f) as max_temp,
                COUNT(*) as reading_count
            FROM sensor_readings
            WHERE timestamp > ?
        """, (since,))

        sensor_stats = dict(cursor.fetchone())

        # Decision count
        cursor.execute("""
            SELECT COUNT(*) as decision_count
            FROM ai_decisions
            WHERE timestamp > ?
        """, (since,))

        decision_stats = dict(cursor.fetchone())

        # Device event count
        cursor.execute("""
            SELECT device, COUNT(*) as count
            FROM device_events
            WHERE timestamp > ?
            GROUP BY device
        """, (since,))

        device_stats = {row['device']: row['count'] for row in cursor.fetchall()}

        return {
            "period_hours": hours,
            "sensors": sensor_stats,
            "decisions": decision_stats,
            "device_events": device_stats,
        }


# =============================================================================
# Quick test
# =============================================================================

if __name__ == "__main__":
    db = Database("test_grow.db")
    db.init()

    # Test logging
    db.log_sensor_reading(
        temperature_f=75.5,
        humidity=55.0,
        vpd=1.05,
        co2=420,
        soil_moisture=45.0,
    )

    db.log_ai_decision(
        decision="Maintain current conditions",
        actions_taken=["No changes needed"],
        reasoning="All parameters within range",
        sensor_snapshot={"temp": 75.5, "humidity": 55.0},
    )

    db.log_device_event("grow_light", "on", triggered_by="schedule")

    db.log_stage_change("SEEDLING", reason="Initial planting")

    db.log_observation("Clone planted successfully", category="milestone")

    # Test retrieval
    print("\nLatest reading:", db.get_latest_reading())
    print("\nCurrent stage:", db.get_current_stage())
    print("\nStats:", db.get_stats(hours=1))

    db.close()
    print("\nDatabase test complete!")
