from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from src.interfaces.models import LLMConfig, LLMRequest
from src.prompts.rtec_policy import OUTPUT_POLICY

class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Handles the construction of a strictly controlled prompt format:
    <system>, <domain>, <example>, <user>.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    def generate(self, request: LLMRequest) -> str:
        """
        Unified method for building a complete prompt and calling the provider.
        """
        final_prompt = self._build_prompt(request)
        return self._call_provider(final_prompt)

    def _build_prompt(self, request: LLMRequest) -> str:
        """
        Builds a structured prompt with consistent ordering:
        <system>, <policy>, <domain>, <example>*, <user>
        """
        parts = []

        # REQUIRED: System prompt
        if request.system_prompt:
            parts.append(f"<system>\n{request.system_prompt}\n</system>")

        # Automatically inject Output-Policy
        parts.append(f"<policy>\n{OUTPUT_POLICY}\n</policy>")

        # Domain prompt (optional)
        if request.domain_prompt:
            parts.append(f"<domain>\n{request.domain_prompt}\n</domain>")

        # Few-shot examples (optional)
        if request.fewshots:
            examples = "\n".join(
                f"<example>\nUser: {fs.user}\nAssistant: {fs.assistant}\n</example>"
                for fs in request.fewshots
            )
            parts.append(examples)

        # User request
        parts.append(f"<user>\n{request.prompt}\n</user>")

        # Feedback (optional)
        if request.feedback:
            parts.append(f"<feedback>\n{request.feedback}\n</feedback>")

        return "\n\n".join(parts)

    @abstractmethod
    async def _call_provider(self, request: LLMRequest, final_prompt: str) -> str:
        raise NotImplementedError
