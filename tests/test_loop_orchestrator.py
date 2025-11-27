"""
Comprehensive test suite for LoopOrchestrator.

This module tests the core feedback loop logic including:
- Initial rule generation
- Iterative refinement with feedback
- Convergence detection
- Error handling and recovery
- State management across iterations
"""

import pytest
from unittest.mock import Mock, patch, call

from typing import List

from src.core.models import (
    LLMResponse,
    EvaluationResult,
    LoopConfig,
    LoopState,
    FinalResult
)
from src.core.rule_memory import RuleMemory
from src.loop.orchestrator import LoopOrchestrator


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_prompt_builder():
    """Mock prompt builder that returns predictable prompts."""
    builder = Mock()
    builder.build_initial.return_value = "Initial prompt for activity"
    builder.build_refinement.return_value = (
        "Refinement prompt with feedback"
    )
    builder.get_activity_description.return_value = "Mock activity description."
    return builder



@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider that returns configurable responses."""
    provider = Mock()
    return provider



@pytest.fixture
def mock_simlp_client():
    """Mock SimLP client that returns configurable evaluations."""
    client = Mock()
    return client



@pytest.fixture
def basic_config():
    """Basic loop configuration for testing."""
    return LoopConfig(
        provider="openai",
        objective="Generate RTEC rules for activity recognition",
        max_iterations=5,
        convergence_threshold=0.9,
        batch_size=1,
        retry_limit=3
    )



@pytest.fixture
def orchestrator(
    mock_prompt_builder,
    mock_llm_provider,
    mock_simlp_client,
    basic_config
):
    """Fully configured orchestrator with mocked dependencies."""
    return LoopOrchestrator(
        prompt_builder=mock_prompt_builder,
        llm_provider=mock_llm_provider,
        simlp_client=mock_simlp_client,
        config=basic_config,
        rule_memory=RuleMemory(),
    )


def create_llm_response(
    content: str,
    request_id: str = "test-req-1",
    tokens: int = 100,
    latency: float = 500.0
) -> LLMResponse:
    """Helper to create LLM responses."""
    return LLMResponse(
        request_id=request_id,
        provider="openai",
        model="gpt-4",
        content=content,
        tokens_used=tokens,
        latency_ms=latency,
        finish_reason="stop",
        raw={}
    )


def create_evaluation(
    score: float,
    matches: bool,
    feedback: str = "",
    issues: List[str] = None
) -> EvaluationResult:
    """Helper to create evaluation results."""
    return EvaluationResult(
        rule_id="test-rule-1",
        score=score,
        matches_reference=matches,
        feedback=feedback,
        issues=issues or [],
        metadata={"iteration": 1}
    )


# ============================================================================
# TEST CLASS 1: INITIALIZATION
# ============================================================================



class TestLoopOrchestratorInitialization:
    """Test orchestrator initialization and configuration."""
    
    def test_initialization_with_all_components(
        self,
        mock_prompt_builder,
        mock_llm_provider,
        mock_simlp_client,
        basic_config
    ):
        """Test that orchestrator initializes with all required components."""
        orchestrator = LoopOrchestrator(
            prompt_builder=mock_prompt_builder,
            llm_provider=mock_llm_provider,
            simlp_client=mock_simlp_client,
            config=basic_config
        )
        
        assert orchestrator.prompt_builder == mock_prompt_builder
        assert orchestrator.llm_provider == mock_llm_provider
        assert orchestrator.simlp_client == mock_simlp_client
        assert orchestrator.config == basic_config
    
    def test_initialization_with_custom_config(
        self,
        mock_prompt_builder,
        mock_llm_provider,
        mock_simlp_client
    ):
        """Test initialization with custom configuration values."""
        config = LoopConfig(
            provider="anthropic",
            objective="Custom objective",
            max_iterations=10,
            convergence_threshold=0.95,
            batch_size=2,
            retry_limit=5
        )
        
        orchestrator = LoopOrchestrator(
            prompt_builder=mock_prompt_builder,
            llm_provider=mock_llm_provider,
            simlp_client=mock_simlp_client,
            config=config
        )
        
        assert orchestrator.config.max_iterations == 10
        assert orchestrator.config.convergence_threshold == 0.95
        assert orchestrator.config.retry_limit == 5
    
    def test_orchestrator_starts_with_empty_state(self, orchestrator):
        """Test that orchestrator starts with no execution history."""
        # Should be able to check initial state
        assert orchestrator.current_iteration == 0
        assert orchestrator.history == []


# ============================================================================
# TEST CLASS 2: HAPPY PATH - IMMEDIATE CONVERGENCE
# ============================================================================



class TestImmediateConvergence:
    """Test cases where rules are perfect on the first attempt."""
    
    def test_perfect_rules_on_first_try(self, orchestrator):
        """
        Test convergence on first iteration when rules are perfect.
        
        Scenario:
        1. Generate initial rules
        2. Evaluate: similarity = 1.0 (perfect match)
        3. Stop immediately without refinement
        """
        # Setup: LLM returns perfect rules
        perfect_rules = """
        initiatedAt(active(P), T) :-
            happensAt(start_activity(P), T).
        """
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content=perfect_rules
        )
        
        # Setup: SimLP returns perfect score
        orchestrator.simlp_client.evaluate.return_value = create_evaluation(
            score=1.0,
            matches=True,
            feedback="Perfect match!"
        )
        
        # Execute
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Only one iteration occurred
        assert orchestrator.llm_provider.generate.call_count == 1
        assert orchestrator.simlp_client.evaluate.call_count == 1
        
        # Verify: Result structure
        assert isinstance(result, FinalResult)
        assert len(result.states) == 1
        assert result.states[0].converged is True
        assert result.states[0].iteration == 1
        
        # Verify: Final rules match generated rules
        assert perfect_rules.strip() in result.best_rules[0]
        
        # Verify: Evaluation recorded
        assert len(result.evaluations) == 1
        assert result.evaluations[0].score == 1.0
    
    def test_high_similarity_triggers_convergence(self, orchestrator):
        """
        Test that similarity >= threshold triggers convergence.
        
        Scenario:
        1. Generate rules
        2. Evaluate: similarity = 0.92 (>= 0.9 threshold)
        3. Stop without refinement
        """
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Good rules"
        )
        
        orchestrator.simlp_client.evaluate.return_value = create_evaluation(
            score=0.92,
            matches=True,
            feedback="Very close match"
        )
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Should converge immediately
        assert orchestrator.llm_provider.generate.call_count == 1
        assert result.states[0].converged is True
        assert result.evaluations[0].score == 0.92


# ============================================================================
# TEST CLASS 3: ITERATIVE REFINEMENT
# ============================================================================



class TestIterativeRefinement:
    """Test cases requiring multiple refinement iterations."""
    
    def test_convergence_after_two_iterations(self, orchestrator):
        """
        Test convergence after one refinement cycle.
        
        Scenario:
        Iteration 1: similarity = 0.6 (below threshold) → refine
        Iteration 2: similarity = 0.95 (above threshold) → converge
        """
        # Setup: Different responses for each iteration
        iter1_rules = "initiatedAt(active(P), T) :- happensAt(start(P), T)."
        iter2_rules = "initiatedAt(active(P), T) :- happensAt(start_activity(P), T)."
        
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content=iter1_rules, request_id="req-1"),
            create_llm_response(content=iter2_rules, request_id="req-2")
        ]
        
        # Setup: Improving evaluations
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(
                score=0.6,
                matches=False,
                feedback="Predicate name mismatch",
                issues=["Use 'start_activity' instead of 'start'"]
            ),
            create_evaluation(
                score=0.95,
                matches=True,
                feedback="Excellent match"
            )
        ]
        
        # Execute
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Two iterations occurred
        assert orchestrator.llm_provider.generate.call_count == 2
        assert orchestrator.simlp_client.evaluate.call_count == 2
        
        # Verify: Refinement was called once
        orchestrator.prompt_builder.build_refinement.assert_called_once()
        
        # Verify: Refinement received correct parameters
        call_args = orchestrator.prompt_builder.build_refinement.call_args
        assert call_args[1]['activity'] == 'active'
        assert call_args[1]['prev_rules'] == iter1_rules
        assert 'Predicate name mismatch' in call_args[1]['feedback']
        assert call_args[1]['attempt'] == 2
        
        # Verify: Final state
        assert len(result.states) == 2
        assert result.states[0].converged is False
        assert result.states[1].converged is True
        
        # Verify: Best rules are from iteration 2
        assert iter2_rules in result.best_rules[0]
    
    def test_convergence_after_multiple_iterations(self, orchestrator):
        """
        Test convergence after several refinement cycles.
        
        Scenario:
        Iteration 1: 0.4 → refine
        Iteration 2: 0.6 → refine
        Iteration 3: 0.8 → refine
        Iteration 4: 0.93 → converge
        """
        # Setup: Progressive improvement
        responses = [
            create_llm_response(content=f"Rules v{i}", request_id=f"req-{i}")
            for i in range(1, 5)
        ]
        orchestrator.llm_provider.generate.side_effect = responses
        
        evaluations = [
            create_evaluation(score=0.4, matches=False, feedback="Poor match"),
            create_evaluation(score=0.6, matches=False, feedback="Improved"),
            create_evaluation(score=0.8, matches=False, feedback="Better"),
            create_evaluation(score=0.93, matches=True, feedback="Excellent")
        ]
        orchestrator.simlp_client.evaluate.side_effect = evaluations
        
        # Execute
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Four iterations
        assert orchestrator.llm_provider.generate.call_count == 4
        assert len(result.states) == 4
        
        # Verify: Progressive improvement in scores
        scores = [state.evaluations[0].score for state in result.states]
        assert scores == [0.4, 0.6, 0.8, 0.93]
        
        # Verify: Only last iteration converged
        convergence = [state.converged for state in result.states]
        assert convergence == [False, False, False, True]
        
        # Verify: Attempt number increases correctly
        refinement_calls = (
            orchestrator.prompt_builder.build_refinement.call_args_list
        )
        assert len(refinement_calls) == 3  # 3 refinements for 4 iterations
        assert refinement_calls[0][1]['attempt'] == 2
        assert refinement_calls[1][1]['attempt'] == 3
        assert refinement_calls[2][1]['attempt'] == 4
    
    def test_feedback_passed_to_next_iteration(self, orchestrator):
        """Test that evaluation feedback is passed to refinement prompt."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="Rules v1"),
            create_llm_response(content="Rules v2")
        ]
        
        specific_feedback = (
            "Missing termination condition. "
            "Add terminatedAt clause for activity completion."
        )
        
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(
                score=0.5,
                matches=False,
                feedback=specific_feedback,
                issues=["Missing terminatedAt clause"]
            ),
            create_evaluation(score=0.95, matches=True)
        ]
        
        # Execute
        orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Feedback was passed to refinement
        call_args = orchestrator.prompt_builder.build_refinement.call_args
        assert call_args[1]['feedback'] == specific_feedback


