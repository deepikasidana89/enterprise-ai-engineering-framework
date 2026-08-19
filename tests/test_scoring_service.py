from __future__ import annotations

from earf.models import ControlTier, RuleDefinition, Severity
from earf.rules.catalog import RuleCatalog
from earf.rules.results import RuleResult, RuleStatus
from earf.scoring.config import DEFAULT_SEVERITY_WEIGHTS, ReadinessThresholds
from earf.scoring.models import ProductionReadiness
from earf.scoring.service import ScoringService


def _rule(
    rule_id: str,
    *,
    category: str,
    severity: Severity,
    tier: ControlTier = ControlTier.CORE,
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title=f"{rule_id} title",
        description="desc",
        category=category,
        severity=severity,
        tier=tier,
        applicability={"always": True},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )


def _result(rule_id: str, status: RuleStatus) -> RuleResult:
    return RuleResult(rule_id=rule_id, status=status, message="status")


def test_default_severity_weights_are_configured() -> None:
    assert DEFAULT_SEVERITY_WEIGHTS[Severity.CRITICAL] == 10
    assert DEFAULT_SEVERITY_WEIGHTS[Severity.HIGH] == 7
    assert DEFAULT_SEVERITY_WEIGHTS[Severity.MEDIUM] == 4
    assert DEFAULT_SEVERITY_WEIGHTS[Severity.LOW] == 2
    assert DEFAULT_SEVERITY_WEIGHTS[Severity.INFO] == 1


def test_overall_score_uses_weighted_earned_over_possible() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL),
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.PASS),
        _result("GOV-001", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.overall_score == 58.8
    assert score.passed_rules == 1
    assert score.failed_rules == 1


def test_category_scores_include_earned_possible_percentage() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("GOV-002", category="governance", severity=Severity.LOW),
            _rule("SEC-001", category="security", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("GOV-002", RuleStatus.FAIL),
        _result("SEC-001", RuleStatus.PASS),
    ]

    score = ScoringService().score(results, catalog)

    assert score.category_scores["governance"] == 77.8
    assert score.category_scores["security"] == 100.0
    assert score.category_details["governance"].earned_weight == 7
    assert score.category_details["governance"].possible_weight == 9


def test_not_applicable_excluded_from_denominator() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("SEC-001", category="security", severity=Severity.CRITICAL),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("SEC-001", RuleStatus.NOT_APPLICABLE),
    ]

    score = ScoringService().score(results, catalog)

    assert score.overall_score == 100.0
    assert score.not_applicable_rules == 1
    assert score.assessment_coverage.percentage == 100.0


def test_disabled_excluded_from_denominator() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("SEC-001", category="security", severity=Severity.CRITICAL),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("SEC-001", RuleStatus.DISABLED),
    ]

    score = ScoringService().score(results, catalog)

    assert score.overall_score == 100.0
    assert score.disabled_rules == 1


def test_error_counts_as_zero_and_included_in_denominator() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL),
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.ERROR),
        _result("GOV-001", RuleStatus.PASS),
    ]

    score = ScoringService().score(results, catalog)

    assert score.overall_score == 41.2
    assert score.error_rules == 1
    assert score.assessment_coverage.percentage == 50.0
    assert score.assessment_coverage.evaluated == 1
    assert score.assessment_coverage.applicable == 2


def test_production_readiness_thresholds_are_configurable() -> None:
    catalog = RuleCatalog([
        _rule("GOV-001", category="governance", severity=Severity.HIGH),
        _rule("REL-001", category="reliability", severity=Severity.LOW),
    ])
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("REL-001", RuleStatus.FAIL),
    ]

    service = ScoringService(
        thresholds=ReadinessThresholds(
            ready=90.0,
            ready_with_warnings=75.0,
        )
    )
    score = service.score(results, catalog)

    assert score.overall_score == 77.8
    assert score.production_readiness == ProductionReadiness.READY_WITH_WARNINGS


def test_critical_failure_gate_forces_not_ready() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL),
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("MOD-001", category="modeling", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.FAIL),
        _result("GOV-001", RuleStatus.PASS),
        _result("MOD-001", RuleStatus.PASS),
    ]

    score = ScoringService().score(results, catalog)

    assert score.overall_score == 58.3
    assert score.critical_failures == 1
    assert score.production_readiness == ProductionReadiness.NOT_READY


