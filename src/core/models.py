"""Data models for the feedback loop orchestrator.

These models track state across iterations and provide final results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class IterationResult:
    """Result of a single iteration in the feedback loop.

    Captures the generated rules, evaluation, and metadata for one iteration.
    """
    iteration: int
    generated_rules: str
    similarity_score: float
    feedback: Optional[str] = None
    prompt_used: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Optional detailed metrics from SimLP
    optimal_matching: Optional[Any] = None
    distances: Optional[Any] = None

    # Optional self-consistency metrics
    sc_confidence: Optional[float] = None
    sc_num_samples: Optional[int] = None
    
    @property
    def is_perfect(self) -> bool:
        """Check if this iteration achieved a perfect score."""
        return self.similarity_score >= 1.0


@dataclass
class LoopStatistics:
    """Statistics collected across all iterations.
    
    Tracks improvement metrics, token usage, and timing.
    """
    total_iterations: int
    initial_score: float
    final_score: float
    best_score: float
    best_iteration: int
    
    # Improvement metrics
    improvement: float = field(init=False)
    improvement_rate: float = field(init=False)
    
    # Optional: token/latency tracking (for future use)
    total_tokens: Optional[int] = None
    total_latency_ms: Optional[float] = None
    
    def __post_init__(self):
        self.improvement = self.final_score - self.initial_score
        self.improvement_rate = (
            self.improvement / self.total_iterations 
            if self.total_iterations > 0 else 0.0
        )


@dataclass
class FinalResult:
    """Final result of the feedback loop orchestration.
    
    Contains the best rules found, all iteration history, and statistics.
    """
    fluent_name: str
    domain: str
    
    # Best result
    best_rules: str
    best_score: float
    best_iteration: int
    
    # Convergence info
    converged: bool
    convergence_threshold: float
    max_iterations: int
    
    # Full history and statistics
    iterations: List[IterationResult]
    statistics: LoopStatistics
    
    # Metadata
    started_at: datetime
    completed_at: datetime
    
    @property
    def duration_seconds(self) -> float:
        """Total duration of the orchestration in seconds."""
        return (self.completed_at - self.started_at).total_seconds()
    
    def summary(self) -> str:
        """Generate a human-readable summary of the result."""
        status = "✓ Converged" if self.converged else "✗ Did not converge"
        return (
            f"{10*"="} {self.fluent_name} ({self.domain}) {10*"="}\n"
            f"Status: {status}\n"
            f"Best Score: {self.best_score:.4f} (iteration {self.best_iteration})\n"
            f"Iterations: {len(self.iterations)}/{self.max_iterations}\n"
            f"Improvement: {self.statistics.initial_score:.4f} → {self.best_score:.4f} "
            f"(+{self.statistics.improvement:.4f})\n"
            f"Duration: {self.duration_seconds:.2f}s"
        )


@dataclass
class OrchestratorConfig:
    """Configuration for the LoopOrchestrator.

    Controls convergence criteria and iteration limits.
    """
    max_iterations: int = 5
    convergence_threshold: float = 0.9

    # Self-consistency parameters
    use_self_consistency: bool = False
    sc_num_samples: int = 5
    sc_temperature: float = 0.7

    # Whether to stop early when score starts decreasing
    early_stopping: bool = False
    early_stopping_patience: int = 2

    # Logging verbosity
    verbose: bool = True

    def __post_init__(self):
        if not (0.0 <= self.convergence_threshold <= 1.0):
            raise ValueError(
                f"convergence_threshold must be between 0.0 and 1.0, "
                f"got {self.convergence_threshold}"
            )
        if self.max_iterations < 1:
            raise ValueError(
                f"max_iterations must be at least 1, got {self.max_iterations}"
            )

        # Self-consistency validation
        if self.use_self_consistency and self.sc_num_samples < 1:
            raise ValueError(
                f"sc_num_samples must be >= 1 when use_self_consistency is enabled, "
                f"got {self.sc_num_samples}"
            )
        if not (0.0 <= self.sc_temperature <= 2.0):
            raise ValueError(
                f"sc_temperature must be between 0.0 and 2.0, got {self.sc_temperature}"
            )

