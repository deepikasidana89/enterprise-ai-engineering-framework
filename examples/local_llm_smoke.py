"""Manual smoke test: run with EARF_LLM_ENABLED=true python examples/local_llm_smoke.py."""
from earf.llm_config import LLMConfig
from earf.reasoning import EvidenceSnippet, LocalLLMReasoner

evidence = [EvidenceSnippet("E1", "payment.py", 1, 5, "CODE", "approval-related execution path",
                            "if request.risk == 'HIGH': require_human_approval(request)\nreturn process_payment(request)")]
result = LocalLLMReasoner(LLMConfig.from_environment().model_path).evaluate("human_approval_boundary", evidence)
print(result)
