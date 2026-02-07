"""Tests for the self-consistency validation module."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.self_consistency import (
    SelfConsistencyResult,
    _all_identical,
    _compute_average_similarities,
    _compute_confidence_score,
    _compute_similarity_matrix,
    _generate_candidates,
    _handle_identical_candidates,
    _handle_single_sample,
    _select_best_candidate,
    generate_with_self_consistency,
)
from src.interfaces.models import LLMRequest
from src.llm.mock_provider import MockLLMProvider

# ============================================================
# Tests for SelfConsistencyResult dataclass
# ============================================================


class TestSelfConsistencyResult:
    """Tests for the SelfConsistencyResult dataclass."""

    def test_valid_result(self):
        """Should create a valid result with correct data."""
        result = SelfConsistencyResult(
            best_candidate="foo(X).",
            best_candidate_index=0,
            confidence_score=0.85,
            all_candidates=["foo(X).", "bar(X)."],
            similarity_matrix=[[1.0, 0.7], [0.7, 1.0]],
            average_similarities=[0.7, 0.7],
        )
        assert result.best_candidate == "foo(X)."
        assert result.num_samples == 2
        assert not result.is_unanimous

    def test_unanimous_detection(self):
        """Should detect when all candidates are identical."""
        result = SelfConsistencyResult(
            best_candidate="foo(X).",
            best_candidate_index=0,
            confidence_score=1.0,
            all_candidates=["foo(X).", "foo(X).", "foo(X)."],
            similarity_matrix=[[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]],
            average_similarities=[1.0, 1.0, 1.0],
        )
        assert result.is_unanimous

    def test_empty_candidates_raises(self):
        """Should raise ValueError for empty candidates."""
        with pytest.raises(ValueError, match="all_candidates cannot be empty"):
            SelfConsistencyResult(
                best_candidate="",
                best_candidate_index=0,
                confidence_score=1.0,
                all_candidates=[],
                similarity_matrix=[],
                average_similarities=[],
            )

    def test_invalid_best_index_raises(self):
        """Should raise ValueError for out-of-range best_candidate_index."""
        with pytest.raises(ValueError, match="out of range"):
            SelfConsistencyResult(
                best_candidate="foo(X).",
                best_candidate_index=5,
                confidence_score=0.8,
                all_candidates=["foo(X).", "bar(X)."],
                similarity_matrix=[[1.0, 0.7], [0.7, 1.0]],
                average_similarities=[0.7, 0.7],
            )

    def test_invalid_confidence_score_raises(self):
        """Should raise ValueError for confidence outside [0, 1]."""
        with pytest.raises(ValueError, match="confidence_score must be between"):
            SelfConsistencyResult(
                best_candidate="foo(X).",
                best_candidate_index=0,
                confidence_score=1.5,
                all_candidates=["foo(X)."],
                similarity_matrix=[[1.0]],
                average_similarities=[1.0],
            )

    def test_mismatched_matrix_rows_raises(self):
        """Should raise ValueError when matrix rows don't match candidate count."""
        with pytest.raises(ValueError, match="similarity_matrix has"):
            SelfConsistencyResult(
                best_candidate="foo(X).",
                best_candidate_index=0,
                confidence_score=0.8,
                all_candidates=["foo(X).", "bar(X)."],
                similarity_matrix=[[1.0, 0.7]],  # Only 1 row, need 2
                average_similarities=[0.7, 0.7],
            )

    def test_mismatched_average_similarities_raises(self):
        """Should raise ValueError when average_similarities length doesn't match."""
        with pytest.raises(ValueError, match="average_similarities has"):
            SelfConsistencyResult(
                best_candidate="foo(X).",
                best_candidate_index=0,
                confidence_score=0.8,
                all_candidates=["foo(X).", "bar(X)."],
                similarity_matrix=[[1.0, 0.7], [0.7, 1.0]],
                average_similarities=[0.7],  # Only 1, need 2
            )


# ============================================================
# Tests for helper functions
# ============================================================


