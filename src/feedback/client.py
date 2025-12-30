from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from simlp.run import parse_and_compute_distance


@dataclass
class FeedbackResult:
    similarity: float
    optimal_matching: Any
    distances: Any
    feedback: Optional[Dict[str, Any]]
    log_file: Path


class FeedbackClient:
    def __init__(self, log_file: str | Path = "logs/simlp_feedback.log"):
        self.log_file = Path(log_file)

    def evaluate(
        self,
        generated_rules: str,
        ground_truth_rules: str,
        *,
        generate_feedback: bool = True,
    ) -> FeedbackResult:
        # Ensure log directory exists before simLP writes
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        optimal_matching, distances, similarity, feedback = parse_and_compute_distance(
            generated_event_description=generated_rules,
            ground_event_description=ground_truth_rules,
            log_file=str(self.log_file),
            generate_feedback=generate_feedback,
        )

        return FeedbackResult(
            similarity=similarity,
            optimal_matching=optimal_matching,
            distances=distances,
            feedback=feedback if generate_feedback else None,
            log_file=self.log_file,
        )

    def render_feedback(self, result: FeedbackResult) -> str:
        """Flatten structured feedback (if any) into plain text for LLM prompts."""
        if not result.feedback:
            return "No structured feedback available."
        
        # Handle case where feedback is already a string
        if isinstance(result.feedback, str):
            return result.feedback
        
        # Handle dict-based feedback
        sections = []
        for concept, data in result.feedback.items():
            sections.append(f"[{concept}]\n{data}")
        return "\n\n".join(sections)


if __name__ == "__main__":
    # Toy Prolog rules for comparison
    generated = """
    initiatedAt(highSpeedNearCoast(Vessel) = true, T) :-
        happensAt(velocity(Vessel, Speed), T),
        holdsAt(nearCoast(Vessel) = true, T),
        greater(Speed, 5).
    """

    ground = """
    initiatedAt(highSpeedNearCoast(Vessel) = true, T) :-
        happensAt(velocity(Vessel, Speed, _, _), T),
        greater(Speed, 5),
        holdsAt(withinArea(Vessel, nearCoast) = true, T).
    """

    client = FeedbackClient(log_file="logs/demo_feedback.log")
    result = client.evaluate(generated, ground, generate_feedback=True)
    feedback_text = client.render_feedback(result)

    print(f"Similarity: {result.similarity}")
    print("\nFeedback:\n", feedback_text)
    print(f"\nLog written to: {result.log_file}")