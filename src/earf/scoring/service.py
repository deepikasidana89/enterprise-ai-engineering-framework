from __future__ import annotations

from dataclasses import dataclass

from ..models import Severity
from ..rules.catalog import RuleCatalog
from ..rules.results import RuleResult, RuleStatus
from .config import DEFAULT_SEVERITY_WEIGHTS, ReadinessThresholds
from .models import CategoryScoreDetail, ProductionReadiness, ReadinessScore


@dataclass
class _CategoryAccumulator:
    earned_weight: int = 0
    possible_weight: int = 0
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    not_applicable_rules: int = 0
    disabled_rules: int = 0
    error_rules: int = 0
    critical_failures: int = 0
    high_failures: int = 0


class ScoringService:
    def __init__(
        self,
        severity_weights: dict[Severity, int] | None = None,
        thresholds: ReadinessThresholds | None = None,
    ) -> None:
        self._weights = dict(DEFAULT_SEVERITY_WEIGHTS)
        if severity_weights is not None:
            self._weights.update(severity_weights)
        self._thresholds = thresholds or ReadinessThresholds()

    def score(
        self,
        results: list[RuleResult],
        catalog: RuleCatalog,
    ) -> ReadinessScore:
        rules = catalog.all()
        known_rule_ids = {rule.id for rule in rules}
        result_by_id = {result.rule_id: result for result in results}

        total_rules = 0
        passed_rules = 0
        failed_rules = 0
        not_applicable_rules = 0
        disabled_rules = 0
        error_rules = 0
        critical_failures = 0
        high_failures = 0

        earned_weight = 0
        possible_weight = 0

        category_accumulators: dict[str, _CategoryAccumulator] = {}

        for rule in rules:
            total_rules += 1
            status = result_by_id.get(rule.id, RuleResult(
                rule_id=rule.id,
                status=RuleStatus.ERROR,
                message="Missing rule result.",
                error="No result was provided for this rule.",
            )).status

            weight = self._weights.get(rule.severity, 0)
            category = rule.category
            category_state = category_accumulators.setdefault(category, _CategoryAccumulator())
            category_state.total_rules += 1

            if status == RuleStatus.PASS:
                passed_rules += 1
                category_state.passed_rules += 1
                earned_weight += weight
                possible_weight += weight
                category_state.earned_weight += weight
                category_state.possible_weight += weight
            elif status == RuleStatus.FAIL:
                failed_rules += 1
                category_state.failed_rules += 1
                possible_weight += weight
                category_state.possible_weight += weight
                if rule.severity == Severity.CRITICAL:
                    critical_failures += 1
                    category_state.critical_failures += 1
                if rule.severity == Severity.HIGH:
                    high_failures += 1
                    category_state.high_failures += 1
            elif status == RuleStatus.ERROR:
                error_rules += 1
                category_state.error_rules += 1
                possible_weight += weight
                category_state.possible_weight += weight
            elif status == RuleStatus.NOT_APPLICABLE:
                not_applicable_rules += 1
                category_state.not_applicable_rules += 1
            elif status == RuleStatus.DISABLED:
                disabled_rules += 1
                category_state.disabled_rules += 1

        overall_score = self._percentage(earned_weight, possible_weight)
        category_details = self._build_category_details(category_accumulators)
        category_scores = {
            category: detail.percentage for category, detail in category_details.items()
        }

        production = self._production_readiness(
            overall_score=overall_score,
            critical_failures=critical_failures,
        )

        unknown_result_count = sum(
            1 for result in results if result.rule_id not in known_rule_ids
        )

        summary: dict[str, object] = {
            "earned_weight": earned_weight,
            "possible_weight": possible_weight,
            "top_failing_categories": self._top_failing_categories(category_details),
            "lowest_scoring_categories": self._lowest_scoring_categories(category_details),
            "category_ranking": self._category_ranking(category_details),
            "critical_failures": critical_failures,
            "high_failures": high_failures,
            "unknown_result_count": unknown_result_count,
        }

        return ReadinessScore(
            overall_score=overall_score,
            category_scores=category_scores,
            total_rules=total_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            not_applicable_rules=not_applicable_rules,
            disabled_rules=disabled_rules,
            error_rules=error_rules,
            critical_failures=critical_failures,
            high_failures=high_failures,
            summary=summary,
            production_readiness=production,
            category_details=category_details,
        )

    def _build_category_details(
        self,
        category_accumulators: dict[str, _CategoryAccumulator],
    ) -> dict[str, CategoryScoreDetail]:
        details: dict[str, CategoryScoreDetail] = {}
        for category, state in category_accumulators.items():
            details[category] = CategoryScoreDetail(
                category=category,
                earned_weight=state.earned_weight,
                possible_weight=state.possible_weight,
                percentage=self._percentage(state.earned_weight, state.possible_weight),
                total_rules=state.total_rules,
                passed_rules=state.passed_rules,
                failed_rules=state.failed_rules,
                not_applicable_rules=state.not_applicable_rules,
                disabled_rules=state.disabled_rules,
                error_rules=state.error_rules,
                critical_failures=state.critical_failures,
                high_failures=state.high_failures,
            )
        return details

    def _production_readiness(
        self,
        overall_score: float,
        critical_failures: int,
    ) -> ProductionReadiness:
        if critical_failures > 0:
            return ProductionReadiness.NOT_READY
        if overall_score >= self._thresholds.ready:
            return ProductionReadiness.READY
        if overall_score >= self._thresholds.ready_with_warnings:
            return ProductionReadiness.READY_WITH_WARNINGS
        return ProductionReadiness.NOT_READY

    def _percentage(self, earned: int, possible: int) -> float:
        if possible <= 0:
            return 0.0
        return round((earned / possible) * 100, 1)

    def _top_failing_categories(
        self,
        category_details: dict[str, CategoryScoreDetail],
        limit: int = 3,
    ) -> list[str]:
        ranked = sorted(
            category_details.values(),
            key=lambda item: (-item.failed_rules, item.percentage, item.category),
        )
        return [item.category for item in ranked if item.failed_rules > 0][:limit]

    def _category_ranking(
        self,
        category_details: dict[str, CategoryScoreDetail],
    ) -> list[str]:
        ranked = sorted(
            category_details.values(),
            key=lambda item: (-item.percentage, item.category),
        )
        return [item.category for item in ranked]

    def _lowest_scoring_categories(
        self,
        category_details: dict[str, CategoryScoreDetail],
        limit: int = 3,
    ) -> list[str]:
        ranked = sorted(
            category_details.values(),
            key=lambda item: (item.percentage, item.category),
        )
        return [item.category for item in ranked][:limit]
