# 06 · AI/ML Architecture

The AI layer is the core of FasalRakshak. Design stance: every model exists to remove a specific failure mode; all outputs are calibrated, versioned, and allowed to say **"Insufficient Evidence."** [PROPOSED DESIGN; SOURCE-DERIVED scope]

## 1. Inference Pipeline

```
Image (client-compressed)
  → M1 Quality Engine ........ gate: usable? (score, category, reasons)
  → M2 Crop/Leaf ID .......... supported crop? (wrong-crop guard)
  → M3 Disease Classifier .... top-k hypotheses + calibrated confidence
  → M4 Pest Detector ......... visible insects (YOLO) [P1]
  → Uncertainty Layer ........ calibration + OOD → sufficient / insufficient
  → Adaptive Questions ....... if insufficient (docs: question engine)
  → Context Fusion ........... + answers + weather + stage + location + history
  → Risk Engine .............. current + 3/7/14-day (docs/10)
  → Recommendation ........... RAG-grounded advisory (docs/11)
```

## 2. Model Portfolio

| Model | Task | Architecture (candidate) | Output | Priority |
|---|---|---|---|---|
| M1 Quality | Usability gate | Heuristics (Laplacian variance, histogram stats, EXIF) + tiny CNN leaf-coverage head | score 0–100, category, reasons, usable flag | P0 |
| M2 Crop ID | Wrong-crop guard | MobileNetV3-small / EfficientNet-Lite0 (10–20 crops) | crop label + confidence | P0 |
| M3 Disease | Per-crop classification | EfficientNet-Lite0 / MobileNetV3; transfer learning ImageNet → PlantVillage/PlantDoc → field data | top-k labels + calibrated probs + OOD score | P0 |
| M4 Pest | Visible insect detection | YOLOv8n/YOLO11n; classes: aphid, whitefly, caterpillar-family (extensible) | boxes + classes + confidences | P1 |
| M5 Risk | Learned risk (optional) | XGBoost on labeled outcomes | risk probability | P2/ADVANCED |

**WHY these choices:** small models are CPU-feasible (NFR: AI p95 < 4 s), transfer learning mitigates limited field data, per-crop heads keep class spaces small and interpretable. Alternatives rejected: large ViT/LLM-based classification (hardware + hallucination risk at MVP), classical CV only (insufficient accuracy on complex symptoms). Limitations: domain gap between lab datasets and field images — mitigated by quality gating, OOD detection, and field-data collection (docs/18).

## 3. Dataset Requirements

| Dataset | Purpose | Minimum targets (prototype) |
|---|---|---|
| Disease classification | M3 training | ≥300 usable images/class; MVP crops: tomato, potato, cotton |
| Crop ID | M2 training | ≥200 images/crop across stages |
| Pest detection | M4 training | ≥500 labeled instances/class |
| Quality | M1 calibration | ≥1,000 rated samples (Good/Acceptable/Poor/Unusable) |
| Risk features | M5 (future) | Labeled season outcomes per field |

**Sources:** PlantVillage (lab, pre-training only) · PlantDoc (field realism) · IP102 (pests) · team field captures (highest value; consent + expert-labeled) · expert-verified app cases (continuous). Raw data never committed to git; manifests only (docs/18).

## 4. Training Protocol

1. **Cleaning:** pHash dedupe; corruption scan; quality-gate filter (train on usable only); EXIF normalize; resize 224–320 px.
2. **Labeling:** label-studio instances; expert-verified ground truth; ambiguity flagged; labeling guide per crop (docs/18).
3. **Splits:** per-field/per-session stratified 70/15/15 — **never per-image** (prevents near-duplicate leakage).
4. **Augmentation:** h-flip, random crop, brightness/contrast jitter, mild blur — nothing that changes lesion morphology.
5. **Imbalance:** weighted cross-entropy + minority oversampling; per-class recall floor enforced.
6. **Optimization:** AdamW, cosine LR, early stopping on val macro-F1; two-stage (head → full, low LR).
7. **Calibration:** temperature scaling on val; report ECE; per-class thresholds chosen for documented precision/recall trade-offs.
8. **OOD:** energy score / max-softmax; threshold tuned on held-out out-of-scope images (other crops, soil, hands, non-leaf objects).
9. **Reproducibility:** fixed seeds; config-as-code; dataset manifest hash + model version + metrics → `model_registry`.
10. **Human gate:** no promotion to `active` without expert review of a confusion-matrix error sample.

## 5. Uncertainty, Unknowns & Safety

- **Calibration:** probabilities must mean what they say — temperature scaling, ECE reported, recalibrated after every retrain.
- **OOD/unknown:** high OOD score or low max-probability → state `insufficient_evidence`; system shows top-k as *hypotheses* only, asks questions, and flags expert review. **Never a forced label.** [SOURCE-DERIVED]
- **Visually similar diseases:** maintained as a differential; the fusion layer + questions resolve; the UI always shows top-k, not a single label.
- **Unseen diseases:** OOD routing; expert correction path feeds future data.
- **Regional variation:** per-region thresholds/config in model registry; knowledge-base rules carry region applicability metadata.
- **Model safety checklist (docs/34 of blueprint §15.3):** no accuracy claims without held-out evaluation; dataset vs field performance reported separately; poor-quality images lower the confidence ceiling; weather absence down-weights weather factors (never imputes).

## 6. Explainability

- **Grad-CAM/attention overlays** on the top hypothesis **[P2]** — stored as image artifacts linked to `ai_predictions.explainability_ref`.
- **Evidence bullets:** textual "why" — detected symptom descriptors (lesion color/margin/distribution from labeling descriptors), matched answer-based evidence, context factors.
- **Evidence trace in fusion:** which input moved which hypothesis, in which direction — rendered in expert/officer UIs.

## 7. Model Versioning & Monitoring

- `model_registry`: name, version, artifact URI + SHA, thresholds, metrics, status (shadow/active/retired), activation date. Every `ai_predictions` row references the exact version used.
- **Shadow mode:** new versions run shadow inference on live traffic; promotion requires metric parity + expert spot-check.
- **Monitoring:** confidence-distribution drift, OOD firing rate, quality-rejection rate, expert disagreement rate per class, latency. Alerts on drift beyond documented bounds.

## 8. Inference Service Design

- Single entrypoint `ai/inference.py` (scan_id → full result), called by Scan API via an in-process interface; extraction into a standalone `ai-service` container is a documented path **[ADVANCED]** — API code does not change.
- CPU-first: ONNX Runtime execution; bounded worker pool; per-stage timeouts; graceful degradation (if disease model unavailable → quality + questions still function, scan marked `pending_ai`).
- Warm-up at startup; models loaded once; artifact checksum verified on boot.

## 9. Honesty Rules (binding)

1. No accuracy claims without held-out evaluation recorded in docs/17.
2. "Unknown / Insufficient Evidence" is a first-class output.
3. Dataset performance ≠ field performance; both reported separately when available.
4. No fabricated datasets, papers, or results — ever.
