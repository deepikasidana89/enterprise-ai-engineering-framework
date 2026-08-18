from pathlib import Path

import pytest

from earf.exceptions import DuplicateRuleError, RuleLoadError, RuleValidationError
from earf.models import ControlTier
from earf.rules.loader import YamlRuleLoader


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _valid_rule(rule_id: str = "GOV-001", severity: str = "high") -> str:
    return f"""
rules:
  - id: {rule_id}
    title: Title {rule_id}
    description: Description {rule_id}
    category: governance
    severity: {severity}
    version: "1.0"
    enabled: true
    applicability: {{always: true}}
    rationale: why
    recommendation: do
    tags: [governance]
    references: []
    evidence_requirements: {{any: []}}
    metadata: {{}}
""".strip()


def test_load_single_file(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", _valid_rule())
    rules = YamlRuleLoader().load(p)
    assert len(rules) == 1
    assert rules[0].id == "GOV-001"


def test_load_directory(tmp_path: Path) -> None:
    _write(tmp_path / "one.yaml", _valid_rule("GOV-001"))
    _write(tmp_path / "two.yaml", _valid_rule("GOV-002"))
    rules = YamlRuleLoader().load(tmp_path)
    assert {rule.id for rule in rules} == {"GOV-001", "GOV-002"}


def test_load_nested_directory(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    _write(nested / "rules.yaml", _valid_rule("GOV-001"))
    rules = YamlRuleLoader().load(tmp_path)
    assert [rule.id for rule in rules] == ["GOV-001"]


def test_load_yaml_and_yml_extensions(tmp_path: Path) -> None:
    _write(tmp_path / "a.yaml", _valid_rule("GOV-001"))
    _write(tmp_path / "b.yml", _valid_rule("GOV-002"))
    rules = YamlRuleLoader().load(tmp_path)
    assert {rule.id for rule in rules} == {"GOV-001", "GOV-002"}


def test_sorted_file_order(tmp_path: Path) -> None:
    _write(tmp_path / "b.yaml", _valid_rule("GOV-002"))
    _write(tmp_path / "a.yaml", _valid_rule("GOV-001"))
    rules = YamlRuleLoader().load(tmp_path)
    assert [rule.id for rule in rules] == ["GOV-001", "GOV-002"]


def test_ignore_non_yaml_files(tmp_path: Path) -> None:
    _write(tmp_path / "rules.yaml", _valid_rule("GOV-001"))
    _write(tmp_path / "notes.txt", "ignore")
    rules = YamlRuleLoader().load(tmp_path)
    assert [rule.id for rule in rules] == ["GOV-001"]


def test_malformed_yaml(tmp_path: Path) -> None:
    p = _write(tmp_path / "broken.yaml", "rules: [")
    with pytest.raises(RuleLoadError):
        YamlRuleLoader().load(p)


def test_missing_path() -> None:
    with pytest.raises(RuleLoadError):
        YamlRuleLoader().load(Path("no-such-rules-path"))


def test_missing_rules_key(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", "not_rules: []")
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_invalid_rules_type(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", "rules: {}")
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_invalid_entry_type(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", "rules:\n  - just-a-string")
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_missing_required_fields(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "rules.yaml",
        """
rules:
  - id: GOV-001
    title: Missing fields
""".strip(),
    )
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_invalid_severity(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", _valid_rule("GOV-001", severity="severe"))
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_invalid_rule_id(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", _valid_rule("gov-001"))
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_duplicate_ids_in_one_file(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "rules.yaml",
        """
rules:
  - id: GOV-001
    title: One
    description: desc
    category: governance
    severity: high
    version: "1.0"
    enabled: true
    applicability: {}
    rationale: why
    recommendation: do
    tags: []
    references: []
    evidence_requirements: {}
    metadata: {}
  - id: GOV-001
    title: Two
    description: desc
    category: governance
    severity: high
    version: "1.0"
    enabled: true
    applicability: {}
    rationale: why
    recommendation: do
    tags: []
    references: []
    evidence_requirements: {}
    metadata: {}
""".strip(),
    )
    with pytest.raises(DuplicateRuleError):
        YamlRuleLoader().load(p)


def test_duplicate_ids_across_files(tmp_path: Path) -> None:
    _write(tmp_path / "one.yaml", _valid_rule("GOV-001"))
    _write(tmp_path / "two.yaml", _valid_rule("GOV-001"))
    with pytest.raises(DuplicateRuleError):
        YamlRuleLoader().load(tmp_path)


def test_empty_yaml_rejected(tmp_path: Path) -> None:
    p = _write(tmp_path / "empty.yaml", "")
    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)


def test_tier_defaults_to_core_when_missing(tmp_path: Path) -> None:
    p = _write(tmp_path / "rules.yaml", _valid_rule())

    rules = YamlRuleLoader().load(p)

    assert rules[0].tier == ControlTier.CORE


def test_tier_accepts_advanced_value(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "rules.yaml",
        _valid_rule().replace("severity: high", "severity: high\n    tier: advanced"),
    )

    rules = YamlRuleLoader().load(p)

    assert rules[0].tier == ControlTier.ADVANCED


def test_invalid_tier_is_rejected(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "rules.yaml",
        _valid_rule().replace("severity: high", "severity: high\n    tier: experimental"),
    )

    with pytest.raises(RuleValidationError):
        YamlRuleLoader().load(p)
