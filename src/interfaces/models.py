from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class LLMConfig:
    provider: str
    api_key: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FewShotExample:
    user: str
    assistant: str


@dataclass
class LLMRequest:
    prompt: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    domain_prompt: Optional[str] = None
    feedback: Optional[str] = None
    fewshots: list[FewShotExample] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)