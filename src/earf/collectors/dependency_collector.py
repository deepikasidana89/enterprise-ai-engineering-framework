from __future__ import annotations

import ast
import configparser
import json
from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET
import re

from .base import EvidenceCollector
from ..dependency_normalization import (
    extract_python_dependency_name,
    normalize_dependency_identifier,
)
from ..models import Evidence, EvidenceType, RepositoryContext


class DependencyCollector(EvidenceCollector):
    name = "dependency"

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        root = context.root_path
        evidence: list[Evidence] = []

        evidence.extend(self._collect_requirements(root))
        evidence.extend(self._collect_pyproject(root))
        evidence.extend(self._collect_pipfile(root))
        evidence.extend(self._collect_setup_cfg(root))
        evidence.extend(self._collect_setup_py(root))
        evidence.extend(self._collect_package_json(root))
        evidence.extend(self._collect_pom_xml(root))
        evidence.extend(self._collect_gradle(root))

        return sorted(evidence, key=lambda item: (item.identifier, item.path or ""))

    def _collect_requirements(self, root: Path) -> list[Evidence]:
        requirements_file = root / "requirements.txt"
        if not requirements_file.is_file():
            return []

        items: list[Evidence] = []
        seen: set[str] = set()
        for raw_line in requirements_file.read_text(encoding="utf-8").splitlines():
            dep_name = extract_python_dependency_name(raw_line)
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

        dependencies: list[str] = []

        project = content.get("project", {})
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

        tool = content.get("tool", {})
        if isinstance(tool, dict):
            poetry = tool.get("poetry", {})
            if isinstance(poetry, dict):
                poetry_dependencies = poetry.get("dependencies", {})
                if isinstance(poetry_dependencies, dict):
                    for name in poetry_dependencies.keys():
                        if isinstance(name, str) and name.lower() != "python":
                            dependencies.append(name)

                groups = poetry.get("group", {})
                if isinstance(groups, dict):
                    for group_value in groups.values():
                        if not isinstance(group_value, dict):
                            continue
                        group_deps = group_value.get("dependencies", {})
                        if not isinstance(group_deps, dict):
                            continue
                        for name in group_deps.keys():
                            if isinstance(name, str) and name.lower() != "python":
                                dependencies.append(name)

        items: list[Evidence] = []
        seen: set[str] = set()
        rel_path = str(pyproject_file.relative_to(root))
        for dependency in dependencies:
            dep_name = extract_python_dependency_name(dependency)
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

    def _collect_pipfile(self, root: Path) -> list[Evidence]:
        pipfile = root / "Pipfile"
        if not pipfile.is_file():
            return []

        try:
            content = tomllib.loads(pipfile.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            return []

        identifiers: set[str] = set()
        for section_name in ("packages", "dev-packages"):
            section = content.get(section_name, {})
            if not isinstance(section, dict):
                continue
            for package_name in section.keys():
                if not isinstance(package_name, str):
                    continue
                normalized = normalize_dependency_identifier(package_name)
                if normalized:
                    identifiers.add(normalized)

        rel_path = str(pipfile.relative_to(root))
        return [
            Evidence(
                evidence_type=EvidenceType.DEPENDENCY,
                source=self.name,
                description=f"Dependency declared in {rel_path}",
                identifier=identifier,
                path=rel_path,
                location=rel_path,
                metadata={"collector": self.name, "origin": "Pipfile"},
            )
            for identifier in sorted(identifiers)
        ]

    def _collect_setup_cfg(self, root: Path) -> list[Evidence]:
        setup_cfg = root / "setup.cfg"
        if not setup_cfg.is_file():
            return []

        parser = configparser.ConfigParser()
        try:
            parser.read(setup_cfg, encoding="utf-8")
        except (configparser.Error, OSError):
            return []

        requirements: list[str] = []
        if parser.has_section("options") and parser.has_option("options", "install_requires"):
            requirements.extend(
                line.strip()
                for line in parser.get("options", "install_requires").splitlines()
                if line.strip()
            )

        if parser.has_section("options.extras_require"):
            for _, value in parser.items("options.extras_require"):
                requirements.extend(
                    line.strip()
                    for line in value.splitlines()
                    if line.strip()
                )

        identifiers: set[str] = set()
        for requirement in requirements:
            dep_name = extract_python_dependency_name(requirement)
            if dep_name:
                identifiers.add(dep_name)

        rel_path = str(setup_cfg.relative_to(root))
        return [
            Evidence(
                evidence_type=EvidenceType.DEPENDENCY,
                source=self.name,
                description=f"Dependency declared in {rel_path}",
                identifier=identifier,
                path=rel_path,
                location=rel_path,
                metadata={"collector": self.name, "origin": "setup.cfg"},
            )
            for identifier in sorted(identifiers)
        ]

    def _collect_setup_py(self, root: Path) -> list[Evidence]:
        setup_py = root / "setup.py"
        if not setup_py.is_file():
            return []

        try:
            tree = ast.parse(setup_py.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            return []

        requirements: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            is_setup_call = False
            if isinstance(node.func, ast.Name) and node.func.id == "setup":
                is_setup_call = True
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "setup":
                is_setup_call = True
            if not is_setup_call:
                continue

            for keyword in node.keywords:
                if keyword.arg == "install_requires":
                    requirements.extend(self._extract_requirements_from_ast(keyword.value))
                elif keyword.arg == "extras_require":
                    requirements.extend(self._extract_extras_requirements_from_ast(keyword.value))

        identifiers: set[str] = set()
        for requirement in requirements:
            dep_name = extract_python_dependency_name(requirement)
            if dep_name:
                identifiers.add(dep_name)

        rel_path = str(setup_py.relative_to(root))
        return [
            Evidence(
                evidence_type=EvidenceType.DEPENDENCY,
                source=self.name,
                description=f"Dependency declared in {rel_path}",
                identifier=identifier,
                path=rel_path,
                location=rel_path,
                metadata={"collector": self.name, "origin": "setup.py"},
            )
            for identifier in sorted(identifiers)
        ]

    def _extract_requirements_from_ast(self, value: ast.AST) -> list[str]:
        if isinstance(value, (ast.List, ast.Tuple)):
            return [
                item.value
                for item in value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
        return []

    def _extract_extras_requirements_from_ast(self, value: ast.AST) -> list[str]:
        if not isinstance(value, ast.Dict):
            return []

        requirements: list[str] = []
        for list_node in value.values:
            requirements.extend(self._extract_requirements_from_ast(list_node))
        return requirements

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
                    collected.add(normalize_dependency_identifier(name))

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

    def _collect_gradle(self, root: Path) -> list[Evidence]:
        gradle_files = [root / "build.gradle", root / "build.gradle.kts"]
        items: list[Evidence] = []
        seen: set[tuple[str, str]] = set()

        pattern = re.compile(r"['\"]([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+):[^'\"]+['\"]")
        for gradle_file in gradle_files:
            if not gradle_file.is_file():
                continue

            try:
                content = gradle_file.read_text(encoding="utf-8")
            except OSError:
                continue

            rel_path = str(gradle_file.relative_to(root))
            for match in pattern.finditer(content):
                group = match.group(1).strip().lower()
                artifact = match.group(2).strip().lower()
                candidates = {artifact, f"{group}:{artifact}"}
                for identifier in candidates:
                    key = (rel_path, identifier)
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(
                        Evidence(
                            evidence_type=EvidenceType.DEPENDENCY,
                            source=self.name,
                            description=f"Dependency declared in {rel_path}",
                            identifier=identifier,
                            path=rel_path,
                            location=rel_path,
                            metadata={"collector": self.name, "origin": gradle_file.name},
                        )
                    )

        return sorted(items, key=lambda item: (item.identifier, item.path or ""))


# Backward-compatible alias for existing imports.
DependencyEvidenceCollector = DependencyCollector
