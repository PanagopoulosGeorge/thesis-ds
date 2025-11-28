import pytest
from pydantic import ValidationError

from src.core.models import (
    EvaluationResult,
    FinalResult,
    LLMRequest,
    LLMResponse,
    LoopConfig,
    LoopState,
)


def test_llm_request_defaults_and_validation():
    request = LLMRequest(provider="openai", model="gpt-4o", prompt="Generate new inertia rules.")

    assert request.temperature == pytest.approx(0.7)
    assert request.max_tokens == 1024
    assert request.metadata == {}
    assert request.context == []

    with pytest.raises(ValidationError):
        LLMRequest(
            provider="openai",
            model="gpt-4o",
            prompt="",
            max_tokens=1,
        )


def test_llm_response_requires_non_negative_usage():
    request = LLMRequest(provider="openai", model="gpt-4o", prompt="Return holdsAt clauses.")

    response = LLMResponse(
        request_id="req-1",
        provider=request.provider,
        model=request.model,
        content="initiatedAt(moving(X), T) :- happensAt(startMoving(X), T).",
        tokens_used=128,
        latency_ms=123.4,
        finish_reason="stop",
        raw={"id": "abc123"},
    )

    assert response.tokens_used == 128
    assert response.latency_ms == pytest.approx(123.4)

    with pytest.raises(ValidationError):
        LLMResponse(
            request_id="req-2",
            provider=request.provider,
            model=request.model,
            content="",
            tokens_used=-1,
            latency_ms=-0.5,
            finish_reason="length",
            raw={"id": "xyz987"},
        )


def test_evaluation_result_score_bounds():
    result = EvaluationResult(
        rule_id="rule-1",
        score=0.62,
        matches_reference=True,
        feedback="Rule matches reference except for variable naming.",
        reference_rule="holdsAt(fluent, T) :- initiatedAt(fluent, Ts), Ts < T.",
        metadata={"precision": 0.8},
    )
    assert result.metadata["precision"] == pytest.approx(0.8)

    with pytest.raises(ValidationError):
        EvaluationResult(
            rule_id="rule-2",
            score=1.1,
            matches_reference=False,
            feedback="Score cannot exceed 1.0",
        )


def test_loop_config_validation():
    config = LoopConfig(
        provider="openai",
        objective="maximize_precision",
        max_iterations=3,
        convergence_threshold=0.9,
        batch_size=2,
        retry_limit=2,
    )

    assert config.max_iterations == 3
    assert config.retry_limit == 2

    with pytest.raises(ValidationError):
        LoopConfig(
            provider="openai",
            objective="maximize_precision",
            max_iterations=0,
            convergence_threshold=1.5,
            batch_size=0,
            retry_limit=-1,
        )


def test_loop_state_requires_non_negative_iteration():
    request = LLMRequest(provider="openai", model="gpt-4o", prompt="Draft monitoring rules.")
    response = LLMResponse(
        request_id="req-state",
        provider=request.provider,
        model=request.model,
        content="terminatedAt(active(X), T) :- happensAt(stop(X), T).",
        tokens_used=64,
        latency_ms=88.0,
        finish_reason="stop",
        raw={"id": "state"},
    )
    evaluation = EvaluationResult(
        rule_id="rule-state",
        score=0.74,
        matches_reference=False,
        feedback="Needs explicit negation of conflicting fluent.",
    )

    state = LoopState(
        iteration=1,
        pending_requests=[],
        rules = "test rules",
        completed_requests=[response],
        evaluations=[evaluation],
        converged=False,
        notes="Initial loop.",
    )

    assert state.completed_requests[0].request_id == "req-state"
    assert state.iteration == 1

    with pytest.raises(ValidationError):
        LoopState(
            iteration=-1,
            pending_requests=[],
            completed_requests=[],
            evaluations=[],
            converged=False,
        )

