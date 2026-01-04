### Setup & Full Documentation

This document is the **single source of truth** for how to:

- **download, install, and run** the project
- run the **CLI** and the included **examples**
- understand the **project structure** and configuration knobs
- **add a new domain** (prompt builder + domain knowledge + requests + tests)
- **add a new LLM provider** (provider class + factory registration + env vars)

---

### Requirements

- **Python**: 3.9+
- **OS**: tested on macOS/Linux (Windows should work with a venv, but is not explicitly tested)
- **Network access**: required at install time because `simlp` is installed from a Git URL (see `pyproject.toml`)

---

### Download / clone

If you already have the repo, skip this.

```bash
git clone <YOUR_REPO_URL>
cd thesis-ds-repo
```

---

### Installation

You can install with either **plain venv + pip** or **uv**. Pick one.

#### Option A: venv + pip (most common)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

#### Option B: uv (fast, reproducible)

If you use `uv`, you can install from `pyproject.toml` / `uv.lock`.

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras
```

---

### Environment variables (`.env`)

The CLI loads environment variables via `python-dotenv` (`load_dotenv()` in `src/cli/main.py`).  
Create a `.env` file in the **repo root**.

#### Minimal (OpenAI)

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=your_key_here
EOF
```

Notes:
- The CLI defaults to reading `OPENAI_API_KEY`, but you can change the env var name with `--api-key-name`.
- Providers may require additional env vars depending on how you implement them (see “Add a new LLM provider”).

---

### Quickstart: run the CLI

The package defines a console script named **`rtec-llm`** (see `[project.scripts]` in `pyproject.toml`).

#### List available domains

```bash
rtec-llm domains
```

#### Run MSA (default provider/model)

```bash
rtec-llm run --domain msa
```

#### Run HAR with explicit model/iterations/threshold

```bash
rtec-llm run --domain har --provider openai --model gpt-4o-mini --max-iterations 3 --convergence-threshold 0.9
```

#### Save outputs + generate plots

```bash
rtec-llm run --domain msa --output ./results/msa_run --visualize
```

Plot modes:
- `--visualize`: generates plots into the output directory
- `--show-plots`: opens plots interactively (requires a GUI backend)
- `--latex`: generates **PDF** plots with “paper-friendly” styling (instead of PNG)

---

### What the CLI actually does (high level)

When you run `rtec-llm run ...`, it wires together:

- a **domain prompt builder** (from `src/prompts/factory.py`)
- an **LLM provider** (from `src/llm/factory.py`)
- **RuleMemory** (stores good fluents so later fluents can depend on them)
- **FeedbackClient** (calls `simlp` to score similarity and produce feedback)
- the **LoopOrchestrator** (runs generate → evaluate → refine until convergence)

Key files:
- `src/core/orchestrator.py`: iterative loop controller
- `src/feedback/client.py`: simLP evaluation + feedback rendering
- `src/utils/code_extractor.py`: extracts ```prolog``` blocks from the LLM response
- `src/cli/main.py`: Typer CLI entrypoint and end-to-end wiring

---

### Running examples (without the CLI)

#### End-to-end orchestrator example (calls OpenAI)

```bash
python examples/run_orchestrator.py
```

#### Offline / no-API example (mock LLM)

This is the fastest way to validate the loop without external calls:

```bash
python examples/test_orchestrator_mock.py
```

It uses `MockLLMProvider` (`src/llm/mock_provider.py`).

---

### Running tests

```bash
pytest
```

Coverage HTML is written to `htmlcov/` (see `pytest` `addopts` in `pyproject.toml`).

---

### Outputs, logs, and artifacts

- **Results JSON**: when `--output` (or `--visualize`) is used, the CLI writes `results.json`
- **Plots**: written into the output directory when `--visualize` is enabled
- **SimLP logs**: default `logs/simlp_feedback.log` (configurable via `FeedbackClient(log_file=...)`)

---

### Configuration knobs (what to tune)

CLI flags map to `OrchestratorConfig` in `src/core/models.py`:

- **`--max-iterations`**: maximum refinement rounds per fluent
- **`--convergence-threshold`**: similarity score \(0.0–1.0\) needed to mark “converged”
- **`--verbose/--quiet`**: controls debug printing and logging verbosity

Memory behavior:
- The CLI constructs `RuleMemory(min_score_threshold=0.7)` (see `src/cli/main.py`).
  Fluents above this score are eligible to be stored and reused as prerequisites.

---

### Add a new domain (prompts + requests + wiring)

Domains are “pluggable”, but there are **two** places you must wire them:

- the **prompt builder registry** (`src/prompts/factory.py`)  
- the **CLI’s request loader** (`src/cli/main.py:get_requests_for_domain`)  

The recommended pattern is to mirror the existing `msa` and `har` modules.

#### 1) Create domain prompt content

Add domain-specific system prompt content and few-shot examples under `src/prompts/`.

Typical files (recommended):

- `src/prompts/<domain>_domain.py`
  - domain events, input fluents, background knowledge text blocks used by the system prompt
