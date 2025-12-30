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


def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return
    
    # =========================================================
    # Step 1: Initialize Components
    # =========================================================
    
    # Prompt builder for Maritime Situational Awareness domain
    prompt_builder = get_prompt_builder("msa")
    
    # LLM provider (OpenAI)
    llm_config = LLMConfig(
        provider="openai",
        api_key=api_key,
        extra={"model": "gpt-4o"}
    )
    provider_class = get_provider("openai")
    llm_provider = provider_class(llm_config)
    
    # Memory for storing validated fluents
    memory = RuleMemory(min_score_threshold=0.95)
    
    # Feedback client for SimLP evaluation
    feedback_client = FeedbackClient(log_file="logs/orchestrator_feedback.log")
    
    # Orchestrator configuration
    config = OrchestratorConfig(
        max_iterations=3,
        convergence_threshold=0.95,
        early_stopping=True,
        early_stopping_patience=2,
        verbose=True,
    )
    
    # =========================================================
    # Step 2: Create Orchestrator
    # =========================================================
    
    orchestrator = LoopOrchestrator(
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        memory=memory,
        feedback_client=feedback_client,
        config=config,
    )
    
    # =========================================================
    # Step 3: Run for a Single Fluent
    # =========================================================
    
    # Get the first MSA request (gap fluent)
    fluent = msa_requests[0]
    
    print(f"\n{'='*60}")
    print(f"Running feedback loop for: {fluent['fluent_name']}")
    print(f"{'='*60}\n")
    
    result = orchestrator.run(
        fluent_name=fluent['fluent_name'],
        activity_description=fluent['description'],
        ground_truth=fluent['prolog'],
    )
    
    # =========================================================
    # Step 4: Review Results
    # =========================================================
    
    print(f"\n{'='*60}")
    print("FINAL RESULT")
    print(f"{'='*60}")
    print(result.summary())
    
    print(f"\n{'='*60}")
    print("BEST RULES GENERATED")
    print(f"{'='*60}")
    print(result.best_rules)
    
    print(f"\n{'='*60}")
    print("ITERATION HISTORY")
    print(f"{'='*60}")
    for it in result.iterations:
        print(f"  Iteration {it.iteration}: score={it.similarity_score:.4f}")
    
    # =========================================================
    # Step 5: Check Memory State
    # =========================================================
    
    print(f"\n{'='*60}")
    print("MEMORY STATE")
    print(f"{'='*60}")
    print(f"Stored fluents: {memory.list_fluents()}")
    print(f"Statistics: {memory.get_statistics()}")
    
    return result


def run_batch_example():
    """Example of running multiple fluents in sequence."""
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
        convergence_threshold=0.8,
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
            "ground_truth": f["prolog"],
            "prerequisites": None,  # First fluents have no prerequisites
        }
        for f in msa_requests[:3]
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
    main()
    
    # Uncomment to run batch example:
    # run_batch_example()

