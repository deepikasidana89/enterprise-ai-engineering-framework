from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models import Metadata, Severity


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    title: str
    description: str
    category: str
    severity: Severity
    version: str
    applicability: Optional[str] = None
    metadata: Optional[Metadata] = None
