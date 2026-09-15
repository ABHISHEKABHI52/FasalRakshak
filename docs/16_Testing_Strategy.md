# 16 · Testing Strategy

Layered, CI-gated, honest-uncertainty tested explicitly. [PROPOSED DESIGN]

## 1. Test Pyramid & Ownership

| Layer | Scope | Tools | Gate | Owner |
|---|---|---|---|---|
| Unit | risk math, fusion updates, question selection (IG), validators, quality heuristics, i18n keys | pytest, vitest | PR | Backend/AI/FE devs |
| Contract/API | auth matrix (RBAC per docs/03), validation, status codes, idempotency, error envelope | pytest + httpx against app | PR | Backend |
| Integration | scan→quality→predict→risk→advisory on seeded DB; weather fixtures; outbox sync | pytest + Postgres service | PR | Backend |
| AI eval | frozen eval set; thresholds: macro-F1 floor per class, ECE ceiling, OOD recall; quality-gate cases | pytest + eval scripts | PR (small set) + scheduled (full) | AI/ML |
| Frontend unit | compression, outbox, forms, offline UI states | vitest | PR | Frontend |
| E2E | farmer scan incl. Q&A loop; expert verdict; officer map; offline sync | Playwright | nightly + pre-demo | FE+BE |
| Security | IDOR suite, auth bypass, upload fuzz, rate limits, headers | scripted pytest | nightly | Backend |
| Load | 50 concurrent scans; p95 budgets (non-AI <500 ms; AI <4 s) | k6 | pre-release | Backend |
| UAT | 3–5 farmers + 1 expert comprehension checklist | manual | pre-pilot | UX+team |

## 2. Critical Test Scenarios (must-pass)

1. Blurred image → 422 + retake reasons, **no diagnosis row** (AC-01).
2. Good image, confident → diagnosis + risk + cited advisory (AC-02).
3. Confidence 0.55 → questions returned (200, not error) → answers → recomputed result (AC-03).
4. Weather down → risk flags `weather unknown`, factors reweighted (AC-04).
5. Expert correction → review row with frozen original + model version; export yields training record (AC-05).
6. Duplicate `client_scan_uuid` → original returned, no dup row.
7. Offline capture → outbox persists across app restart → syncs once (no dup).
8. Farmer requests another farmer's scan → 404.
9. `.exe` renamed `.jpg` → rejected by magic bytes.
10. 10.5 MB upload → 413.

## 3. Test Data Management

- Seed script: 2 demo farmers, 1 expert, 1 officer, farms/fields (fixed coords), labeled demo images per state (usable/blurry/dark/non-leaf), one insufficient-evidence case, one verified hotspot cluster. All demo data labeled "DEMO" in notes.
- Fixtures: recorded weather responses (normal/stale/failing), model outputs frozen per version for regression.
- Eval sets versioned with manifests (docs/18); never train on eval fields.

## 4. CI Gates (definition of done)

PR merge: lint + typecheck + unit + contract + small AI-eval green; nightly: E2E + security + full AI-eval; pre-demo: load + UAT checklist + demo-rehearsal pass.

## 5. Bug Triage & Quality Bars

Sev1 (farmer-facing crash/data loss/wrong-diagnosis-without-uncertainty) → fix before demo; Sev2 (feature broken, workaround exists) → fix in sprint; Sev3 (polish) → backlog. Coverage target: ≥70% backend core services; 100% of risk-engine rule paths unit-tested.
