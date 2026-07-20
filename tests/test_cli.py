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
    assert "Repository loaded successfully." in result.stdout
    assert "Project: proj" in result.stdout
    assert f"Path: {d.resolve()}" in result.stdout
    assert "Repository scanning is not implemented in Phase 1." in result.stdout


def test_scan_invalid() -> None:
    result = runner.invoke(app, ["scan", "no-such-path"])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Traceback" not in result.stdout


def test_scan_file_path_invalid(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("hi")
    result = runner.invoke(app, ["scan", str(f)])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Path is not a directory" in result.stdout
    assert "Traceback" not in result.stdout
