"""MSA (Maritime Situational Awareness) domain prompt builder."""
from typing import List

from src.interfaces.models import FewShotExample
from src.interfaces.prompts import PromptBuilder
from src.prompts.rtec_base import basic_system_messages, example_system_messages
from src.prompts.msa_domain import system_MSA, system_MSA_events, system_MSA_BK
from src.prompts.msa_examples import simple_fluent_examples, static_fluent_examples


class MSAPromptBuilder(PromptBuilder):
    """Prompt builder for Maritime Situational Awareness domain.
    
    Provides MSA-specific:
    - Events (vessel movements, signals, area transitions)
    - Input fluents (proximity, velocity)
    - Background knowledge (thresholds, vessel types)
    - Few-shot examples (withinArea, stopped, underWay, rendezVous)
    """
    
    @property
    def domain_name(self) -> str:
        return "msa"
    
    def get_system_prompt(self) -> str:
        """Return complete system prompt (base RTEC + MSA domain)."""
        parts: List[str] = list(basic_system_messages + example_system_messages)
        parts.extend([system_MSA, system_MSA_events, system_MSA_BK])
        return "\n\n".join(parts)
    
    def get_fewshot_examples(self) -> List[FewShotExample]:
        """Return MSA few-shot examples (simple + static fluents)."""
        examples: List[FewShotExample] = []
        
        for ex in simple_fluent_examples + static_fluent_examples:
            examples.append(FewShotExample(
                user=ex["input"].strip(),
                assistant=ex["output"].strip()
            ))
        
        return examples

