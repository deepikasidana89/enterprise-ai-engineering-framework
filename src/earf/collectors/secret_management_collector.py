from __future__ import annotations

import re
from pathlib import Path

from .base import EvidenceCollector
from ..models import Evidence, EvidenceType, RepositoryContext


class SecretManagementCollector(EvidenceCollector):
    """Collect repository evidence for externalized secret-management patterns."""

    name = "secret_management"

    _MAX_FILE_BYTES = 1_000_000
    _IGNORED_DIRS = {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
    }
    _NON_PRODUCTION_DIRS = {
        "test",
        "tests",
        "testing",
        "spec",
        "specs",
        "example",
        "examples",
        "sample",
        "samples",
        "fixtures",
        "docs",
    }
    _SUPPORTED_SUFFIXES = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".java",
        ".kt",
        ".go",
        ".cs",
        ".rb",
        ".php",
        ".yaml",
        ".yml",
        ".json",
        ".properties",
        ".env",
        ".tf",
        ".xml",
        ".conf",
        ".ini",
        ".toml",
    }

    _KNOWN_PROVIDER_PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
        (
            "sec.externalized_secret.vault_usage",
            "HashiCorp Vault integration pattern detected",
            re.compile(
                r"\bhvac\b|"
                r"hashicorp[/._-]?vault|"
                r"com\.bettercloud\.vault|"
                r"\bvault\s+kv\s+(get|put)\b|"
                r"\bVaultClient\b",
                re.IGNORECASE,
            ),
        ),
        (
            "sec.externalized_secret.aws_usage",
            "AWS Secrets Manager integration pattern detected",
            re.compile(
                r"software\.amazon\.awssdk\.services\.secretsmanager|"
                r"com\.amazonaws\.services\.secretsmanager|"
                r"@aws-sdk/client-secrets-manager|"
                r"\bSecretsManager(Client|AsyncClient|Builder)?\b|"
                r"boto3\.client\(\s*['\"]secretsmanager['\"]",
                re.IGNORECASE,
            ),
        ),
        (
            "sec.externalized_secret.azure_usage",
            "Azure Key Vault integration pattern detected",
            re.compile(
                r"azure[-_.]keyvault[-_.]secrets|"
                r"@azure/keyvault-secrets|"
                r"com\.azure\.security\.keyvault|"
                r"Azure\.Security\.KeyVault\.Secrets|"
                r"\bKeyVaultSecret\b",
                re.IGNORECASE,
            ),
        ),
        (
            "sec.externalized_secret.gcp_usage",
            "GCP Secret Manager integration pattern detected",
            re.compile(
                r"google[-_.]cloud[-_.]secret[-_.]manager|"
                r"google\.cloud\.secretmanager|"
                r"@google-cloud/secret-manager|"
                r"\bSecretManagerServiceClient\b",
                re.IGNORECASE,
            ),
        ),
        (
            "sec.externalized_secret.kubernetes_secret_ref",
            "Kubernetes Secret reference pattern detected",
            re.compile(
                r"valueFrom\s*:\s*(?:\r?\n\s*)+secretKeyRef\s*:|"
                r"\bsecretKeyRef\b|"
                r"\bSecretKeySelector\b",
                re.IGNORECASE,
            ),
        ),
    )

    _CUSTOM_ABSTRACTION_PATTERN = re.compile(
        r"\b("
        r"[A-Za-z0-9_]*SecretManager|"
        r"[A-Za-z0-9_]*SecretsManager|"
        r"[A-Za-z0-9_]*CredentialProvider|"
        r"[A-Za-z0-9_]*CredentialsProvider|"
        r"[A-Za-z0-9_]*CredentialService|"
        r"[A-Za-z0-9_]*SecretProvider|"
        r"[A-Za-z0-9_]*SecretsProvider|"
        r"[A-Za-z0-9_]*VaultClient|"
        r"[A-Za-z0-9_]*KeyProvider|"
        r"[A-Za-z0-9_]*SecureConfigProvider"
        r")\b",
        re.IGNORECASE,
    )

    _SENSITIVE_ENV_NAME = r"[A-Z0-9_]*(API_KEY|SECRET|TOKEN|PASSWORD|CLIENT_SECRET|PRIVATE_KEY|CREDENTIALS?)" \
        r"[A-Z0-9_]*"
    _SENSITIVE_ENV_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(rf"os\.getenv\(\s*['\"]{_SENSITIVE_ENV_NAME}['\"]\s*\)", re.IGNORECASE),
        re.compile(rf"os\.environ\[\s*['\"]{_SENSITIVE_ENV_NAME}['\"]\s*\]", re.IGNORECASE),
        re.compile(rf"System\.getenv\(\s*['\"]{_SENSITIVE_ENV_NAME}['\"]\s*\)", re.IGNORECASE),
        re.compile(rf"process\.env\.{_SENSITIVE_ENV_NAME}\b", re.IGNORECASE),
        re.compile(rf"@Value\(\s*['\"]\$\{{[^}}]*{_SENSITIVE_ENV_NAME}[^}}]*\}}['\"]\s*\)", re.IGNORECASE),
        re.compile(rf"\$\{{[^}}]*{_SENSITIVE_ENV_NAME}[^}}]*\}}", re.IGNORECASE),
    )

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        root = context.root_path
        items: list[Evidence] = []

        for file_path in self._iter_candidate_files(root):
            rel_path = str(file_path.relative_to(root))
            content = self._read_text(file_path)
            if content is None:
                continue

            for identifier, description, pattern in self._KNOWN_PROVIDER_PATTERNS:
                line = self._first_match_line(content, pattern)
                if line is not None:
                    items.append(
                        self._build_evidence(
                            identifier=identifier,
                            description=description,
                            path=rel_path,
                            line=line,
                        )
                    )

            custom_line = self._first_match_line(content, self._CUSTOM_ABSTRACTION_PATTERN)
            if custom_line is not None:
                items.append(
                    self._build_evidence(
                        identifier="sec.externalized_secret.custom_abstraction",
                        description="Potential custom secret-management abstraction detected",
                        path=rel_path,
                        line=custom_line,
                    )
                )

            for pattern in self._SENSITIVE_ENV_PATTERNS:
                sensitive_line = self._first_match_line(content, pattern)
                if sensitive_line is not None:
                    items.append(
                        self._build_evidence(
                            identifier="sec.externalized_secret.sensitive_env_access",
                            description="Sensitive environment-variable access pattern detected",
                            path=rel_path,
                            line=sensitive_line,
                        )
                    )
                    break

        return sorted(items, key=lambda item: (item.identifier, item.path or "", item.location or ""))

    def _iter_candidate_files(self, root: Path) -> list[Path]:
        candidates: list[Path] = []
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in self._IGNORED_DIRS for part in file_path.parts):
                continue
            if self._looks_like_non_production_path(file_path.relative_to(root)):
                continue
            if file_path.suffix.lower() not in self._SUPPORTED_SUFFIXES:
                continue
            try:
                if file_path.stat().st_size > self._MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            candidates.append(file_path)
        return candidates

    def _looks_like_non_production_path(self, relative_path: Path) -> bool:
        lowered_parts = {part.lower() for part in relative_path.parts}
        if lowered_parts.intersection(self._NON_PRODUCTION_DIRS):
            return True

        name = relative_path.name.lower()
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or name.endswith(".spec.ts")
            or name.endswith(".spec.js")
        )

    def _read_text(self, file_path: Path) -> str | None:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

    def _first_match_line(self, content: str, pattern: re.Pattern[str]) -> int | None:
        match = pattern.search(content)
        if match is None:
            return None
        line_number = content.count("\n", 0, match.start()) + 1
        return line_number

    def _build_evidence(
        self,
        *,
        identifier: str,
        description: str,
        path: str,
        line: int,
    ) -> Evidence:
        location = f"{path}:{line}"
        return Evidence(
            evidence_type=EvidenceType.CONFIGURATION,
            source=self.name,
            description=description,
            identifier=identifier,
            path=path,
            location=location,
            metadata={"collector": self.name, "line": line},
        )


# Backward-compatible alias for existing imports.
SecretManagementEvidenceCollector = SecretManagementCollector