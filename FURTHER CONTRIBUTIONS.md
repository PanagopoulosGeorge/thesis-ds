## FURTHER CONTRIBUTIONS

This document is a **thesis-facing companion** to the repository. It summarizes **what is implemented**, shows **how to run the project**, and provides a **ready-to-present demo script**. It ends with **high-value follow-up experiments** chosen to require **minimal new development**.

---

### What you have implemented so far (repo contributions)

This repository implements a full **LLM → evaluate → feedback → refine** workflow for generating **RTEC / Prolog-style event descriptions**.

- **Iterative orchestration (the “feedback loop”)**
  - Controller: `src/core/orchestrator.py`
  - Config + result tracking models: `src/core/models.py`
  - Behavior: generate initial rules → evaluate with simLP → inject feedback → iterate until convergence / max iterations.

- **Automatic evaluation + feedback generation (simLP integration)**
  - Client wrapper: `src/feedback/client.py`
  - Core call: `simlp.run.parse_and_compute_distance(...)` producing similarity + structured feedback.

- **Memory for hierarchical prompting**
  - Module: `src/memory/rule_memory.py`
  - Purpose: store validated fluent rules (above a threshold) so later composite fluents can reuse prerequisites.

- **Prompting system (base RTEC + domain knowledge + few-shot examples)**
  - Prompt builder interface: `src/interfaces/prompts.py`
  - MSA: `src/prompts/msa_builder.py` with MSA domain text + examples in `src/prompts/msa_domain.py`, `src/prompts/msa_examples.py`
  - HAR: `src/prompts/har_builder.py` with HAR domain text + examples in `src/prompts/har_domain.py`, `src/prompts/har_examples.py`
  - Requests / evaluation pairs (NL request + ground-truth RTEC): `src/prompts/msa_requests.py`, `src/prompts/har_requests.py`
  - Prompt registry: `src/prompts/factory.py`

- **LLM provider abstraction (pluggable backends)**
  - Provider base: `src/interfaces/llm.py`
  - Provider registry: `src/llm/factory.py`
  - Providers:
    - OpenAI: `src/llm/openai_client.py`
    - Ollama (local): `src/llm/ollama_client.py`
    - Mock provider (for offline demos/tests): `src/llm/mock_provider.py`

- **Rule extraction from LLM outputs**
  - Extracts ```prolog``` blocks from natural-language responses: `src/utils/code_extractor.py`

- **CLI for end-to-end runs + plotting**
  - Main CLI entrypoint (`rtec-llm`): `src/cli/main.py`
  - Visualization + JSON export: `src/cli/visualize.py`
  - Output artifacts:
    - `results.json` (machine-readable run summary)
    - plots as PNG (presentation mode) or PDF (LaTeX-friendly mode)

- **Thesis-facing utilities**
  - Generate TikZ/PGFPlots LaTeX bar-chart code from `results.json`: `src/utils/results2latex.py`

- **Examples**
  - Online run (OpenAI): `examples/run_orchestrator.py`
  - Offline run (mock provider): `examples/test_orchestrator_mock.py`

- **Tests**
  - Prompt builder tests: `tests/prompts/`
  - Utility tests: `tests/utils/`

For the architectural narrative, also see:
- `docs/ARCHITECTURE.md`
- `docs/fluent-hierarchy.md`
- `docs/setup.md`

---

### How to run the repository (practical quickstart)

#### Requirements
- **Python**: 3.9+
- **Network**: required for install because `simlp` is installed from a Git URL (see `pyproject.toml`)

#### Install (choose one)

- **Option A: venv + pip**

