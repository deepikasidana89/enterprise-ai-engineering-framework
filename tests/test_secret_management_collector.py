from __future__ import annotations

from pathlib import Path

from earf.collectors.secret_management_collector import SecretManagementCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_secret_management_collector_detects_known_provider_usage(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "import boto3\n"
        "client = boto3.client('secretsmanager')\n",
        encoding="utf-8",
    )

    items = SecretManagementCollector().collect(_context(tmp_path))
    identifiers = {item.identifier for item in items}

    assert "sec.externalized_secret.aws_usage" in identifiers


def test_secret_management_collector_detects_custom_abstraction_and_sensitive_env(tmp_path: Path) -> None:
    (tmp_path / "security.py").write_text(
        "class EnterpriseCredentialProvider:\n"
        "    pass\n"
        "token = os.getenv('CLIENT_SECRET')\n",
        encoding="utf-8",
    )

    items = SecretManagementCollector().collect(_context(tmp_path))
    identifiers = {item.identifier for item in items}

    assert "sec.externalized_secret.custom_abstraction" in identifiers
    assert "sec.externalized_secret.sensitive_env_access" in identifiers


def test_secret_management_collector_ignores_irrelevant_env_variable(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "import os\n"
        "port = os.getenv('PORT')\n",
        encoding="utf-8",
    )

    items = SecretManagementCollector().collect(_context(tmp_path))

    assert all(item.identifier != "sec.externalized_secret.sensitive_env_access" for item in items)


def test_secret_management_collector_detects_node_and_dotnet_provider_variants(tmp_path: Path) -> None:
    (tmp_path / "index.ts").write_text(
        "import { SecretsManagerClient } from '@aws-sdk/client-secrets-manager';\n",
        encoding="utf-8",
    )
    (tmp_path / "Program.cs").write_text(
        "using Azure.Security.KeyVault.Secrets;\n",
        encoding="utf-8",
    )

    items = SecretManagementCollector().collect(_context(tmp_path))
    identifiers = {item.identifier for item in items}

    assert "sec.externalized_secret.aws_usage" in identifiers
    assert "sec.externalized_secret.azure_usage" in identifiers


def test_secret_management_collector_ignores_test_and_docs_paths(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_secrets.py").write_text(
        "client = boto3.client('secretsmanager')\n",
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "security.md").write_text(
        "Use HashiCorp Vault and SecretManagerServiceClient.\n",
        encoding="utf-8",
    )

    items = SecretManagementCollector().collect(_context(tmp_path))

    assert items == []