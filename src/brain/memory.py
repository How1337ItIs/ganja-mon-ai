"""
Episodic Memory System for Grok & Mon
======================================
Based on SOLTOMATO's (Claude & Sol) memory pattern.

From SOLTOMATO AI narratives:
```
Episodic Memory Stored:
*** DAY 49 - MID-DAY UPDATE (11:31 AM) ***

CONDITIONS: 25.72°C, 51.8% RH, 634.4 ppm CO2
Soil: 19.87%/36.78% (~28.3% avg)
Leaf Δ: -2.19°C cooler [OK] healthy transpiration

ACTIONS TAKEN:
- [water:200ml] [OK] (average below 30% flowering threshold)

Day 49 watering total: 600ml (400ml from 6:04 AM + 200ml now)

OBSERVATION: Probe 1 dropped from 26.45% (9:09 AM) to 19.87% (11:31 AM)

NEXT (~1:31 PM):
- Read sensors
- If RH > 65% → exhaust ON
- If probe 1 < 18% → water 200ml
```

This pattern enables:
1. Context persistence between decision cycles
2. Tracking cumulative actions (watering totals)
3. Planning next actions
4. Learning from patterns
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class EpisodicMemoryEntry:
    """Single episodic memory entry (one decision cycle)"""

    # When
    timestamp: datetime
    grow_day: int
    time_label: str  # "MORNING CHECK", "MID-DAY UPDATE", "EVENING MONITORING"

    # Conditions snapshot
    conditions: dict  # temp, humidity, co2, vpd, soil moisture

    # What happened
    actions_taken: list[str]  # ["water:200ml", "co2:inject"]
    observations: list[str]  # Key observations from this cycle

    # Planning
    next_actions: list[str]  # What to check next cycle

    # Cumulative tracking
    day_totals: dict  # {"water_ml": 600, "co2_injections": 2}

    # Hippocampus-style memory dynamics (Pattern #17)
    importance: float = 0.5       # 0.0-1.0 — how valuable this memory is
    access_count: int = 0         # How often this memory was retrieved
    decay_rate: float = 0.01      # Per-hour exponential decay
    last_accessed: Optional[datetime] = None  # Last time this memory was read

    def decay(self, hours_elapsed: float):
        """Apply exponential decay to importance based on time elapsed."""
        self.importance *= (1 - self.decay_rate) ** hours_elapsed
        self.importance = max(self.importance, 0.01)  # Floor to prevent total loss

    def reinforce(self, boost: float = 0.1):
        """Strengthen a memory when it's accessed or proven useful."""
        self.importance = min(self.importance + boost, 1.0)
        self.access_count += 1
        self.last_accessed = datetime.now()

    def format_for_display(self) -> str:
        """Format memory entry for console/log display"""
        lines = [
            f"*** DAY {self.grow_day} - {self.time_label} ({self.timestamp.strftime('%I:%M %p')}) ***",
            "",
            f"CONDITIONS: {self.conditions.get('temp_c', 'N/A')}°C, "
            f"{self.conditions.get('humidity', 'N/A')}% RH, "
            f"{self.conditions.get('co2', 'N/A')} ppm CO2",
        ]

        # Soil moisture if available
        if "soil_moisture" in self.conditions:
            sm = self.conditions["soil_moisture"]
            if isinstance(sm, dict):
                lines.append(f"Soil: {sm.get('probe1', 'N/A')}%/{sm.get('probe2', 'N/A')}% "
                           f"(~{sm.get('avg', 'N/A')}% avg)")
            else:
                lines.append(f"Soil: {sm}%")

        # VPD status
        if "vpd" in self.conditions:
            lines.append(f"VPD: {self.conditions['vpd']} kPa")

        lines.append("")

        # Actions taken
        if self.actions_taken:
            lines.append("ACTIONS TAKEN:")
            for action in self.actions_taken:
                lines.append(f"- [{action}] [OK]")
        else:
            lines.append("ACTIONS TAKEN: None (conditions stable)")

        lines.append("")

        # Day totals
        if self.day_totals:
            totals = []
            if "water_ml" in self.day_totals:
                totals.append(f"Day {self.grow_day} watering total: {self.day_totals['water_ml']}ml")
            if "co2_injections" in self.day_totals:
                totals.append(f"CO2 injections today: {self.day_totals['co2_injections']}")
            if totals:
                lines.extend(totals)
                lines.append("")

        # Observations
        if self.observations:
            lines.append("OBSERVATIONS:")
            for obs in self.observations:
                lines.append(f"- {obs}")
            lines.append("")

        # Next actions
        if self.next_actions:
            next_time = self.timestamp + timedelta(hours=2)
            lines.append(f"NEXT (~{next_time.strftime('%I:%M %p')}):")
            for action in self.next_actions:
                lines.append(f"- {action}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "grow_day": self.grow_day,
            "time_label": self.time_label,
            "conditions": self.conditions,
            "actions_taken": self.actions_taken,
            "observations": self.observations,
            "next_actions": self.next_actions,
            "day_totals": self.day_totals,
            "importance": self.importance,
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EpisodicMemoryEntry":
        """Deserialize from dictionary"""
        last_acc = data.get("last_accessed")
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            grow_day=data["grow_day"],
            time_label=data["time_label"],
            conditions=data["conditions"],
            actions_taken=data["actions_taken"],
            observations=data["observations"],
            next_actions=data["next_actions"],
            day_totals=data["day_totals"],
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            decay_rate=data.get("decay_rate", 0.01),
            last_accessed=datetime.fromisoformat(last_acc) if last_acc else None,
        )


