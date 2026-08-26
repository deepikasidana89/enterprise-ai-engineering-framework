from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from .builder import format_timestamp
from .models import ReadinessReport
from .pdf_reporter import PdfReporter


def _title_case_category(value: str) -> str:
    return value.replace("_", " ").title()


def _escape_markdown_table(value: object) -> str:
    return str(value).replace("|", "\\|")


class ReportWriter:
    def render_console(self, report: ReadinessReport) -> str:
        category_details = report.readiness_score.category_details
        categories = sorted(category_details.items(), key=lambda item: item[0].lower())
        rule_details = cast(list[dict[str, object]], report.metadata.get("rule_details", []))
        core_gaps = cast(list[dict[str, object]], report.metadata.get("core_gaps", []))
        advanced = cast(list[dict[str, object]], report.metadata.get("advanced_opportunities", []))
        passed = cast(list[dict[str, object]], report.metadata.get("passed_controls", []))
        manual = cast(list[dict[str, object]], report.metadata.get("manual_review_required", []))
        semantic = cast(list[dict[str, object]], report.metadata.get("semantic_review_required", []))
        critical = [item for item in core_gaps if str(item.get("severity", "")).upper() == "CRITICAL"]
        high = [item for item in core_gaps if str(item.get("severity", "")).upper() == "HIGH"]
        coverage = report.readiness_score.assessment_coverage

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
            f"Automated Evaluation Coverage: {coverage.percentage:.1f}%",
            "",
            "Production Status",
            "",
            report.readiness_score.production_readiness.value,
            "",
            f"Critical Blockers: {len(critical)}",
            f"High-Priority Core Gaps: {len(high)}",
            "",
            "Category Scores",
            "",
            "Category                 Score   Passed/Failed",
        ]
        for category, detail in categories:
            score_text = f"{detail.score:.1f}" if detail.score is not None else "N/A"
            lines.append(f"{_title_case_category(category):<24} {score_text:>5}   {detail.passed_rules}/{detail.failed_rules}")

        def append_findings(title: str, findings: list[dict[str, object]]) -> None:
            lines.extend(["", title, ""])
            if not findings:
                lines.append("None")
                return
            for item in findings:
                lines.append(f"{item.get('rule_id', '')} - {item.get('title', 'Finding')}")
                recommendation = str(item.get("recommendation", item.get("action", ""))).strip()
                if recommendation:
                    lines.append(f"Action: {recommendation}")

        append_findings("Critical Blockers", critical)
        append_findings("Top Core Gaps", [item for item in core_gaps if item not in critical])
        append_findings("Advanced Opportunities", advanced)
        append_findings("Manual Review Required", manual)
        append_findings("Needs Semantic Review", semantic)
        lines.extend(["", "Passed Controls", ""])
        lines.extend([f"PASS {item.get('rule_id', '')} - {item.get('title', '')}" for item in passed] or ["None"])
        lines.extend(["", f"Total Rule Results: {len(rule_details)}"])
        return "\n".join(lines)

    def render_json(self, report: ReadinessReport) -> str:
        return json.dumps(self._json_payload(report), indent=2, ensure_ascii=False)

    def render_markdown(self, report: ReadinessReport) -> str:
        score = report.readiness_score
        coverage = score.assessment_coverage
        rule_details = cast(list[dict[str, object]], report.metadata.get("rule_details", []))
        core_gaps = cast(list[dict[str, object]], report.metadata.get("core_gaps", []))
        advanced = cast(list[dict[str, object]], report.metadata.get("advanced_opportunities", []))
        passed = cast(list[dict[str, object]], report.metadata.get("passed_controls", []))
        recommendations = cast(list[dict[str, str]], report.metadata.get("recommendations", []))
        critical = [item for item in core_gaps if str(item.get("severity", "")).upper() == "CRITICAL"]

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
            f"| Core Readiness | {score.core_readiness_score:.1f} / 100 |",
            f"| Advanced Controls | {score.advanced_controls_score:.1f} / 100 |",
            f"| Automated Evaluation Coverage | {coverage.percentage:.1f}% ({coverage.evaluated}/{coverage.applicable}) |",
            f"| Overall Score | {score.overall_score:.1f} / 100 |",
            "",
            "## Production Status",
            "",
            score.production_readiness.value,
            "",
            "## Category Scores",
            "",
            "| Category | Score | Passed | Failed | Manual Review | Needs Semantic Review | N/A |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for category, detail in sorted(score.category_details.items(), key=lambda item: item[0].lower()):
            score_text = f"{detail.score:.1f}" if detail.score is not None else "N/A"
            lines.append(
                f"| {_escape_markdown_table(_title_case_category(category))} | {score_text} | {detail.passed_rules} | {detail.failed_rules} | {detail.manual_review_rules} | {detail.needs_semantic_review_rules} | {detail.not_applicable_rules} |"
            )

        lines.extend(["", "## Critical Blockers", ""])
        self._append_markdown_findings(lines, critical)
        lines.extend(["", "## Top Core Gaps", ""])
        self._append_markdown_findings(lines, [item for item in core_gaps if item not in critical])
        lines.extend(["", "## Advanced Opportunities", ""])
        self._append_markdown_findings(lines, advanced)
        lines.extend(["", "## Recommendations", ""])
        if recommendations:
            for item in recommendations:
                lines.append(f"- {item.get('rule_id', '')}: {item.get('recommendation', '')}")
        else:
            lines.append("- None")
        lines.extend(["", "## Passed Controls", ""])
        lines.extend([f"- PASS {item.get('rule_id', '')}: {item.get('title', '')}" for item in passed] or ["- None"])
        lines.extend(["", "## Full Rule Results", "", "| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |", "| --- | --- | --- | --- | --- | --- | --- |"])
        for row in rule_details:
            lines.append(
                "| " + " | ".join([
                    _escape_markdown_table(row.get("rule_id", "")),
                    _escape_markdown_table(row.get("title", "")),
                    _escape_markdown_table(_title_case_category(str(row.get("category", "")))),
                    _escape_markdown_table(row.get("tier", "")),
                    _escape_markdown_table(row.get("severity", "")),
                    _escape_markdown_table(row.get("status", "")),
                    _escape_markdown_table(row.get("recommendation", "")),
                ]) + " |"
            )
        return "\n".join(lines) + "\n"

    def write_json(self, report: ReadinessReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_json(report), encoding="utf-8")
        return output_path

    def write_markdown(self, report: ReadinessReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_markdown(report), encoding="utf-8")
        return output_path

    def write_pdf(self, report: ReadinessReport, output_path: Path) -> Path:
        return PdfReporter().write(report, output_path)

    @staticmethod
    def _append_markdown_findings(lines: list[str], findings: list[dict[str, object]]) -> None:
        if not findings:
            lines.append("- None")
            return
        for item in findings:
            lines.append(f"### {item.get('rule_id', '')} - {item.get('title', 'Finding')}")
            lines.append("")
            severity = str(item.get("severity", "")).strip()
            recommendation = str(item.get("recommendation", item.get("action", ""))).strip()
            if severity:
                lines.append(f"**Severity:** {severity}")
                lines.append("")
            if recommendation:
                lines.append(f"**Recommended action:** {recommendation}")
                lines.append("")

    def _json_payload(self, report: ReadinessReport) -> dict[str, object]:
        score = report.readiness_score
        rule_details = cast(list[dict[str, object]], report.metadata.get("rule_details", []))
        return {
            "repository_name": report.repository_name,
            "generated_at": format_timestamp(report.generated_at),
            "earf_version": report.earf_version,
            "overall_score": score.overall_score,
            "core_readiness": score.core_readiness_score,
            "advanced_controls": score.advanced_controls_score,
            "assessment_coverage": {
                "percentage": score.assessment_coverage.percentage,
                "evaluated": score.assessment_coverage.evaluated,
                "applicable": score.assessment_coverage.applicable,
            },
            "production_status": score.production_readiness.value,
            "total_evidence": report.total_evidence,
            "category_scores": dict(score.category_scores),
            "rule_results": rule_details,
            "summary": {
                "passed": score.passed_rules,
                "failed": score.failed_rules,
                "manual_review": score.manual_review_rules,
                "needs_semantic_review": score.needs_semantic_review_rules,
                "not_applicable": score.not_applicable_rules,
                "disabled": score.disabled_rules,
                "errors": score.error_rules,
                "critical_failures": score.critical_failures,
                "high_failures": score.high_failures,
            },
            "metadata": dict(report.metadata),
        }
