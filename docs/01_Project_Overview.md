# 01 · Project Overview

| Field | Value |
|---|---|
| Product | **FasalRakshak** |
| Tagline | Scan. Predict. Protect. |
| Category | AI-Powered Crop Health, Disease Detection & Early Warning Platform |
| Problem Statement | SIH26131 — Early detection and management of crop diseases and pest infestations **[SOURCE-DERIVED]** |
| Theme | Agriculture, FoodTech & Rural Development |
| Category | Software |
| Phase | Architecture & Documentation (v1.0) |

> ⚠️ The original concept PDF was not in the repository at authoring time; this overview is aligned to the approved written brief. Source tags: `[SOURCE-DERIVED]`, `[ARCHITECT INFERENCE]`, `[PROPOSED DESIGN]`, `[FUTURE FEATURE]`.

## 1. What FasalRakshak IS

An agricultural **decision-support and early-warning platform** [SOURCE-DERIVED] that:

1. **Scans** — farmer captures a crop/leaf/pest-trap image; a quality gate rejects unusable photos *before* AI runs.
2. **Analyzes** — vision models produce crop ID, disease candidates, pest detections, each with calibrated confidence and an explicit **Unknown / Insufficient Evidence** state.
3. **Inquires** — when evidence is insufficient, an adaptive question engine asks a *small, targeted* set of questions (Chain-of-Inquiry inspired **[SOURCE-DERIVED]**, External Research R1).
4. **Fuses** — visual evidence + answers + weather + crop stage + location + field history → context-aware diagnosis.
5. **Predicts** — a transparent risk engine outputs current, 3-day, 7-day and 14-day risk with the factors that drive it.
6. **Advises** — RAG-grounded recommendations from ICAR/state/IPM sources, with citations, in English/Hindi/Hinglish.
7. **Protects** — alerts, expert escalation, GIS surveillance for officers, and a feedback loop that turns confirmed cases into better future intelligence.

## 2. What FasalRakshak is NOT

| It is NOT | Because |
|---|---|
| A single-image "disease name" app | Real fields need confidence, context, risk and action — not labels |
| A pesticide prescription engine | It recommends IPM steps and routes chemical decisions to verified guidance + experts |
| An outbreak confirmation system | It distinguishes **AI-predicted risk** vs **farmer-reported case** vs **expert-verified case** |
| A fully autonomous diagnosis system | Human-in-the-loop validation is a core feature, not an afterthought |

## 3. The Three Answers

1. **Diagnosis Confidence** — calibrated model certainty, including "insufficient evidence".
2. **Disease/Pest Risk** — evidence + weather + crop stage + history → Low/Medium/High/Critical, with drivers.
3. **Escalation Risk (3/7/14 days)** — forecast of how the situation may evolve and whether to escalate.

These are deliberately separated; a high-confidence diagnosis of a minor issue can be Low-risk, and a low-confidence sighting under highly favorable weather can be High-risk. See `docs/10_Risk_Engine.md`.

## 4. Module Summary

- **A. Farmer Application** — scan, quality gate, AI analysis, adaptive questions, risk, advisory, alerts, history, expert request. *(MVP)*
- **B. AI Intelligence Layer** — crop ID, disease classification, pest detection, quality, confidence/OOD, questions, fusion, explainability, guardrails. *(MVP; pest detection SIH demo)*
- **C. Risk Intelligence Engine** — current + 3/7/14-day risk, drivers, escalation. *(MVP)*
- **D. GIS Intelligence** — field map, heatmaps, hotspots, clusters, officer map. *(basic MVP, full SIH demo)*
- **E. Expert Validation Layer** — queue, confirm/correct/remarks, feedback. *(SIH demo)*
- **F. Officer Dashboard** — district overview, alerts, hotspots, inspections, interventions. *(SIH demo)*

## 5. Priority Classification (summary)

- **MVP (P0):** auth, farms/fields/crops, scan + quality gate, disease classification + confidence, adaptive questions, risk score, recommendation, scan history, basic weather, basic officer dashboard, basic GIS map, multilingual (en/hi/Hinglish).
- **SIH DEMO (P1/P2):** pest detection (YOLO), expert validation console, hotspot clustering, officer full workflow, offline queue demo, feedback loop, explainability (Grad-CAM), notifications.
- **ADVANCED/FUTURE (P3):** XGBoost learned risk on historical data, pest-trap image pipeline, IoT/soil sensor ingestion, satellite/drone imagery, regional forecasting, edge AI, SMS/IVR, more languages, government integrations (e.g., NPSS-style feeds **[FUTURE FEATURE]**).

## 6. Prototype Success Criteria

1. A farmer can complete a scan → diagnosis/risk/advisory loop on a mid-range Android over a weak network.
2. The system demonstrably returns **"Insufficient Evidence"** and asks better questions instead of guessing (the SIH demo centerpiece).
3. Risk changes visibly when context changes (e.g., humidity/rainfall raise 7-day risk).
4. Expert corrections are stored in a form that is directly trainable on (dataset-ready export).
5. Officer dashboard distinguishes predicted vs reported vs verified cases on a GIS map.
6. Every advisory shows its sources and safety notes.

## 7. Key Assumptions

- Field data collection during the hackathon window is limited; model accuracy claims come only from held-out evaluation on collected datasets (docs/17, docs/18). **Dataset performance ≠ real-world field performance.**
- MVP crops: tomato, potato, cotton (public-dataset coverage + team access); expandable.
- Government knowledge content is ingested only from publicly available official material with source metadata.
- Weather uses free-tier public APIs with caching and graceful degradation.