class EpisodicMemory:
    """
    Manages episodic memory for the AI agent.

    SOLTOMATO pattern:
    - Store memories after each decision cycle
    - Retrieve recent memories for context
    - Track cumulative actions per day
    - Format memories for AI context injection
    """

    DEFAULT_PERSIST_PATH = "data/episodic_memory.json"

    def __init__(self, max_entries: int = 50, persist_path: str = None):
        self.entries: list[EpisodicMemoryEntry] = []
        self.max_entries = max_entries
        self._day_totals: dict = {}  # Track totals for current day
        self._current_day: int = 1
        self._persist_path: Path | None = (
            Path(persist_path) if persist_path
            else Path(self.DEFAULT_PERSIST_PATH)
        )
        self._load_from_disk()

    def get_time_label(self, timestamp: datetime) -> str:
        """Generate time label based on hour of day"""
        hour = timestamp.hour

        if 5 <= hour < 8:
            return "EARLY MORNING CHECK"
        elif 8 <= hour < 12:
            return "MORNING UPDATE"
        elif 12 <= hour < 14:
            return "MID-DAY UPDATE"
        elif 14 <= hour < 17:
            return "AFTERNOON CHECK"
        elif 17 <= hour < 20:
            return "EVENING MONITORING"
        elif 20 <= hour < 23:
            return "NIGHT CHECK"
        else:
            return "LATE NIGHT MONITORING"

    def store(
        self,
        grow_day: int,
        conditions: dict,
        actions_taken: list[str],
        observations: list[str],
        next_actions: list[str],
        timestamp: Optional[datetime] = None,
    ) -> EpisodicMemoryEntry:
        """
        Store a new episodic memory entry.

        Args:
            grow_day: Current grow day number
            conditions: Environmental conditions dict
            actions_taken: List of actions taken (e.g., ["water:200ml"])
            observations: Key observations from this cycle
            next_actions: Planned actions for next cycle
            timestamp: Override timestamp (defaults to now)

        Returns:
            The created memory entry
        """
        timestamp = timestamp or datetime.now()

        # Reset day totals if new day
        if grow_day != self._current_day:
            self._day_totals = {}
            self._current_day = grow_day

        # Update day totals from actions
        for action in actions_taken:
            self._update_day_totals(action)
        # Auto-score importance based on what happened (Pattern #17)
        importance = 0.4  # Baseline for status-only checks
        if actions_taken:
            importance = 0.7  # Actions were taken → more memorable
            for a in actions_taken:
                if a.startswith("water:") or a.startswith("light:"):
                    importance = 0.8  # Actuator actions are high-importance
                    break
        if observations:
            importance = max(importance, 0.6)
            # Anomalous observations get boosted
            for obs in observations:
                obs_lower = obs.lower() if isinstance(obs, str) else ""
                if any(kw in obs_lower for kw in ("warning", "concern", "high", "low", "stress", "anomal")):
                    importance = max(importance, 0.9)
                    break

        entry = EpisodicMemoryEntry(
            timestamp=timestamp,
            grow_day=grow_day,
            time_label=self.get_time_label(timestamp),
            conditions=conditions,
            actions_taken=actions_taken,
            observations=observations,
            next_actions=next_actions,
            day_totals=self._day_totals.copy(),
            importance=importance,
        )

        self.entries.append(entry)

        # Apply decay to all existing memories before trimming
        self.decay_all()

        # Trim: keep max_entries, but prefer high-importance memories
        if len(self.entries) > self.max_entries:
            # Sort by importance, keep the most important
            self.entries.sort(key=lambda e: e.importance)
            # Always keep the newest 5 regardless of importance
            newest = self.entries[-5:]
            rest = self.entries[:-5]
            rest.sort(key=lambda e: e.importance)
            # Drop the lowest-importance entries
            keep_count = self.max_entries - len(newest)
            kept = rest[-keep_count:] if keep_count > 0 else []
            self.entries = sorted(kept + newest, key=lambda e: e.timestamp)

        # Persist to disk so memories survive restarts
        self._save_to_disk()

        return entry

    def _update_day_totals(self, action: str):
        """Update cumulative totals from action string"""
        # Parse action format: "water:200ml", "co2:inject"
        if ":" in action:
            action_type, value = action.split(":", 1)

            if action_type == "water":
                # Extract ml value
                try:
                    ml = int(value.replace("ml", ""))
                    self._day_totals["water_ml"] = self._day_totals.get("water_ml", 0) + ml
                except ValueError:
                    pass

            elif action_type == "co2":
                self._day_totals["co2_injections"] = self._day_totals.get("co2_injections", 0) + 1

            elif action_type == "light":
                # Track light changes
                self._day_totals["light_changes"] = self._day_totals.get("light_changes", 0) + 1

    def get_recent(self, count: int = 5) -> list[EpisodicMemoryEntry]:
        """Get most recent memory entries"""
        return self.entries[-count:]

    def get_today(self) -> list[EpisodicMemoryEntry]:
        """Get all memories from today"""
        today = datetime.now().date()
        return [e for e in self.entries if e.timestamp.date() == today]

    def get_by_day(self, grow_day: int) -> list[EpisodicMemoryEntry]:
        """Get all memories for a specific grow day"""
        return [e for e in self.entries if e.grow_day == grow_day]

    def decay_all(self):
        """Apply time-based decay to all memories (Pattern #17).

        Called automatically on every store(). Each memory's importance
        decays exponentially based on hours since creation.
        """
        now = datetime.now()
        for entry in self.entries:
            hours_elapsed = (now - entry.timestamp).total_seconds() / 3600
            if hours_elapsed > 0:
                entry.decay(hours_elapsed)

    def consolidate(self, min_importance: float = 0.05) -> int:
        """Remove memories that have decayed below the importance threshold.

        Returns the number of memories pruned. Call periodically (e.g. daily)
        to keep the memory store lean.
        """
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.importance >= min_importance]
        pruned = before - len(self.entries)
        if pruned > 0:
            logger.info(f"Memory consolidation: pruned {pruned} weak memories")
            self._save_to_disk()
        return pruned

    def get_most_important(self, count: int = 5) -> list[EpisodicMemoryEntry]:
        """Get the most important memories regardless of recency."""
        sorted_entries = sorted(self.entries, key=lambda e: e.importance, reverse=True)
        return sorted_entries[:count]

    def format_context(self, count: int = 3) -> str:
        """
        Format memories as context for AI injection.

        Selects a mix of recent + important memories, reinforces them
        on access, and includes feedback analysis.
        """
        if not self.entries:
            return "No previous memories recorded yet."

        # Get recent memories
        recent = self.get_recent(min(count, len(self.entries)))

        # Also pull in high-importance memories not already in recent
        important = self.get_most_important(count)
        recent_timestamps = {e.timestamp for e in recent}
        extra_important = [e for e in important if e.timestamp not in recent_timestamps][:2]

        selected = list(recent) + extra_important

        # Reinforce all retrieved memories (Pattern #17 — accessed = reinforced)
        for entry in selected:
            entry.reinforce(boost=0.05)

        context_parts = ["## Recent Activity Log\n"]

        for entry in selected:
            importance_marker = ""
            if entry.importance >= 0.8:
                importance_marker = " ⚡"
            elif entry.importance >= 0.6:
                importance_marker = " ●"
            context_parts.append(f"[importance: {entry.importance:.2f}{importance_marker}]")
            context_parts.append(entry.format_for_display())
            context_parts.append("\n---\n")

        # Add feedback analysis if we have enough data
        feedback = self.analyze_action_outcomes()
        if feedback:
            context_parts.append("\n## Learning from Past Actions\n")
            context_parts.append(feedback)

        # Auto-save after reinforcement updates
        self._save_to_disk()

        return "\n".join(context_parts)

    def analyze_action_outcomes(self) -> str:
        """
        Analyze action→outcome patterns from episodic memory.

        Compares conditions BEFORE an action to conditions in the NEXT entry
        to measure actual effect vs expected effect.
        """
        if len(self.entries) < 3:
            return ""

        insights = []

        # Look at watering outcomes
        watering_outcomes = []
        for i in range(len(self.entries) - 1):
            curr = self.entries[i]
            next_entry = self.entries[i + 1]

            # Check if watering happened this cycle
            watered_ml = 0
            for action in curr.actions_taken:
                if action.startswith("water:"):
                    try:
                        watered_ml = int(action.split(":")[1].replace("ml", ""))
                    except (ValueError, IndexError):
                        pass

            if watered_ml > 0:
                soil_before = curr.conditions.get("soil_moisture")
                soil_after = next_entry.conditions.get("soil_moisture")

                if soil_before is not None and soil_after is not None:
                    # Handle dict or scalar soil moisture
                    if isinstance(soil_before, dict):
                        soil_before = soil_before.get("avg", soil_before.get("probe1"))
                    if isinstance(soil_after, dict):
                        soil_after = soil_after.get("avg", soil_after.get("probe1"))

                    if soil_before is not None and soil_after is not None:
                        change = soil_after - soil_before
                        watering_outcomes.append({
                            "ml": watered_ml,
                            "soil_before": soil_before,
                            "soil_after": soil_after,
                            "change": change,
                            "time_gap_hrs": (next_entry.timestamp - curr.timestamp).total_seconds() / 3600,
                        })

        if watering_outcomes:
            avg_change = sum(w["change"] for w in watering_outcomes) / len(watering_outcomes)
            avg_ml = sum(w["ml"] for w in watering_outcomes) / len(watering_outcomes)
            insights.append(
                f"WATERING FEEDBACK: {len(watering_outcomes)} watering events tracked. "
                f"Average {avg_ml:.0f}ml produced {avg_change:+.1f}% soil moisture change. "
                f"{'Effective' if avg_change > 3 else 'Consider increasing volume' if avg_change < 1 else 'Marginal effect'}."
            )

            # Check for over/under watering patterns
            if any(w["soil_after"] > 70 for w in watering_outcomes):
                insights.append("WARNING: Some waterings pushed soil above 70% - reduce volume.")
            if any(w["change"] < 0 for w in watering_outcomes):
                insights.append("NOTE: Soil dried between waterings faster than added - substrate draining quickly.")

        # Analyze VPD trends
        vpds = [e.conditions.get("vpd") for e in self.entries[-10:] if e.conditions.get("vpd")]
        if len(vpds) >= 3:
            avg_vpd = sum(vpds) / len(vpds)
            trend = vpds[-1] - vpds[0]
            insights.append(
                f"VPD TREND: Average {avg_vpd:.2f} kPa over last {len(vpds)} readings. "
                f"{'Rising' if trend > 0.1 else 'Falling' if trend < -0.1 else 'Stable'} "
                f"({trend:+.2f} kPa)."
            )

        return "\n".join(insights) if insights else ""

    def get_day_summary(self, grow_day: Optional[int] = None) -> dict:
        """
        Get summary statistics for a grow day.

        Returns cumulative totals and key events.
        """
        day = grow_day or self._current_day
        day_entries = self.get_by_day(day)

        if not day_entries:
            return {"grow_day": day, "entries": 0}

        # Aggregate actions
        all_actions = []
        for entry in day_entries:
            all_actions.extend(entry.actions_taken)

        # Get latest totals
        latest = day_entries[-1]

        return {
            "grow_day": day,
            "entries": len(day_entries),
            "first_check": day_entries[0].timestamp.isoformat(),
            "last_check": latest.timestamp.isoformat(),
            "totals": latest.day_totals,
            "all_actions": all_actions,
        }

    def to_json(self) -> str:
        """Serialize entire memory to JSON"""
        return json.dumps({
            "entries": [e.to_dict() for e in self.entries],
            "day_totals": self._day_totals,
            "current_day": self._current_day,
        })

    @classmethod
    def from_json(cls, json_str: str, persist_path: str = None) -> "EpisodicMemory":
        """Deserialize memory from JSON"""
        data = json.loads(json_str)
        memory = cls.__new__(cls)
        memory.entries = [EpisodicMemoryEntry.from_dict(e) for e in data["entries"]]
        memory._day_totals = data.get("day_totals", {})
        memory._current_day = data.get("current_day", 1)
        memory.max_entries = 50
        memory._persist_path = Path(persist_path) if persist_path else None
        return memory

    # =========================================================================
    # Disk persistence — memories survive process restarts
    # =========================================================================

    def _load_from_disk(self):
        """Load memories from JSON file on disk (called during __init__)."""
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            data = json.loads(self._persist_path.read_text())
            self.entries = [
                EpisodicMemoryEntry.from_dict(e)
                for e in data.get("entries", [])
            ]
            self._day_totals = data.get("day_totals", {})
            self._current_day = data.get("current_day", 1)
            logger.info(
                "episodic_memory_loaded",
                extra={"entries": len(self.entries), "path": str(self._persist_path)},
            )
        except Exception as exc:
            logger.warning(
                "episodic_memory_load_failed",
                extra={"error": str(exc), "path": str(self._persist_path)},
            )

    def _save_to_disk(self):
        """Persist current memories to JSON file on disk."""
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entries": [e.to_dict() for e in self.entries],
                "day_totals": self._day_totals,
                "current_day": self._current_day,
            }
            self._persist_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as exc:
            logger.warning(
                "episodic_memory_save_failed",
                extra={"error": str(exc), "path": str(self._persist_path)},
            )


