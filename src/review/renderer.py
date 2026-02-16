"""
Review Renderer
===============
Produces human-readable markdown reports from analysis results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _score_emoji(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


class ReviewRenderer:
    """Renders review results into a markdown report."""

    def render(
        self,
        review_type: str,
        period_start: datetime,
        period_end: datetime,
        stage_name: str,
        grow_day_start: int,
        grow_day_end: int,
        strain: str,
        compliance: dict[str, Any],
        decision_quality: dict[str, Any],
        patterns: dict[str, Any],
        suggestions: list[dict[str, Any]],
        overall_score: float,
        compliance_score: float,
        stability_score: float,
        decision_quality_score: float,
        data_quality_score: float,
        visual: dict[str, Any] | None = None,
    ) -> str:
        lines: list[str] = []

        # Header
        lines.append(f"# Grow Review: {review_type.title()}")
        lines.append("")
        lines.append(f"**Period:** {period_start:%Y-%m-%d %H:%M} to {period_end:%Y-%m-%d %H:%M}")
        lines.append(f"**Strain:** {strain}")
        lines.append(f"**Stage:** {stage_name} (Days {grow_day_start}-{grow_day_end})")
        lines.append(f"**Generated:** {datetime.now():%Y-%m-%d %H:%M}")
        lines.append("")

        # Overall score
        grade = _score_emoji(overall_score)
        lines.append(f"## Overall Score: {overall_score:.0f}/100 ({grade})")
        lines.append("")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")
        lines.append(f"| Environmental Compliance | {compliance_score:.0f}/100 |")
        lines.append(f"| Stability | {stability_score:.0f}/100 |")
        lines.append(f"| Decision Quality | {decision_quality_score:.0f}/100 |")
        lines.append(f"| Data Quality | {data_quality_score:.0f}/100 |")
        lines.append("")

        # Environmental compliance
        lines.append("## Environmental Compliance")
        lines.append("")
        if compliance.get("insufficient_data"):
            lines.append(
                f"*Insufficient data ({compliance.get('reading_count', 0)} readings)*"
            )
        else:
            lines.append("| Metric | Avg | Target Range | Optimal | In Range | Grade |")
            lines.append("|--------|-----|--------------|---------|----------|-------|")
            for key in ["temperature", "humidity", "vpd", "co2", "soil_moisture"]:
                m = compliance.get(key, {})
                if m.get("insufficient_data"):
                    lines.append(f"| {key.replace('_', ' ').title()} | - | - | - | insufficient data | - |")
                    continue
                lines.append(
                    f"| {key.replace('_', ' ').title()} "
                    f"| {m['avg']}{m.get('unit', '')} "
                    f"| {m['target_min']}-{m['target_max']} "
                    f"| {m['optimal']} "
                    f"| {m['time_in_range_pct']}% "
                    f"| {m['grade']} |"
                )
        lines.append("")

        # Decision quality
        lines.append("## Decision Quality")
        lines.append("")
        if decision_quality.get("insufficient_data"):
            lines.append("*No AI decisions in this period.*")
        else:
            lines.append(f"- **Decisions:** {decision_quality['total_decisions']}")
            lines.append(f"- **Actions evaluated:** {decision_quality['evaluated_actions']}")
            lines.append(
                f"- **Effective:** {decision_quality['effective']} | "
                f"**Neutral:** {decision_quality['neutral']} | "
                f"**Counterproductive:** {decision_quality['counterproductive']} | "
                f"**Unnecessary:** {decision_quality['unnecessary']}"
            )
            missed = decision_quality.get("missed_opportunities", 0)
            if missed > 0:
                lines.append(f"- **Missed opportunities:** {missed}")
        lines.append("")

        # Visual analysis
        lines.append("## Visual Analysis")
        lines.append("")
        if visual and visual.get("decisions_analyzed", 0) > 0:
            lines.append(
                f"Analyzed vision data from {visual['decisions_analyzed']} recent decision cycles."
            )
            healthy_pct = visual.get("healthy_mention_pct", 0)
            lines.append(f"- **Healthy mentions:** {healthy_pct}% of cycles")
            recurring = visual.get("recurring_issues", [])
            if recurring:
                lines.append("")
                lines.append("**Recurring visual issues:**")
                lines.append("")
                lines.append("| Issue | Frequency | Severity |")
                lines.append("|-------|-----------|----------|")
                for vi in recurring:
                    lines.append(
                        f"| {vi['category'].replace('_', ' ').title()} "
                        f"| {vi['mention_count']}/{visual['decisions_analyzed']} "
                        f"({vi['frequency_pct']}%) "
                        f"| {vi['severity'].upper()} |"
                    )
            else:
                lines.append("- No recurring visual issues detected.")
        else:
            lines.append("*No vision data available for this period.*")
        lines.append("")

        # Pattern analysis
        lines.append("## Issues Detected")
        lines.append("")
        issues = patterns.get("issues", [])
        if not issues:
            lines.append("No issues detected.")
        else:
            for issue in issues:
                sev = issue["severity"].upper()
                lines.append(f"- **[{sev}]** {issue['description']}")
        lines.append("")

        # Optimization suggestions
        lines.append("## Optimization Suggestions")
        lines.append("")
        if not suggestions:
            lines.append("No suggestions — environment is well-managed.")
        else:
            for s in suggestions:
                prio = s["priority"].upper()
                lines.append(f"### [{prio}] {s['title']}")
                lines.append("")
                lines.append(f"**Action:** {s['action']}")
                lines.append(f"**Rationale:** {s['rationale']}")
                lines.append("")

        # Data quality
        dq = patterns.get("data_quality", {})
        lines.append("## Data Quality")
        lines.append("")
        lines.append(f"- **Readings:** {dq.get('total_readings', 0)}/{dq.get('expected_readings', '?')}")
        lines.append(f"- **Coverage:** {dq.get('coverage_pct', 0)}%")
        lines.append(f"- **Gaps:** {dq.get('gap_count', 0)}")
        lines.append("")

        return "\n".join(lines)

    def generate_summary(
        self,
        overall_score: float,
        compliance: dict[str, Any],
        issues: list[dict[str, Any]],
        suggestions: list[dict[str, Any]],
    ) -> str:
        """One-line summary for quick display."""
        grade = _score_emoji(overall_score)
        issue_count = len(issues)
        suggestion_count = len(suggestions)

        high_priority = sum(1 for s in suggestions if s.get("priority") == "high")

        parts = [f"Score: {overall_score:.0f}/100 ({grade})"]

        if issue_count > 0:
            parts.append(f"{issue_count} issue{'s' if issue_count != 1 else ''}")
        else:
            parts.append("no issues")

        if high_priority > 0:
            parts.append(f"{high_priority} high-priority suggestion{'s' if high_priority != 1 else ''}")
        elif suggestion_count > 0:
            parts.append(f"{suggestion_count} suggestion{'s' if suggestion_count != 1 else ''}")

        return " | ".join(parts)
