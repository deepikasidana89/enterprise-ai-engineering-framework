from pathlib import Path

import pytest

from earf.exceptions import RuleNotFoundError
from earf.rules.catalog import RuleCatalog


def test_catalog_all_returns_copy() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    listed = catalog.all()
    listed.pop()

    assert len(catalog.all()) == 12


def test_catalog_get() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    rule = catalog.get("GOV-001")
    assert rule.id == "GOV-001"


def test_catalog_get_case_insensitive() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    rule = catalog.get("gov-001")
    assert rule.id == "GOV-001"


def test_catalog_get_missing_rule() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    with pytest.raises(RuleNotFoundError):
        catalog.get("GOV-999")


def test_catalog_by_category() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    governance = catalog.by_category("governance")
    assert [rule.id for rule in governance] == ["GOV-001", "GOV-002"]


def test_catalog_enabled() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    enabled_ids = [rule.id for rule in catalog.enabled()]
    assert len(enabled_ids) == 12
    assert "GOV-001" in enabled_ids


def test_real_rules_directory_expectations() -> None:
    rules_dir = Path(__file__).resolve().parents[1] / "rules"
    catalog, _ = RuleCatalog.from_path(rules_dir)

    rules = catalog.all()
    ids = [rule.id for rule in rules]
    expected = {
        "GOV-001",
        "GOV-002",
        "MOD-001",
        "MOD-002",
        "SAF-001",
        "SAF-002",
        "SEC-001",
        "SEC-002",
        "REL-001",
        "REL-002",
        "EVA-001",
        "OBS-001",
    }

    assert len(rules) == 12
    assert set(ids) == expected
    assert len(ids) == len(set(ids))
    assert all(rule.rationale.strip() for rule in rules)
    assert all(rule.recommendation.strip() for rule in rules)
