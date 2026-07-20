from __future__ import annotations

from pathlib import Path

from .models import RepositoryContext
from .exceptions import InvalidRepositoryPathError


class RepositoryLoader:
    """Load and validate a repository path and create a RepositoryContext.

    Phase 1: validates path, verifies directory, derives project name, returns
    empty files list.
    """

    def load(self, path: Path) -> RepositoryContext:
        if not path.exists():
            raise InvalidRepositoryPathError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise InvalidRepositoryPathError(f"Path is not a directory: {path}")
        resolved = path.resolve()
        project_name = resolved.name
        return RepositoryContext(root_path=resolved, project_name=project_name, files=[])
