from __future__ import annotations

from pathlib import Path

from earf.evidence_collection import EvidenceCollectionService
from earf.models import RepositoryContext
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleStatus

SUPPORTED_RULE_EVIDENCE_TYPES = {"file", "dependency", "workflow", "configuration"}


def _rules_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "rules"


def _repo_context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def _evaluate_rules(repo_path: Path) -> dict[str, RuleStatus]:
    catalog, _ = RuleCatalog.from_path(_rules_dir())
    evidence_repo = EvidenceCollectionService().collect(_repo_context(repo_path))
    results = RuleEvaluationService().evaluate_all(catalog, evidence_repo)
    return {result.rule_id: result.status for result in results}


def _collect_direct_requirements(requirement: dict[str, object]) -> list[dict[str, object]]:
    direct: list[dict[str, object]] = []

    if "any" in requirement:
        children = requirement["any"]
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    direct.extend(_collect_direct_requirements(child))
        return direct

    if "all" in requirement:
        children = requirement["all"]
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    direct.extend(_collect_direct_requirements(child))
        return direct

    if "evidence_type" in requirement:
        direct.append(requirement)
    return direct


def test_real_rules_use_only_supported_collector_evidence_types() -> None:
    catalog, _ = RuleCatalog.from_path(_rules_dir())

    for rule in catalog.all():
        requirements = _collect_direct_requirements(rule.evidence_requirements)
        assert requirements, f"{rule.id} must define at least one direct requirement"

        for req in requirements:
            evidence_type = req.get("evidence_type")
            assert isinstance(evidence_type, str)
            assert evidence_type in SUPPORTED_RULE_EVIDENCE_TYPES


def test_populated_repository_satisfies_all_rules(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# AI system purpose", encoding="utf-8")
    (tmp_path / "CODEOWNERS").write_text("* @team", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("Security policy", encoding="utf-8")
    (tmp_path / ".env.example").write_text("API_KEY=", encoding="utf-8")

    (tmp_path / "requirements.txt").write_text(
        "\n".join(
            [
                "openai==1.0.0",
                "opentelemetry-sdk==1.0.0",
                "tenacity==8.2.0",
                "pydantic==2.8.0",
                "guardrails-ai==0.5.0",
            ]
        ),
        encoding="utf-8",
    )

    (tmp_path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "sample-ai"',
                'version = "0.1.0"',
                "dependencies = [",
                '  "openai>=1.0",',
                '  "opentelemetry-sdk>=1.0",',
                '  "tenacity>=8.2",',
                '  "pydantic>=2.8",',
                '  "guardrails-ai>=0.5",',
                "]",
            ]
        ),
        encoding="utf-8",
    )

    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text("name: CI", encoding="utf-8")

    statuses = _evaluate_rules(tmp_path)

    assert len(statuses) == 12
    assert all(status == RuleStatus.PASS for status in statuses.values())


def test_repository_without_required_artifacts_fails_all_rules(tmp_path: Path) -> None:
    statuses = _evaluate_rules(tmp_path)

    assert len(statuses) == 12
    assert all(status in {RuleStatus.FAIL, RuleStatus.NOT_APPLICABLE} for status in statuses.values())
    assert any(status == RuleStatus.NOT_APPLICABLE for status in statuses.values())
