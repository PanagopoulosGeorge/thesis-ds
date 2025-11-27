"""Tests for SimLP client."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from src.core.models import EvaluationResult
from src.simlp.client import SimLPClient

class TestSimLPClientInitialization:
    """Tests for SimLPClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        client = SimLPClient()

        assert client.reference_rules_dir is None
        assert client.log_dir.exists()

    def test_init_with_custom_dirs(self, tmp_path):
        """Test initialization with custom directories."""
        ref_dir = tmp_path / "references"
        log_dir = tmp_path / "logs"

        client = SimLPClient(
            reference_rules_dir=str(ref_dir),
            log_dir=str(log_dir)
        )

        assert client.reference_rules_dir == ref_dir
        assert client.log_dir == log_dir
        assert log_dir.exists()

    def test_init_creates_log_dir(self, tmp_path):
        """Test that initialization creates log directory if needed."""
        log_dir = tmp_path / "nonexistent" / "logs"

        client = SimLPClient(log_dir=str(log_dir))

        assert log_dir.exists()

class TestSimLPClientEvaluate:
    """Tests for SimLPClient.evaluate method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = SimLPClient()
        self.generated_rules = """
        initiatedAt(gap(Vessel)=nearPorts, T) :-
            happensAt(gap_start(Vessel), T),
            holdsAt(withinArea(Vessel, nearPorts)=true, T).
        """
        self.reference_rules = """
        initiatedAt(gap(Vessel)=nearPorts, T) :-
            happensAt(gap_start(Vessel), T),
            holdsAt(withinArea(Vessel, nearPorts)=true, T).
        """

    @patch('src.simlp.client.parse_and_compute_distance')

    def test_evaluate_with_reference_rules(self, mock_parse):
        """Test evaluate with provided reference rules."""
        # Mock SimLP response with feedback
        mock_parse.return_value = (
            np.array([0]),  # optimal_matching
            np.array([0.1]),  # distances
            0.95,  # similarity
            {'gap(Vessel)=nearPorts': {'suggestions': ['Good match']}}
        )

        result = self.client.evaluate(
            domain='MSA',
            activity='gap',
            generated_rules=self.generated_rules,
            reference_rules=self.reference_rules,
            generate_feedback=True
        )

        # Verify mock was called correctly
        mock_parse.assert_called_once()
        call_args = mock_parse.call_args
        assert call_args[1]['generated_event_description'] == self.generated_rules
        assert call_args[1]['ground_event_description'] == self.reference_rules
        assert call_args[1]['generate_feedback'] is True

        # Verify result
        assert isinstance(result, EvaluationResult)
        assert result.rule_id == 'MSA_gap'
        assert result.score == 0.95
        assert result.matches_reference is True
        assert 'gap(Vessel)=nearPorts' in result.feedback
        assert result.reference_rule == self.reference_rules

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_evaluate_without_feedback(self, mock_parse):
        """Test evaluate without feedback generation."""
        mock_parse.return_value = (
            np.array([0]),
            np.array([0.2]),
            0.85,
            0  # No feedback
        )

        result = self.client.evaluate(
            domain='MSA',
            activity='gap',
            generated_rules=self.generated_rules,
            reference_rules=self.reference_rules,
            generate_feedback=False
        )

        assert result.score == 0.85
        assert result.matches_reference is False  # Below 0.9 threshold
        assert 'No detailed feedback available' in result.feedback

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_evaluate_loads_reference_from_file(self, mock_parse, tmp_path):
        """Test evaluate loads reference rules from file."""
        # Create reference file
        ref_dir = tmp_path / "references" / "MSA"
        ref_dir.mkdir(parents=True)
        ref_file = ref_dir / "gap.pl"
        ref_file.write_text(self.reference_rules)

        client = SimLPClient(reference_rules_dir=str(tmp_path / "references"))

        mock_parse.return_value = (
            np.array([0]),
            np.array([0.1]),
            0.95,
            {}
        )

        result = client.evaluate(
            domain='MSA',
            activity='gap',
            generated_rules=self.generated_rules
        )

        # Verify reference was loaded
        call_args = mock_parse.call_args
        assert call_args[1]['ground_event_description'] == self.reference_rules
        assert result.score == 0.95

    def test_evaluate_raises_error_without_reference(self):
        """Test evaluate raises error when reference not found."""
        with pytest.raises(ValueError, match="reference_rules_dir not set"):
            self.client.evaluate(
                domain='MSA',
                activity='gap',
                generated_rules=self.generated_rules
            )

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_evaluate_handles_simlp_errors(self, mock_parse):
        """Test evaluate handles SimLP errors gracefully."""
        mock_parse.side_effect = Exception("SimLP parsing error")

        with pytest.raises(RuntimeError, match="SimLP evaluation failed"):
            self.client.evaluate(
                domain='MSA',
                activity='gap',
                generated_rules=self.generated_rules,
                reference_rules=self.reference_rules
            )

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_evaluate_handles_none_result(self, mock_parse):
        """Test evaluate handles None result from SimLP."""
        mock_parse.return_value = None

        with pytest.raises(RuntimeError, match="returned None"):
            self.client.evaluate(
                domain='MSA',
                activity='gap',
                generated_rules=self.generated_rules,
                reference_rules=self.reference_rules
            )

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_evaluate_similarity_thresholds(self, mock_parse):
        """Test different similarity score thresholds."""
        test_cases = [
            (0.95, True, 0),  # High similarity, matches
            (0.90, True, 0),  # Threshold, matches
            (0.89, False, 1),  # Just below, doesn't match
            (0.50, False, 1),  # Moderate, doesn't match
            (0.30, False, 1),  # Low, doesn't match
        ]

        for similarity, should_match, min_issues in test_cases:
            mock_parse.return_value = (
                np.array([0]),
                np.array([1 - similarity]),
                similarity,
                {}
            )

            result = self.client.evaluate(
                domain='MSA',
                activity='gap',
                generated_rules=self.generated_rules,
                reference_rules=self.reference_rules
            )

            assert result.score == similarity
            assert result.matches_reference == should_match
            assert len(result.issues) >= min_issues

class TestSimLPClientReferenceLoading:
    """Tests for reference rules loading."""

    def test_load_reference_rules_from_pl_file(self, tmp_path):
        """Test loading reference rules from .pl file."""
        ref_dir = tmp_path / "refs" / "MSA"
        ref_dir.mkdir(parents=True)
        ref_file = ref_dir / "gap.pl"
        ref_file.write_text("test content")

        client = SimLPClient(reference_rules_dir=str(tmp_path / "refs"))
        content = client._load_reference_rules('MSA', 'gap')

        assert content == "test content"

    def test_load_reference_rules_from_prolog_file(self, tmp_path):
        """Test loading reference rules from .prolog file."""
        ref_dir = tmp_path / "refs" / "HAR"
        ref_dir.mkdir(parents=True)
        ref_file = ref_dir / "moving.prolog"
        ref_file.write_text("prolog content")

        client = SimLPClient(reference_rules_dir=str(tmp_path / "refs"))
        content = client._load_reference_rules('HAR', 'moving')

        assert content == "prolog content"

    def test_load_reference_rules_flat_structure(self, tmp_path):
        """Test loading from flat directory structure."""
        ref_dir = tmp_path / "refs"
        ref_dir.mkdir()
        ref_file = ref_dir / "MSA_gap.pl"
        ref_file.write_text("flat structure")

        client = SimLPClient(reference_rules_dir=str(ref_dir))
        content = client._load_reference_rules('MSA', 'gap')

        assert content == "flat structure"

    def test_load_reference_rules_not_found(self, tmp_path):
        """Test error when reference rules not found."""
        ref_dir = tmp_path / "refs"
        ref_dir.mkdir()

        client = SimLPClient(reference_rules_dir=str(ref_dir))

        with pytest.raises(ValueError, match="Reference rules not found"):
            client._load_reference_rules('MSA', 'nonexistent')

class TestSimLPClientFeedbackFormatting:
    """Tests for feedback formatting."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = SimLPClient()
        self.log_file = Path(tempfile.gettempdir()) / "test.log"

    def test_format_feedback_empty(self):
        """Test formatting empty feedback."""
        feedback = self.client._format_feedback({}, self.log_file)

        assert "No detailed feedback available" in feedback
        assert str(self.log_file) in feedback

    def test_format_feedback_with_data(self):
        """Test formatting feedback with data."""
        feedback_data = {
            'gap(Vessel)=nearPorts': {
                'missing_rules': ['rule1', 'rule2'],
                'extra_rules': ['rule3'],
                'mismatched_rules': [],
                'suggestions': ['Add rule1', 'Remove rule3']
            }
        }

        feedback = self.client._format_feedback(feedback_data, self.log_file)

        assert 'gap(Vessel)=nearPorts' in feedback
        assert 'Missing rules: 2' in feedback
        assert 'Extra rules: 1' in feedback
        assert 'Add rule1' in feedback
        assert 'Remove rule3' in feedback

    def test_format_feedback_multiple_concepts(self):
        """Test formatting feedback for multiple concepts."""
        feedback_data = {
            'concept1': {'suggestions': ['Fix concept1']},
            'concept2': {'missing_rules': ['rule1']}
        }

        feedback = self.client._format_feedback(feedback_data, self.log_file)

        assert 'concept1' in feedback
        assert 'concept2' in feedback
        assert 'Fix concept1' in feedback
        assert 'Missing rules: 1' in feedback

