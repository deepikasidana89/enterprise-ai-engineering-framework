from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

import typer

from .repository import RepositoryLoader
from . import __version__
from .exceptions import InvalidRepositoryPathError

app = typer.Typer(help="EARF CLI")


@app.command()
def version() -> None:
    """Show EARF version."""
    typer.echo(f"EARF {__version__}")


@app.command()
def scan(path: Path) -> None:
    """Load repository at PATH (Phase 1: scanning not implemented)."""
    try:
        loader = RepositoryLoader()
        context = loader.load(path)
        typer.echo("Repository loaded successfully.")
        typer.echo("")
        typer.echo(f"Project: {context.project_name}")
        typer.echo(f"Path: {context.root_path}")
        typer.echo("")
        typer.echo("Repository scanning is not implemented in Phase 1.")
        raise typer.Exit(code=0)
    except InvalidRepositoryPathError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def rules() -> None:
    """Phase 1 placeholder: rule loading not implemented."""
    typer.echo("EARF rule loading is not implemented in Phase 1.")


def main(argv: Optional[list[str]] | None = None) -> int:
    try:
        app(argv or sys.argv[1:])
    except SystemExit:
        # typer uses SystemExit, re-raise to preserve exit code
        raise
    return 0
