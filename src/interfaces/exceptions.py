class LLMProviderNotFoundError(Exception):
    """Raised when an LLM provider is not found."""
    pass


class PromptBuilderNotFoundError(Exception):
    """Raised when a requested prompt builder is not found in the registry."""
    pass

