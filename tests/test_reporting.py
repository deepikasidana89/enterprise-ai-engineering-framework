from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from earf.evidence import EvidenceRepository
from earf.models import ControlTier, RepositoryContext, RuleDefinition, Severity
from earf.pipeline import AnalysisResult
from earf.reporting.builder import ReportBuilder, build_readiness_report, format_timestamp
from earf.reporting.models import ReadinessReport
from earf.reporting.writer import ReportWriter
from earf.rules.catalog import RuleCatalog
from earf.rules.results import RuleResult, RuleStatus
from earf.scoring.models import (
    AssessmentCoverage,
    ProductionReadiness,
    ReadinessScore,
    TierScoreDetail,
)


TIMESTAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def _rule(
    rule_id: str,
    *,
    title: str,
    category: str,
    severity: Severity,
    tier: ControlTier = ControlTier.CORE,
    failure_message: str,
    recommendation: str,
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title=title,
        description="desc",
        category=category,
        severity=severity,
        tier=tier,
        applicability={"always": True},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
        failure_message=failure_message,
        recommendation=recommendation,
    )


def _result(rule_id: str, status: RuleStatus, message: str = "message") -> RuleResult:
    return RuleResult(rule_id=rule_id, status=status, message=message)


def _score() -> ReadinessScore:
    return ReadinessScore(
        overall_score=84.6,
        core_readiness_score=100.0,
        advanced_controls_score=0.0,
        category_scores={
            "security": 66.7,
            "governance": 100.0,
            "reliability": 0.0,
            "evaluation": 0.0,
        },
        total_rules=4,
        passed_rules=1,
        failed_rules=3,
        not_applicable_rules=0,
        disabled_rules=0,
        error_rules=0,
        critical_failures=1,
        high_failures=2,
        summary={"earned_weight": 22, "possible_weight": 26},
        production_readiness=ProductionReadiness.READY,
        category_details={},
        tier_details={
            "core": TierScoreDetail(
                tier=ControlTier.CORE,
                score=100.0,
                earned_weight=17,
                possible_weight=17,
                total_rules=3,
                passed_rules=2,
                failed_rules=0,
                manual_review_rules=0,
                not_applicable_rules=0,
                disabled_rules=0,
                error_rules=0,
                critical_failures=0,
                high_failures=0,
            ),
            "advanced": TierScoreDetail(
                tier=ControlTier.ADVANCED,
                score=0.0,
                earned_weight=0,
                possible_weight=14,
                total_rules=1,
                passed_rules=0,
                failed_rules=1,
                manual_review_rules=0,
                not_applicable_rules=0,
                disabled_rules=0,
                error_rules=0,
                critical_failures=1,
                high_failures=1,
            ),
        },
        assessment_coverage=AssessmentCoverage(percentage=100.0, evaluated=4, applicable=4),
    )


def _analysis_result() -> AnalysisResult:
    catalog = RuleCatalog(
        [
            _rule(
                "SEC-001",
                title="Secrets are not hard-coded",
                category="security",
                severity=Severity.CRITICAL,
                failure_message="No supported evidence of externalized secret management was detected.",
                recommendation="Move secrets to environment variables or secret managers.",
            ),
            _rule(
                "GOV-001",
                title="AI ownership documented",
                category="governance",
                severity=Severity.HIGH,
                failure_message="AI ownership documentation evidence was not detected.",
                recommendation="Add CODEOWNERS or OWNERS.",
            ),
            _rule(
                "REL-001",
                title="Timeouts defined",
                category="reliability",
                severity=Severity.HIGH,
                failure_message="Timeout configuration evidence for model calls was not detected.",
                recommendation="Add timeouts.",
            ),
            _rule(
                "OBS-001",
                title="Telemetry present",
                category="evaluation",
                severity=Severity.HIGH,
                tier=ControlTier.ADVANCED,
                failure_message="AI observability or tracing evidence was not detected.",
                recommendation="Add CODEOWNERS or OWNERS.",
            ),
        ]
    )
    results = [
        _result("REL-001", RuleStatus.FAIL, "Timeout configuration evidence for model calls was not detected."),
        _result("GOV-001", RuleStatus.PASS),
        _result("SEC-001", RuleStatus.FAIL, "No supported evidence of externalized secret management was detected."),
        _result("OBS-001", RuleStatus.FAIL, "AI observability or tracing evidence was not detected."),
    ]
    evidence_repository = EvidenceRepository()
    for _ in range(3):
        evidence_repository.add_many([])
    return AnalysisResult(
        repository_context=RepositoryContext(root_path=Path("."), project_name="sample-repo"),
        evidence_repository=evidence_repository,
        rule_catalog=catalog,
        rule_results=results,
        readiness_score=_score(),
    )


