from __future__ import annotations

from pathlib import Path

from earf.evidence_collection import EvidenceCollectionService
from earf.models import RepositoryContext, RuleDefinition, Severity
from earf.rules.capabilities import RepositoryCapabilityDetector
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleStatus
from earf.scoring.service import ScoringService


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def _rule(
    rule_id: str,
    *,
    applicability: dict[str, object],
    evidence_requirements: dict[str, object],
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        title=f"{rule_id} title",
        description="desc",
        category="evaluation",
        severity=Severity.HIGH,
        applicability=applicability,
        evidence_requirements=evidence_requirements,
        recommendation="do",
    )


def _collect(tmp_path: Path):
    return EvidenceCollectionService().collect(_context(tmp_path))


def test_rag_rule_no_rag_returns_not_applicable(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "EVA-001",
        applicability={"all": [{"capability": "uses_rag"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.NOT_APPLICABLE


def test_rag_rule_rag_detected_is_evaluated_normally(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "langchain>=0.2.0\nchromadb>=0.5.0\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "EVA-001",
        applicability={"all": [{"capability": "uses_rag"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.PASS


def test_api_rule_no_api_returns_not_applicable(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "SAF-001",
        applicability={"all": [{"capability": "has_api"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.NOT_APPLICABLE


def test_api_rule_fastapi_detected_is_evaluated(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\nfastapi>=0.110.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("AI project", encoding="utf-8")

    rule = _rule(
        "SAF-001",
        applicability={"all": [{"capability": "has_api"}]},
        evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
    )

    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), _collect(tmp_path))[0]

    assert result.status == RuleStatus.PASS


def test_has_cicd_detected_from_workflow(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "test.yml").write_text("name: ci", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("has_cicd")

    assert detection.detected is True
    assert detection.evidence


def test_uses_llm_detected_from_dependency(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai" for item in detection.evidence)


def test_uses_llm_detected_from_version_pinned_openai(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai==1.40.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai" for item in detection.evidence)


def test_uses_llm_detected_from_mixed_case_openai_dependency(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("OpenAI>=1.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai" for item in detection.evidence)


def test_uses_llm_detected_from_langchain_openai_hyphen_dependency(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("langchain-openai==0.3.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "langchain-openai" for item in detection.evidence)


def test_uses_llm_detected_from_langchain_openai_underscore_dependency(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("langchain_openai\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "langchain-openai" for item in detection.evidence)


def test_uses_llm_detected_from_openai_import_pattern(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("from openai import OpenAI\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai_client_import" for item in detection.evidence)


def test_uses_llm_detected_from_async_openai_constructor_pattern(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("client = AsyncOpenAI()\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai_client_construct" for item in detection.evidence)


def test_uses_llm_detected_from_azure_chat_openai_pattern(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("llm = AzureChatOpenAI()\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "langchain_chat_provider_construct" for item in detection.evidence)


def test_generic_model_service_does_not_trigger_uses_llm(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text(
        "class ModelService:\n"
        "    def get_model(self, model_config_id):\n"
        "        return model_config_id\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is False


def test_generic_pricing_model_predict_does_not_trigger_uses_llm(tmp_path: Path) -> None:
    (tmp_path / "pricing.py").write_text(
        "class PricingModel:\n"
        "    def predict(self, features):\n"
        "        return 0\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is False


def test_substring_package_name_does_not_trigger_uses_llm(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("my-openai-helper\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is False


def test_openai_prefixed_internal_package_does_not_trigger_uses_llm(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai-tools-internal\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is False


def test_uses_llm_detected_from_real_requirements_file_path(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture_openai"
    fixture.mkdir()
    (fixture / "requirements.txt").write_text("openai==1.40.0\n", encoding="utf-8")
    repo = _collect(fixture)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(item.identifier == "openai" and item.path == "requirements.txt" for item in detection.evidence)


def test_uses_llm_detected_from_real_pyproject_dependency_path(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture_langchain_openai"
    fixture.mkdir()
    (fixture / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                "name = \"fixture-langchain-openai\"",
                "version = \"0.1.0\"",
                "dependencies = [\"langchain-openai==0.3.0\"]",
            ]
        ),
        encoding="utf-8",
    )
    repo = _collect(fixture)

    detection = RepositoryCapabilityDetector(repo).detect("uses_llm")

    assert detection.detected is True
    assert any(
        item.identifier == "langchain-openai" and item.path == "pyproject.toml"
        for item in detection.evidence
    )


def test_readme_keyword_does_not_trigger_rag(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("We may use RAG someday.", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_rag")

    assert detection.detected is False


def test_readme_keyword_does_not_trigger_api_or_agents(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "This service exposes an API and uses agent orchestration.",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    api_detection = RepositoryCapabilityDetector(repo).detect("has_api")
    agent_detection = RepositoryCapabilityDetector(repo).detect("uses_agents")

    assert api_detection.detected is False
    assert agent_detection.detected is False


def test_has_api_detected_from_code_pattern_without_dependency(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("has_api")

    assert detection.detected is True
    assert any(item.evidence_type.name == "CODE_PATTERN" for item in detection.evidence)


def test_uses_agents_detected_from_code_pattern_without_dependency(tmp_path: Path) -> None:
    (tmp_path / "agent_flow.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "graph = StateGraph(dict)\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_agents")

    assert detection.detected is True
    assert any(item.identifier == "langgraph_state_graph" for item in detection.evidence)


def test_generic_agent_service_name_does_not_trigger_uses_agents(tmp_path: Path) -> None:
    (tmp_path / "agent_service.py").write_text(
        "class AgentService:\n"
        "    pass\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_agents")

    assert detection.detected is False


def test_uses_rag_detected_from_code_pattern_combination(tmp_path: Path) -> None:
    (tmp_path / "rag_pipeline.py").write_text(
        "result = client.embeddings.create(input='q', model='text-embedding-3-small')\n"
        "hits = collection.query(query_embeddings=[result], n_results=5)\n"
        "retriever = vectorstore.as_retriever()\n"
        "chain = create_retrieval_chain(retriever, combine_docs_chain)\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_rag")

    assert detection.detected is True
    identifiers = {item.identifier for item in detection.evidence}
    assert "rag_embedding_api_call" in identifiers
    assert "rag_vector_query_call" in identifiers
    assert "rag_retriever_chain" in identifiers


def test_uses_rag_needs_full_pattern_combination(tmp_path: Path) -> None:
    (tmp_path / "rag_partial.py").write_text(
        "result = client.embeddings.create(input='q', model='text-embedding-3-small')\n"
        "hits = collection.query(query_embeddings=[result], n_results=5)\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_rag")

    assert detection.detected is False


def test_not_applicable_rules_not_in_score_denominator() -> None:
    rules = RuleCatalog(
        [
            _rule(
                "GOV-001",
                applicability={"always": True},
                evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
            ),
            _rule(
                "GOV-002",
                applicability={"always": True},
                evidence_requirements={"evidence_type": "file", "identifiers": ["SECURITY.md"]},
            ),
            _rule(
                "EVA-001",
                applicability={"all": [{"capability": "uses_rag"}]},
                evidence_requirements={"evidence_type": "file", "identifiers": ["README.md"]},
            ),
        ]
    )

    tmp_path = Path(".")
    repo = EvidenceCollectionService().collect(RepositoryContext(root_path=tmp_path, project_name="x"))

    # Build deterministic direct evidence instead of scanning current workspace files.
    from earf.evidence import EvidenceRepository
    from earf.models import Evidence, EvidenceType

    direct_repo = EvidenceRepository()
    direct_repo.add(
        Evidence(
            evidence_type=EvidenceType.FILE,
            source="file",
            description="readme",
            identifier="README.md",
        )
    )

    results = RuleEvaluationService().evaluate_all(rules, direct_repo)
    score = ScoringService().score(results, rules)

    assert score.not_applicable_rules == 1
    assert score.overall_score == 50.0


def test_capability_provenance_for_agents(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("langgraph>=0.2.0\n", encoding="utf-8")
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_agents")

    assert detection.detected is True
    assert any(item.identifier == "langgraph" for item in detection.evidence)


def test_capability_provenance_includes_dependency_and_code_pattern(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("langgraph>=0.2.0\n", encoding="utf-8")
    (tmp_path / "agent_flow.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "graph = StateGraph(dict)\n",
        encoding="utf-8",
    )
    repo = _collect(tmp_path)

    detection = RepositoryCapabilityDetector(repo).detect("uses_agents")

    assert detection.detected is True
    identifiers = {item.identifier for item in detection.evidence}
    assert "langgraph" in identifiers
    assert "langgraph_state_graph" in identifiers
