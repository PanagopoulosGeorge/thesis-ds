"""Factory for creating domain-specific prompt builders.

Follows the Factory Pattern with a registry for extensibility.
New domains can be added by:
1. Creating a new PromptBuilder subclass
2. Registering it with register_prompt_builder()
"""
from typing import Dict, Type

from src.interfaces.prompts import PromptBuilder
from src.prompts.msa_builder import MSAPromptBuilder
from src.prompts.har_builder import HARPromptBuilder
from src.interfaces.exceptions import PromptBuilderNotFoundError

# Registry mapping domain names to builder classes
_BUILDER_REGISTRY: Dict[str, Type[PromptBuilder]] = {}

def register_prompt_builder(domain: str, builder_class: Type[PromptBuilder]) -> None:
    """Register a prompt builder for a domain.
    
    Args:
        domain: Domain name (e.g., 'msa', 'har')
        builder_class: PromptBuilder subclass to register
    """
    _BUILDER_REGISTRY[domain.lower()] = builder_class

def get_prompt_builder(domain: str) -> PromptBuilder:
    """Get a prompt builder instance for the specified domain.
    
    Args:
        domain: Domain name (e.g., 'msa', 'har')
        
    Returns:
        Instantiated PromptBuilder for the domain
        
    Raises:
        PromptBuilderNotFoundError: If no builder is registered for the domain
    """
    builder_class = _BUILDER_REGISTRY.get(domain.lower())
    if not builder_class:
        available = ", ".join(_BUILDER_REGISTRY.keys()) or "none"
        raise PromptBuilderNotFoundError(
            f"No prompt builder found for domain '{domain}'. "
            f"Available domains: {available}"
        )
    return builder_class()

def list_available_domains() -> list[str]:
    """List all registered domain names."""
    return list(_BUILDER_REGISTRY.keys())


# ============================================================
# Register built-in domain builders
# ============================================================
register_prompt_builder("msa", MSAPromptBuilder)
register_prompt_builder("har", HARPromptBuilder)

