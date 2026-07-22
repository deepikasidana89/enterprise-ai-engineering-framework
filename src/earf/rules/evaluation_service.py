from __future__ import annotations

from ..evidence import EvidenceRepository
from .catalog import RuleCatalog
from .evaluator import RuleEvaluator
from .results import RuleResult


class RuleEvaluationService:
    def __init__(self, evaluator: RuleEvaluator | None = None) -> None:
        self._evaluator = evaluator or RuleEvaluator()

    def evaluate_all(
        self,
        catalog: RuleCatalog,
        evidence_repository: EvidenceRepository,
    ) -> list[RuleResult]:
        results = [
            self._evaluator.evaluate(rule, evidence_repository)
            for rule in catalog.all()
        ]
        return sorted(results, key=lambda result: result.rule_id)
