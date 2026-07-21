from __future__ import annotations

from .base import EvidenceCollector
from ..models import Evidence, EvidenceType, RepositoryContext


class WorkflowCollector(EvidenceCollector):
    name = "workflow"

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        root = context.root_path
        workflows_dir = root / ".github" / "workflows"
        if not workflows_dir.is_dir():
            return []

        items: list[Evidence] = []
        for workflow in sorted(
            (p for p in workflows_dir.iterdir() if p.is_file()),
            key=lambda p: p.name,
        ):
            rel_path = str(workflow.relative_to(root))
            items.append(
                Evidence(
                    evidence_type=EvidenceType.WORKFLOW,
                    source=self.name,
                    description=f"Workflow file found: {workflow.name}",
                    identifier=workflow.name,
                    path=rel_path,
                    location=rel_path,
                    metadata={"collector": self.name},
                )
            )

        return items
