from typer.testing import CliRunner

from earf import __version__
from earf.cli import app
from pathlib import Path


runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"EARF {__version__}" in result.stdout


def test_rules_command() -> None:
    result = runner.invoke(app, ["rules"])
    assert result.exit_code == 0
    assert "EARF rule loading is not implemented in Phase 1." in result.stdout


def test_scan_valid(tmp_path: Path) -> None:
    d = tmp_path / "proj"
    d.mkdir()
    result = runner.invoke(app, ["scan", str(d)])
    assert result.exit_code == 0
    assert "Loaded repository: proj" in result.stdout


def test_scan_invalid() -> None:
    result = runner.invoke(app, ["scan", "no-such-path"])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
