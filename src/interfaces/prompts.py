"""
Abstract base class for domain-specific prompt builders.
  - Each domain implements its own PromptBuilder 
  - Adding new domains doesn't require modifying existing code
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.interfaces.models import LLMRequest, FewShotExample


class PromptBuilder(ABC):
    """Abstract base class for RTEC prompt builders.
    
    Subclasses must implement:
    - get_system_prompt(): Full system prompt (base RTEC + domain knowledge)
    - get_fewshot_examples(): Domain-specific few-shot examples
    - domain_name: Domain identifier
    
    Few-shot structure:
    1. Domain examples (from get_fewshot_examples) - teach format/style
    2. Prerequisites (from RuleMemory) - provide learned fluents as context
    """
    
    def build_prompt(
        self,
        activity_description: str,
        prerequisites: Optional[List[FewShotExample]] = None,
        feedback: Optional[str] = None,
    ) -> LLMRequest:
        """Build a complete LLMRequest for generating RTEC rules.
        
        Args:
            activity_description: Natural language description of the activity
            prerequisites: Previously learned fluents as request→response pairs
        
        Returns:
            LLMRequest ready to send to the LLM provider
        """
        system_prompt = self.get_system_prompt()
        fewshots = self._build_fewshots(prerequisites)
        
        return LLMRequest(
            prompt=activity_description,
            system_prompt=system_prompt,
            fewshots=fewshots,
            feedback=feedback,
        )
    
    def _build_fewshots(
        self, 
        prerequisites: Optional[List[FewShotExample]] = None
    ) -> List[FewShotExample]:
        """Combine domain examples with prerequisite fluents.
        
        Order: domain examples first (teach format), then prerequisites (context).
        """
        fewshots: List[FewShotExample] = []
        
        # 1. Domain examples (teach the LLM how to write rules)
        examples = self.get_fewshot_examples()
        if examples:
            fewshots.extend(examples)
        
        # 2. Prerequisites (previously learned fluents from RuleMemory)
        if prerequisites:
            fewshots.extend(prerequisites)
        
        return fewshots
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the complete system prompt (base RTEC + domain knowledge).
        
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_fewshot_examples(self) -> List[FewShotExample]:
        """Return domain-specific few-shot examples.
        
        Must be implemented by subclasses.
        """
        pass
    
    @property
    @abstractmethod
    def domain_name(self) -> str:
        """Return the domain name (e.g., 'msa', 'har')."""
        pass