def test_rounding_to_one_decimal() -> None:
    catalog = RuleCatalog([
        _rule("GOV-001", category="governance", severity=Severity.HIGH),
        _rule("REL-001", category="reliability", severity=Severity.MEDIUM),
    ])
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("REL-001", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.overall_score == 63.6


def test_empty_catalog_has_zero_scores_and_no_categories() -> None:
    score = ScoringService().score([], RuleCatalog([]))

    assert score.overall_score == 0.0
    assert score.category_scores == {}
    assert score.total_rules == 0
    assert score.production_readiness == ProductionReadiness.NOT_READY
    assert score.assessment_coverage.percentage == 0.0


def test_summary_helpers_rank_categories() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("SEC-001", category="security", severity=Severity.HIGH),
            _rule("REL-001", category="reliability", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("SEC-001", RuleStatus.FAIL),
        _result("REL-001", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.top_failing_categories() == ["reliability", "security"]
    assert score.lowest_scoring_categories() == ["reliability", "security", "governance"]
    assert score.category_ranking() == ["governance", "reliability", "security"]


def test_custom_severity_weights_are_used() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("REL-001", category="reliability", severity=Severity.MEDIUM),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("REL-001", RuleStatus.FAIL),
    ]

    service = ScoringService(
        severity_weights={
            Severity.CRITICAL: 10,
            Severity.HIGH: 2,
            Severity.MEDIUM: 1,
            Severity.LOW: 1,
            Severity.INFO: 1,
        }
    )
    score = service.score(results, catalog)

    assert score.overall_score == 66.7


def test_manual_review_counts_without_penalizing_score_or_failures() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL),
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.MANUAL_REVIEW),
        _result("GOV-001", RuleStatus.PASS),
    ]

    score = ScoringService().score(results, catalog)

    assert score.manual_review_rules == 1
    assert score.failed_rules == 0
    assert score.critical_failures == 0
    assert score.overall_score == 100.0
    assert score.assessment_coverage.evaluated == 1
    assert score.assessment_coverage.applicable == 2
    assert score.assessment_coverage.percentage == 50.0


def test_manual_review_does_not_trigger_not_ready_gate() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL, tier=ControlTier.CORE),
            _rule("GOV-001", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.MANUAL_REVIEW),
        _result("GOV-001", RuleStatus.PASS),
    ]

    score = ScoringService().score(results, catalog)

    assert score.core_readiness_score == 100.0
    assert score.production_readiness == ProductionReadiness.READY


def test_advanced_failures_do_not_force_not_ready_when_core_is_ready() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL, tier=ControlTier.CORE),
            _rule("GOV-001", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
            _rule("MOD-001", category="modeling", severity=Severity.HIGH, tier=ControlTier.ADVANCED),
            _rule("EVA-001", category="evaluation", severity=Severity.HIGH, tier=ControlTier.ADVANCED),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.PASS),
        _result("GOV-001", RuleStatus.PASS),
        _result("MOD-001", RuleStatus.FAIL),
        _result("EVA-001", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.core_readiness_score == 100.0
    assert score.advanced_controls_score == 0.0
    assert score.production_readiness == ProductionReadiness.READY


def test_core_critical_failure_blocks_even_with_high_core_score() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.CRITICAL, tier=ControlTier.CORE),
            _rule("GOV-001", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
            _rule("REL-001", category="reliability", severity=Severity.HIGH, tier=ControlTier.CORE),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.FAIL),
        _result("GOV-001", RuleStatus.PASS),
        _result("REL-001", RuleStatus.PASS),
    ]

    score = ScoringService().score(results, catalog)

    assert score.core_readiness_score == 58.3
    assert score.production_readiness == ProductionReadiness.NOT_READY


