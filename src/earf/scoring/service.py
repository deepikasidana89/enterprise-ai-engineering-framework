from __future__ import annotations

from dataclasses import dataclass

from ..models import ControlTier, Severity
from ..rules.catalog import RuleCatalog
from ..rules.results import RuleResult, RuleStatus
from .config import DEFAULT_SEVERITY_WEIGHTS, ReadinessThresholds
from .models import (
    AssessmentCoverage,
    CategoryScoreDetail,
    ProductionReadiness,
    ReadinessScore,
    TierScoreDetail,
)


@dataclass
class _CategoryAccumulator:
    earned_weight: int = 0
    possible_weight: int = 0
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    manual_review_rules: int = 0
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
        manual_review_rules = 0
        not_applicable_rules = 0
        disabled_rules = 0
        error_rules = 0
        critical_failures = 0
        high_failures = 0

        earned_weight = 0
        possible_weight = 0

        category_accumulators: dict[str, _CategoryAccumulator] = {}
        tier_accumulators: dict[ControlTier, _CategoryAccumulator] = {
            ControlTier.CORE: _CategoryAccumulator(),
            ControlTier.ADVANCED: _CategoryAccumulator(),
        }
        coverage_applicable = 0
        coverage_evaluated = 0

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
            tier_state = tier_accumulators.setdefault(rule.tier, _CategoryAccumulator())
            category_state.total_rules += 1
            tier_state.total_rules += 1

            if status == RuleStatus.PASS:
                passed_rules += 1
                coverage_applicable += 1
                coverage_evaluated += 1
                category_state.passed_rules += 1
                tier_state.passed_rules += 1
                earned_weight += weight
                possible_weight += weight
                category_state.earned_weight += weight
                category_state.possible_weight += weight
                tier_state.earned_weight += weight
                tier_state.possible_weight += weight
            elif status == RuleStatus.FAIL:
                failed_rules += 1
                coverage_applicable += 1
                coverage_evaluated += 1
                category_state.failed_rules += 1
                tier_state.failed_rules += 1
                possible_weight += weight
                category_state.possible_weight += weight
                tier_state.possible_weight += weight
                if rule.severity == Severity.CRITICAL:
                    critical_failures += 1
                    category_state.critical_failures += 1
                    tier_state.critical_failures += 1
                if rule.severity == Severity.HIGH:
                    high_failures += 1
                    category_state.high_failures += 1
                    tier_state.high_failures += 1
            elif status == RuleStatus.MANUAL_REVIEW:
                manual_review_rules += 1
                failed_rules += 1
                coverage_applicable += 1
                coverage_evaluated += 1
                category_state.manual_review_rules += 1
                category_state.failed_rules += 1
                tier_state.manual_review_rules += 1
                tier_state.failed_rules += 1
                possible_weight += weight
                category_state.possible_weight += weight
                tier_state.possible_weight += weight
                if rule.severity == Severity.CRITICAL:
                    critical_failures += 1
                    category_state.critical_failures += 1
                    tier_state.critical_failures += 1
                if rule.severity == Severity.HIGH:
                    high_failures += 1
                    category_state.high_failures += 1
                    tier_state.high_failures += 1
            elif status == RuleStatus.ERROR:
                error_rules += 1
                coverage_applicable += 1
                category_state.error_rules += 1
                tier_state.error_rules += 1
                possible_weight += weight
                category_state.possible_weight += weight
                tier_state.possible_weight += weight
            elif status == RuleStatus.NOT_APPLICABLE:
                not_applicable_rules += 1
                category_state.not_applicable_rules += 1
                tier_state.not_applicable_rules += 1
            elif status == RuleStatus.DISABLED:
                disabled_rules += 1
                category_state.disabled_rules += 1
                tier_state.disabled_rules += 1

        overall_score = self._percentage(earned_weight, possible_weight)
        category_details = self._build_category_details(category_accumulators)
        tier_details = self._build_tier_details(tier_accumulators)
        category_scores = {
            category: detail.percentage for category, detail in category_details.items()
        }

        core_detail = tier_details[ControlTier.CORE.value]
        advanced_detail = tier_details[ControlTier.ADVANCED.value]
        core_readiness_score = core_detail.score
        advanced_controls_score = advanced_detail.score

        production = self._production_readiness(
            overall_score=core_readiness_score,
            critical_failures=core_detail.critical_failures,
        )

        assessment_coverage = AssessmentCoverage(
            percentage=self._percentage(coverage_evaluated, coverage_applicable),
            evaluated=coverage_evaluated,
            applicable=coverage_applicable,
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
            "manual_review_rules": manual_review_rules,
            "unknown_result_count": unknown_result_count,
            "core_readiness_score": core_readiness_score,
            "advanced_controls_score": advanced_controls_score,
            "assessment_coverage": {
                "percentage": assessment_coverage.percentage,
                "evaluated": assessment_coverage.evaluated,
                "applicable": assessment_coverage.applicable,
            },
        }

        return ReadinessScore(
            overall_score=overall_score,
            core_readiness_score=core_readiness_score,
            advanced_controls_score=advanced_controls_score,
            category_scores=category_scores,
            total_rules=total_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            manual_review_rules=manual_review_rules,
            not_applicable_rules=not_applicable_rules,
            disabled_rules=disabled_rules,
            error_rules=error_rules,
            critical_failures=critical_failures,
            high_failures=high_failures,
            summary=summary,
            production_readiness=production,
            category_details=category_details,
            tier_details=tier_details,
            assessment_coverage=assessment_coverage,
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
                manual_review_rules=state.manual_review_rules,
                not_applicable_rules=state.not_applicable_rules,
                disabled_rules=state.disabled_rules,
                error_rules=state.error_rules,
                critical_failures=state.critical_failures,
                high_failures=state.high_failures,
            )
        return details

    def _build_tier_details(
        self,
        tier_accumulators: dict[ControlTier, _CategoryAccumulator],
    ) -> dict[str, TierScoreDetail]:
        details: dict[str, TierScoreDetail] = {}
        for tier in (ControlTier.CORE, ControlTier.ADVANCED):
            state = tier_accumulators.get(tier, _CategoryAccumulator())
            details[tier.value] = TierScoreDetail(
                tier=tier,
                score=self._percentage(state.earned_weight, state.possible_weight),
                earned_weight=state.earned_weight,
                possible_weight=state.possible_weight,
                total_rules=state.total_rules,
                passed_rules=state.passed_rules,
                failed_rules=state.failed_rules,
                manual_review_rules=state.manual_review_rules,
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
