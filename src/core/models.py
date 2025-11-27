from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class LLMRequest(BaseModel):
    provider: str
    model: str
    prompt: str = Field(min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, gt=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    context: List[Any] = Field(default_factory=list)

class LLMResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    content: str
    tokens_used: int = Field(gt=0)
    latency_ms: float = Field(ge=0.0)
    finish_reason: str
    raw: Dict[str, Any]

class EvaluationResult(BaseModel):
    rule_id: str
    score: float = Field(ge=0.0, le=1.0)
    matches_reference: bool
    feedback: str
    reference_rule: Optional[str] = None
    issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LoopConfig(BaseModel):
    provider: str
    objective: str
    max_iterations: int
    convergence_threshold: float = Field(ge=0.0, le=1.0)
    batch_size: int = Field(gt=0)
    retry_limit: int = Field(gt=0)

class LoopState(BaseModel):
    iteration: int = Field(gt=0)
    pending_requests: List[LLMRequest]
    completed_requests: List[LLMResponse]
    rules: str
    evaluations: List[EvaluationResult]
    converged: bool
    notes: Optional[str] = None

class FinalResult(BaseModel):
    config: LoopConfig
    states: List[LoopState]
    best_rules: List[str]
    evaluations: List[EvaluationResult]
    summary: Dict[str, Any]
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)