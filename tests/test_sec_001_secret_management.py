from __future__ import annotations

from pathlib import Path

from earf.evidence_collection import EvidenceCollectionService
from earf.models import RepositoryContext
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleResult, RuleStatus


def _rules_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "rules"


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def _evaluate_sec_001(repo_path: Path) -> RuleResult:
    catalog, _ = RuleCatalog.from_path(_rules_dir())
    sec_001 = catalog.get("SEC-001")
    evidence_repo = EvidenceCollectionService().collect(_context(repo_path))
    return RuleEvaluationService().evaluate_all(
        RuleCatalog([sec_001]),
        evidence_repo,
    )[0]


def test_sec_001_env_example_alone_is_not_sufficient(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("API_KEY=", encoding="utf-8")

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.FAIL
    assert result.message == "No supported evidence of externalized secret management was detected."


def test_sec_001_passes_for_aws_secrets_manager_usage(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("boto3>=1.34.0", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "import boto3\n"
        "client = boto3.client('secretsmanager')\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.PASS
    assert result.message == "Externalized secret-management evidence detected."
    assert any(item.identifier == "sec.externalized_secret.aws_usage" for item in result.matched_evidence)


def test_sec_001_passes_for_azure_key_vault_usage(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "from azure.keyvault.secrets import SecretClient\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.PASS
    assert any(item.identifier == "sec.externalized_secret.azure_usage" for item in result.matched_evidence)


def test_sec_001_passes_for_hashicorp_vault_usage(tmp_path: Path) -> None:
    (tmp_path / "security.py").write_text(
        "import hvac\n"
        "client = hvac.Client(url='https://vault.internal')\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.PASS
    assert any(item.identifier == "sec.externalized_secret.vault_usage" for item in result.matched_evidence)


def test_sec_001_passes_for_gcp_secret_manager_usage(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text(
        "from google.cloud import secretmanager\n"
        "client = secretmanager.SecretManagerServiceClient()\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.PASS
    assert any(item.identifier == "sec.externalized_secret.gcp_usage" for item in result.matched_evidence)


def test_sec_001_passes_for_kubernetes_secret_reference(tmp_path: Path) -> None:
    (tmp_path / "deployment.yaml").write_text(
        "env:\n"
        "  - name: API_TOKEN\n"
        "    valueFrom:\n"
        "      secretKeyRef:\n"
        "        name: app-secrets\n"
        "        key: api-token\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.PASS
    assert any(
        item.identifier == "sec.externalized_secret.kubernetes_secret_ref"
        for item in result.matched_evidence
    )


def test_sec_001_custom_abstraction_without_supporting_signals_needs_manual_review(tmp_path: Path) -> None:
    (tmp_path / "EnterpriseCredentialProvider.java").write_text(
        "public class EnterpriseCredentialProvider {}\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.MANUAL_REVIEW
    assert result.message == "Potential custom secret-management evidence detected. Manual review recommended."
    assert any(item.identifier == "sec.externalized_secret.custom_abstraction" for item in result.matched_evidence)


def test_sec_001_dependency_only_does_not_pass(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("boto3>=1.34.0", encoding="utf-8")

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.FAIL
    assert result.message == "No supported evidence of externalized secret management was detected."


def test_sec_001_irrelevant_environment_variable_does_not_pass(tmp_path: Path) -> None:
    (tmp_path / "App.java").write_text(
        "class App { String p = System.getenv(\"PORT\"); }\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.FAIL
    assert result.message == "No supported evidence of externalized secret management was detected."


def test_sec_001_likely_secret_environment_variable_is_supporting_only(tmp_path: Path) -> None:
    (tmp_path / "App.java").write_text(
        "class App { String s = System.getenv(\"CLIENT_SECRET\"); }\n",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.FAIL
    assert result.message == "No supported evidence of externalized secret management was detected."


def test_sec_001_no_evidence_fails_with_supported_message(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.FAIL
    assert result.message == "No supported evidence of externalized secret management was detected."


def test_sec_001_generic_word_secret_in_readme_does_not_pass(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "Remember to protect your secrets.",
        encoding="utf-8",
    )

    result = _evaluate_sec_001(tmp_path)

    assert result.status == RuleStatus.FAIL
    assert result.message == "No supported evidence of externalized secret management was detected."