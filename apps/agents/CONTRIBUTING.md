# Agents Contributor Guide

This guide helps new contributors understand how the agents app works and how to make safe changes quickly.

## What this app does

The agents app generates multiple-choice quizzes from text material using a lightweight RAG pipeline.

Flow:

1. Retriever loads `.txt` materials and finds relevant chunks.
2. Teacher model generates quiz JSON from the retrieved context.
3. Post-processing removes weak/duplicate/leaky outputs.
4. Quiz is written to `study_quiz.json`.

## Project map

- `src/aimo_agents/runner.py`: CLI and entry points
- `src/aimo_agents/agents/teacher`: teacher graph, nodes, state
- `src/aimo_agents/rag`: chunking, embeddings, retrieval
- `src/aimo_agents/tools`: wrappers/utilities used by the graph
- `src/aimo_agents/config/settings.py`: `.env`-driven settings
- `data/materials/chapters`: source text files for retrieval
- `tests`: unit tests and integration-style tests

## Local setup

From `apps/agents`:

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -e .
cp .env.example .env
```

PowerShell copy command:

```powershell
Copy-Item .env.example .env
```

## First change (example)

Goal: adjust number of retrieved chunks.

1. Open `.env` and change `RAG_TOP_K`.
2. Run:

```bash
python -m aimo_agents.runner --topic colours --questions 5
```

3. Validate output in `study_quiz.json`.

## Common contributor tasks

- Tune retrieval quality: edit `src/aimo_agents/rag/retriever.py` and related settings.
- Change prompt/quiz format: edit teacher node logic in `src/aimo_agents/agents/teacher/nodes.py`.
- Add pipeline behavior: update teacher graph in `src/aimo_agents/agents/teacher/graph.py`.
- Add new material: place focused `.txt` files in `data/materials/chapters`.

## Testing and validation

From `apps/agents`:

```bash
pytest
```

Recommended after each change:

1. Run `pytest`.
2. Run one CLI generation.
3. Open `study_quiz.json` and confirm format and answer quality.

## FOSS requirement

This project is intentionally FOSS-first. Use open-source models and libraries only.

## Troubleshooting

- Slow first run: initial model and embedding downloads can take time.
- Empty retrieval results: check `MATERIAL_DIR` and verify `.txt` files exist.
- Low quiz quality: tune `RAG_SCORE_THRESHOLD`, `RAG_TOP_K`, and chapter content focus.
