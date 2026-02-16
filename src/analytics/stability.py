"""
Stability Metrics Calculator
============================
Calculate environmental control quality metrics.

Based on SmartGrow DataControl's Jupyter notebook analysis:
- Standard deviation from ideal (stability indicator)
- Coefficient of variation
- Time in range percentages
- Outlier filtering

Example from SmartGrow:
    ideal_ec = 900
    deviation_ratio = df_ec['_value'].std() / ideal_ec  # 0.085 = good stability

Usage:
    # From raw lists
    calculator = StabilityCalculator()
    report = calculator.calculate(vpd_vals, temp_vals, hum_vals, start, end)

    # From sensor reading dicts
    report = calculate_stability_metrics(readings)

    # From database (last 24h)
    report = await StabilityCalculator.compute(hours=24)
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Sequence

from src.hardware.sensors import filter_vpd_outliers

logger = logging.getLogger(__name__)


@dataclass
class MetricStats:
    """Statistical summary for a single metric"""
    mean: float
    std: float
    min: float
    max: float
    count: int
    valid_count: int  # After outlier filtering
    in_range_percent: float  # % of readings within target range


@dataclass
class StabilityReport:
    """Complete stability report for a time window"""
    window_start: datetime
    window_end: datetime
    window_hours: int

    # Per-metric stats
    vpd: MetricStats
    temperature: MetricStats
    humidity: MetricStats

    # Targets used for comparison
    vpd_target: float
    temp_target: float
    humidity_target: float

    # Derived metrics
    vpd_deviation_ratio: float  # std / target (lower = better)
    overall_score: float  # 0-100

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/JSON"""
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "window_hours": self.window_hours,
            "vpd_mean": self.vpd.mean,
            "vpd_std": self.vpd.std,
            "vpd_min": self.vpd.min,
            "vpd_max": self.vpd.max,
            "vpd_in_range_percent": self.vpd.in_range_percent,
            "vpd_target": self.vpd_target,
            "vpd_deviation_ratio": self.vpd_deviation_ratio,
            "temp_mean": self.temperature.mean,
            "temp_std": self.temperature.std,
            "temp_in_range_percent": self.temperature.in_range_percent,
            "humidity_mean": self.humidity.mean,
            "humidity_std": self.humidity.std,
            "humidity_in_range_percent": self.humidity.in_range_percent,
            "overall_score": self.overall_score,
            "sample_count": self.vpd.count,
            "valid_sample_count": self.vpd.valid_count,
        }