- `src/prompts/<domain>_examples.py`
  - few-shot examples that teach the format/style of correct RTEC rules

Use the existing ones as reference:
- `src/prompts/msa_domain.py`, `src/prompts/msa_examples.py`
- `src/prompts/har_domain.py`, `src/prompts/har_examples.py`

#### 2) Implement a `PromptBuilder` for the domain

Create `src/prompts/<domain>_builder.py` similar to:
- `src/prompts/msa_builder.py`
- `src/prompts/har_builder.py`

Your builder must:
- subclass `PromptBuilder` (`src/interfaces/prompts.py`)
- implement:
  - `domain_name` (string)
  - `get_system_prompt()` (base RTEC + your domain text)
  - `get_fewshot_examples()` (list of `FewShotExample`)

#### 3) Register the new domain builder

Edit `src/prompts/factory.py` and register it:

- import your builder class
- call `register_prompt_builder("<domain>", <YourBuilderClass>)`

This enables:

```bash
rtec-llm domains
```

to show your domain, and makes `get_prompt_builder("<domain>")` work.

#### 4) Provide the domain “requests” list (evaluation batch)

The CLI runs a “batch” of fluents for each domain. Each fluent request is a dict with keys like:

- `fluent_name`: string
- `description`: natural language task description
- `prolog`: ground-truth Prolog/RTEC rules (used for simLP similarity scoring)
- `prerequisites` (optional): list of fluent names that should be injected from memory

Create:

- `src/prompts/<domain>_requests.py`

and define:

- `<domain>_requests = [ ... ]`

See:
- `src/prompts/msa_requests.py`
- `src/prompts/har_requests.py`

#### 5) Wire the domain requests into the CLI

Edit `src/cli/main.py` → `get_requests_for_domain(domain: str)` and add an `elif` branch for your domain that imports and returns your requests list.

This is currently required because the CLI uses explicit imports for `msa_requests` and `har_requests`.

#### 6) Add tests for the new builder

Add a new test file:

- `tests/prompts/test_<domain>_builder.py`

and follow the pattern in:
- `tests/prompts/test_msa_builder.py`
- `tests/prompts/test_har_builder.py`

At minimum, verify:
- `domain_name` is correct
- `get_system_prompt()` is non-empty and includes base RTEC predicates
- `get_fewshot_examples()` returns non-empty `FewShotExample`s

---

### Add a new LLM provider (provider class + registration)

Providers are implemented via the abstract `LLMProvider` base class:
- `src/interfaces/llm.py`

At runtime, the CLI constructs:
- `LLMConfig(provider=..., api_key=..., extra={"model": ...})` (see `src/cli/main.py`)
- then calls `get_provider(provider)(llm_config)` (see `src/llm/factory.py`)

#### 1) Implement the provider class

Create a new provider module:

- `src/llm/<your_provider>_client.py`

Implement a class that subclasses `LLMProvider` and implements:

- `_call_provider(self, final_prompt: str) -> str`

Use `src/llm/openai_client.py` as the reference implementation.

What you receive:
- `final_prompt` is a single string containing a structured prompt assembled from:
  - `<system>` (system prompt)
  - `<policy>` (output policy from `src/prompts/rtec_policy.py`)
  - `<domain>` (optional)
  - `<example>` blocks (few-shots)
  - `<user>` (the natural language description)
  - `<feedback>` (optional, from simLP)

Return value:
- a **string** response (the orchestrator will extract ```prolog``` blocks)

#### 2) Register the provider in the provider factory

Edit:
- `src/llm/factory.py`

and add:
- an import for your provider class
- `register_provider("<provider_name>", <YourProviderClass>)`

Then you can run:

```bash
rtec-llm run --domain msa --provider <provider_name> --api-key-name <ENV_VAR_NAME>
```

#### 3) Add env vars

If your provider needs API keys, add them to `.env` and pass the variable name via `--api-key-name`.

Example:

```bash
cat >> .env << 'EOF'
MY_PROVIDER_API_KEY=your_key_here
EOF
```

Then:

```bash
rtec-llm run --domain msa --provider my_provider --api-key-name MY_PROVIDER_API_KEY
```

#### 4) (Optional) Add a mock/test provider

For deterministic/offline tests:
- use `MockLLMProvider` (`src/llm/mock_provider.py`)
- or add your own deterministic provider and register it for local experiments

---

### Troubleshooting

#### Install fails on `simlp @ git+...`

- Ensure `git` is installed and available in your PATH.
- Ensure you have network access during installation.

#### “API key not found”

- Ensure `.env` exists at the repo root and contains the key.
- Or pass the correct env var name via `--api-key-name`.

#### “Unknown domain”

- Ensure your builder is registered in `src/prompts/factory.py`.
- Ensure the CLI request loader (`src/cli/main.py:get_requests_for_domain`) knows about your domain.

#### Visualization errors

- If you’re on a headless machine, avoid `--show-plots` and use `--visualize` only.


