from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

from earf.cli import app
from earf.evidence import EvidenceRepository
from earf.evidence_collection import EvidenceCollectionService
from earf.models import Evidence, EvidenceType, RepositoryContext, RuleDefinition, Severity
from earf.pipeline import AnalysisResult, EARFPipeline
from earf.reporting.builder import ReportBuilder
from earf.reporting.models import ReadinessReport
from earf.repository import RepositoryLoader
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.loader import RuleLoader
from earf.rules.results import RuleResult, RuleStatus
from earf.scoring.models import ProductionReadiness, ReadinessScore
from earf.scoring.service import ScoringService


runner = CliRunner()


def _rule_yaml() -> str:
    return """
rules:
  - id: GOV-001
    title: Readme exists
    description: Repository has readme
    category: governance
    severity: high
    version: "1.0"
    enabled: true
    applicability: {always: true}
    rationale: why
    recommendation: Add README.md.
    tags: []
    references: []
    evidence_requirements:
      evidence_type: file
      identifiers: [README.md]
    metadata: {}
""".strip()


def _readiness_score() -> ReadinessScore:
    return ReadinessScore(
        overall_score=100.0,
        category_scores={"governance": 100.0},
        total_rules=1,
        passed_rules=1,
        failed_rules=0,
        not_applicable_rules=0,
        disabled_rules=0,
        error_rules=0,
        critical_failures=0,
        high_failures=0,
        summary={"earned_weight": 7, "possible_weight": 7},
        production_readiness=ProductionReadiness.READY,
        category_details={},
    )


def test_pipeline_returns_analysis_result(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_rule_yaml(), encoding="utf-8")

    analysis = EARFPipeline(rules_path=rules_dir).analyze(tmp_path)

    assert analysis.repository_context.project_name == tmp_path.name
    assert analysis.rule_results[0].status == RuleStatus.PASS
    assert analysis.readiness_report is not None
    assert analysis.readiness_report.readiness_score.overall_score == 100.0


def test_pipeline_dependency_injection(tmp_path: Path) -> None:
    repository_context = RepositoryContext(root_path=tmp_path, project_name="sample")
    evidence_repository = EvidenceRepository()
    evidence_repository.add(
        Evidence(
            evidence_type=EvidenceType.FILE,
            source="file",
            description="readme",
            identifier="README.md",
        )
    )
    rule = RuleDefinition(
        id="GOV-001",
        title="Readme exists",
        description="desc",
        category="governance",
        severity=Severity.HIGH,
        applicability={"always": True},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
        recommendation="Add README.md.",
    )
    rule_results = [RuleResult(rule_id="GOV-001", status=RuleStatus.PASS, message="ok")]
    readiness_score = _readiness_score()

    class FakeRepositoryLoader(RepositoryLoader):
        def load(self, path: Path) -> RepositoryContext:
            assert path == tmp_path
            return repository_context

    class FakeEvidenceService(EvidenceCollectionService):
        def collect(self, context: RepositoryContext, repository: EvidenceRepository | None = None) -> EvidenceRepository:
            assert context is repository_context
            return evidence_repository

    class FakeRuleLoader(RuleLoader):
        def load(self, path: Path) -> list[RuleDefinition]:
            assert path == tmp_path / "rules"
            return [rule]

    class FakeEvaluationService(RuleEvaluationService):
        def evaluate_all(self, catalog: RuleCatalog, evidence_repository_arg: EvidenceRepository) -> list[RuleResult]:
            assert catalog.get("GOV-001").id == "GOV-001"
            assert evidence_repository_arg is evidence_repository
            return rule_results

    class FakeScoringService(ScoringService):
        def score(self, results: list[RuleResult], catalog: RuleCatalog) -> ReadinessScore:
            assert results == rule_results
            assert catalog.get("GOV-001").id == "GOV-001"
            return readiness_score

    class FakeReportBuilder(ReportBuilder):
        def build(self, analysis_result: AnalysisResult, generated_at=None) -> ReadinessReport:
            assert analysis_result.repository_context is repository_context
            assert analysis_result.evidence_repository is evidence_repository
            assert analysis_result.rule_catalog.get("GOV-001").id == "GOV-001"
            assert analysis_result.rule_results == rule_results
            assert analysis_result.readiness_score is readiness_score
            report = ReadinessReport(
                repository_name=analysis_result.repository_context.project_name,
                generated_at=datetime.now(timezone.utc),
                earf_version="0.1.0-test",
                readiness_score=analysis_result.readiness_score,
                rule_results=tuple(analysis_result.rule_results),
                total_evidence=analysis_result.evidence_repository.count(),
                metadata={},
                analysis_result=analysis_result,
            )
            return report

    analysis = EARFPipeline(
        repository_loader=FakeRepositoryLoader(),
        evidence_service=FakeEvidenceService(),
        rule_loader=FakeRuleLoader(),
        rule_evaluation_service=FakeEvaluationService(),
        scoring_service=FakeScoringService(),
        report_builder=FakeReportBuilder(),
        rules_path=tmp_path / "rules",
    ).analyze(tmp_path)

    assert analysis.readiness_report is not None
    assert analysis.readiness_report.readiness_score is readiness_score


def test_cli_delegates_to_pipeline_analyze(monkeypatch, tmp_path: Path) -> None:
    analysis_result = AnalysisResult(
        repository_context=RepositoryContext(root_path=tmp_path, project_name=tmp_path.name),
        evidence_repository=EvidenceRepository(),
        rule_catalog=RuleCatalog([]),
        rule_results=[],
        readiness_score=_readiness_score(),
    )
    report = ReadinessReport(
        repository_name=tmp_path.name,
        generated_at=datetime.now(timezone.utc),
        earf_version="0.1.0-test",
        readiness_score=analysis_result.readiness_score,
        rule_results=(),
        total_evidence=0,
        metadata={},
        analysis_result=analysis_result,
    )
    analysis_result.readiness_report = report

    called_paths: list[Path] = []

    class FakePipeline:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

        def analyze(self, repository_path: Path) -> AnalysisResult:
            called_paths.append(repository_path)
            return analysis_result

    monkeypatch.setattr("earf.cli.EARFPipeline", FakePipeline)

    result = runner.invoke(app, ["report", str(tmp_path)])

    assert result.exit_code == 0
    assert called_paths == [tmp_path]
    assert "EARF Enterprise AI Readiness Report" in result.stdout
