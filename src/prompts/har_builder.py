"""HAR (Human Activity Recognition) domain prompt builder."""
from typing import List

from src.interfaces.models import FewShotExample
from src.interfaces.prompts import PromptBuilder
from src.prompts.rtec_base import basic_system_messages, example_system_messages
from src.prompts.har_domain import har_system_messages
from src.prompts.har_examples import har_examples


class HARPromptBuilder(PromptBuilder):
    """Prompt builder for Human Activity Recognition domain.
    
    Provides HAR-specific:
    - Events
    - Input fluents 
    - Background knowledge
    - Few-shot examples
    """
    
    @property
    def domain_name(self) -> str:
        return "har"
    
    def get_system_prompt(self) -> str:
        """Return complete system prompt (base RTEC + HAR domain)."""
        parts: List[str] = list(basic_system_messages + example_system_messages)
        parts.extend(har_system_messages)
        return "\n\n".join(parts)
    
    def get_fewshot_examples(self) -> List[FewShotExample]:
        """Return HAR few-shot examples."""
        examples: List[FewShotExample] = []
        
        for ex in har_examples:
            examples.append(FewShotExample(
                user=ex["input"].strip(),
                assistant=ex["output"].strip()
            ))
        
        return examples

