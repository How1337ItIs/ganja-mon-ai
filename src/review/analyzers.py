"""
Review Analyzers
================
Four analyzer classes that consume raw data and produce structured findings.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from src.db.models import SensorReading, AIDecision, ActionLog, ActionType, WateringPrediction
from src.cultivation.stages import StageParameters


def _c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def _grade(pct: float) -> str:
    if pct >= 95:
        return "A"
    if pct >= 85:
        return "B"
    if pct >= 75:
        return "C"
    if pct >= 60:
        return "D"
    return "F"


def _grade_to_numeric(g: str) -> float:
    return {"A": 95, "B": 87, "C": 77, "D": 65, "F": 40}.get(g, 50)


# Action type -> which sensor metric(s) it should affect
ACTION_METRIC_MAP: dict[str, list[str]] = {
    ActionType.WATER.value: ["soil_moisture"],
    ActionType.CO2_INJECT.value: ["co2"],
    ActionType.EXHAUST_ON.value: ["temperature", "humidity"],
    ActionType.EXHAUST_OFF.value: ["temperature", "humidity"],
    ActionType.FAN_ON.value: ["temperature"],
    ActionType.FAN_OFF.value: ["temperature"],
    ActionType.HUMIDIFIER_ON.value: ["humidity"],
    ActionType.HUMIDIFIER_OFF.value: ["humidity"],
    ActionType.DEHUMIDIFIER_ON.value: ["humidity"],
    ActionType.DEHUMIDIFIER_OFF.value: ["humidity"],
    ActionType.HEAT_ON.value: ["temperature"],
    ActionType.HEAT_OFF.value: ["temperature"],
    ActionType.LIGHT_ON.value: [],
    ActionType.LIGHT_OFF.value: [],
    ActionType.CAMERA_CAPTURE.value: [],
    ActionType.STAGE_TRANSITION.value: [],
}


class ComplianceAnalyzer:
    """Checks environmental metrics against stage-appropriate targets."""

    MIN_READINGS = 10

    def analyze(
        self,
        readings: list[SensorReading],
        stage_params: StageParameters,
        stage_name: str,
    ) -> dict[str, Any]:
        if len(readings) < self.MIN_READINGS:
            return {
                "insufficient_data": True,
                "reading_count": len(readings),
                "overall_compliance_score": -1,
            }

        metrics = self._analyze_all_metrics(readings, stage_params)
        scores = [
            _grade_to_numeric(m["grade"])
            for m in metrics.values()
            if not m.get("insufficient_data")
        ]
        metrics["overall_compliance_score"] = (
            round(statistics.mean(scores), 1) if scores else -1
        )
        metrics["reading_count"] = len(readings)
        metrics["stage"] = stage_name
        return metrics

    def _analyze_all_metrics(
        self, readings: list[SensorReading], p: StageParameters
    ) -> dict[str, Any]:
        results = {}

        # Temperature (C->F conversion)
        temps_f = [_c_to_f(r.air_temp) for r in readings if r.air_temp is not None]
        if len(temps_f) >= self.MIN_READINGS:
            results["temperature"] = self._score_metric(
                temps_f, p.temp_min_f, p.temp_max_f, p.temp_optimal_f,
                near_threshold=3.0, unit="F",
                timestamps=[r.timestamp for r in readings if r.air_temp is not None],
            )
        else:
            results["temperature"] = {"insufficient_data": True, "count": len(temps_f)}

        # Humidity
        hums = [r.humidity for r in readings if r.humidity is not None]
        if len(hums) >= self.MIN_READINGS:
            results["humidity"] = self._score_metric(
                hums, p.humidity_min, p.humidity_max, p.humidity_optimal,
                near_threshold=5.0, unit="%",
                timestamps=[r.timestamp for r in readings if r.humidity is not None],
            )
        else:
            results["humidity"] = {"insufficient_data": True, "count": len(hums)}

        # VPD
        vpds = [r.vpd for r in readings if r.vpd is not None]
        if len(vpds) >= self.MIN_READINGS:
            results["vpd"] = self._score_metric(
                vpds, p.vpd_min, p.vpd_max, p.vpd_optimal,
                near_threshold=0.15, unit="kPa",
                timestamps=[r.timestamp for r in readings if r.vpd is not None],
            )
        else:
            results["vpd"] = {"insufficient_data": True, "count": len(vpds)}

        # CO2
        co2s = [r.co2 for r in readings if r.co2 is not None]
        if len(co2s) >= self.MIN_READINGS:
            results["co2"] = self._score_metric(
                co2s, p.co2_min, p.co2_max, p.co2_optimal,
                near_threshold=100, unit="ppm",
                timestamps=[r.timestamp for r in readings if r.co2 is not None],
            )
        else:
            results["co2"] = {"insufficient_data": True, "count": len(co2s)}

        # Soil moisture
        soils = [r.soil_moisture for r in readings if r.soil_moisture is not None]
        if len(soils) >= self.MIN_READINGS:
            results["soil_moisture"] = self._score_metric(
                soils, p.soil_moisture_min, p.soil_moisture_max, p.soil_moisture_optimal,
                near_threshold=10.0, unit="%",
                timestamps=[r.timestamp for r in readings if r.soil_moisture is not None],
            )
        else:
            results["soil_moisture"] = {"insufficient_data": True, "count": len(soils)}

        return results

    def _score_metric(
        self,
        values: list[float],
        target_min: float,
        target_max: float,
        optimal: float,
        near_threshold: float,
        unit: str,
        timestamps: list[datetime],
    ) -> dict[str, Any]:
        n = len(values)
        in_range = sum(1 for v in values if target_min <= v <= target_max)
        near_optimal = sum(1 for v in values if abs(v - optimal) <= near_threshold)
        deviations = [abs(v - optimal) for v in values]

        # Find worst period
        worst_idx = max(range(n), key=lambda i: deviations[i])

        pct_in_range = round(in_range / n * 100, 1)
        return {
            "avg": round(statistics.mean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "std": round(statistics.stdev(values), 2) if n > 1 else 0,
            "optimal": optimal,
            "target_min": target_min,
            "target_max": target_max,
            "time_in_range_pct": pct_in_range,
            "time_optimal_pct": round(near_optimal / n * 100, 1),
            "avg_deviation": round(statistics.mean(deviations), 2),
            "max_deviation": round(max(deviations), 2),
            "worst_period": timestamps[worst_idx].isoformat() if timestamps else None,
            "grade": _grade(pct_in_range),
            "count": n,
            "unit": unit,
        }


class DecisionQualityAnalyzer:
    """Evaluates whether AI decisions improved conditions."""

    AFTER_WINDOW_MIN = 30   # minutes after action to check
    AFTER_WINDOW_MAX = 120  # max minutes after action

    def analyze(
        self,
        decisions: list[AIDecision],
        readings: list[SensorReading],
        stage_params: StageParameters,
    ) -> dict[str, Any]:
        if not decisions:
            return {
                "total_decisions": 0,
                "total_actions": 0,
                "decision_quality_score": -1,
                "insufficient_data": True,
            }

        all_actions = []
        for d in decisions:
            for a in (d.actions or []):
                all_actions.append(a)

        action_details = []
        effective = neutral = counterproductive = unnecessary = 0

        for action in all_actions:
            action_type_val = (
                action.action_type.value
                if hasattr(action.action_type, "value")
                else action.action_type
            )
            target_metrics = ACTION_METRIC_MAP.get(action_type_val, [])
            if not target_metrics:
                continue

            detail = self._evaluate_action(
                action, target_metrics, readings, stage_params
            )
            action_details.append(detail)

            v = detail["verdict"]
            if v == "effective":
                effective += 1
            elif v == "counterproductive":
                counterproductive += 1
            elif v == "unnecessary":
                unnecessary += 1
            else:
                neutral += 1

        total_evaluated = len(action_details)
        if total_evaluated > 0:
            score = round(
                (effective * 100 + neutral * 50) / total_evaluated
                - counterproductive * 10
                - unnecessary * 5,
                1,
            )
            score = max(0, min(100, score))
        else:
            score = -1

        # Detect missed opportunities
        missed = self._detect_missed_opportunities(
            decisions, readings, stage_params
        )

        return {
            "total_decisions": len(decisions),
            "total_actions": len(all_actions),
            "evaluated_actions": total_evaluated,
            "effective": effective,
            "neutral": neutral,
            "counterproductive": counterproductive,
            "unnecessary": unnecessary,
            "missed_opportunities": len(missed),
            "missed_details": missed[:5],
            "action_details": action_details[:20],
            "decision_quality_score": score,
        }

    def _evaluate_action(
        self,
        action: ActionLog,
        target_metrics: list[str],
        readings: list[SensorReading],
        stage_params: StageParameters,
    ) -> dict[str, Any]:
        action_time = action.timestamp or action.execution_time
        if not action_time:
            return self._action_detail(action, "unknown", "No timestamp")

        # Get reading closest before the action
        before = self._find_reading_near(readings, action_time, before=True)
        # Get reading 30-120min after
        after_start = action_time + timedelta(minutes=self.AFTER_WINDOW_MIN)
        after_end = action_time + timedelta(minutes=self.AFTER_WINDOW_MAX)
        after = self._find_reading_in_window(readings, after_start, after_end)

        if not before or not after:
            return self._action_detail(action, "neutral", "Insufficient before/after data")

        verdicts = []
        for metric_name in target_metrics:
            before_val, after_val, target = self._get_metric_values(
                before, after, metric_name, stage_params
            )
            if before_val is None or after_val is None or target is None:
                continue

            before_dist = abs(before_val - target)
            after_dist = abs(after_val - target)

            if before_dist < 0.01 * target:  # already at target
                verdicts.append("unnecessary")
            elif after_dist < before_dist:
                verdicts.append("effective")
            elif after_dist > before_dist * 1.1:  # >10% worse
                verdicts.append("counterproductive")
            else:
                verdicts.append("neutral")

        if not verdicts:
            final = "neutral"
        elif "effective" in verdicts:
            final = "effective"
        elif "counterproductive" in verdicts and "effective" not in verdicts:
            final = "counterproductive"
        elif "unnecessary" in verdicts and len(set(verdicts)) == 1:
            final = "unnecessary"
        else:
            final = "neutral"

        return self._action_detail(action, final, f"Metrics: {target_metrics}")

    def _detect_missed_opportunities(
        self,
        decisions: list[AIDecision],
        readings: list[SensorReading],
        stage_params: StageParameters,
    ) -> list[dict[str, Any]]:
        """Find periods where a metric was out-of-range for >30min with no action."""
        if len(readings) < 2:
            return []

        missed = []
        # Check for extended out-of-range periods
        out_of_range_start: dict[str, datetime | None] = {
            "temperature": None,
            "humidity": None,
            "vpd": None,
        }

        action_times = set()
        for d in decisions:
            for a in (d.actions or []):
                if a.timestamp:
                    action_times.add(a.timestamp)

        for r in readings:
            checks = {
                "temperature": (
                    _c_to_f(r.air_temp) if r.air_temp is not None else None,
                    stage_params.temp_min_f,
                    stage_params.temp_max_f,
                ),
                "humidity": (
                    r.humidity,
                    stage_params.humidity_min,
                    stage_params.humidity_max,
                ),
                "vpd": (
                    r.vpd,
                    stage_params.vpd_min,
                    stage_params.vpd_max,
                ),
            }

            for metric, (val, lo, hi) in checks.items():
                if val is None:
                    continue
                if val < lo or val > hi:
                    if out_of_range_start[metric] is None:
                        out_of_range_start[metric] = r.timestamp
                else:
                    if out_of_range_start[metric] is not None:
                        duration = (r.timestamp - out_of_range_start[metric]).total_seconds() / 60
                        if duration > 30:
                            # Check if any action was taken during this window
                            had_action = any(
                                out_of_range_start[metric] <= t <= r.timestamp
                                for t in action_times
                            )
                            if not had_action:
                                missed.append({
                                    "metric": metric,
                                    "start": out_of_range_start[metric].isoformat(),
                                    "end": r.timestamp.isoformat(),
                                    "duration_minutes": round(duration, 1),
                                })
                    out_of_range_start[metric] = None

        return missed

    def _find_reading_near(
        self, readings: list[SensorReading], ts: datetime, before: bool
    ) -> SensorReading | None:
        best = None
        best_dist = timedelta(hours=2)
        for r in readings:
            delta = ts - r.timestamp if before else r.timestamp - ts
            if delta >= timedelta(0) and delta < best_dist:
                best = r
                best_dist = delta
        return best

    def _find_reading_in_window(
        self, readings: list[SensorReading], start: datetime, end: datetime
    ) -> SensorReading | None:
        for r in readings:
            if start <= r.timestamp <= end:
                return r
        return None

    def _get_metric_values(
        self,
        before: SensorReading,
        after: SensorReading,
        metric: str,
        p: StageParameters,
    ) -> tuple[float | None, float | None, float | None]:
        if metric == "temperature":
            bv = _c_to_f(before.air_temp) if before.air_temp is not None else None
            av = _c_to_f(after.air_temp) if after.air_temp is not None else None
            return bv, av, p.temp_optimal_f
        if metric == "humidity":
            return before.humidity, after.humidity, p.humidity_optimal
        if metric == "vpd":
            return before.vpd, after.vpd, p.vpd_optimal
        if metric == "soil_moisture":
            return before.soil_moisture, after.soil_moisture, p.soil_moisture_optimal
        if metric == "co2":
            return before.co2, after.co2, float(p.co2_optimal)
        return None, None, None

    def _action_detail(
        self, action: ActionLog, verdict: str, notes: str
    ) -> dict[str, Any]:
        return {
            "timestamp": action.timestamp.isoformat() if action.timestamp else None,
            "action_type": (
                action.action_type.value
                if hasattr(action.action_type, "value")
                else action.action_type
            ),
            "verdict": verdict,
            "notes": notes,
        }


class PatternDetector:
    """Detects problematic patterns in sensor and action data."""

    def analyze(
        self,
        readings: list[SensorReading],
        actions: list[ActionLog],
        watering_predictions: list[WateringPrediction],
    ) -> dict[str, Any]:
        issues: list[dict[str, Any]] = []

        if len(readings) >= 10:
            issues.extend(self._detect_vpd_instability(readings))
            issues.extend(self._detect_temp_swings(readings))
            issues.extend(self._detect_humidity_spikes(readings))

        if actions:
            issues.extend(self._detect_overcorrection(actions))

        data_quality = self._assess_data_quality(readings)

        watering_accuracy = None
        if watering_predictions:
            verified = [
                p for p in watering_predictions
                if p.accuracy_pct is not None
            ]
            if verified:
                watering_accuracy = round(
                    statistics.mean(p.accuracy_pct for p in verified), 1
                )
                if watering_accuracy < 70:
                    issues.append({
                        "type": "watering_prediction_inaccuracy",
                        "severity": "warning",
                        "description": (
                            f"Watering predictions averaging {watering_accuracy}% accuracy "
                            f"({len(verified)} verified)"
                        ),
                        "details": {"accuracy_pct": watering_accuracy, "count": len(verified)},
                    })

        return {
            "issues": issues,
            "data_quality": data_quality,
            "watering_prediction_accuracy": watering_accuracy,
        }

    def _detect_vpd_instability(self, readings: list[SensorReading]) -> list[dict]:
        """Flag 2-hour windows where VPD std deviation > 0.2 kPa."""
        issues = []
        vpd_vals = [(r.timestamp, r.vpd) for r in readings if r.vpd is not None]
        if len(vpd_vals) < 4:
            return issues

        window = timedelta(hours=2)
        flagged_windows = []
        i = 0
        while i < len(vpd_vals):
            window_start = vpd_vals[i][0]
            window_end = window_start + window
            window_vals = [
                v for ts, v in vpd_vals if window_start <= ts < window_end
            ]
            if len(window_vals) >= 3:
                std = statistics.stdev(window_vals)
                if std > 0.2:
                    flagged_windows.append({
                        "start": window_start.isoformat(),
                        "std": round(std, 3),
                    })
            # Advance by roughly half a window
            next_i = i + max(1, len(window_vals) // 2)
            if next_i == i:
                next_i = i + 1
            i = next_i

        if flagged_windows:
            sev = "info" if len(flagged_windows) <= 2 else (
                "warning" if len(flagged_windows) <= 5 else "critical"
            )
            issues.append({
                "type": "vpd_instability",
                "severity": sev,
                "description": (
                    f"VPD std deviation >0.2 kPa in {len(flagged_windows)} "
                    f"2-hour windows"
                ),
                "details": {
                    "windows": flagged_windows[:5],
                    "avg_std": round(
                        statistics.mean(w["std"] for w in flagged_windows), 3
                    ),
                },
            })
        return issues

    def _detect_temp_swings(self, readings: list[SensorReading]) -> list[dict]:
        """Flag 1-hour windows with temp delta > 5F."""
        issues = []
        temps = [
            (r.timestamp, _c_to_f(r.air_temp))
            for r in readings
            if r.air_temp is not None
        ]
        if len(temps) < 3:
            return issues

        window = timedelta(hours=1)
        worst_swing = 0.0
        worst_period = None
        swing_count = 0

        i = 0
        while i < len(temps):
            window_start = temps[i][0]
            window_end = window_start + window
            window_vals = [
                v for ts, v in temps if window_start <= ts < window_end
            ]
            if len(window_vals) >= 2:
                delta = max(window_vals) - min(window_vals)
                if delta > 5:
                    swing_count += 1
                    if delta > worst_swing:
                        worst_swing = delta
                        worst_period = window_start.isoformat()
            next_i = i + max(1, len(window_vals) // 2)
            if next_i == i:
                next_i = i + 1
            i = next_i

        if swing_count > 0:
            issues.append({
                "type": "temperature_swing",
                "severity": "warning" if worst_swing < 10 else "critical",
                "description": (
                    f"Temperature swings >5F detected in {swing_count} "
                    f"1-hour windows (worst: {worst_swing:.1f}F)"
                ),
                "details": {
                    "worst_swing_f": round(worst_swing, 1),
                    "worst_period": worst_period,
                    "window_count": swing_count,
                },
            })
        return issues

    def _detect_humidity_spikes(self, readings: list[SensorReading]) -> list[dict]:
        """Flag >15% humidity increase in any 30-min window."""
        issues = []
        hums = [(r.timestamp, r.humidity) for r in readings if r.humidity is not None]
        if len(hums) < 3:
            return issues

        spike_count = 0
        worst_spike = 0.0
        for i in range(len(hums)):
            for j in range(i + 1, len(hums)):
                delta_t = (hums[j][0] - hums[i][0]).total_seconds()
                if delta_t > 1800:  # > 30 min
                    break
                increase = hums[j][1] - hums[i][1]
                if increase > 15:
                    spike_count += 1
                    worst_spike = max(worst_spike, increase)
                    break  # one per starting point

        if spike_count > 0:
            issues.append({
                "type": "humidity_spike",
                "severity": "warning",
                "description": (
                    f"Humidity spikes >15% in 30min detected "
                    f"({spike_count} occurrences, worst: +{worst_spike:.1f}%)"
                ),
                "details": {"count": spike_count, "worst_increase_pct": round(worst_spike, 1)},
            })
        return issues

    def _detect_overcorrection(self, actions: list[ActionLog]) -> list[dict]:
        """Find ON->OFF->ON or OFF->ON->OFF cycles within 60min for same device."""
        issues = []
        by_device: dict[str, list[ActionLog]] = defaultdict(list)
        for a in actions:
            at = a.action_type.value if hasattr(a.action_type, "value") else a.action_type
            # Group by device root (e.g. exhaust_on and exhaust_off -> exhaust)
            device = at.replace("_on", "").replace("_off", "")
            by_device[device].append(a)

        for device, device_actions in by_device.items():
            if len(device_actions) < 3:
                continue
            device_actions.sort(key=lambda a: a.timestamp or datetime.min)
            cycle_count = 0
            for i in range(len(device_actions) - 2):
                a1, a2, a3 = device_actions[i], device_actions[i + 1], device_actions[i + 2]
                if not (a1.timestamp and a3.timestamp):
                    continue
                delta = (a3.timestamp - a1.timestamp).total_seconds() / 60
                if delta <= 60:
                    cycle_count += 1

            if cycle_count > 0:
                issues.append({
                    "type": "overcorrection_cycle",
                    "severity": "warning",
                    "description": (
                        f"{device}: toggled 3+ times within 60min "
                        f"({cycle_count} cycles) — possible hunting/oscillation"
                    ),
                    "details": {"device": device, "cycles": cycle_count},
                })
        return issues

    def _assess_data_quality(self, readings: list[SensorReading]) -> dict[str, Any]:
        """Assess sensor data coverage and gaps."""
        if not readings:
            return {
                "total_readings": 0,
                "coverage_pct": 0,
                "gaps": [],
                "data_quality_score": 0,
            }

        sorted_r = sorted(readings, key=lambda r: r.timestamp)
        total = len(sorted_r)

        # Detect gaps (>30 min between consecutive readings)
        gaps = []
        for i in range(1, len(sorted_r)):
            delta = (sorted_r[i].timestamp - sorted_r[i - 1].timestamp).total_seconds()
            if delta > 1800:
                gaps.append({
                    "start": sorted_r[i - 1].timestamp.isoformat(),
                    "end": sorted_r[i].timestamp.isoformat(),
                    "duration_minutes": round(delta / 60, 1),
                })

        # Estimate expected readings (assume ~5 min interval)
        period = (sorted_r[-1].timestamp - sorted_r[0].timestamp).total_seconds()
        expected = max(1, period / 300)  # 5-min intervals
        coverage = min(100, round(total / expected * 100, 1))

        score = max(0, coverage - len(gaps) * 2)

        return {
            "total_readings": total,
            "expected_readings": round(expected),
            "coverage_pct": coverage,
            "gaps": gaps[:10],
            "gap_count": len(gaps),
            "data_quality_score": round(score, 1),
        }


class OptimizationSuggester:
    """Generates specific optimization suggestions from analysis results."""

    def suggest(
        self,
        compliance: dict[str, Any],
        decision_quality: dict[str, Any],
        patterns: dict[str, Any],
        stage_params: StageParameters,
        stage_name: str,
    ) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []

        if not compliance.get("insufficient_data"):
            suggestions.extend(self._from_compliance(compliance, stage_params, stage_name))

        if not decision_quality.get("insufficient_data"):
            suggestions.extend(self._from_decisions(decision_quality))

        suggestions.extend(self._from_patterns(patterns))

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s.get("priority", "low"), 3))

        return suggestions

    def _from_compliance(
        self,
        compliance: dict,
        p: StageParameters,
        stage: str,
    ) -> list[dict]:
        suggestions = []

        # VPD analysis
        vpd = compliance.get("vpd", {})
        if not vpd.get("insufficient_data") and vpd.get("grade") in ("D", "F"):
            avg_vpd = vpd["avg"]
            if avg_vpd > p.vpd_optimal:
                delta_needed = round(avg_vpd - p.vpd_optimal, 2)
                suggestions.append({
                    "category": "environment",
                    "priority": "high",
                    "title": "VPD too high — raise humidity or lower temperature",
                    "action": (
                        f"Increase humidity target by ~5% or reduce temperature "
                        f"by ~2F to bring VPD closer to {p.vpd_optimal} kPa"
                    ),
                    "rationale": (
                        f"VPD averaged {avg_vpd} kPa vs optimal {p.vpd_optimal} kPa "
                        f"(only {vpd['time_in_range_pct']}% time in range)"
                    ),
                })
            else:
                suggestions.append({
                    "category": "environment",
                    "priority": "high",
                    "title": "VPD too low — decrease humidity or raise temperature",
                    "action": (
                        f"Decrease humidity target by ~5% or increase temperature "
                        f"to bring VPD closer to {p.vpd_optimal} kPa"
                    ),
                    "rationale": (
                        f"VPD averaged {avg_vpd} kPa vs optimal {p.vpd_optimal} kPa "
                        f"(only {vpd['time_in_range_pct']}% time in range)"
                    ),
                })

        # Temperature
        temp = compliance.get("temperature", {})
        if not temp.get("insufficient_data") and temp.get("grade") in ("D", "F"):
            avg_temp = temp["avg"]
            if avg_temp > p.temp_optimal_f:
                suggestions.append({
                    "category": "environment",
                    "priority": "high",
                    "title": "Temperature consistently above target",
                    "action": "Increase exhaust fan runtime or reduce light intensity",
                    "rationale": (
                        f"Temperature averaged {avg_temp:.1f}F vs optimal "
                        f"{p.temp_optimal_f}F ({temp['time_in_range_pct']}% in range)"
                    ),
                })
            else:
                suggestions.append({
                    "category": "environment",
                    "priority": "high",
                    "title": "Temperature consistently below target",
                    "action": "Check heat mat or increase light hours on",
                    "rationale": (
                        f"Temperature averaged {avg_temp:.1f}F vs optimal "
                        f"{p.temp_optimal_f}F ({temp['time_in_range_pct']}% in range)"
                    ),
                })

        # Humidity
        hum = compliance.get("humidity", {})
        if not hum.get("insufficient_data") and hum.get("grade") in ("D", "F"):
            avg_hum = hum["avg"]
            direction = "too high" if avg_hum > p.humidity_optimal else "too low"
            device = "dehumidifier/exhaust" if avg_hum > p.humidity_optimal else "humidifier"
            suggestions.append({
                "category": "environment",
                "priority": "medium",
                "title": f"Humidity {direction}",
                "action": f"Adjust {device} settings for {stage} stage",
                "rationale": (
                    f"Humidity averaged {avg_hum:.1f}% vs optimal "
                    f"{p.humidity_optimal}% ({hum['time_in_range_pct']}% in range)"
                ),
            })

        # Soil moisture
        soil = compliance.get("soil_moisture", {})
        if not soil.get("insufficient_data") and soil.get("grade") in ("D", "F"):
            avg_soil = soil["avg"]
            if avg_soil < p.soil_moisture_optimal:
                suggestions.append({
                    "category": "watering",
                    "priority": "high",
                    "title": "Soil moisture consistently below target",
                    "action": "Increase watering frequency or volume",
                    "rationale": (
                        f"Soil moisture averaged {avg_soil:.1f}% vs optimal "
                        f"{p.soil_moisture_optimal}% ({soil['time_in_range_pct']}% in range)"
                    ),
                })
            else:
                suggestions.append({
                    "category": "watering",
                    "priority": "medium",
                    "title": "Soil moisture consistently above target",
                    "action": "Reduce watering frequency — allow more dry-back",
                    "rationale": (
                        f"Soil moisture averaged {avg_soil:.1f}% vs optimal "
                        f"{p.soil_moisture_optimal}% ({soil['time_in_range_pct']}% in range)"
                    ),
                })

        return suggestions

    def _from_decisions(self, dq: dict) -> list[dict]:
        suggestions = []
        if dq.get("missed_opportunities", 0) > 2:
            suggestions.append({
                "category": "ai_behavior",
                "priority": "medium",
                "title": "Missed opportunities to correct out-of-range conditions",
                "action": "Reduce AI decision interval to respond faster to environmental changes",
                "rationale": (
                    f"{dq['missed_opportunities']} periods where metrics were out-of-range "
                    f">30min with no corrective action"
                ),
            })
        if dq.get("unnecessary", 0) > dq.get("evaluated_actions", 1) * 0.3:
            suggestions.append({
                "category": "ai_behavior",
                "priority": "low",
                "title": "Unnecessary actions taken while metrics were optimal",
                "action": "Widen dead-band / hysteresis before triggering actions",
                "rationale": (
                    f"{dq['unnecessary']} of {dq['evaluated_actions']} evaluated actions "
                    f"were taken when the target metric was already optimal"
                ),
            })
        return suggestions

    def _from_patterns(self, patterns: dict) -> list[dict]:
        suggestions = []
        for issue in patterns.get("issues", []):
            if issue["type"] == "overcorrection_cycle":
                suggestions.append({
                    "category": "ai_behavior",
                    "priority": "medium",
                    "title": f"Over-correction on {issue['details']['device']}",
                    "action": (
                        f"Add hysteresis band to {issue['details']['device']} "
                        f"control logic to prevent hunting"
                    ),
                    "rationale": issue["description"],
                })
            elif issue["type"] == "temperature_swing" and issue["severity"] == "critical":
                suggestions.append({
                    "category": "environment",
                    "priority": "high",
                    "title": "Severe temperature swings detected",
                    "action": "Check for drafts, insulate grow space, or add thermal mass",
                    "rationale": issue["description"],
                })

        dq = patterns.get("data_quality", {})
        if dq.get("gap_count", 0) > 3:
            suggestions.append({
                "category": "hardware",
                "priority": "medium",
                "title": "Frequent sensor data gaps",
                "action": "Check sensor connectivity, battery levels, and WiFi signal",
                "rationale": (
                    f"{dq['gap_count']} gaps detected "
                    f"(coverage: {dq.get('coverage_pct', 0)}%)"
                ),
            })

        return suggestions
