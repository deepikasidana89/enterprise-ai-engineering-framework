from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from .. import __version__
from ..evidence import EvidenceRepository
from ..models import ControlTier, RepositoryContext
from ..rules.catalog import RuleCatalog
from ..rules.results import RuleResult, RuleStatus
from ..scoring.models import ReadinessScore
from .models import ReadinessReport

if TYPE_CHECKING:
    from ..pipeline import AnalysisResult


class ReportBuilder:
    def build(
        self,
        analysis_result: AnalysisResult,
        generated_at: datetime | None = None,
    ) -> ReadinessReport:
        timestamp = generated_at or datetime.now(timezone.utc)
        rule_lookup = {rule.id: rule for rule in analysis_result.rule_catalog.all()}
        ordered_results = tuple(
            sorted(analysis_result.rule_results, key=lambda result: result.rule_id)
        )

        rule_details: list[dict[str, object]] = []
        critical_findings: list[dict[str, object]] = []
        high_findings: list[dict[str, object]] = []
        recommendations: list[dict[str, str]] = []
        seen_recommendations: set[str] = set()
        core_gaps: list[dict[str, object]] = []
        advanced_opportunities: list[dict[str, object]] = []

        for result in ordered_results:
            rule = rule_lookup.get(result.rule_id)
            title = rule.title if rule is not None else ""
            category = rule.category if rule is not None else ""
            severity = rule.severity.name.lower() if rule is not None else ""
            tier = rule.tier.value if rule is not None else ControlTier.CORE.value
            recommendation = rule.recommendation if rule is not None else ""

            rule_details.append(
                {
                    "rule_id": result.rule_id,
                    "title": title,
                    "category": category,
                    "severity": severity,
                    "tier": tier,
                    "status": result.status.name,
                    "message": result.message,
                    "failure_message": result.message if result.status in {RuleStatus.FAIL, RuleStatus.MANUAL_REVIEW} else "",
                    "applicability_reason": str(result.metadata.get("applicability_reason", "")),
                    "recommendation": recommendation,
                    "error": result.error,
                    "missing_requirements": list(result.missing_requirements),
                }
            )

            if result.status not in {RuleStatus.FAIL, RuleStatus.MANUAL_REVIEW} or rule is None:
                continue

            finding = {
                "rule_id": rule.id,
                "title": rule.title,
                "severity": rule.severity.name,
                "status": result.status.name,
                "failure_message": result.message,
                "recommendation": rule.recommendation,
                "missing_requirements": list(result.missing_requirements),
            }
            if rule.severity.name == "CRITICAL":
                critical_findings.append(finding)
            elif rule.severity.name == "HIGH":
                high_findings.append(finding)

            if rule.tier == ControlTier.CORE:
                core_gaps.append(finding)
            else:
                advanced_opportunities.append(finding)

            recommendation_text = rule.recommendation.strip()
            if recommendation_text and recommendation_text not in seen_recommendations:
                seen_recommendations.add(recommendation_text)
                recommendations.append(
                    {
                        "rule_id": rule.id,
                        "title": rule.title,
                        "recommendation": recommendation_text,
                    }
                )

        return ReadinessReport(
            repository_name=analysis_result.repository_context.project_name,
            generated_at=timestamp,
            earf_version=__version__,
            readiness_score=analysis_result.readiness_score,
            rule_results=ordered_results,
            total_evidence=analysis_result.evidence_repository.count(),
            metadata={
                "rule_details": rule_details,
                "critical_findings": critical_findings,
                "high_findings": high_findings,
                "recommendations": recommendations,
                    "core_gaps": core_gaps,
                    "advanced_opportunities": advanced_opportunities,
            },
            analysis_result=analysis_result,
        )


def build_readiness_report(
    *,
    repository_name: str,
    readiness_score: ReadinessScore,
    rule_results: Iterable[RuleResult],
    catalog: RuleCatalog,
    total_evidence: int,
    generated_at: datetime | None = None,
) -> ReadinessReport:
    from ..pipeline import AnalysisResult

    analysis_result = AnalysisResult(
        repository_context=RepositoryContext(
            root_path=Path("."),
            project_name=repository_name,
        ),
        evidence_repository=EvidenceRepository(),
        rule_catalog=catalog,
        rule_results=list(rule_results),
        readiness_score=readiness_score,
    )
    report = ReportBuilder().build(analysis_result, generated_at=generated_at)
    analysis_result.readiness_report = report

    if total_evidence == report.total_evidence:
        return report

    return ReadinessReport(
        repository_name=report.repository_name,
        generated_at=report.generated_at,
        earf_version=report.earf_version,
        readiness_score=report.readiness_score,
        rule_results=report.rule_results,
        total_evidence=total_evidence,
        metadata=report.metadata,
        analysis_result=analysis_result,
    )


def format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")
