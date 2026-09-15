# 03 · Product Requirements

Status: [PROPOSED DESIGN] unless tagged otherwise. Priorities: **P0** required (MVP) · **P1** important · **P2** SIH enhancement · **P3** future.

## 1. Functional Requirements

### FR-A · Identity & Access (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-A1 | Registration (phone-first) + password login; JWT access+refresh tokens | P0 |
| FR-A2 | Role-based access: farmer, extension worker, expert, district officer, admin | P0 |
| FR-A3 | Farmer profile: name, preferred language, district/state, contact | P0 |
| FR-A4 | Expert/officer/admin accounts via admin console or verified signup | P1 |

### FR-B · Farm, Field & Crop (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-B1 | Create/edit/archive farms (name, address, district) | P0 |
| FR-B2 | Register fields with GPS point (auto-capture) or manual map pin + area | P0 |
| FR-B3 | Crop selection from catalogue (MVP: tomato, potato, cotton) | P0 |
| FR-B4 | Crop cycle with sowing date → derived crop stage | P0 |
| FR-B5 | Multiple fields per farm; multiple cycles per field; field status | P0 |

### FR-C · Crop Scan (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-C1 | Capture (camera/gallery); select field + cycle + plant part | P0 |
| FR-C2 | Client-side compression (≤1024 px, JPEG q≈0.8) before upload | P0 |
| FR-C3 | Duplicate-scan guard (idempotency + cooldown per field) | P1 |
| FR-C4 | Offline queueing with retry/backoff sync | P1 |

### FR-D · AI Analysis (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-D1 | Image quality: score 0–100, category Good/Acceptable/Poor/Unusable + actionable retake reasons | P0 |
| FR-D2 | Crop/leaf identification gate ("not a supported crop leaf" state) | P0 |
| FR-D3 | Per-crop disease classification with top-k hypotheses | P0 |
| FR-D4 | Pest detection (aphid/whitefly/caterpillar family) | P1 |
| FR-D5 | Calibrated confidence + explicit Unknown/Insufficient-Evidence state | P0 |
| FR-D6 | Explainability: Grad-CAM overlay + textual evidence bullets | P2 |
| FR-D7 | Model version recorded with every prediction | P0 |

### FR-E · Adaptive Questioning (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-E1 | Question bank tagged by crop, symptom, stage, context-need | P0 |
| FR-E2 | Policy: high confidence → diagnose; medium/low → targeted questions | P0 |
| FR-E3 | Max 3–5 questions/round; skip already-known info (e.g., weather) | P0 |
| FR-E4 | Answers stored; diagnosis and risk recomputed after answers | P0 |

### FR-F · Risk (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-F1 | Current risk: Low/Medium/High/Critical + numeric score | P0 |
| FR-F2 | 3/7/14-day outlook with trend | P0 |
| FR-F3 | Named risk factors in plain language | P0 |
| FR-F4 | Escalation recommendation (monitor / act / contact expert / alert officer) | P0 |

### FR-G · Advisory (P0)
| ID | Requirement | Priority |
|---|---|---|
| FR-G1 | Recommendations assembled only from retrieved knowledge chunks (RAG) | P0 |
| FR-G2 | Every recommendation shows source title, publisher, safety note | P0 |
| FR-G3 | IPM-first; no automatic pesticide prescription | P0 |
| FR-G4 | Multilingual: en/hi/Hinglish; localized disease names | P0 |
| FR-G5 | Farmer-friendly: 3–5 numbered steps, icons, large text | P0 |

## 2. Roles & Permissions Matrix

Legend: **C**reate **R**ead **U**pdate **D**elete · `Own` = own records · `Dist.` = district scope · `–` = none.

| Resource | Farmer | Ext. Worker | Expert | Dist. Officer | Admin |
|---|---|---|---|---|---|
| Own profile | CRU | CRU | CRU | CRU | CRUD |
| Users (all) | – | – | – | R (Dist.) | CRUD |
| Farms/fields | CRUD (Own) | CRU (assisted) | R (case-linked) | R (Dist.) | CRUD |
| Crop cycles | CRUD (Own) | CRU (assisted) | R | R (Dist.) | CRUD |
| Scans | CR + R (Own) | CR (assisted) | R (assigned) | R (Dist.) | R |
| AI predictions | R (Own) | R | R (assigned) | R (Dist., agg.) | R |
| Adaptive answers | CRU (Own, pre-submit) | CRU (assisted) | R | R (Dist.) | R |
| Risk predictions | R (Own) | R | R (assigned) | R (Dist.) | R |
| Recommendations | R (Own) | R | R | R (Dist.) | R |
| Weather (field) | R (Own) | R | R | R (Dist.) | R |
| GIS heatmap (agg.) | – | R (Dist.) | R (Dist.) | R (Dist.) | R |
| GIS identity-annotated map | – | – | – | R (audited) | R |
| Disease/pest reports | CR (Own) | CR | CRU (verified) | CRUD (Dist.) | CRUD |
| Expert review queue | – | – | R/U (assigned) | R (Dist. status) | R |
| Officer dashboard | – | – | – | R (Dist.) | R |
| Knowledge base | – | R | R | R | CRUD |
| Model registry | – | – | – | – | CRUD |
| Notifications/alerts | R (Own) | R (Own) | R (Own) | R (Dist.) | R |
| Feedback | CR (Own) | CR (Own) | CRU (Own) | R (Dist.) | CRUD |
| Audit logs | – | – | – | – | R |

