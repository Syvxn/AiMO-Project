# AiMO-Project

Monorepo containing independent applications:

- apps/game: Godot game project
- apps/agents: AI agents backend/tools
- apps/website: Next.js + FastAPI website stack

Each app remains independently developed, with its own dependencies, tooling, and runtime.

## First-Time Setup

Clone the repository:

```bash
git clone https://github.com/Syvxn/AiMO-Project.git
cd AiMO-Project
```

## Prerequisites

- Docker Desktop (for website stack)
- Python 3.11+ (for agents)
- Godot 4.6 (for game)

## Run Apps Independently

You do not need to run every app at the same time. Each app can be developed and run on its own.

## Website App (`apps/website`)

This runs Next.js + FastAPI + PostgreSQL + Nginx via Docker Compose.

1. Open a terminal in the website app:

```bash
cd apps/website
```

2. Create environment file:

```bash
cp .env.example .env
```

PowerShell alternative:

```powershell
Copy-Item .env.example .env
```

3. Start services:

```bash
docker compose up --build
```

4. Open in browser:

- Website: http://localhost
- API via Nginx: http://localhost/api
- API health: http://localhost/api/health

To stop:

```bash
docker compose down
```

## Agents App (`apps/agents`)

1. Open a terminal in agents app:

```bash
cd apps/agents
```

2. Create and activate virtual environment:

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. Create environment file:

```bash
cp .env.example .env
```

PowerShell alternative:

```powershell
Copy-Item .env.example .env
```

5. Run a sample quiz generation:

```bash
python -m aimo_agents.runner --topic colours --questions 5
```

Run tests:

```bash
pytest
```

## Game App (`apps/game`)

1. Open a terminal in game app:

```bash
cd apps/game
```

2. Create env config file:

```bash
cp .env_example.json .env.json
```

PowerShell alternative:

```powershell
Copy-Item .env_example.json .env.json
```

3. Open Godot 4.6.
4. Click Import and select `apps/game/project.godot`.
5. Run from editor (F5) or export builds as needed.

## Recommended Workflow

- Keep dependencies and tools isolated per app.
- Commit changes within the relevant app directory.
- Use app-specific READMEs for deeper setup and architecture notes:
	- `apps/website/README.md`
	- `apps/agents/README.md`
	- `apps/game/README.md`
