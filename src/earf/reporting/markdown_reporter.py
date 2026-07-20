from __future__ import annotations

from ..models import AssessmentReport


class MarkdownReporter:
    def render(self, report: AssessmentReport) -> str:
        return f"# {report.project_name}\n\nEARF {report.earf_version}\n"
