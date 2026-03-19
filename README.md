# AiMO Agents

## Repository layout

```text
AiMO Agents/
├── notebooks/
│   └── langgraph_demo_v2.ipynb
├── src/
│   └── aimo_agents/
│       ├── __init__.py
│       ├── runner.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── graph.py
│       │   ├── orchestrator/
│       │   │   ├── __init__.py
│       │   │   ├── graph.py
│       │   │   ├── nodes.py
│       │   │   └── state.py
│       │   └── teacher/
│       │       ├── __init__.py
│       │       ├── graph.py
│       │       ├── nodes.py
│       │       └── state.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── create_quiz.py
│       │   ├── retrieve_material.py
│       │   └── send_analytics.py
│       └── config/
│           ├── __init__.py
│           └── settings.py
├── tests/
│   ├── test_agent.py
│   ├── test_create_quiz.py
│   └── test_retrieve_material.py
├── .env.example
├── .gitattributes
├── .gitignore
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Setup

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust the model IDs if needed.

Optional: install in editable mode if you want imports to resolve as a package while developing.

```bash
pip install -e .
```

## Usage

Run the CLI:

```bash
python -m aimo_agents.runner
```

Or use the package programmatically:

```python
from aimo_agents import run_once

result = run_once(
	user_input="Create a quiz on photosynthesis",
	learning_material="Photosynthesis converts light energy into chemical energy.",
	topic="photosynthesis",
	question_count=3,
)

print(result.get("quiz"))
```

Note: runtime files are currently scaffolded (`pass`) by design, so this repository is intended as a project template/structure at this stage.

## Tests

```bash
pytest
```
