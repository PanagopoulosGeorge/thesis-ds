# SimLP Integration

This module provides a clean interface for evaluating RTEC rules using the SimLP similarity metric.

## Overview

The `SimLPClient` wraps the SimLP `parse_and_compute_distance` function and provides:
- Automatic loading of reference rules from files
- Structured evaluation results with feedback
- Issue extraction and scoring
- Integration with the `EvaluationResult` model

## Basic Usage

```python
from src.simlp import SimLPClient

# Initialize client
client = SimLPClient()

# Evaluate generated rules against reference
generated_rules = """
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).
"""

reference_rules = """
initiatedAt(gap(Vessel)=nearPorts, T) :-
    happensAt(gap_start(Vessel), T),
    holdsAt(withinArea(Vessel, nearPorts)=true, T).
"""

result = client.evaluate(
    domain='MSA',
    activity='gap',
    generated_rules=generated_rules,
    reference_rules=reference_rules,
    generate_feedback=True
)

print(f"Similarity: {result.score}")
print(f"Matches reference: {result.matches_reference}")
print(f"Feedback: {result.feedback}")
print(f"Issues: {result.issues}")
```

## Using Reference Files

Store reference rules in a directory structure:

```
references/
  MSA/
    gap.pl
    loitering.pl
    highSpeedNearCoast.pl
  HAR/
    leaving_object.pl
    moving.pl
```

Then load them automatically:

```python
client = SimLPClient(
    reference_rules_dir='path/to/references',
    log_dir='path/to/logs'
)

# Reference rules loaded automatically from references/MSA/gap.pl
result = client.evaluate(
    domain='MSA',
    activity='gap',
    generated_rules=generated_rules
)
```

## Evaluation Result

The `evaluate()` method returns an `EvaluationResult` object with:

- `rule_id`: Identifier for the evaluated rules (e.g., "MSA_gap")
- `score`: Similarity score from 0.0 to 1.0
- `matches_reference`: Boolean indicating if similarity >= 0.9
- `feedback`: Formatted feedback string with suggestions
- `reference_rule`: The reference rules used for comparison
- `issues`: List of specific issues found
- `metadata`: Additional data including:
  - `domain`: Domain name
  - `activity`: Activity name
  - `log_file`: Path to detailed SimLP log
  - `optimal_matching`: Rule matching indices
  - `distances`: Distance values per rule pair
  - `feedback_data`: Raw feedback from SimLP

## Similarity Thresholds

- **>= 0.9**: Rules match reference (perfect or near-perfect)
- **0.5 - 0.9**: Moderate similarity, minor improvements needed
- **< 0.5**: Low similarity, significant differences

## Feedback Generation

Enable detailed feedback to get actionable suggestions:

```python
result = client.evaluate(
    domain='MSA',
    activity='gap',
    generated_rules=generated_rules,
    reference_rules=reference_rules,
    generate_feedback=True  # Detailed feedback
)

# Access structured feedback
for issue in result.issues:
    print(f"Issue: {issue}")

# Access raw feedback data
feedback_data = result.metadata['feedback_data']
for concept, data in feedback_data.items():
    if 'suggestions' in data:
        for suggestion in data['suggestions']:
            print(f"Suggestion for {concept}: {suggestion}")
```

## Integration with Feedback Loop

The SimLPClient is designed to integrate seamlessly with the feedback loop:

```python
from src.simlp import SimLPClient
from src.prompts.builder import MSAPromptBuilder
from src.llm import ProviderFactory

# Setup
client = SimLPClient(reference_rules_dir='references')
builder = MSAPromptBuilder()
provider = ProviderFactory.create('openai', api_key='...')

# Generate initial rules
messages = builder.build_initial('gap')
response = provider.generate_from_messages(messages, model='gpt-4')
generated_rules = response.content

# Evaluate
result = client.evaluate(
    domain='MSA',
    activity='gap',
    generated_rules=generated_rules,
    generate_feedback=True
)

# Check if refinement needed
if not result.matches_reference:
    # Build refinement prompt with feedback
    refinement_messages = builder.build_refinement(
        activity='gap',
        prev_rules=generated_rules,
        feedback=result.feedback,
        attempt=2
    )
    # Generate improved rules
    refined_response = provider.generate_from_messages(
        refinement_messages,
        model='gpt-4'
    )
```

## Error Handling

```python
from src.simlp import SimLPClient

client = SimLPClient()

try:
    result = client.evaluate(
        domain='MSA',
        activity='gap',
        generated_rules=generated_rules,
        reference_rules=reference_rules
    )
except ValueError as e:
    # Reference rules not found or invalid input
    print(f"Validation error: {e}")
except RuntimeError as e:
    # SimLP evaluation failed (parsing error, etc.)
    print(f"Evaluation error: {e}")
```

## File Structure Support

The client supports multiple file naming patterns:

```
# Nested by domain
references/MSA/gap.pl
references/MSA/gap.prolog

# Flat structure
references/MSA_gap.pl
references/MSA_gap.prolog
```

## Logging

SimLP generates detailed logs for each evaluation:

```python
client = SimLPClient(log_dir='logs')

result = client.evaluate(...)

# Log file path included in metadata
log_path = result.metadata['log_file']
print(f"Detailed log: {log_path}")
```

## Testing

See `tests/test_simlp_client.py` for comprehensive examples including:
- Initialization patterns
- Reference loading strategies
- Feedback formatting
- Issue extraction
- Mock-based testing of SimLP integration