# ============================================================================
# TEST CLASS 4: MAXIMUM ITERATIONS
# ============================================================================



class TestMaximumIterations:
    """Test behavior when max iterations limit is reached."""
    
    def test_stops_at_max_iterations(self, orchestrator):
        """
        Test that loop stops at max_iterations even without convergence.
        
        Scenario:
        All 5 iterations return similarity = 0.7 (below threshold)
        Should stop after iteration 5 without convergence
        """
        orchestrator.config.max_iterations = 5
        
        # Setup: Constant low similarity
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Mediocre rules"
        )
        orchestrator.simlp_client.evaluate.return_value = create_evaluation(
            score=0.7,
            matches=False,
            feedback="Still not good enough"
        )
        
        # Execute
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Exactly max_iterations calls
        assert orchestrator.llm_provider.generate.call_count == 5
        assert len(result.states) == 5
        
        # Verify: None converged
        assert all(not state.converged for state in result.states)
        
        # Verify: Summary indicates non-convergence
        assert result.summary['converged'] is False
        assert result.summary['final_score'] == 0.7
        assert result.summary['iterations_used'] == 5
    
    def test_returns_best_rules_when_not_converged(self, orchestrator):
        """
        Test that best rules are returned even without convergence.
        
        Scenario:
        Iteration 1: 0.5
        Iteration 2: 0.7 (best)
        Iteration 3: 0.6
        Should return rules from iteration 2
        """
        orchestrator.config.max_iterations = 3
        
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="Rules v1"),
            create_llm_response(content="Rules v2 (best)"),
            create_llm_response(content="Rules v3")
        ]
        
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.7, matches=False),
            create_evaluation(score=0.6, matches=False)
        ]
        
        # Execute
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Best rules are from iteration 2
        assert "best" in result.best_rules[0]
        assert result.summary['best_score'] == 0.7
        assert result.summary['best_iteration'] == 2


