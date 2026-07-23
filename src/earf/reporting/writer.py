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
        critical_findings = cast(
            list[dict[str, str]],
            report.metadata.get("critical_findings", []),
        )
        high_findings = cast(
            list[dict[str, str]],
            report.metadata.get("high_findings", []),
        )
        recommendations = cast(
            list[dict[str, str]],
            report.metadata.get("recommendations", []),
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
            "Overall Readiness",
            "",
            f"{report.readiness_score.overall_score:.1f} / 100",
            "",
            "Production Status",
            "",
            report.readiness_score.production_readiness.value,
            "",
            "Category Scores",
            "",
        ]

        for category, score in categories:
            lines.append(
                f"{_title_case_category(category):<{category_width}}  {score:>5.1f}"
            )

        lines.extend(
            [
                "",
                "Summary",
                "",
                f"Passed: {report.readiness_score.passed_rules}",
                f"Failed: {report.readiness_score.failed_rules}",
                f"Not Applicable: {report.readiness_score.not_applicable_rules}",
                f"Disabled: {report.readiness_score.disabled_rules}",
                f"Errors: {report.readiness_score.error_rules}",
                f"Critical Failures: {report.readiness_score.critical_failures}",
                f"High Failures: {report.readiness_score.high_failures}",
                "",
                "Critical Findings",
                "",
            ]
        )

        if critical_findings:
            for finding in critical_findings:
                lines.append(f"{finding['rule_id']}  {finding['title']}")
        else:
            lines.append("None")

        lines.extend(["", "High Findings", ""])
        if high_findings:
            for finding in high_findings:
                lines.append(f"{finding['rule_id']}  {finding['title']}")
        else:
            lines.append("None")

        lines.extend(["", "Recommendations", ""])
        if recommendations:
            for item in recommendations:
                lines.append(f"{item['rule_id']}  {item['recommendation']}")
        else:
            lines.append("None")

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
        critical_findings = cast(
            list[dict[str, str]],
            report.metadata.get("critical_findings", []),
        )
        high_findings = cast(
            list[dict[str, str]],
            report.metadata.get("high_findings", []),
        )
        recommendations = cast(
            list[dict[str, str]],
            report.metadata.get("recommendations", []),
        )

        lines = [
            "# EARF Enterprise AI Readiness Report",
            "",
            f"Repository: {report.repository_name}",
            f"Generated: {format_timestamp(report.generated_at)}",
            f"EARF Version: {report.earf_version}",
            f"Total Evidence: {report.total_evidence}",
            "",
            "## Overall Readiness",
            "",
            f"{report.readiness_score.overall_score:.1f} / 100",
            "",
            "## Production Status",
            "",
            report.readiness_score.production_readiness.value,
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
                f"| Not Applicable | {report.readiness_score.not_applicable_rules} |",
                f"| Disabled | {report.readiness_score.disabled_rules} |",
                f"| Errors | {report.readiness_score.error_rules} |",
                f"| Critical Failures | {report.readiness_score.critical_failures} |",
                f"| High Failures | {report.readiness_score.high_failures} |",
                "",
                "## Critical Findings",
                "",
            ]
        )

        if critical_findings:
            for finding in critical_findings:
                lines.append(f"- {finding['rule_id']}: {finding['title']}")
        else:
            lines.append("- None")

        lines.extend(["", "## High Findings", ""])
        if high_findings:
            for finding in high_findings:
                lines.append(f"- {finding['rule_id']}: {finding['title']}")
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "## Full Rule Results",
                "",
                "| Rule ID | Title | Category | Severity | Status | Recommendation |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )

        for row in rule_details:
            lines.append(
                "| "
                f"{_escape_markdown_table(row.get('rule_id', ''))} | "
                f"{_escape_markdown_table(row.get('title', ''))} | "
                f"{_escape_markdown_table(_title_case_category(str(row.get('category', ''))))} | "
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
            list[dict[str, str]],
            report.metadata.get("critical_findings", []),
        )
        high_findings = cast(
            list[dict[str, str]],
            report.metadata.get("high_findings", []),
        )
        recommendations = cast(
            list[dict[str, str]],
            report.metadata.get("recommendations", []),
        )

        return {
            "repository_name": report.repository_name,
            "generated_at": format_timestamp(report.generated_at),
            "earf_version": report.earf_version,
            "overall_score": report.readiness_score.overall_score,
            "production_status": report.readiness_score.production_readiness.value,
            "category_scores": {category: score for category, score in categories},
            "summary": {
                "passed": report.readiness_score.passed_rules,
                "failed": report.readiness_score.failed_rules,
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
