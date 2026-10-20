# Turnos y Reservas — Appointment Booking SaaS

[![CI](https://github.com/metalargento/turnos-y-reservas-public/actions/workflows/ci.yml/badge.svg)](https://github.com/metalargento/turnos-y-reservas-public/actions/workflows/ci.yml)

A multi-tenant appointment booking platform for small businesses (clinics, salons, gyms, workshops). A business owner signs up, completes a 5-step onboarding wizard, and gets a public booking page where customers reserve a slot without creating an account.

**Stack:** FastAPI (Python 3.11) · React + Vite + Tailwind CSS · PostgreSQL (Supabase) · Docker · GitHub Actions

**Live demo:** backend on Render (free tier) and frontend on Vercel. The Render backend sleeps after 15 minutes of inactivity, so the first request can take a while to respond.

## What it does

- **Owner panel** (JWT login): dashboard with booking stats, CRUD for services, branches and professionals, weekly availability and manual time blocks, booking management, logo/avatar upload, light and dark mode.
- **Onboarding wizard:** 5 steps (business, brand, first branch, services, scheduling settings). Progress is saved and resumed.
- **Public booking page** `/book/:slug`: no login. The customer picks a service and professional, sees only free slots (weekly availability, blocks and existing bookings are respected), and books.
- **Customer portal** `/mis-reservas/:slug`: customers look up and cancel their bookings with email and phone, or with the confirmation token, with no account.
- **Emails:** booking confirmation and cancellation through Resend, or through the business's own Gmail account (OAuth2 flow), with Resend as fallback.

## Architecture

```mermaid
flowchart LR
    Customer([Customer]) --> FE
    Owner([Business owner]) --> FE
    FE["Frontend<br/>React + Vite + Tailwind<br/>(Vercel)"] -->|REST / JSON| API
    subgraph API["Backend: FastAPI (Render)"]
        direction LR
        R[Router] --> C[Controller] --> S[Service] --> Repo[Repository]
    end
    Repo --> DB[(PostgreSQL<br/>Supabase)]
    API --> Storage[Supabase Storage<br/>logos and avatars]
    API --> Mail[Resend / Gmail OAuth2<br/>transactional email]
```

Backend layers (`backend/`): `routers` (HTTP only) → `controllers` (flow orchestration) → `services` (business logic) → `repositories` (SQL), plus `integrations` (Resend, Gmail, Supabase Storage), `middleware` (JWT auth, CORS, rate limiting, error handling) and `migrations` (versioned SQL).

## Run it locally

Requirements: Docker, Python 3.11+, Node.js 22+.

```bash
# 1. Database
docker compose up -d postgres          # PostgreSQL 16 on localhost:5433 (user postgres, password postgres by default)

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                   # then edit it (see below)
uvicorn main:app --reload --port 8000  # applies SQL migrations on startup

# 3. Frontend (another terminal)
cd frontend
npm ci
cp .env.example .env                   # VITE_API_URL=http://localhost:8000
npm run dev                            # http://localhost:5173
```

The default password can be changed by exporting `POSTGRES_PASSWORD` before the first `docker compose up`. In `backend/.env` set at least:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/turnos_reservas
SECRET_KEY=<any random string, 32+ characters>
JWT_SECRET=<a different random string, 32+ characters>
APP_ENV=development
```

Generate random values with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. API docs are served at http://localhost:8000/docs.

### Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `SECRET_KEY`, `JWT_SECRET` | yes | Application secret and JWT signing key |
| `APP_ENV` | no | `development` (default) or `production`. `localhost` origins are only allowed outside production |
| `ALLOWED_ORIGINS` | no | Comma-separated list of exact CORS origins |
| `FRONTEND_URL` | no | Used to build links in emails |
| `AUTH_RATE_LIMIT` | no | Login/register limit per IP (default `5/minute`) |
| `RESEND_API_KEY`, `EMAIL_FROM` | no | Transactional email. Without a key no email is sent |
| `SUPABASE_URL`, `SUPABASE_KEY` | no | Image uploads (Supabase Storage) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | no | Gmail OAuth2 connection |

Frontend: `VITE_API_URL` (backend base URL).

## Tests

The suite needs a PostgreSQL database whose name ends in `_test` (the tests refuse to run otherwise, so they can't touch real data). With the Docker database running:

```bash
cd backend
pip install -r requirements-dev.txt
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5433/turnos_reservas_test"
pytest -q
```

The database is created if missing, migrations are applied, and tables are cleaned between tests. Emails are stubbed. 21 tests cover registration and login, rate limiting, booking creation, double-booking and overlap prevention, cancellation (email + name, and token), minimum advance time, and `/health`.

## CI

`.github/workflows/ci.yml` runs on pushes to `main`, pull requests, and manually:

| Job | What it does |
| --- | --- |
| Backend | Python 3.11, PostgreSQL 16 service container, installs dependencies, runs `pytest` (applies migrations first) |
| Frontend | Node 24, `npm ci`, `npm run build` (TypeScript type-check + Vite build) |
| Docker | Builds the backend image without pushing it |
| Terraform | `fmt -check`, `validate` and an offline `plan` of `infra/` (fake credentials, never applies) |

No secrets are used; the test database credentials live in the workflow, and the Terraform job runs with fake AWS credentials.

## Infrastructure as code (AWS)

The live demo runs on Render, Vercel and Supabase. `infra/` is a Terraform description of how the same backend would run on AWS:

| Module | Resources |
| --- | --- |
| `network` | VPC, private subnets, NAT gateway, security groups (only the backend reaches the database) |
| `database` | RDS PostgreSQL 16, private and encrypted |
| `app` | ECR registry, Secrets Manager, IAM roles, App Runner service with a VPC connector |

```bash
cd infra
terraform init -backend=false
TF_VAR_use_fake_credentials=true TF_VAR_secret_key=x TF_VAR_jwt_secret=x TF_VAR_db_password=x terraform plan
```

The plan runs offline with fake credentials, so no AWS account is needed and nothing is created. It is deliberately never applied: the NAT gateway and RDS cost money, and the App Runner service needs an image pushed to ECR first. Secrets have no defaults and are never committed.

## Design decisions

- **Layered backend** with typed errors (`AppError`), so HTTP concerns, orchestration, business rules and SQL stay separate.
- **Schema as code:** versioned SQL files in `backend/migrations/` are applied automatically at startup and tracked in a `schema_migrations` table.
- **No accounts for customers:** bookings are managed with email + phone, or with a per-booking confirmation token.
- **Double-booking protection in two layers:** an application-level conflict check, and a PostgreSQL exclusion constraint (`bookings_no_overlap`) that closes the race between check and insert. The API returns 409 on conflict.
- **Email fallback:** Gmail of the business first, then Resend. Email failures never block a booking.
- **Rate limiting** on login and register (slowapi), and **CORS** limited to exact origins from `ALLOWED_ORIGINS`.
- **Health check:** `GET /health` runs `SELECT 1` and returns 200 or 503 without exposing error details.

## Known limitations

- The Render free tier sleeps after 15 minutes of inactivity (slow first request).
- Rate limiting is in memory (resets on deploy, not shared across processes) and keys on the first `X-Forwarded-For` value, which a client can spoof.
- Business timezone is hardcoded to `America/Argentina/Buenos_Aires` in the booking logic.
- The Gmail OAuth2 flow is implemented but was not verified end to end (it needs the redirect URI configured in Google Cloud Console).
- The frontend has no lint script or automated tests; the access token is stored in `localStorage`.
- Not implemented yet: Mercado Pago payments, Google Calendar sync, WhatsApp/email reminders, password reset, email verification, bulk cancellation, a dedicated panel for the `professional` role.

## Repository layout

```
backend/    FastAPI app, SQL migrations, tests
frontend/   React + Vite + Tailwind app
infra/      Terraform for AWS (network, database, App Runner)
docs/       Development notes, original design document, progress log
.github/    CI workflow
```

`docs/ORIGINAL-DESIGN.md` is the initial product design and differs from the implementation in places; this README describes what is built.
