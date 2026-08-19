from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import RepositoryContext


_MAX_FILE_BYTES = 1_000_000
_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    "coverage",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
_IGNORED_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
}
_TEXT_SUFFIXES = {
    ".py",
    ".java",
    ".kt",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".cs",
    ".rb",
    ".rs",
    ".php",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".properties",
    ".conf",
    ".cfg",
    ".ini",
    ".xml",
    ".md",
    ".rst",
    ".txt",
    ".env.example",
}


@dataclass(frozen=True)
class IndexedFile:
    path: Path
    relative_path: str
    suffix: str
    size_bytes: int
    is_text: bool
    text: str | None
    is_workflow: bool
    is_documentation: bool
    is_test_like: bool


@dataclass(frozen=True)
class WorkspaceEvidenceIndex:
    files: tuple[IndexedFile, ...]

    def by_suffix(self, suffixes: set[str]) -> list[IndexedFile]:
        lowered = {item.lower() for item in suffixes}
        return [item for item in self.files if item.suffix.lower() in lowered]

    def by_name(self, names: set[str]) -> list[IndexedFile]:
        lowered = {name.lower() for name in names}
        return [item for item in self.files if Path(item.relative_path).name.lower() in lowered]


class WorkspaceScanner:
    def build_index(self, context: RepositoryContext) -> WorkspaceEvidenceIndex:
        root = context.root_path
        files: list[IndexedFile] = []

        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            relative = file_path.relative_to(root)
            if any(part in _IGNORED_DIRS for part in relative.parts):
                continue

            filename = relative.name
            if filename in _IGNORED_FILENAMES:
                continue
            if filename.endswith(".min.js"):
                continue

            lower_name = filename.lower()
            if lower_name.startswith(".env") and lower_name != ".env.example":
                # Do not read potential secrets from live env files.
                continue

            try:
                size_bytes = file_path.stat().st_size
            except OSError:
                continue

            if size_bytes > _MAX_FILE_BYTES:
                continue

            suffix = "".join(relative.suffixes[-2:]).lower() if lower_name.endswith(".env.example") else file_path.suffix.lower()
            is_text_candidate = suffix in _TEXT_SUFFIXES or lower_name in {
                "dockerfile",
                "docker-compose.yml",
                "docker-compose.yaml",
                "makefile",
                "pipfile",
            }

            text: str | None = None
            is_text = False
            if is_text_candidate:
                try:
                    raw = file_path.read_bytes()
                except OSError:
                    continue

                if b"\x00" in raw:
                    continue

                is_text = True
                text = raw.decode("utf-8", errors="ignore")

            rel_text = relative.as_posix()
            lowered_parts = {part.lower() for part in relative.parts}
            is_workflow = rel_text.startswith(".github/workflows/") and rel_text.endswith((".yml", ".yaml"))
            is_documentation = (
                rel_text.endswith((".md", ".rst"))
                or "docs" in lowered_parts
                or "articles" in lowered_parts
                or "notes" in lowered_parts
            )
            is_test_like = bool(
                lowered_parts.intersection({"test", "tests", "__tests__", "fixtures", "mocks", "spec", "specs"})
            ) or lower_name.startswith("test_") or lower_name.endswith(("_test.py", ".spec.ts", ".spec.js"))

            files.append(
                IndexedFile(
                    path=file_path,
                    relative_path=rel_text,
                    suffix=suffix,
                    size_bytes=size_bytes,
                    is_text=is_text,
                    text=text,
                    is_workflow=is_workflow,
                    is_documentation=is_documentation,
                    is_test_like=is_test_like,
                )
            )

        files.sort(key=lambda item: item.relative_path)
        return WorkspaceEvidenceIndex(files=tuple(files))


def get_workspace_index(context: RepositoryContext) -> WorkspaceEvidenceIndex | None:
    index = context.metadata.get("workspace_index")
    if isinstance(index, WorkspaceEvidenceIndex):
        return index
    return None


def ensure_workspace_index(context: RepositoryContext) -> WorkspaceEvidenceIndex:
    existing = get_workspace_index(context)
    if existing is not None:
        return existing

    index = WorkspaceScanner().build_index(context)
    context.metadata["workspace_index"] = index
    return index
