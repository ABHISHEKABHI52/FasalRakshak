# 18 · Data Strategy

How FasalRakshak acquires, cleans, labels, versions and learns from data — with honest separation of dataset vs field performance. [PROPOSED DESIGN; SOURCE-DERIVED discipline rules]

## 1. Data Inventory & Sources

| Data | Source | Use | Access mode |
|---|---|---|---|
| Disease leaf images | PlantVillage (public, lab conditions) | M3 pre-training | download; **lab≠field** |
| Field disease images | PlantDoc (public) + team captures | M3 fine-tune/eval | download + consented collection |
| Pest images | IP102-class public sets | M4 training | download; class remap to Indian priority pests |
| Crop/leaf ID images | public sets + captures | M2 | mixed |
| Quality-rated images | team-rated samples + gate outcomes | M1 calibration | internal |
| Weather history | public/free APIs (IMD-sourced where accessible) | risk features, backtests | API |
| Expert labels | agronomy students/KVK/expert partners | ground truth | partnership (start early — docs/00 §50) |
| Production cases | expert_reviews export | continuous learning | consent-gated |
| Knowledge text | ICAR/state/govt public documents | RAG corpus | curation |
| Geo observations | app events | GIS/hotspots | operational |

## 2. Collection Ethics & Consent

Field capture only with informed consent (localized script); `consent_ml_use` flag controls training eligibility; images anonymized at export (no names/phones); GPS bucketed to region for datasets; collection log records date/place/crop/stage/photographer-role.

## 3. Cleaning Pipeline

1. Ingest → checksum/dedupe (pHash + SHA-256). 2. Corruption/decode check. 3. Quality gate (M1-style heuristics) — usable only for training. 4. EXIF normalize; resize policy. 5. Duplicate-cluster review (near-dupes across splits = leakage risk). 6. Quarantine bucket for ambiguous samples.

## 4. Labeling Protocol

- Labeling guide per crop: symptom descriptors (lesion color, margin, distribution, stage) — matching AgriChain-style standardized descriptors [EXTERNAL RESEARCH R2].
- Tool: label-studio; two-pass (annotator + expert reviewer); disagreements adjudicated; ambiguity flag retained (useful for OOD research).
- Class registry: canonical disease/pest codes (docs/07) with per-locale names — single source of truth.

## 5. Splits & Leakage Prevention

**Per-field / per-session splitting** (images from the same plant/session never straddle splits); stratified by class; test set frozen at v1 and only extended (never re-sampled) — evaluation comparability across model versions.

## 6. Class Balance

Per-class counts published with each manifest; weighted loss + oversampling; classes below floor (e.g., <100 usable images) marked **data-poor** → excluded from MVP classifier (better an honest smaller class set than an unreliable big one).

## 7. Versioning

Dataset manifests (JSON): sources, versions, checksums, split hash, labeling-guide version, consent filter, counts. Style: DVC-compatible; manifests in git, data out. Model↔dataset lineage enforced in `model_registry` (model records its dataset manifest hash).

## 8. Dataset vs Field Performance (binding rule [SOURCE-DERIVED])

- **Dataset performance:** metrics on curated test sets — reported with full protocol.
- **Field performance:** only from prospective use (pilot scans judged by experts) — reported with sample size and confidence intervals, never extrapolated from benchmarks.
- Any public claim must state which of the two it is. Marketing-style single numbers prohibited (docs/17 §4).
