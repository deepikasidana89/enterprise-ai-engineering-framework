from __future__ import annotations

from typing import List

from .base import EvidenceCollector
from ..models import Evidence, RepositoryContext


class ConfigurationEvidenceCollector(EvidenceCollector):
    name = "configuration"

    def collect(self, context: RepositoryContext) -> List[Evidence]:
        # Phase 1: placeholder
        return []