class StabilityCalculator:
    """
    Calculate stability metrics for environmental control.

    Uses statistical analysis to measure how well the system
    maintains target conditions over time.
    """

    def __init__(
        self,
        vpd_target: float = 1.0,
        vpd_range: tuple[float, float] = (0.8, 1.2),
        temp_target: float = 77.0,
        temp_range: tuple[float, float] = (72.0, 82.0),
        humidity_target: float = 55.0,
        humidity_range: tuple[float, float] = (45.0, 65.0),
    ):
        """
        Initialize calculator with target values.

        Args:
            vpd_target: Target VPD in kPa
            vpd_range: Acceptable VPD range (min, max)
            temp_target: Target temperature in F
            temp_range: Acceptable temp range (min, max)
            humidity_target: Target humidity %
            humidity_range: Acceptable humidity range (min, max)
        """
        self.vpd_target = vpd_target
        self.vpd_range = vpd_range
        self.temp_target = temp_target
        self.temp_range = temp_range
        self.humidity_target = humidity_target
        self.humidity_range = humidity_range

    def _calculate_stats(
        self,
        values: list[float],
        target_range: tuple[float, float],
        filter_outliers: bool = True,
        outlier_min: Optional[float] = None,
        outlier_max: Optional[float] = None,
    ) -> MetricStats:
        """Calculate statistics for a list of values"""
        original_count = len(values)

        # Filter outliers if requested
        if filter_outliers and outlier_min is not None and outlier_max is not None:
            values = [v for v in values if outlier_min < v <= outlier_max]

        valid_count = len(values)

        if not values:
            return MetricStats(
                mean=0, std=0, min=0, max=0,
                count=original_count, valid_count=0,
                in_range_percent=0,
            )

        # Calculate basic stats
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        min_val = min(values)
        max_val = max(values)

        # Calculate % in range
        in_range = sum(1 for v in values if target_range[0] <= v <= target_range[1])
        in_range_percent = (in_range / len(values)) * 100 if values else 0

        return MetricStats(
            mean=round(mean_val, 3),
            std=round(std_val, 3),
            min=round(min_val, 3),
            max=round(max_val, 3),
            count=original_count,
            valid_count=valid_count,
            in_range_percent=round(in_range_percent, 1),
        )

    def _calculate_overall_score(
        self,
        vpd_stats: MetricStats,
        temp_stats: MetricStats,
        humidity_stats: MetricStats,
    ) -> float:
        """
        Calculate overall stability score (0-100).

        Weights:
        - VPD: 40% (most important for plant health)
        - Temperature: 35%
        - Humidity: 25%

        Score based on:
        - % time in range (primary)
        - Deviation from target (secondary)
        """
        # Weighted in-range percentages
        weighted_in_range = (
            vpd_stats.in_range_percent * 0.4 +
            temp_stats.in_range_percent * 0.35 +
            humidity_stats.in_range_percent * 0.25
        )

        # Penalty for high standard deviation
        # Lower std = less penalty
        vpd_deviation_penalty = min(20, (vpd_stats.std / self.vpd_target) * 50) if self.vpd_target else 0
        temp_deviation_penalty = min(10, (temp_stats.std / 10) * 10)  # Normalize by 10°F
        humidity_deviation_penalty = min(10, (humidity_stats.std / 20) * 10)  # Normalize by 20%

        total_penalty = vpd_deviation_penalty + temp_deviation_penalty + humidity_deviation_penalty

        score = max(0, weighted_in_range - total_penalty)
        return round(score, 1)

    @classmethod
    async def compute(
        cls,
        hours: int = 24,
        vpd_target: float = 1.0,
        vpd_range: tuple[float, float] = (0.8, 1.2),
        temp_target: float = 77.0,
        temp_range: tuple[float, float] = (72.0, 82.0),
        humidity_target: float = 55.0,
        humidity_range: tuple[float, float] = (45.0, 65.0),
    ) -> "StabilityReport":
        """
        Pull sensor readings from the DB for the last *hours* and compute
        a StabilityReport.

        This is the high-level entry point -- it handles the DB query,
        data extraction, and delegates to ``calculate()``.

        Args:
            hours: How many hours of history to analyse (default 24)
            *_target / *_range: forwarded to the calculator

        Returns:
            StabilityReport with 0-100 overall stability score
        """
        from src.db.connection import get_db_session
        from src.db.repository import GrowRepository

        now = datetime.utcnow()
        window_start = now - timedelta(hours=hours)

        async with get_db_session() as session:
            repo = GrowRepository(session)
            readings = await repo.get_sensors_history(hours=hours)

        if not readings:
            logger.warning("No sensor readings found for stability computation")
            return StabilityReport(
                window_start=window_start,
                window_end=now,
                window_hours=hours,
                vpd=MetricStats(0, 0, 0, 0, 0, 0, 0),
                temperature=MetricStats(0, 0, 0, 0, 0, 0, 0),
                humidity=MetricStats(0, 0, 0, 0, 0, 0, 0),
                vpd_target=vpd_target,
                temp_target=temp_target,
                humidity_target=humidity_target,
                vpd_deviation_ratio=0,
                overall_score=0,
            )

        # Extract per-metric lists.
        # DB stores air_temp in Celsius -- convert to Fahrenheit for consistency.
        vpd_values = [
            r["vpd"] for r in readings if r.get("vpd") is not None
        ]
        temp_values_f = [
            r["air_temp"] * 9 / 5 + 32
            for r in readings
            if r.get("air_temp") is not None
        ]
        humidity_values = [
            r["humidity"] for r in readings if r.get("humidity") is not None
        ]

        calculator = cls(
            vpd_target=vpd_target,
            vpd_range=vpd_range,
            temp_target=temp_target,
            temp_range=temp_range,
            humidity_target=humidity_target,
            humidity_range=humidity_range,
        )

        return calculator.calculate(
            vpd_readings=vpd_values,
            temp_readings=temp_values_f,
            humidity_readings=humidity_values,
            window_start=window_start,
            window_end=now,
        )

    def calculate(
        self,
        vpd_readings: list[float],
        temp_readings: list[float],
        humidity_readings: list[float],
        window_start: datetime,
        window_end: datetime,
    ) -> StabilityReport:
        """
        Calculate stability metrics for a time window.

        Args:
            vpd_readings: List of VPD values
            temp_readings: List of temperature values (F)
            humidity_readings: List of humidity values (%)
            window_start: Start of time window
            window_end: End of time window

        Returns:
            StabilityReport with all metrics
        """
        # Calculate stats for each metric
        vpd_stats = self._calculate_stats(
            vpd_readings,
            self.vpd_range,
            filter_outliers=True,
            outlier_min=0.0,
            outlier_max=3.5,
        )

        temp_stats = self._calculate_stats(
            temp_readings,
            self.temp_range,
            filter_outliers=True,
            outlier_min=32.0,  # Freezing
            outlier_max=120.0,  # Way too hot
        )

        humidity_stats = self._calculate_stats(
            humidity_readings,
            self.humidity_range,
            filter_outliers=True,
            outlier_min=0.0,
            outlier_max=100.0,
        )

        # Calculate VPD deviation ratio (SmartGrow pattern)
        vpd_deviation_ratio = (
            vpd_stats.std / self.vpd_target if self.vpd_target else 0
        )

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            vpd_stats, temp_stats, humidity_stats
        )

        # Calculate window hours
        window_hours = int((window_end - window_start).total_seconds() / 3600)

        return StabilityReport(
            window_start=window_start,
            window_end=window_end,
            window_hours=window_hours,
            vpd=vpd_stats,
            temperature=temp_stats,
            humidity=humidity_stats,
            vpd_target=self.vpd_target,
            temp_target=self.temp_target,
            humidity_target=self.humidity_target,
            vpd_deviation_ratio=round(vpd_deviation_ratio, 4),
            overall_score=overall_score,
        )


