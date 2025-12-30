"""Test the LoopOrchestrator with mock LLM provider (no API calls).

Run with:
    python examples/test_orchestrator_mock.py
"""
import time
from src.core import LoopOrchestrator, OrchestratorConfig
from src.feedback.client import FeedbackClient
from src.llm.mock_provider import MockLLMProvider
from src.memory import RuleMemory
from src.prompts.factory import get_prompt_builder
from src.prompts.msa_requests import msa_requests


def test_single_iteration():
    """Test a single fluent with mock responses."""
    
    print("\n" + "="*60)
    time.sleep(0.4)
    print("TEST: Single iteration with mock LLM")
    time.sleep(0.4)
    print("="*60)
    
    # Get ground truth for "gap" fluent
    fluent = msa_requests[0]
    ground_truth = fluent['prolog']
    
    # Create mock provider that returns the ground truth directly
    # (simulates a perfect LLM response)
    mock_response = f"""
Here are the RTEC rules for the gap fluent:

```prolog
{ground_truth}
```

These rules capture the communication gap behavior.
"""
    
    mock_provider = MockLLMProvider(responses=mock_response)
    
    # Create orchestrator
    orchestrator = LoopOrchestrator(
        prompt_builder=get_prompt_builder("msa"),
        llm_provider=mock_provider,
        memory=RuleMemory(),
        feedback_client=FeedbackClient(log_file="logs/mock_test.log"),
        config=OrchestratorConfig(
            max_iterations=3,
            convergence_threshold=0.9,
            verbose=True,
        ),
    )
    
    # Run
    result = orchestrator.run(
        fluent_name=fluent['fluent_name'],
        activity_description=fluent['description'],
        ground_truth=ground_truth,
    )
    time.sleep(0.4)
    print(f"\nResult: {result.fluent_name}")
    time.sleep(0.4)
    print(f"Best score: {result.best_score:.4f}")
    time.sleep(0.4)
    print(f"Converged: {result.converged}")
    time.sleep(0.4)
    print(f"LLM calls made: {mock_provider.call_count}")
    time.sleep(0.4)
    return result


def test_improving_responses():
    """Test with responses that improve over iterations."""
    print("\n" + "="*60)
    time.sleep(0.4)
    print("TEST: Improving responses over iterations")
    time.sleep(0.4)
    print("="*60)
    
    fluent = msa_requests[0]
    ground_truth = fluent['prolog']
    
    # Create responses that progressively improve
    responses = [
        # Iteration 1: Completely wrong
        """```prolog
initiatedAt(gap(Vessel)=true, T) :-
    happensAt(start(Vessel), T).
```""",
        # Iteration 2: Better structure, missing details
        """```prolog
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T).

terminatedAt(gap(Vessel)=_, T) :-
    happensAt(gap_end(Vessel), T).
```""",
        # Iteration 3: Very close to ground truth
        f"""```prolog
{ground_truth}
```""",
    ]
    
    mock_provider = MockLLMProvider(responses=responses)
    
    orchestrator = LoopOrchestrator(
        prompt_builder=get_prompt_builder("msa"),
        llm_provider=mock_provider,
        memory=RuleMemory(),
        feedback_client=FeedbackClient(log_file="logs/mock_improving.log"),
        config=OrchestratorConfig(
            max_iterations=5,
            convergence_threshold=0.95,
            verbose=True,
        ),
    )
    
    time.sleep(0.4)
    result = orchestrator.run(
        fluent_name=fluent['fluent_name'],
        activity_description=fluent['description'],
        ground_truth=ground_truth,
    )
    time.sleep(0.4)
    print(f"\n--- Iteration History ---")
    for it in result.iterations:
        print(f"  Iteration {it.iteration}: score={it.similarity_score:.4f}")
    time.sleep(0.4)
    print(f"\nFinal: {result.best_score:.4f} (converged: {result.converged})")
    time.sleep(0.4)
    print(f"Improvement: {result.statistics.initial_score:.4f} → {result.best_score:.4f}")
    time.sleep(0.4)
    print(f"LLM calls: {mock_provider.call_count}")
    time.sleep(0.4)
    return result


