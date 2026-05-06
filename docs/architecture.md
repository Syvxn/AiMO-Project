# Architecture Outline

## Apps and Services

- apps/web: Next.js frontend pages and role-aware UI shell.
- apps/api: FastAPI backend for auth, quiz, scores, and integration endpoints.
- db: PostgreSQL for users, roles, quiz records, and score history.
- nginx: reverse proxy for web and API.

## Planned Integrations

- Godot web client embedded on Play page.
- Game server endpoints and websocket routing.
- AiMO agent service for chat quiz generation and analytics.

## Auth Roadmap

Phase 1:
- FastAPI JWT access tokens
- role claims for admin, teacher, student

Phase 2:
- Authentik OIDC provider
- role mapping from Authentik groups to application roles

## Deployment Recommendation

MVP target:
- Single VPS running Docker Compose with Nginx and TLS

Scale path:
- Move database to managed service
- Split services or transition to orchestrated deployment when needed
