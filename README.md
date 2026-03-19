# AiMO Agents

AiMO Agents is a LangGraph-based teaching assistant project organized around three core areas:

- `src/aimo_agents/agents/`: one folder per agent, plus shared graph and state.
- `src/aimo_agents/tools/`: one file per tool.
- `src/aimo_agents/config/`: runtime settings loaded from the environment.

## Repository layout

```text
AiMO Agents/
|-- notebooks/                      # Demos and experiments
|   `-- demo.ipynb
|-- src/
|   `-- aimo_agents/                # Main Python package
|       |-- agents/                 # One folder per agent
|       |   |-- __init__.py
|       |   |-- graph.py            # Parent StateGraph wiring subgraphs together
|       |   |-- orchestrator/       # Orchestrator agent scaffold
|       |   |   |-- __init__.py
|       |   |   |-- graph.py
|       |   |   |-- nodes.py
|       |   |   `-- state.py
|       |   `-- teacher/            # Teacher agent scaffold
|       |       |-- __init__.py
|       |       |-- graph.py
|       |       |-- nodes.py
|       |       `-- state.py
|       |-- config/                 # Centralized runtime settings
|       |   |-- __init__.py
|       |   `-- settings.py         # Model names, temperature, and defaults
|       |-- tools/                  # One file per shared tool
|       |   |-- __init__.py         # Exposes all tools and the tool registry
|       |   |-- create_quiz.py
|       |   |-- retrieve_material.py
|       |   `-- send_analytics.py
|       |-- __init__.py
|       `-- runner.py               # CLI and programmatic entrypoints
|-- tests/                          # One test file per tool or component
|   |-- test_agent.py
|   |-- test_create_quiz.py
|   `-- test_retrieve_material.py
|-- .env.example
|-- .gitignore
|-- pyproject.toml
`-- requirements.txt                # Pinned dependencies
```

## Setup

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and adjust the model IDs if needed.

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

## Tests

```bash
pytest
```
