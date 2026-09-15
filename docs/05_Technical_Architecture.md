# 05 · Technical Architecture

Frontend + backend engineering specification. [ARCHITECT INFERENCE / PROPOSED DESIGN]

## 1. Frontend Architecture

### 1.1 Stack
Next.js 14 (App Router) · TypeScript (strict) · Tailwind CSS · next-intl · PWA (next-pwa/Workbox) · react-leaflet + OSM tiles (no API key) · TanStack Query · Zustand · Zod · Dexie (IndexedDB) · Playwright.

**Why:** one framework delivers PWA + role routing + i18n; Leaflet avoids Mapbox keys/cost; TanStack Query provides retry/caching critical on weak networks.

### 1.2 Folder structure
```
frontend/
├── app/                        # App Router
│   ├── (auth)/                 # login, register, onboarding
│   ├── (farmer)/               # dashboard, scan wizard, scans/[id], fields, history
│   ├── (expert)/               # case queue, case detail
│   ├── (officer)/              # dashboard, map, cases, reports
│   ├── (admin)/                # users, knowledge, models, config
│   └── api/                    # thin route handlers (proxy)
├── components/                 # design-system primitives (Button, Card, Stepper…)
├── features/                   # scan, diagnosis, risk, advisory, questions,
│                               # maps, expert, alerts  (each: components/ hooks/ api.ts)
├── services/                   # typed API client (fetch wrapper, retries, refresh)
├── hooks/                      # useGeolocation, useOnline, useSyncQueue, useAuth
├── lib/                        # image compression, idb outbox, jwt storage
├── stores/                     # zustand slices
├── types/                      # API DTO + domain types
├── i18n/                       # en.json, hi.json, hinglish.json + glossary
├── public/                     # manifest, icons, service worker
└── tests/                      # vitest + Playwright
```

### 1.3 Key mechanisms
- **Auth:** access token in memory + refresh in httpOnly cookie; silent refresh; role-based route guards; 401 → re-auth interceptor.
- **API layer:** typed fetch wrapper — timeouts, exponential backoff with jitter, idempotency keys on scan submission, offline detection → Dexie outbox.
- **Error handling:** API error envelope mapped (docs/39) to farmer-friendly localized messages; per-route error boundaries; no crashes on failures.
- **Loading:** skeletons everywhere; AI analysis shows staged progress (quality → analyzing → risk).
- **Image upload:** client resize/compress; EXIF stripped; progressive upload; client-side pHash for dedupe.
- **Offline:** app-shell precache; cached advisories/fields; outbox (`scans_pending`) with background sync; pending badges in UI.
- **i18n:** all strings via next-intl; disease names resolved from API-localized fields; glossary for agri terms; Hinglish = en strings with transliterated agri vocabulary.
- **Accessibility:** ≥44 px targets, large-text mode, icon+text pairing, high-contrast support.

## 2. Backend Architecture

### 2.1 Stack
Python 3.11+ · FastAPI · Pydantic v2 · SQLAlchemy 2 (async) + Alembic · PostgreSQL 16 (PostGIS, pgvector) · PyTorch/torchvision + ONNX Runtime · Ultralytics YOLO (nano) · XGBoost · httpx · argon2-cffi · APScheduler · pytest.

### 2.2 Folder structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI factory, middleware, routers
│   ├── core/                   # config (pydantic-settings), security, logging, errors
│   ├── api/
│   │   ├── deps.py             # auth guards, DB session, pagination
│   │   └── v1/                 # routers: auth, farms, fields, crops, scans, ai,
│   │                           # risk, weather, gis, expert, notifications,
│   │                           # knowledge, feedback, admin, health
│   ├── models/                 # SQLAlchemy ORM models (docs/07)
│   ├── schemas/                # Pydantic request/response DTOs
│   ├── services/               # business logic per domain
│   ├── ai/
│   │   ├── quality/            # quality engine (heuristics + model)
│   │   ├── vision/             # crop ID, disease classifier, pest detector
│   │   ├── uncertainty/        # calibration, OOD/energy scores
│   │   ├── questions/          # question bank + selection engine
│   │   ├── fusion/             # context fusion
│   │   └── inference.py        # single pipeline entrypoint
│   ├── risk/                   # factors, rules, scoring, outlook, escalation
│   ├── gis/                    # spatial queries, heatmap, DBSCAN wrappers
│   ├── weather/                # provider adapters, cache, validators
│   ├── rag/                    # ingestion, chunking, embeddings, retrieval
│   ├── recommend/              # advisory assembly, i18n, safety notes
│   ├── notifications/          # severity rules, dedupe, channel adapters
│   ├── tasks/                  # background jobs (worker loop; APScheduler)
│   └── utils/
├── alembic/                    # migrations
├── tests/                      # unit / integration / contract
├── scripts/                    # seed, ingest_docs, eval_model, backup
└── pyproject.toml
```

### 2.3 Conventions
- **Routers thin, services fat:** parse/validate → business rules in services → persistence via ORM.
- **Every AI call is logged** (model version, latency, outcome) — `ai_predictions` doubles as the monitoring ledger.
- **Idempotency:** scan submission carries `client_scan_uuid`; duplicates return the original result.
- **Transactions:** prediction + risk + advisory written atomically per scan.
- **Config:** pydantic-settings + `.env`; secrets never in code.
- **Errors:** RFC7807-style envelope with stable `code` values mapped to localized UI messages.

## 3. Cross-Cutting
- **API versioning** `/api/v1/…`; pagination cursor-based; time stored UTC, rendered Asia/Kolkata; uploads to backend (MVP) → presigned object-store URLs at scale **[FUTURE FEATURE]**.