class TestSimLPClientIssueExtraction:
    """Tests for issue extraction."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = SimLPClient()

    def test_extract_issues_high_similarity(self):
        """Test issue extraction with high similarity."""
        issues = self.client._extract_issues({}, 0.95)

        assert len(issues) == 0

    def test_extract_issues_moderate_similarity(self):
        """Test issue extraction with moderate similarity."""
        issues = self.client._extract_issues({}, 0.75)

        assert len(issues) == 1
        assert 'Moderate similarity' in issues[0]

    def test_extract_issues_low_similarity(self):
        """Test issue extraction with low similarity."""
        issues = self.client._extract_issues({}, 0.3)

        assert len(issues) == 1
        assert 'Low similarity' in issues[0]

    def test_extract_issues_from_feedback_data(self):
        """Test extracting issues from feedback data."""
        feedback_data = {
            'gap': {
                'missing_rules': ['r1', 'r2'],
                'extra_rules': ['r3'],
                'mismatched_rules': ['r4', 'r5']
            },
            'loitering': {
                'missing_rules': ['r6']
            }
        }

        issues = self.client._extract_issues(feedback_data, 0.95)

        assert len(issues) >= 4
        assert any(
            'gap' in issue and 'Missing 2 rule' in issue for issue in issues
        )
        assert any(
            'gap' in issue and '1 extra rule' in issue for issue in issues
        )
        assert any(
            'gap' in issue and '2 mismatched rule' in issue
            for issue in issues
        )
        assert any(
            'loitering' in issue and 'Missing 1 rule' in issue
            for issue in issues
        )


class TestSimLPClientIntegration:
    """Integration tests for SimLPClient."""

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_end_to_end_evaluation_flow(self, mock_parse, tmp_path):
        """Test complete evaluation flow."""
        # Setup
        ref_dir = tmp_path / "refs" / "MSA"
        ref_dir.mkdir(parents=True)
        ref_file = ref_dir / "gap.pl"
        ref_file.write_text("reference rules")

        log_dir = tmp_path / "logs"

        client = SimLPClient(
            reference_rules_dir=str(tmp_path / "refs"),
            log_dir=str(log_dir)
        )

        # Mock SimLP
        mock_parse.return_value = (
            np.array([0, 1]),
            np.array([0.1, 0.2]),
            0.88,
            {
                'gap(Vessel)=nearPorts': {
                    'missing_rules': ['rule1'],
                    'suggestions': ['Add initiatedAt rule']
                }
            }
        )

        # Execute
        result = client.evaluate(
            domain='MSA',
            activity='gap',
            generated_rules="generated rules"
        )

        # Verify
        assert result.rule_id == 'MSA_gap'
        assert result.score == 0.88
        assert result.matches_reference is False
        assert len(result.issues) > 0
        assert 'gap(Vessel)=nearPorts' in result.feedback
        assert 'Add initiatedAt rule' in result.feedback
        assert result.metadata['domain'] == 'MSA'
        assert result.metadata['activity'] == 'gap'
        assert len(result.metadata['optimal_matching']) == 2
        assert len(result.metadata['distances']) == 2

    @patch('src.simlp.client.parse_and_compute_distance')
    def test_perfect_match_scenario(self, mock_parse):
        """Test scenario with perfect rule match."""
        mock_parse.return_value = (
            np.array([0]),
            np.array([0.0]),
            1.0,
            {'gap': {'suggestions': []}}
        )

        client = SimLPClient()
        result = client.evaluate(
            domain='MSA',
            activity='gap',
            generated_rules="rules",
            reference_rules="rules"
        )

        assert result.score == 1.0
        assert result.matches_reference is True
        assert len(result.issues) == 0
