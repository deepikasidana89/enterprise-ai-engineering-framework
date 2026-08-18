from __future__ import annotations

from pathlib import Path
import re

from .base import EvidenceCollector
from .code_pattern_registry import CODE_PATTERN_REGISTRY, CodePatternDefinition
from ..models import Evidence, EvidenceType, RepositoryContext


class CodePatternCollector(EvidenceCollector):
    """Scan production source files for deterministic engineering code patterns."""

    name = "code_pattern"

    _MAX_FILE_BYTES = 1_000_000
    _IGNORED_DIRS = {
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        "build",
        "target",
        "coverage",
        "__pycache__",
        ".idea",
        ".vscode",
    }
    _TEST_LIKE_DIRS = {
        "tests",
        "test",
        "__tests__",
        "fixtures",
        "mocks",
    }
    _SUPPORTED_EXTENSIONS = {
        ".py",
        ".java",
        ".kt",
        ".js",
        ".ts",
        ".tsx",
        ".go",
        ".cs",
    }

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        root = context.root_path
        evidence_items: list[Evidence] = []

        for file_path in self._iter_candidate_files(root):
            rel_path = str(file_path.relative_to(root))
            content = self._read_text(file_path)
            if content is None:
                continue

            cleaned = self._strip_comments(content, file_path.suffix.lower())
            extension = file_path.suffix.lower()
            for definition in CODE_PATTERN_REGISTRY:
                if extension not in definition.extensions:
                    continue

                match = definition.pattern.search(cleaned)
                if match is None:
                    continue

                line = cleaned.count("\n", 0, match.start()) + 1
                matched_text = cleaned[match.start():match.end()].strip()
                location = f"{rel_path}:{line}"
                evidence_items.append(
                    Evidence(
                        evidence_type=EvidenceType.CODE_PATTERN,
                        source=self.name,
                        description=definition.description,
                        identifier=definition.identifier,
                        path=rel_path,
                        location=location,
                        metadata={
                            "collector": self.name,
                            "pattern_id": definition.identifier,
                            "category": definition.category,
                            "language": extension.lstrip("."),
                            "line": line,
                            "matched_text": matched_text[:120],
                            "source_scope": "production",
                        },
                    )
                )

        return sorted(evidence_items, key=lambda item: (item.identifier, item.path or "", item.location or ""))

    def _iter_candidate_files(self, root: Path) -> list[Path]:
        candidates: list[Path] = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            relative = file_path.relative_to(root)
            if any(part in self._IGNORED_DIRS for part in relative.parts):
                continue
            if any(part in self._TEST_LIKE_DIRS for part in relative.parts):
                continue
            if file_path.suffix.lower() not in self._SUPPORTED_EXTENSIONS:
                continue

            try:
                if file_path.stat().st_size > self._MAX_FILE_BYTES:
                    continue
                raw = file_path.read_bytes()
            except OSError:
                continue

            if b"\x00" in raw:
                continue

            candidates.append(file_path)

        return candidates

    def _read_text(self, file_path: Path) -> str | None:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _strip_comments(self, content: str, extension: str) -> str:
        if extension == ".py":
            return self._strip_python_line_comments(content)

        no_block = self._strip_block_comments(content)
        return self._strip_double_slash_comments(no_block)

    def _strip_python_line_comments(self, content: str) -> str:
        lines: list[str] = []
        for line in content.splitlines(keepends=True):
            hash_index = line.find("#")
            if hash_index == -1:
                lines.append(line)
                continue
            lines.append(line[:hash_index] + ("\n" if line.endswith("\n") else ""))
        return "".join(lines)

    def _strip_double_slash_comments(self, content: str) -> str:
        lines: list[str] = []
        for line in content.splitlines(keepends=True):
            marker = line.find("//")
            if marker == -1:
                lines.append(line)
                continue
            lines.append(line[:marker] + ("\n" if line.endswith("\n") else ""))
        return "".join(lines)

    def _strip_block_comments(self, content: str) -> str:
        pattern = re.compile(r"/\*.*?\*/", re.DOTALL)

        def _replace(match: re.Match[str]) -> str:
            chunk = match.group(0)
            return "".join("\n" if ch == "\n" else " " for ch in chunk)

        return pattern.sub(_replace, content)


# Backward-compatible alias for existing imports.
CodePatternEvidenceCollector = CodePatternCollector
