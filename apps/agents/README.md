# AiMO Agents

A multi-agent system that generates multiple-choice quizzes with an open-source instruction-tuned HuggingFace model, running on the GPU when CUDA is available. Quizzes are based on supplied study material (the website's teacher uploads), or on the model's own knowledge when none applies.

> New contributors should start with [CONTRIBUTING.md](CONTRIBUTING.md).
> For mixed hardware teams, see [Team GPU/CPU setup](CONTRIBUTING.md#team-gpucpu-setup).

> **For a hands-on walkthrough see [`notebooks/contributor_guide.ipynb`](notebooks/contributor_guide.ipynb).**

---

## How it works

```
Quiz request (topic, count, optional learning material)
      │
      ▼
 Material excerpt      ← up to ~1200 words, favouring text that matches the topic
      │                  (no material + use_model_knowledge=false → error)
      ▼
 Teacher LLM           ← Qwen2.5-1.5B-Instruct (any HF chat model), JSON output
      │                  grounded in the material, or its own knowledge if allowed
      ▼
 Validation            ← answer supported by the source, no duplicates or leaks,
      │                  answer shuffling, up to 3 generation attempts
      ▼
 generated_quizzes/     ← saved to project root (one file per quiz)
```

The NPC chat uses the same model instance, so one copy sits in GPU memory. The `rag/` package and
`retrieve_material` tool still exist for experiments but the quiz pipeline no longer uses them.

---

## Repository layout

```text
AiMO-Agents/
├── data/
│   └── materials/
│       ├── english_grade5.txt          ← full study material (source)
│       └── chapters/                   ← auto-split per-chapter files (used by RAG)
│           ├── ch01_greetings_and_introductions.txt
│           └── ...
├── notebooks/
│   ├── contributor_guide.ipynb         ← NEW: step-by-step contributor guide
│   └── langgraph_demo_v2.ipynb
├── src/
│   └── aimo_agents/
│       ├── __init__.py
│       ├── runner.py                   ← CLI + programmatic entry points
│       ├── agents/
│       │   ├── graph.py                ← parent graph wiring
│       │   ├── orchestrator/           ← routing agent (scaffold)
│       │   └── teacher/
│       │       ├── graph.py            ← generate → END
│       │       ├── nodes.py            ← prompt + LLM call + validation
│       │       └── state.py
│       ├── rag/
│       │   ├── chunker.py              ← word-overlap text splitter
│       │   ├── embedder.py             ← sentence-transformers wrapper
│       │   └── retriever.py            ← TxtRetriever with score threshold filter
│       ├── tools/
│       │   ├── create_quiz.py          ← saves quiz to generated_quizzes/
│       │   ├── retrieve_material.py    ← LangChain tool wrapping TxtRetriever
│       │   └── send_analytics.py       ← analytics stub
│       └── config/
│           └── settings.py             ← all settings, loaded from .env
├── tests/
│   ├── test_agent.py
│   ├── test_create_quiz.py
│   └── test_retrieve_material.py       ← RAG unit tests (12 tests)
├── .env.example
├── pyproject.toml
└── requirements.txt
```

---

## Setup

### Prerequisites

- Python 3.11+
- ~4 GB disk space for the default model (`Qwen2.5-1.5B-Instruct`)

### Steps

```bash
# 1. Create and activate a virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Linux / macOS

# 2. Install the project and all dependencies
pip install -e .

# 3. Run it. No .env is needed: the defaults in settings.py work as they are.
# To change a setting, copy .env.example to .env (or to .env.local for machine-specific values).
```

The loader reads `.env` first, then `.env.local` (if present); local values win.

### `.env` settings (all optional)

| Variable | Default | Description |
|---|---|---|
| `TEACHER_MODEL_ID` | `Qwen/Qwen2.5-1.5B-Instruct` | Chat model that writes quizzes |
| `ORCHESTRATOR_MODEL_ID` | `Qwen/Qwen2.5-1.5B-Instruct` | Chat model for NPC conversations |
| `DEVICE_MAP` | `auto` | `auto` uses the GPU when available; `cpu` forces the CPU |
| `TEMPERATURE` | `0.2` | `0` is deterministic; higher is more varied |
| `DEFAULT_QUESTION_COUNT` | `5` | Questions per quiz |

### Team GPU/CPU workflow

- Put machine-specific overrides in `.env.local` (gitignored); leave `.env` for values shared by everyone.
- Example for a developer who wants to force GPU:

```bash
DEVICE_MAP=cuda:0
TEACHER_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
ORCHESTRATOR_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
```

- Example for a CPU-only developer:

```bash
DEVICE_MAP=cpu
```

---

## Usage

### CLI

```bash
python -m aimo_agents.runner --topic colours --questions 5            # model's own knowledge
python -m aimo_agents.runner --topic plants --material lesson.pdf     # based on a file
```

### Programmatic

```python
from aimo_agents import run_once

result = run_once("", topic="colours", question_count=5, use_model_knowledge=True)
print(result.get("quiz"))   # the quiz dict; a copy is saved under generated_quizzes/
```

Pass `learning_material="..."` to base the quiz on text instead. Without it, `use_model_knowledge=True` is required.

The quiz is saved as a new file in `generated_quizzes/` in the project root.

### Study material

The agents service does not keep its own material. The website API sends the teacher's uploaded text
with each quiz request, and students without a class get quizzes from the model's own knowledge.

---

## Tests

```bash
pytest
```

The test suite covers the RAG chunker, embedder, and retriever (12 tests). Run after any changes to `src/aimo_agents/rag/`.

---

## Architecture decisions

- **No vector database** — the index is built in memory from scratch on each run using numpy dot products. Fast enough for small-to-medium corpora (< 10 000 chunks).
- **FOSS only** — all models and libraries are open-source (Apache-2.0 / MIT). No OpenAI API key required.
- **Score threshold filtering** — chunks below cosine similarity 0.30 are discarded before reaching the LLM, preventing topic drift.
- **Post-processing quality layer** — generated questions are filtered for structural validity, exact/option-set duplicates, answer leakage between questions, and content overlap (Jaccard ≥ 0.40).
