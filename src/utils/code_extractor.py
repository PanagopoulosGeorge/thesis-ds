"""Code extraction utilities for parsing LLM responses.

LLM responses often contain explanatory text along with code blocks.
This module provides utilities to extract code from markdown-formatted responses.

Example LLM response:
    The gap fluent is defined as follows:
    
    ```prolog
    initiatedAt(gap(Vessel)=nearPorts, T) :-
        happensAt(gap_start(Vessel), T).
    ```
    
    And it terminates when:
    
    ```prolog
    terminatedAt(gap(Vessel)=_Status, T) :-
        happensAt(gap_end(Vessel), T).
    ```

This module extracts all prolog blocks into a single string.
"""

import re
from typing import List, Optional, Tuple


# Pattern to match markdown code blocks with optional language tag
# Captures: (language_tag, code_content)
CODE_BLOCK_PATTERN = re.compile(
    r"```(\w*)\s*\n(.*?)```",
    re.DOTALL
)

# Common aliases for Prolog-like languages
PROLOG_ALIASES = {"prolog", "pl", "rtec", ""}


def extract_all_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Extract all code blocks from markdown-formatted text.
    
    Args:
        text: The full LLM response text containing markdown code blocks
        
    Returns:
        List of (language, code) tuples for each code block found
        
    Example:
        >>> text = '''Here's the code:
        ... ```python
        ... print("hello")
        ... ```
        ... '''
        >>> extract_all_code_blocks(text)
        [('python', 'print("hello")\\n')]
    """
    matches = CODE_BLOCK_PATTERN.findall(text)
    return [(lang.lower().strip(), code) for lang, code in matches]


def extract_prolog_blocks(
    text: str,
    include_untagged: bool = True,
    strip_whitespace: bool = True,
) -> str:
    """Extract all Prolog/RTEC code blocks from an LLM response.
    
    Searches for markdown code blocks tagged with 'prolog', 'pl', 'rtec',
    or untagged blocks (if include_untagged=True), and concatenates them
    into a single string.
    
    Args:
        text: The full LLM response text
        include_untagged: Whether to include code blocks without a language tag
        strip_whitespace: Whether to strip leading/trailing whitespace from blocks
        
    Returns:
        Concatenated Prolog code from all matching blocks
        
    Example:
        >>> text = '''
        ... The gap is expressed as:
        ... 
        ... ```prolog
        ... initiatedAt(gap(Vessel)=nearPorts, T) :-
        ...     happensAt(gap_start(Vessel), T).
        ... ```
        ... 
        ... And terminated using:
        ... 
        ... ```prolog
        ... terminatedAt(gap(Vessel)=_Status, T) :-
        ...     happensAt(gap_end(Vessel), T).
        ... ```
        ... '''
        >>> extract_prolog_blocks(text)
        'initiatedAt(gap(Vessel)=nearPorts, T) :-\\n    happensAt(gap_start(Vessel), T).\\n\\nterminatedAt(gap(Vessel)=_Status, T) :-\\n    happensAt(gap_end(Vessel), T).'
    """
    all_blocks = extract_all_code_blocks(text)
    
    prolog_blocks: List[str] = []
    
    for lang, code in all_blocks:
        # Check if this is a Prolog-like block (excluding empty string check)
        is_prolog = lang in PROLOG_ALIASES and lang != ""
        is_untagged = lang == ""
        
        if is_prolog or (is_untagged and include_untagged):
            block = code.strip() if strip_whitespace else code
            if block:  # Only add non-empty blocks
                prolog_blocks.append(block)
    
    return "\n\n".join(prolog_blocks)


def extract_rules_from_response(
    response: str,
    fallback_to_full: bool = True,
) -> str:
    """Extract RTEC rules from an LLM response with fallback behavior.
    
    Primary extraction method: Look for prolog/rtec code blocks.
    Fallback: If no code blocks found and fallback_to_full=True,
    return the original response (assuming it's raw code).
    
    Args:
        response: The LLM response text
        fallback_to_full: If True and no code blocks found, return full response
        
    Returns:
        Extracted rules string
        
    Example:
        >>> # When response contains code blocks
        >>> response = "Here's the rule:\\n```prolog\\nfoo(X).\\n```"
        >>> extract_rules_from_response(response)
        'foo(X).'
        
        >>> # When response is raw code (no blocks)
        >>> response = "initiatedAt(foo(X)=true, T) :- bar(X, T)."
        >>> extract_rules_from_response(response)
        'initiatedAt(foo(X)=true, T) :- bar(X, T).'
    """
    extracted = extract_prolog_blocks(response)
    
    if extracted:
        return extracted
    
    if fallback_to_full:
        # No code blocks found - assume the response is raw code
        return response.strip()
    
    return ""

