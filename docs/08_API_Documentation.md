# 08 · API Documentation

REST API under `/api/v1/`. Conventions: JSON bodies; JWT Bearer auth (access token); errors as `{code, message_key, details}` with accurate HTTP status; cursor pagination (`?cursor=&limit=`); idempotency via `client_scan_uuid`; all timestamps ISO-8601 UTC. Auth roles shown per endpoint; "own" = row-level scoped to the caller. Status: [PROPOSED DESIGN] — implemented endpoints will be validated against docs/16 contract tests.

## 1. Auth

### POST /api/v1/auth/register — public
Request: `{phone, password, full_name, preferred_language, district?, state?, consent_ml_use}` → 201 `{user_id, role:"farmer"}`. Errors: 400 invalid (phone format, weak password), 409 duplicate phone. Validation: phone E.164-ish (10–13 digits), password ≥8 chars.

### POST /api/v1/auth/login — public
Request: `{phone_or_email, password}` → 200 `{access_token, expires_in, refresh_token_in_cookie:true, user{…}}`. Errors: 401 invalid credentials (generic message), 429 rate-limited (5/min/IP).

### POST /api/v1/auth/refresh — public (cookie)
Refresh httpOnly cookie → 200 new access token. 401 on invalid/expired/revoked. **POST /api/v1/auth/logout** — auth → 204; revokes refresh token.

### GET/PATCH /api/v1/users/me — any authed
GET → 200 profile. PATCH `{full_name?, preferred_language?, district?}` → 200. Role changes are admin-only (audited).

## 2. Farms, Fields, Crops

### POST /api/v1/farms — farmer
`{name, address?, district?, state?}` → 201 `{id, …}`. GET /api/v1/farms — farmer (own) → 200 list. PATCH/DELETE (archive) `/api/v1/farms/{id}` — owner → 200/204. Errors: 403 non-owner, 404.

### POST /api/v1/fields — farmer (owner of farm)
`{farm_id, name, area_hectares?, location:{lat,lng}, soil_type?}` → 201. Validation: lat −90..90, lng −180..180. GET `/api/v1/fields?farm_id=` (own; extension: assisted) ; GET `/api/v1/fields/{id}` — owner/officer-district; PATCH; DELETE (soft). PostGIS stores geography(Point,4326).

### GET /api/v1/crops — any authed
→ 200 `[{code, name_en, name_hi, is_supported, stage_model}]`. POST/PATCH — admin only (catalogue management).

### POST /api/v1/crop-cycles — farmer
`{field_id, crop_id, variety?, sowing_date, expected_harvest_date?}` → 201 (server derives `current_stage`). GET `/api/v1/crop-cycles?field_id=` — owner. PATCH `/api/v1/crop-cycles/{id}` (complete/abandon). Errors: 400 invalid dates, 403.

## 3. Scans

### POST /api/v1/scans — farmer (own field)
Request: `{field_id, crop_cycle_id, plant_part, captured_at, client_scan_uuid}` → 201 `{scan_id, status:"pending_image"}`. **Idempotency:** same `client_scan_uuid` → 200 with the *original* scan (no duplicate). Errors: 400 validation, 403 not-own-field, 404 field/cycle missing.

### POST /api/v1/scans/{id}/image — owner
multipart/form-data `image` → 202 `{scan_id, image_id, status:"analyzing"}`. Validation: JPEG/PNG/WebP magic bytes, ≤10 MB; server re-encodes (EXIF stripped). Errors: 413 too large, 415 unsupported, 409 already-has-image (re-upload replaces within pending window).

### GET /api/v1/scans?field_id=&cursor= — owner (farmer), assigned (expert), district (officer, aggregated)
→ 200 `{items:[scan summaries], next_cursor}`. GET /api/v1/scans/{id} — full detail incl. quality, predictions, diagnosis, risk, recommendation (as available).

### POST /api/v1/scans/{id}/questions — owner
Request: `{round:1}` → 200 `{questions:[{id, code, text_en, text_hi, answer_type, options[]}]}`. Returned only when diagnosis state = insufficient_evidence. Errors: 409 not-in-questioning-state.

### POST /api/v1/scans/{id}/answers — owner
Request: `{answers:[{question_id, value}]}` → 202 `{scan_id, status:"analyzing"}` (recompute). Errors: 400 unknown question/answer-shape, 409 round closed.

## 4. AI Analysis & Results

### POST /api/v1/ai/analyze — system (or farmer-trigger for queued scans)
`{scan_id}` → 200 `{quality:{score, category, reasons[], usable}, predictions:[{type, label_code, confidence, topk, ood_score, model:{name,version}}], diagnosis:{final_status, primary_label_code?, fused_confidence?, differential[], evidence_trace[]}, risk:{current, 3d, 7d, 14d, factors[]}, recommendation?|questions?}`.
- 422 `{code:"quality_unusable", reasons[]}` — no diagnosis produced (AC-01).
- 200 with `diagnosis.final_status="insufficient_evidence"` + `questions[]` is a **success** response (never an error).
- 503 `{code:"ai_unavailable"}` — scan stays `pending`, retried by worker.

