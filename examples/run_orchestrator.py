"""Example: Running the LoopOrchestrator for RTEC rule generation.

This script demonstrates the complete feedback loop:
1. Initialize components (prompt builder, LLM provider, memory)
2. Run the orchestrator for a single fluent
3. Review results and statistics

Usage:
    python examples/run_orchestrator.py
    
Requirements:
    - OPENAI_API_KEY environment variable set
    - simlp package installed
"""

import os
from dotenv import load_dotenv

from src.core import LoopOrchestrator, OrchestratorConfig
from src.feedback.client import FeedbackClient
from src.llm.factory import get_provider
from src.interfaces.models import LLMConfig
from src.memory import RuleMemory
from src.prompts.factory import get_prompt_builder
from src.prompts.msa_requests import msa_requests
from src.prompts.har_requests import har_requests

def run_msa_experiment():
    """
    Run the orchestrator for the MSA domain.

    Returns:
        List[OrchestratorResult]: List of orchestrator results.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    # Initialize components
    prompt_builder = get_prompt_builder("msa")
    llm_config = LLMConfig(
        provider="openai",
        api_key=api_key,
        extra={"model": "gpt-4o"}
    )
    llm_provider = get_provider("openai")(llm_config)
    memory = RuleMemory(min_score_threshold=0.7)
    feedback_client = FeedbackClient()
    
    config = OrchestratorConfig(
        max_iterations=3,
        convergence_threshold=0.95,
        verbose=True,
    )
    
    orchestrator = LoopOrchestrator(
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        memory=memory,
        feedback_client=feedback_client,
        config=config,
    )
    
    # Prepare batch: first 3 fluents
    fluent_configs = [
        {
            "fluent_name": f["fluent_name"],
            "activity_description": f["description"],
            "ground_truth": f.get("prolog", None),
            "prerequisites": f.get("prerequisites", None)
        }
        for f in msa_requests
    ]
    
    # Run batch
    results = orchestrator.run_batch(fluent_configs)
    
    # Summary
    print(f"\n{'='*60}")
    print("BATCH SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✓" if r.converged else "✗"
        print(f"  {status} {r.fluent_name}: {r.best_score:.4f} ({r.statistics.total_iterations} iterations)")
    
    return results

def run_har_experiment():
    """
    Run the orchestrator for the HAR domain.

    Returns:
        List[OrchestratorResult]: List of orchestrator results.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    # Initialize components
    prompt_builder = get_prompt_builder("har")
    llm_config = LLMConfig(
        provider="openai",
        api_key=api_key,
        extra={"model": "gpt-4o"}
    )
    llm_provider = get_provider("openai")(llm_config)
    memory = RuleMemory(min_score_threshold=0.7)
    feedback_client = FeedbackClient()
    
    config = OrchestratorConfig(
        max_iterations=3,
        convergence_threshold=0.95,
        verbose=True,
    )
    
    orchestrator = LoopOrchestrator(
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        memory=memory,
        feedback_client=feedback_client,
        config=config,
    )
    
    # Prepare batch: first 3 fluents
    fluent_configs = [
        {
            "fluent_name": f["fluent_name"],
            "activity_description": f["description"],
            "ground_truth": f.get("prolog", None),
            "prerequisites": f.get("prerequisites", None)
        }
        for f in har_requests
    ]
    
    # Run batch
    results = orchestrator.run_batch(fluent_configs)
    
    # Summary
    print(f"\n{'='*60}")
    print("BATCH SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✓" if r.converged else "✗"
        print(f"  {status} {r.fluent_name}: {r.best_score:.4f} ({r.statistics.total_iterations} iterations)")
    
    return results


if __name__ == "__main__":
    # Run single fluent example
    #main()
    
    # Uncomment to run batch example:
    run_msa_experiment()

