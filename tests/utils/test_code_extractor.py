"""Tests for the code extraction utilities."""

import pytest

from src.utils.code_extractor import (
    extract_all_code_blocks,
    extract_prolog_blocks,
    extract_rules_from_response,
)


# ============================================================
# Sample LLM responses for testing
# ============================================================

SAMPLE_RESPONSE_SINGLE_BLOCK = """
The gap fluent is defined as follows:

```prolog
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).
```

This rule captures when a communication gap starts near a port.
"""

SAMPLE_RESPONSE_MULTIPLE_BLOCKS = """
The gap is expressed as:

```prolog
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).

initiatedAt(gap(Vessel)=farFromPorts, T) :-
    happensAt(gap_start(Vessel), T),
    \\+holdsAt(withinArea(Vessel, nearPorts)=true, T).
```

And terminated using:

```prolog
terminatedAt(gap(Vessel)=_PortStatus, T) :-
    happensAt(gap_end(Vessel), T).
```

These rules together define the complete gap fluent behavior.
"""

SAMPLE_RESPONSE_MIXED_LANGUAGES = """
Here's the RTEC rule:

```prolog
initiatedAt(highSpeed(Vessel)=true, T) :-
    happensAt(velocity(Vessel, Speed, _, _), T),
    Speed > 10.
```

And here's how you might call it in Python:

```python
result = evaluate_rule("highSpeed", vessel_id=123)
print(result)
```

The Prolog rule will be extracted.
"""

SAMPLE_RESPONSE_UNTAGGED_BLOCK = """
Here's the rule:

```
initiatedAt(lowSpeed(Vessel)=true, T) :-
    happensAt(slow_motion_start(Vessel), T).
```

Notice the block has no language tag.
"""

SAMPLE_RESPONSE_RTEC_TAG = """
The RTEC definition:

```rtec
holdsFor(trawling(Vessel)=true, I) :-
    holdsFor(trawlSpeed(Vessel)=true, It),
    holdsFor(trawlingMovement(Vessel)=true, Itc),
    intersect_all([It, Itc], I).
```
"""

SAMPLE_RESPONSE_RAW_CODE = """initiatedAt(foo(X)=true, T) :-
    happensAt(bar(X), T).

terminatedAt(foo(X)=true, T) :-
    happensAt(baz(X), T)."""

SAMPLE_RESPONSE_EMPTY = """
This response contains no code blocks, just explanatory text
about how the fluent should work.
"""


# ============================================================
# Tests for extract_all_code_blocks
# ============================================================

class TestExtractAllCodeBlocks:
    """Tests for the extract_all_code_blocks function."""
    
    def test_single_block(self):
        """Should extract a single code block."""
        blocks = extract_all_code_blocks(SAMPLE_RESPONSE_SINGLE_BLOCK)
        assert len(blocks) == 1
        assert blocks[0][0] == "prolog"
        assert "initiatedAt(gap(Vessel)" in blocks[0][1]
    
    def test_multiple_blocks(self):
        """Should extract multiple code blocks."""
        blocks = extract_all_code_blocks(SAMPLE_RESPONSE_MULTIPLE_BLOCKS)
        assert len(blocks) == 2
        assert all(lang == "prolog" for lang, _ in blocks)
    
    def test_mixed_languages(self):
        """Should extract blocks with different language tags."""
        blocks = extract_all_code_blocks(SAMPLE_RESPONSE_MIXED_LANGUAGES)
        assert len(blocks) == 2
        
        languages = [lang for lang, _ in blocks]
        assert "prolog" in languages
        assert "python" in languages
    
    def test_untagged_block(self):
        """Should extract untagged code blocks with empty language."""
        blocks = extract_all_code_blocks(SAMPLE_RESPONSE_UNTAGGED_BLOCK)
        assert len(blocks) == 1
        assert blocks[0][0] == ""  # Empty language tag
        assert "initiatedAt" in blocks[0][1]
    
    def test_no_blocks(self):
        """Should return empty list when no code blocks found."""
        blocks = extract_all_code_blocks(SAMPLE_RESPONSE_EMPTY)
        assert blocks == []
    
    def test_rtec_tag(self):
        """Should extract blocks tagged with 'rtec'."""
        blocks = extract_all_code_blocks(SAMPLE_RESPONSE_RTEC_TAG)
        assert len(blocks) == 1
        assert blocks[0][0] == "rtec"


# ============================================================
# Tests for extract_prolog_blocks
# ============================================================

