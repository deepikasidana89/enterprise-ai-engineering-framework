"""Optional local reasoning over small, pre-selected evidence snippets."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

SYSTEM_PROMPT = """You are an evidence verifier for the Enterprise AI Readiness Framework (EARF).
You receive a capability definition and repository evidence selected by EARF.
Determine whether the supplied evidence actually demonstrates implementation.
Do not treat keywords, comments, imports, dependencies, filenames, function names,
or configuration variables as proof on their own. Use only supplied evidence.
Never invent files, code paths, tests, controls, runtime behavior, or relationships.
Use exactly one verdict: VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, or NOT_DETECTED.
Be conservative. Return JSON only with capability, verdict, confidence, reasoning,
supporting_evidence_ids, and missing_evidence."""

VERDICTS = {"VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "NOT_DETECTED"}


@dataclass(frozen=True)
class EvidenceSnippet:
    evidence_id: str
    file: str
    line_start: int
    line_end: int
    evidence_type: str
    reason_detected: str
    content: str


@dataclass
class ReasoningResult:
    capability: str
    verdict: str
    confidence: float
    reasoning: str = ""
    supporting_evidence_ids: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    reasoning_method: str = "deterministic"
    model: str | None = None
    unsupported_evidence_ids: list[str] = field(default_factory=list)


class EvidenceReasoner:
    def evaluate(self, capability: str, evidence: list[EvidenceSnippet]) -> ReasoningResult:
        raise NotImplementedError


class LocalLLMReasoner(EvidenceReasoner):
    def __init__(self, model_path: str | Path, context_size: int = 4096, temperature: float = 0.0, llm: Any = None) -> None:
        self.model_path = Path(model_path)
        self.context_size = context_size
        self.temperature = temperature
        self._llm = llm
        self.unavailable_reason: str | None = None

    @property
    def model(self) -> Any:
        if self._llm is None:
            if not self.model_path.is_file():
                raise RuntimeError("model file does not exist")
            try:
                from llama_cpp import Llama
                self._llm = Llama(model_path=str(self.model_path), n_ctx=self.context_size, verbose=False)
            except Exception as exc:
                self.unavailable_reason = str(exc)
                raise RuntimeError(f"local LLM unavailable: {exc}") from exc
        return self._llm

    def evaluate(self, capability: str, evidence: list[EvidenceSnippet]) -> ReasoningResult:
        ids = {item.evidence_id for item in evidence}
        payload = {"capability": capability, "evidence": [item.__dict__ for item in evidence]}
        prompt = json.dumps(payload, ensure_ascii=False)
        try:
            response = self.model.create_chat_completion(
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            raw = response["choices"][0]["message"]["content"]
            parsed = json.loads(raw)
            verdict = str(parsed.get("verdict", "")).upper()
            confidence = float(parsed.get("confidence", 0.0))
            if verdict not in VERDICTS or not 0.0 <= confidence <= 1.0:
                raise ValueError("invalid verdict or confidence")
            cited = [str(value) for value in parsed.get("supporting_evidence_ids", [])]
            unsupported = [value for value in cited if value not in ids]
            cited = [value for value in cited if value in ids]
            if unsupported:
                confidence = min(confidence, 0.5)
            return ReasoningResult(capability, verdict, confidence, str(parsed.get("reasoning", "")), cited,
                                   [str(v) for v in parsed.get("missing_evidence", [])], "local_llm",
                                   self.model_path.name, unsupported)
        except Exception as exc:
            return ReasoningResult(capability, "UNVERIFIED" if evidence else "NOT_DETECTED", 0.0,
                                   f"Local reasoning failed; deterministic fallback used: {exc}",
                                   reasoning_method="deterministic", model=self.model_path.name)


def deterministic_reasoning(capability: str, evidence: Iterable[EvidenceSnippet]) -> ReasoningResult:
    items = list(evidence)
    if not items:
        return ReasoningResult(capability, "NOT_DETECTED", 0.0, "No candidate evidence supplied.")
    types = {item.evidence_type.lower() for item in items}
    has_runtime = "runtime_call" in types or any("invocation" in item.reason_detected.lower() for item in items)
    verdict = "VERIFIED" if has_runtime and len(items) > 1 else "PARTIALLY_VERIFIED" if items else "NOT_DETECTED"
    return ReasoningResult(capability, verdict, 0.7 if verdict == "VERIFIED" else 0.4,
                           "Deterministic candidate evidence was retained without semantic proof.")
