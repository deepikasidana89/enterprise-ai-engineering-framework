from __future__ import annotations

import json
from ..models import AssessmentReport


class JsonReporter:
    def render(self, report: AssessmentReport) -> str:
        return json.dumps({"project": report.project_name, "earf_version": report.earf_version})
