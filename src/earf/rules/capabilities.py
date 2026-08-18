from __future__ import annotations

from dataclasses import dataclass

from ..evidence import EvidenceRepository
from ..models import Evidence, EvidenceType


@dataclass(frozen=True)
class CapabilityDetection:
    name: str
    detected: bool
    reason: str
    evidence: list[Evidence]


class RepositoryCapabilityDetector:
    """Deterministic capability detector based on collected repository evidence."""

    _SUPPORTED_CAPABILITIES = {
        "uses_llm",
        "uses_rag",
        "uses_agents",
        "has_api",
        "has_cicd",
    }

    _LLM_DEPENDENCIES = {
        "openai",
        "anthropic",
        "langchain",
        "langgraph",
        "transformers",
        "llama-index",
        "litellm",
        "semantic-kernel",
        "google-generativeai",
        "azure-ai-inference",
    }

    _RAG_FRAMEWORK_DEPENDENCIES = {
        "langchain",
        "llama-index",
        "haystack-ai",
    }
    _VECTOR_STORE_DEPENDENCIES = {
        "chromadb",
        "faiss-cpu",
        "pinecone-client",
        "qdrant-client",
        "weaviate-client",
        "pymilvus",
        "milvus",
        "pgvector",
    }

    _AGENT_DEPENDENCIES = {
        "langgraph",
        "autogen",
        "pyautogen",
        "crewai",
    }

    _API_DEPENDENCIES = {
        "fastapi",
        "flask",
        "django",
        "djangorestframework",
        "spring-boot-starter-web",
        "spring-web",
        "express",
        "@nestjs/core",
        "gin",
    }

    _API_CODE_PATTERNS = {
        "spring_rest_controller",
        "spring_request_mapping",
        "fastapi_app_init",
        "fastapi_route_decorator",
        "flask_route_decorator",
        "express_app_init",
        "express_router_method",
    }

    _AGENT_CODE_PATTERNS = {
        "langgraph_state_graph",
        "langchain_agent_executor",
        "crewai_agent_construct",
        "autogen_agent_construct",
    }

    _RAG_EMBEDDING_CODE_PATTERNS = {
        "rag_embedding_api_call",
    }
    _RAG_VECTOR_CODE_PATTERNS = {
        "rag_vector_query_call",
    }
    _RAG_RETRIEVER_CODE_PATTERNS = {
        "rag_retriever_chain",
    }

    def __init__(self, evidence_repository: EvidenceRepository) -> None:
        self._repository = evidence_repository
        self._cache: dict[str, CapabilityDetection] = {}

    @classmethod
    def supported_capabilities(cls) -> set[str]:
        return set(cls._SUPPORTED_CAPABILITIES)

    def detect(self, capability: str) -> CapabilityDetection:
        name = capability.strip().lower()
        if name in self._cache:
            return self._cache[name]

        detection = self._detect_uncached(name)
        self._cache[name] = detection
        return detection

    def _detect_uncached(self, capability: str) -> CapabilityDetection:
        if capability == "uses_llm":
            return self._detect_dependency_capability(capability, self._LLM_DEPENDENCIES)

        if capability == "uses_agents":
            return self._detect_dependency_or_code_pattern_capability(
                capability,
                dependency_identifiers=self._AGENT_DEPENDENCIES,
                code_pattern_identifiers=self._AGENT_CODE_PATTERNS,
            )

        if capability == "has_api":
            return self._detect_dependency_or_code_pattern_capability(
                capability,
                dependency_identifiers=self._API_DEPENDENCIES,
                code_pattern_identifiers=self._API_CODE_PATTERNS,
            )

        if capability == "has_cicd":
            workflows = self._repository.find(evidence_type=EvidenceType.WORKFLOW)
            if workflows:
                return CapabilityDetection(
                    name=capability,
                    detected=True,
                    reason="CI/CD workflow evidence detected.",
                    evidence=workflows,
                )
            return CapabilityDetection(
                name=capability,
                detected=False,
                reason="CI/CD capability evidence was not detected.",
                evidence=[],
            )

        if capability == "uses_rag":
            rag_framework_hits = self._dependency_matches(self._RAG_FRAMEWORK_DEPENDENCIES)
            vector_hits = self._dependency_matches(self._VECTOR_STORE_DEPENDENCIES)
            if rag_framework_hits and vector_hits:
                return CapabilityDetection(
                    name=capability,
                    detected=True,
                    reason="RAG capability evidence detected from framework and vector-store dependencies.",
                    evidence=self._dedupe(rag_framework_hits + vector_hits),
                )

            # Conservatively allow well-known integrated RAG frameworks.
            if rag_framework_hits and any(item.identifier.lower() == "llama-index" for item in rag_framework_hits):
                return CapabilityDetection(
                    name=capability,
                    detected=True,
                    reason="RAG capability evidence detected from integrated retrieval framework dependency.",
                    evidence=rag_framework_hits,
                )

            embedding_hits = self._code_pattern_matches(self._RAG_EMBEDDING_CODE_PATTERNS)
            vector_pattern_hits = self._code_pattern_matches(self._RAG_VECTOR_CODE_PATTERNS)
            retriever_hits = self._code_pattern_matches(self._RAG_RETRIEVER_CODE_PATTERNS)
            if embedding_hits and vector_pattern_hits and retriever_hits:
                return CapabilityDetection(
                    name=capability,
                    detected=True,
                    reason=(
                        "RAG capability evidence detected from embedding generation, "
                        "vector query, and retriever-chain implementation patterns."
                    ),
                    evidence=self._dedupe(
                        embedding_hits + vector_pattern_hits + retriever_hits
                    ),
                )

            return CapabilityDetection(
                name=capability,
                detected=False,
                reason="RAG capability evidence was not detected.",
                evidence=[],
            )

        return CapabilityDetection(
            name=capability,
            detected=False,
            reason=f"Unsupported capability: {capability}",
            evidence=[],
        )

    def _detect_dependency_capability(
        self,
        capability: str,
        expected_identifiers: set[str],
    ) -> CapabilityDetection:
        matches = self._dependency_matches(expected_identifiers)
        if matches:
            return CapabilityDetection(
                name=capability,
                detected=True,
                reason=f"{capability} capability evidence detected.",
                evidence=matches,
            )

        return CapabilityDetection(
            name=capability,
            detected=False,
            reason=f"{capability} capability evidence was not detected.",
            evidence=[],
        )

    def _detect_dependency_or_code_pattern_capability(
        self,
        capability: str,
        *,
        dependency_identifiers: set[str],
        code_pattern_identifiers: set[str],
    ) -> CapabilityDetection:
        dependency_hits = self._dependency_matches(dependency_identifiers)
        code_pattern_hits = self._code_pattern_matches(code_pattern_identifiers)
        combined = self._dedupe(dependency_hits + code_pattern_hits)
        if combined:
            return CapabilityDetection(
                name=capability,
                detected=True,
                reason=f"{capability} capability evidence detected.",
                evidence=combined,
            )

        return CapabilityDetection(
            name=capability,
            detected=False,
            reason=f"{capability} capability evidence was not detected.",
            evidence=[],
        )

    def _dependency_matches(self, expected_identifiers: set[str]) -> list[Evidence]:
        dependencies = self._repository.find(evidence_type=EvidenceType.DEPENDENCY)
        expected = {item.lower() for item in expected_identifiers}
        return [item for item in dependencies if item.identifier.lower() in expected]

    def _code_pattern_matches(self, expected_identifiers: set[str]) -> list[Evidence]:
        patterns = self._repository.find(evidence_type=EvidenceType.CODE_PATTERN)
        expected = {item.lower() for item in expected_identifiers}
        return [item for item in patterns if item.identifier.lower() in expected]

    def _dedupe(self, evidence: list[Evidence]) -> list[Evidence]:
        seen: set[tuple[str, str, str | None]] = set()
        result: list[Evidence] = []
        for item in evidence:
            key = (item.source, item.identifier, item.location)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result
