
# 17 · Model Evaluation

Metrics per model + system + user levels. [PROPOSED DESIGN; measured, never claimed]

## 1. Per-Model Metric Sets

| Model | Primary metrics | Secondary | Failure modes watched |
|---|---|---|---|
| M1 Quality | rejection precision/recall, Cohen's kappa vs human ratings | latency (<300 ms) | over-rejection of usable photos |
| M2 Crop ID | top-1 accuracy | wrong-crop-pass-through rate (target ~0) | look-alike crops |
| M3 Disease | per-class P/R/F1, macro-F1, confusion matrix, ROC-AUC per class | ECE (calibration), OOD recall / FP rate | visually similar classes; lab-field gap |
| M4 Pest | mAP@50, per-class P/R | FP boxes/image | tiny pests; similar insects |
| M5 Risk [ADV] | MAE/RMSE vs outcomes; event P/R (HIGH+) | calibration curve | threshold gaming |

## 2. System-Level Metrics

API p95 latency by endpoint class · AI pipeline p95 (quality <300 ms; full analyze <4 s CPU) · failure rate · uptime · image-processing time · queue depth/outbox sync lag · weather cache hit rate.

## 3. User-Level Metrics

Task completion rate (scan→result) · advisory comprehension (UAT checklist: can farmer state what to do next?) · expert agreement rate (AI vs expert verdicts) · correction rate by class · question-answer completion rate · notification action rate.

## 4. Evaluation Protocol

- **Frozen eval sets:** versioned manifests; per-field splits (docs/18); never used in training.
- **Baseline first:** publish baseline numbers (public-dataset training only) before field-data fine-tuning — showing the gap is part of our honesty.
- **Reporting format:** dataset name + version + split hash + date + per-class table + calibration plot + OOD stats; macro-F1 headline (imbalance-honest).
- **No cherry-picking:** single-number marketing claims prohibited; any published metric links its eval manifest.
- **Regression gates:** new model must beat incumbent on macro-F1 **and** not degrade any class recall below documented floor; else stays shadow.
- **Risk engine eval:** backtest vs expert outcomes; weight-review cadence documented (docs/10 §8).
- **RAG eval:** retrieval hit-rate on curated query→chunk set; citation-integrity check (every advisory step maps to a source).

## 5. Current Status (honesty section)

IMPLEMENTED: none yet — architecture phase. First baseline evaluation is a Phase-1 deliverable (docs/00 §48). Until then, no accuracy numbers exist for FasalRakshak models — and none will be claimed without this protocol.