```bash
cd /Users/gphome/Desktop/projects/thesis-ds/thesis-ds-repo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

- **Option B: uv (recommended if you already use it)**

```bash
cd /Users/gphome/Desktop/projects/thesis-ds/thesis-ds-repo
uv venv
source .venv/bin/activate
uv sync --all-extras
```

#### Configure environment variables

Create `.env` in the repo root (the CLI loads it via `dotenv`):

```bash
cd /Users/gphome/Desktop/projects/thesis-ds/thesis-ds-repo
cat > .env << 'EOF'
OPENAI_API_KEY=your_key_here
EOF
```

#### Run the CLI

- List domains:

```bash
rtec-llm domains
```

- Run MSA:

```bash
rtec-llm run --domain msa
```

- Run HAR with explicit iteration control:

```bash
rtec-llm run --domain har --provider openai --model gpt-4o --max-iterations 3 --convergence-threshold 0.95
```

- Save outputs and generate plots (PDF in LaTeX style):

```bash
rtec-llm run --domain msa --output ./results/demo_msa --visualize --latex
```

This creates:
- `./results/demo_msa/results.json`
- `./results/demo_msa/iteration_progress.pdf`
- `./results/demo_msa/summary_scores.pdf`
- `./results/demo_msa/improvement.pdf`

#### Run examples (without the CLI)

- **Offline (no API calls)**

```bash
python examples/test_orchestrator_mock.py
```

- **Online (OpenAI API)**

```bash
python examples/run_orchestrator.py
```

#### Run tests

```bash
pytest
```

---

### Demo section (what to present live)

This is designed as a **10–15 minute demo** that shows:
1) the system works offline (deterministic), 2) the real LLM loop runs, 3) the run produces thesis-ready artifacts.

#### Demo narrative (what you say)
- **Problem**: RTEC rules are precise and hierarchical; LLMs can generate syntax but often miss temporal/logical constraints.
- **Solution**: a **closed-loop system**: generate → evaluate (simLP) → feedback → regenerate; plus **memory** for prerequisite fluents.
- **Evidence**: similarity improvements across iterations + saved plots/JSON for reproducibility.

#### Demo steps (copy/paste)

##### Step 0: sanity / setup

```bash
cd /Users/gphome/Desktop/projects/thesis-ds/thesis-ds-repo
source .venv/bin/activate
rtec-llm version
rtec-llm domains
```

##### Step 1: offline proof (no API calls, shows the loop + feedback injection)

```bash
python examples/test_orchestrator_mock.py
```

What to highlight:
- It runs without network.
- It generates simLP feedback (written to `logs/`), and subsequent prompts include `<feedback>...</feedback>`.

##### Step 2: online run (OpenAI) + export artifacts

```bash
rtec-llm run --domain msa --provider openai --model gpt-4o --max-iterations 3 --convergence-threshold 0.95 --output ./results/demo_msa --visualize --latex
```

What to highlight:
- The table shows per-fluent convergence + best score.
- Plots are automatically produced for your thesis/presentation.

##### Step 3: generate LaTeX TikZ figure code from the produced `results.json`

```bash
python src/utils/results2latex.py ./results/demo_msa/results.json --output ./results/demo_msa/iteration_scores.tex --label fig:iteration_scores_MSA
```

What to highlight:
- This directly supports Chapter 5 figures (PGFPlots/TikZ).

#### Optional: demo with a local model (Ollama)

If you want a “no cloud” demo path:
- Ensure Ollama is installed and running (`ollama serve`) and you have pulled a model.
- Install Ollama python package if needed: `pip install ollama`

Then:

```bash
rtec-llm run --domain msa --provider ollama --model llama3.2 --max-iterations 2 --convergence-threshold 0.9 --output ./results/demo_msa_ollama --visualize
```

---

### Further contributions (max thesis value with minimal development)

Below is a prioritized list of **experiments + deliverables**. The top items require **no code changes** (only running commands + analyzing `results.json`), then “tiny code changes” (small CLI flags / wiring), then bigger work.

---

### High-value experiments you can run today (no code changes)

#### 1) Baseline vs feedback-loop (your “iteration benefit” claim)
Goal: quantify how much the feedback loop improves quality.

- **Run baseline (no refinement)**:

```bash
rtec-llm run -d msa -i 1 -t 0.95 -o ./results/msa_i1 --visualize --latex
```

- **Run with feedback loop**:

```bash
rtec-llm run -d msa -i 3 -t 0.95 -o ./results/msa_i3 --visualize --latex
```

Do the same for HAR:

```bash
rtec-llm run -d har -i 1 -t 0.95 -o ./results/har_i1 --visualize --latex
rtec-llm run -d har -i 3 -t 0.95 -o ./results/har_i3 --visualize --latex
```

What you report in Chapter 5:
- average best score by domain (and per fluent)
- number of converged fluents by domain
- improvement distribution (how many got better / same / worse)

#### 2) “Regression exists” analysis (supports your HAR Fighting observation)
Goal: show iteration is not strictly monotonic and motivate early stopping / best-iteration selection.

You already export both **best score** and **final score** per fluent in `results.json`:
- `best_score` vs `final_score` indicates whether later iterations regressed.

Deliverable:
- A small table: `%fluents where best_iteration != last_iteration`, plus examples (e.g., Fighting).

#### 3) Model comparison (cheap vs strong model)
Goal: show cost/quality tradeoffs without building anything new.

```bash
rtec-llm run -d msa -m gpt-4o -i 3 -t 0.95 -o ./results/msa_gpt4o --visualize --latex
rtec-llm run -d msa -m gpt-4o-mini -i 3 -t 0.95 -o ./results/msa_gpt4omini --visualize --latex
```

Report:
- avg score, converged count, and note qualitative differences (missing predicates / interval ops).

---

### Minimal development, maximum payoff (small changes, big evaluation uplift)

These are intentionally scoped to “small edits” (typically 1–2 files).

#### A) Expose **early stopping** in the CLI
Why: directly addresses “Iteration 3 can regress” and improves runtime.

- Current support exists in `OrchestratorConfig` (`early_stopping`, `early_stopping_patience`) in `src/core/models.py`.
- Minimal change: add CLI flags in `src/cli/main.py` and pass them into `OrchestratorConfig`.

Experiment enabled:
- run with and without early stopping, compare: average iterations, best score, and regression rate.

#### B) Expose **temperature / max tokens** in the CLI (and wire them into OpenAI calls)
Why: unlocks robustness + sampling experiments (and reproducibility narratives).

- `LLMConfig` already has `temperature`/`max_tokens` in `src/interfaces/models.py`.
- Ollama already reads `config.temperature`/`config.max_tokens`.
- OpenAI currently uses only `config.extra`.

Minimal change:
- add CLI flags, set `LLMConfig(temperature=..., max_tokens=...)`
- in `src/llm/openai_client.py`, pass `temperature`/`max_tokens` to `chat.completions.create(...)`

Experiments enabled:
- temperature sweep (0.0 / 0.2 / 0.7)
- stability across runs (variance of outcomes)

#### C) Add “**best-of-N**” sampling with evaluator selection (small, very publishable)
Why: big score gains with little conceptual complexity; aligns with your “automated evaluator” story.

Minimal implementation idea:
- for each iteration, sample N candidate generations (e.g., N=3)
- evaluate each with simLP
- keep the best and feed back from the best (or from the worst, as a control)

Deliverable:
- a plot: quality vs N and cost vs N (even N=1 vs N=3 is enough).

---

### Experiments that add thesis value but may require more work

Only do these if you have time/data; they’re strong but not “minimal”.

#### 1) Functional evaluation on data streams (precision/recall)
Goal: evaluate whether generated rules “behave” like ground truth on actual streams.

Requirement:
- access to event streams + annotation labels (or ability to run RTEC end-to-end in your environment)

#### 2) Prompt ablations (base vs domain examples vs memory)
Goal: empirically show which prompt component drives improvements.

Minimal-ish if you add flags:
- disable few-shot examples
- disable memory injection
- compare deltas on the same fluent set

#### 3) Robustness to paraphrases / ambiguity
Goal: show sensitivity of the formalization to the user’s wording.

Implementation:
- add a few paraphrased variants per fluent in `*_requests.py`
- run and report variance

---

### Suggested “next best” set (lowest effort, best thesis payoff)

If you want the best ROI path, do these in order:
- **Run baseline vs loop** for both domains (already possible).
- **Compute regression rate** using `best_score` vs `final_score` from `results.json` (already possible).
- **Compare gpt-4o vs gpt-4o-mini** (already possible).
- Then implement **early stopping CLI flag** (tiny change) and rerun to show fewer iterations + fewer regressions.

