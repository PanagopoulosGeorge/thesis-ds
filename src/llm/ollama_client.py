"""Ollama LLM provider for local model inference."""

from typing import Optional
from src.interfaces.llm import LLMProvider
from src.interfaces.models import LLMConfig, LLMRequest

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class OllamaLLMProvider(LLMProvider):
    """LLM provider for local Ollama models.
    
    Ollama runs models locally and exposes them via HTTP API (default: localhost:11434).
    
    Config options:
        - config.extra["model"]: The model name (e.g., "llama3.2", "mistral", "codellama")
        - config.extra["host"]: Optional Ollama host URL (defaults to http://localhost:11434)
        - config.extra["options"]: Optional model parameters (temperature, num_predict, etc.)
    
    Example usage:
        >>> config = LLMConfig(
        ...     provider="ollama",
        ...     api_key="",  # Not required for local Ollama
        ...     extra={"model": "llama3.2", "options": {"temperature": 0.7}}
        ... )
        >>> provider = OllamaLLMProvider(config)
        >>> response = provider.generate(request)
    
    CLI usage:
        rtec-llm run --domain msa --provider ollama --model llama3.2
    """
    
    def __init__(self, config: LLMConfig):
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "The 'ollama' package is required for OllamaLLMProvider. "
                "Install it with: pip install ollama"
            )
        super().__init__(config)
        
        # Get host from config or use default
        host = config.extra.get("host", "http://localhost:11434")
        self.client = ollama.Client(host=host)
        
        # Get model from config.extra (set by CLI via --model flag)
        self.model = config.extra.get("model", "llama3.2")
    
    def _call_provider(self, request: LLMRequest, final_prompt: str) -> str:
        """Call Ollama to generate a response.
        
        Args:
            request: The LLMRequest containing temperature and other parameters
            final_prompt: The structured prompt to send to the model.
            
        Returns:
            The model's response text.
        """
        # Build options from request (preferred) and config (fallback)
        options = {}
        
        # Use temperature from request if provided, otherwise fall back to config
        temperature = request.temperature if request.temperature is not None else self.config.temperature
        if temperature is not None:
            options["temperature"] = temperature
        
        # Use max_tokens from request if provided, otherwise from config
        max_tokens = request.max_tokens if request.max_tokens is not None else self.config.max_tokens
        if max_tokens is not None:
            options["num_predict"] = max_tokens  # Ollama uses num_predict instead of max_tokens
        
        # Merge any additional options from config.extra
        extra_options = self.config.extra.get("options", {})
        options.update(extra_options)
        
        # Use model from request if provided, otherwise from config
        model = request.model if request.model is not None else self.model
        
        # Call Ollama
        response = self.client.chat(
            model=model,
            messages=[{"role": "user", "content": final_prompt}],
            options=options if options else None,
        )
        
        return response["message"]["content"]