class TestAllIdentical:
    """Tests for the _all_identical helper."""

    def test_empty_list(self):
        """Empty list should be considered identical."""
        assert _all_identical([]) is True

    def test_single_element(self):
        """Single element list should be identical."""
        assert _all_identical(["foo"]) is True

    def test_identical_elements(self):
        """List with identical elements should return True."""
        assert _all_identical(["foo", "foo", "foo"]) is True

    def test_different_elements(self):
        """List with different elements should return False."""
        assert _all_identical(["foo", "bar", "foo"]) is False


class TestComputeAverageSimilarities:
    """Tests for the _compute_average_similarities helper."""

    def test_symmetric_matrix(self):
        """Should compute correct averages for symmetric matrix."""
        matrix = [
            [1.0, 0.8, 0.6],
            [0.8, 1.0, 0.7],
            [0.6, 0.7, 1.0],
        ]
        averages = _compute_average_similarities(matrix)

        # Candidate 0: avg of (0.8 + 0.6) / 2 = 0.7
        # Candidate 1: avg of (0.8 + 0.7) / 2 = 0.75
        # Candidate 2: avg of (0.6 + 0.7) / 2 = 0.65
        assert abs(averages[0] - 0.7) < 0.01
        assert abs(averages[1] - 0.75) < 0.01
        assert abs(averages[2] - 0.65) < 0.01

    def test_uniform_similarities(self):
        """All same similarities should give same averages."""
        matrix = [
            [1.0, 0.5, 0.5],
            [0.5, 1.0, 0.5],
            [0.5, 0.5, 1.0],
        ]
        averages = _compute_average_similarities(matrix)
        assert all(abs(a - 0.5) < 0.01 for a in averages)


class TestSelectBestCandidate:
    """Tests for the _select_best_candidate helper."""

    def test_selects_highest_average(self):
        """Should select candidate with highest average similarity."""
        averages = [0.6, 0.8, 0.7]
        assert _select_best_candidate(averages) == 1

    def test_selects_first_on_tie(self):
        """Should select first candidate when tied."""
        averages = [0.8, 0.8, 0.5]
        assert _select_best_candidate(averages) == 0


class TestComputeConfidenceScore:
    """Tests for the _compute_confidence_score helper."""

    def test_perfect_similarity(self):
        """Perfect similarities should give confidence of 1.0."""
        matrix = [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
        ]
        averages = [1.0, 1.0, 1.0]
        confidence = _compute_confidence_score(averages, matrix)
        assert abs(confidence - 1.0) < 0.001

    def test_low_similarity(self):
        """Low similarities should give low confidence."""
        matrix = [
            [1.0, 0.2, 0.2],
            [0.2, 1.0, 0.2],
            [0.2, 0.2, 1.0],
        ]
        averages = [0.2, 0.2, 0.2]
        confidence = _compute_confidence_score(averages, matrix)
        assert confidence < 0.3

    def test_geometric_mean(self):
        """Confidence should be geometric mean of max_avg and mean_pairwise."""
        matrix = [
            [1.0, 0.64],
            [0.64, 1.0],
        ]
        averages = [0.64, 0.64]
        # max_avg = 0.64, mean_pairwise = 0.64
        # confidence = sqrt(0.64 * 0.64) = 0.64
        confidence = _compute_confidence_score(averages, matrix)
        assert abs(confidence - 0.64) < 0.001


# ============================================================
# Tests for edge case handlers
# ============================================================


class TestHandleSingleSample:
    """Tests for the _handle_single_sample handler."""

    def test_single_sample_result(self):
        """Should return result with single candidate and confidence 1.0."""
        provider = MockLLMProvider("```prolog\nfoo(X).\n```")
        request = LLMRequest(prompt="Generate rules")

        result = _handle_single_sample(request, provider)

        assert result.num_samples == 1
        assert result.confidence_score == 1.0
        assert "foo(X)." in result.best_candidate
        assert result.similarity_matrix == [[1.0]]


