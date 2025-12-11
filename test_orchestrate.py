from src.prompts.factory import get_prompt_builder
from src.interfaces.llm import LLMProvider
from src.interfaces.models import LLMConfig

builder = get_prompt_builder("msa")
request = builder.build_prompt("Generate gap rules")

config = LLMConfig(
    provider="openai",
    api_key="sk-proj-1234567890",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2048,
    timeout=30,
    extra={"api_base": "https://api.openai.com/v1"}
)

provider = LLMProvider(config)
result = provider._build_prompt(request)
print(result)
