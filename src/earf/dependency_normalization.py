from __future__ import annotations

import re


_PYTHON_NAME_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)")


def normalize_dependency_identifier(raw: str) -> str:
    """Normalize a dependency identifier without changing package identity."""
    token = raw.strip().strip('"').strip("'").lower()
    if not token:
        return ""

    if token.startswith("@") and "/" in token:
        # Preserve scoped npm package format.
        return token

    if ":" in token:
        # Preserve Java coordinates like group:artifact.
        return token

    if re.fullmatch(r"[a-z0-9_.-]+", token):
        return token.replace("_", "-").replace(".", "-")

    return token


def extract_python_dependency_name(requirement: str) -> str | None:
    """Extract and normalize a Python package name from a requirement specifier."""
    line = requirement.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith(("-r", "--requirement", "-c", "--constraint")):
        return None

    line = line.split("#", 1)[0].strip()
    if not line:
        return None

    if line.startswith("-e "):
        line = line[3:].strip()

    if line.startswith(("git+", "http://", "https://")):
        return None

    line = line.strip().strip('"').strip("'")
    if not line:
        return None

    if ";" in line:
        line = line.split(";", 1)[0].strip()

    if " @ " in line:
        line = line.split(" @ ", 1)[0].strip()

    if "[" in line:
        line = line.split("[", 1)[0].strip()

    match = _PYTHON_NAME_PATTERN.match(line)
    if match is None:
        return None

    return normalize_dependency_identifier(match.group(1))
