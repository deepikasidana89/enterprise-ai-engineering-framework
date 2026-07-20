from __future__ import annotations

from pathlib import Path
from typing import List

from .models import RuleDefinition


class RuleLoader:
    def load(self, path: Path) -> List[RuleDefinition]:
        raise NotImplementedError("Rule loading is not implemented in Phase 1")
