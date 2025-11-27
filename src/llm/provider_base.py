"""Base class for LLM provider implementations."""

from __future__ import annotations

import time
import uuid

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.core.models import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize the provider.

        Args:
            api_key: API key for the provider.
            **kwargs: Additional provider-specific configuration.
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            request: The LLM request containing prompt and parameters.

        Returns:
            LLMResponse with the generated content and metadata.

        Raises:
            Exception: If the API call fails.
        """
        pass

    @abstractmethod

    def generate_from_messages(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model name to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with the generated content and metadata.

        Raises:
            Exception: If the API call fails.
        """
        pass

    def _create_response(
        self,
        provider: str,
        model: str,
        content: str,
        tokens_used: int,
        latency_ms: float,
        finish_reason: str,
        raw: Dict[str, Any],
    ) -> LLMResponse:
        """Create a standardized LLMResponse.

        Args:
            provider: Provider name.
            model: Model name.
            content: Generated content.
            tokens_used: Number of tokens used.
            latency_ms: Latency in milliseconds.
            finish_reason: Reason for completion.
            raw: Raw API response.

        Returns:
            LLMResponse object.
        """
        return LLMResponse(
            request_id=str(uuid.uuid4()),
            provider=provider,
            model=model,
            content=content,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            raw=raw,
        )

    @staticmethod

    def _measure_latency() -> float:
        """Get current time in milliseconds for latency measurement.

        Returns:
            Current time in milliseconds.
        """
        return time.time() * 1000
