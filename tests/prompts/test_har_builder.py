"""Unit tests for HARPromptBuilder.

Tests HAR-specific domain knowledge and few-shot examples.
"""
import pytest

from src.interfaces.models import LLMRequest, FewShotExample
from src.interfaces.prompts import PromptBuilder
from src.prompts.har_builder import HARPromptBuilder


class TestHARPromptBuilderInterface:
    """Tests that HARPromptBuilder correctly implements PromptBuilder."""
    
    def test_is_prompt_builder_subclass(self):
        """HARPromptBuilder must be a PromptBuilder."""
        assert issubclass(HARPromptBuilder, PromptBuilder)
    
    def test_domain_name_is_har(self):
        """Domain name must be 'har'."""
        builder = HARPromptBuilder()
        assert builder.domain_name == "har"
    
    def test_instantiation(self):
        """Builder can be instantiated without arguments."""
        builder = HARPromptBuilder()
        assert builder is not None


class TestHARSystemPrompt:
    """Tests for HAR system prompt."""
    
    def test_system_prompt_not_empty(self):
        """Must return non-empty system prompt."""
        builder = HARPromptBuilder()
        prompt = builder.get_system_prompt()
        
        assert len(prompt) > 0
    
    def test_system_prompt_contains_rtec_base(self):
        """System prompt must include base RTEC predicates."""
        builder = HARPromptBuilder()
        prompt = builder.get_system_prompt()
        
        # Base RTEC predicates
        assert "happensAt" in prompt
        assert "holdsAt" in prompt
        assert "holdsFor" in prompt
    
    def test_system_prompt_contains_har_events(self):
        """System prompt must include HAR events."""
        builder = HARPromptBuilder()
        prompt = builder.get_system_prompt()
        
        # Key HAR events from har_domain.py
        assert "appear" in prompt
        assert "disappear" in prompt
    
    def test_system_prompt_contains_har_fluents(self):
        """System prompt must include HAR input fluents."""
        builder = HARPromptBuilder()
        prompt = builder.get_system_prompt()
        
        # HAR input fluents
        assert "walking" in prompt or "running" in prompt
        assert "close" in prompt


class TestHARFewShotExamples:
    """Tests for HAR few-shot examples."""
    
    def test_fewshot_examples_not_empty(self):
        """Must return few-shot examples."""
        builder = HARPromptBuilder()
        examples = builder.get_fewshot_examples()
        
        assert len(examples) > 0
    
    def test_fewshot_examples_are_fewshot_example_type(self):
        """All examples must be FewShotExample instances."""
        builder = HARPromptBuilder()
        examples = builder.get_fewshot_examples()
        
        for ex in examples:
            assert isinstance(ex, FewShotExample)
    
    def test_fewshot_examples_have_content(self):
        """Each example must have non-empty user and assistant fields."""
        builder = HARPromptBuilder()
        examples = builder.get_fewshot_examples()
        
        for i, ex in enumerate(examples):
            assert ex.user.strip(), f"Example {i} has empty user field"
            assert ex.assistant.strip(), f"Example {i} has empty assistant field"


class TestHARBuildPrompt:
    """Integration tests for complete prompt building."""
    
    def test_build_prompt_returns_llm_request(self, sample_activity_description):
        """build_prompt returns valid LLMRequest."""
        builder = HARPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        assert isinstance(result, LLMRequest)
    
    def test_build_prompt_system_contains_har_content(self, sample_activity_description):
        """System prompt includes HAR-specific content."""
        builder = HARPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        # Should contain HAR introduction
        assert "human activity" in result.system_prompt.lower() or "HAR" in result.system_prompt

