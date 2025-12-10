"""Contract tests for PromptBuilder base class.

These tests verify that ANY PromptBuilder implementation follows the contract.
Uses a concrete test double to test base class behavior.
"""
import pytest
from typing import List

from src.interfaces.models import LLMRequest, FewShotExample
from src.interfaces.prompts import PromptBuilder


# ============================================================
# Test Double: Minimal concrete implementation for testing base behavior
# ============================================================
class StubPromptBuilder(PromptBuilder):
    """Minimal implementation for testing base class logic."""
    
    def __init__(self, system_prompt: str = None, examples: List[FewShotExample] = None):
        self._system_prompt = system_prompt or "Base RTEC: happensAt, holdsAt, holdsFor. Domain: stub content."
        self._examples = examples or [
            FewShotExample(user="Example input", assistant="Example output")
        ]
    
    @property
    def domain_name(self) -> str:
        return "stub"
    
    def get_system_prompt(self) -> str:
        return self._system_prompt
    
    def get_fewshot_examples(self) -> List[FewShotExample]:
        return self._examples


# ===================================================================
# Contract Tests: What any PromptBuilder implementation must satisfy
# ===================================================================
class TestPromptBuilderContract:
    """Tests for the PromptBuilder contract (base class behavior)."""
    
    def test_build_prompt_returns_llm_request(self, sample_activity_description):
        """build_prompt() must return an LLMRequest."""
        builder = StubPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        assert isinstance(result, LLMRequest)
    
    def test_build_prompt_sets_user_prompt(self, sample_activity_description):
        """The activity description becomes the user prompt."""
        builder = StubPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        assert result.prompt == sample_activity_description
    
    def test_build_prompt_includes_system_prompt(self, sample_activity_description):
        """System prompt must be non-empty."""
        builder = StubPromptBuilder()
        result = builder.build_prompt(sample_activity_description)
        
        assert result.system_prompt is not None
        assert len(result.system_prompt) > 0
    
    
    def test_fewshots_include_domain_examples(self, sample_activity_description):
        """Few-shots must include domain examples."""
        examples = [
            FewShotExample(user="Input 1", assistant="Output 1"),
            FewShotExample(user="Input 2", assistant="Output 2"),
        ]
        builder = StubPromptBuilder(examples=examples)
        result = builder.build_prompt(sample_activity_description)
        
        assert len(result.fewshots) == len(examples)
        # Domain examples should be at the beginning
        assert result.fewshots[0].user == "Input 1"
        assert result.fewshots[1].user == "Input 2"


class TestPrerequisiteInjection:
    """Tests for prerequisite (learned fluent) injection."""
    
    def test_prerequisites_none_by_default(self, sample_activity_description):
        """When no prerequisites, only domain examples in fewshots."""
        examples = [FewShotExample(user="Example", assistant="Output")]
        builder = StubPromptBuilder(examples=examples)
        
        result = builder.build_prompt(sample_activity_description, prerequisites=None)
        
        assert len(result.fewshots) == 1
    
    def test_prerequisites_appended_to_fewshots(
        self, sample_activity_description, sample_prerequisites
    ):
        """Prerequisites are appended after domain examples."""
        examples = [FewShotExample(user="Domain example", assistant="Domain output")]
        builder = StubPromptBuilder(examples=examples)
        
        result = builder.build_prompt(sample_activity_description, prerequisites=sample_prerequisites)
        
        # Total = domain examples + prerequisites
        assert len(result.fewshots) == 1 + len(sample_prerequisites)
    
    def test_prerequisites_order_after_domain_examples(
        self, sample_activity_description, sample_prerequisites
    ):
        """Domain examples come first, then prerequisites."""
        examples = [FewShotExample(user="DOMAIN", assistant="domain output")]
        builder = StubPromptBuilder(examples=examples)
        
        result = builder.build_prompt(sample_activity_description, prerequisites=sample_prerequisites)
        
        # First should be domain example
        assert result.fewshots[0].user == "DOMAIN"
        # Rest should be prerequisites
        assert result.fewshots[1].user == sample_prerequisites[0].user
        assert result.fewshots[2].user == sample_prerequisites[1].user
    
    def test_empty_prerequisites_list_same_as_none(self, sample_activity_description):
        """Empty list behaves same as None."""
        builder = StubPromptBuilder()
        
        result_none = builder.build_prompt(sample_activity_description, prerequisites=None)
        result_empty = builder.build_prompt(sample_activity_description, prerequisites=[])
        
        assert len(result_none.fewshots) == len(result_empty.fewshots)

