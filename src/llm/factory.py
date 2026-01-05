from __future__ import annotations

import os
from typing import Any, Callable, Dict

from src.interfaces.exceptions import LLMProviderNotFoundError
from src.interfaces.llm import LLMProvider
from src.llm import OpenAILLMProvider
from src.llm.ollama_client import OllamaLLMProvider

_PROVIDER_REGISTRY: Dict[str, Callable[..., LLMProvider]] = {}

def register_provider(provider_name: str, provider_class: Callable[..., LLMProvider]) -> None:
    _PROVIDER_REGISTRY[provider_name] = provider_class

def get_provider(provider_name: str) -> LLMProvider:
    provider_class = _PROVIDER_REGISTRY.get(provider_name)
    if not provider_class:
        raise LLMProviderNotFoundError(f"LLM provider {provider_name} not found")
    return provider_class

# ============================================================
# Register LLM providers
# ============================================================
register_provider("openai", OpenAILLMProvider)
register_provider("ollama", OllamaLLMProvider)