"""OpenAI LLM provider implementation."""

from __future__ import annotations

from typing import Any, Dict, List

from openai import OpenAI

from src.core.models import LLMRequest, LLMResponse

from src.llm.provider_base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY env var.
            **kwargs: Additional configuration (e.g., base_url, timeout).
        """
        super().__init__(api_key, **kwargs)
        self.client = OpenAI(api_key=api_key, **kwargs)

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from OpenAI.

        Args:
            request: The LLM request containing prompt and parameters.

        Returns:
            LLMResponse with the generated content and metadata.

        Raises:
            Exception: If the OpenAI API call fails.
        """
        # Convert single prompt to messages format
        messages = [{"role": "user", "content": request.prompt}]

        return self.generate_from_messages(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    def generate_from_messages(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from OpenAI using messages format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: OpenAI model name (e.g., 'gpt-4', 'gpt-3.5-turbo').
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional OpenAI parameters (e.g., top_p, presence_penalty).

        Returns:
            LLMResponse with the generated content and metadata.

        Raises:
            Exception: If the OpenAI API call fails.
        """
        start_time = self._measure_latency()

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        end_time = self._measure_latency()
        latency_ms = end_time - start_time

        # Extract response data
        choice = response.choices[0]
        content = choice.message.content or ""
        finish_reason = choice.finish_reason or "unknown"

        # Calculate tokens used
        tokens_used = response.usage.total_tokens if response.usage else 0

        # Create standardized response
        return self._create_response(
            provider="openai",
            model=model,
            content=content,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            raw=response.model_dump(),
        )
