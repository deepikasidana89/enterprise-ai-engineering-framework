from __future__ import annotations

from pathlib import Path

from earf.evidence_collection import EvidenceCollectionService
from earf.models import RepositoryContext
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleStatus


def _rules_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "rules"


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_rel_002_passes_with_retry_code_pattern_without_retry_dependencies(tmp_path: Path) -> None:
    # Applicability now requires corroborated AI capability evidence. A lone AI
    # dependency keeps applicability in semantic-review state.
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0", encoding="utf-8")
    (tmp_path / "service.py").write_text(
        "from tenacity import retry, stop_after_attempt\n"
        "@retry(stop=stop_after_attempt(3))\n"
        "def call_model():\n"
        "    return \"ok\"\n",
        encoding="utf-8",
    )

    catalog, _ = RuleCatalog.from_path(_rules_dir())
    rule = catalog.get("REL-002")
    evidence_repo = EvidenceCollectionService().collect(_context(tmp_path))
    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), evidence_repo)[0]

    assert result.status == RuleStatus.NEEDS_SEMANTIC_REVIEW
    assert any(item.identifier == "openai" for item in result.matched_evidence)
