from __future__ import annotations

from typing import List

from ..models import RuleResult
from ..evidence import EvidenceRepository
from ..models import RepositoryContext


class RuleEngine:
    def evaluate(
        self,
        rules: List[object],
        evidence: EvidenceRepository,
        context: RepositoryContext,
    ) -> List[RuleResult]:
        raise NotImplementedError("Rule evaluation is not implemented in Phase 1")
