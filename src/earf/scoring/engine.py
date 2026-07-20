from __future__ import annotations

from typing import List, Tuple

from ..models import RuleResult, CategoryScore


class ScoringEngine:
    def calculate(self, results: List[RuleResult]) -> Tuple[float, List[CategoryScore], str]:
        raise NotImplementedError("Scoring is not implemented in Phase 1")
