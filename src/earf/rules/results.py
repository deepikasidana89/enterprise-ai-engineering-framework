from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..models import Evidence, Metadata


class RuleStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    status: RuleStatus
    message: str
    matched_evidence: list[Evidence] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    metadata: Metadata = field(default_factory=dict)
    error: str | None = None
