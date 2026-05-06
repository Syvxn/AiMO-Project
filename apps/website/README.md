# AiMO-Website

Monorepo for the AiMO web platform.

## Stack

- Frontend: Next.js (apps/web)
- API: FastAPI (apps/api)
- Authentication: JWT first, Authentik in later phase
- Database: PostgreSQL
- Reverse proxy: Nginx
- Local integration: Docker Compose

## MVP Pages

- Landing
- Play
- Login
- Register
- Contact
- About
- Admin (role-aligned starter page)

## Roles

- admin
- teacher
- student

## Run locally with containers

1. Copy .env.example to .env
2. Run docker compose up --build
3. Open http://localhost

## Service URLs

- Web via Nginx: http://localhost
- API via Nginx: http://localhost/api
- API health: http://localhost/api/health

## Game Launcher Integration (Website Side)

The Play page now launches a Godot web export from:

- `/game/index.html`

Place exported game files in this folder inside the website app:

- `apps/web/public/game/`

Expected result after placing files:

- `http://localhost/game/index.html` loads directly
- `http://localhost/play` shows `Game export detected` and allows launch

Typical Godot web export artifacts include:

- `index.html`
- one or more `.js` files
- one or more `.wasm` files
- one or more `.pck` files

If Play says no export was found, verify the file path is exactly:

- `apps/web/public/game/index.html`

## Notes

- Current auth endpoints are stubs to accelerate initial frontend and integration work.
- Quiz and score endpoints currently return placeholder data and will be wired to the agent service next.
- Authentik integration is planned after MVP baseline is stable.
