import json
from pathlib import Path

import pytest

from earf.reasoning import EvidenceSnippet, LocalLLMReasoner


FIXTURES = Path(__file__).parent / "fixtures" / "llm_usage"


class FixtureModel:
    def __init__(self, verdict):
        self.verdict = verdict

    def create_chat_completion(self, **kwargs):
        return {"choices": [{"message": {"content": json.dumps({
            "capability": "uses_llm",
            "verdict": self.verdict,
            "confidence": 0.9,
            "reasoning": "Fixture evaluation",
            "supporting_evidence_ids": ["E1"],
            "missing_evidence": []
        })}}]}


def _fixture_names():
    return sorted(path.name for path in FIXTURES.iterdir() if path.is_dir())


@pytest.mark.parametrize("fixture_name", _fixture_names())
def test_labeled_fixture_has_expected_verdict(fixture_name):
    fixture = FIXTURES / fixture_name
    expected = json.loads((fixture / "expected.json").read_text())
    source = "\n".join(
        path.read_text(errors="ignore") for path in fixture.rglob("*") if path.is_file() and path.name != "expected.json"
    )
    evidence = [EvidenceSnippet("E1", "fixture", 1, max(1, len(source.splitlines())), "SOURCE_CODE", "fixture evidence", source)]
    result = LocalLLMReasoner("missing.gguf", llm=FixtureModel(expected["expected_verdict"])).evaluate(expected["capability"], evidence)
    assert result.verdict == expected["expected_verdict"]


def test_fixture_set_contains_negative_cases():
    assert {"dependency_only", "commented_only", "client_without_call"}.issubset(_fixture_names())
