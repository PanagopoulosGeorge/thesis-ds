"""Tests for rule extraction from LLM responses."""

import pytest
from unittest.mock import Mock

from src.loop.orchestrator import LoopOrchestrator
from src.core.models import LLMResponse, LoopConfig


def create_response(content: str, tokens: int = 100) -> LLMResponse:
    """Helper to create LLMResponse objects."""
    return LLMResponse(
        request_id="test",
        provider="openai",
        model="gpt-4",
        content=content,
        tokens_used=tokens,
        latency_ms=float(tokens),
        finish_reason="stop",
        raw={}
    )


class TestRuleExtraction:
    """Test the _extract_rules_from_response method."""

    @pytest.fixture
    def orchestrator(self):
        """Create a minimal orchestrator for testing."""
        config = LoopConfig(
            provider="openai",
            objective="test",
            max_iterations=5,
            convergence_threshold=0.9,
            batch_size=1,
            retry_limit=3
        )
        
        # Create mock dependencies
        mock_builder = Mock()
        mock_provider = Mock()
        mock_simlp = Mock()
        
        return LoopOrchestrator(
            prompt_builder=mock_builder,
            llm_provider=mock_provider,
            simlp_client=mock_simlp,
            config=config
        )
    
    def test_extract_single_code_block(self, orchestrator):
        """Test extraction of a single code block."""
        content = """
Here is the rule:

```prolog
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).
```

That's the rule.
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        assert "initiatedAt(gap(Vessel)=nearPorts, T)" in rules
        assert "happensAt(gap_start(Vessel), T)" in rules
        assert "holdsAt(withinArea(Vessel, nearPorts)=true, T)" in rules
        # Should not contain markdown or explanatory text
        assert "Here is the rule" not in rules
        assert "That's the rule" not in rules
        assert "```" not in rules
    
    def test_extract_multiple_code_blocks(self, orchestrator):
        """Test extraction and concatenation of multiple code blocks."""
        content = '''The activity "gap" starts when a vessel stops sending signals.

```prolog
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).
```

The activity "gap" may also start far from all ports.

```prolog
initiatedAt(gap(Vessel)=farFromPorts, T) :-
    happensAt(gap_start(Vessel), T),
    not holdsAt(withinArea(Vessel, nearPorts)=true, T).
```

The activity "gap" ends when a vessel resumes sending signals.

```prolog
terminatedAt(gap(Vessel)=_Status, T) :-
    happensAt(gap_end(Vessel), T).
```
'''
        response = create_response(content, 200)
        rules = orchestrator._extract_rules_from_response(response)
        
        # Should contain all three rules
        assert "initiatedAt(gap(Vessel)=nearPorts, T)" in rules
        assert "initiatedAt(gap(Vessel)=farFromPorts, T)" in rules
        assert "terminatedAt(gap(Vessel)=_Status, T)" in rules
        
        # Should be concatenated with double newlines
        assert rules.count("initiatedAt") == 2
        assert rules.count("terminatedAt") == 1
        
        # Should not contain explanatory text
        assert "activity starts when" not in rules
        assert "may also start" not in rules
        assert "```" not in rules
    
    def test_extract_code_block_with_pl_marker(self, orchestrator):
        """Test extraction with 'pl' language marker."""
        content = """
```pl
initiatedAt(active(Vessel)=true, T) :-
    happensAt(start_move(Vessel), T).
```
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        assert "initiatedAt(active(Vessel)=true, T)" in rules
        assert "```" not in rules
    
    def test_extract_code_block_without_language_marker(self, orchestrator):
        """Test extraction from unmarked code block."""
        content = """
```
initiatedAt(gap(Vessel)=true, T) :-
    happensAt(gap_start(Vessel), T).
```
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        assert "initiatedAt(gap(Vessel)=true, T)" in rules
        assert "```" not in rules
    
    def test_fallback_to_pattern_matching(self, orchestrator):
        """Test fallback to pattern matching when no code blocks."""
        content = """
Here are the rules:

initiatedAt(gap(Vessel)=true, T) :-
    happensAt(gap_start(Vessel), T).

terminatedAt(gap(Vessel)=_Status, T) :-
    happensAt(gap_end(Vessel), T).
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        assert "initiatedAt(gap(Vessel)=true, T)" in rules
        assert "terminatedAt(gap(Vessel)=_Status, T)" in rules
    
    def test_extract_complex_multiline_rules(self, orchestrator):
        """Test extraction of complex multi-line rules."""
        content = """
```prolog
initiatedAt(withinArea(Vessel, Area_ID)=true, T) :-
    happensAt(entersArea(Vessel, Area_ID), T),
    holdsAt(someOtherCondition(Vessel)=true, T),
    not holdsAt(blocked(Vessel)=true, T),
    anotherCondition(Vessel, Area_ID).
```
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        assert "initiatedAt(withinArea(Vessel, Area_ID)=true, T)" in rules
        assert "happensAt(entersArea(Vessel, Area_ID), T)" in rules
        assert "holdsAt(someOtherCondition(Vessel)=true, T)" in rules
        assert "not holdsAt(blocked(Vessel)=true, T)" in rules
        assert "anotherCondition(Vessel, Area_ID)" in rules
    
    def test_extract_preserves_formatting(self, orchestrator):
        """Test that extraction preserves indentation and formatting."""
        content = """
```prolog
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).
```
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        # Check that indentation is preserved
        lines = rules.split('\n')
        assert any(line.startswith('    ') for line in lines)
    
    def test_empty_response_fallback(self, orchestrator):
        """Test handling of response with no identifiable rules."""
        content = "This is just explanatory text with no rules."
        response = create_response(content, 10)
        rules = orchestrator._extract_rules_from_response(response)
        
        # Should return the full content as fallback
        assert rules == content
    
    def test_multiple_code_blocks_concatenated(self, orchestrator):
        """Test that multiple code blocks are separated properly."""
        content = """
```prolog
rule1(X) :- condition1(X).
```

Some text.

```prolog
rule2(Y) :- condition2(Y).
```
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        # Should have both rules
        assert "rule1(X)" in rules
        assert "rule2(Y)" in rules
        
        # Should be separated by double newline
        assert "\n\n" in rules
        
        # Should not contain the explanatory text
        assert "Some text" not in rules
    
    def test_code_block_with_comments(self, orchestrator):
        """Test extraction of code blocks containing Prolog comments."""
        content = """
```prolog
% This is a comment
initiatedAt(gap(Vessel)=true, T) :-
    % Another comment
    happensAt(gap_start(Vessel), T).

%% Header comment
terminatedAt(gap(Vessel)=_Status, T) :-
    happensAt(gap_end(Vessel), T).
```
"""
        response = create_response(content)
        rules = orchestrator._extract_rules_from_response(response)
        
        # Comments should be preserved
        assert "% This is a comment" in rules
        assert "% Another comment" in rules
        assert "%% Header comment" in rules
        assert "initiatedAt" in rules
        assert "terminatedAt" in rules
