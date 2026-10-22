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
```

On a host with NVIDIA GPU support in Docker Desktop, start the stack with the GPU override:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

On a CPU only machine, start the stack with the following command:

```bash
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

### Teacher-approved textbook practice

The teacher panel has a Minigame Question Bank. Select an uploaded textbook unit,
prepare AI drafts or add questions manually, then review the question, four choices,
correct answer and student source quotation. Save at least three questions as
approved to make that unit playable. Saving an approved question as a draft
withdraws it from future games. Drafts are never served to enrolled students.
The unit's JSON can be downloaded for external LLM review and pasted back into
the bank editor. Keep IDs to update existing questions. Save JSON edits keeps new
and changed questions as drafts; Save JSON and approve all approves the submitted
batch explicitly. The unit's Approve all button approves all saved questions.

The API applies migration `005` on startup. Existing uploads are preserved. Game
requests read approved exercises from the database without calling an AI model.
AI assistance is optional; teachers can create and approve questions without it.

### Optional AI drafting pilot (NVIDIA GPU)

The opt-in teacher pilot uses `Qwen/Qwen3-4B-Instruct-2507` with 4-bit loading for
teacher-facing drafts. Its output still needs human review; the pilot did not
reliably reject incorrect vocabulary answers. NPC conversations retain their baseline model. From
`apps/website`, start the teacher service with:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml -f docker-compose.teacher-pilot.yml up --build -d agents
```

The first use downloads several GB of model weights into the shared model cache.
The other website services and the dedicated game server must also be running as
described below. The CPU baseline configuration remains available without this
override.

The Think English teacher edition is parsed into six student units with separate
teacher guidance. Existing uploads do not need to be uploaded again. Reopen the
minigame's chapter picker after updating the parser to refresh the unit IDs.

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
2. The current preset exports to `apps/website/apps/web/public/game/index.html`, which is the asset path used by `/play`.
3. Re-export after game source changes, then verify the folder contains `index.html` plus associated `.js`, `.wasm`, and `.pck` files.

If you change the export path, copy all exported files to:

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
