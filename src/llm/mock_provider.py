"""Mock LLM provider for testing without API calls."""

from typing import List, Optional, Union
from src.interfaces.llm import LLMProvider
from src.interfaces.models import LLMConfig, LLMRequest


class MockLLMProvider(LLMProvider):
    """Mock LLM provider that returns predefined responses.
    
    Useful for testing the feedback loop without making actual API calls.
    
    Example:
        >>> responses = [
        ...     "```prolog\\ninitiatedAt(foo(X)=true, T).\\n```",
        ...     "```prolog\\ninitiatedAt(foo(X)=true, T) :- bar(X, T).\\n```",
        ... ]
        >>> provider = MockLLMProvider(responses)
        >>> provider.generate(request)  # Returns first response
        >>> provider.generate(request)  # Returns second response
    """
    
    def __init__(
        self,
        responses: Optional[Union[str, List[str]]] = None,
        config: Optional[LLMConfig] = None,
    ):
        """Initialize with predefined responses.
        
        Args:
            responses: Single response string or list of responses.
                       If list, responses are returned in order (cycling if needed).
                       If None, returns a default placeholder response.
            config: Optional LLMConfig (not used, just for interface compatibility)
        """
        # Create a dummy config if none provided
        if config is None:
            config = LLMConfig(provider="mock", api_key="mock-key")
        super().__init__(config)
        
        if responses is None:
            self._responses = ["```prolog\n% Mock response\nmock_rule(X).\n```"]
        elif isinstance(responses, str):
            self._responses = [responses]
        else:
            self._responses = list(responses)
        
        self._call_count = 0
        self._call_history: List[LLMRequest] = []
    
    def _call_provider(self, final_prompt: str) -> str:
        """Return the next predefined response."""
        # Cycle through responses
        response = self._responses[self._call_count % len(self._responses)]
        self._call_count += 1
        return response
    
    def generate(self, request: LLMRequest) -> str:
        """Generate response and track the request."""
        self._call_history.append(request)
        return super().generate(request)
    
    @property
    def call_count(self) -> int:
        """Number of times generate() was called."""
        return self._call_count
    
    @property
    def call_history(self) -> List[LLMRequest]:
        """History of all requests made."""
        return self._call_history
    
    def reset(self) -> None:
        """Reset call count and history."""
        self._call_count = 0
        self._call_history = []


class ProgressiveMockProvider(MockLLMProvider):
    """Mock provider that simulates improvement over iterations.
    
    Returns progressively "better" responses that get closer to ground truth.
    Useful for testing the full feedback loop behavior.
    """
    
    def __init__(
        self,
        ground_truth: str,
        initial_response: Optional[str] = None,
        improvement_steps: int = 3,
    ):
        """Initialize with ground truth to converge towards.
        
        Args:
            ground_truth: The target rules to eventually return
            initial_response: First response (defaults to partial match)
            improvement_steps: Number of steps before returning ground truth
        """
        # Create responses that progressively improve
        if initial_response is None:
            initial_response = """```prolog
% Initial attempt - incomplete
mock_initial_rule(X) :- placeholder(X).
```"""
        
        # Build progression: initial -> ... -> ground_truth
        responses = [initial_response]
        
        # Add intermediate "improving" responses
        for i in range(1, improvement_steps):
            responses.append(f"""```prolog
% Iteration {i+1} - improving
{ground_truth[:len(ground_truth)//2]}
% ... partial implementation
```""")
        
        # Final response is the ground truth wrapped in code block
        responses.append(f"```prolog\n{ground_truth}\n```")
        
        super().__init__(responses=responses)
        self.ground_truth = ground_truth
        self.improvement_steps = improvement_steps