**Security restrictions:** farmers can never list/read other farmers' data (row-level scoping in backend); officers see aggregates by default — identity-annotated access is a separate audited permission; experts see only assigned/queued cases; per-role JWT scopes; all admin actions audit-logged.

### FR-H · Alerts & Notifications (P1)
| ID | Requirement | Priority |
|---|---|---|
| FR-H1 | Severities LOW/MEDIUM/HIGH/CRITICAL with owner routing | P1 |
| FR-H2 | Channels: in-app (MVP), web-push (P2), SMS adapter stub (P3) | P1 |
| FR-H3 | Anti-spam: dedupe key, per-field cooldown, severity throttling, digests | P1 |

### FR-I · History & Monitoring (P1)
Scan history per field; field timeline; follow-up scan reminders; case history export (P2).

### FR-J · Expert Validation (P1)
Expert queue with filters; case detail (image, AI prediction, confidence, answers, weather, stage, location, history); confirm/correct/reject + remarks; feedback stored dataset-ready; farmer notified of validated result.

### FR-K · Officer Dashboard (P1)
District overview cards; GIS map with heatmap; hotspot drill-down; case lists; inspection notes; intervention tracking; CSV/PDF export (P2).

### FR-L · GIS Intelligence (P1)
Field locations; layered reporting (farmer-reported vs AI-predicted vs expert-verified); hex-grid heatmap; DBSCAN hotspot candidates from reported/verified cases only; district aggregation.

### FR-M · Weather (P0)
Current + short-range forecast per field (temp, humidity, rainfall, wind); caching + fallback chain; validation/clamping; missing-data flags surfaced in risk — never silently imputed.

### FR-N · Multilingual (P0)
UI strings externalized; AI-output templates localized; agri terminology glossary; Hinglish transliteration layer; data-driven extensibility.

### FR-O · Offline & Low Connectivity (P1)
Installable PWA; app shell + last advisories cached; IndexedDB outbox for scans/forms; background sync; progressive upload.

### FR-P · Feedback (P1)
Farmer useful/not-useful + comments; expert corrections; linked to scan/prediction; dataset-export tagging.

### FR-Q · Admin (P2)
User management; knowledge ingestion with source metadata; model registry view; region/crop config; feature flags.

## 3. MVP Acceptance Criteria (Given/When/Then)

- **AC-01** Given a blurred leaf photo, When submitted, Then the system replies "Unusable image — please retake" with a specific reason and produces **no** diagnosis.
- **AC-02** Given a clear tomato leaf with characteristic symptoms, When analyzed, Then the farmer sees top hypothesis + confidence % + "why we think so" + current risk + 3 next steps + source citation.
- **AC-03** Given confidence below threshold, When analysis completes, Then 3–5 targeted questions are asked; after answering, updated diagnosis and risk are recomputed and shown.
- **AC-04** Given weather data unavailable, When risk is computed, Then the risk explicitly states "weather unknown" and its confidence is reduced — never silent imputation.
- **AC-05** Given an expert corrects a diagnosis, When saved, Then the correction is stored with model version and is exportable as a training record.
- **AC-06** Given a reported+verified cluster in a district, When the officer opens the map, Then a hotspot candidate is highlighted distinctly from AI-predicted risk zones.
- **AC-07** Given no network, When the farmer completes a scan, Then it is stored on-device and auto-syncs on reconnect without data loss or duplicates.
- **AC-08** Given any API/model failure, When the UI renders, Then a localized, actionable message appears — the UI never crashes.

## 4. Non-Functional Requirements

Summary (full targets: docs/00 §8): performance p95 non-AI <500 ms, AI p95 <4 s CPU; district-pilot scale (10k scans/month single node); ≥99% availability during pilot; security per docs/12; privacy by data minimization; maintainability ≥70% core coverage; WCAG 2.1 AA targets; en/hi/Hinglish; explainability mandatory; structured logging mandatory, Prometheus optional.

## 5. Requirement Traceability

| Brief element | Where satisfied |
|---|---|
| Multimodal inputs (image, weather, soil/IoT, GIS) | FR-C/D/M/L (+ soil/IoT [FUTURE]) |
| Adaptive questioning | FR-E |
| 3/7/14-day prediction | FR-F |
| GIS hotspot mapping | FR-L |
| Farmer-ready IPM recommendations | FR-G |
| Expert/lab referral + human-in-the-loop | FR-J (+ lab referral [FUTURE]) |
| Multilingual advisory | FR-N |
| SIH26131 early detection & management | Whole product; success = docs/01 §6 |
