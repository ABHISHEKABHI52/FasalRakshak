# 15 · Deployment Guide

Docker-first, single-VM deployable, SIH-demo friendly. [ARCHITECT INFERENCE]

## 1. Services (docker-compose)

| Service | Image/build | Ports | Volumes | Notes |
|---|---|---|---|---|
| `nginx` | nginx:stable | 80/443 | certs, frontend dist | TLS, rate limit, security headers, static + reverse proxy |
| `frontend` | Node build → static | internal | — | Next.js output consumed by nginx (or standalone node) |
| `backend` | python:3.11-slim + app | internal 8000 | media volume | uvicorn workers; AI models baked/in volume |
| `db` | postgis/postgis:16-3.4 (+pgvector) | internal 5432 | `pgdata` | init scripts: extensions, app role |
| `jobs` | same as backend (worker profile) | — | media | APScheduler loop (weather refresh, GIS jobs, exports) — merged into backend container at MVP |

Volumes: `pgdata`, `media` (images + knowledge docs + model artifacts). Healthchecks on all services; `depends_on` with condition; restart policies `unless-stopped`.

## 2. Environments

| Env | Purpose | Specifics |
|---|---|---|
| Development | local dev | hot-reload, seeded demo data, debug logs, no TLS |
| Staging | pre-demo validation | prod images, staging secrets, test weather keys, synthetic data labeled STAGING |
| Production | pilot/demo | pinned digests, TLS (Let's Encrypt), secrets via env injection, log rotation, backups on |

`.env.example` (names only): `DATABASE_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `ACCESS_TTL`, `REFRESH_TTL`, `WEATHER_PROVIDER`, `WEATHER_API_KEY?`, `CORS_ORIGINS`, `MEDIA_DIR`, `MODEL_REGISTRY_DIR`, `LOG_LEVEL`, `RATE_LIMIT_*`, `DEFAULT_LOCALE`. **Secrets never committed**; production values injected by deployment owner.

## 3. Database Operations

- **Migrations:** Alembic; `alembic upgrade head` on deploy (backward-compatible steps; expand→contract pattern for risky changes).
- **Backups:** nightly `pg_dump -Fc` + media volume sync to backup dir/off-box; retention 7–30 days; restore runbook rehearsed (`createdb → pg_restore`); **[P2] WAL archiving**.
- **Init:** extension bootstrap (`postgis`, `vector`), app role least-privilege (no DDL in prod runtime).

## 4. Model & Knowledge Artifacts

- `models/` registry layout: `{name}/{version}/model.onnx|pt + manifest.json (metrics, thresholds, sha256)`; boot verifies checksums; activation via admin API (status shadow→active) — never by file copy.
- Knowledge docs ingested via admin endpoint with metadata + checksum; embeddings built by `scripts/ingest_knowledge.py`; re-embedding migration documented when embedding model changes.

## 5. CI/CD (GitHub Actions)

PR: lint (ruff/eslint) → typecheck (mypy/tsc) → unit+contract tests (postgres service container) → build images. Main: push images (tagged `sha`) → deployment via documented script/SSH to VM (`docker compose pull && up -d` + `alembic upgrade head` + smoke `/ready`). Secrets in GitHub Actions secrets; no keys in repo.

## 6. Demo-day Deployment (SIH)

- **Mode A — online:** VM with public HTTPS + phones on venue Wi-Fi.
- **Mode B — offline (robust):** laptop runs full compose stack; phones connect via local hotspot to `https://demo.fasalrakshak.local` (self-signed, pre-installed trust) or LAN HTTP; OSM tiles pre-cached; seed data pre-loaded; weather adapter in **canned-data mode** (recorded fixtures, clearly labeled as demo fixtures).
- Fallback: recorded video backup of the full demo story.

## 7. Runbook Essentials

Scale up/down (`docker compose up -d --scale backend=2` behind nginx), log access (`docker compose logs -f backend`), DB shell, backup command, restore drill, model rollback (registry status flip + restart), incident checklist (docs/12 §12).

## 8. Resource Sizing (prototype)

| Env | CPU | RAM | Disk |
|---|---|---|---|
| Dev | 4 cores | 8 GB | 20 GB |
| Demo/pilot VM | 4–8 cores | 8–16 GB | 50–100 GB (media growth) |

CPU-only inference fits the budget (nano models); GPU optional **[ADVANCED]**.
