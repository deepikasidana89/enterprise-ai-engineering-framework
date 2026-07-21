from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

import typer

from .repository import RepositoryLoader
from . import __version__
from .exceptions import (
    InvalidRepositoryPathError,
    RuleDefinitionError,
)
from .rules.catalog import RuleCatalog

app = typer.Typer(help="EARF CLI")
rules_app = typer.Typer(help="Rule catalog commands")
app.add_typer(rules_app, name="rules")


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


def _load_rule_catalog(path: Path) -> tuple[RuleCatalog, int]:
    catalog, file_count = RuleCatalog.from_path(path)
    return catalog, file_count


@rules_app.command("list")
def rules_list(
    path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")
) -> None:
    """List all loaded rules."""
    try:
        catalog, _ = _load_rule_catalog(path)
        rules = catalog.all()
        typer.echo("ID  Category  Severity  Title  Enabled")
        for rule in rules:
            typer.echo(
                f"{rule.id}  {rule.category}  {rule.severity.name.lower()}  {rule.title}  {rule.enabled}"
            )
        typer.echo("")
        typer.echo(f"{len(rules)} rules loaded.")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@rules_app.command("validate")
def rules_validate(
    path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")
) -> None:
    """Validate rule catalog."""
    try:
        catalog, file_count = _load_rule_catalog(path)
        typer.echo("Rule catalog is valid.")
        typer.echo(f"{len(catalog.all())} rules loaded from {file_count} files.")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@rules_app.command("show")
def rules_show(
    rule_id: str,
    path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory"),
) -> None:
    """Show one rule by ID."""
    try:
        catalog, _ = _load_rule_catalog(path)
        rule = catalog.get(rule_id)
        typer.echo(f"id: {rule.id}")
        typer.echo(f"title: {rule.title}")
        typer.echo(f"description: {rule.description}")
        typer.echo(f"category: {rule.category}")
        typer.echo(f"severity: {rule.severity.name.lower()}")
        typer.echo(f"version: {rule.version}")
        typer.echo(f"enabled: {rule.enabled}")
        typer.echo(f"applicability: {rule.applicability}")
        typer.echo(f"rationale: {rule.rationale}")
        typer.echo(f"recommendation: {rule.recommendation}")
        typer.echo(f"tags: {rule.tags}")
        typer.echo(f"references: {rule.references}")
        typer.echo(f"evidence_requirements: {rule.evidence_requirements}")
        typer.echo(f"metadata: {rule.metadata}")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


def main(argv: Optional[list[str]] | None = None) -> int:
    try:
        app(argv or sys.argv[1:])
    except SystemExit:
        # typer uses SystemExit, re-raise to preserve exit code
        raise
    return 0
