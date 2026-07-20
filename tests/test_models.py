from pathlib import Path

import pytest

from earf.models import (
    ScanStatus,
    Severity,
    EvidenceType,
    RepositoryFile,
    RepositoryContext,
    RuleResult,
)


def test_enums_values() -> None:
    assert ScanStatus.PASS.value == "PASS"
    assert Severity.CRITICAL.value == "CRITICAL"
    assert EvidenceType.FILE.value == "FILE"


def test_repository_file_and_context_defaults(tmp_path: Path) -> None:
    rf = RepositoryFile(path=tmp_path / "x", relative_path=Path("x"), extension=".md", size_bytes=10)
    ctx = RepositoryContext(root_path=tmp_path, project_name="proj")
    assert rf.size_bytes == 10
    assert ctx.project_name == "proj"


def test_rule_result_confidence_validation() -> None:
    # Valid confidence
    r = RuleResult(rule_id="r1", status=ScanStatus.PASS, confidence=0.5)
    assert r.confidence == 0.5

    # Invalid confidence
    with pytest.raises(ValueError):
        RuleResult(rule_id="r2", status=ScanStatus.FAIL, confidence=1.5)
