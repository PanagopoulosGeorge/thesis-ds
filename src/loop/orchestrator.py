import logging
import re

from typing import Optional, Tuple, List, Dict

from src.core.models import (
    EvaluationResult,
    FinalResult,
    LoopConfig,
    LoopState,
    LLMResponse
)

from src.prompts.builder import BasePromptBuilder
from src.simlp.client import SimLPClient
from src.llm.provider_base import BaseLLMProvider
from src.loop.logging_config import OrchestratorLogger

# Default logger (will be replaced if custom logger provided)
logger = logging.getLogger(__name__)

class LoopOrchestrator:
    """
    Orchestrates the feedback loop for iterative RTEC rule generation.
    
    Algorithm (from thesis):
    1. messages = builder.build_initial(activity)
    2. rules = llm.generate(messages)
    3. eval = simlp.evaluate(rules, reference)
    4. while eval.similarity < threshold and attempts < max_attempts:
         a. messages = builder.build_refinement(activity, rules, eval.feedback, attempt)
         b. rules = llm.generate(messages)
         c. eval = simlp.evaluate(rules, reference)
    5. return FinalResult(rules, evaluations, state)
    """

    def __init__(
        self,
        prompt_builder: BasePromptBuilder,
        llm_provider: BaseLLMProvider, 
        simlp_client: SimLPClient,
        config: LoopConfig,
        logger: Optional[logging.Logger] = None,
        verbose: bool = False,
        log_file: Optional[str] = None,
        log_dir: Optional[str] = None
    ):
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider
        self.simlp_client = simlp_client
        self.config = config
        self.current_iteration = 0
        self.history: List[LoopState] = []
        
        # Set up logging
        if logger:
            self.logger = logger
            self._logger_config = None
        else:
            self._logger_config = OrchestratorLogger(
                name="orchestrator",
                log_level="DEBUG" if verbose else "INFO",
                log_file=log_file,
                log_dir=log_dir,
                verbose=verbose
            )
            self.logger = self._logger_config.get_logger()

    def _generate_initial_rules(self, activity: str) -> Tuple[str, LLMResponse]:
        """
        Generate initial rules for an activity.
        
        Steps:
        1. Build the initial prompt using self.prompt_builder
        2. Call the LLM provider to generate
        3. Extract rules from the response
        4. Validate rules are not empty
        5. Return (rules, response)
        
        Raises:
            ValueError: If response is empty
        """
        self.logger.debug(f"Building initial prompt for activity: {activity}")
        prompt = self.prompt_builder.build_initial(activity)
        
        self.logger.debug("Calling LLM to generate initial rules...")
        # Handle both message list and string prompts (for testing flexibility)
        if isinstance(prompt, list):
            response = self.llm_provider.generate_from_messages(
                messages=prompt,
                model="gpt-4",  
                temperature=0.7,
                max_tokens=2048
            )
        else:
            # Mock scenario or simple string prompt
            response = self.llm_provider.generate(prompt)
        
        self.logger.debug(
            f"LLM response received: {response.tokens_used} tokens, "
            f"{response.latency_ms:.2f} ms"
        )
        
        rules = self._extract_rules_from_response(response)

        if not rules or not rules.strip():
            self.logger.error("LLM returned empty response")
            raise ValueError("LLM returned empty response")
        
        self.logger.debug(f"Extracted {len(rules)} characters of rules")
        return rules, response
    
    def _refine_rules(
        self,
        activity: str,
        previous_rules: str,
        feedback: str,
        attempt: int
    ) -> Tuple[str, LLMResponse]:
        """
        Refine rules based on feedback.
        
        Steps:
        1. Build refinement prompt
        2. Call LLM to generate refined rules
        3. Extract rules from response
        4. Validate rules are not empty
        5. Return (rules, response)
        
        Raises:
            ValueError: If response is empty
        """
        self.logger.debug(
            f"Building refinement prompt for activity: {activity}, "
            f"attempt: {attempt}"
        )
        self.logger.debug(f"Feedback length: {len(feedback)} characters")
        
        prompt = self.prompt_builder.build_refinement(
            activity=activity,
            prev_rules=previous_rules,
            feedback=feedback,
            attempt=attempt
        )
        
        self.logger.debug("Calling LLM to generate refined rules...")
        # Handle both message list and string prompts (for testing flexibility)
        if isinstance(prompt, list):
            response = self.llm_provider.generate_from_messages(
                messages=prompt,
                model="gpt-4",
                temperature=0.7,
                max_tokens=2048
            )
        else:
            # Mock scenario or simple string prompt
            response = self.llm_provider.generate(prompt)
        
        self.logger.debug(
            f"LLM response received: {response.tokens_used} tokens, "
            f"{response.latency_ms:.2f} ms"
        )
        
        rules = self._extract_rules_from_response(response)
        
        if not rules or not rules.strip():
            self.logger.error("LLM returned empty response during refinement")
            raise ValueError(
                f"LLM returned empty response during refinement "
                f"(attempt {attempt})"
            )
        
        self.logger.debug(f"Extracted {len(rules)} characters of refined rules")
        
        return rules, response

    def run(self, domain: str, activity: str) -> FinalResult:
        """
        Execute the feedback loop for a given activity.
        
        Args:
            domain: Domain name (e.g., "MSA", "HAR")
            activity: Activity name (e.g., "active", "walking")
            
        Returns:
            FinalResult containing best rules, evaluations, and statistics
            
        Raises:
            ValueError: If LLM returns empty response
            Exception: If LLM or SimLP operations fail
        """
        # Reset state for new run
        self.current_iteration = 0
        self.history = []
        
        self.logger.info("=" * 80)
        self.logger.info(
            f"Starting feedback loop for {domain}/{activity}"
        )
        self.logger.info(f"  Max iterations: {self.config.max_iterations}")
        self.logger.info(f"  Convergence threshold: {self.config.convergence_threshold}")
        self.logger.info("=" * 80)
        
        # Step 1: Generate initial rules
        self.logger.info("ITERATION 1: Generating initial rules...")
        rules, response = self._generate_initial_rules(activity)
        
        # Step 2: Evaluate initial rules
        self.logger.info("Evaluating initial rules...")
        evaluation = self._evaluate_rules(domain, activity, rules)
        
        # Step 3: Record first iteration
        self.current_iteration = 1
        self._record_iteration(response, evaluation, rules)
        
        # Step 4: Check if we converged immediately
        should_continue, reason = self._should_continue(
            self.current_iteration,
            evaluation,
            [evaluation]
        )
        
        self.logger.info(
            f"Iteration 1 complete: score={evaluation.score:.4f}, "
            f"converged={not should_continue}"
        )
        if evaluation.issues:
            self.logger.debug(f"Issues found: {', '.join(evaluation.issues)}")
        if evaluation.feedback:
            self.logger.debug(f"Feedback: {evaluation.feedback[:150]}...")
        
        # Step 5: Refinement loop
        while should_continue:
            self.current_iteration += 1
            
            self.logger.info(
                f"\nITERATION {self.current_iteration}: Refining rules..."
            )
            
            # Generate refined rules
            rules, response = self._refine_rules(
                activity,
                rules,
                evaluation.feedback,
                self.current_iteration
            )
            
            # Evaluate refined rules
            self.logger.info("Evaluating refined rules...")
            evaluation = self._evaluate_rules(domain, activity, rules)
            
            # Record iteration
            self._record_iteration(response, evaluation, rules)
            
            # Check convergence
            all_evaluations = [
                state.evaluations[0] for state in self.history
            ]
            should_continue, reason = self._should_continue(
                self.current_iteration,
                evaluation,
                all_evaluations
            )
            
            self.logger.info(
                f"Iteration {self.current_iteration} complete: "
                f"score={evaluation.score:.4f}, converged={not should_continue}"
            )
            if evaluation.issues:
                self.logger.debug(f"Issues found: {', '.join(evaluation.issues)}")
            if evaluation.feedback:
                self.logger.debug(f"Feedback: {evaluation.feedback[:150]}...")
        
        # Step 6: Build final result
        result = self._build_final_result(reason)
        
        # Log completion summary
        self.logger.info("\n" + "=" * 80)
        self.logger.info("FEEDBACK LOOP COMPLETED")
        self.logger.info("=" * 80)
        self.logger.info(f"Reason: {reason}")
        self.logger.info(f"Converged: {result.summary['converged']}")
        self.logger.info(f"Iterations used: {result.summary['iterations_used']}")
        self.logger.info(f"Final score: {result.summary['final_score']:.4f}")
        self.logger.info(f"Best score: {result.summary['best_score']:.4f}")
        self.logger.info(f"Improvement: {result.summary['improvement']:.4f}")
        self.logger.info(f"Total tokens: {result.summary['total_tokens']}")
        self.logger.info(
            f"Average latency: {result.summary['avg_latency_ms']:.2f} ms"
        )
        self.logger.info("=" * 80)
        
        return result
    
    def _evaluate_rules(
        self,
        domain: str,
        activity: str,
        rules: str
    ) -> EvaluationResult:
        """
        Evaluate rules using SimLP.
        
        Args:
            domain: Domain name
            activity: Activity name
            rules: Generated rules to evaluate
            
        Returns:
            EvaluationResult from SimLP
        """
        self.logger.debug(f"Calling SimLP to evaluate rules for {domain}/{activity}")
        evaluation = self.simlp_client.evaluate(
            domain=domain,
            activity=activity,
            generated_rules=rules,
            generate_feedback=True
        )
        
        self.logger.debug(
            f"Evaluation complete: score={evaluation.score:.4f}, "
            f"matches_reference={evaluation.matches_reference}"
        )
        
        return evaluation
    
    def _should_continue(
        self,
        iteration: int,
        current_eval: EvaluationResult,
        history: List[EvaluationResult]
    ) -> Tuple[bool, str]:
        """
        Determine if the loop should continue iterating.
        
        Convergence criteria:
        1. Similarity score >= threshold → converged
        2. Iteration >= max_iterations → stop (not converged)
        3. Perfect score (1.0) → converged
        
        Args:
            iteration: Current iteration number
            current_eval: Current evaluation result
            history: List of all evaluation results
            
        Returns:
            Tuple of (should_continue, reason)
        """
        # Check max iterations
        if iteration >= self.config.max_iterations:
            reason = (
                f"Reached maximum iterations "
                f"({self.config.max_iterations})"
            )
            return False, reason
        
        # Check convergence threshold
        if current_eval.score >= self.config.convergence_threshold:
            reason = (
                f"Converged (score={current_eval.score:.2f} >= "
                f"{self.config.convergence_threshold})"
            )
            return False, reason
        
        # Perfect score always converges
        if current_eval.score >= 1.0:
            return False, "Perfect score achieved"
        
        # Continue iterating
        return True, "Below convergence threshold"
    
    def _record_iteration(
        self,
        response: LLMResponse,
        evaluation: EvaluationResult,
        rules: str
    ):
        """
        Record the current iteration's state.
        
        Args:
            response: LLM response from this iteration
            evaluation: Evaluation result from this iteration
        """
        # Determine if this iteration converged
        converged = evaluation.score >= self.config.convergence_threshold
        
        # Create state record
        state = LoopState(
            iteration=self.current_iteration,
            pending_requests=[],
            completed_requests=[response],
            rules = rules,
            evaluations=[evaluation],
            converged=converged,
            notes=(
                f"Iteration {self.current_iteration}: "
                f"score={evaluation.score:.2f}"
            )
        )
        
        self.history.append(state)
    
    def _extract_rules_from_response(self, response: LLMResponse) -> str:
        """
        Extract RTEC rules from LLM response content.
        
        The LLM may include explanatory text along with the rules.
        This method extracts and concatenates all Prolog code blocks.
        
        Args:
            response: LLM response object
            
        Returns:
            Extracted rules as string (all code blocks concatenated)
        """
        content = response.content
        
        # Extract all code blocks (prolog, pl, or unmarked)
        code_block_pattern = r'```(?:prolog|pl|erlang)?\s*(.*?)```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        if matches:
            # Concatenate all code blocks with double newline separator
            extracted = '\n\n'.join(match.strip() for match in matches)
            self.logger.debug(
                f"Extracted {len(matches)} code block(s), "
                f"total {len(extracted)} chars"
            )
            return extracted
        
        # If no code blocks, look for Prolog rule patterns
        # Match multi-line rules: predicate(...) :- body.
        rule_pattern = (
            r'((?:initiatedAt|terminatedAt|holdsAt|happensAt|'
            r'fi|grounding)\s*\([^)]*\)[^.]*\.)'
        )
        rules = re.findall(rule_pattern, content, re.DOTALL)
        if rules:
            extracted = '\n\n'.join(rule.strip() for rule in rules)
            self.logger.debug(
                f"Extracted {len(rules)} Prolog rule(s) using pattern matching"
            )
            return extracted
        
        # If no patterns match, return full content
        self.logger.warning(
            "No code blocks or Prolog patterns found, returning full content"
        )
        return content.strip()
    
    def _build_final_result(self, completion_reason: str) -> FinalResult:
        """
        Build the final result object with statistics.
        
        Args:
            completion_reason: Reason for loop completion
            
        Returns:
            FinalResult with all data and statistics
        """
        # Find best iteration
        all_evals = [state.evaluations[0] for state in self.history]
        best_eval = max(all_evals, key=lambda e: e.score)
        best_idx = all_evals.index(best_eval)
        
        # Get best rules
        best_response = self.history[best_idx].completed_requests[0]
        best_rules = self._extract_rules_from_response(best_response)
        
        # Calculate statistics
        total_tokens = sum(
            resp.tokens_used
            for state in self.history
            for resp in state.completed_requests
        )
        
        total_latency = sum(
            resp.latency_ms
            for state in self.history
            for resp in state.completed_requests
        )
        
        avg_latency = (
            total_latency / len(self.history) if self.history else 0
        )
        avg_tokens = total_tokens / len(self.history) if self.history else 0
        
        first_score = all_evals[0].score
        final_score = all_evals[-1].score
        improvement = final_score - first_score
        improvement_rate = (
            improvement / (len(self.history) - 1)
            if len(self.history) > 1
            else 0
        )
        
        # Build summary
        summary = {
            'iterations_used': len(self.history),
            'converged': self.history[-1].converged,
            'final_score': round(final_score, 10),
            'best_score': round(best_eval.score, 10),
            'best_iteration': best_idx + 1,
            'total_tokens': total_tokens,
            'avg_tokens_per_iteration': round(avg_tokens, 2),
            'total_latency_ms': round(total_latency, 2),
            'avg_latency_ms': round(avg_latency, 2),
            'improvement': round(improvement, 10),
            'improvement_rate': round(improvement_rate, 10),
        }
        
        # Build final result
        result = FinalResult(
            config=self.config,
            states=self.history,
            best_rules=[best_rules],
            evaluations=all_evals,
            summary=summary,
            notes=completion_reason,
            metadata={}
        )
        
        return result
    