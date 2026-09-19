# Implementation Status

> Authoritative architecture: `docs/00`–`docs/22`. This file tracks **implementation** only.
> Status labels used everywhere: **IMPLEMENTED** · **MVP** · **SIH DEMO** · **ADVANCED** · **FUTURE PHASE**.

## Phase 1 — Platform Foundation: COMPLETE (verified)

### Implemented

| Area | What exists | Status |
|---|---|---|
| Repository structure | `backend/`, `frontend/`, `ai/`, `database/`, `docs/`, `scripts/`, `tests/`, `docker/`, `.github/` | IMPLEMENTED |
| Backend service | FastAPI factory (`backend/app/main.py`), `/api/v1` versioning, CORS from env, request-ID + structured JSON logging middleware, error envelope `{code, message_key, details}`, no stack traces to clients | IMPLEMENTED |
| Configuration | `pydantic-settings`; env-driven `DATABASE_URL`, `JWT_SECRET` (≥32 chars enforced), token TTLs, CORS, rate limits; production refuses the dev JWT placeholder | IMPLEMENTED |
| Database | PostgreSQL 16 + PostGIS + pgvector image (`docker/database/Dockerfile` + `database/init/01_extensions.sql`), async SQLAlchemy 2 session layer, DB health probe | IMPLEMENTED (runtime needs Docker) |
| Migrations | Alembic async env; `0001_initial_foundation` creates `roles`, `users`, `user_roles`, `refresh_tokens`, `audit_logs` and seeds the 5 roles; `upgrade` / `downgrade -1` / re-`upgrade` verified locally, PostgreSQL DDL verified offline | IMPLEMENTED |
| Authentication | `POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `GET /api/v1/auth/me`; Argon2id hashing; JWT access tokens (HS256, configurable TTL); rotating refresh tokens stored only as SHA-256 hashes, delivered in httpOnly cookies | IMPLEMENTED |
| RBAC | Roles FARMER · EXTENSION_WORKER · EXPERT · OFFICER · ADMIN; `require_role(...)` dependency enforced server-side; `/api/v1/admin/ping` is an ADMIN-only reference endpoint | IMPLEMENTED |
| Audit logging | Append-only `audit_logs` + `AuditService`; records `user.register`, `user.login`, `user.login_failed` with hashed IP | IMPLEMENTED |
| Health/readiness | `GET /api/v1/health` (liveness), `GET /api/v1/ready` (DB probe, 503 when down) | IMPLEMENTED |
| Frontend foundation | Next.js App Router + TypeScript strict + Tailwind; FasalRakshak landing shell (brand, tagline, Evidence > Guess, honest status note), `/login` page wired to the real API, route `error.tsx`, reusable `ErrorBoundary`, `loading.tsx`, 404 page, PWA manifest + icon, typed API client with error mapping | IMPLEMENTED |
| Tests | Backend: 33 pytest tests (health, readiness incl. DB-down 503 and no-internals-leak, register, duplicate, validation errors, login success/invalid/unknown, `/me`, refresh rotation + reuse rejection, rate limiting, RBAC denial for all non-ADMIN roles + ADMIN allow, role round-trip for all five roles, audit rows, DB connectivity, seeded roles). Frontend: landing-shell + error-message vitest suites (6 tests) | IMPLEMENTED |
| CI | GitHub Actions: backend tests + migrations against real PostgreSQL (upgrade → downgrade → upgrade + `alembic check`), frontend typecheck/tests/build, `docker compose config -q` | IMPLEMENTED |
| Docker Compose | `db` (PostGIS + pgvector, healthcheck), `backend` (migrates then serves, healthcheck), `frontend`; service-name networking (no localhost inside containers) | IMPLEMENTED (authored; live run needs Docker — see limitations) |

### Not implemented (deliberately, per Phase 1 scope)

Marked **TODO — FUTURE PHASE**: crop/field/crop-cycle domain tables and APIs, scan upload, image quality engine,
AI vision pipeline, adaptive question engine, context fusion, risk engine, weather integration, GIS intelligence,
RAG knowledge system, expert validation console, officer dashboard, notifications, offline sync, PWA service worker,
UI session persistence/protected routes, SMS adapters, IoT/satellite inputs.
See `docs/19_Future_Roadmap.md` and `docs/00` §§42–45 for sequencing. **No AI code exists yet.**

## Commands

```powershell
# 1) Environment
./scripts/init_env.ps1                 # creates .env from .env.example (edit secrets first)

# 2) Full stack (requires Docker Desktop — validates PostGIS + pgvector + migrations)
docker compose up --build              # db -> backend (alembic upgrade head) -> frontend
#   API:      http://localhost:8000/api/v1/health   ·  docs: http://localhost:8000/api/docs
#   Frontend: http://localhost:3000

# 3) Backend only (no Docker; SQLite fallback for local smoke tests)
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q          # 33 tests
.venv\Scripts\python -m alembic upgrade head

# 4) Frontend only
cd frontend
npm install
npm run typecheck; npm run test; npm run build   # or: npm run dev

# 5) Everything at once
./scripts/run_all_checks.ps1
```

## Environment variables

See `.env.example` (root) and `frontend/.env.example`. Never commit `.env`.
Key values: `DATABASE_URL` (`postgresql+asyncpg://…@db:5432/…` in Compose), `JWT_SECRET` (≥32 chars),
`ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`.

## Known limitations (honest)

1. **Docker was not executed on the authoring machine** (Docker Desktop absent). The compose file, the PostGIS/pgvector image and the migration DDL were verified by configuration review plus offline PostgreSQL DDL generation (`alembic upgrade head --sql`). A live PostgreSQL run happens in CI and on any machine with Docker.
2. Backend tests run on an **isolated per-test SQLite database**. Phase-1 tables are deliberately portable (JSONB→JSON, BIGINT→INTEGER variants for SQLite); PostgreSQL-specific behaviour is validated separately in CI, including `alembic check` for model/migration drift.
3. `POST /api/v1/auth/register` returns `{user_id, roles}` — `docs/08` §1 shows `role` (singular, lowercase); the plural form matches the M:N `user_roles` design in `docs/07`. Reconcile the docs example when convenient.
4. Login is **phone-or-email + password** only. OTP, password reset and email verification are FUTURE PHASE.
5. Refresh cookie is `SameSite=Lax` with `Secure` outside development; CSRF hardening for cross-site deployment is FUTURE PHASE.
6. Rate limiting is in-process (single worker). Distributed limiting (Redis) is FUTURE PHASE.
7. No nginx/TLS/object storage in Compose yet — that belongs to the deployment phase (`docs/15`).

## Next recommended phase

**Phase 2 — Farmer core loop (MVP):** farm/field/crop-cycle domain tables + APIs, scan capture with client-side
compression and idempotency, the image-quality gate, then the AI disease classifier behind the documented
uncertainty / "insufficient evidence" contract — with tests at every step. Do not start until this status is
reviewed.