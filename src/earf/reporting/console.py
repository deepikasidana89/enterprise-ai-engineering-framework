from __future__ import annotations

from ..models import AssessmentReport
from .. import __version__


class ConsoleReporter:
    def render(self, report: AssessmentReport) -> str:
        return f"Project: {report.project_name} - EARF {__version__}"
