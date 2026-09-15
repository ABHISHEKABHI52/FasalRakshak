# 20 · SIH Demo Strategy

Goal: demonstrate the full intelligence loop in one coherent story, robust to stage conditions. [PROPOSED DESIGN; SOURCE-DERIVED story]

## 1. The Demo Story (single narrative)

Farmer notices abnormal symptoms → opens FasalRakshak → selects crop → uploads image → quality evaluated → AI detects a possible problem → **confidence insufficient** → targeted questions → answers → weather/context fused → risk changes → 7-day risk → actionable advisory (Hindi, cited) → case appears on GIS map → officer dashboard shows emerging hotspot → expert validates a case → feedback enters the system.

## 2. 3-Minute Version (judges' attention window)

| Time | Beat | Show |
|---|---|---|
| 0:00–0:20 | Hook + problem | One slide: SIH26131 + "Evidence > Guess" |
| 0:20–0:50 | Scan + quality gate | Rejected blurry image (retake guidance) → good image |
| 0:50–1:40 | The differentiator | Insufficient evidence → 2 questions → fused diagnosis; risk changes 0.55→0.87 |
| 1:40–2:20 | Risk + advisory | 3/7/14 outlook; Hindi advisory with sources |
| 2:20–2:50 | Ecosystem | Officer map hotspot + expert confirms one case |
| 2:50–3:00 | Close | "Scan. Predict. Protect." + honest-uncertainty line |

## 3. 5-Minute Version

3-min version + : field/crop setup (30 s) · weather panel & forecast-driven risk change (30 s) · pest detection sample image (20 s) · expert queue + verdict flow (30 s) · feedback stored → dataset export shown (20 s).

## 4. 10-Minute Technical Version (jury deep-dive)

5-min version + architecture walkthrough (blueprint diagrams: system, AI pipeline, risk engine) · quality-engine internals (scores shown) · question selection logic (information gain, before/after entropy) · risk-engine factor table transparency (weights labeled prototype) · RAG citations demo · expert-review export shown as training manifest · security/privacy summary · testing summary · scalability path (district→state) · dataset-vs-field performance honesty slide.

## 5. Demo Engineering (robustness)

- Seed script loads the exact story data (2 farmers, expert, officer, labeled images, one insufficient case, hotspot cluster) — all tagged DEMO.
- Two modes: online VM, or fully offline laptop+hotspot (compose stack; cached tiles; weather adapter in canned-data mode — labeled as demo fixtures).
- AI runs are **real pipeline runs** on staged images — never mocked responses; the offline mode is the safety net.
- Backup: pre-recorded full video; presentation clicker; offline FAQ pack (docs/21).

## 6. Demo Metrics to Quote (honest)

System latencies measured live; quality-gate rejections; question-round completion; expert agreement on staged cases; **no accuracy claims without the docs/17 protocol** — quote dataset baselines as "dataset performance".
