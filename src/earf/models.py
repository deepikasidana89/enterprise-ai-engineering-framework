from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class ScanStatus(Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EvidenceType(Enum):
    FILE = "FILE"
    DEPENDENCY = "DEPENDENCY"
    CONFIGURATION = "CONFIGURATION"
    SOURCE_CODE = "SOURCE_CODE"
    DOCUMENTATION = "DOCUMENTATION"
    WORKFLOW = "WORKFLOW"
    MANUAL = "MANUAL"
    LLM_REVIEW = "LLM_REVIEW"


@dataclass(frozen=True)
class RepositoryFile:
    path: Path
    relative_path: Path
    extension: Optional[str]
    size_bytes: int


@dataclass
class RepositoryContext:
    root_path: Path
    project_name: str
    files: List[RepositoryFile] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    evidence_type: EvidenceType
    source: str
    description: str
    location: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    title: str
    description: str
    category: str
    severity: Severity
    version: str
    applicability: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class RuleResult:
    rule_id: str
    status: ScanStatus
    evidence: List[Evidence] = field(default_factory=list)
    explanation: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: float = 0.0
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class CategoryScore:
    category: str
    score: float
    applicable_rules: int = 0
    passed_rules: int = 0
    partial_rules: int = 0
    failed_rules: int = 0


@dataclass
class AssessmentReport:
    project_name: str
    earf_version: str
    overall_score: Optional[float] = None
    readiness_level: Optional[str] = None
    category_scores: List[CategoryScore] = field(default_factory=list)
    rule_results: List[RuleResult] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