def test_advanced_critical_failure_does_not_block_core_readiness() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.HIGH, tier=ControlTier.CORE),
            _rule("EVA-001", category="evaluation", severity=Severity.CRITICAL, tier=ControlTier.ADVANCED),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.PASS),
        _result("EVA-001", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.core_readiness_score == 100.0
    assert score.advanced_controls_score == 0.0
    assert score.production_readiness == ProductionReadiness.READY


def test_not_applicable_core_rules_do_not_penalize_core_score() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
            _rule("GOV-002", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
            _rule("GOV-003", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
            _rule("GOV-004", category="governance", severity=Severity.HIGH, tier=ControlTier.CORE),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("GOV-002", RuleStatus.PASS),
        _result("GOV-003", RuleStatus.FAIL),
        _result("GOV-004", RuleStatus.NOT_APPLICABLE),
    ]

    score = ScoringService().score(results, catalog)

    assert score.core_readiness_score == 66.7
    assert score.not_applicable_rules == 1


def test_assessment_coverage_formula_across_statuses() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("GOV-002", category="governance", severity=Severity.HIGH),
            _rule("GOV-003", category="governance", severity=Severity.HIGH),
            _rule("GOV-004", category="governance", severity=Severity.HIGH),
            _rule("GOV-005", category="governance", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("GOV-002", RuleStatus.FAIL),
        _result("GOV-003", RuleStatus.ERROR),
        _result("GOV-004", RuleStatus.NOT_APPLICABLE),
        _result("GOV-005", RuleStatus.DISABLED),
    ]

    score = ScoringService().score(results, catalog)

    assert score.assessment_coverage.evaluated == 2
    assert score.assessment_coverage.applicable == 3
    assert score.assessment_coverage.percentage == 66.7


def test_assessment_coverage_excludes_manual_review_from_evaluated() -> None:
    catalog = RuleCatalog(
        [
            _rule("GOV-001", category="governance", severity=Severity.HIGH),
            _rule("GOV-002", category="governance", severity=Severity.HIGH),
            _rule("GOV-003", category="governance", severity=Severity.HIGH),
            _rule("GOV-004", category="governance", severity=Severity.HIGH),
            _rule("GOV-005", category="governance", severity=Severity.HIGH),
        ]
    )
    results = [
        _result("GOV-001", RuleStatus.PASS),
        _result("GOV-002", RuleStatus.PASS),
        _result("GOV-003", RuleStatus.FAIL),
        _result("GOV-004", RuleStatus.FAIL),
        _result("GOV-005", RuleStatus.MANUAL_REVIEW),
    ]

    score = ScoringService().score(results, catalog)

    assert score.assessment_coverage.evaluated == 4
    assert score.assessment_coverage.applicable == 5
    assert score.assessment_coverage.percentage == 80.0


def test_category_with_only_manual_review_has_no_scored_weight() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.HIGH),
            _rule("SEC-002", category="security", severity=Severity.MEDIUM),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.MANUAL_REVIEW),
        _result("SEC-002", RuleStatus.MANUAL_REVIEW),
    ]

    score = ScoringService().score(results, catalog)

    assert score.category_details["security"].possible_weight == 0
    assert score.category_details["security"].passed_rules == 0
    assert score.category_details["security"].failed_rules == 0
    assert score.category_details["security"].manual_review_rules == 2


def test_category_with_no_applicable_controls_is_not_assessed() -> None:
    catalog = RuleCatalog(
        [
            _rule("EVA-001", category="evaluation", severity=Severity.HIGH),
            _rule("EVA-002", category="evaluation", severity=Severity.MEDIUM),
        ]
    )
    results = [
        _result("EVA-001", RuleStatus.NOT_APPLICABLE),
        _result("EVA-002", RuleStatus.NOT_APPLICABLE),
    ]

    score = ScoringService().score(results, catalog)

    assert score.category_scores["evaluation"] is None
    assert score.category_details["evaluation"].assessment_status == "NOT_ASSESSED"


def test_category_with_applicable_controls_all_failed_scores_zero() -> None:
    catalog = RuleCatalog(
        [
            _rule("SEC-001", category="security", severity=Severity.HIGH),
            _rule("SEC-002", category="security", severity=Severity.MEDIUM),
        ]
    )
    results = [
        _result("SEC-001", RuleStatus.FAIL),
        _result("SEC-002", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.category_scores["security"] == 0.0
    assert score.category_details["security"].assessment_status == "ASSESSED"


def test_category_with_mixed_pass_fail_uses_weighted_formula() -> None:
    catalog = RuleCatalog(
        [
            _rule("REL-001", category="reliability", severity=Severity.HIGH),
            _rule("REL-002", category="reliability", severity=Severity.MEDIUM),
        ]
    )
    results = [
        _result("REL-001", RuleStatus.PASS),
        _result("REL-002", RuleStatus.FAIL),
    ]

    score = ScoringService().score(results, catalog)

    assert score.category_scores["reliability"] == 63.6
