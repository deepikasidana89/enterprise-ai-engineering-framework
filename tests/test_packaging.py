from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import tomllib

from earf import __version__
from earf.rules.builtin import built_in_rules_path
from earf.rules.catalog import RuleCatalog


def test_package_version_is_current() -> None:
    assert __version__ == "0.7.0"


def test_built_in_rule_files_available_via_package_resources() -> None:
    package_rules = files("earf").joinpath("rules", "catalog")
    expected_files = {
        "evaluation.yaml",
        "governance.yaml",
        "modeling.yaml",
        "observability.yml",
        "reliability.yaml",
        "safety.yaml",
        "security.yaml",
    }

    discovered = {item.name for item in package_rules.iterdir() if item.is_file()}
    assert expected_files.issubset(discovered)

    catalog, file_count = RuleCatalog.from_path(built_in_rules_path())
    assert file_count >= len(expected_files)
    assert len(catalog.all()) > 0


def test_console_entry_point_configured() -> None:
    project_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    scripts = pyproject["project"]["scripts"]
    assert scripts["earf"] == "earf.cli:main"
