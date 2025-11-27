"""Tests for LLM provider implementations."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.models import LLMRequest, LLMResponse

from src.llm.factory import ProviderFactory

from src.llm.provider_openai import OpenAIProvider


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_openai_provider_initialization(self):
        """Test OpenAI provider can be initialized."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.client is not None

    @patch("src.llm.provider_openai.OpenAI")
    def test_generate_from_messages(self, mock_openai_class):
        """Test generate_from_messages sends correct request to OpenAI."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock response
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated RTEC rules"
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {"id": "test-response"}

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider and call
        provider = OpenAIProvider(api_key="test-key")
        messages = [
            {"role": "system", "content": "You are an RTEC expert."},
            {"role": "user", "content": "Generate rules for gap activity."},
        ]

        response = provider.generate_from_messages(
            messages=messages,
            model="gpt-4",
            temperature=0.5,
            max_tokens=2048,
        )

        # Assert OpenAI client was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs

        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["messages"] == messages
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 2048

        # Assert response is correct
        assert isinstance(response, LLMResponse)
        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert response.content == "Generated RTEC rules"
        assert response.tokens_used == 150
        assert response.finish_reason == "stop"
        assert response.latency_ms >= 0
        assert response.raw == {"id": "test-response"}

    @patch("src.llm.provider_openai.OpenAI")
    def test_generate_converts_prompt_to_messages(self, mock_openai_class):
        """Test generate method converts single prompt to messages format."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock response
        mock_choice = MagicMock()
        mock_choice.message.content = "Response"
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 100

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider and call
        provider = OpenAIProvider(api_key="test-key")
        request = LLMRequest(
            provider="openai",
            model="gpt-3.5-turbo",
            prompt="Test prompt",
            temperature=0.7,
            max_tokens=1024,
        )

        response = provider.generate(request)

        # Assert the prompt was converted to messages format
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        expected_messages = [{"role": "user", "content": "Test prompt"}]
        assert call_kwargs["messages"] == expected_messages
        assert call_kwargs["model"] == "gpt-3.5-turbo"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 1024

        # Assert response is valid
        assert isinstance(response, LLMResponse)
        assert response.content == "Response"

    @patch("src.llm.provider_openai.OpenAI")
    def test_generate_handles_none_content(self, mock_openai_class):
        """Test provider handles None content gracefully."""
        # Setup mock with None content
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_choice.finish_reason = "length"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 50

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider and call
        provider = OpenAIProvider(api_key="test-key")
        response = provider.generate_from_messages(
            messages=[{"role": "user", "content": "Test"}],
            model="gpt-4",
        )

        # Assert empty string is returned for None content
        assert response.content == ""
        assert response.finish_reason == "length"


class TestProviderFactory:
    """Tests for ProviderFactory."""

    def test_create_openai_provider(self):
        """Test factory can create OpenAI provider."""
        provider = ProviderFactory.create("openai", api_key="test-key")

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"

    def test_create_openai_case_insensitive(self):
        """Test factory is case-insensitive."""
        provider1 = ProviderFactory.create("OpenAI", api_key="key1")
        provider2 = ProviderFactory.create("OPENAI", api_key="key2")
        provider3 = ProviderFactory.create("openai", api_key="key3")

        assert all(
            isinstance(p, OpenAIProvider)
            for p in [provider1, provider2, provider3]
        )

    def test_create_unknown_provider_raises_error(self):
        """Test factory raises error for unknown provider."""
        with pytest.raises(ValueError) as exc_info:
            ProviderFactory.create("unknown-provider", api_key="key")

        assert "Unknown provider: 'unknown-provider'" in str(exc_info.value)
        assert "Available providers:" in str(exc_info.value)
        assert "openai" in str(exc_info.value)

    def test_list_providers(self):
        """Test listing all available providers."""
        providers = ProviderFactory.list_providers()

        assert isinstance(providers, list)
        assert "openai" in providers
        assert len(providers) >= 1

    def test_register_custom_provider(self):
        """Test registering a custom provider."""
        # Create a mock provider class

        class CustomProvider(OpenAIProvider):
            pass

        # Register it
        ProviderFactory.register_provider("custom", CustomProvider)

        # Verify it's registered
        assert "custom" in ProviderFactory.list_providers()

        # Verify it can be created
        provider = ProviderFactory.create("custom", api_key="test")
        assert isinstance(provider, CustomProvider)

        # Cleanup
        del ProviderFactory._providers["custom"]

    def test_factory_passes_kwargs_to_provider(self):
        """Test factory passes additional kwargs to provider."""
        provider = ProviderFactory.create(
            "openai",
            api_key="test-key",
            timeout=30,
            max_retries=3,
        )

        assert provider.api_key == "test-key"
        assert "timeout" in provider.config
        assert "max_retries" in provider.config
        assert provider.config["timeout"] == 30
        assert provider.config["max_retries"] == 3


class TestLLMProviderIntegration:
    """Integration tests for LLM providers."""

    @patch("src.llm.provider_openai.OpenAI")
    def test_end_to_end_openai_flow(self, mock_openai_class):
        """Test complete flow: factory -> provider -> response."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "initiatedAt(gap(V)=nearPorts, T) :- ..."
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 250

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {"id": "chatcmpl-123"}

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider via factory
        provider = ProviderFactory.create("openai", api_key="sk-test")

        # Create request
        request = LLMRequest(
            provider="openai",
            model="gpt-4",
            prompt="Generate RTEC rules for gap activity",
            temperature=0.3,
            max_tokens=2000,
        )

        # Generate response
        response = provider.generate(request)

        # Verify response
        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert "initiatedAt" in response.content
        assert response.tokens_used == 250
        assert response.finish_reason == "stop"
        assert response.request_id is not None
        assert len(response.request_id) > 0

    @patch("src.llm.provider_openai.OpenAI")
    def test_multiple_messages_conversation(self, mock_openai_class):
        """Test provider handles multi-turn conversation."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "Improved rules with feedback"
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 300

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model_dump.return_value = {}

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider
        provider = ProviderFactory.create("openai", api_key="test")

        # Multi-turn conversation
        messages = [
            {"role": "system", "content": "You are an RTEC expert."},
            {"role": "user", "content": "Generate rules for gap."},
            {"role": "assistant", "content": "Here are the rules: ..."},
            {"role": "user", "content": "Add the farFromPorts case."},
        ]

        response = provider.generate_from_messages(
            messages=messages,
            model="gpt-4",
        )

        # Verify all messages were sent
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == messages
        assert len(call_kwargs["messages"]) == 4

        # Verify response
        assert response.content == "Improved rules with feedback"
        assert response.tokens_used == 300
