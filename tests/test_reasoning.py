import json
from pathlib import Path

from earf.reasoning import EvidenceSnippet, LocalLLMReasoner


EVIDENCE = [EvidenceSnippet("E1", "app.py", 1, 2, "SOURCE_CODE", "provider call", "client.responses.create(...)")]


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def create_chat_completion(self, **kwargs):
        return {"choices": [{"message": {"content": json.dumps(self.payload)}}]}


def reason(payload):
    return LocalLLMReasoner(Path("missing.gguf"), llm=FakeLLM(payload)).evaluate("uses_llm", EVIDENCE)


def test_verified_result():
    assert reason({"verdict": "VERIFIED", "confidence": .9, "supporting_evidence_ids": ["E1"]}).verdict == "VERIFIED"


def test_partial_result():
    assert reason({"verdict": "PARTIALLY_VERIFIED", "confidence": .8, "supporting_evidence_ids": ["E1"]}).verdict == "PARTIALLY_VERIFIED"


def test_unverified_result():
    assert reason({"verdict": "UNVERIFIED", "confidence": .2, "supporting_evidence_ids": []}).verdict == "UNVERIFIED"


def test_invalid_json_falls_back():
    class Invalid:
        def create_chat_completion(self, **kwargs):
            return {"choices": [{"message": {"content": "not json"}}]}
    result = LocalLLMReasoner(Path("missing.gguf"), llm=Invalid()).evaluate("uses_llm", EVIDENCE)
    assert result.reasoning_method == "deterministic"


def test_unknown_evidence_ids_are_removed_and_confidence_lowered():
    result = reason({"verdict": "VERIFIED", "confidence": .9, "supporting_evidence_ids": ["E1", "E99"]})
    assert result.supporting_evidence_ids == ["E1"]
    assert result.unsupported_evidence_ids == ["E99"]
    assert result.confidence == .5
