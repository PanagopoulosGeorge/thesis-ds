# Architecture Overview

This document describes the architecture of the feedback loop system for iterative RTEC rule generation.

## Key Components

1. **LoopOrchestrator**: Main controller implementing the feedback loop algorithm
2. **Prompt Builders**: Domain-specific prompt construction (MSA, HAR)
3. **LLM Providers**: Abstraction layer for LLM APIs (OpenAI, etc.)
4. **SimLP Client**: Rule evaluation and feedback generation
5. **Logging System**: Comprehensive logging with file output
6. **Data Models**: Pydantic models for type safety and validation

# Component Interactions

## 1. **Prompt Building Pipeline**

```mermaid
sequenceDiagram
    participant User
    participant Builder as PromptBuilder
    participant RTEC as RTEC Prompts
    participant Domain as Domain Prompts
    participant Examples as Examples
    
    User->>Builder: build_initial("gap")
    Builder->>RTEC: Load base prompts
    RTEC-->>Builder: system_1, system_2, system_3
    Builder->>RTEC: Load fluent definitions
    RTEC-->>Builder: simple/static definitions
    Builder->>Domain: Load domain-specific
    Domain-->>Builder: MSA events, fluents, BK
    Builder->>Examples: Load examples
    Examples-->>Builder: Simple & static examples
    Builder->>Examples: get_examples("both")
    Examples-->>Builder: Combined examples
    Builder->>Builder: Format all into messages
    Builder-->>User: [system_msg, user_msg]
```

## 2. **LLM Provider Flow**

```mermaid
sequenceDiagram
    participant App as Application
    participant Factory as ProviderFactory
    participant Provider as OpenAIProvider
    participant API as OpenAI API
    
    App->>Factory: create("openai", api_key)
    Factory->>Provider: __init__(api_key)
    Factory-->>App: provider instance
    
    App->>Provider: generate_from_messages(msgs)
    Provider->>Provider: Start latency timer
    Provider->>API: chat.completions.create()
    API-->>Provider: completion response
    Provider->>Provider: End latency timer
    Provider->>Provider: Extract content & tokens
    Provider->>Provider: _create_response()
    Provider-->>App: LLMResponse
```

## 3. **Feedback Loop Cycle**

```mermaid
flowchart TD
    Start([Start Loop]) --> InitLog[Initialize Logger<br/>+ LoopState]
    InitLog --> LogStart[Log: Starting feedback loop]
    LogStart --> BuildPrompt[Build Initial Prompt<br/>from Builder]
    BuildPrompt --> LogGenerate[Log: Calling LLM]
    LogGenerate --> CallLLM[Call LLM Provider<br/>generate_from_messages]
    CallLLM --> LogResponse[Log: Tokens + Latency]
    LogResponse --> ParseRules[Parse Generated Rules]
    ParseRules --> LogEval[Log: Evaluating rules]
    LogEval --> Evaluate[Evaluate Rules<br/>using SimLP]
    
    Evaluate --> LogIterComplete[Log: Iteration complete<br/>Score + Convergence]
    LogIterComplete --> CheckScore{Score >= Threshold?}
    CheckScore -->|Yes| Converged[Mark Converged]
    CheckScore -->|No| CheckIter{Max Iterations?}
    
    CheckIter -->|Reached| LogFinal[Log: Final summary]
    CheckIter -->|Not Reached| LogRefine[Log: Starting refinement]
    LogRefine --> BuildRefinement[Build Refinement Prompt<br/>with prev_rules + feedback]
    
    BuildRefinement --> LogGenerate
    Converged --> LogFinal
    LogFinal --> Stop[Return Final Results]
    
    Stop --> Results([FinalResult with<br/>best rules & evaluations])
```

**Usage Examples:**
```python
# Verbose logging with file output
orchestrator = LoopOrchestrator(
    ...,
    verbose=True,
    log_dir="./logs"
)

# Custom log file
orchestrator = LoopOrchestrator(
    ...,
    log_file="./experiments/run_001.log"
)

# Custom logger
from src.loop.logging_config import setup_orchestrator_logging
logger = setup_orchestrator_logging(verbose=True)
orchestrator = LoopOrchestrator(..., logger=logger)
```

## 5. **Orchestrator Algorithm**

The `LoopOrchestrator` implements Algorithm 1 from the thesis:

```python
def run(domain: str, activity: str) -> FinalResult:
    """
    Algorithm Implementation:
    1. Generate initial rules using prompt builder + LLM
    2. Evaluate rules using SimLP
    3. While not converged and iterations < max:
         a. Build refinement prompt with feedback
         b. Generate refined rules
         c. Evaluate refined rules
         d. Check convergence (score >= threshold)
    4. Return best rules and statistics
    """
```

**Key Methods:**

- `_generate_initial_rules(activity)`: Build prompt → LLM → Extract rules
- `_refine_rules(activity, rules, feedback, attempt)`: Refinement prompt → LLM → Extract
- `_evaluate_rules(domain, activity, rules)`: Call SimLP with feedback generation
- `_should_continue(iteration, eval, history)`: Check convergence criteria
- `_record_iteration(response, evaluation)`: Track state and metrics
- `_extract_rules_from_response(response)`: Parse Prolog rules from LLM output
- `_build_final_result(reason)`: Calculate statistics and identify best iteration

**Convergence Criteria:**
1. Similarity score >= threshold (configurable, default 0.9)
2. Maximum iterations reached (configurable, default 5)

**State Tracking:**
- Each iteration creates a `LoopState` with requests, responses, evaluations
- History preserved for analysis and debugging
- Best rules tracked across all iterations (not necessarily the last one)

**Statistics Calculated:**
- Total/average tokens used
- Total/average latency
- Improvement (final - initial score)
- Improvement rate (improvement / iterations)
- Best iteration number and score


## File Organization

```
feedback-loop/
├── src/
│   ├── core/
│   │   └── models.py          # Pydantic models for all data structures
│   ├── prompts/
│   │   ├── builder.py         # Prompt builder classes
│   │   ├── rtec_base.py       # Core RTEC prompts
│   │   ├── msa_domain.py      # MSA domain knowledge
│   │   ├── msa_examples.py    # MSA examples
│   │   ├── msa_requests.py    # MSA activity descriptions
│   │   ├── har_domain.py      # HAR domain knowledge
│   │   ├── har_examples.py    # HAR examples
│   │   └── har_requests.py    # HAR activity descriptions
│   ├── llm/
│   │   ├── provider_base.py   # Abstract provider interface
│   │   ├── provider_openai.py # OpenAI implementation
│   │   └── factory.py         # Provider factory
│   ├── loop/
│   │   ├── orchestrator.py    # Feedback loop orchestration
│   │   └── logging_config.py  # Logging configuration
│   ├── simlp/
│   │   └── client.py          # SimLP evaluation client
│   └── cli/
│       └── main.py            # Command-line interface
├── tests/
│   ├── test_models.py         # Core model tests
│   ├── test_prompts.py        # RTEC prompt tests
│   ├── test_loop_orchestrator.py # Orchestrator tests (27 tests)
│   └── test_llm_provider.py   # Provider tests
├── notebooks/
│   └── feedback_loop_usage.ipynb # Tutorial notebook
├── docs/
│   └── LOGGING_GUIDE.md       # Comprehensive logging guide
└── logs/                      # Auto-generated log files
```
