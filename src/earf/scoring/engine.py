from __future__ import annotations

from ..models import Severity
from ..rules.catalog import RuleCatalog
from ..rules.results import RuleResult
from .config import ReadinessThresholds
from .models import ReadinessScore
from .service import ScoringService


class ScoringEngine:
    """Backward-compatible facade around Phase 5 ScoringService."""

    def __init__(
        self,
        severity_weights: dict[Severity, int] | None = None,
        thresholds: ReadinessThresholds | None = None,
    ) -> None:
        self._service = ScoringService(
            severity_weights=severity_weights,
            thresholds=thresholds,
        )

    def calculate(
        self,
        results: list[RuleResult],
        catalog: RuleCatalog,
    ) -> ReadinessScore:
        return self._service.score(results, catalog)
