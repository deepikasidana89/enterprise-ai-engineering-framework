from __future__ import annotations

from pathlib import Path

from ..exceptions import RuleNotFoundError
from ..models import RuleDefinition
from .loader import RuleLoader, YamlRuleLoader


class RuleCatalog:
    def __init__(self, rules: list[RuleDefinition]) -> None:
        self._rules = sorted(rules, key=lambda rule: rule.id)
        self._index = {rule.id.upper(): rule for rule in self._rules}

    @classmethod
    def from_path(
        cls,
        path: Path,
        loader: RuleLoader | None = None,
    ) -> tuple["RuleCatalog", int]:
        selected_loader = loader or YamlRuleLoader()
        rules = selected_loader.load(path)
        file_count = len(getattr(selected_loader, "last_loaded_files", ()))
        return cls(rules), file_count

    def all(self) -> list[RuleDefinition]:
        return list(self._rules)

    def get(self, rule_id: str) -> RuleDefinition:
        key = rule_id.upper()
        rule = self._index.get(key)
        if rule is None:
            raise RuleNotFoundError(f"Rule not found: {rule_id}")
        return rule

    def by_category(self, category: str) -> list[RuleDefinition]:
        category_key = category.lower()
        return [rule for rule in self._rules if rule.category.lower() == category_key]

    def enabled(self) -> list[RuleDefinition]:
        return [rule for rule in self._rules if rule.enabled]
