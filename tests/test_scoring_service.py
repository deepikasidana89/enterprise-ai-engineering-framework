from __future__ import annotations

from earf.models import RuleDefinition, Severity
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
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title=f"{rule_id} title",
        description="desc",
        category=category,
        severity=severity,
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
