"""SimLP client for evaluating RTEC rules using similarity metrics."""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional

from simlp import parse_and_compute_distance

from src.core.models import EvaluationResult


class SimLPClient:
    """
    Client for evaluating RTEC rules using SimLP similarity metrics.
    
    This class wraps the SimLP parse_and_compute_distance function and provides
    a cleaner interface for evaluating generated RTEC rules against reference
    implementations.
    """
    
    def __init__(
        self,
        reference_rules_dir: Optional[str] = None,
        log_dir: Optional[str] = None
    ):
        """
        Initialize the SimLP client.
        
        Args:
            reference_rules_dir: Directory containing reference RTEC rules.
                If None, rules must be provided directly to evaluate().
            log_dir: Directory for SimLP log files. If None, uses temp directory.
        """
        self.reference_rules_dir = (
            Path(reference_rules_dir) if reference_rules_dir else None
        )
        self.log_dir = (
            Path(log_dir) if log_dir else Path('./../logs/simlp/' + 
                                               f'{tempfile.mkdtemp()}')
        )
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def evaluate(
        self,
        domain: str,
        activity: str,
        generated_rules: str,
        reference_rules: Optional[str] = None,
        generate_feedback: bool = True
    ) -> EvaluationResult:
        """
        Evaluate generated RTEC rules against reference rules.
        
        Args:
            domain: Domain name (e.g., 'MSA', 'HAR').
            activity: Activity name (e.g., 'gap', 'loitering').
            generated_rules: Generated RTEC rules as a string.
            reference_rules: Reference RTEC rules as a string. If None,
                attempts to load from reference_rules_dir.
            generate_feedback: Whether to generate detailed feedback.
                
        Returns:
            EvaluationResult containing similarity score, feedback, and metadata.
            
        Raises:
            ValueError: If reference rules cannot be found or loaded.
            RuntimeError: If SimLP evaluation fails.
        """
        # Load reference rules if not provided
        if reference_rules is None:
            reference_rules = self._load_reference_rules(domain, activity)
            
        # Create log file for this evaluation
        log_file = self.log_dir / f"simlp_{domain}_{activity}.log"
        
        try:
            # Call SimLP evaluation
            result = parse_and_compute_distance(
                generated_event_description=generated_rules,
                ground_event_description=reference_rules,
                log_file=str(log_file),
                generate_feedback=generate_feedback
            )
            
            if result is None or result[0] is None:
                raise RuntimeError(
                    "SimLP evaluation returned None - likely parsing error"
                )
            
            # Unpack results
            if generate_feedback:
                optimal_matching, distances, similarity, feedback_data = result
            else:
                optimal_matching, distances, similarity, _ = result
                feedback_data = {}
                
        except Exception as e:
            raise RuntimeError(f"SimLP evaluation failed: {e}") from e
        
        # Format feedback from SimLP output
        feedback_text = self._format_feedback(feedback_data, log_file)
        
        # Determine if rules match reference (threshold: 0.9)
        matches_reference = similarity >= 0.9
        
        # Extract issues from feedback data
        issues = self._extract_issues(feedback_data, similarity)
        
        return EvaluationResult(
            rule_id=f"{domain}_{activity}",
            score=similarity,
            matches_reference=matches_reference,
            feedback=feedback_text,
            reference_rule=reference_rules,
            issues=issues,
            metadata={
                'domain': domain,
                'activity': activity,
                'log_file': str(log_file),
                'optimal_matching': (
                    optimal_matching.tolist()
                    if optimal_matching is not None else []
                ),
                'distances': (
                    distances.tolist() if distances is not None else []
                ),
                'feedback_data': feedback_data if generate_feedback else {}
            }
        )
    
    def _load_reference_rules(self, domain: str, activity: str) -> str:
        """
        Load reference rules from file.
        
        Args:
            domain: Domain name.
            activity: Activity name.
            
        Returns:
            Reference rules as string.
            
        Raises:
            ValueError: If reference rules directory not set or file not found.
        """
        if self.reference_rules_dir is None:
            raise ValueError(
                "reference_rules_dir not set. Provide reference_rules directly "
                "or set reference_rules_dir during initialization."
            )
        
        # Try multiple possible file patterns
        possible_paths = [
            self.reference_rules_dir / domain / f"{activity}.pl",
            self.reference_rules_dir / domain / f"{activity}.prolog",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.read_text()
        
        raise ValueError(
            f"Reference rules not found for {domain}/{activity}. "
            f"Tried paths: {[str(p) for p in possible_paths]}"
        )
    
    def _format_feedback(
        self,
        feedback_data: Dict,
        log_file: Path
    ) -> str:
        """
        Format feedback from SimLP output.
        
        Args:
            feedback_data: Feedback dictionary from SimLP.
            log_file: Path to log file with detailed output.
            
        Returns:
            Formatted feedback string.
        """
        if not feedback_data:
            return (
                f"No detailed feedback available. "
                f"Check log file for details: {log_file}"
            )
        
        feedback_parts = []
        
        for concept, data in feedback_data.items():
            feedback_parts.append(f"\n=== Feedback for {concept} ===")
            
            if isinstance(data, dict):
                # Extract relevant feedback information
                if 'missing_rules' in data:
                    feedback_parts.append(
                        f"Missing rules: {len(data['missing_rules'])}"
                    )
                if 'extra_rules' in data:
                    feedback_parts.append(
                        f"Extra rules: {len(data['extra_rules'])}"
                    )
                if 'mismatched_rules' in data:
                    feedback_parts.append(
                        f"Mismatched rules: {len(data['mismatched_rules'])}"
                    )
                if 'suggestions' in data:
                    feedback_parts.append("\nSuggestions:")
                    for suggestion in data['suggestions']:
                        feedback_parts.append(f"  - {suggestion}")
            else:
                feedback_parts.append(str(data))
        
        feedback_parts.append(f"\n\nDetailed log: {log_file}")
        
        return "\n".join(feedback_parts)
    
    def _extract_issues(
        self,
        feedback_data: Dict,
        similarity: float
    ) -> list:
        """
        Extract issues from feedback data.
        
        Args:
            feedback_data: Feedback dictionary from SimLP.
            similarity: Overall similarity score.
            
        Returns:
            List of issue descriptions.
        """
        issues = []
        
        if similarity < 0.5:
            issues.append(
                "Low similarity score - significant differences from reference"
            )
        elif similarity < 0.9:
            issues.append("Moderate similarity - minor improvements needed")
        
        if not feedback_data:
            return issues
        
        for concept, data in feedback_data.items():
            if isinstance(data, dict):
                if data.get('missing_rules'):
                    issues.append(
                        f"{concept}: Missing {len(data['missing_rules'])} rule(s)"
                    )
                if data.get('extra_rules'):
                    issues.append(
                        f"{concept}: {len(data['extra_rules'])} extra rule(s)"
                    )
                if data.get('mismatched_rules'):
                    num_mismatched = len(data['mismatched_rules'])
                    issues.append(
                        f"{concept}: {num_mismatched} mismatched rule(s)"
                    )
        
        return issues