def _report() -> ReadinessReport:
    analysis = _analysis_result()
    report = ReportBuilder().build(analysis, generated_at=TIMESTAMP)
    analysis.readiness_report = report
    return report


def test_readiness_report_is_immutable() -> None:
    report = _report()

    with pytest.raises(Exception):
        report.repository_name = "other"  # type: ignore[misc]


def test_readiness_report_has_phase6_fields() -> None:
    report = _report()

    assert report.repository_name == "sample-repo"
    assert report.earf_version
    assert report.total_evidence == 0
    assert report.readiness_score.overall_score == 84.6


def test_report_builder_uses_utc_timestamp_and_analysis_result() -> None:
    analysis = _analysis_result()
    report = ReportBuilder().build(analysis, generated_at=TIMESTAMP)

    assert report.generated_at == TIMESTAMP
    assert format_timestamp(report.generated_at) == "2026-01-02T03:04:05Z"
    assert report.analysis_result is analysis


def test_report_builder_deterministic_ordering() -> None:
    report = _report()

    rule_details = report.metadata["rule_details"]
    critical_findings = report.metadata["critical_findings"]
    high_findings = report.metadata["high_findings"]

    assert [row["rule_id"] for row in rule_details] == ["GOV-001", "OBS-001", "REL-001", "SEC-001"]
    assert [item["rule_id"] for item in critical_findings] == ["SEC-001"]
    assert [item["rule_id"] for item in high_findings] == ["OBS-001", "REL-001"]


def test_recommendations_come_from_failed_rules_and_are_deduplicated() -> None:
    report = _report()

    recommendations = report.metadata["recommendations"]
    assert recommendations == [
        {"rule_id": "OBS-001", "title": "Telemetry present", "recommendation": "Add CODEOWNERS or OWNERS."},
        {"rule_id": "REL-001", "title": "Timeouts defined", "recommendation": "Add timeouts."},
        {
            "rule_id": "SEC-001",
            "title": "Secrets are not hard-coded",
            "recommendation": "Move secrets to environment variables or secret managers.",
        },
    ]


def test_not_applicable_rules_do_not_appear_in_findings_or_recommendations() -> None:
    catalog = RuleCatalog(
        [
            _rule(
                "GOV-001",
                title="AI ownership documented",
                category="governance",
                severity=Severity.HIGH,
                failure_message="AI ownership documentation evidence was not detected.",
                recommendation="Document ownership.",
            ),
            _rule(
                "MOD-001",
                title="Model provider configured",
                category="modeling",
                severity=Severity.HIGH,
                failure_message="Model provider configuration evidence was not detected.",
                recommendation="Add provider configuration.",
            ),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.FAIL),
        RuleResult(rule_id="MOD-001", status=RuleStatus.NOT_APPLICABLE, message="Rule is not applicable to this repository."),
    ]
    analysis = AnalysisResult(
        repository_context=RepositoryContext(root_path=Path("."), project_name="sample-repo"),
        evidence_repository=EvidenceRepository(),
        rule_catalog=catalog,
        rule_results=results,
        readiness_score=ReadinessScore(
            overall_score=100.0,
            category_scores={"governance": 100.0},
            total_rules=2,
            passed_rules=0,
            failed_rules=1,
            not_applicable_rules=1,
            disabled_rules=0,
            error_rules=0,
            critical_failures=0,
            high_failures=1,
            summary={},
            production_readiness=ProductionReadiness.NOT_READY,
            category_details={},
        ),
    )

    report = ReportBuilder().build(analysis, generated_at=TIMESTAMP)

    assert [item["rule_id"] for item in report.metadata["critical_findings"]] == []
    assert [item["rule_id"] for item in report.metadata["high_findings"]] == ["GOV-001"]
    assert [item["rule_id"] for item in report.metadata["recommendations"]] == ["GOV-001"]
    assert any(row["status"] == "NOT_APPLICABLE" for row in report.metadata["rule_details"])


