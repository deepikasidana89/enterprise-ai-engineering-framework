from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
from typing import List, Optional, TypeAlias

MetadataValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | list["MetadataValue"]
    | dict[str, "MetadataValue"]
)

Metadata: TypeAlias = dict[str, MetadataValue]


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
    CODE_PATTERN = "CODE_PATTERN"
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
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    evidence_type: EvidenceType
    source: str
    description: str
    identifier: str = ""
    path: Optional[str] = None
    location: Optional[str] = None
    metadata: Metadata = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    title: str
    description: str
    category: str
    severity: Severity
    version: str = "1.0"
    enabled: bool = True
    applicability: Metadata = field(default_factory=dict)
    rationale: str = ""
    failure_message: str = ""
    recommendation: str = ""
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    evidence_requirements: Metadata = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        required_fields = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "version": self.version,
        }
        for field_name, value in required_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        if re.fullmatch(r"^[A-Z]{3}-\d{3}$", self.id.strip()) is None:
            raise ValueError(
                f"id must match pattern ^[A-Z]{{3}}-\\d{{3}}$, got {self.id!r}"
            )


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
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

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
    metadata: Metadata = field(default_factory=dict)
