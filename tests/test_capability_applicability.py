from __future__ import annotations

from pathlib import Path

from earf.evidence_collection import EvidenceCollectionService
from earf.models import RepositoryContext, RuleDefinition, Severity
from earf.rules.capabilities import RepositoryCapabilityDetector
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleStatus
from earf.scoring.service import ScoringService


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def _rule(
    rule_id: str,
    *,
    applicability: dict[str, object],
    evidence_requirements: dict[str, object],
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title=f"{rule_id} title",
        description="desc",
        category="evaluation",
        severity=Severity.HIGH,
        applicability=applicability,
        evidence_requirements=evidence_requirements,
        recommendation="do",
    )


def _collect(tmp_path: Path):
    return EvidenceCollectionService().collect(_context(tmp_path))


def test_rag_rule_no_rag_returns_not_applicable(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "EVA-001",
        applicability={"all": [{"capability": "uses_rag"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.NOT_APPLICABLE


def test_rag_rule_rag_detected_is_evaluated_normally(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "langchain>=0.2.0\nchromadb>=0.5.0\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "EVA-001",
        applicability={"all": [{"capability": "uses_rag"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.PASS


def test_api_rule_no_api_returns_not_applicable(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "SAF-001",
        applicability={"all": [{"capability": "has_api"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.NOT_APPLICABLE


def test_api_rule_fastapi_detected_is_evaluated(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\nfastapi>=0.110.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "SAF-001",
        applicability={"all": [{"capability": "has_api"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.PASS


def test_has_cicd_detected_from_workflow(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "test.yml").write_text("name: ci", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("has_cicd")

    assert detection.detected is True
    assert detection.evidence


def test_uses_llm_detected_from_dependency(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai" for item in detection.evidence)


def test_readme_keyword_does_not_trigger_rag(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("We may use RAG someday.", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_rag")

    assert detection.detected is False


def test_not_applicable_rules_not_in_score_denominator() -> None:
    rules = RuleCatalog(
        [
            _rule(
                "GOV-001",
                applicability={"always": True},
                evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
            ),
            _rule(
                "GOV-002",
                applicability={"always": True},
                evidence_requirements={"evidence_type": "file", "identifiers": ["SECURITY.md"]},
            ),
            _rule(
                "EVA-001",
                applicability={"all": [{"capability": "uses_rag"}]},
                evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
            ),
        ]
    )

    tmp_path = Path(".")
    repo = EvidenceCollectionService().collect(RepositoryContext(root_path=tmp_path, project_name="x"))

    # Build deterministic direct evidence instead of scanning current workspace files.
    from earf.evidence import EvidenceRepository
    from earf.models import Evidence, EvidenceType

    direct_repo = EvidenceRepository()
    direct_repo.add(
        Evidence(
            evidence_type=EvidenceType.FILE,
            source="file",
            description="readme",
            identifier="README.md",
        )
    )

    results = RuleEvaluationService().evaluate_all(rules, direct_repo)
    score = ScoringService().score(results, rules)

    assert score.not_applicable_rules == 1
    assert score.overall_score == 50.0


def test_capability_provenance_for_agents(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("langgraph>=0.2.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_agents")

    assert detection.detected is True
    assert any(item.identifier == "langgraph" for item in detection.evidence)
