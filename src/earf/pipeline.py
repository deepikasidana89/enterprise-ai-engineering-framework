from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .evidence import EvidenceRepository
from .evidence_collection import EvidenceCollectionService
from .models import Evidence, RepositoryContext
from .repository import RepositoryLoader
from .reporting.builder import ReportBuilder
from .reporting.models import ReadinessReport
from .rules.builtin import built_in_rules_path
from .rules.catalog import RuleCatalog
from .rules.evaluation_service import RuleEvaluationService
from .rules.loader import RuleLoader
from .rules.results import RuleResult
from .scoring.models import ReadinessScore
from .scoring.service import ScoringService
from .llm_config import LLMConfig
from .reasoning import EvidenceSnippet, LocalLLMReasoner, deterministic_reasoning
from .models import EvidenceType


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
        rules_path: Path | None = None,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self._repository_loader = repository_loader or RepositoryLoader()
        self._evidence_service = evidence_service or EvidenceCollectionService()
        self._rule_loader = rule_loader
        self._rule_evaluation_service = rule_evaluation_service or RuleEvaluationService()
        self._scoring_service = scoring_service or ScoringService()
        self._report_builder = report_builder or ReportBuilder()
        self._rules_path = self._resolve_rules_path(rules_path)
        self._llm_config = llm_config or LLMConfig.from_environment()

    def _resolve_rules_path(self, rules_path: Path | None) -> Path:
        if rules_path is not None:
            return rules_path

        local_rules = Path("rules")
        if local_rules.exists():
            return local_rules
        return built_in_rules_path()

    def analyze(self, repository_path: Path) -> AnalysisResult:
        repository_context = self._repository_loader.load(repository_path)
        evidence_repository = self._evidence_service.collect(repository_context)
        self._reason_about_llm(repository_context, evidence_repository)
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

    def _reason_about_llm(self, context: RepositoryContext, repository: EvidenceRepository) -> None:
        # Disabled means preserve the established deterministic pipeline exactly.
        if not self._llm_config.enabled:
            return
        candidates = [e for e in repository.all() if e.identifier in {
            "openai_client_import", "openai_client_construct", "anthropic_client_construct",
            "llm_provider_api_call", "ai.provider_import", "ai.runtime_call", "ai.model_config",
        } or e.evidence_type in {EvidenceType.DEPENDENCY, EvidenceType.RUNTIME_CALL}]
        snippets = [EvidenceSnippet(f"E{i}", e.path or "", int((e.metadata or {}).get("line", 1)),
                                    int((e.metadata or {}).get("line", 1)), e.evidence_type.value,
                                    e.description, str((e.metadata or {}).get("matched_text", e.description)))
                    for i, e in enumerate(candidates[:40], 1)]
        reasoner = None
        if self._llm_config.enabled:
            try:
                reasoner = LocalLLMReasoner(self._llm_config.resolved_model_path(context.root_path), self._llm_config.context_size, self._llm_config.temperature)
                result = reasoner.evaluate("uses_llm", snippets)
            except Exception:
                result = deterministic_reasoning("uses_llm", snippets)
        else:
            result = deterministic_reasoning("uses_llm", snippets)
        repository.add(Evidence(EvidenceType.LLM_REVIEW, "hybrid_reasoning", "LLM usage capability verdict",
                                identifier="uses_llm", metadata={"verdict": result.verdict, "confidence": result.confidence,
                                "reasoning_method": result.reasoning_method, "model": result.model or "",
                                "supporting_evidence_ids": result.supporting_evidence_ids}))
