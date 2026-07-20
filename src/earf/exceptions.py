from __future__ import annotations

class EARFError(Exception):
    """Base class for EARF errors."""


class RepositoryError(EARFError):
    """Errors related to repository access or loading."""


class InvalidRepositoryPathError(RepositoryError):
    """Raised when a provided repository path is invalid."""


class RuleDefinitionError(EARFError):
    pass


class DuplicateRuleError(RuleDefinitionError):
    pass


class ConfigurationError(EARFError):
    pass


class ScanError(EARFError):
    pass


class ReportingError(EARFError):
    pass
