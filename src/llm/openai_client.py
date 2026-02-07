from src.interfaces.llm import LLMProvider
from src.interfaces.models import LLMConfig, LLMRequest
from openai import OpenAI
from src.prompts.msa_requests import msa_requests
class OpenAILLMProvider(LLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = OpenAI(api_key=config.api_key)

    def _call_provider(self, request: LLMRequest, final_prompt: str) -> str:
        """Call OpenAI API with temperature from request (fallback to config)."""
        # Build API parameters
        api_params = {
            "messages": [{"role": "user", "content": final_prompt}],
        }
        
        # Use temperature from request if provided, otherwise fall back to config
        temperature = request.temperature if request.temperature is not None else self.config.temperature
        if temperature is not None:
            api_params["temperature"] = temperature
        
        # Use model from request if provided, otherwise from config.extra
        model = request.model if request.model is not None else self.config.extra.get("model")
        if model is not None:
            api_params["model"] = model
        
        # Use max_tokens from request if provided, otherwise from config
        max_tokens = request.max_tokens if request.max_tokens is not None else self.config.max_tokens
        if max_tokens is not None:
            api_params["max_tokens"] = max_tokens
        
        # Merge any additional parameters from config.extra (but don't override explicit params)
        extra_params = {k: v for k, v in self.config.extra.items() if k not in api_params}
        api_params.update(extra_params)
        
        resp = self.client.chat.completions.create(**api_params)
        return resp.choices[0].message.content
