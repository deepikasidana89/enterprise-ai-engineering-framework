from __future__ import annotations

class EARFError(Exception):
    """Base class for EARF errors."""


class RepositoryError(EARFError):
    """Errors related to repository access or loading."""


class InvalidRepositoryPathError(RepositoryError):
    """Raised when a provided repository path is invalid."""


class RuleDefinitionError(EARFError):
    pass


class RuleLoadError(RuleDefinitionError):
    pass


class RuleValidationError(RuleDefinitionError):
    pass


class DuplicateRuleError(RuleDefinitionError):
    pass


class RuleNotFoundError(RuleDefinitionError):
    pass


class InvalidEvidenceRequirementError(RuleDefinitionError):
    pass


class UnsupportedApplicabilityError(RuleDefinitionError):
    pass


class RuleEvaluationError(RuleDefinitionError):
    pass


class ConfigurationError(EARFError):
    pass


class ScanError(EARFError):
    pass


class ReportingError(EARFError):
    pass
