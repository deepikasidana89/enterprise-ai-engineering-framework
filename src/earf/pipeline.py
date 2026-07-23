from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .evidence import EvidenceRepository
from .evidence_collection import EvidenceCollectionService
from .models import RepositoryContext
from .repository import RepositoryLoader
from .reporting.builder import ReportBuilder
from .reporting.models import ReadinessReport
from .rules.catalog import RuleCatalog
from .rules.evaluation_service import RuleEvaluationService
from .rules.loader import RuleLoader
from .rules.results import RuleResult
from .scoring.models import ReadinessScore
from .scoring.service import ScoringService


@dataclass
class AnalysisResult:
    repository_context: RepositoryContext
    evidence_repository: EvidenceRepository
    rule_catalog: RuleCatalog
    rule_results: list[RuleResult]
    readiness_score: ReadinessScore
    readiness_report: ReadinessReport | None = None


class EARFPipeline:
    def __init__(
        self,
        *,
        repository_loader: RepositoryLoader | None = None,
        evidence_service: EvidenceCollectionService | None = None,
        rule_loader: RuleLoader | None = None,
        rule_evaluation_service: RuleEvaluationService | None = None,
        scoring_service: ScoringService | None = None,
        report_builder: ReportBuilder | None = None,
        rules_path: Path = Path("rules"),
    ) -> None:
        self._repository_loader = repository_loader or RepositoryLoader()
        self._evidence_service = evidence_service or EvidenceCollectionService()
        self._rule_loader = rule_loader
        self._rule_evaluation_service = rule_evaluation_service or RuleEvaluationService()
        self._scoring_service = scoring_service or ScoringService()
        self._report_builder = report_builder or ReportBuilder()
        self._rules_path = rules_path

    def analyze(self, repository_path: Path) -> AnalysisResult:
        repository_context = self._repository_loader.load(repository_path)
        evidence_repository = self._evidence_service.collect(repository_context)
        rule_catalog, _ = RuleCatalog.from_path(self._rules_path, loader=self._rule_loader)
        rule_results = self._rule_evaluation_service.evaluate_all(
            rule_catalog,
            evidence_repository,
        )
        readiness_score = self._scoring_service.score(rule_results, rule_catalog)

        analysis_result = AnalysisResult(
            repository_context=repository_context,
            evidence_repository=evidence_repository,
            rule_catalog=rule_catalog,
            rule_results=rule_results,
            readiness_score=readiness_score,
        )
        readiness_report = self._report_builder.build(analysis_result)
        analysis_result.readiness_report = readiness_report
        return analysis_result