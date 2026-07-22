from earf.evidence import EvidenceRepository
from earf.models import Evidence, EvidenceType, RuleDefinition, Severity
from earf.rules.evaluator import RuleEvaluator
from earf.rules.results import RuleResult, RuleStatus


def _rule(
    rule_id: str = "GOV-001",
    *,
    enabled: bool = True,
    applicability: dict[str, object] | None = None,
    evidence_requirements: dict[str, object] | None = None,
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title="Sample rule",
        description="Sample description",
        category="governance",
        severity=Severity.HIGH,
        enabled=enabled,
        applicability=applicability or {"always": True},
        evidence_requirements=evidence_requirements or {},
    )


def _evidence(
    evidence_type: EvidenceType,
    identifier: str,
    *,
    source: str = "collector",
    path: str | None = None,
) -> Evidence:
    return Evidence(
        evidence_type=evidence_type,
        source=source,
        description="sample",
        identifier=identifier,
        path=path,
        location=path,
    )


def test_rule_status_values() -> None:
    assert RuleStatus.PASS.value == "pass"
    assert RuleStatus.FAIL.value == "fail"
    assert RuleStatus.NOT_APPLICABLE.value == "not_applicable"
    assert RuleStatus.DISABLED.value == "disabled"
    assert RuleStatus.ERROR.value == "error"


def test_rule_result_has_no_scoring_fields() -> None:
    result = RuleResult(rule_id="GOV-001", status=RuleStatus.PASS, message="ok")
    assert not hasattr(result, "confidence")
    assert not hasattr(result, "score")


def test_direct_requirement_matching_pass() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md"))

    rule = _rule(
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS
    assert len(result.matched_evidence) == 1


def test_any_operator_succeeds_with_one_child() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "CODEOWNERS"))

    rule = _rule(
        evidence_requirements={
            "any": [
                {"evidence_type": "file", "identifiers": ["README.md"]},
                {"evidence_type": "file", "identifiers": ["CODEOWNERS"]},
            ]
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_any_operator_fails_when_none_match() -> None:
    repo = EvidenceRepository()

    rule = _rule(
        evidence_requirements={
            "any": [
                {"evidence_type": "file", "identifiers": ["README.md"]},
                {"evidence_type": "file", "identifiers": ["CODEOWNERS"]},
            ]
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL
    assert result.missing_requirements


def test_all_operator_succeeds_when_all_match() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md"))
    repo.add(_evidence(EvidenceType.FILE, "SECURITY.md"))

    rule = _rule(
        evidence_requirements={
            "all": [
                {"evidence_type": "file", "identifiers": ["README.md"]},
                {"evidence_type": "file", "identifiers": ["SECURITY.md"]},
            ]
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_all_operator_fails_when_one_missing() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md"))

    rule = _rule(
        evidence_requirements={
            "all": [
                {"evidence_type": "file", "identifiers": ["README.md"]},
                {"evidence_type": "file", "identifiers": ["SECURITY.md"]},
            ]
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL


def test_identifier_alternatives_match_any() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "OWNERS"))

    rule = _rule(
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["CODEOWNERS", "OWNERS"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_dependency_case_normalization() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.DEPENDENCY, "OpenAI"))

    rule = _rule(
        evidence_requirements={
            "evidence_type": "dependency",
            "identifiers": ["openai"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_source_filtering() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md", source="file_collector"))

    rule = _rule(
        evidence_requirements={
            "evidence_type": "file",
            "source": "file_collector",
            "identifiers": ["README.md"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_path_filtering() -> None:
    repo = EvidenceRepository()
    repo.add(
        _evidence(
            EvidenceType.WORKFLOW,
            "ci.yml",
            path=".github/workflows/ci.yml",
        )
    )

    rule = _rule(
        evidence_requirements={
            "evidence_type": "workflow",
            "path": [".github/workflows/ci.yml"],
            "identifiers": ["ci.yml"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_missing_evidence_fails() -> None:
    repo = EvidenceRepository()
    rule = _rule(
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL


def test_disabled_rule_not_evaluated() -> None:
    repo = EvidenceRepository()
    rule = _rule(enabled=False, evidence_requirements={"evidence_type": "file"})
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.DISABLED


def test_always_false_returns_not_applicable() -> None:
    repo = EvidenceRepository()
    rule = _rule(applicability={"always": False}, evidence_requirements={"evidence_type": "file"})
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.NOT_APPLICABLE


def test_invalid_requirement_structure_returns_error() -> None:
    repo = EvidenceRepository()
    rule = _rule(evidence_requirements={"any": {"evidence_type": "file"}})
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.ERROR
    assert result.error


def test_invalid_applicability_structure_returns_error() -> None:
    repo = EvidenceRepository()
    rule = _rule(applicability={"framework": "python"}, evidence_requirements={"evidence_type": "file"})
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.ERROR


def test_unexpected_evaluation_error_returns_error() -> None:
    class BrokenRepository(EvidenceRepository):
        def find(self, **kwargs):  # type: ignore[override]
            raise RuntimeError("broken")

    repo = BrokenRepository()
    rule = _rule(evidence_requirements={"evidence_type": "file"})
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.ERROR
    assert result.error == "broken"


def test_duplicate_evidence_not_duplicated_in_result() -> None:
    repo = EvidenceRepository()
    duplicate = _evidence(EvidenceType.FILE, "README.md")
    repo.add(duplicate)
    repo.add(duplicate)

    rule = _rule(
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS
    assert len(result.matched_evidence) == 1


def test_empty_evidence_repository_fails_when_applicable() -> None:
    repo = EvidenceRepository()
    rule = _rule(evidence_requirements={"evidence_type": "file"})
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL
