from src.interfaces.llm import LLMProvider
from src.interfaces.models import LLMConfig, LLMRequest
from openai import AsyncOpenAI

class OpenAILLMProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=config.api_key, **config.extra)

    def _call_provider(self, final_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            messages=[{"role": "user", "content": final_prompt}],
            **self.config.extra,
        )
        return resp.choices[0].message.content