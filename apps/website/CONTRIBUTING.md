# Website Contributor Guide

This guide is the fastest way to get productive in the website app.

## What this app does

The website app provides:

- public pages (landing/about/contact)
- authentication (register/login)
- role-aware pages (admin/student/teacher flows)
- the Play entry page that launches the Godot web build

High-level request flow:

1. Browser hits Nginx at `http://localhost`.
2. Nginx sends web traffic to Next.js and `/api/*` traffic to FastAPI.
3. FastAPI talks to PostgreSQL for user/auth data.
4. Frontend stores auth state and enforces protected routes.

## Project map

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `infra/nginx/default.conf`: reverse proxy rules
- `docker-compose.yml`: local multi-service startup
- `docs/architecture.md`: architecture notes

Frontend paths you will edit most often:

- `apps/web/src/app`: routes and pages
- `apps/web/src/components`: shared UI (navigation, guards)
- `apps/web/src/lib`: API calls and auth context

Backend paths you will edit most often:

- `apps/api/app/routers`: API endpoints
- `apps/api/app/core`: config, password hashing, JWT
- `apps/api/app/models.py`: SQLAlchemy models

## Local setup

From `apps/website`:

```bash
cp .env.example .env
docker compose up --build
```

PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open:

- website: `http://localhost`
- API: `http://localhost/api`
- health: `http://localhost/api/health`

Stop services:

```bash
docker compose down
```

## First frontend change (example)

Goal: change text on the Play page.

1. Open `apps/web/src/app/play/page.tsx`.
2. Edit heading/body text.
3. Save and refresh `http://localhost/play`.

Why this works quickly: `next dev` runs in the web container with hot reload.

## Common frontend tasks

- Add a page: create folder under `apps/web/src/app/<route>/page.tsx`.
- Add reusable UI: place component in `apps/web/src/components`.
- Call backend API: add function in `apps/web/src/lib/api.ts`.
- Protect a page by role: wrap page with `ProtectedRoute` from `apps/web/src/components/protected-route.tsx`.

## Common backend tasks

- Add endpoint: create/update router in `apps/api/app/routers`, then include it in `apps/api/app/main.py`.
- Add model fields/tables: update `apps/api/app/models.py`.
- Update auth behavior: edit `apps/api/app/core/security.py` and `apps/api/app/routers/auth.py`.

## Game integration notes

The Play page launches a Godot web export from:

- `apps/web/public/game/index.html`

If exporting from the game app, copy all web export files (`.html`, `.js`, `.wasm`, `.pck`) into `apps/web/public/game/`.

## Quality checks before opening a PR

From `apps/website/apps/web`:

```bash
npm run lint
npm run format:check
```

From `apps/website`:

```bash
docker compose ps
```

Quick manual check list:

- login/register works
- protected routes redirect correctly
- API health endpoint returns `{"status":"ok"}`
- changed pages render on mobile and desktop widths

## Troubleshooting

- Port 80 busy: stop other web servers, then restart compose.
- API unavailable in UI: check `docker compose logs api`.
- Login fails unexpectedly: confirm DB is up and seed users are present.
