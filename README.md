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

Build the project and start services with docker compose:

```bash
cd apps/website
cp .env.example .env
docker compose up --build
```

Stop services:

```bash
docker compose down
```

## New Contributor Entry Points

Start with these docs first:

- Website contributor guide: `apps/website/CONTRIBUTING.md`
- Agents contributor guide: `apps/agents/CONTRIBUTING.md`
- Game component overview: `apps/game/README.md`

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

## Godot Exporting (Web + Dedicated Server)

Use this when you need browser builds, standalone builds, or server binaries.

### 1. Install export templates (required)

In Godot 4.6:

1. Open `Editor` -> `Manage Export Templates...`.
2. If templates are missing, click `Download and Install`.
3. If auto-download fails, download templates manually from the official Godot release page and use `Install from File`.
4. Confirm templates show as installed for your exact Godot version.

### 2. Open export presets

1. Open the game project at `apps/game/project.godot`.
2. Go to `Project` -> `Export...`.
3. Confirm presets from `apps/game/export_presets.cfg` are available.

### 3. Export web client build

1. Select the `Web` preset.
2. Choose an export path (default currently points to `apps/game/exports/web_client/index.html`).
3. Export and verify files include `index.html` plus associated `.js`, `.wasm`, and `.pck` files.

If you want the website app to launch the build from `/play`, copy the exported web files to:

- `apps/website/apps/web/public/game/`

Then verify:

- `http://localhost/game/index.html` loads
- `http://localhost/play` can launch the game

### 4. Export dedicated server build

1. Select the `Windows Desktop` preset (configured as dedicated server in current presets).
2. Export binary to your preferred server output folder.
3. Run that server process separately from the website stack.

### 5. Runtime notes

- Web builds must be served through HTTP(S), not opened directly as local files.
- If using the website stack, keep websocket routing aligned with `apps/website/infra/nginx/default.conf`.
- If changing server ports, update both game env config and Nginx route config.

## Recommended Workflow

- Keep dependencies and tools isolated per app.
- Commit changes within the relevant app directory.
- Use app-specific READMEs for deeper setup and architecture notes:
	- `apps/website/README.md`
	- `apps/website/CONTRIBUTING.md`
	- `apps/agents/README.md`
	- `apps/agents/CONTRIBUTING.md`
	- `apps/game/README.md`
