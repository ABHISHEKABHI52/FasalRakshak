# 19 · Future Roadmap

Phases marked honestly: IMPLEMENTED (none yet) / MVP / SIH DEMO / ADVANCED / FUTURE.

| Phase | Scope | Status label |
|---|---|---|
| **Phase 1 — MVP** (weeks 1–6) | scan→quality→diagnosis→risk→advisory loop; weather; history; basic officer dashboard/map; en/hi/Hinglish | MVP |
| **Phase 2 — SIH prototype** (by national demo) | pest YOLO; expert console; hotspots + drill-down; offline queue; feedback export; Grad-CAM; web push | SIH DEMO |
| **Phase 3 — Field validation** (post-SIH, 3–6 months) | pilots on real farms; comprehension studies; calibration review; dataset growth; risk-weight tuning | ADVANCED (process) |
| **Phase 4 — District pilot** | officer workflows live; expert network onboarding; regional config; M5 XGBoost risk | ADVANCED |
| **Phase 5 — State deployment** | scale-out; more crops/languages; department integration prep | FUTURE-leaning |
| **Future backlog** | IoT/soil sensors; pest-trap pipeline; satellite/drone; edge AI; SMS/IVR; advanced regional forecasting; government surveillance integrations (NPSS-style) | FUTURE FEATURE |

## Priority Matrix (P0–P3)

| Priority | Meaning | Examples |
|---|---|---|
| P0 | Absolutely required | auth, fields, scan, quality gate, disease AI + confidence, questions, risk, advisory, weather, i18n |
| P1 | Important | history, alerts, expert validation, officer dashboard full, offline queue, GIS clustering |
| P2 | SIH enhancement | Grad-CAM, web push, reports export, admin console, knowledge search |
| P3 | Future | IoT, traps, satellite, edge AI, SMS/IVR, XGBoost risk, gov integrations |

## Week-by-Week Development Roadmap (small student team, 8 weeks)

| Week | Focus | Deliverables |
|---|---|---|
| 1 | Foundations | repo, compose stack, DB schema + migrations, auth/RBAC, CI green |
| 2 | Core backend | scans API, quality engine, crop-ID + disease classifier v0 (public data), model registry |
| 3 | Intelligence loop | uncertainty/OOD, question engine v1, fusion, risk engine v1 (rules), advisory templates (en) |
| 4 | Farmer MVP UI | scan wizard, result, questions, risk, history, i18n (en/hi), error states |
| 5 | Context & safety | weather service + fallback, expert queue + verdict flow, feedback store, security suite |
| 6 | SIH features | officer dashboard + GIS map + hotspots, offline queue, pest detector demo, push |
| 7 | Hardening | E2E + load + security tests, seed/demo script, observability, docs freeze |
| 8 | Demo prep | full story rehearsal (3/5/10-min), backup video, judge FAQ dry-run, pilot checklist |

(If only 6 weeks available: merge weeks 2–3 and 6–7 — never cut week 7–8 hardening.)
