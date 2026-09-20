# Implementation Status

> Authoritative architecture: `docs/00`–`docs/22`. This file tracks **implementation** only.
> Status labels used everywhere: **IMPLEMENTED** · **MVP** · **SIH DEMO** · **ADVANCED** · **FUTURE PHASE**.

## Phase 2 — Farmer Core Loop (MVP): COMPLETE (verified)

### Implemented

| Area | What exists | Status |
|---|---|---|
| **Farm** | Model, schema, repository, service, API (`POST/GET/PATCH /api/v1/farms`), ownership enforcement, tests | IMPLEMENTED |
| **Field** | Model, schema, repository, service, API (`POST/GET/PATCH /api/v1/fields`), PostGIS geometry, ownership enforcement, tests | IMPLEMENTED |
| **Crop** | Canonical crop catalog entity, seed data (`database/seed_data.py`), retrieval API (`GET /api/v1/crops`), tests | IMPLEMENTED |
| **CropCycle** | Model, schema, repository, service, API (`POST/GET/PATCH /api/v1/crop-cycles`), field ownership validation, tests | IMPLEMENTED |
| **Scan** | Model, schema, repository, service, API (`POST /api/v1/scans`), `client_scan_uuid` idempotency, lifecycle states (`CREATED → IMAGE_UPLOADED → QUALITY_CHECKING → QUALITY_ACCEPTED → ANALYZING → COMPLETED`, plus `QUALITY_REJECTED`, `ANALYSIS_FAILED`, `INSUFFICIENT_EVIDENCE`), ownership enforcement, tests | IMPLEMENTED |
| **ImageAsset** | Model, repository, secure local storage (`app/storage/local.py`), MIME/type/size/dimension validation, path traversal protection, safe generated filenames | IMPLEMENTED |
| **Image Quality Engine** | `app/quality/engine.py` + `validation.py`: resolution, blur, brightness, darkness checks. Output: `quality_score` (0–100) + status (`GOOD` / `ACCEPTABLE` / `POOR` / `UNUSABLE`). Prototype thresholds labeled as such. Usable image blocks diagnosis. | IMPLEMENTED |
| **AI Analysis Contract** | `app/analysis/service.py`: clean `ImageAnalysisService` interface accepting `ImageAsset + Crop + CropCycle + Field context`, returning `diagnosis_candidates`, `confidence`, `insufficient_evidence` flag, `model_version`, `inference_metadata`. Deterministic mock for tests only — clearly labeled mock/test behavior. | IMPLEMENTED (contract + mock; real model = FUTURE) |
| **Insufficient Evidence** | First-class outcome throughout scan lifecycle. Quality gate blocks diagnosis on `UNUSABLE`. AI contract returns `insufficient_evidence` rather than forced diagnosis. | IMPLEMENTED |
| **Scan History** | `GET /api/v1/scans` (owner-only, paginated), `GET /api/v1/scans/{id}` with quality result and analysis result. | IMPLEMENTED |
| **Farmer Frontend Flow** | 8 dashboard pages: `/dashboard`, `/dashboard/farms`, `/dashboard/farms/[farmId]`, `/dashboard/farms/[farmId]/fields`, `/dashboard/farms/[farmId]/fields/[fieldId]`, `/dashboard/farms/[farmId]/fields/[fieldId]/cycles`, `/dashboard/farms/[farmId]/fields/[fieldId]/cycles/[cycleId]/scans`, `/dashboard/scans`. Login page, auth context, typed API client, responsive Tailwind UI. | IMPLEMENTED |
| **Providers/Auth** | `frontend/src/app/providers.tsx` — client component wrapping `AuthProvider`. `layout.tsx` is server component with metadata exports. `auth_context.tsx` — in-memory session (Phase 2). | IMPLEMENTED |
| **Tests** | Backend: 72 pytest tests (Phase 1: 33 + Phase 2: 39 covering farms, fields, crops, cycles, scans, idempotency, image pipeline, quality engine, ownership protection). Frontend: vitest 6/6. | IMPLEMENTED |
| **Build** | TypeScript strict passes. Next.js production build passes (8/8 routes). | IMPLEMENTED |
| **Docker Compose** | Unchanged from Phase 1 — `db`, `backend`, `frontend`. | IMPLEMENTED (authored; live run needs Docker) |
| **CI** | Unchanged from Phase 1. | IMPLEMENTED |

### Repair (this commit)

- Fixed 5 corrupted dashboard page files (duplicated `use client`, duplicated component copies, malformed JSX)
- Created `frontend/src/app/providers.tsx` (client component) and `frontend/src/app/layout.tsx` (server component with metadata) — resolved `useAuth must be used inside an AuthProvider` prerender error
- Removed empty duplicate `frontend/src/lib/auth-context.tsx`
- Added `.gitattributes` for consistent LF line endings
- Removed temporary recovery scripts (`repair_frontend.py`, `frontend/write_*.py`)
- Fixed `input` component / Button size root cause in shared UI component
- Fixed 4 unused-variable TypeScript issues

### Test results

- **Backend pytest**: 72 passed
- **Frontend vitest**: 6 passed
- **TypeScript**: 0 errors
- **Next.js build**: 8/8 routes compiled successfully
- **git diff --check**: clean
- **Working tree**: clean after commit `cf1968a`

### Known limitations

1. **Docker not executed locally** — CI covers live PostgreSQL + PostGIS + pgvector validation.
2. Backend tests use isolated SQLite; PostgreSQL DDL verified offline via `alembic upgrade head --sql`.
3. Register returns `roles` (M:N) vs `role` (singular) in docs/08 §1 — documented limitation.
4. Login is phone/email + password only (no OTP, reset, verification).
5. Refresh cookie `SameSite=Lax`; CSRF hardening = FUTURE PHASE.
6. Rate limiting is in-process; Redis = FUTURE PHASE.
7. Image quality thresholds are prototype values — not scientifically validated.
8. `ImageAnalysisService` uses deterministic mock for tests; real AI model = FUTURE PHASE.
9. No PWA service worker offline sync yet (Phase 2+).

### Next recommended phase

**Phase 3 — Field Validation & SIH Demo Polish:** real image dataset integration, crop-specific quality thresholds, scan status real-time updates, expanded farmer UI with result visualization, and SIH demo story rehearsal.

## Phase 1 — Platform Foundation: COMPLETE (verified)

### Implemented

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

### Not implemented (as of Phase 1, since Phase 2 addressed the farmer core loop)

The items below were listed as not implemented at Phase 1 time. They have since been
implemented in **Phase 2** (see the Phase 2 table above): crop/field/crop-cycle domain
tables and APIs, scan creation with `client_scan_uuid` idempotency, image upload with
secure local storage, the image-quality engine, the AI analysis contract, scan history,
and the farmer dashboard pages.

Remaining **not implemented** per current scope:

Marked **TODO — FUTURE PHASE**: disease/pest AI vision model training and inference,
adaptive question engine, context fusion, risk engine, weather integration, GIS intelligence,
RAG knowledge system, expert validation console, agriculture officer dashboard,
notifications, offline sync, PWA service worker, UI session persistence/protected routes,
SMS adapters, IoT/satellite inputs.
See `docs/19_Future_Roadmap.md` and `docs/00` §§42–45 for sequencing.

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

**Phase 3 — Field Validation & SIH Demo Polish:** real image dataset integration, crop-specific quality thresholds, scan status real-time updates, expanded farmer UI with result visualization, and SIH demo story rehearsal.