def test_console_rendering() -> None:
    output = ReportWriter().render_console(_report())

    assert "EARF Enterprise AI Readiness Report" in output
    assert "Repository: sample-repo" in output
    assert "Generated: 2026-01-02T03:04:05Z" in output
    assert "EARF Version:" in output
    assert "Overall Assessment" in output
    assert "Core Readiness: 100.0 / 100" in output
    assert "Assessment Coverage: 100.0%" in output
    assert "Production Status" in output
    assert "Why?" in output
    assert "1 critical blockers" in output
    assert "Critical Blockers" in output
    assert "Top Core Gaps" in output
    assert "Advanced Opportunities" in output
    assert "Passed Controls" in output
    assert "Summary" in output
    assert "Critical Findings" not in output
    assert "High Findings" not in output
    assert "Recommendations" not in output
    assert "[CRITICAL] SEC-001 - Secrets are not hard-coded" in output
    assert "Reason:" in output
    assert "No supported evidence of externalized secret management was detected." in output
    assert "Action:" in output
    assert "[HIGH] OBS-001 - Telemetry present" in output
    assert output.count("SEC-001") == 1


def test_json_serialization_and_enum_values(tmp_path: Path) -> None:
    report = _report()
    writer = ReportWriter()
    output_path = writer.write_json(report, tmp_path / "earf-report.json")

    parsed = json.loads(output_path.read_text(encoding="utf-8"))
    assert parsed["repository_name"] == "sample-repo"
    assert parsed["generated_at"] == "2026-01-02T03:04:05Z"
    assert parsed["earf_version"] == report.earf_version
    assert parsed["overall_score"] == 84.6
    assert parsed["production_status"] == "READY"
    assert parsed["core_readiness"]["score"] == 100.0
    assert parsed["advanced_controls"]["score"] == 0.0
    assert parsed["assessment_coverage"]["percentage"] == 100.0
    assert parsed["category_scores"] == {
        "evaluation": 0.0,
        "governance": 100.0,
        "reliability": 0.0,
        "security": 66.7,
    }
    failing = [row for row in parsed["rule_results"] if row["rule_id"] == "SEC-001"][0]
    assert failing["failure_message"] == "No supported evidence of externalized secret management was detected."


def test_markdown_rendering_and_file_output(tmp_path: Path) -> None:
    report = _report()
    writer = ReportWriter()
    output_path = writer.write_markdown(report, tmp_path / "EARF_REPORT.md")

    content = output_path.read_text(encoding="utf-8")
    assert output_path.name == "EARF_REPORT.md"
    assert "# EARF Enterprise AI Readiness Report" in content
    assert "## Overall Assessment" in content
    assert "## Core Controls" in content
    assert "## Advanced Controls" in content
    assert "## Category Scores" in content
    assert "## Full Rule Results" in content
    assert "| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |" in content
    assert "**Reason:** No supported evidence of externalized secret management was detected." in content
    assert "## Recommendations" in content
    assert "## Advanced Opportunities" in content


def test_build_readiness_report_compatibility_helper() -> None:
    analysis = _analysis_result()
    report = build_readiness_report(
        repository_name="sample-repo",
        readiness_score=analysis.readiness_score,
        rule_results=analysis.rule_results,
        catalog=analysis.rule_catalog,
        total_evidence=7,
        generated_at=TIMESTAMP,
    )

    assert report.repository_name == "sample-repo"
    assert report.total_evidence == 7
    assert report.generated_at == TIMESTAMP