def calculate_stability_metrics(
    sensor_readings: Sequence[dict],
    vpd_target: float = 1.0,
    vpd_range: tuple[float, float] = (0.8, 1.2),
    temp_target: float = 77.0,
    temp_range: tuple[float, float] = (72.0, 82.0),
    humidity_target: float = 55.0,
    humidity_range: tuple[float, float] = (45.0, 65.0),
) -> StabilityReport:
    """
    Convenience function to calculate stability from sensor reading dicts.

    Args:
        sensor_readings: List of sensor reading dictionaries with keys:
            - timestamp: datetime
            - vpd: float
            - air_temp: float (Celsius, will be converted to F)
            - humidity: float
        *_target: Target values
        *_range: Acceptable ranges

    Returns:
        StabilityReport
    """
    if not sensor_readings:
        now = datetime.now()
        return StabilityReport(
            window_start=now,
            window_end=now,
            window_hours=0,
            vpd=MetricStats(0, 0, 0, 0, 0, 0, 0),
            temperature=MetricStats(0, 0, 0, 0, 0, 0, 0),
            humidity=MetricStats(0, 0, 0, 0, 0, 0, 0),
            vpd_target=vpd_target,
            temp_target=temp_target,
            humidity_target=humidity_target,
            vpd_deviation_ratio=0,
            overall_score=0,
        )

    # Extract values
    vpd_values = [r.get("vpd", 0) for r in sensor_readings if r.get("vpd") is not None]
    temp_values_c = [r.get("air_temp", 0) for r in sensor_readings if r.get("air_temp") is not None]
    temp_values_f = [t * 9/5 + 32 for t in temp_values_c]  # Convert to F
    humidity_values = [r.get("humidity", 0) for r in sensor_readings if r.get("humidity") is not None]

    # Get time window
    timestamps = [r.get("timestamp") for r in sensor_readings if r.get("timestamp")]
    if timestamps:
        window_start = min(timestamps)
        window_end = max(timestamps)
    else:
        window_start = window_end = datetime.now()

    calculator = StabilityCalculator(
        vpd_target=vpd_target,
        vpd_range=vpd_range,
        temp_target=temp_target,
        temp_range=temp_range,
        humidity_target=humidity_target,
        humidity_range=humidity_range,
    )

    return calculator.calculate(
        vpd_readings=vpd_values,
        temp_readings=temp_values_f,
        humidity_readings=humidity_values,
        window_start=window_start,
        window_end=window_end,
    )


def interpret_stability_score(score: float) -> str:
    """
    Interpret a stability score into a human-readable assessment.

    Args:
        score: Stability score (0-100)

    Returns:
        String description of control quality
    """
    if score >= 90:
        return "Excellent - Near-perfect environmental control"
    elif score >= 80:
        return "Good - Minor fluctuations, plant is thriving"
    elif score >= 70:
        return "Acceptable - Some variation, monitor closely"
    elif score >= 60:
        return "Fair - Noticeable swings, consider adjustments"
    elif score >= 50:
        return "Poor - Significant instability, action needed"
    else:
        return "Critical - Major control issues, immediate attention required"