class TestHandleIdenticalCandidates:
    """Tests for the _handle_identical_candidates handler."""

    def test_identical_candidates_result(self):
        """Should return result with confidence 1.0 for identical candidates."""
        candidates = ["foo(X).", "foo(X).", "foo(X)."]

        result = _handle_identical_candidates(candidates)

        assert result.num_samples == 3
        assert result.confidence_score == 1.0
        assert result.is_unanimous
        assert all(all(s == 1.0 for s in row) for row in result.similarity_matrix)


# ============================================================
# Tests for _generate_candidates
# ============================================================


class TestGenerateCandidates:
    """Tests for the _generate_candidates function."""

    def test_generates_correct_number(self):
        """Should generate the requested number of candidates."""
        responses = [
            "```prolog\ncandidate1(X).\n```",
            "```prolog\ncandidate2(X).\n```",
            "```prolog\ncandidate3(X).\n```",
        ]
        provider = MockLLMProvider(responses)
        request = LLMRequest(prompt="Generate rules")

        candidates = _generate_candidates(request, provider, num_samples=3, temperature=0.7)

        assert len(candidates) == 3
        assert "candidate1(X)." in candidates[0]
        assert "candidate2(X)." in candidates[1]
        assert "candidate3(X)." in candidates[2]

    def test_extracts_rules_from_response(self):
        """Should extract Prolog rules from markdown responses."""
        provider = MockLLMProvider("Here's the rule:\n```prolog\nfoo(X) :- bar(X).\n```")
        request = LLMRequest(prompt="Generate rules")

        candidates = _generate_candidates(request, provider, num_samples=1, temperature=0.7)

        assert len(candidates) == 1
        assert "foo(X) :- bar(X)." in candidates[0]
        assert "Here's the rule" not in candidates[0]


# ============================================================
# Tests for _compute_similarity_matrix
# ============================================================


