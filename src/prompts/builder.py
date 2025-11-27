"""Prompt builder for generating LLM messages for RTEC rule generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.prompts.har_domain import (
    system_HAR,
    system_HAR_BK,
    system_HAR_events,
    system_HAR_fluents,
)
from src.prompts.har_examples import har_examples
from src.prompts.har_requests import har_requests
from src.prompts.msa_domain import (
    system_MSA,
    system_MSA_BK,
    system_MSA_events,
)
from src.prompts.msa_examples import (
    simple_fluent_examples,
    static_fluent_examples,
)
from src.prompts.msa_requests import msa_requests
from src.prompts.rtec_base import (
    system_1,
    system_2,
    system_3,
    system_simple_fluent_definition,
    system_static_fluent_definition,
)


class BasePromptBuilder(ABC):
    """Base class for building prompts for RTEC rule generation."""
    
    def __init__(self):
        """Initialize the base prompt builder."""
        self.base_system_messages = [
            system_1,
            system_2,
            system_3,
            system_simple_fluent_definition,
            system_static_fluent_definition,
        ]

    @abstractmethod
    def get_domain_messages(self) -> List[Any]:
        """Get domain-specific system messages.
        
        Returns:
            List of domain-specific system message templates.
        """
        pass

    @abstractmethod
    def get_examples(self, fluent_type: str = "both") -> List[Dict[str, str]]:
        """
        Get domain-specific examples.
        
        Args:
            fluent_type: Type of examples to return.
                Options: 'simple', 'static', or 'both'.
        
        Returns:
            List of example dictionaries with 'input' and 'output' keys.
        """
        pass

    @abstractmethod

    def get_activity_description(self, activity: str) -> str:
        """Get the full activity description for a given activity name.
        
        Args:
            activity: The activity name (e.g., 'gap', 'leaving_object').
            
        Returns:
            The full activity description string.
        """
        pass
    
    def _format_examples(self, fluent_type: str = "both") -> str:
        """Format examples into a readable string for the system message.
        
        Args:
            fluent_type: Type of examples to format.
                Options: 'simple', 'static', or 'both'.
        
        Returns:
            Formatted string containing all examples.
        """
        examples = self.get_examples(fluent_type)
        formatted = []
        
        for i, example in enumerate(examples, 1):
            formatted.append(f"Example {i}:\n")
            formatted.append(f"Input: {example['input'].strip()}\n")
            formatted.append(f"Output: {example['output'].strip()}\n")
            formatted.append("\n")
        
        return "\n".join(formatted)
    
    def build_initial(
        self,
        activity: str,
        fluent_type: str = "both",
        prerequisite_rules: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build initial prompt for generating RTEC rules.
        
        Args:
            activity: The activity name to generate rules for.
            fluent_type: Type of examples to include in the prompt.
                Options: 'simple', 'static', or 'both'.
            
        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        messages = []
        
        # Build comprehensive system message
        system_parts = []

        # Add base RTEC prompts
        for msg_template in self.base_system_messages:
            formatted = msg_template.format()
            system_parts.append(formatted.content)

        # Add domain-specific messages
        for msg_template in self.get_domain_messages():
            formatted = msg_template.format()
            system_parts.append(formatted.content)
        
        # Add examples
        system_parts.append("\n=== Examples ===\n")
        system_parts.append(self._format_examples(fluent_type))

        # Inject prerequisite rules if provided
        if prerequisite_rules:
            system_parts.append("\n=== Previously Learned Rules ===\n")
            system_parts.append(prerequisite_rules)
        
        # Combine into single system message
        system_content = "\n\n".join(system_parts)
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add user message with activity description
        activity_desc = self.get_activity_description(activity)
        messages.append({
            "role": "user",
            "content": activity_desc
        })
        
        return messages
    
    def build_refinement(
        self,
        activity: str,
        prev_rules: str,
        feedback: str,
        attempt: int,
        fluent_type: str = "both",
        prerequisite_rules: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build refinement prompt for improving RTEC rules based on feedback.
        
        Args:
            activity: The activity name.
            prev_rules: Previously generated rules.
            feedback: Feedback on the previous rules.
            attempt: The current attempt number.
            fluent_type: Type of examples to include in the prompt.
                Options: 'simple', 'static', or 'both'.
            
        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        messages = []
        
        # Build comprehensive system message (same as initial)
        system_parts = []

        # Add base RTEC prompts
        for msg_template in self.base_system_messages:
            formatted = msg_template.format()
            system_parts.append(formatted.content)

        # Add domain-specific messages
        for msg_template in self.get_domain_messages():
            formatted = msg_template.format()
            system_parts.append(formatted.content)
        
        # Add examples
        system_parts.append("\n=== Examples ===\n")
        system_parts.append(self._format_examples(fluent_type))

        # Inject prerequisite rules if provided
        if prerequisite_rules:
            system_parts.append("\n=== Previously Learned Rules ===\n")
            system_parts.append(prerequisite_rules)
        
        # Combine into single system message
        system_content = "\n\n".join(system_parts)
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add user message with refinement context
        activity_desc = self.get_activity_description(activity)

        refinement_content = (
            f"""This is attempt {attempt} at generating rules for """
            f"""this activity.

