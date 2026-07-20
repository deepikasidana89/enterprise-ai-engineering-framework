from __future__ import annotations

from typing import List

from .base import EvidenceCollector
from ..models import Evidence, RepositoryContext


class DependencyEvidenceCollector(EvidenceCollector):
    name = "dependency"

    def collect(self, context: RepositoryContext) -> List[Evidence]:
        # Phase 1: placeholder
        return []
