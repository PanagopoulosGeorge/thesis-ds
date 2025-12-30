"""RTEC-LLM: LLM-Driven Generation & Evaluation of RTEC Event Descriptions.

This package provides a feedback loop system for iterative RTEC rule generation.
"""

# Core orchestration
from src.core import (
    FinalResult,
    IterationResult,
    LoopOrchestrator,
    LoopStatistics,
    OrchestratorConfig,
)

# Memory system
from src.memory import RuleMemory, RuleMemoryEntry

# LLM providers
from src.llm import OpenAILLMProvider
from src.llm.factory import get_provider, register_provider

# Prompt builders
from src.prompts.factory import get_prompt_builder, register_prompt_builder

# Feedback/evaluation
from src.feedback.client import FeedbackClient, FeedbackResult

__all__ = [
    # Core
    "LoopOrchestrator",
    "OrchestratorConfig",
    "FinalResult",
    "IterationResult",
    "LoopStatistics",
    # Memory
    "RuleMemory",
    "RuleMemoryEntry",
    # LLM
    "OpenAILLMProvider",
    "get_provider",
    "register_provider",
    # Prompts
    "get_prompt_builder",
    "register_prompt_builder",
    # Feedback
    "FeedbackClient",
    "FeedbackResult",
]

