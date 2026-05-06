# AiMO Agents

A multi-agent system that generates multiple-choice quizzes from plain-text study material using a lightweight RAG (Retrieval-Augmented Generation) pipeline and open-source HuggingFace models.

> **For a hands-on walkthrough see [`notebooks/contributor_guide.ipynb`](notebooks/contributor_guide.ipynb).**

---

## How it works

```
User query (topic)
      │
      ▼
 TxtRetriever          ← indexes .txt files in data/materials/chapters/
 (sentence-transformers/all-MiniLM-L6-v2)
      │  top-k chunks filtered by cosine score threshold
      ▼
 Teacher LLM           ← Qwen2.5-1.5B-Instruct (or any HF text-generation model)
      │  structured JSON prompt with few-shot examples
      ▼
 Post-processing       ← deduplication, leakage detection, answer shuffling
      │
      ▼
 study_quiz.json       ← saved to project root
```

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
│       │       ├── graph.py            ← retrieve → generate → END
│       │       ├── nodes.py            ← RAG retrieval + LLM call + post-processing
│       │       └── state.py
│       ├── rag/
│       │   ├── chunker.py              ← word-overlap text splitter
│       │   ├── embedder.py             ← sentence-transformers wrapper
│       │   └── retriever.py            ← TxtRetriever with score threshold filter
│       ├── tools/
│       │   ├── create_quiz.py          ← saves quiz to study_quiz.json
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

# 3. Configure environment
cp .env.example .env
# Edit .env – at minimum set MATERIAL_DIR if your materials are not in data/materials/chapters/
```

### Key `.env` settings

| Variable | Default | Description |
|---|---|---|
| `TEACHER_MODEL_ID` | `Qwen/Qwen2.5-1.5B-Instruct` | HuggingFace model for quiz generation |
| `MATERIAL_DIR` | `data/materials/chapters` | Directory of `.txt` study files |
| `RAG_MODEL_ID` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `RAG_TOP_K` | `5` | Max chunks retrieved per query |
| `RAG_SCORE_THRESHOLD` | `0.30` | Min cosine similarity to accept a chunk |
| `RAG_CHUNK_SIZE` | `200` | Words per chunk |
| `DEFAULT_QUESTION_COUNT` | `5` | Questions per quiz |

---

## Usage

### CLI

```bash
python -m aimo_agents.runner --topic colours --questions 5
# or
quiz-run --topic "present simple tense"
```

### Programmatic

```python
from aimo_agents import run_once

result = run_once("", topic="colours", question_count=5)
print(result.get("quiz"))   # path to saved study_quiz.json
```

The quiz is saved to `study_quiz.json` in the project root.

### Adding your own study material

1. Place `.txt` files in `data/materials/chapters/`.
2. Each file should cover a single topic — the RAG score threshold filter works best when files are focused.
3. No indexing step needed; the retriever builds the index in memory on first call.

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
