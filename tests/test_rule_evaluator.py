from earf.evidence import EvidenceRepository
from earf.models import Evidence, EvidenceType, RuleDefinition, Severity
from earf.rules.evaluator import RuleEvaluator
from earf.rules.results import RuleResult, RuleStatus


AI_DEPENDENCY_APPLICABILITY = {
    "any": [
        {
            "evidence_type": "dependency",
            "identifiers": [
                "openai",
                "anthropic",
                "langchain",
                "langgraph",
                "transformers",
                "llama-index",
                "litellm",
                "semantic-kernel",
                "google-generativeai",
                "azure-ai-inference",
            ],
        }
    ]
}


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
        applicability={"always": True} if applicability is None else applicability,
        evidence_requirements=evidence_requirements or {},
    )


def _rule_with_failure_message(
    message: str,
    *,
    evidence_requirements: dict[str, object] | None = None,
) -> RuleDefinition:
    return RuleDefinition(
        id="SAF-001",
        title="Input validation is present",
        description="Sample description",
        category="safety",
        severity=Severity.HIGH,
        enabled=True,
        applicability={"always": True},
        evidence_requirements=evidence_requirements or {
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
        failure_message=message,
    )


def _evidence(
    evidence_type: EvidenceType,
    identifier: str,
    *,
    source: str = "collector",
    path: str | None = None,
    metadata: dict[str, object] | None = None,
) -> Evidence:
    return Evidence(
        evidence_type=evidence_type,
        source=source,
        description="sample",
        identifier=identifier,
        path=path,
        location=path,
        metadata=metadata or {},
    )


def test_rule_status_values() -> None:
    assert RuleStatus.PASS.value == "pass"
    assert RuleStatus.FAIL.value == "fail"
    assert RuleStatus.MANUAL_REVIEW.value == "manual_review"
    assert RuleStatus.NEEDS_SEMANTIC_REVIEW.value == "needs_semantic_review"
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


def test_rule_without_applicability_behaves_normally() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md"))

    rule = _rule(
        applicability={},
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_ai_context_makes_rule_applicable_and_passes() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.DEPENDENCY, "openai"))
    repo.add(_evidence(EvidenceType.FILE, "README.md"))

    rule = _rule(
        applicability=AI_DEPENDENCY_APPLICABILITY,
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS
    assert result.matched_evidence


def test_ai_context_rule_can_fail_when_requirements_missing() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.DEPENDENCY, "openai"))

    rule = _rule(
        applicability=AI_DEPENDENCY_APPLICABILITY,
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL
    assert result.missing_requirements


def test_non_applicable_rule_returns_not_applicable() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md"))

    rule = _rule(
        applicability=AI_DEPENDENCY_APPLICABILITY,
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.NOT_APPLICABLE
    assert result.missing_requirements == []
    assert result.message == "Rule is not applicable to this repository."


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


def test_uncertain_llm_capability_returns_needs_semantic_review() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.CODE_PATTERN, "ai_gateway_usage", path="service.py"))
    repo.add(_evidence(EvidenceType.CODE_PATTERN, "prompt_template_usage", path="service.py"))

    rule = _rule(
        rule_id="EVA-001",
        applicability={"all": [{"capability": "uses_llm"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.NEEDS_SEMANTIC_REVIEW
    assert "applicability_reason" in result.metadata
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


def test_scope_filtering_passes_with_matching_scope() -> None:
    repo = EvidenceRepository()
    repo.add(
        _evidence(
            EvidenceType.CODE_PATTERN,
            "python_tenacity_retry",
            source="code_pattern",
            path="src/service.py",
            metadata={"source_scope": "production"},
        )
    )

    rule = _rule(
        evidence_requirements={
            "evidence_type": "code_pattern",
            "scope": "production",
            "identifiers": ["python_tenacity_retry"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS


def test_scope_filtering_fails_when_scope_mismatch() -> None:
    repo = EvidenceRepository()
    repo.add(
        _evidence(
            EvidenceType.CODE_PATTERN,
            "python_tenacity_retry",
            source="code_pattern",
            path="src/service.py",
            metadata={"source_scope": "production"},
        )
    )

    rule = _rule(
        evidence_requirements={
            "evidence_type": "code_pattern",
            "scope": "test",
            "identifiers": ["python_tenacity_retry"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL
    assert any("scope=test" in item for item in result.missing_requirements)


def test_scope_filter_invalid_value_returns_error() -> None:
    repo = EvidenceRepository()
    rule = _rule(
        evidence_requirements={
            "evidence_type": "code_pattern",
            "scope": "staging",
            "identifiers": ["python_tenacity_retry"],
        }
    )
    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.ERROR


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


def test_fail_uses_rule_failure_message_when_present() -> None:
    repo = EvidenceRepository()
    rule = _rule_with_failure_message(
        "Input validation evidence was not detected.",
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )

    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL
    assert result.message == "Input validation evidence was not detected."


def test_fail_uses_generic_fallback_message_when_rule_has_no_failure_message() -> None:
    repo = EvidenceRepository()
    rule = _rule(
        rule_id="OBS-001",
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )

    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.FAIL
    assert result.message == "Required evidence for this control was not detected."


def test_pass_does_not_use_failure_message() -> None:
    repo = EvidenceRepository()
    repo.add(_evidence(EvidenceType.FILE, "README.md"))
    rule = _rule_with_failure_message(
        "Input validation evidence was not detected.",
        evidence_requirements={
            "evidence_type": "file",
            "identifiers": ["README.md"],
        },
    )

    result = RuleEvaluator().evaluate(rule, repo)

    assert result.status == RuleStatus.PASS
    assert result.message != "Input validation evidence was not detected."