# =============================================================================
# Helper functions for common memory operations
# =============================================================================

def create_memory_entry(
    grow_day: int,
    sensor_data: dict,
    ai_decision: dict,
    actions_executed: list[dict],
) -> EpisodicMemoryEntry:
    """
    Create a memory entry from agent decision cycle data.

    Args:
        grow_day: Current grow day
        sensor_data: Raw sensor readings
        ai_decision: Grok's decision output
        actions_executed: List of executed action dicts

    Returns:
        Formatted EpisodicMemoryEntry
    """
    # Build conditions dict
    conditions = {
        "temp_c": sensor_data.get("environment", {}).get("temperature_c"),
        "temp_f": sensor_data.get("environment", {}).get("temperature_f"),
        "humidity": sensor_data.get("environment", {}).get("humidity_percent"),
        "vpd": sensor_data.get("environment", {}).get("vpd_kpa"),
        "co2": sensor_data.get("environment", {}).get("co2_ppm"),
    }

    # Add soil moisture if available
    substrate = sensor_data.get("substrate", {})
    if substrate:
        conditions["soil_moisture"] = {
            "probe1": substrate.get("moisture_probe1"),
            "probe2": substrate.get("moisture_probe2"),
            "avg": substrate.get("moisture_percent"),
        }

    # Format actions taken
    actions_taken = []
    for action in actions_executed:
        tool = action.get("tool", "unknown")
        params = action.get("parameters", {})

        if tool == "trigger_irrigation":
            ml = params.get("amount_ml", 200)
            actions_taken.append(f"water:{ml}ml")
        elif tool == "inject_co2":
            actions_taken.append("co2:inject")
        elif "light" in tool:
            state = "on" if params.get("state", True) else "off"
            actions_taken.append(f"light:{state}")
        elif "exhaust" in tool or "fan" in tool:
            speed = params.get("speed_percent", 50)
            actions_taken.append(f"exhaust:{speed}%")
        else:
            actions_taken.append(f"{tool}:{json.dumps(params)}")

    # Extract observations from AI decision
    observations = ai_decision.get("analysis", {}).get("observations", [])

    # Generate next actions based on concerns
    next_actions = []
    concerns = ai_decision.get("analysis", {}).get("concerns", [])
    recommendations = ai_decision.get("recommendations", [])

    # Default next actions
    next_actions.append("Read sensors")

    for rec in recommendations[:2]:
        next_actions.append(rec)

    for concern in concerns[:2]:
        if "humidity" in concern.lower():
            next_actions.append("If RH > 65% → exhaust ON")
        elif "moisture" in concern.lower() or "water" in concern.lower():
            next_actions.append("If soil moisture < threshold → water")
        elif "temperature" in concern.lower():
            next_actions.append("Monitor temperature trends")

    memory = EpisodicMemory()
    return memory.store(
        grow_day=grow_day,
        conditions=conditions,
        actions_taken=actions_taken,
        observations=observations,
        next_actions=next_actions,
    )