### GET /api/v1/diagnoses/{scan_id} — owner roles
→ 200 full diagnosis + evidence trace + localized labels. 404/403 rules as scans.

## 5. Risk, Weather

### GET /api/v1/risk/{field_id}?horizon=3|7|14 — owner / extension / officer-district
→ 200 `{current:{score, category, factors[]}, outlook:[{horizon, score, category, trend}], weather_completeness, generated_at}`. 200 with `weather_completeness={temperature:false,…}` when weather missing (never imputed).

### GET /api/v1/weather/{field_id} — owner roles
→ 200 `{current:{temperature_c, humidity_pct, rainfall_mm, wind_kmph, observed_at, provider, age_hours}, forecast:[…], completeness}`; 200 `{status:"unavailable", fallback:"stale"|"climatology", age_hours}` when degraded.

## 6. GIS & Officer

### GET /api/v1/gis/heatmap?district=&threat=&from=&to= — officer / extension / expert
→ 200 `{cells:[{hex_id, center:{lat,lng}, intensity, source:"reported"|"predicted"|"verified"}]}` — **source dimension mandatory** (predicted ≠ reported ≠ verified).

### GET /api/v1/gis/hotspots?district=&status= — officer / extension
→ 200 `[{id, district, centroid, threat_type, threat_code, cluster_size, status, trend, first_seen_at, last_updated_at, recommended_intervention}]`.

### GET /api/v1/gis/hotspots/{id}/cases — officer
→ 200 `{cases:[{field_ref (pseudonymized), crop, risk, reports[], verification_status, last_update}]}`.

### GET /api/v1/officer/dashboard?district= — district_officer
→ 200 `{monitored_fields, active_alerts, high_risk_fields, disease_reports, pest_reports, pending_expert_cases, emerging_hotspots, map_layers}`.

## 7. Expert Workflow

### GET /api/v1/expert/cases?status=&urgency=&cursor= — expert (assigned/queued)
→ 200 `{items:[{case_id, scan_id, crop, image_url, ai:{label, confidence, topk}, farmer_answers[], weather, crop_stage, location:{district}, history_summary, queued_at}]}`.

### POST /api/v1/expert/review — expert
Request: `{diagnosis_id, verdict:"confirmed"|"corrected"|"rejected", corrected_label_code?, remarks?}` → 201 `{review_id, diagnosis_status}`. Errors: 403 not-assigned, 409 already-reviewed, 400 invalid verdict/correction pairing. Side effects: farmer notification; feedback row (dataset-ready); diagnosis final_status updated.

### POST /api/v1/scans/{id}/expert-request — farmer (own)
→ 202 `{case_id, queue_position_estimate}`.

## 8. Notifications, Feedback, Knowledge

### GET /api/v1/notifications?unread= — any (own) → 200; PATCH `/api/v1/notifications/{id}/read` → 204. GET `/api/v1/alerts?district=` (officer) / `/api/v1/alerts?field_id=` (farmer-own).

### POST /api/v1/feedback — any (own)
`{scan_id?, diagnosis_id?, rating:"useful"|"not_useful", comment?}` → 201. Used for retraining signals + UX metrics.

### GET /api/v1/knowledge/search?q=&crop=&threat= — expert/admin
→ 200 `{chunks:[{content, source{title, publisher, year, url}, score}]}` — RAG retrieval preview (transparency tool).

## 9. Admin

CRUD `/api/v1/admin/users` (role assignment, audited) · POST `/api/v1/admin/knowledge/ingest` (document upload + source metadata) · GET/PATCH `/api/v1/admin/models` (registry: status transitions shadow→active→retired, audited) · GET/PATCH `/api/v1/admin/config` (region/crop config, feature flags).

## 10. Health

GET `/api/v1/health` → 200 `{status:"ok"}` (public). GET `/api/v1/ready` → 200 `{db:true, models:true}` or 503 with component states.

## 11. Error Envelope & Codes

```
{ "code": "quality_unusable", "message_key": "errors.quality_unusable",
  "details": { "reasons": ["blurry","dark"], "quality_score": 31 } }
```

| Code | HTTP | Meaning |
|---|---|---|
| validation_error | 400 | Schema/field validation failure |
| unauthorized | 401 | Missing/expired token |
| forbidden | 403 | Role/ownership denial |
| not_found | 404 | Resource missing or out of scope |
| duplicate_scan | 409 | Idempotency conflict (returns original) |
| payload_too_large | 413 | >10 MB image |
| unsupported_media | 415 | Non-JPEG/PNG/WebP |
| quality_unusable | 422 | Quality gate rejected (retake guidance attached) |
| rate_limited | 429 | Too many requests |
| internal_error | 500 | Unexpected (logged, generic message) |
| ai_unavailable / weather_unavailable / db_unavailable | 503 | Dependency degradation (scan queued / risk flagged / retry) |

**Status-code discipline:** `insufficient_evidence` is 200 (a valid outcome, not an error); 4xx never leaks internals; 5xx always logged with request-id.
