from __future__ import annotations

from dataclasses import dataclass

from ..models import Severity

DEFAULT_SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.CRITICAL: 10,
    Severity.HIGH: 7,
    Severity.MEDIUM: 4,
    Severity.LOW: 2,
    Severity.INFO: 1,
}


@dataclass(frozen=True)
class ReadinessThresholds:
    ready: float = 85.0
    ready_with_warnings: float = 70.0
