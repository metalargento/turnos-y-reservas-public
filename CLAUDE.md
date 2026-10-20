# CLAUDE.md

Guidance for Claude Code when working in this repository. For the user-facing overview, setup and architecture diagram, see [README.md](README.md).

## What this project is

A multi-tenant appointment booking SaaS for small businesses (clinics, salons, gyms, workshops). An owner signs up, completes a 5-step onboarding wizard, and gets a public booking page where customers reserve a slot without an account.

## Stack

- **Backend:** Python 3.11, FastAPI, PostgreSQL 16 (psycopg, raw SQL), pytest
- **Frontend:** React, Vite, TypeScript, Tailwind CSS
- **Email:** Resend, or the business's own Gmail via OAuth2 (Resend as fallback)
- **Storage:** Supabase Storage (logos and avatars)
- **Infra:** Docker, GitHub Actions CI, Terraform description of an AWS deployment (`infra/`, plan-only, never applied)
- **Live demo:** Render (backend), Vercel (frontend), Supabase (database)

## Repository layout

```
backend/
├── main.py            # Entry point, middleware wiring, startup migrations
├── config/            # Settings loaded from environment variables
├── routers/           # HTTP endpoints only, no business logic
├── controllers/       # Flow orchestration
├── services/          # Business logic
├── repositories/      # SQL access
├── integrations/      # External services (Resend, Gmail, Supabase Storage)
├── schemas/           # Pydantic models
├── middleware/        # JWT auth, CORS policy, rate limiting, error handling
├── utils/             # Logger, DB client, AppError
├── migrations/        # Versioned SQL, applied automatically at startup
└── tests/             # pytest suite (needs a *_test PostgreSQL database)
frontend/              # React app (owner panel, public booking page, customer portal)
infra/                 # Terraform: network, database, App Runner
docs/                  # Development notes (written in Spanish)
```

## Commands

```bash
docker compose up -d postgres                       # Local PostgreSQL on :5433
cd backend && uvicorn main:app --reload --port 8000 # API; applies migrations on startup
cd backend && pytest -q                             # Needs TEST_DATABASE_URL ending in _test
cd frontend && npm run dev                          # Dev server on :5173
cd frontend && npm run build                        # Type-check + production build
cd infra && terraform fmt -check -recursive && terraform validate
```

CI (`.github/workflows/ci.yml`) runs backend tests, the frontend build, a Docker image build and Terraform fmt/validate/plan. Keep all four green.

## Conventions

- **Layering:** router → controller → service → repository → DB. Routers never contain business logic; repositories never contain business rules.
- **Errors:** raise `AppError` (message, code, status_code). The global handler in `middleware/error_handler.py` turns it into a JSON response.
- **CORS:** a single policy lives in `middleware/cors_policy.py` (exact origins from `ALLOWED_ORIGINS`; localhost only outside production). Reuse it. Never match origins by substring.
- **Logging:** business events only, through `utils.logger`. Never log secrets or personal data.
- **Validation:** every request body is a Pydantic schema. External IDs are typed as UUID in endpoints.
- **Docstrings:** required on service and integration functions.
- **Secrets:** none in code or in git. Configuration comes from environment variables (`backend/.env.example` lists them).
- **File size targets:** routers ~80 lines, controllers ~100, services ~150, repositories ~100. A few files exceed these today; when touching one, propose how to split it before adding more code.
- **Language:** code, comments, commit messages and the README are in English. Everything under `docs/` is in Spanish.

## Migrations

The SQL files in `backend/migrations/` are the source of truth for the schema.

- Files are named `NNN_description.sql` and run in name order from `migrations/run_migrations.py` on FastAPI startup.
- Applied files are recorded in the `schema_migrations` table, so each runs once.
- To change the schema, add a new numbered file. Never edit one that has already been applied.
- Write idempotent SQL where practical (`IF NOT EXISTS`, guarded `ALTER`).

## Domain rules worth knowing

- **Double-booking protection has two layers:** an application-level conflict check, plus a PostgreSQL exclusion constraint (`bookings_no_overlap`, migration 011) that closes the race. A conflict returns 409.
- **Customers have no accounts.** They manage bookings with email + phone, or with a per-booking confirmation token.
- **Email failures never block a booking.** Gmail of the business is tried first, then Resend.
- **Auth routes are rate limited** (slowapi, in memory). `GET /health` runs `SELECT 1` and returns 200 or 503.
- **Business timezone** is currently hardcoded to `America/Argentina/Buenos_Aires` in the booking logic.

## Working rules

- Stay within the scope of the task; do not modify unrelated files.
- Ask before choosing between two materially different approaches.
- Follow `docs/BASES-DE-DESARROLLO.md` (development), `docs/SEGURIDAD-PENTEST.md` (security) and `docs/UX-UI.md` (UX for non-technical small-business users).
- Run the relevant tests before calling a change done, and say so plainly if something fails or was not run.
- Do not push, and do not touch `infra/` apply behavior, without explicit confirmation.

## Status

**Implemented:** JWT auth, 5-step onboarding, CRUD for services, branches and professionals, weekly availability and manual time blocks, bookings (panel and public), customer portal, dashboard stats, image upload, Gmail OAuth2 and Resend email, rate limiting, health check, CI, Terraform plan for AWS.

**Not implemented:** Mercado Pago payments, Google Calendar sync, reminders, password reset, email verification, bulk cancellation, a dedicated panel for the `professional` role.

**Known gaps:** in-memory rate limiting, hardcoded timezone, access token in `localStorage`, no frontend tests or lint script, Gmail OAuth2 not verified end to end. See "Known limitations" in the README.
