from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import Evidence, RepositoryContext


class EvidenceCollector(ABC):
    """Abstract base for evidence collectors."""

    name: str

    @abstractmethod
    def collect(self, context: RepositoryContext) -> List[Evidence]:
        """Collect evidence from the provided repository context."""
