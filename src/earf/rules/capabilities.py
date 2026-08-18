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
            return self._detect_dependency_capability(capability, self._AGENT_DEPENDENCIES)

        if capability == "has_api":
            return self._detect_dependency_capability(capability, self._API_DEPENDENCIES)

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

    def _dependency_matches(self, expected_identifiers: set[str]) -> list[Evidence]:
        dependencies = self._repository.find(evidence_type=EvidenceType.DEPENDENCY)
        expected = {item.lower() for item in expected_identifiers}
        return [item for item in dependencies if item.identifier.lower() in expected]

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
