"""Self-consistency validation for RTEC rule generation.

Implements a self-consistency approach where multiple candidate rules are generated,
pairwise similarity is computed using SimLP, and the most consistent candidate
(highest average similarity to others) is selected.

This technique reduces variance in LLM outputs by selecting the candidate that
best agrees with the ensemble of generated alternatives.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import structlog

from src.feedback.client import FeedbackClient
from src.interfaces.llm import LLMProvider
from src.interfaces.models import LLMRequest
from src.utils.code_extractor import extract_rules_from_response

logger = structlog.get_logger(__name__)


@dataclass
class SelfConsistencyResult:
    """Result of self-consistency validation.

    Contains the selected best candidate, confidence metrics, and full details
    about all candidates and their pairwise similarities.
    """

    best_candidate: str
    best_candidate_index: int
    confidence_score: float
    all_candidates: list[str]
    similarity_matrix: list[list[float]]
    average_similarities: list[float]

    @property
    def num_samples(self) -> int:
        """Number of candidates that were generated."""
        return len(self.all_candidates)

    @property
    def is_unanimous(self) -> bool:
        """Check if all candidates are identical."""
        if not self.all_candidates:
            return False
        first = self.all_candidates[0]
        return all(c == first for c in self.all_candidates)

    def __post_init__(self):
        """Validate the result data."""
        if not self.all_candidates:
            raise ValueError("all_candidates cannot be empty")

        if not (0 <= self.best_candidate_index < len(self.all_candidates)):
            raise ValueError(
                f"best_candidate_index {self.best_candidate_index} out of range "
                f"for {len(self.all_candidates)} candidates"
            )

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(
                f"confidence_score must be between 0.0 and 1.0, " f"got {self.confidence_score}"
            )

        n = len(self.all_candidates)
        if len(self.similarity_matrix) != n:
            raise ValueError(
                f"similarity_matrix has {len(self.similarity_matrix)} rows, " f"expected {n}"
            )
        for i, row in enumerate(self.similarity_matrix):
            if len(row) != n:
                raise ValueError(
                    f"similarity_matrix row {i} has {len(row)} columns, " f"expected {n}"
                )

        if len(self.average_similarities) != n:
            raise ValueError(
                f"average_similarities has {len(self.average_similarities)} elements, "
                f"expected {n}"
            )


def generate_with_self_consistency(
    request: LLMRequest,
    llm_provider: LLMProvider,
    num_samples: int = 5,
    temperature: float = 0.7,
    feedback_client: Optional[FeedbackClient] = None,
    log_dir: Optional[Path] = None,
) -> SelfConsistencyResult:
    """Generate RTEC rules using self-consistency validation.

    Generates N candidate rules, computes pairwise similarity between all pairs,
    and selects the candidate with highest average similarity to others.

    Args:
        request: The LLM request containing the prompt and configuration
        llm_provider: LLM provider to generate candidates
        num_samples: Number of candidate rules to generate (must be >= 1)
        temperature: Temperature to use for generation (higher = more diverse)
        feedback_client: Client for computing similarity (creates one if None)
        log_dir: Optional directory for similarity computation logs

    Returns:
        SelfConsistencyResult containing the best candidate and metrics

    Raises:
        ValueError: If num_samples < 1

    Example:
        >>> from src.llm.mock_provider import MockLLMProvider
        >>> from src.interfaces.models import LLMRequest
        >>>
        >>> provider = MockLLMProvider()
        >>> request = LLMRequest(prompt="Generate gap fluent rules")
        >>> result = generate_with_self_consistency(request, provider, num_samples=3)
        >>> print(f"Confidence: {result.confidence_score}")
    """
    if num_samples < 1:
        raise ValueError(f"num_samples must be >= 1, got {num_samples}")

    logger.info(
        "Starting self-consistency generation",
        num_samples=num_samples,
        temperature=temperature,
    )

    # Handle edge case: single sample
    if num_samples == 1:
        logger.warning("Single sample requested, no consistency validation possible")
        return _handle_single_sample(request, llm_provider)

    # Initialize feedback client for similarity computation
    if feedback_client is None:
        log_path = log_dir / "self_consistency.log" if log_dir else "logs/self_consistency.log"
        feedback_client = FeedbackClient(log_file=log_path)

    # Step 1: Generate N candidates
    candidates = _generate_candidates(request, llm_provider, num_samples, temperature)

    # Handle edge case: all candidates identical
    if _all_identical(candidates):
        logger.info("All candidates are identical, skipping similarity computation")
        return _handle_identical_candidates(candidates)

    # Step 2: Compute NxN pairwise similarity matrix
    similarity_matrix = _compute_similarity_matrix(candidates, feedback_client)

    # Step 3: Calculate average similarity for each candidate
    average_similarities = _compute_average_similarities(similarity_matrix)

    # Step 4: Select candidate with highest average similarity
    best_index = _select_best_candidate(average_similarities)

    # Step 5: Compute confidence score
    confidence = _compute_confidence_score(average_similarities, similarity_matrix)

    logger.info(
        "Self-consistency generation complete",
        best_index=best_index,
        confidence=f"{confidence:.4f}",
        avg_similarities=[f"{s:.4f}" for s in average_similarities],
    )

    return SelfConsistencyResult(
        best_candidate=candidates[best_index],
        best_candidate_index=best_index,
        confidence_score=confidence,
        all_candidates=candidates,
        similarity_matrix=similarity_matrix,
        average_similarities=average_similarities,
    )


def _generate_candidates(
    request: LLMRequest,
    llm_provider: LLMProvider,
    num_samples: int,
    temperature: float,
) -> list[str]:
    """Generate N candidate rules from the LLM.

    Args:
        request: Base LLM request
        llm_provider: Provider for generation
        num_samples: Number of candidates to generate
        temperature: Temperature for generation

    Returns:
        List of extracted rule strings
    """
    candidates: list[str] = []

    for i in range(num_samples):
        logger.debug(f"Generating candidate {i + 1}/{num_samples}")

        # Create modified request with specified temperature
        modified_request = LLMRequest(
            prompt=request.prompt,
            temperature=temperature,
            max_tokens=request.max_tokens,
            model=request.model,
            system_prompt=request.system_prompt,
            domain_prompt=request.domain_prompt,
            feedback=request.feedback,
            fewshots=request.fewshots,
            extra=request.extra,
        )

        # Generate and extract rules
        raw_response = llm_provider.generate(modified_request)
        extracted_rules = extract_rules_from_response(raw_response)
        candidates.append(extracted_rules)

        logger.debug(
            f"Candidate {i + 1} generated",
            length=len(extracted_rules),
            preview=(
                extracted_rules[:100] + "..." if len(extracted_rules) > 100 else extracted_rules
            ),
        )

    return candidates


def _compute_similarity_matrix(
    candidates: list[str],
    feedback_client: FeedbackClient,
) -> list[list[float]]:
    """Compute NxN pairwise similarity matrix.

    Only computes upper triangle and mirrors to lower (symmetric).
    Diagonal is 1.0 (self-similarity).

    Args:
        candidates: List of candidate rule strings
        feedback_client: Client for similarity computation

    Returns:
        NxN similarity matrix as nested lists
    """
    n = len(candidates)
    matrix: list[list[float]] = [[0.0] * n for _ in range(n)]

    # Fill diagonal with 1.0 (self-similarity)
    for i in range(n):
        matrix[i][i] = 1.0

    # Compute upper triangle and mirror
    for i in range(n):
        for j in range(i + 1, n):
            similarity = _compute_pair_similarity(candidates[i], candidates[j], feedback_client)
            matrix[i][j] = similarity
            matrix[j][i] = similarity  # Mirror (symmetric)

            logger.debug(
                f"Computed similarity ({i}, {j})",
                similarity=f"{similarity:.4f}",
            )

    return matrix


def _compute_pair_similarity(
    candidate_a: str,
    candidate_b: str,
    feedback_client: FeedbackClient,
) -> float:
    """Compute similarity between two candidates using SimLP.

    Args:
        candidate_a: First candidate rules
        candidate_b: Second candidate rules
        feedback_client: Client for similarity computation

    Returns:
        Similarity score between 0.0 and 1.0
    """
    result = feedback_client.evaluate(
        generated_rules=candidate_a,
        ground_truth_rules=candidate_b,
        generate_feedback=False,
    )
    return result.similarity


def _compute_average_similarities(similarity_matrix: list[list[float]]) -> list[float]:
    """Compute average similarity for each candidate (excluding self).

    Args:
        similarity_matrix: NxN similarity matrix

    Returns:
        List of average similarities for each candidate
    """
    n = len(similarity_matrix)
    averages: list[float] = []

    for i in range(n):
        # Sum similarities to all other candidates (excluding self)
        total = sum(similarity_matrix[i][j] for j in range(n) if j != i)
        # Average over n-1 other candidates
        avg = total / (n - 1) if n > 1 else 1.0
        averages.append(avg)

    return averages


def _select_best_candidate(average_similarities: list[float]) -> int:
    """Select the candidate with highest average similarity.

    Args:
        average_similarities: List of average similarities for each candidate

    Returns:
        Index of the best candidate
    """
    best_index = 0
    best_avg = average_similarities[0]

    for i, avg in enumerate(average_similarities):
        if avg > best_avg:
            best_avg = avg
            best_index = i

    logger.debug(
        "Selected best candidate",
        index=best_index,
        average_similarity=f"{best_avg:.4f}",
    )

    return best_index


def _compute_confidence_score(
    average_similarities: list[float],
    similarity_matrix: list[list[float]],
) -> float:
    """Compute confidence score as geometric mean of max avg and mean pairwise.

    Confidence formula: (max_avg_similarity * mean_pairwise_similarity) ** 0.5

    Args:
        average_similarities: Average similarity for each candidate
        similarity_matrix: Full NxN similarity matrix

    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Max average similarity
    max_avg = max(average_similarities)

    # Mean pairwise similarity (upper triangle only, excluding diagonal)
    n = len(similarity_matrix)
    pairwise_sum = 0.0
    pairwise_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            pairwise_sum += similarity_matrix[i][j]
            pairwise_count += 1

    mean_pairwise = pairwise_sum / pairwise_count if pairwise_count > 0 else 1.0

    # Geometric mean
    confidence = (max_avg * mean_pairwise) ** 0.5

    logger.debug(
        "Computed confidence score",
        max_avg=f"{max_avg:.4f}",
        mean_pairwise=f"{mean_pairwise:.4f}",
        confidence=f"{confidence:.4f}",
    )

    return confidence


