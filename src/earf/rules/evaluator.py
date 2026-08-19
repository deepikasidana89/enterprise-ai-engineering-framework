from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from typing import Mapping

from ..evidence import EvidenceRepository
from ..exceptions import (
    InvalidEvidenceRequirementError,
)
from ..models import Evidence, EvidenceType, RuleDefinition
from .capabilities import RepositoryCapabilityDetector
from .results import RuleResult, RuleStatus


SEC_001_RULE_ID = "SEC-001"
SEC_001_POTENTIAL_IDENTIFIERS = {
    "sec.externalized_secret.custom_abstraction",
}
SEC_001_SUPPORTING_IDENTIFIERS = {
    "sec.externalized_secret.sensitive_env_access",
}
SEC_001_WEAK_FILE_IDENTIFIERS = {".env.example", "SECURITY.md"}
DEFAULT_MISSING_EVIDENCE_MESSAGE = "Required evidence for this control was not detected."


@dataclass(frozen=True)
class RequirementMatch:
    matched: bool
    matched_evidence: list[Evidence]
    missing_requirements: list[str]
    uncertain: bool = False
    uncertain_reasons: list[str] | None = None


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
            applicability_match = self._evaluate_applicability(
                rule,
                evidence_repository,
            )
            if applicability_match.uncertain:
                uncertain_reasons = applicability_match.uncertain_reasons or [
                    "Deterministic applicability could not be established."
                ]
                return RuleResult(
                    rule_id=rule.id,
                    status=RuleStatus.NEEDS_SEMANTIC_REVIEW,
                    message="Deterministic applicability is inconclusive.",
                    matched_evidence=applicability_match.matched_evidence,
                    metadata={
                        "applicability_reason": uncertain_reasons[0],
                        "applicability_uncertain_reasons": uncertain_reasons,
                        "applicability_evidence": [
                            {
                                "evidence_type": item.evidence_type.value,
                                "identifier": item.identifier,
                                "source": item.source,
                                "strength": str(item.metadata.get("strength", "")),
                                "path": item.path,
                                "location": item.location,
                            }
                            for item in self._deduplicate(applicability_match.matched_evidence)
                        ],
                    },
                )

            if not applicability_match.matched:
                applicability_reason = (
                    applicability_match.missing_requirements[0]
                    if applicability_match.missing_requirements
                    else "Rule applicability requirements were not met."
                )
                return RuleResult(
                    rule_id=rule.id,
                    status=RuleStatus.NOT_APPLICABLE,
                    message="Rule is not applicable to this repository.",
                    matched_evidence=applicability_match.matched_evidence,
                    metadata={
                        "applicability_reason": applicability_reason,
                        "applicability_evidence": [
                            {
                                "evidence_type": item.evidence_type.value,
                                "identifier": item.identifier,
                                "source": item.source,
                                "strength": str(item.metadata.get("strength", "")),
                                "path": item.path,
                                "location": item.location,
                            }
                            for item in self._deduplicate(applicability_match.matched_evidence)
                        ],
                    },
                )

            match = self._evaluate_requirement(
                rule.evidence_requirements,
                evidence_repository,
            )
            matched_evidence = self._deduplicate(
                applicability_match.matched_evidence + match.matched_evidence
            )

            if rule.id == SEC_001_RULE_ID:
                return self._evaluate_sec_001(
                    rule,
                    evidence_repository,
                    match,
                    matched_evidence,
                )

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
                message=self._failure_message_for(rule),
                matched_evidence=matched_evidence,
                missing_requirements=match.missing_requirements,
            )
        except InvalidEvidenceRequirementError as exc:
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

    def _evaluate_sec_001(
        self,
        rule: RuleDefinition,
        evidence_repository: EvidenceRepository,
        match: RequirementMatch,
        matched_evidence: list[Evidence],
    ) -> RuleResult:
        if match.matched:
            observed = evidence_repository.find(source="secret_management")
            return RuleResult(
                rule_id=rule.id,
                status=RuleStatus.PASS,
                message="Externalized secret-management evidence detected.",
                matched_evidence=self._deduplicate(matched_evidence + observed),
            )

        potential_evidence = self._deduplicate(
            self._find_sec_001_potential_evidence(evidence_repository)
        )
        if potential_evidence:
            return RuleResult(
                rule_id=rule.id,
                status=RuleStatus.MANUAL_REVIEW,
                message=(
                    "Potential custom secret-management evidence detected. "
                    "Manual review recommended."
                ),
                matched_evidence=potential_evidence,
                missing_requirements=match.missing_requirements,
            )

        return RuleResult(
            rule_id=rule.id,
            status=RuleStatus.FAIL,
            message=self._failure_message_for(rule),
            matched_evidence=[],
            missing_requirements=match.missing_requirements,
        )

    def _failure_message_for(self, rule: RuleDefinition) -> str:
        message = rule.failure_message.strip()
        if message:
            return message
        return DEFAULT_MISSING_EVIDENCE_MESSAGE

    def _find_sec_001_potential_evidence(
        self,
        evidence_repository: EvidenceRepository,
    ) -> list[Evidence]:
        potential = [
            item
            for item in evidence_repository.find(source="secret_management")
            if item.identifier in SEC_001_POTENTIAL_IDENTIFIERS
        ]

        supporting = [
            item
            for item in evidence_repository.find(source="secret_management")
            if item.identifier in SEC_001_SUPPORTING_IDENTIFIERS
        ]
        weak_files = [
            item
            for item in evidence_repository.find(evidence_type=EvidenceType.FILE)
            if item.identifier in SEC_001_WEAK_FILE_IDENTIFIERS
        ]

        if potential:
            return potential + supporting + weak_files
        return []

    def _evaluate_applicability(
        self,
        rule: RuleDefinition,
        evidence_repository: EvidenceRepository,
    ) -> RequirementMatch:
        applicability = rule.applicability
        if not applicability:
            return RequirementMatch(matched=True, matched_evidence=[], missing_requirements=[])

        if set(applicability.keys()) == {"always"}:
            always = applicability.get("always")
            if not isinstance(always, bool):
                raise InvalidEvidenceRequirementError(
                    f"Rule {rule.id}: applicability.always must be a boolean"
                )
            return RequirementMatch(
                matched=always,
                matched_evidence=[],
                missing_requirements=[],
            )

        capability_detector = RepositoryCapabilityDetector(evidence_repository)
        return self._evaluate_applicability_requirement(
            applicability,
            evidence_repository,
            capability_detector,
        )

    def _evaluate_applicability_requirement(
        self,
        requirement: Mapping[str, object],
        evidence_repository: EvidenceRepository,
        capability_detector: RepositoryCapabilityDetector,
    ) -> RequirementMatch:
        if not requirement:
            return RequirementMatch(matched=True, matched_evidence=[], missing_requirements=[])

        if "capability" in requirement:
            capability_value = requirement.get("capability")
            if not isinstance(capability_value, str) or not capability_value.strip():
                raise InvalidEvidenceRequirementError(
                    "applicability capability must be a non-empty string"
                )
            capability_name = capability_value.strip().lower()
            if capability_name not in RepositoryCapabilityDetector.supported_capabilities():
                supported = ", ".join(sorted(RepositoryCapabilityDetector.supported_capabilities()))
                raise InvalidEvidenceRequirementError(
                    f"Unsupported applicability capability {capability_value!r}. Supported: {supported}"
                )

            detected = capability_detector.detect(capability_name)
            if detected.detected:
                metadata_evidence = list(detected.evidence)
                metadata_evidence.extend(detected.ignored_weak_evidence or [])
                return RequirementMatch(
                    matched=True,
                    matched_evidence=self._deduplicate(metadata_evidence),
                    missing_requirements=[],
                )

            if detected.uncertain:
                uncertain_reasons = [detected.reason]
                if detected.ignored_weak_evidence:
                    uncertain_reasons.append("Weak documentary/comment/file hints were ignored for capability confirmation.")
                metadata_evidence = list(detected.evidence)
                metadata_evidence.extend(detected.ignored_weak_evidence or [])
                return RequirementMatch(
                    matched=False,
                    matched_evidence=self._deduplicate(metadata_evidence),
                    missing_requirements=[],
                    uncertain=True,
                    uncertain_reasons=uncertain_reasons,
                )

            return RequirementMatch(
                matched=False,
                matched_evidence=[],
                missing_requirements=[detected.reason],
            )

        has_any = "any" in requirement
        has_all = "all" in requirement
        has_not = "not" in requirement
        operator_count = sum(1 for item in (has_any, has_all, has_not) if item)
        if operator_count > 1:
            raise InvalidEvidenceRequirementError(
                "Applicability requirement cannot contain more than one of 'any', 'all', or 'not'"
            )

        if has_not:
            child = requirement.get("not")
            if not isinstance(child, dict):
                raise InvalidEvidenceRequirementError("Applicability 'not' must contain a mapping")
            child_match = self._evaluate_applicability_requirement(
                child,
                evidence_repository,
                capability_detector,
            )
            if child_match.uncertain:
                return RequirementMatch(
                    matched=False,
                    matched_evidence=child_match.matched_evidence,
                    missing_requirements=[],
                    uncertain=True,
                    uncertain_reasons=child_match.uncertain_reasons,
                )
            if child_match.matched:
                return RequirementMatch(
                    matched=False,
                    matched_evidence=[],
                    missing_requirements=["NOT condition failed for applicability requirement."],
                )
            return RequirementMatch(
                matched=True,
                matched_evidence=[],
                missing_requirements=[],
            )

        if has_any or has_all:
            operator = "any" if has_any else "all"
            children = requirement.get(operator)
            if not isinstance(children, list):
                raise InvalidEvidenceRequirementError(
                    f"Applicability operator '{operator}' must contain a list"
                )
            if not children:
                raise InvalidEvidenceRequirementError(
                    f"Applicability operator '{operator}' requires at least one child requirement"
                )

            child_matches: list[RequirementMatch] = []
            for child in children:
                if not isinstance(child, dict):
                    raise InvalidEvidenceRequirementError(
                        f"Applicability operator '{operator}' child must be a mapping"
                    )
                child_matches.append(
                    self._evaluate_applicability_requirement(
                        child,
                        evidence_repository,
                        capability_detector,
                    )
                )

            if operator == "any":
                for child_match in child_matches:
                    if child_match.matched:
                        return RequirementMatch(
                            matched=True,
                            matched_evidence=child_match.matched_evidence,
                            missing_requirements=[],
                        )

                uncertain_reasons = [
                    reason
                    for child in child_matches
                    if child.uncertain
                    for reason in (child.uncertain_reasons or [])
                ]
                if uncertain_reasons:
                    matched_evidence = [
                        item
                        for child in child_matches
                        for item in child.matched_evidence
                    ]
                    return RequirementMatch(
                        matched=False,
                        matched_evidence=matched_evidence,
                        missing_requirements=[],
                        uncertain=True,
                        uncertain_reasons=uncertain_reasons,
                    )

                return RequirementMatch(
                    matched=False,
                    matched_evidence=[],
                    missing_requirements=[
                        msg
                        for child in child_matches
                        for msg in child.missing_requirements
                    ],
                )

            matched_evidence: list[Evidence] = []
            missing_requirements: list[str] = []
            uncertain_reasons: list[str] = []
            for child_match in child_matches:
                matched_evidence.extend(child_match.matched_evidence)
                missing_requirements.extend(child_match.missing_requirements)

                if child_match.uncertain:
                    uncertain_reasons.extend(child_match.uncertain_reasons or [])

            if uncertain_reasons and not missing_requirements:
                return RequirementMatch(
                    matched=False,
                    matched_evidence=matched_evidence,
                    missing_requirements=[],
                    uncertain=True,
                    uncertain_reasons=uncertain_reasons,
                )

            return RequirementMatch(
                matched=not missing_requirements,
                matched_evidence=matched_evidence,
                missing_requirements=missing_requirements,
            )

        # Backward-compatible path for existing applicability using evidence requirements.
        return self._evaluate_direct_requirement(requirement, evidence_repository)

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
        scope_filter = self._normalize_scope_filter(requirement.get("scope"))
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

        if scope_filter is not None:
            candidates = [
                item
                for item in candidates
                if str(item.metadata.get("source_scope", "")).strip().lower() == scope_filter
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
                missing_requirements=[self._describe_missing(evidence_type, identifiers, source, path_filter, scope_filter)],
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
            missing_requirements=[self._describe_missing(evidence_type, identifiers, source, path_filter, scope_filter)],
        )

    def _normalize_scope_filter(self, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidEvidenceRequirementError("scope must be a string")

        normalized = value.strip().lower()
        if not normalized:
            return None
        if normalized == "any":
            return None
        if normalized not in {"production", "test"}:
            raise InvalidEvidenceRequirementError(
                "scope must be one of: production, test, any"
            )
        return normalized

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
        scope_filter: str | None,
    ) -> str:
        details: list[str] = [f"evidence_type={evidence_type.value.lower()}"]
        if identifiers:
            details.append(f"identifiers={sorted(identifiers)}")
        if source:
            details.append(f"source={source}")
        if path_filter:
            details.append(f"path={sorted(path_filter)}")
        if scope_filter:
            details.append(f"scope={scope_filter}")
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
