from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class LLMConfig:
    enabled: bool = False
    provider: str = "local"
    model_path: str = "./models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
    context_size: int = 4096
    temperature: float = 0.0
    deterministic_fallback: bool = True

    @classmethod
    def from_environment(cls) -> "LLMConfig":
        enabled = os.getenv("EARF_LLM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        return cls(enabled=enabled, model_path=os.getenv("EARF_LLM_MODEL_PATH", cls.model_path),
                   context_size=int(os.getenv("EARF_LLM_CONTEXT_SIZE", cls.context_size)))

    def resolved_model_path(self, repository_root: Path) -> Path:
        path = Path(self.model_path).expanduser()
        return path if path.is_absolute() else repository_root / path
