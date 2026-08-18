from __future__ import annotations

import re
import json
from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET

from .base import EvidenceCollector
from ..models import Evidence, EvidenceType, RepositoryContext


def _extract_requirement_name(requirement: str) -> str | None:
    line = requirement.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith(("-r", "--requirement", "-c", "--constraint")):
        return None
    if line.startswith(("git+", "http://", "https://")):
        return None

    line = line.split("#", 1)[0].strip()
    if not line:
        return None

    if line.startswith("-e "):
        line = line[3:].strip()

    match = re.match(r"^([A-Za-z0-9_.-]+)", line)
    if match is None:
        return None
    return match.group(1).lower()


class DependencyCollector(EvidenceCollector):
    name = "dependency"

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        root = context.root_path
        evidence: list[Evidence] = []

        evidence.extend(self._collect_requirements(root))
        evidence.extend(self._collect_pyproject(root))
        evidence.extend(self._collect_package_json(root))
        evidence.extend(self._collect_pom_xml(root))

        return sorted(evidence, key=lambda item: (item.identifier, item.path or ""))

    def _collect_requirements(self, root: Path) -> list[Evidence]:
        requirements_file = root / "requirements.txt"
        if not requirements_file.is_file():
            return []

        items: list[Evidence] = []
        seen: set[str] = set()
        for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
            dep_name = _extract_requirement_name(raw_line)
            if dep_name is None or dep_name in seen:
                continue
            seen.add(dep_name)
            rel_path = str(requirements_file.relative_to(root))
            items.append(
                Evidence(
                    evidence_type=EvidenceType.DEPENDENCY,
                    source=self.name,
                    description=f"Dependency declared in {rel_path}",
                    identifier=dep_name,
                    path=rel_path,
                    location=rel_path,
                    metadata={"collector": self.name, "origin": "requirements.txt"},
                )
            )
        return items

    def _collect_pyproject(self, root: Path) -> list[Evidence]:
        pyproject_file = root / "pyproject.toml"
        if not pyproject_file.is_file():
            return []

        try:
            content = tomllib.loads(pyproject_file.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            return []

        project = content.get("project", {})
        dependencies: list[str] = []

        direct = project.get("dependencies", [])
        if isinstance(direct, list):
            dependencies.extend(
                [item for item in direct if isinstance(item, str)]
            )

        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group_dependencies in optional.values():
                if isinstance(group_dependencies, list):
                    dependencies.extend(
                        [item for item in group_dependencies if isinstance(item, str)]
                    )

        items: list[Evidence] = []
        seen: set[str] = set()
        rel_path = str(pyproject_file.relative_to(root))
        for dependency in dependencies:
            dep_name = _extract_requirement_name(dependency)
            if dep_name is None or dep_name in seen:
                continue
            seen.add(dep_name)
            items.append(
                Evidence(
                    evidence_type=EvidenceType.DEPENDENCY,
                    source=self.name,
                    description=f"Dependency declared in {rel_path}",
                    identifier=dep_name,
                    path=rel_path,
                    location=rel_path,
                    metadata={"collector": self.name, "origin": "pyproject.toml"},
                )
            )
        return items

    def _collect_package_json(self, root: Path) -> list[Evidence]:
        package_file = root / "package.json"
        if not package_file.is_file():
            return []

        try:
            content = json.loads(package_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        dependency_sections = (
            "dependencies",
            "optionalDependencies",
            "peerDependencies",
        )
        collected: set[str] = set()
        for section in dependency_sections:
            values = content.get(section)
            if not isinstance(values, dict):
                continue
            for name in values.keys():
                if isinstance(name, str) and name.strip():
                    collected.add(name.strip().lower())

        rel_path = str(package_file.relative_to(root))
        return [
            Evidence(
                evidence_type=EvidenceType.DEPENDENCY,
                source=self.name,
                description=f"Dependency declared in {rel_path}",
                identifier=identifier,
                path=rel_path,
                location=rel_path,
                metadata={"collector": self.name, "origin": "package.json"},
            )
            for identifier in sorted(collected)
        ]

    def _collect_pom_xml(self, root: Path) -> list[Evidence]:
        pom_file = root / "pom.xml"
        if not pom_file.is_file():
            return []

        try:
            xml_root = ET.fromstring(pom_file.read_text(encoding="utf-8"))
        except (ET.ParseError, OSError):
            return []

        rel_path = str(pom_file.relative_to(root))
        dependencies: set[str] = set()

        for dep in xml_root.findall(".//{*}dependency"):
            group_id = dep.findtext("{*}groupId")
            artifact_id = dep.findtext("{*}artifactId")

            if artifact_id and artifact_id.strip():
                artifact_token = artifact_id.strip().lower()
                dependencies.add(artifact_token)
                if group_id and group_id.strip():
                    group_token = group_id.strip().lower()
                    dependencies.add(f"{group_token}:{artifact_token}")

        return [
            Evidence(
                evidence_type=EvidenceType.DEPENDENCY,
                source=self.name,
                description=f"Dependency declared in {rel_path}",
                identifier=identifier,
                path=rel_path,
                location=rel_path,
                metadata={"collector": self.name, "origin": "pom.xml"},
            )
            for identifier in sorted(dependencies)
        ]


# Backward-compatible alias for existing imports.
DependencyEvidenceCollector = DependencyCollector
