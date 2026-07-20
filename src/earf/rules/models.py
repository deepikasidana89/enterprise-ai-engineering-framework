from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..models import Severity


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    title: str
    description: str
    category: str
    severity: Severity
    version: str
    applicability: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
