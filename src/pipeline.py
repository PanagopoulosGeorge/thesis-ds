# e.g., src/pipeline.py
import asyncio
from typing import Callable, Optional, Any
from src.prompts.factory import get_prompt_builder
from src.llm.openai import OpenAILLMProvider
from src.interfaces.models import LLMRequest, FewShotExample, LLMConfig

class PromptRun:
    def __init__(self, builder, provider):
        self.builder = builder
        self.provider = provider
        self.request: Optional[LLMRequest] = None
        self.output: Optional[str] = None
        self.evaluation: Any = None

    def build(self, activity_description: str,
              prerequisites: Optional[list[FewShotExample]] = None,
              feedback: Optional[str] = None):
        self.request = self.builder.build_prompt(
            activity_description, prerequisites=prerequisites, feedback=feedback
        )
        return self

    def generate(self):
        if not self.request:
            raise ValueError("Call build() before generate().")
        # run the async provider synchronously
        self.output = asyncio.run(self.provider._call_provider(self.request, self.provider._build_prompt(self.request)))
        return self

    def evaluate(self, scorer: Callable[[str], Any]):
        if self.output is None:
            raise ValueError("Call generate() before evaluate().")
        self.evaluation = scorer(self.output)
        return self

# Example use
builder = get_prompt_builder("msa")
config = LLMConfig(provider="openai", api_key="sk-...", model="gpt-4o")
provider = OpenAILLMProvider(config)

run = PromptRun(builder, provider) \
    .build("Generate gap rules") \
    .generate() \
    .evaluate(lambda out: {"length": len(out)})
print(run.output, run.evaluation)