# ============================================================================
# TEST CLASS 5: ERROR HANDLING
# ============================================================================



class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    def test_llm_generation_failure_raises_exception(self, orchestrator):
        """Test that LLM generation failures are properly raised."""
        orchestrator.llm_provider.generate.side_effect = Exception(
            "API rate limit exceeded"
        )
        
        with pytest.raises(Exception, match="API rate limit exceeded"):
            orchestrator.run(domain="MSA", activity="active")
    
    def test_simlp_evaluation_failure_raises_exception(self, orchestrator):
        """Test that SimLP evaluation failures are properly raised."""
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Valid rules"
        )
        orchestrator.simlp_client.evaluate.side_effect = Exception(
            "Prolog syntax error"
        )
        
        with pytest.raises(Exception, match="Prolog syntax error"):
            orchestrator.run(domain="MSA", activity="active")
    
    def test_empty_llm_response_handling(self, orchestrator):
        """Test handling of empty LLM responses."""
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content=""
        )
        
        with pytest.raises(ValueError, match="empty.*response"):
            orchestrator.run(domain="MSA", activity="active")
    
    def test_invalid_prolog_syntax_in_response(self, orchestrator):
        """
        Test handling of invalid Prolog syntax from LLM.
        
        Should be caught by SimLP and provide helpful feedback.
        """
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="INVALID SYNTAX {{{"),
            create_llm_response(content="Valid corrected rules")
        ]
        
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(
                score=0.0,
                matches=False,
                feedback="Syntax error: unmatched braces",
                issues=["Fix Prolog syntax errors"]
            ),
            create_evaluation(score=0.95, matches=True)
        ]
        
        # Should recover and succeed
        result = orchestrator.run(domain="MSA", activity="active")
        
        assert len(result.states) == 2
        assert result.states[1].converged is True