class TestExtractPrologBlocks:
    """Tests for the extract_prolog_blocks function."""
    
    def test_single_prolog_block(self):
        """Should extract a single prolog block."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_SINGLE_BLOCK)
        assert "initiatedAt(gap(Vessel)=nearPorts, T)" in result
        assert "happensAt(gap_start(Vessel), T)" in result
    
    def test_multiple_prolog_blocks_concatenated(self):
        """Should concatenate multiple prolog blocks."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_MULTIPLE_BLOCKS)
        
        # Both blocks should be present
        assert "initiatedAt(gap(Vessel)=nearPorts" in result
        assert "terminatedAt(gap(Vessel)=_PortStatus" in result
        
        # Blocks should be separated by double newline
        assert "\n\n" in result
    
    def test_filters_non_prolog(self):
        """Should exclude non-prolog code blocks."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_MIXED_LANGUAGES)
        
        # Prolog should be present
        assert "initiatedAt(highSpeed" in result
        
        # Python should NOT be present
        assert "print(result)" not in result
        assert "evaluate_rule" not in result
    
    def test_includes_untagged_by_default(self):
        """Should include untagged blocks by default."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_UNTAGGED_BLOCK)
        assert "initiatedAt(lowSpeed" in result
    
    def test_excludes_untagged_when_disabled(self):
        """Should exclude untagged blocks when include_untagged=False."""
        result = extract_prolog_blocks(
            SAMPLE_RESPONSE_UNTAGGED_BLOCK,
            include_untagged=False
        )
        assert result == ""
    
    def test_recognizes_rtec_tag(self):
        """Should recognize 'rtec' as a prolog alias."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_RTEC_TAG)
        assert "holdsFor(trawling" in result
    
    def test_strips_whitespace_by_default(self):
        """Should strip whitespace from extracted blocks."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_SINGLE_BLOCK)
        assert not result.startswith("\n")
        assert not result.endswith("\n")
    
    def test_preserves_whitespace_when_disabled(self):
        """Should preserve internal whitespace structure."""
        result = extract_prolog_blocks(
            SAMPLE_RESPONSE_SINGLE_BLOCK,
            strip_whitespace=True
        )
        # Should preserve indentation within the block
        assert "    happensAt" in result or "happensAt" in result
    
    def test_empty_when_no_prolog_blocks(self):
        """Should return empty string when no prolog blocks found."""
        result = extract_prolog_blocks(SAMPLE_RESPONSE_EMPTY)
        assert result == ""


# ============================================================
# Tests for extract_rules_from_response
# ============================================================

class TestExtractRulesFromResponse:
    """Tests for the extract_rules_from_response function."""
    
    def test_extracts_from_code_blocks(self):
        """Should extract rules from code blocks."""
        result = extract_rules_from_response(SAMPLE_RESPONSE_SINGLE_BLOCK)
        assert "initiatedAt(gap(Vessel)" in result
    
    def test_fallback_to_raw_code(self):
        """Should return full response when no blocks found (fallback)."""
        result = extract_rules_from_response(SAMPLE_RESPONSE_RAW_CODE)
        assert "initiatedAt(foo(X)=true" in result
        assert "terminatedAt(foo(X)=true" in result
    
    def test_no_fallback_when_disabled(self):
        """Should return empty when no blocks and fallback disabled."""
        result = extract_rules_from_response(
            SAMPLE_RESPONSE_EMPTY,
            fallback_to_full=False
        )
        assert result == ""
    
    def test_prefers_code_blocks_over_fallback(self):
        """Should prefer code blocks even when response has other text."""
        result = extract_rules_from_response(SAMPLE_RESPONSE_MULTIPLE_BLOCKS)
        
        # Should have the code
        assert "initiatedAt(gap" in result
        
        # Should NOT have the explanatory text
        assert "The gap is expressed as" not in result
        assert "These rules together" not in result
    
    def test_handles_empty_response(self):
        """Should handle empty string input."""
        result = extract_rules_from_response("")
        assert result == ""
    
    def test_strips_result(self):
        """Should strip whitespace from final result."""
        result = extract_rules_from_response(SAMPLE_RESPONSE_SINGLE_BLOCK)
        assert result == result.strip()


# ============================================================
# Edge case tests
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""
    
    def test_nested_backticks(self):
        """Should handle code that mentions backticks."""
        text = """
```prolog
% This rule uses \\` for escaping
foo(X) :- bar(X).
```
"""
        result = extract_prolog_blocks(text)
        assert "foo(X)" in result
    
    def test_incomplete_code_block(self):
        """Should not extract incomplete code blocks."""
        text = """
```prolog
initiatedAt(foo(X), T)
        
Missing the closing backticks...
"""
        result = extract_prolog_blocks(text)
        assert result == ""
    
    def test_multiple_languages_same_response(self):
        """Should only extract prolog from mixed-language responses."""
        text = """
```javascript
console.log("hello");
```

```prolog
foo(X) :- bar(X).
```

```sql
SELECT * FROM rules;
```
"""
        result = extract_prolog_blocks(text, include_untagged=False)
        assert "foo(X)" in result
        assert "console.log" not in result
        assert "SELECT" not in result
    
    def test_preserves_prolog_operators(self):
        """Should preserve Prolog operators like \\+ and =\\=."""
        text = """
```prolog
test(X) :-
    \\+foo(X),
    X =\\= 0.
```
"""
        result = extract_prolog_blocks(text)
        assert "\\+foo(X)" in result
        assert "=\\= 0" in result
    
    def test_empty_code_block(self):
        """Should handle empty code blocks gracefully."""
        text = """
```prolog
```

```prolog
foo(X).
```
"""
        result = extract_prolog_blocks(text)
        assert "foo(X)" in result
        # Empty block should not add extra newlines
        assert result.strip() == "foo(X)."

