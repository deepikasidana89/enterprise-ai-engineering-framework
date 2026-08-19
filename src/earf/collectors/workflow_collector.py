from __future__ import annotations

from .base import EvidenceCollector
from .workspace_index import ensure_workspace_index
from ..models import Evidence, EvidenceType, RepositoryContext


class WorkflowCollector(EvidenceCollector):
    name = "workflow"

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        index = ensure_workspace_index(context)

        items: list[Evidence] = []
        workflow_files = [item for item in index.files if item.is_workflow]
        for workflow in workflow_files:
            rel_path = workflow.relative_path
            items.append(
                Evidence(
                    evidence_type=EvidenceType.WORKFLOW,
                    source=self.name,
                    description=f"Workflow file found: {workflow.path.name}",
                    identifier=workflow.path.name,
                    path=rel_path,
                    location=rel_path,
                    metadata={"collector": self.name},
                )
            )

        return items