# ============================================================================
# TEST CLASS 6: STATE MANAGEMENT
# ============================================================================



class TestStateManagement:
    """Test proper state tracking across iterations."""
    
    def test_iteration_counter_increments_correctly(self, orchestrator):
        """Test that iteration counter increments properly."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content=f"Rules v{i}")
            for i in range(1, 4)
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.7, matches=False),
            create_evaluation(score=0.92, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Iteration numbers
        assert result.states[0].iteration == 1
        assert result.states[1].iteration == 2
        assert result.states[2].iteration == 3
    
    def test_history_preserves_all_iterations(self, orchestrator):
        """Test that full history is preserved."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content=f"Rules v{i}", request_id=f"req-{i}")
            for i in range(1, 4)
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.7, matches=False),
            create_evaluation(score=0.92, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: All responses preserved
        assert len(result.states[0].completed_requests) == 1
        assert len(result.states[1].completed_requests) == 1
        assert len(result.states[2].completed_requests) == 1
        
        # Verify: All evaluations preserved
        assert len(result.evaluations) == 3
        assert [e.score for e in result.evaluations] == [0.5, 0.7, 0.92]
    
    def test_summary_statistics_calculated_correctly(self, orchestrator):
        """Test that summary statistics are accurate."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="v1", tokens=100, latency=500.0),
            create_llm_response(content="v2", tokens=150, latency=600.0),
            create_llm_response(content="v3", tokens=120, latency=550.0)
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.7, matches=False),
            create_evaluation(score=0.93, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Summary calculations
        assert result.summary['iterations_used'] == 3
        assert result.summary['converged'] is True
        assert result.summary['final_score'] == 0.93
        assert result.summary['best_score'] == 0.93
        assert result.summary['best_iteration'] == 3
        assert result.summary['total_tokens'] == 370
        assert result.summary['avg_latency_ms'] == 550.0


# ============================================================================
# TEST CLASS 7: EDGE CASES
# ============================================================================



class TestEdgeCases:
    """Test unusual but valid scenarios."""
    
    def test_oscillating_scores(self, orchestrator):
        """
        Test handling of oscillating similarity scores.
        
        Scenario: Scores go up and down but never converge
        0.7 → 0.8 → 0.7 → 0.85 → 0.75
        """
        orchestrator.config.max_iterations = 5
        
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Oscillating rules"
        )
        
        scores = [0.7, 0.8, 0.7, 0.85, 0.75]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=s, matches=False)
            for s in scores
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Returns best score despite oscillation
        assert result.summary['best_score'] == 0.85
        assert result.summary['best_iteration'] == 4
        assert result.summary['converged'] is False
    
    def test_no_improvement_across_iterations(self, orchestrator):
        """Test when all iterations return same low score."""
        orchestrator.config.max_iterations = 3
        
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Stuck rules"
        )
        orchestrator.simlp_client.evaluate.return_value = create_evaluation(
            score=0.5,
            matches=False,
            feedback="Same issues persist"
        )
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: All scores identical
        scores = [e.score for e in result.evaluations]
        assert scores == [0.5, 0.5, 0.5]
        
        # Verify: Notes indicate stagnation
        assert result.summary['improvement'] == 0.0
    
    def test_single_iteration_config(self, orchestrator):
        """Test with max_iterations = 1."""
        orchestrator.config.max_iterations = 1
        
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Only attempt"
        )
        orchestrator.simlp_client.evaluate.return_value = create_evaluation(
            score=0.6,
            matches=False
        )
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Only one iteration
        assert len(result.states) == 1
        assert orchestrator.prompt_builder.build_refinement.call_count == 0


# ============================================================================
# TEST CLASS 8: CONVERGENCE POLICIES
# ============================================================================



class TestConvergencePolicies:
    """Test different convergence detection strategies."""
    
    def test_threshold_based_convergence(self, orchestrator):
        """Test standard threshold-based convergence."""
        orchestrator.config.convergence_threshold = 0.95
        
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="v1"),
            create_llm_response(content="v2")
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.94, matches=False),
            create_evaluation(score=0.96, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # 0.94 < 0.95, so continues
        # 0.96 >= 0.95, so converges
        assert len(result.states) == 2
        assert result.states[0].converged is False
        assert result.states[1].converged is True
    
    def test_perfect_score_always_converges(self, orchestrator):
        """Test that perfect score (1.0) always triggers convergence."""
        orchestrator.config.convergence_threshold = 0.99  # Very high threshold
        
        orchestrator.llm_provider.generate.return_value = create_llm_response(
            content="Perfect rules"
        )
        orchestrator.simlp_client.evaluate.return_value = create_evaluation(
            score=1.0,
            matches=True
        )
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Should converge immediately despite high threshold
        assert len(result.states) == 1
        assert result.states[0].converged is True


# ============================================================================
# TEST CLASS 9: INTEGRATION SCENARIOS
# ============================================================================



class TestIntegrationScenarios:
    """Test realistic end-to-end scenarios."""
    
    def test_realistic_improvement_pattern(self, orchestrator):
        """
        Test realistic scenario with typical improvement pattern.
        
        Iteration 1: Missing predicates (0.4)
        Iteration 2: Wrong predicate names (0.6)
        Iteration 3: Minor syntax issues (0.85)
        Iteration 4: Correct (0.96)
        """
        responses = [
            "% Missing termination\ninitiatedAt(active(P), T) :- happensAt(start(P), T).",
            "% Wrong name\ninitiatedAt(active(P), T) :- happensAt(begin_activity(P), T).\nterminatedAt(active(P), T) :- happensAt(end_activity(P), T).",
            "% Almost there\ninitiatedAt(active(P), T) :- happensAt(start_activity(P), T).\nterminatedAt(active(P), T) :- happensAt(stop_activity(P), T).",
            "% Perfect\ninitiatedAt(active(P), T) :- happensAt(start_activity(P), T).\nterminatedAt(active(P), T) :- happensAt(end_activity(P), T)."
        ]
        
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content=r, request_id=f"req-{i}")
            for i, r in enumerate(responses, 1)
        ]
        
        feedbacks = [
            "Missing terminatedAt clause for activity completion",
            "Use 'start_activity' not 'begin_activity', 'end_activity' not 'stop_activity'",
            "Correct structure, minor predicate name issue in termination",
            "Excellent match with reference rules"
        ]
        
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.4, matches=False, feedback=feedbacks[0]),
            create_evaluation(score=0.6, matches=False, feedback=feedbacks[1]),
            create_evaluation(score=0.85, matches=False, feedback=feedbacks[2]),
            create_evaluation(score=0.96, matches=True, feedback=feedbacks[3])
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Verify: Progressive improvement
        scores = [e.score for e in result.evaluations]
        assert scores == [0.4, 0.6, 0.85, 0.96]
        assert all(scores[i] <= scores[i+1] for i in range(len(scores)-1))
        
        # Verify: Feedback incorporated
        refinement_calls = (
            orchestrator.prompt_builder.build_refinement.call_args_list
        )
        assert len(refinement_calls) == 3
        assert "terminatedAt" in refinement_calls[0][1]['feedback']
        assert "start_activity" in refinement_calls[1][1]['feedback']
        
        # Verify: Converged on iteration 4
        assert result.states[3].converged is True
    
    def test_multiple_activities_sequential(
        self,
        mock_prompt_builder,
        mock_llm_provider,
        mock_simlp_client,
        basic_config
    ):
        """Test processing multiple activities sequentially."""
        orchestrator = LoopOrchestrator(
            prompt_builder=mock_prompt_builder,
            llm_provider=mock_llm_provider,
            simlp_client=mock_simlp_client,
            config=basic_config
        )
        
        # Setup: Different responses for each activity
        mock_llm_provider.generate.return_value = create_llm_response(
            content="Activity-specific rules"
        )
        mock_simlp_client.evaluate.return_value = create_evaluation(
            score=0.95,
            matches=True
        )
        
        # Execute: Process two activities
        result1 = orchestrator.run(domain="MSA", activity="active")
        result2 = orchestrator.run(domain="MSA", activity="inactive")
        
        # Verify: Both succeeded
        assert result1.summary['converged'] is True
        assert result2.summary['converged'] is True
        
        # Verify: Separate histories
        assert len(result1.states) >= 1
        assert len(result2.states) >= 1


# ============================================================================
# TEST CLASS 10: METRICS AND MONITORING
# ============================================================================



class TestMetricsAndMonitoring:
    """Test metrics collection and monitoring capabilities."""
    
    def test_token_usage_tracking(self, orchestrator):
        """Test that token usage is correctly aggregated."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="v1", tokens=100),
            create_llm_response(content="v2", tokens=150),
            create_llm_response(content="v3", tokens=200)
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.7, matches=False),
            create_evaluation(score=0.92, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        assert result.summary['total_tokens'] == 450
        assert result.summary['avg_tokens_per_iteration'] == 150
    
    def test_latency_tracking(self, orchestrator):
        """Test that latency metrics are tracked."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content="v1", latency=500.0),
            create_llm_response(content="v2", latency=600.0),
            create_llm_response(content="v3", latency=700.0)
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.7, matches=False),
            create_evaluation(score=0.92, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        assert result.summary['avg_latency_ms'] == 600.0
        assert result.summary['total_latency_ms'] == 1800.0
    
    def test_improvement_rate_calculation(self, orchestrator):
        """Test calculation of improvement rate."""
        orchestrator.llm_provider.generate.side_effect = [
            create_llm_response(content=f"v{i}")
            for i in range(1, 5)
        ]
        orchestrator.simlp_client.evaluate.side_effect = [
            create_evaluation(score=0.5, matches=False),
            create_evaluation(score=0.6, matches=False),
            create_evaluation(score=0.8, matches=False),
            create_evaluation(score=0.95, matches=True)
        ]
        
        result = orchestrator.run(domain="MSA", activity="active")
        
        # Improvement from 0.5 to 0.95 = 0.45
        assert result.summary['improvement'] == 0.45
        assert result.summary['improvement_rate'] == 0.45 / 3  # 3 refinements


class TestMemoryIntegration:
    """Tests for RuleMemory integration within the orchestrator."""

    def test_prerequisite_rules_injected_into_prompt(
        self,
        mock_prompt_builder,
        mock_llm_provider,
        mock_simlp_client,
        basic_config
    ):
        """Prerequisite rules from memory are injected per RULE_MEMORY sequence."""
        rule_memory = RuleMemory()
        rule_memory.add_entry(
            name="gap",
            description="Gap description.",
            rules="initiatedAt(gap(Vessel)=nearPort, T) :- happensAt(gap_start(Vessel), T)."
        )

        orchestrator = LoopOrchestrator(
            prompt_builder=mock_prompt_builder,
            llm_provider=mock_llm_provider,
            simlp_client=mock_simlp_client,
            config=basic_config,
            rule_memory=rule_memory
        )

        mock_prompt_builder.reset_mock()
        mock_prompt_builder.get_activity_description.return_value = (
            "Composite activity description."
        )
        mock_llm_provider.generate.return_value = create_llm_response(
            content="initiatedAt(rendezVous(V)=true, T) :- ..."
        )
        mock_simlp_client.evaluate.return_value = create_evaluation(
            score=0.95,
            matches=True,
            feedback="Good job"
        )

        orchestrator.run(
            domain="MSA",
            activity="rendezVous",
            prerequisites=["gap"]
        )

        initial_kwargs = mock_prompt_builder.build_initial.call_args.kwargs
        assert "prerequisite_rules" in initial_kwargs
        assert "gap" in initial_kwargs["prerequisite_rules"]

    def test_best_rules_persisted_to_memory(
        self,
        mock_prompt_builder,
        mock_llm_provider,
        mock_simlp_client,
        basic_config
    ):
        """Final best rules are stored in memory for future runs."""
        rule_memory = RuleMemory()

        orchestrator = LoopOrchestrator(
            prompt_builder=mock_prompt_builder,
            llm_provider=mock_llm_provider,
            simlp_client=mock_simlp_client,
            config=basic_config,
            rule_memory=rule_memory
        )

        mock_prompt_builder.get_activity_description.return_value = (
            "Gap description."
        )
        mock_llm_provider.generate.return_value = create_llm_response(
            content="initiatedAt(gap(V)=true, T) :- happensAt(gap_start(V), T)."
        )
        mock_simlp_client.evaluate.return_value = create_evaluation(
            score=0.97,
            matches=True,
            feedback="Excellent"
        )

        orchestrator.run(domain="MSA", activity="gap")

        entry = rule_memory.get("gap")
        assert entry is not None
        assert "initiatedAt" in entry.rules
        assert entry.score == 0.97
        assert entry.metadata["domain"] == "MSA"
        assert entry.metadata["prerequisites"] == []
