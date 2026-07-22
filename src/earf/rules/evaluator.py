from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Mapping

from ..evidence import EvidenceRepository
from ..exceptions import (
    InvalidEvidenceRequirementError,
    UnsupportedApplicabilityError,
)
from ..models import Evidence, EvidenceType, RuleDefinition
from .results import RuleResult, RuleStatus


@dataclass(frozen=True)
class RequirementMatch:
    matched: bool
    matched_evidence: list[Evidence]
    missing_requirements: list[str]


class RuleEvaluator:
    def evaluate(
        self,
        rule: RuleDefinition,
        evidence_repository: EvidenceRepository,
    ) -> RuleResult:
        if not rule.enabled:
            return RuleResult(
                rule_id=rule.id,
                status=RuleStatus.DISABLED,
                message="Rule is disabled.",
            )

        try:
            applicable = self._evaluate_applicability(rule)
            if not applicable:
                return RuleResult(
                    rule_id=rule.id,
                    status=RuleStatus.NOT_APPLICABLE,
                    message="Rule is not applicable.",
                )

            match = self._evaluate_requirement(rule.evidence_requirements, evidence_repository)
            matched_evidence = self._deduplicate(match.matched_evidence)
            if match.matched:
                return RuleResult(
                    rule_id=rule.id,
                    status=RuleStatus.PASS,
                    message="Matched required evidence.",
                    matched_evidence=matched_evidence,
                )

            return RuleResult(
                rule_id=rule.id,
                status=RuleStatus.FAIL,
                message="Missing required evidence.",
                matched_evidence=matched_evidence,
                missing_requirements=match.missing_requirements,
            )
        except (InvalidEvidenceRequirementError, UnsupportedApplicabilityError) as exc:
            return RuleResult(
                rule_id=rule.id,
                status=RuleStatus.ERROR,
                message="Rule evaluation failed due to invalid rule configuration.",
                error=str(exc),
            )
        except Exception as exc:
            return RuleResult(
                rule_id=rule.id,
                status=RuleStatus.ERROR,
                message="Unexpected rule evaluation error.",
                error=str(exc),
            )

    def _evaluate_applicability(self, rule: RuleDefinition) -> bool:
        applicability = rule.applicability
        if not applicability:
            return True

        if set(applicability.keys()) != {"always"}:
            raise UnsupportedApplicabilityError(
                f"Rule {rule.id}: unsupported applicability structure {applicability}"
            )

        always = applicability.get("always")
        if not isinstance(always, bool):
            raise UnsupportedApplicabilityError(
                f"Rule {rule.id}: applicability.always must be a boolean"
            )
        return always

    def _evaluate_requirement(
        self,
        requirement: Mapping[str, object],
        evidence_repository: EvidenceRepository,
    ) -> RequirementMatch:
        if not requirement:
            return RequirementMatch(matched=True, matched_evidence=[], missing_requirements=[])

        has_any = "any" in requirement
        has_all = "all" in requirement

        if has_any and has_all:
            raise InvalidEvidenceRequirementError(
                "Requirement cannot contain both 'any' and 'all'"
            )

        if has_any or has_all:
            operator = "any" if has_any else "all"
            children = requirement.get(operator)
            if not isinstance(children, list):
                raise InvalidEvidenceRequirementError(
                    f"Operator '{operator}' must contain a list"
                )
            if not children:
                raise InvalidEvidenceRequirementError(
                    f"Operator '{operator}' requires at least one child requirement"
                )

            child_matches: list[RequirementMatch] = []
            for child in children:
                if not isinstance(child, dict):
                    raise InvalidEvidenceRequirementError(
                        f"Operator '{operator}' child must be a mapping"
                    )
                child_matches.append(self._evaluate_requirement(child, evidence_repository))

            if operator == "any":
                for child_match in child_matches:
                    if child_match.matched:
                        return RequirementMatch(
                            matched=True,
                            matched_evidence=child_match.matched_evidence,
                            missing_requirements=[],
                        )
                missing = [msg for c in child_matches for msg in c.missing_requirements]
                return RequirementMatch(
                    matched=False,
                    matched_evidence=[],
                    missing_requirements=missing,
                )

            # all
            matched_evidence: list[Evidence] = []
            missing_requirements: list[str] = []
            for child_match in child_matches:
                matched_evidence.extend(child_match.matched_evidence)
                missing_requirements.extend(child_match.missing_requirements)
            return RequirementMatch(
                matched=not missing_requirements,
                matched_evidence=matched_evidence,
                missing_requirements=missing_requirements,
            )

        return self._evaluate_direct_requirement(requirement, evidence_repository)

    def _evaluate_direct_requirement(
        self,
        requirement: Mapping[str, object],
        evidence_repository: EvidenceRepository,
    ) -> RequirementMatch:
        evidence_type_raw = requirement.get("evidence_type")
        if not isinstance(evidence_type_raw, str) or not evidence_type_raw.strip():
            raise InvalidEvidenceRequirementError(
                "Direct requirement must define a non-empty 'evidence_type'"
            )

        evidence_type = self._parse_evidence_type(evidence_type_raw)
        source = self._optional_string(requirement.get("source"), field_name="source")
        path_filter = self._normalize_path_filter(requirement.get("path"))
        identifiers = self._normalize_identifiers(requirement.get("identifiers"))

        candidates = evidence_repository.find(
            evidence_type=evidence_type,
            source=source,
        )

        if path_filter is not None:
            candidates = [
                item
                for item in candidates
                if item.path is not None
                and self._normalize_path_value(item.path) in path_filter
            ]

        if identifiers is None:
            if candidates:
                return RequirementMatch(
                    matched=True,
                    matched_evidence=candidates,
                    missing_requirements=[],
                )
            return RequirementMatch(
                matched=False,
                matched_evidence=[],
                missing_requirements=[self._describe_missing(evidence_type, identifiers, source, path_filter)],
            )

        matched = [
            item
            for item in candidates
            if self._identifier_matches(item, identifiers)
        ]
        if matched:
            return RequirementMatch(
                matched=True,
                matched_evidence=matched,
                missing_requirements=[],
            )

        return RequirementMatch(
            matched=False,
            matched_evidence=[],
            missing_requirements=[self._describe_missing(evidence_type, identifiers, source, path_filter)],
        )

    def _parse_evidence_type(self, value: str) -> EvidenceType:
        token = value.strip().upper()
        try:
            return EvidenceType[token]
        except KeyError as exc:
            raise InvalidEvidenceRequirementError(
                f"Unsupported evidence_type {value!r}"
            ) from exc

    def _optional_string(self, value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidEvidenceRequirementError(f"{field_name} must be a string")
        normalized = value.strip().lower()
        return normalized if normalized else None

    def _normalize_path_filter(self, value: object) -> set[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = self._normalize_path_value(value)
            return {normalized}
        if isinstance(value, list) and all(isinstance(v, str) for v in value):
            return {self._normalize_path_value(v) for v in value}
        raise InvalidEvidenceRequirementError("path must be a string or list of strings")

    def _normalize_identifiers(self, value: object) -> set[str] | None:
        if value is None:
            return None
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise InvalidEvidenceRequirementError(
                "identifiers must be a list of strings"
            )
        if not value:
            raise InvalidEvidenceRequirementError(
                "identifiers must contain at least one identifier"
            )
        normalized = {v.strip() for v in value if v.strip()}
        if not normalized:
            raise InvalidEvidenceRequirementError(
                "identifiers must contain at least one non-empty identifier"
            )
        return normalized

    def _identifier_matches(self, evidence: Evidence, requested: set[str]) -> bool:
        evidence_identifier = evidence.identifier.strip()
        if evidence.evidence_type == EvidenceType.DEPENDENCY:
            return evidence_identifier.lower() in {item.lower() for item in requested}
        return evidence_identifier in requested

    def _describe_missing(
        self,
        evidence_type: EvidenceType,
        identifiers: set[str] | None,
        source: str | None,
        path_filter: set[str] | None,
    ) -> str:
        details: list[str] = [f"evidence_type={evidence_type.value.lower()}"]
        if identifiers:
            details.append(f"identifiers={sorted(identifiers)}")
        if source:
            details.append(f"source={source}")
        if path_filter:
            details.append(f"path={sorted(path_filter)}")
        return "Missing requirement: " + ", ".join(details)

    def _normalize_path_value(self, value: str) -> str:
        return PurePath(value.strip().replace("\\", "/")).as_posix()

    def _deduplicate(self, evidence: list[Evidence]) -> list[Evidence]:
        seen: set[tuple[str, str, str, str | None, str | None]] = set()
        result: list[Evidence] = []
        for item in evidence:
            key = (
                item.evidence_type.value,
                item.identifier,
                item.source,
                item.path,
                item.location,
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result
