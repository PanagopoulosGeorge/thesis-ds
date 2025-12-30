"""LoopOrchestrator - Main controller for the iterative feedback loop.

Implements Algorithm 1 from the thesis:
1. Generate initial rules using prompt builder + LLM
2. Evaluate rules using SimLP
3. While not converged and iterations < max:
     a. Build refinement prompt with feedback
     b. Generate refined rules
     c. Evaluate refined rules
     d. Check convergence (score >= threshold)
4. Return best rules and statistics
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

import structlog

from src.core.models import (
    FinalResult,
    IterationResult,
    LoopStatistics,
    OrchestratorConfig,
)
from src.feedback.client import FeedbackClient, FeedbackResult
from src.interfaces.llm import LLMProvider
from src.interfaces.models import FewShotExample
from src.interfaces.prompts import PromptBuilder
from src.memory.rule_memory import RuleMemory
from src.utils.code_extractor import extract_rules_from_response


logger = structlog.get_logger(__name__)


class LoopOrchestrator:
    """Main controller for iterative RTEC rule generation with feedback.
    
    Orchestrates the feedback loop by coordinating:
    - Prompt building (domain-specific prompts)
    - LLM generation (rule synthesis)
    - Evaluation (SimLP similarity scoring)
    - Refinement (feedback injection)
    - Memory (storing validated fluents)
    
    Example:
        >>> from src.prompts.factory import get_prompt_builder
        >>> from src.llm.factory import get_provider
        >>> 
        >>> builder = get_prompt_builder("msa")
        >>> provider = get_provider("openai")(config)
        >>> memory = RuleMemory()
        >>> 
        >>> orchestrator = LoopOrchestrator(
        ...     prompt_builder=builder,
        ...     llm_provider=provider,
        ...     memory=memory,
        ... )
        >>> 
        >>> result = orchestrator.run(
        ...     fluent_name="gap",
        ...     activity_description="A communication gap starts when...",
        ...     ground_truth="initiatedAt(gap(Vessel)=nearPorts, T) :- ...",
        ... )
        >>> print(result.summary())
    """
    
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        memory: Optional[RuleMemory] = None,
        feedback_client: Optional[FeedbackClient] = None,
        config: Optional[OrchestratorConfig] = None,
    ):
        """Initialize the orchestrator.
        
        Args:
            prompt_builder: Domain-specific prompt builder (e.g., MSAPromptBuilder)
            llm_provider: LLM provider for rule generation (e.g., OpenAILLMProvider)
            memory: RuleMemory for storing/retrieving validated fluents
            feedback_client: Client for SimLP evaluation and feedback
            config: Orchestrator configuration (iterations, thresholds)
        """
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider
        self.memory = memory or RuleMemory()
        self.feedback_client = feedback_client or FeedbackClient()
        self.config = config or OrchestratorConfig()
        
        logger.info(
            "LoopOrchestrator initialized",
            domain=prompt_builder.domain_name,
            max_iterations=self.config.max_iterations,
            convergence_threshold=self.config.convergence_threshold,
        )
    
    def run(
        self,
        fluent_name: str,
        activity_description: str,
        ground_truth: str,
        prerequisites: Optional[List[str]] = None,
    ) -> FinalResult:
        """Execute the feedback loop for a single fluent.
        
        Args:
            fluent_name: Name of the fluent to generate (e.g., "gap")
            activity_description: Natural language description of the activity
            ground_truth: Ground truth RTEC rules for evaluation
            prerequisites: List of fluent names to retrieve from memory
            
        Returns:
            FinalResult containing best rules, history, and statistics
        """
        started_at = datetime.utcnow()
        iterations: List[IterationResult] = []
        
        # Track best result across all iterations
        best_rules = ""
        best_score = 0.0
        best_iteration = 0
        
        # Early stopping tracking
        no_improvement_count = 0
        
        logger.info(
            "Starting feedback loop",
            fluent_name=fluent_name,
            max_iterations=self.config.max_iterations,
            threshold=self.config.convergence_threshold,
        )
        
        # Prepare prerequisites from memory
        prerequisite_examples = self._get_prerequisites(prerequisites)
        
        # Current feedback (None for first iteration)
        current_feedback: Optional[str] = None
        
        for iteration in range(1, self.config.max_iterations + 1):
            logger.info(f"=== Iteration {iteration} ===")
            
            # Step 1: Build prompt
            request = self.prompt_builder.build_prompt(
                activity_description=activity_description,
                prerequisites=prerequisite_examples,
                feedback=current_feedback,
            )
            
            # Step 2: Generate rules
            raw_response = self.llm_provider.generate(request)
            
            # Step 2b: Extract Prolog code from LLM response
            generated_rules = extract_rules_from_response(raw_response)
            
            if self.config.verbose:
                logger.debug(
                    "Extracted rules from response",
                    raw_length=len(raw_response),
                    extracted_length=len(generated_rules),
                    rules_preview=generated_rules[:200] + "..." if len(generated_rules) > 200 else generated_rules,
                )
            
            # Step 3: Evaluate with SimLP
            eval_result = self.feedback_client.evaluate(
                generated_rules=generated_rules,
                ground_truth_rules=ground_truth,
                generate_feedback=True,
            )
            
            score = eval_result.similarity
            
            logger.info(
                "Evaluation complete",
                iteration=iteration,
                score=f"{score:.4f}",
                previous_best=f"{best_score:.4f}",
            )
            
            # Step 4: Record iteration result
            iteration_result = IterationResult(
                iteration=iteration,
                generated_rules=generated_rules,
                similarity_score=score,
                feedback=self.feedback_client.render_feedback(eval_result),
                optimal_matching=eval_result.optimal_matching,
                distances=eval_result.distances,
            )
            iterations.append(iteration_result)
            
            # Step 5: Update best if improved
            if score > best_score:
                best_rules = generated_rules
                best_score = score
                best_iteration = iteration
                no_improvement_count = 0
                logger.info(f"New best score: {score:.4f}")
            else:
                no_improvement_count += 1
            
            # Step 6: Check convergence
            if score >= self.config.convergence_threshold:
                logger.info(
                    "Converged!",
                    score=f"{score:.4f}",
                    threshold=self.config.convergence_threshold,
                )
                break
            
            # Step 7: Check early stopping
            if (
                self.config.early_stopping 
                and no_improvement_count >= self.config.early_stopping_patience
            ):
                logger.info(
                    "Early stopping triggered",
                    patience=self.config.early_stopping_patience,
                )
                break
            
            # Step 8: Prepare feedback for next iteration
            current_feedback = self.feedback_client.render_feedback(eval_result)
        
        completed_at = datetime.utcnow()
        
        # Calculate statistics
        statistics = LoopStatistics(
            total_iterations=len(iterations),
            initial_score=iterations[0].similarity_score if iterations else 0.0,
            final_score=iterations[-1].similarity_score if iterations else 0.0,
            best_score=best_score,
            best_iteration=best_iteration,
        )
        
        # Build final result
        result = FinalResult(
            fluent_name=fluent_name,
            domain=self.prompt_builder.domain_name,
            best_rules=best_rules,
            best_score=best_score,
            best_iteration=best_iteration,
            converged=best_score >= self.config.convergence_threshold,
            convergence_threshold=self.config.convergence_threshold,
            max_iterations=self.config.max_iterations,
            iterations=iterations,
            statistics=statistics,
            started_at=started_at,
            completed_at=completed_at,
        )
        
        # Store in memory if score meets threshold
        if best_score >= self.memory.min_score_threshold:
            self.memory.add_entry(
                fluent_name=fluent_name,
                rules=best_rules,
                score=best_score,
                natural_language_description=activity_description,
            )
        
        if self.config.verbose:
            print(result.summary())
        
        return result
    
    def run_batch(
        self,
        fluent_configs: List[Dict[str, Any]],
        stop_on_failure: bool = False,
    ) -> List[FinalResult]:
        """Run the feedback loop for multiple fluents in sequence.
        
        Processes fluents in order, building up memory as each is completed.
        Later fluents can use earlier ones as prerequisites.
        
        Args:
            fluent_configs: List of dicts with keys:
                - fluent_name: str
                - activity_description: str
                - ground_truth: str
                - prerequisites: Optional[List[str]]
            stop_on_failure: Whether to stop if a fluent fails to converge
            
        Returns:
            List of FinalResult for each fluent
        """
        results: List[FinalResult] = []
        
        logger.info(
            "Starting batch run",
            total_fluents=len(fluent_configs),
        )
        
        for i, config in enumerate(fluent_configs, 1):
            logger.info(
                f"Processing fluent {i}/{len(fluent_configs)}",
                fluent_name=config["fluent_name"],
            )
            
            result = self.run(
                fluent_name=config["fluent_name"],
                activity_description=config["activity_description"],
                ground_truth=config["ground_truth"],
                prerequisites=config.get("prerequisites"),
            )
            
            results.append(result)
            
            if stop_on_failure and not result.converged:
                logger.warning(
                    "Stopping batch due to failure",
                    fluent_name=config["fluent_name"],
                    score=result.best_score,
                )
                break
        
        # Log batch summary
        converged = sum(1 for r in results if r.converged)
        avg_score = sum(r.best_score for r in results) / len(results) if results else 0
        
        logger.info(
            "Batch complete",
            total=len(results),
            converged=converged,
            avg_score=f"{avg_score:.4f}",
        )
        
        return results
    
    def _get_prerequisites(
        self,
        fluent_names: Optional[List[str]],
    ) -> Optional[List[FewShotExample]]:
        """Retrieve prerequisite fluents from memory as few-shot examples.
        
        Args:
            fluent_names: List of fluent names to retrieve
            
        Returns:
            List of FewShotExample for injection into prompts, or None
        """
        if not fluent_names:
            return None
        
        examples: List[FewShotExample] = []
        
        for name in fluent_names:
            entry = self.memory.get_entry(name)
            if entry:
                examples.append(FewShotExample(
                    user=entry.natural_language_description or f"Generate rules for {name}",
                    assistant=entry.rules,
                ))
            else:
                logger.warning(
                    "Prerequisite not found in memory",
                    fluent_name=name,
                    available=self.memory.list_fluents(),
                )
        
        return examples if examples else None

