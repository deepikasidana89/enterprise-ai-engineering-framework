from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def built_in_rules_path() -> Path:
    """Return the packaged rule catalog directory path."""
    return Path(str(files("earf").joinpath("rules", "catalog")))
