
## 9. Threat Model (STRIDE-lite)

| Threat | Vector | Mitigation |
|---|---|---|
| Spoofing | Stolen tokens, credential stuffing | Short access TTL, refresh rotation + reuse detection, Argon2id, rate limits, generic errors |
| Tampering | Malicious image uploads, IDOR writes | Magic-byte + re-encode, ownership checks on every mutation, audit logs |
| Repudiation | Disputed verdicts/admin changes | Append-only audit_logs, expert verdicts frozen copies |
| Information disclosure | IDOR, over-broad officer views, verbose errors | Row-level scoping, aggregates by default, 404-not-403, generic errors |
| Denial of service | Upload floods, AI hammering | Rate limits, body caps, queue backpressure, per-stage timeouts |
| Elevation of privilege | Role tampering via API | Role changes admin-only + audited; JWT scopes checked server-side |

## 10. Dependency & Supply Chain

Pinned dependencies; `pip-audit` / `npm audit` in CI; base images pinned by digest; SBOM generation **[P2]**; model artifacts checksummed; knowledge documents checksummed at ingestion.

## 11. Security Testing & Checklist (CI-gated)

Auth-bypass suite · IDOR suite on every `/id` route · upload fuzzing (polyglot files, oversized, EXIF-laden) · rate-limit verification · header verification · secrets scan · dependency audit. OWASP ASVS-lite checklist reviewed before pilot; pen-test **[FUTURE FEATURE]**.

## 12. Incident Response (prototype-grade)

Log-based detection (5xx spikes, auth-failure bursts, unusual export volume) → on-call rotation (team) → documented runbook: contain (disable feature flag/revoke tokens), assess (audit log), notify (admin/officer as appropriate), patch, postmortem. Backups enable restore (docs/15).

---

# 13 · User Flows

Step-by-step flows for the seven canonical data flows. Statuses: all flows assume MVP unless tagged.

## Flow A — Farmer Crop Scan (happy path)

1. Farmer opens PWA → Dashboard → **New Scan**.
2. Selects field → crop cycle (stage auto-derived) → plant part.
3. Captures image → client compresses (≤1024 px, q≈0.8) → pHash computed.
4. `POST /scans` (idempotency key) → 201 `pending_image` → upload → 202 `analyzing`.
5. Backend: quality gate → (usable) → crop-ID gate → disease classifier → uncertainty layer.
6. Sufficient → `diagnosed`: persist prediction/diagnosis/risk/recommendation → 200 result.
7. UI renders: hypothesis + confidence + why + current risk + 3/7/14 outlook + advisory (cited, localized).
8. Optional: farmer taps "Ask an expert" **[SIH DEMO]**; feedback thumbs captured.

## Flow B — Low-Confidence Diagnosis (the differentiator)

1. Steps A.1–5 identical; uncertainty layer returns `insufficient_evidence` (e.g., top confidence 0.55, OOD moderate).
2. Response 200: `diagnosis.final_status="insufficient_evidence"`, `questions[]` (3–5, information-gain ranked, weather-known items skipped).
3. UI renders hypotheses as *possibilities* + questions (localized, icons, single-tap answers).
4. `POST /scans/{id}/answers` → 202 recompute.
5. Fusion updates posterior from answer evidence updates (rule-based, transparent).
6. Outcome a: confidence crosses threshold → `diagnosed` (Flow A.6–8 resumes).
7. Outcome b: still uncertain → confidence capped, `referred_expert` flagged; farmer told "expert verification recommended"; risk still computed conservatively.

## Flow C — High-Risk Alert

1. Risk engine outputs High/Critical (current or outlook).
2. Alert service creates `alerts` row — dedupe key `field:threat:window` prevents spam; severity mapped (HIGH/CRITICAL).
3. Farmer: in-app notification (+ web push **[P2]**); advisory re-emphasized; escalation recommendation shown.
4. Officer: district counters +, hotspot candidate pipeline sees the event.
5. Officer ack/throttle rules: cooldown 24 h per field+threat unless severity escalates.

## Flow D — Expert Validation **[SIH DEMO]**

1. Case enters expert queue (auto: insufficient-evidence/High-risk; manual: farmer request).
2. Expert opens case: image + quality data + AI prediction (top-k, confidence, model version) + farmer answers + weather/stage + district + history summary.
3. Verdict: **Confirm** | **Correct** (pick actual label) | **Reject** (+reason) | remarks.
4. `expert_reviews` row: verdict, original_prediction (frozen JSON incl. model version + confidence), corrected label, remarks, reviewed_at.
5. Diagnosis `final_status` → expert_confirmed / expert_corrected / rejected; farmer notified with updated advisory.
6. Feedback row tagged dataset-ready → Flow G.

## Flow E — GIS Hotspot Creation **[SIH DEMO]**

1. Trigger: new verified/reported report (job runs on-write + nightly).
2. Aggregate last-N-day reported+verified points for district.
3. DBSCAN (eps ~3–5 km config, minPts ~3) → clusters + noise.
4. Cluster ≥ criteria → `gis_hotspots` candidate (centroid, size, threat, trend) or update existing (trend recompute).
5. Officer alert: "New hotspot candidate in {district} — {threat}" (dedupe by hotspot id + day).
6. Map layers refresh (heatmap materialization + hotspot layer). **Predicted-risk layers remain separate.**

## Flow F — Officer Response **[SIH DEMO]**

1. Officer opens dashboard → sees hotspot on map (pulsing) → clicks → popup (crop, threat, count, risk, trend, last update, verification status, recommended intervention).
2. "View cases" → drill-down list (pseudonymized fields) → opens case detail.
3. Actions: mark **inspection** (visit logged → `field_observations`, officer_inspection) | broadcast **advisory** (targeted farmer alerts, deduped) | **dismiss** hotspot (reason recorded) | escalate **[FUTURE]**.
4. Dashboard + hotspot status/trend update; audit log row per action.

## Flow G — Feedback → Future Model Improvement **[SIH DEMO]**

1. Sources accumulate: expert verdicts (original vs corrected), farmer ratings, quality-gate outcomes, OOD confirmations.
2. Export job (manual trigger at MVP): builds **versioned dataset manifest** — images (paths), labels (final + original), splits, context snapshot, consent filter (`consent_ml_use`), anonymization applied.
3. Weak-class report: per-class expert-correction rates highlight model weaknesses.
4. ML engineer retrains candidate → shadow mode → metrics + expert spot-check → promotion via model registry (audited).
5. Loop closure metric: expert-agreement rate trend per release (docs/17).

## Flow H — Offline Scan Sync **[SIH DEMO]**

1. No network detected → UI badge "offline mode".
2. Scan captured normally → stored in IndexedDB outbox with idempotency key → status "saved on phone".
3. Reconnect → background sync pushes outbox sequentially → server idempotency prevents duplicates → UI flips to synced.
4. Analysis results arrive via notification/refresh.

## Cross-Flow Invariants

- Every AI artifact persists model version + thresholds (reproducibility).
- No flow ever *forces* a diagnosis — insufficiency is a legal terminal state pending questions/expert.
- Predicted ≠ reported ≠ verified distinction preserved end-to-end (DB → API → UI labels).
- All destructive/identity actions audited.
