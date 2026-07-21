from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import yaml

from ..exceptions import DuplicateRuleError, RuleLoadError, RuleValidationError
from ..models import RuleDefinition, Severity


def _ensure_dict(value: Any, field_name: str, rule_id: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuleValidationError(
            f"Rule {rule_id}: {field_name} must be a mapping, got {type(value).__name__}"
        )
    return value


def _ensure_list_of_strings(value: Any, field_name: str, rule_id: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuleValidationError(
            f"Rule {rule_id}: {field_name} must be a list of strings"
        )
    return value


def _ensure_non_empty_string(value: Any, field_name: str, rule_id: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuleValidationError(
            f"Rule {rule_id}: {field_name} must be a non-empty string"
        )
    return value.strip()


def _ensure_bool(value: Any, field_name: str, rule_id: str) -> bool:
    if not isinstance(value, bool):
        raise RuleValidationError(f"Rule {rule_id}: {field_name} must be a boolean")
    return value


def _ensure_string(value: Any, field_name: str, rule_id: str) -> str:
    if not isinstance(value, str):
        raise RuleValidationError(f"Rule {rule_id}: {field_name} must be a string")
    return value


class RuleLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> list[RuleDefinition]:
        raise NotImplementedError


class YamlRuleLoader(RuleLoader):
    def __init__(self) -> None:
        self.last_loaded_files: tuple[Path, ...] = ()

    def load(self, path: Path) -> list[RuleDefinition]:
        yaml_files = self._discover_yaml_files(path)
        rules: list[RuleDefinition] = []
        seen_rule_ids: dict[str, Path] = {}

        for yaml_file in yaml_files:
            file_rules = self._load_yaml_file(yaml_file)
            for rule in file_rules:
                existing = seen_rule_ids.get(rule.id)
                if existing is not None:
                    raise DuplicateRuleError(
                        f"Duplicate rule id {rule.id!r} found in {yaml_file} and {existing}"
                    )
                seen_rule_ids[rule.id] = yaml_file
                rules.append(rule)

        self.last_loaded_files = tuple(yaml_files)
        return rules

    def _discover_yaml_files(self, path: Path) -> list[Path]:
        if not path.exists():
            raise RuleLoadError(f"Rules path does not exist: {path}")

        if path.is_file():
            if path.suffix.lower() not in {".yaml", ".yml"}:
                raise RuleLoadError(f"Rules file must end with .yaml or .yml: {path}")
            return [path.resolve()]

        if not path.is_dir():
            raise RuleLoadError(f"Rules path is neither file nor directory: {path}")

        files = sorted(
            [
                file.resolve()
                for file in path.rglob("*")
                if file.is_file() and file.suffix.lower() in {".yaml", ".yml"}
            ],
            key=lambda p: str(p),
        )
        if not files:
            raise RuleLoadError(f"No YAML rule files found under: {path}")
        return files

    def _load_yaml_file(self, file_path: Path) -> list[RuleDefinition]:
        try:
            loaded = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise RuleLoadError(f"Unable to read rules file {file_path}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise RuleLoadError(f"Malformed YAML in {file_path}: {exc}") from exc

        if loaded is None:
            raise RuleValidationError(f"Rules file is empty: {file_path}")
        if not isinstance(loaded, dict):
            raise RuleValidationError(
                f"Top-level YAML document must be a mapping in {file_path}"
            )
        if "rules" not in loaded:
            raise RuleValidationError(f"Missing top-level 'rules' key in {file_path}")

        rules_data = loaded["rules"]
        if not isinstance(rules_data, list):
            raise RuleValidationError(
                f"The 'rules' key must contain a list in {file_path}"
            )

        rules: list[RuleDefinition] = []
        seen_local: set[str] = set()
        for idx, entry in enumerate(rules_data, start=1):
            if not isinstance(entry, dict):
                raise RuleValidationError(
                    f"Entry {idx} in {file_path} must be a mapping"
                )

            rule = self._build_rule(entry, file_path, idx)
            if rule.id in seen_local:
                raise DuplicateRuleError(
                    f"Duplicate rule id {rule.id!r} found multiple times in {file_path}"
                )
            seen_local.add(rule.id)
            rules.append(rule)

        return rules

    def _build_rule(
        self,
        data: dict[str, Any],
        file_path: Path,
        index: int,
    ) -> RuleDefinition:
        required = ["id", "title", "description", "category", "severity"]
        missing = [field for field in required if field not in data]
        if missing:
            raise RuleValidationError(
                f"Rule entry {index} in {file_path} is missing required field(s): {', '.join(missing)}"
            )

        rule_id_value = data["id"]
        if not isinstance(rule_id_value, str):
            raise RuleValidationError(
                f"Rule entry {index} in {file_path}: id must be a string"
            )
        rule_id = rule_id_value.strip()

        severity_value = data["severity"]
        if not isinstance(severity_value, str):
            raise RuleValidationError(
                f"Rule {rule_id or f'entry {index}'} in {file_path}: severity must be a string"
            )

        try:
            severity = Severity[severity_value.strip().upper()]
        except KeyError as exc:
            supported = ", ".join(level.name.lower() for level in Severity)
            raise RuleValidationError(
                f"Rule {rule_id or f'entry {index}'} in {file_path}: invalid severity {severity_value!r}. Supported values: {supported}"
            ) from exc

        applicability = data.get("applicability", {})
        evidence_requirements = data.get("evidence_requirements", {})
        metadata = data.get("metadata", {})

        try:
            return RuleDefinition(
                id=rule_id,
                title=_ensure_non_empty_string(data.get("title"), "title", rule_id),
                description=_ensure_non_empty_string(
                    data.get("description"),
                    "description",
                    rule_id,
                ),
                category=_ensure_non_empty_string(
                    data.get("category"),
                    "category",
                    rule_id,
                ),
                severity=severity,
                version=_ensure_non_empty_string(
                    data.get("version", "1.0"),
                    "version",
                    rule_id,
                ),
                enabled=_ensure_bool(data.get("enabled", True), "enabled", rule_id),
                applicability=_ensure_dict(applicability, "applicability", rule_id),
                rationale=_ensure_string(data.get("rationale", ""), "rationale", rule_id),
                recommendation=_ensure_string(
                    data.get("recommendation", ""),
                    "recommendation",
                    rule_id,
                ),
                tags=_ensure_list_of_strings(data.get("tags", []), "tags", rule_id),
                references=_ensure_list_of_strings(
                    data.get("references", []), "references", rule_id
                ),
                evidence_requirements=_ensure_dict(
                    evidence_requirements,
                    "evidence_requirements",
                    rule_id,
                ),
                metadata=_ensure_dict(metadata, "metadata", rule_id),
            )
        except ValueError as exc:
            raise RuleValidationError(
                f"Rule {rule_id or f'entry {index}'} in {file_path}: {exc}"
            ) from exc
