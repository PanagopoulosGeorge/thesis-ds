"""Unit tests for MSAPromptBuilder.

Tests MSA-specific domain knowledge and few-shot examples.
"""
import pytest

from src.interfaces.models import LLMRequest, FewShotExample
from src.interfaces.prompts import PromptBuilder
from src.prompts.msa_builder import MSAPromptBuilder


class TestMSAPromptBuilderInterface:
    """Tests that MSAPromptBuilder correctly implements PromptBuilder."""
    
    def test_is_prompt_builder_subclass(self):
        """MSAPromptBuilder must be a PromptBuilder."""
        assert issubclass(MSAPromptBuilder, PromptBuilder)
    
    def test_domain_name_is_msa(self):
        """Domain name must be 'msa'."""
        builder = MSAPromptBuilder()
        assert builder.domain_name == "msa"
    
    def test_instantiation(self):
        """Builder can be instantiated without arguments."""
        builder = MSAPromptBuilder()
        assert builder is not None


class TestMSASystemPrompt:
    """Tests for MSA system prompt."""
    
    def test_system_prompt_not_empty(self):
        """Must return non-empty system prompt."""
        builder = MSAPromptBuilder()
        prompt = builder.get_system_prompt()
        
        assert len(prompt) > 0
    
    def test_system_prompt_contains_rtec_base(self):
        """System prompt must include base RTEC predicates."""
        builder = MSAPromptBuilder()
        prompt = builder.get_system_prompt()
        
        # Base RTEC predicates
        assert "happensAt" in prompt
        assert "holdsAt" in prompt
        assert "holdsFor" in prompt
    
    def test_system_prompt_contains_msa_events(self):
        """System prompt must include MSA events."""
        builder = MSAPromptBuilder()
        prompt = builder.get_system_prompt()
        
        # Key MSA events from msa_domain.py
        assert "change_in_speed_start" in prompt or "gap_start" in prompt
        assert "entersArea" in prompt or "leavesArea" in prompt
    
    def test_system_prompt_contains_background_knowledge(self):
        """System prompt must include MSA background knowledge."""
        builder = MSAPromptBuilder()
        prompt = builder.get_system_prompt()
        
        # MSA background knowledge predicates
        assert "thresholds" in prompt


class TestMSAFewShotExamples:
    """Tests for MSA few-shot examples."""
    
    def test_fewshot_examples_not_empty(self):
        """Must return few-shot examples."""
        builder = MSAPromptBuilder()
        examples = builder.get_fewshot_examples()
        
        assert len(examples) > 0
    
    def test_fewshot_examples_are_fewshot_example_type(self):
        """All examples must be FewShotExample instances."""
        builder = MSAPromptBuilder()
        examples = builder.get_fewshot_examples()
        
        for ex in examples:
            assert isinstance(ex, FewShotExample)
    
    def test_fewshot_examples_have_content(self):
        """Each example must have non-empty user and assistant fields."""
        builder = MSAPromptBuilder()
        examples = builder.get_fewshot_examples()
        
        for i, ex in enumerate(examples):
            assert ex.user.strip(), f"Example {i} has empty user field"
            assert ex.assistant.strip(), f"Example {i} has empty assistant field"
    
    def test_fewshot_includes_simple_fluent_examples(self):
        """Must include simple fluent examples (initiatedAt/terminatedAt)."""
        builder = MSAPromptBuilder()
        examples = builder.get_fewshot_examples()
        combined_outputs = " ".join(ex.assistant for ex in examples)
        
        assert "initiatedAt" in combined_outputs or "terminatedAt" in combined_outputs
    
    def test_fewshot_includes_static_fluent_examples(self):
        """Must include statically determined fluent examples (holdsFor)."""
        builder = MSAPromptBuilder()
        examples = builder.get_fewshot_examples()
        combined_outputs = " ".join(ex.assistant for ex in examples)
        
        assert "holdsFor" in combined_outputs


class TestMSABuildPrompt:
    """Integration tests for complete prompt building."""
    
    def test_build_prompt_returns_llm_request(self, sample_activity_description):
        """build_prompt returns valid LLMRequest."""
        builder = MSAPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        assert isinstance(result, LLMRequest)
    
    def test_build_prompt_system_contains_msa_content(self, sample_activity_description):
        """System prompt includes MSA-specific content."""
        builder = MSAPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        # Should contain MSA introduction
        assert "maritime" in result.system_prompt.lower() or "MSA" in result.system_prompt
    
    def test_build_prompt_with_prerequisites(
        self, sample_activity_description, sample_prerequisites
    ):
        """Prerequisites are correctly included in fewshots."""
        builder = MSAPromptBuilder()
        result = builder.build_prompt(sample_activity_description, prerequisites=sample_prerequisites)
        
        # Prerequisites should be in the fewshots
        prerequisite_users = [p.user for p in sample_prerequisites]
        result_users = [f.user for f in result.fewshots]
        
        for prereq_user in prerequisite_users:
            assert prereq_user in result_users

