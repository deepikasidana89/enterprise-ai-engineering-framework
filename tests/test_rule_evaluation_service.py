from earf.evidence import EvidenceRepository
from earf.models import Evidence, EvidenceType, RuleDefinition, Severity
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleStatus


def _rule(rule_id: str, requirement: dict[str, object]) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title=f"{rule_id} title",
        description="desc",
        category="governance",
        severity=Severity.HIGH,
        applicability={"always": True},
        evidence_requirements=requirement,
    )


def test_evaluation_service_deterministic_ordering() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-002", {"evidence_type": "file", "identifiers": ["A"]}),
            _rule("GOV-001", {"evidence_type": "file", "identifiers": ["A"]}),
        ]
    )
    repo = EvidenceRepository()
    repo.add(
        Evidence(
            evidence_type=EvidenceType.FILE,
            source="file",
            description="d",
            identifier="A",
        )
    )

    results = RuleEvaluationService().evaluate_all(catalog, repo)
    assert [result.rule_id for result in results] == ["GOV-001", "SEC-002"]


def test_evaluation_service_evaluates_all_rules() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", {"evidence_type": "file", "identifiers": ["README.md"]}),
            _rule("SEC-001", {"evidence_type": "file", "identifiers": ["SECURITY.md"]}),
        ]
    )
    repo = EvidenceRepository()
    repo.add(
        Evidence(
            evidence_type=EvidenceType.FILE,
            source="file",
            description="d",
            identifier="README.md",
        )
    )

    results = RuleEvaluationService().evaluate_all(catalog, repo)

    assert len(results) == 2
    assert results[0].status == RuleStatus.PASS
    assert results[1].status == RuleStatus.FAIL