def test_feedback_injection():
    """Verify that feedback is properly passed to subsequent prompts."""
    print("\n" + "="*60)
    time.sleep(0.4)
    print("TEST: Feedback injection verification")
    time.sleep(0.4)
    print("="*60)
    time.sleep(0.4)
    fluent = msa_requests[0]
    ground_truth = fluent['prolog']
    
    # Wrong response to ensure feedback is generated
    mock_provider = MockLLMProvider(responses="""```prolog
wrong_rule(X) :- placeholder(X).
```""")
    
    orchestrator = LoopOrchestrator(
        prompt_builder=get_prompt_builder("msa"),
        llm_provider=mock_provider,
        memory=RuleMemory(),
        feedback_client=FeedbackClient(log_file="logs/mock_feedback.log"),
        config=OrchestratorConfig(
            max_iterations=3,
            convergence_threshold=0.99,  # Won't converge
            verbose=False,
        ),
    )
    
    result = orchestrator.run(
        fluent_name=fluent['fluent_name'],
        activity_description=fluent['description'],
        ground_truth=ground_truth,
    )
    time.sleep(0.4)
    # Check that feedback was generated
    print(f"Iterations run: {len(result.iterations)}")
    time.sleep(0.4)
    for it in result.iterations:
        has_feedback = it.feedback and len(it.feedback) > 0
        print(f"  Iteration {it.iteration}: score={it.similarity_score:.4f}, has_feedback={has_feedback}")
        time.sleep(0.4)
    # Inspect call history to see if feedback was injected
    print(f"\nLLM call history ({mock_provider.call_count} calls):")
    time.sleep(0.4)
    for i, req in enumerate(mock_provider.call_history, 1):
        has_fb = req.feedback is not None and len(req.feedback) > 0
        print(f"  Call {i}: feedback_injected={has_fb}")
        time.sleep(0.4)
    return result


def test_early_stopping():
    """Test early stopping when no improvement."""
    print("\n" + "="*60)
    print("TEST: Early stopping")
    print("="*60)
    
    fluent = msa_requests[0]
    
    # Same bad response every time - should trigger early stopping
    mock_provider = MockLLMProvider(responses="""```prolog
static_bad_rule(X).
```""")
    
    orchestrator = LoopOrchestrator(
        prompt_builder=get_prompt_builder("msa"),
        llm_provider=mock_provider,
        memory=RuleMemory(),
        feedback_client=FeedbackClient(log_file="logs/mock_early_stop.log"),
        config=OrchestratorConfig(
            max_iterations=10,
            convergence_threshold=0.99,
            early_stopping=True,
            early_stopping_patience=2,
            verbose=False,
        ),
    )
    
    result = orchestrator.run(
        fluent_name=fluent['fluent_name'],
        activity_description=fluent['description'],
        ground_truth=fluent['prolog'],
    )
    time.sleep(0.4)
    print(f"Max iterations: 10")
    time.sleep(0.4)
    print(f"Actual iterations: {len(result.iterations)}")
    time.sleep(0.4)
    print(f"Early stopping triggered: {len(result.iterations) < 10}")
    time.sleep(0.4)
    print(f"Scores: {[f'{it.similarity_score:.4f}' for it in result.iterations]}")
    time.sleep(0.4)
    return result


if __name__ == "__main__":
    # Run all tests
    # test_single_iteration()
    # time.sleep(10)
    # test_improving_responses()
    # time.sleep(10)
    test_feedback_injection()
    time.sleep(10)
    # test_early_stopping()
    # time.sleep(10)
    # print("\n" + "="*60)
    # time.sleep(1)
    print("All mock tests completed!")
    time.sleep(1)
    print("="*60)

