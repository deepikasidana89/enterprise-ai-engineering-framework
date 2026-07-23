from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Mapping

from ..rules.results import RuleResult
from ..scoring.models import ReadinessScore

if TYPE_CHECKING:
    from ..pipeline import AnalysisResult


@dataclass(frozen=True)
class ReadinessReport:
    repository_name: str
    generated_at: datetime
    earf_version: str
    readiness_score: ReadinessScore
    rule_results: tuple[RuleResult, ...]
    total_evidence: int
    metadata: Mapping[str, object] = field(default_factory=dict)
    analysis_result: AnalysisResult | None = None
