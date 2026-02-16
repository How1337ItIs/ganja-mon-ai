"""
Review Engine
=============
Main orchestrator that fetches data, runs analyzers, and produces reviews.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from src.db.models import ReviewType, GrowReview
from src.db.repository import GrowRepository
from src.cultivation.stages import (
    StageParameters,
    get_stage_parameters,
    GrowthStage,
)

from .analyzers import (
    ComplianceAnalyzer,
    DecisionQualityAnalyzer,
    PatternDetector,
    OptimizationSuggester,
)
from .renderer import ReviewRenderer
from .visual import VisualAnalyzer


@dataclass
class ReviewResult:
    """Complete review result before DB persistence."""

    review_type: ReviewType
    period_start: datetime
    period_end: datetime
    growth_stage: str
    grow_day_start: int
    grow_day_end: int
    overall_score: float
    compliance_score: float
    stability_score: float
    decision_quality_score: float
    data_quality_score: float
    visual_analysis: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    report_markdown: str = ""
    summary: str = ""
    issues_found: int = 0
    optimizations_suggested: int = 0


class ReviewEngine:
    """
    Orchestrates all analyzers and produces a ReviewResult.

    Usage:
        engine = ReviewEngine(repo)
        result = await engine.generate_review(review_type=ReviewType.DAILY)
    """

    # Score weights
    WEIGHT_COMPLIANCE = 0.40
    WEIGHT_STABILITY = 0.25
    WEIGHT_DECISIONS = 0.20
    WEIGHT_DATA_QUALITY = 0.15

    def __init__(self, repo: GrowRepository):
        self.repo = repo
        self.compliance = ComplianceAnalyzer()
        self.decisions = DecisionQualityAnalyzer()
        self.patterns = PatternDetector()
        self.optimizer = OptimizationSuggester()
        self.visual = VisualAnalyzer()
        self.renderer = ReviewRenderer()

    async def generate_review(
        self,
        review_type: ReviewType = ReviewType.DAILY,
        hours: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[int] = None,
    ) -> ReviewResult:
        """Generate a complete grow review."""
        # 1. Resolve time window
        start, end = self._resolve_time_window(review_type, hours, start_time, end_time)

        # 2. Get grow session info
        session = await self.repo.get_active_session()
        if session is None:
            return self._empty_result(review_type, start, end, "No active grow session")

        if session_id is None:
            session_id = session.id

        stage_name = (
            session.current_stage.value
            if hasattr(session.current_stage, "value")
            else str(session.current_stage)
        )
        grow_day = session.current_day or 1
        strain = session.strain_name or "Unknown"

        # Map DB stage to cultivation stage for parameter lookup
        try:
            stage_params = get_stage_parameters(stage_name)
        except (ValueError, KeyError):
            stage_params = get_stage_parameters("vegetative")

        # 3. Fetch all data
        readings = await self.repo.get_sensor_readings_range(start, end, session_id)
        ai_decisions = await self.repo.get_decisions_range(start, end, session_id)
        watering_preds = await self.repo.get_watering_predictions_range(start, end, session_id)

        # Collect all actions from decisions
        all_actions = []
        for d in ai_decisions:
            all_actions.extend(d.actions or [])

        # Estimate day range
        if review_type == ReviewType.DAILY:
            day_start = grow_day
            day_end = grow_day
        elif review_type == ReviewType.WEEKLY:
            day_start = max(1, grow_day - 6)
            day_end = grow_day
        else:
            period_days = max(1, int((end - start).total_seconds() / 86400))
            day_start = max(1, grow_day - period_days + 1)
            day_end = grow_day

        # 4. Run analyzers
        compliance_result = self.compliance.analyze(readings, stage_params, stage_name)
        decision_result = self.decisions.analyze(ai_decisions, readings, stage_params)
        pattern_result = self.patterns.analyze(readings, all_actions, watering_preds)

        # 4b. Mine historical vision analyses for recurring visual issues
        visual_result = await self.visual.mine_historical_vision(
            ai_decisions, max_recent=20
        )

        suggestions = self.optimizer.suggest(
            compliance_result, decision_result, pattern_result,
            stage_params, stage_name,
        )

        # Add visual-based suggestions
        for vi in visual_result.get("recurring_issues", []):
            if vi["severity"] in ("warning", "critical"):
                suggestions.append({
                    "category": "visual",
                    "priority": "high" if vi["severity"] == "critical" else "medium",
                    "title": f"Recurring visual issue: {vi['category']}",
                    "action": f"Investigate {vi['category']} — mentioned in {vi['mention_count']}/{visual_result['decisions_analyzed']} recent decisions",
                    "rationale": f"Visual analysis flagged {vi['category']} in {vi['frequency_pct']}% of recent decision cycles",
                })
        # Re-sort suggestions by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s.get("priority", "low"), 3))

        # 5. Compute scores
        compliance_score = max(0, compliance_result.get("overall_compliance_score", -1))
        decision_quality_score = max(0, decision_result.get("decision_quality_score", -1))
        data_quality = pattern_result.get("data_quality", {})
        data_quality_score = max(0, data_quality.get("data_quality_score", 0))

        # Stability score from VPD/temp std deviations
        stability_score = self._compute_stability_score(compliance_result)

        overall = self._compute_overall_score(
            compliance_score, stability_score, decision_quality_score, data_quality_score,
        )

        # 6. Render markdown
        report = self.renderer.render(
            review_type=review_type.value,
            period_start=start,
            period_end=end,
            stage_name=stage_name,
            grow_day_start=day_start,
            grow_day_end=day_end,
            strain=strain,
            compliance=compliance_result,
            decision_quality=decision_result,
            patterns=pattern_result,
            suggestions=suggestions,
            overall_score=overall,
            compliance_score=compliance_score,
            stability_score=stability_score,
            decision_quality_score=decision_quality_score,
            data_quality_score=data_quality_score,
            visual=visual_result,
        )

        summary = self.renderer.generate_summary(
            overall, compliance_result,
            pattern_result.get("issues", []),
            suggestions,
        )

        # 7. Build result
        results_json = {
            "compliance": compliance_result,
            "decision_quality": decision_result,
            "patterns": pattern_result,
            "visual": visual_result,
            "suggestions": suggestions,
        }

        total_issues = (
            len(pattern_result.get("issues", []))
            + len(visual_result.get("recurring_issues", []))
        )

        return ReviewResult(
            review_type=review_type,
            period_start=start,
            period_end=end,
            growth_stage=stage_name,
            grow_day_start=day_start,
            grow_day_end=day_end,
            overall_score=overall,
            compliance_score=compliance_score,
            stability_score=stability_score,
            decision_quality_score=decision_quality_score,
            data_quality_score=data_quality_score,
            visual_analysis=visual_result,
            results=results_json,
            report_markdown=report,
            summary=summary,
            issues_found=total_issues,
            optimizations_suggested=len(suggestions),
        )

    async def store_review(self, result: ReviewResult, session_id: int) -> GrowReview:
        """Persist ReviewResult to the database."""
        review_data = {
            "session_id": session_id,
            "review_type": result.review_type,
            "period_start": result.period_start,
            "period_end": result.period_end,
            "growth_stage": result.growth_stage,
            "grow_day_start": result.grow_day_start,
            "grow_day_end": result.grow_day_end,
            "overall_score": result.overall_score,
            "compliance_score": result.compliance_score,
            "stability_score": result.stability_score,
            "decision_quality_score": result.decision_quality_score,
            "data_quality_score": result.data_quality_score,
            "results_json": result.results,
            "report_markdown": result.report_markdown,
            "summary": result.summary,
            "issues_found": result.issues_found,
            "optimizations_suggested": result.optimizations_suggested,
        }
        return await self.repo.store_review(review_data)

    def format_for_ai_context(self, result: ReviewResult, max_lines: int = 15) -> str:
        """Format review findings as a compact context block for AI injection."""
        lines = [
            f"[REVIEW] {result.review_type.value.title()} review — Score: {result.overall_score:.0f}/100",
            f"Period: {result.period_start:%m/%d %H:%M} to {result.period_end:%m/%d %H:%M}",
        ]

        # Add top issues
        issues = result.results.get("patterns", {}).get("issues", [])
        if issues:
            lines.append("Issues:")
            for issue in issues[:3]:
                lines.append(f"  - [{issue['severity'].upper()}] {issue['description']}")

        # Add recurring visual issues
        visual = result.results.get("visual", {})
        recurring = visual.get("recurring_issues", [])
        if recurring:
            lines.append("Recurring visual issues:")
            for vi in recurring[:3]:
                lines.append(
                    f"  - {vi['category']}: seen in {vi['mention_count']}/"
                    f"{visual.get('decisions_analyzed', '?')} recent cycles"
                )

        # Add top suggestions
        suggestions = result.results.get("suggestions", [])
        if suggestions:
            lines.append("Suggestions:")
            for s in suggestions[:3]:
                lines.append(f"  - [{s['priority'].upper()}] {s['title']}: {s['action']}")

        # Add worst compliance metric
        compliance = result.results.get("compliance", {})
        worst_grade = "A"
        worst_metric = None
        for key in ["temperature", "humidity", "vpd", "co2", "soil_moisture"]:
            m = compliance.get(key, {})
            if m.get("insufficient_data"):
                continue
            g = m.get("grade", "A")
            if g > worst_grade:  # F > D > C > B > A alphabetically
                worst_grade = g
                worst_metric = key

        if worst_metric and worst_grade in ("D", "F"):
            m = compliance[worst_metric]
            lines.append(
                f"Worst metric: {worst_metric} — {m['avg']}{m.get('unit', '')} "
                f"({m['time_in_range_pct']}% in range, grade {m['grade']})"
            )

        return "\n".join(lines[:max_lines])

    def format_for_ai_context_from_dict(self, review_dict: dict) -> str:
        """Format from a review dict (from repository) instead of ReviewResult."""
        results = review_dict.get("results_json", {})
        lines = [
            f"[REVIEW] {review_dict['review_type'].title()} — Score: {review_dict['overall_score']:.0f}/100",
        ]

        issues = results.get("patterns", {}).get("issues", [])
        if issues:
            lines.append("Issues:")
            for issue in issues[:3]:
                lines.append(f"  - [{issue['severity'].upper()}] {issue['description']}")

        suggestions = results.get("suggestions", [])
        if suggestions:
            lines.append("Suggestions:")
            for s in suggestions[:3]:
                lines.append(f"  - [{s['priority'].upper()}] {s['title']}: {s['action']}")

        return "\n".join(lines)

    def _resolve_time_window(
        self,
        review_type: ReviewType,
        hours: Optional[int],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> tuple[datetime, datetime]:
        now = datetime.now()

        if start_time and end_time:
            return start_time, end_time

        if hours:
            return now - timedelta(hours=hours), now

        if review_type == ReviewType.DAILY:
            return now - timedelta(hours=24), now
        elif review_type == ReviewType.WEEKLY:
            return now - timedelta(days=7), now
        else:
            return now - timedelta(hours=24), now

    def _compute_stability_score(self, compliance: dict) -> float:
        """Derive stability from metric standard deviations."""
        if compliance.get("insufficient_data"):
            return 0

        stds = []
        # Lower std relative to the range = more stable
        for key, range_size in [
            ("temperature", 15),   # typical 15F range
            ("humidity", 20),      # typical 20% range
            ("vpd", 0.5),         # typical 0.5 kPa range
        ]:
            m = compliance.get(key, {})
            if m.get("insufficient_data") or "std" not in m:
                continue
            # Normalize: std of 0 = 100, std >= range_size = 0
            normalized = max(0, 100 * (1 - m["std"] / range_size))
            stds.append(normalized)

        return round(sum(stds) / len(stds), 1) if stds else 0

    def _compute_overall_score(
        self,
        compliance: float,
        stability: float,
        decisions: float,
        data_quality: float,
    ) -> float:
        """Weighted average of component scores."""
        # If a score is -1 (insufficient data), redistribute weight
        components = []
        weights = []

        if compliance >= 0:
            components.append(compliance)
            weights.append(self.WEIGHT_COMPLIANCE)
        if stability >= 0:
            components.append(stability)
            weights.append(self.WEIGHT_STABILITY)
        if decisions >= 0:
            components.append(decisions)
            weights.append(self.WEIGHT_DECISIONS)
        if data_quality >= 0:
            components.append(data_quality)
            weights.append(self.WEIGHT_DATA_QUALITY)

        if not weights:
            return 0

        # Normalize weights to sum to 1
        total_weight = sum(weights)
        return round(
            sum(c * w / total_weight for c, w in zip(components, weights)), 1
        )

    def _empty_result(
        self, review_type: ReviewType, start: datetime, end: datetime, reason: str
    ) -> ReviewResult:
        return ReviewResult(
            review_type=review_type,
            period_start=start,
            period_end=end,
            growth_stage="unknown",
            grow_day_start=0,
            grow_day_end=0,
            overall_score=0,
            compliance_score=0,
            stability_score=0,
            decision_quality_score=0,
            data_quality_score=0,
            results={"error": reason},
            report_markdown=f"# Review Failed\n\n{reason}",
            summary=reason,
        )
