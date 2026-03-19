# AiMO Agents Codebase Overview

This document describes every file currently present in this repository.

## Root Files

### `.env.example`
Purpose:
- Example environment variables for local setup.

Why it matters:
- Provides a safe template for model IDs and runtime settings without committing secrets.

### `.gitignore`
Purpose:
- Defines files/folders Git should not track.

Why it matters:
- Keeps environment files, caches, and generated artifacts out of version control.

### `pyproject.toml`
Purpose:
- Python project metadata and packaging configuration.

What it contains:
- Build-system config, dependencies, optional dev dependencies, and CLI script mapping.

Why it matters:
- This is the canonical project config file for install/build/run behavior.

## Documentation

### `docs/codebase-overview.md`
Purpose:
- Human-readable map of the repository for contributors.

Why it matters:
- Reduces onboarding time and clarifies where responsibilities live.

## Source Layout

`src/` is the source root for importable Python packages (the standard src layout).

## Active Package: `src/aimo_agents/`

### `src/aimo_agents/__init__.py`
Purpose:
- Package entry surface and re-export point.

Why it matters:
- Lets callers import key APIs directly from `aimo_agents`.

## App Layer

### `src/aimo_agents/app/__init__.py`
Purpose:
- Re-exports runtime entry points from the app layer.

### `src/aimo_agents/app/runner.py`
Purpose:
- Defines `run_once()` and `run_cli()` used by programmatic and CLI execution.

Why it matters:
- Keeps application startup concerns separate from core orchestration logic.

## Config Layer

### `src/aimo_agents/config/__init__.py`
Purpose:
- Re-exports the settings schema and loader.

### `src/aimo_agents/config/settings.py`
Purpose:
- Defines the `Settings` dataclass and loads environment-driven configuration.

Why it matters:
- Centralizes runtime configuration and keeps defaults consistent across modules.

## Core Layer

### `src/aimo_agents/core/__init__.py`
Purpose:
- Re-exports core orchestration contracts (`AgentState`, `build_graph`).

### `src/aimo_agents/core/state.py`
Purpose:
- Shared LangGraph state schema (`AgentState`) and route literals.

Why it matters:
- Defines the cross-node data contract for the whole workflow.

### `src/aimo_agents/core/graph.py`
Purpose:
- Assembles and compiles the LangGraph node/edge topology.

Why it matters:
- Single source of truth for control flow.

## Infrastructure Layer

### `src/aimo_agents/infrastructure/__init__.py`
Purpose:
- Re-exports infrastructure adapters.

### `src/aimo_agents/infrastructure/llm.py`
Purpose:
- Builds the Hugging Face text-generation pipeline wrapper.

Why it matters:
- Isolates model provider setup from app and graph logic.

### `src/aimo_agents/agents/__init__.py`
Purpose:
- Package marker for the agents namespace.

Why it matters:
- Enables clean subpackage imports under `aimo_agents.agents`.

## Orchestrator Agent Package

### `src/aimo_agents/agents/orchestrator/__init__.py`
Purpose:
- Package marker and short package-level description.

### `src/aimo_agents/agents/orchestrator/agent.py`
Purpose:
- Implements `orchestrator_node`, which validates input and decides routing.

Why it matters:
- Controls which agent handles each user request.

### `src/aimo_agents/agents/orchestrator/prompts.py`
Purpose:
- Stores the orchestrator routing prompt template.

Why it matters:
- Keeps prompt text separate from execution code.

## Teacher Agent Package

### `src/aimo_agents/agents/teacher/__init__.py`
Purpose:
- Package marker and short package-level description.

### `src/aimo_agents/agents/teacher/agent.py`
Purpose:
- Defines the teacher ReAct node functions (LLM call, tool step, continue condition).

Current status:
- Function bodies are still scaffold placeholders.

### `src/aimo_agents/agents/teacher/prompts.py`
Purpose:
- Stores the teacher prompt template for quiz generation.

Why it matters:
- Keeps output-format instructions centralized and editable.

### `src/aimo_agents/agents/teacher/tools.py`
Purpose:
- Declares teacher tools and tool lookup mapping.

Current status:
- Tool implementations are still scaffold placeholders.