class TestComputeSimilarityMatrix:
    """Tests for the _compute_similarity_matrix function."""

    def test_diagonal_is_one(self):
        """Diagonal should be 1.0 (self-similarity)."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.similarity = 0.5
        mock_client.evaluate.return_value = mock_result

        candidates = ["a", "b", "c"]
        matrix = _compute_similarity_matrix(candidates, mock_client)

        assert matrix[0][0] == 1.0
        assert matrix[1][1] == 1.0
        assert matrix[2][2] == 1.0

    def test_symmetric_matrix(self):
        """Matrix should be symmetric."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.similarity = 0.7
        mock_client.evaluate.return_value = mock_result

        candidates = ["a", "b", "c"]
        matrix = _compute_similarity_matrix(candidates, mock_client)

        assert matrix[0][1] == matrix[1][0]
        assert matrix[0][2] == matrix[2][0]
        assert matrix[1][2] == matrix[2][1]

    def test_only_computes_upper_triangle(self):
        """Should only call evaluate for upper triangle pairs."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.similarity = 0.8
        mock_client.evaluate.return_value = mock_result

        candidates = ["a", "b", "c"]
        _compute_similarity_matrix(candidates, mock_client)

        # For 3 candidates: (0,1), (0,2), (1,2) = 3 calls
        assert mock_client.evaluate.call_count == 3


# ============================================================
# Tests for generate_with_self_consistency (main function)
# ============================================================


class TestGenerateWithSelfConsistency:
    """Tests for the main generate_with_self_consistency function."""

    def test_invalid_num_samples_raises(self):
        """Should raise ValueError for num_samples < 1."""
        provider = MockLLMProvider()
        request = LLMRequest(prompt="Generate rules")

        with pytest.raises(ValueError, match="num_samples must be >= 1"):
            generate_with_self_consistency(request, provider, num_samples=0)

    def test_single_sample_shortcut(self):
        """Should use shortcut for num_samples=1."""
        provider = MockLLMProvider("```prolog\nfoo(X).\n```")
        request = LLMRequest(prompt="Generate rules")

        result = generate_with_self_consistency(request, provider, num_samples=1)

        assert result.num_samples == 1
        assert result.confidence_score == 1.0
        assert provider.call_count == 1

    def test_identical_candidates_shortcut(self):
        """Should use shortcut when all candidates are identical."""
        # Same response for all samples
        provider = MockLLMProvider("```prolog\nfoo(X).\n```")
        request = LLMRequest(prompt="Generate rules")

        result = generate_with_self_consistency(request, provider, num_samples=3)

        assert result.is_unanimous
        assert result.confidence_score == 1.0
        assert provider.call_count == 3

    @patch("src.core.self_consistency.FeedbackClient")
    def test_multiple_distinct_candidates(self, mock_feedback_class):
        """Should compute similarity matrix for distinct candidates."""
        # Different responses
        responses = [
            "```prolog\ncandidate1(X).\n```",
            "```prolog\ncandidate2(X).\n```",
            "```prolog\ncandidate3(X).\n```",
        ]
        provider = MockLLMProvider(responses)
        request = LLMRequest(prompt="Generate rules")

        # Mock the feedback client
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.similarity = 0.6
        mock_client.evaluate.return_value = mock_result
        mock_feedback_class.return_value = mock_client

        result = generate_with_self_consistency(request, provider, num_samples=3)

        assert result.num_samples == 3
        assert not result.is_unanimous
        assert 0.0 <= result.confidence_score <= 1.0
        assert len(result.similarity_matrix) == 3
        assert len(result.average_similarities) == 3

    @patch("src.core.self_consistency.FeedbackClient")
    def test_selects_most_consistent_candidate(self, mock_feedback_class):
        """Should select the candidate with highest average similarity."""
        responses = [
            "```prolog\noutlier(X).\n```",  # Will have low similarity
            "```prolog\nconsensus1(X).\n```",  # Will have high similarity
            "```prolog\nconsensus2(X).\n```",  # Will have high similarity
        ]
        provider = MockLLMProvider(responses)
        request = LLMRequest(prompt="Generate rules")

        # Mock varying similarities
        mock_client = MagicMock()

        def side_effect(generated_rules, ground_truth_rules, generate_feedback):
            result = MagicMock()
            # Make candidate 1 have highest average similarity
            if "outlier" in generated_rules or "outlier" in ground_truth_rules:
                result.similarity = 0.3  # Low similarity to others
            else:
                result.similarity = 0.9  # High similarity between consensus candidates
            return result

        mock_client.evaluate.side_effect = side_effect
        mock_feedback_class.return_value = mock_client

        result = generate_with_self_consistency(request, provider, num_samples=3)

        # Candidate 1 or 2 (the consensus ones) should be selected
        assert result.best_candidate_index in [1, 2]
        assert "consensus" in result.best_candidate

    def test_returns_all_required_fields(self):
        """Should return result with all required fields populated."""
        provider = MockLLMProvider("```prolog\nfoo(X).\n```")
        request = LLMRequest(prompt="Generate rules")

        result = generate_with_self_consistency(request, provider, num_samples=2)

        assert isinstance(result.best_candidate, str)
        assert isinstance(result.best_candidate_index, int)
        assert isinstance(result.confidence_score, float)
        assert isinstance(result.all_candidates, list)
        assert isinstance(result.similarity_matrix, list)
        assert isinstance(result.average_similarities, list)


# ============================================================
# Integration test
# ============================================================


class TestIntegration:
    """Integration tests using MockLLMProvider."""

    def test_basic_workflow(self):
        """Test basic workflow with mock provider (identical responses)."""
        provider = MockLLMProvider(
            "```prolog\ninitiatedAt(gap(Vessel)=true, T) :- happensAt(gap_start(Vessel), T).\n```"
        )
        request = LLMRequest(prompt="Generate gap fluent rules")

        result = generate_with_self_consistency(request, provider, num_samples=3)

        assert result.num_samples == 3
        assert "initiatedAt(gap(Vessel)" in result.best_candidate
        assert result.confidence_score == 1.0  # All identical
        assert result.is_unanimous
