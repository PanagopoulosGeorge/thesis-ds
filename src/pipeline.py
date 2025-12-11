# e.g., src/pipeline.py
import asyncio
from typing import Callable, Optional, Any
from src.prompts.factory import get_prompt_builder
from src.llm.factory import get_provider
from src.llm import OpenAILLMProvider
from src.interfaces.models import LLMRequest, FewShotExample, LLMConfig
from src.prompts.msa_requests import msa_requests
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

    def prompt(self):
        if not self.request:
            raise ValueError("Call build() before generate().")
        self.output = self.provider.generate(self.request)        
        return self

# Example use
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

builder = get_prompt_builder("msa")
config = LLMConfig(provider="openai", api_key=api_key, extra={"model":"gpt-4o"})
provider_class = get_provider("openai")
provider = provider_class(config)

run = PromptRun(builder, provider) \
    .build(msa_requests[0]) \
    .prompt()
print(run.output)