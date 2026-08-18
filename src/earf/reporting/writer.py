from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from .builder import format_timestamp
from .models import ReadinessReport


def _title_case_category(value: str) -> str:
    return value.replace("_", " ").title()


def _escape_markdown_table(value: object) -> str:
    return str(value).replace("|", "\\|")


class ReportWriter:
    def render_console(self, report: ReadinessReport) -> str:
        categories = sorted(
            report.readiness_score.category_scores.items(),
            key=lambda item: item[0].lower(),
        )
        rule_details = cast(
            list[dict[str, object]],
            report.metadata.get("rule_details", []),
        )
        not_applicable_rows = [
            row for row in rule_details if str(row.get("status", "")) == "NOT_APPLICABLE"
        ]
        passed_controls = cast(
            list[dict[str, object]],
            report.metadata.get("passed_controls", []),
        )
        core_detail = report.readiness_score.tier_details.get("core")
        advanced_detail = report.readiness_score.tier_details.get("advanced")
        coverage = report.readiness_score.assessment_coverage
        core_gaps = cast(
            list[dict[str, object]],
            report.metadata.get("core_gaps", []),
        )
        advanced_opportunities = cast(
            list[dict[str, object]],
            report.metadata.get("advanced_opportunities", []),
        )
        critical_blockers = [
            item for item in core_gaps if str(item.get("severity", "")).upper() == "CRITICAL"
        ]
        top_core_gaps = [
            item for item in core_gaps if str(item.get("severity", "")).upper() != "CRITICAL"
        ]
        high_priority_core_gap_count = sum(
            1 for item in top_core_gaps if str(item.get("severity", "")).upper() == "HIGH"
        )
        core_applicable_controls = (
            (core_detail.passed_rules + core_detail.failed_rules + core_detail.error_rules)
            if core_detail is not None
            else 0
        )

        category_width = max(
            (len(_title_case_category(category)) for category, _ in categories),
            default=0,
        )
        lines = [
            "EARF Enterprise AI Readiness Report",
            "",
            f"Repository: {report.repository_name}",
            f"Generated: {format_timestamp(report.generated_at)}",
            f"EARF Version: {report.earf_version}",
            "",
            "Overall Assessment",
            "",
            f"Core Readiness: {report.readiness_score.core_readiness_score:.1f} / 100",
            f"Advanced Controls: {report.readiness_score.advanced_controls_score:.1f} / 100",
            f"Assessment Coverage: {coverage.percentage:.1f}%",
            "",
            "Production Status",
            "",
            report.readiness_score.production_readiness.value,
            "",
            "Why?",
            "",
            f"{len(critical_blockers)} critical blockers",
            f"{high_priority_core_gap_count} high-priority core gaps",
            (
                f"{core_detail.passed_rules if core_detail else 0} of "
                f"{core_applicable_controls} applicable core controls passed"
            ),
            "",
            "Category Scores",
            "",
        ]

        for category, score in categories:
            lines.append(
                f"{_title_case_category(category):<{category_width}}  {score:>5.1f}"
            )

        lines.extend(["", "Critical Blockers", ""])
        if critical_blockers:
            for finding in critical_blockers:
                self._append_console_finding(lines, finding)
        else:
            lines.append("None")

        lines.extend(["", "Top Core Gaps", ""])
        if top_core_gaps:
            for finding in top_core_gaps:
                self._append_console_finding(lines, finding)
        else:
            lines.append("None")

        lines.extend(["", "Advanced Opportunities", ""])
        if advanced_opportunities:
            for finding in advanced_opportunities:
                self._append_console_finding(lines, finding, action_label="Opportunity")
        else:
            lines.append("None")

        lines.extend(["", "Passed Controls", ""])
        if passed_controls:
            for item in passed_controls:
                rule_id = str(item.get("rule_id", ""))
                title = str(item.get("title", ""))
                lines.append(f"PASS {rule_id} - {title}")
        else:
            lines.append("None")

        lines.extend(["", "Not Applicable", ""])
        if not_applicable_rows:
            for row in not_applicable_rows:
                rule_id = str(row.get("rule_id", ""))
                title = str(row.get("title", ""))
                reason = str(row.get("applicability_reason", "")).strip()
                lines.append(f"N/A {rule_id} - {title}")
                lines.append(f"Reason: {reason or 'Applicability evidence was not detected.'}")
                lines.append("")
        else:
            lines.append("None")

        lines.extend(
            [
                "",
                "Summary",
                "",
                (
                    f"Core: {core_detail.passed_rules if core_detail else 0} passed / "
                    f"{core_detail.failed_rules if core_detail else 0} failed"
                ),
                (
                    f"Advanced: {advanced_detail.passed_rules if advanced_detail else 0} passed / "
                    f"{advanced_detail.failed_rules if advanced_detail else 0} opportunities"
                ),
                f"N/A: {report.readiness_score.not_applicable_rules}",
            ]
        )

        return "\n".join(lines)

    def render_json(self, report: ReadinessReport) -> str:
        return json.dumps(self._json_payload(report), indent=2, ensure_ascii=False)

    def render_markdown(self, report: ReadinessReport) -> str:
        categories = sorted(
            report.readiness_score.category_scores.items(),
            key=lambda item: item[0].lower(),
        )
        rule_details = cast(
            list[dict[str, object]],
            report.metadata.get("rule_details", []),
        )
        core_gaps = cast(list[dict[str, object]], report.metadata.get("core_gaps", []))
        advanced_opportunities = cast(
            list[dict[str, object]],
            report.metadata.get("advanced_opportunities", []),
        )
        passed_controls = cast(
            list[dict[str, object]],
            report.metadata.get("passed_controls", []),
        )
        recommendations = cast(
            list[dict[str, str]],
            report.metadata.get("recommendations", []),
        )
        not_applicable_rows = [
            row for row in rule_details if str(row.get("status", "")) == "NOT_APPLICABLE"
        ]
        critical_blockers = [
            item for item in core_gaps if str(item.get("severity", "")).upper() == "CRITICAL"
        ]
        top_core_gaps = [
            item for item in core_gaps if str(item.get("severity", "")).upper() != "CRITICAL"
        ]
        high_priority_core_gap_count = sum(
            1 for item in top_core_gaps if str(item.get("severity", "")).upper() == "HIGH"
        )
        core_detail = report.readiness_score.tier_details.get("core")
        core_applicable_controls = (
            (core_detail.passed_rules + core_detail.failed_rules + core_detail.error_rules)
            if core_detail is not None
            else 0
        )

        lines = [
            "# EARF Enterprise AI Readiness Report",
            "",
            f"Repository: {report.repository_name}",
            f"Generated: {format_timestamp(report.generated_at)}",
            f"EARF Version: {report.earf_version}",
            f"Total Evidence: {report.total_evidence}",
            "",
            "## Overall Assessment",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            f"| Core Readiness | {report.readiness_score.core_readiness_score:.1f} / 100 |",
            f"| Advanced Controls | {report.readiness_score.advanced_controls_score:.1f} / 100 |",
            (
                "| Assessment Coverage | "
                f"{report.readiness_score.assessment_coverage.percentage:.1f}% "
                f"({report.readiness_score.assessment_coverage.evaluated}/"
                f"{report.readiness_score.assessment_coverage.applicable}) |"
            ),
            f"| Overall Score | {report.readiness_score.overall_score:.1f} / 100 |",
            "",
            "## Production Status",
            "",
            report.readiness_score.production_readiness.value,
            "",
            "## Why?",
            "",
            f"- {len(critical_blockers)} critical blockers",
            f"- {high_priority_core_gap_count} high-priority core gaps",
            (
                f"- {core_detail.passed_rules if core_detail else 0} of "
                f"{core_applicable_controls} applicable core controls passed"
            ),
            "",
            "## Core Controls",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Passed | {report.readiness_score.tier_details.get('core').passed_rules if report.readiness_score.tier_details.get('core') else 0} |",
            f"| Failed | {report.readiness_score.tier_details.get('core').failed_rules if report.readiness_score.tier_details.get('core') else 0} |",
            f"| Manual Review | {report.readiness_score.tier_details.get('core').manual_review_rules if report.readiness_score.tier_details.get('core') else 0} |",
            f"| Not Applicable | {report.readiness_score.tier_details.get('core').not_applicable_rules if report.readiness_score.tier_details.get('core') else 0} |",
            f"| Disabled | {report.readiness_score.tier_details.get('core').disabled_rules if report.readiness_score.tier_details.get('core') else 0} |",
            f"| Errors | {report.readiness_score.tier_details.get('core').error_rules if report.readiness_score.tier_details.get('core') else 0} |",
            "",
            "## Advanced Controls",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Passed | {report.readiness_score.tier_details.get('advanced').passed_rules if report.readiness_score.tier_details.get('advanced') else 0} |",
            (
                f"| Improvement Opportunities | "
                f"{report.readiness_score.tier_details.get('advanced').failed_rules if report.readiness_score.tier_details.get('advanced') else 0} |"
            ),
            f"| Not Applicable | {report.readiness_score.tier_details.get('advanced').not_applicable_rules if report.readiness_score.tier_details.get('advanced') else 0} |",
            f"| Disabled | {report.readiness_score.tier_details.get('advanced').disabled_rules if report.readiness_score.tier_details.get('advanced') else 0} |",
            f"| Errors | {report.readiness_score.tier_details.get('advanced').error_rules if report.readiness_score.tier_details.get('advanced') else 0} |",
            "",
            "## Category Scores",
            "",
            "| Category | Score |",
            "| --- | ---: |",
        ]

        for category, score in categories:
            lines.append(
                f"| {_escape_markdown_table(_title_case_category(category))} | {score:.1f} |"
            )

        lines.extend(
            [
                "",
                "## Summary",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Passed | {report.readiness_score.passed_rules} |",
                f"| Failed | {report.readiness_score.failed_rules} |",
                f"| Manual Review | {report.readiness_score.manual_review_rules} |",
                f"| Not Applicable | {report.readiness_score.not_applicable_rules} |",
                f"| Disabled | {report.readiness_score.disabled_rules} |",
                f"| Errors | {report.readiness_score.error_rules} |",
                f"| Critical Failures | {report.readiness_score.critical_failures} |",
                f"| High Failures | {report.readiness_score.high_failures} |",
            ]
        )

        lines.extend(
            [
                "",
                "## Full Rule Results",
                "",
                "| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )

        for row in rule_details:
            lines.append(
                "| "
                f"{_escape_markdown_table(row.get('rule_id', ''))} | "
                f"{_escape_markdown_table(row.get('title', ''))} | "
                f"{_escape_markdown_table(_title_case_category(str(row.get('category', ''))))} | "
                f"{_escape_markdown_table(row.get('tier', ''))} | "
                f"{_escape_markdown_table(row.get('severity', ''))} | "
                f"{_escape_markdown_table(row.get('status', ''))} | "
                f"{_escape_markdown_table(row.get('recommendation', ''))} |"
            )

        lines.extend(["", "## Recommendations", ""])
        if recommendations:
            for item in recommendations:
                lines.append(f"- {item['rule_id']}: {item['recommendation']}")
        else:
            lines.append("- None")

        lines.extend(["", "## Critical Blockers", ""])
        if critical_blockers:
            for finding in critical_blockers:
                self._append_markdown_finding(lines, finding)
        else:
            lines.append("- None")

        lines.extend(["", "## Top Core Gaps", ""])
        if top_core_gaps:
            for finding in top_core_gaps:
                self._append_markdown_finding(lines, finding)
        else:
            lines.append("- None")

        lines.extend(["", "## Advanced Opportunities", ""])
        if advanced_opportunities:
            for finding in advanced_opportunities:
                self._append_markdown_finding(lines, finding, action_label="Opportunity")
        else:
            lines.append("- None")

        lines.extend(["", "## Passed Controls", ""])
        if passed_controls:
            for item in passed_controls:
                rule_id = str(item.get("rule_id", ""))
                title = str(item.get("title", ""))
                lines.append(f"- PASS {rule_id}: {title}")
        else:
            lines.append("- None")

        lines.extend(["", "## Not Applicable", ""])
        if not_applicable_rows:
            for row in not_applicable_rows:
                rule_id = str(row.get("rule_id", ""))
                title = str(row.get("title", ""))
                reason = str(row.get("applicability_reason", "")).strip()
                lines.append(f"### {rule_id} - {title}")
                lines.append("")
                lines.append(f"**Reason:** {reason or 'Applicability evidence was not detected.'}")
                lines.append("")
        else:
            lines.append("- None")

        return "\n".join(lines) + "\n"

    def write_json(self, report: ReadinessReport, output_path: Path) -> Path:
        output_path.write_text(self.render_json(report), encoding="utf-8")
        return output_path

    def write_markdown(self, report: ReadinessReport, output_path: Path) -> Path:
        output_path.write_text(self.render_markdown(report), encoding="utf-8")
        return output_path

    def _json_payload(self, report: ReadinessReport) -> dict[str, object]:
        categories = sorted(
            report.readiness_score.category_scores.items(),
            key=lambda item: item[0].lower(),
        )
        rule_details = cast(
            list[dict[str, object]],
            report.metadata.get("rule_details", []),
        )
        critical_findings = cast(
            list[dict[str, object]],
            report.metadata.get("critical_findings", []),
        )
        high_findings = cast(
            list[dict[str, object]],
            report.metadata.get("high_findings", []),
        )
        recommendations = cast(
            list[dict[str, str]],
            report.metadata.get("recommendations", []),
        )
        core_detail = report.readiness_score.tier_details.get("core")
        advanced_detail = report.readiness_score.tier_details.get("advanced")

        return {
            "repository_name": report.repository_name,
            "generated_at": format_timestamp(report.generated_at),
            "earf_version": report.earf_version,
            "overall_score": report.readiness_score.overall_score,
            "core_readiness": {
                "score": report.readiness_score.core_readiness_score,
                "passed": core_detail.passed_rules if core_detail else 0,
                "failed": core_detail.failed_rules if core_detail else 0,
                "manual_review": core_detail.manual_review_rules if core_detail else 0,
                "not_applicable": core_detail.not_applicable_rules if core_detail else 0,
            },
            "advanced_controls": {
                "score": report.readiness_score.advanced_controls_score,
                "passed": advanced_detail.passed_rules if advanced_detail else 0,
                "failed": advanced_detail.failed_rules if advanced_detail else 0,
                "manual_review": advanced_detail.manual_review_rules if advanced_detail else 0,
                "improvement_opportunities": (
                    advanced_detail.failed_rules
                )
                if advanced_detail
                else 0,
            },
            "assessment_coverage": {
                "percentage": report.readiness_score.assessment_coverage.percentage,
                "evaluated": report.readiness_score.assessment_coverage.evaluated,
                "applicable": report.readiness_score.assessment_coverage.applicable,
            },
            "production_status": report.readiness_score.production_readiness.value,
            "category_scores": {category: score for category, score in categories},
            "summary": {
                "passed": report.readiness_score.passed_rules,
                "failed": report.readiness_score.failed_rules,
                "manual_review": report.readiness_score.manual_review_rules,
                "not_applicable": report.readiness_score.not_applicable_rules,
                "disabled": report.readiness_score.disabled_rules,
                "errors": report.readiness_score.error_rules,
                "critical_failures": report.readiness_score.critical_failures,
                "high_failures": report.readiness_score.high_failures,
            },
            "total_evidence": report.total_evidence,
            "rule_results": rule_details,
            "critical_findings": critical_findings,
            "high_findings": high_findings,
            "recommendations": recommendations,
            "metadata": dict(report.metadata),
        }

    def _append_console_finding(
        self,
        lines: list[str],
        finding: dict[str, object],
        *,
        action_label: str = "Action",
    ) -> None:
        severity = str(finding.get("severity", ""))
        rule_id = str(finding.get("rule_id", ""))
        title = str(finding.get("title", ""))
        failure_message = str(finding.get("failure_message", "")).strip()
        recommendation = str(finding.get("recommendation", "")).strip()

        lines.append(f"[{severity}] {rule_id} - {title}")
        lines.append("Reason:")
        lines.append(failure_message or "Required evidence for this control was not detected.")
        lines.append(f"{action_label}:")
        lines.append(recommendation or "No recommendation provided.")

        missing = finding.get("missing_requirements")
        if isinstance(missing, list) and missing:
            lines.append("Missing:")
            for item in missing:
                lines.append(f"- {item}")
        lines.append("")

    def _append_markdown_finding(
        self,
        lines: list[str],
        finding: dict[str, object],
        *,
        action_label: str = "Action",
    ) -> None:
        severity = str(finding.get("severity", ""))
        status = str(finding.get("status", ""))
        rule_id = str(finding.get("rule_id", ""))
        title = str(finding.get("title", ""))
        failure_message = str(finding.get("failure_message", "")).strip()
        recommendation = str(finding.get("recommendation", "")).strip()

        lines.append(f"### {rule_id} - {title}")
        lines.append("")
        lines.append(f"**Severity:** {severity.title()}")
        lines.append("")
        lines.append(f"**Status:** {status}")
        lines.append("")
        lines.append(f"**Reason:** {failure_message or 'Required evidence for this control was not detected.'}")
        lines.append("")
        lines.append(f"**{action_label}:** {recommendation or 'No recommendation provided.'}")
        lines.append("")

        missing = finding.get("missing_requirements")
        if isinstance(missing, list) and missing:
            lines.append("**Missing evidence checks:**")
            lines.append("")
            for item in missing:
                lines.append(f"- {item}")
            lines.append("")
