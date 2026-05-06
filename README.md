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

## Notes

- Current auth endpoints are stubs to accelerate initial frontend and integration work.
- Quiz and score endpoints currently return placeholder data and will be wired to the agent service next.
- Authentik integration is planned after MVP baseline is stable.
