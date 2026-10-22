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
- `apps/api/alembic/versions`: schema migrations

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

## Database migrations (required workflow)

This app is migration-driven. Do not rely on `Base.metadata.create_all` for schema updates.

With Docker Compose, migrations are applied automatically when the API container starts.

Manual commands (from `apps/website/apps/api`):

```bash
alembic -c alembic/alembic.ini upgrade head
```

Create a new migration after model changes:

```bash
alembic -c alembic/alembic.ini revision -m "describe_change"
```

Then implement the migration in `apps/api/alembic/versions/` and run upgrade again.

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
- Add model fields/tables: update `apps/api/app/models.py` and add an Alembic migration.
- Update auth behavior: edit `apps/api/app/core/security.py` and `apps/api/app/routers/auth.py`.

## Game integration notes

### Uploaded textbook units

`apps/api/app/services/textbooks.py` contains a page-aware adapter for the
interleaved Think English student/teacher edition. It identifies units and page
roles from running headers, keeping teacher notes separate from student text and
excluding the contents, course map, and back matter. Other documents continue to
use the generic chapter parser. New textbook layouts should get their own adapter
and fixtures rather than hardcoded page numbers in the quiz generator.

The chapter listing exposes only IDs and titles. The generation request sends the
selected student unit and its teacher guidance separately to the agents service.
Existing uploaded files are parsed on request, so no re-upload is needed.
Reopen the minigame's chapter picker after a parser update.

### Teacher-approved question bank

Migration `005` adds `question_bank_items`; API startup applies migrations.
The teacher panel's Minigame Question Bank provides separate textbook and unit
selectors, a draft count from 1–10, and manual questions. Saved question cards
start collapsed. Each card supports form and JSON editing with the same validation
and explicit save/approval actions. The selected unit's saved bank can also be
viewed, edited and downloaded as JSON; this view excludes unsaved card edits. Student text
and teacher guidance remain separate internally without full-text panels in the UI. AI drafts
always start unapproved. Teachers can edit four options, select one correct answer,
and save as draft or approve. The exact evidence quotation must match student text
from the selected unit. Approval is a human correctness and age-suitability review;
model validation alone is insufficient.

Enrolled students' `/quiz/game/generate` requests sample only their teacher's
approved questions. The service never falls back to AI when the bank is too small.
Questions and options are shuffled with the correct answer remapped to A–D.
Serving a game does not parse the PDF or require the agents service. Saving as draft
withdraws approval immediately for future games; deleting a material cascades to
its bank questions. Already-started games retain their received quiz snapshot.
Students without a class retain the existing general-practice path.

Teacher draft generation allows up to 600 seconds for a model response, with a
630-second proxy read limit on that endpoint. Ordinary quiz calls keep their
180-second model timeout. A model read timeout returns 504 with a smaller-batch
suggestion; connection failures return 503. Larger batches may take several minutes.
Invalid draft candidates are skipped individually. If any valid candidates remain,
they are saved unapproved and returned, with `skipped_count` describing rejected
candidates. The interface reports the saved count against the requested count.

Teacher endpoints under `/teacher/question-bank`: `GET /chapters`, `GET` with
`chapter_id`, `POST /drafts`, `POST` for manual questions, `PUT /{id}`, and
`DELETE /{id}`. They are authenticated and scoped to the current teacher's uploads.
`PUT /json` accepts an exported bank object with `chapter_id`, up to 500 questions,
and an explicit `approve_all` flag (false by default). Existing IDs update existing
questions in the selected unit; omitted/null IDs create new questions. Omitted
questions are retained. The entire batch's structure, IDs and student quotations
are checked before any changes or approvals are applied. New and changed questions
become drafts on an ordinary save; unchanged approvals are preserved. Embedded
`status`/`reviewed_at` values do not approve questions. The interface exposes both
Approve all for a unit's saved questions and Save JSON and approve all for the
submitted JSON. These actions approve only on the teacher's explicit click.
`tests/test_question_bank.py` covers ownership, source boundaries, draft exclusion,
approval withdrawal, full question counts, option remapping, and deletion cleanup.

`tests/test_textbooks.py` includes a real-PDF regression check. It discovers the
book under the repository's `docs/` directory, or at `AIMO_TEXTBOOK_PATH` when
running tests in a container. The test is skipped if that optional fixture is
unavailable.

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