Original Activity Description:"
{activity_desc}

Previously Generated Rules (Attempt {attempt - 1}):
{prev_rules}

Feedback on Previous Rules:
{feedback}

Please generate improved rules that address the feedback above."""
        )
        
        messages.append({
            "role": "user",
            "content": refinement_content
        })
        
        return messages


class MSAPromptBuilder(BasePromptBuilder):
    """Prompt builder for Maritime Situational Awareness domain."""
    
    def __init__(self):
        """Initialize the MSA prompt builder."""
        super().__init__()
        self.activity_map = self._build_activity_map()
    
    def _build_activity_map(self) -> Dict[str, str]:
        """Build a mapping from activity names to full descriptions.

        Returns:
            Dictionary mapping activity names to descriptions.
        """
        activity_map = {}

        for request in msa_requests:
            # Extract activity name from description
            # Format uses curly quotes: "activity_name"
            # Unicode characters: " (U+201C) and " (U+201D)
            start_idx = request.find("\u201c")  # Left double quotation mark
            end_idx = request.find("\u201d", start_idx + 1)  # Right quotation mark
            if start_idx != -1 and end_idx != -1:
                activity_name = request[start_idx + 1:end_idx]
                activity_map[activity_name] = request

        return activity_map
    
    def get_domain_messages(self) -> List[Any]:
        """Get MSA domain-specific system messages."""
        return [
            system_MSA,
            system_MSA_events,
            system_MSA_BK,
        ]
    
    def get_examples(self, fluent_type: str = "both") -> List[Dict[str, str]]:
        """Get MSA examples.
        
        Args:
            fluent_type: Type of examples to return.
                Options: 'simple', 'static', or 'both'.
            
        Returns:
            List of example dictionaries with 'input' and 'output' keys.
        """
        if fluent_type == "simple":
            return simple_fluent_examples
        elif fluent_type == "static":
            return static_fluent_examples
        elif fluent_type == "both":
            return simple_fluent_examples + static_fluent_examples
        else:
            raise ValueError(
                f"Invalid fluent_type: '{fluent_type}'. "
                f"Must be 'simple', 'static', or 'both'."
            )
    
    def get_activity_description(self, activity: str) -> str:
        """Get the full activity description for an MSA activity.
        
        Args:
            activity: The activity name (e.g., 'gap', 'highSpeedNearCoast').
            
        Returns:
            The full activity description string.
            
        Raises:
            ValueError: If the activity is not found.
        """
        if activity not in self.activity_map:
            raise ValueError(
                f"Activity '{activity}' not found. Available activities: "
                f"{', '.join(self.activity_map.keys())}"
            )
        
        return self.activity_map[activity]


class HARPromptBuilder(BasePromptBuilder):
    """Prompt builder for Human Activity Recognition domain."""
    
    def __init__(self):
        """Initialize the HAR prompt builder."""
        super().__init__()
        self.activity_map = self._build_activity_map()
    
    def _build_activity_map(self) -> Dict[str, str]:
        """Build a mapping from activity names to full descriptions.

        Returns:
            Dictionary mapping activity names to descriptions.
        """
        activity_map = {}

        for request in har_requests:
            # Extract activity name from description
            # Format uses curly quotes: "activity_name"
            # Unicode characters: " (U+201C) and " (U+201D)
            start_idx = request.find("\u201c")  # Left double quotation mark
            end_idx = request.find("\u201d", start_idx + 1)  # Right quotation mark
            if start_idx != -1 and end_idx != -1:
                activity_name = request[start_idx + 1:end_idx]
                activity_map[activity_name] = request

        return activity_map
    
    def get_domain_messages(self) -> List[Any]:
        """Get HAR domain-specific system messages."""
        return [
            system_HAR,
            system_HAR_events,
            system_HAR_fluents,
            system_HAR_BK,
        ]
    
    def get_examples(self, fluent_type: str = "both") -> List[Dict[str, str]]:
        """Get HAR examples.
        
        Args:
            fluent_type: Type of examples to return.
                Options: 'simple', 'static', or 'both'.
                Note: HAR examples are not explicitly separated by type,
                so all examples are returned regardless of fluent_type.
            
        Returns:
            List of example dictionaries with 'input' and 'output' keys.
        """
        if fluent_type == "simple":
            return [har_examples[0]]  # Return as list
        elif fluent_type == "static":
            return har_examples[1:3]
        return har_examples
    
    def get_activity_description(self, activity: str) -> str:
        """Get the full activity description for a HAR activity.

        Args:
            activity: The activity name (e.g., 'leaving_object', 'moving',
                'fighting').
            
        Returns:
            The full activity description string.
            
        Raises:
            ValueError: If the activity is not found.
        """
        if activity not in self.activity_map:
            raise ValueError(
                f"Activity '{activity}' not found. Available activities: "
                f"{', '.join(self.activity_map.keys())}"
            )
        
        return self.activity_map[activity]
