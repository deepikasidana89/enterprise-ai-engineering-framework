from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import AssessmentReport


class Reporter(ABC):
    @abstractmethod
    def render(self, report: AssessmentReport) -> str:
        """Render an assessment report to a string."""
