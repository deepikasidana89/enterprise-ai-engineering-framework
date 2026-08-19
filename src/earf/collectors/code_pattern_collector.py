from __future__ import annotations

import re

from .base import EvidenceCollector
from .code_pattern_registry import CODE_PATTERN_REGISTRY, CodePatternDefinition
from .workspace_index import ensure_workspace_index
from ..models import Evidence, EvidenceType, RepositoryContext


class CodePatternCollector(EvidenceCollector):
    """Scan production source files for deterministic engineering code patterns."""

    name = "code_pattern"

    _SUPPORTED_EXTENSIONS = {
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
    }

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        index = ensure_workspace_index(context)

        evidence_items: list[Evidence] = []

        for indexed in index.files:
            file_path = indexed.path
            rel_path = indexed.relative_path
            if indexed.is_test_like:
                continue

            extension = file_path.suffix.lower()
            if extension not in self._SUPPORTED_EXTENSIONS:
                continue

            content = indexed.text
            if content is None:
                continue

            cleaned = self._strip_comments(content, file_path.suffix.lower())
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
