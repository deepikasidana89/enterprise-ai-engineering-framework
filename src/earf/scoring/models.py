from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..models import ControlTier


class ProductionReadiness(Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class CategoryScoreDetail:
    category: str
    earned_weight: int
    possible_weight: int
    percentage: float
    total_rules: int
    passed_rules: int
    failed_rules: int
    manual_review_rules: int
    not_applicable_rules: int
    disabled_rules: int
    error_rules: int
    critical_failures: int
    high_failures: int


@dataclass(frozen=True)
class TierScoreDetail:
    tier: ControlTier
    score: float
    earned_weight: int
    possible_weight: int
    total_rules: int
    passed_rules: int
    failed_rules: int
    manual_review_rules: int
    not_applicable_rules: int
    disabled_rules: int
    error_rules: int
    critical_failures: int
    high_failures: int


@dataclass(frozen=True)
class AssessmentCoverage:
    percentage: float
    evaluated: int
    applicable: int


@dataclass(frozen=True)
class ReadinessScore:
    overall_score: float
    category_scores: dict[str, float]
    total_rules: int
    passed_rules: int
    failed_rules: int
    not_applicable_rules: int
    disabled_rules: int
    error_rules: int
    critical_failures: int
    high_failures: int
    manual_review_rules: int = 0
    summary: dict[str, object] = field(default_factory=dict)
    production_readiness: ProductionReadiness = ProductionReadiness.NOT_READY
    category_details: dict[str, CategoryScoreDetail] = field(default_factory=dict)
    core_readiness_score: float = 0.0
    advanced_controls_score: float = 0.0
    tier_details: dict[str, TierScoreDetail] = field(default_factory=dict)
    assessment_coverage: AssessmentCoverage = field(
        default_factory=lambda: AssessmentCoverage(percentage=0.0, evaluated=0, applicable=0)
    )

    def top_failing_categories(self, limit: int = 3) -> list[str]:
        ranked = sorted(
            self.category_details.values(),
            key=lambda item: (-item.failed_rules, item.percentage, item.category),
        )
        return [item.category for item in ranked if item.failed_rules > 0][:limit]

    def category_ranking(self) -> list[str]:
        ranked = sorted(
            self.category_details.values(),
            key=lambda item: (-item.percentage, item.category),
        )
        return [item.category for item in ranked]

    def lowest_scoring_categories(self, limit: int = 3) -> list[str]:
        ranked = sorted(
            self.category_details.values(),
            key=lambda item: (item.percentage, item.category),
        )
        return [item.category for item in ranked][:limit]
