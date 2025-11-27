"""Factory for creating LLM provider instances."""

from __future__ import annotations

from typing import Any

from src.llm.provider_base import BaseLLMProvider

from src.llm.provider_openai import OpenAIProvider


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers = {
        "openai": OpenAIProvider,
    }

    @classmethod

    def create(
        cls,
        provider_name: str,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> BaseLLMProvider:
        """Create an LLM provider instance.

        Args:
            provider_name: Name of the provider ('openai', etc.).
            api_key: API key for the provider.
            **kwargs: Additional provider-specific configuration.

        Returns:
            Instance of the requested provider.

        Raises:
            ValueError: If the provider name is not supported.
        """
        provider_name_lower = provider_name.lower()

        if provider_name_lower not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider: '{provider_name}'. "
                f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name_lower]
        return provider_class(api_key=api_key, **kwargs)

    @classmethod

    def register_provider(
        cls,
        name: str,
        provider_class: type[BaseLLMProvider],
    ) -> None:
        """Register a new provider class.

        Args:
            name: Name to register the provider under.
            provider_class: Provider class to register.
        """
        cls._providers[name.lower()] = provider_class

    @classmethod

    def list_providers(cls) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names.
        """
        return list(cls._providers.keys())
