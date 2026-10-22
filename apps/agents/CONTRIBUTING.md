# Agents Contributor Guide

This guide helps new contributors understand how the agents app works and how to make safe changes quickly.

## What this app does

The agents app generates multiple-choice quizzes with an instruction-tuned chat model, from supplied study material or from the model's own knowledge.

Flow:

1. The website API sends the teacher's uploaded material, or asks for a model-knowledge quiz.
2. The teacher node picks a topic-relevant excerpt and prompts the model for quiz JSON.
3. Validation removes unsupported, duplicate, leaky or position-dependent questions and retries up to 3 times.
4. Quiz is written to a new file in `generated_quizzes/`.

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
```

No `.env` file is needed; the defaults in `settings.py` work as they are. To change a
setting, copy `.env.example` to `.env` and edit it.

## Team GPU/CPU setup

The optional teacher-model pilot uses `Qwen/Qwen3-4B-Instruct-2507` with
`TEACHER_QUANTIZATION=4bit`. This requires a CUDA GPU and the quantization extra:
`pip install -e ".[quantization]"`. The CPU baseline keeps
`TEACHER_QUANTIZATION=none`. Quantization is applied only to the teacher; NPC
loading continues to use `ORCHESTRATOR_MODEL_ID` without quantization.

From `apps/website`, the opt-in container configuration is:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml -f docker-compose.teacher-pilot.yml up --build -d agents
```

The pilot downloads a separate model on first use. Omitting the teacher-pilot
override returns to the baseline model configuration. Evaluate real textbook
questions before treating any model change as a quality improvement.
The pilot selects PyTorch's supported `cudaMallocAsync` allocator to avoid a
large contiguous loading reservation failing on the 8 GB Windows GPU. It does
not patch Transformers or change the baseline CPU configuration.
The pilot disables automatic source reload to avoid overlapping model processes
on a small GPU. Restart the agents container after editing its source.

Put machine-specific overrides in `.env.local` (not committed). The app loads `.env` first
and `.env.local` second, so local values take precedence.

PowerShell example:

```powershell
Copy-Item .env.example .env.local
```

GPU developer example (`.env.local`):

```bash
DEVICE_MAP=cuda:0
TEACHER_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
ORCHESTRATOR_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
```

CPU-only developer example (`.env.local`):

```bash
DEVICE_MAP=cpu
```

## First change (example)

Goal: make the quizzes more varied.

1. In `.env`, set `TEMPERATURE=0.7`.
2. Run:

```bash
python -m aimo_agents.runner --topic colours --questions 5
```

3. Validate output in the newest file in `generated_quizzes/`.

## Common contributor tasks

- Change prompt/quiz format: edit teacher node logic in `src/aimo_agents/agents/teacher/nodes.py`.
- Add pipeline behavior: update teacher graph in `src/aimo_agents/agents/teacher/graph.py`.

## Testing and validation

### Textbook practice used by the minigame

The website API separates student pages from teacher guidance before calling the
agents service. The minigame sends `language_practice=true` and
`require_full_count=true` along with the selected unit's `learning_material` and
separate `teaching_guidance`.

Language practice uses complete student examples and source-grounded grammar
scaffolds to keep the small model's task bounded. A source quotation must occur in
the student material. For a fill-in-the-blank question, completing the sentence
establishes the answer independently of the model's answer letter. A separate
model review solves the exercise without seeing the proposed answer, checking
that there is one correct option and the exercise works by itself. This review
is a quality check, not a guarantee of semantic correctness. Source cleanup
excludes exercise fragments and a limited set of adult terms; the adult course
still needs content review before classroom use.
Repeated correct words are allowed across different exercises.

The minigame gets either the requested question count or an error; partial quizzes
are not saved or started. `tests/test_language_practice.py` covers these contracts.
Raw model output is available through the teacher module's DEBUG logging for
development diagnosis; keep that logging disabled when handling private materials.

From `apps/agents`:

```bash
pytest
```

Recommended after each change:

1. Run `pytest`.
2. Run one CLI generation.
3. Open the newest file in `generated_quizzes/` and confirm format and answer quality.

## FOSS requirement

This project is intentionally FOSS-first. Use open-source models and libraries only.

## Troubleshooting

- Slow first run: the model download (about 3 GB) can take time.
- Slow generation: a "CUDA is not available" warning means PyTorch is a CPU build; install a CUDA build.
- Low quiz quality: try a larger chat model in `TEACHER_MODEL_ID`, or improve the study material.