def _all_identical(candidates: list[str]) -> bool:
    """Check if all candidates are identical.

    Args:
        candidates: List of candidate strings

    Returns:
        True if all candidates are the same
    """
    if not candidates:
        return True
    first = candidates[0]
    return all(c == first for c in candidates)


def _handle_single_sample(
    request: LLMRequest,
    llm_provider: LLMProvider,
) -> SelfConsistencyResult:
    """Handle the edge case of a single sample request.

    Args:
        request: LLM request
        llm_provider: Provider for generation

    Returns:
        SelfConsistencyResult with single candidate and confidence=1.0
    """
    raw_response = llm_provider.generate(request)
    extracted_rules = extract_rules_from_response(raw_response)

    return SelfConsistencyResult(
        best_candidate=extracted_rules,
        best_candidate_index=0,
        confidence_score=1.0,
        all_candidates=[extracted_rules],
        similarity_matrix=[[1.0]],
        average_similarities=[1.0],
    )


def _handle_identical_candidates(candidates: list[str]) -> SelfConsistencyResult:
    """Handle the edge case when all candidates are identical.

    Args:
        candidates: List of identical candidate strings

    Returns:
        SelfConsistencyResult with first candidate and confidence=1.0
    """
    n = len(candidates)

    # All similarities are 1.0 since candidates are identical
    similarity_matrix = [[1.0] * n for _ in range(n)]
    average_similarities = [1.0] * n

    return SelfConsistencyResult(
        best_candidate=candidates[0],
        best_candidate_index=0,
        confidence_score=1.0,
        all_candidates=candidates,
        similarity_matrix=similarity_matrix,
        average_similarities=average_similarities,
    )
