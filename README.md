# Feedback Loop: Iterative Generation, Evaluation & Refinement of Logic-Based Rule Systems

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)



A modular framework for LLM-driven generation, evaluation, and refinement of logic-based rule systems.  
It implements an automated feedback loop that analyzes generated rules, compares them to reference definitions, and produces structured feedback for iterative improvement.

### 📚 Supporting MSc Thesis

> **Applications of Large Language Models in Event Calculus – A comprehensive study on the RTEC framework**  
> *Georgios Panagopoulos, 2025*

## ✨ Features

- Multi-provider LLM interface 
- Automated feedback loop for iterative refinement
- Pluggable parser for logic-based languages (Prolog-style by default)

- Detailed rule-level feedback generation
- Experiment orchestration and logging
- Clean modular architecture

## 🧩 Architecture Overview (without memory)

```mermaid
graph LR
    A[Task Description] --> B[Prompt Builder]
    B --> C[LLM Generator]
    C --> D[Rule Parser]
    D --> E[Similarity Engine]
    E --> F{Converged?}
    F -->|No| G[Feedback Engine]
    G --> B
    F -->|Yes| H[Final Rule Set]
```
## 🧩 Architecture Overview (added memory)
Regarding the architecture you can refer to [Architecture](ARCHITECTURE.md)
## 🚀 Quick Start

### Installation

If you do not already have uv package manager, i suggest you install it!
uv is a modern, ultra-fast Python package manager by Astral

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# Clone the repository
git clone https://github.com/PanagopoulosGeorge/thesis-ds.git
cd thesis-ds

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (includes simLP automatically)
pip install -e .  # Basic installation
```

**Note**: The framework automatically installs [simLP](https://github.com/PanagopoulosGeorge/simLP) for RTEC parsing, similarity computation, and automated feedback generation.