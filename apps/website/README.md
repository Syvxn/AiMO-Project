# AiMO-Website

Monorepo for the AiMO web platform.

## Contributor quick start

If you are new to this app, start with:

- `CONTRIBUTING.md`

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

The API container runs Alembic migrations on startup (`upgrade head`) before launching FastAPI.

### Run the agents service with an NVIDIA GPU

The default Compose setup remains compatible with CPU-only machines. On a host with NVIDIA GPU support in Docker Desktop, start the stack with the GPU override:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build -d
```

The agents container uses `DEVICE_MAP=auto` and loads quiz models in FP16 when CUDA is available. Verify access with:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec agents python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU fallback')"
```

For CPU-only development, continue using `docker compose up --build`.

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

## Game WebSocket Proxy (Client <-> Dedicated Server)

Nginx now proxies game websocket traffic through:

- `ws://localhost/game-ws`

This route forwards to a dedicated game server process running on the host machine at:

- `host.docker.internal:8910`

Recommended game-side env values:

- `GAME_SERVER_URL`: `ws://localhost/game-ws`
- `GAME_SERVER_PORT`: `8910`

Notes:

- Keep website docker stack on port 80 as-is.
- Run the dedicated game server separately so it listens on host port `8910`.
- If you change the dedicated server port, update both nginx `default.conf` and game env values.

## Notes

- Current auth endpoints are stubs to accelerate initial frontend and integration work.
- Quiz and score endpoints currently return placeholder data and will be wired to the agent service next.
- Authentik integration is planned after MVP baseline is stable.
