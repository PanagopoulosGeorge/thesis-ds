"""Prompt building module for RTEC rule generation.

Usage:
    from src.prompts import get_prompt_builder
    
    builder = get_prompt_builder("msa")
    request = builder.build_prompt(activity_description, prerequisites)
"""
from src.interfaces.prompts import PromptBuilder
from src.interfaces.exceptions import PromptBuilderNotFoundError
from src.prompts.factory import (
    get_prompt_builder,
    register_prompt_builder,
    list_available_domains,
)
from src.prompts.msa_builder import MSAPromptBuilder
from src.prompts.har_builder import HARPromptBuilder

__all__ = [
    # Base class
    "PromptBuilder",
    # Factory functions
    "get_prompt_builder",
    "register_prompt_builder", 
    "list_available_domains",
    # Exceptions
    "PromptBuilderNotFoundError",
    # Domain implementations
    "MSAPromptBuilder",
    "HARPromptBuilder",
]

