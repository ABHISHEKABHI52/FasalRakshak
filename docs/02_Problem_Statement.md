# 02 · Problem Statement

## 1. Original Problem Statement [SOURCE-DERIVED]

**SIH26131 — Early detection and management of crop diseases and pest infestations.**
Theme: **Agriculture, FoodTech & Rural Development** · Category: **Software** · SIH 2026.

> Source discipline note: the SIH problem statement, its ID, theme and category are preserved exactly as issued. The original PS PDF was not present in the repository at authoring time; alignment is to the approved written brief. Nothing in this project changes the problem statement — only the implementation architecture and product design may be improved.

## 2. Problem Analysis

Crop diseases and pest infestations are routinely detected **after visible damage** — because visible symptoms are the farmer's only reliable signal today. By then, control is costlier, yields are already affected, and (in the case of pests and airborne pathogens) neighbouring fields are often already exposed.

### 2.1 Structural gaps in current practice

| Gap | Today's reality | Consequence |
|---|---|---|
| Detection timing | Farmer notices when damage is visible | Late intervention |
| Identification | Guesswork or neighbours' advice | Wrong treatment; pesticide overuse |
| Expert access | KVKs/officers are few; distance and travel costs | Advice delayed or never sought |
| Photos taken casually | Blur, glare, occlusion, no context | Any AI tool outputs garbage |
| Surveillance | Mostly manual, periodic, paper-based | Districts react instead of pre-empt |
| Advice localization | Generic advice not tuned to crop stage/region/weather | Low trust, low adoption |
| Language | Hindi/regional-language material exists but is fragmented | Advice not understood |

### 2.2 Why a photo classifier is insufficient

A "photo → label" app breaks on real field conditions: bad photos, look-alike diseases, unseen diseases, and labels with no action attached. It answers *what*, but not *how confident*, *why*, *what next*, or *what happens next week* — the five questions a farmer actually needs answered before acting **[SOURCE-DERIVED core-principle framing]**.

### 2.3 What "early detection and management" demands

1. **Detection while intervention is still cheap** (quality-gated vision AI).
2. **Honest uncertainty** (never force a diagnosis; ask adaptive questions — Chain-of-Inquiry framing **[SOURCE-DERIVED]**, External Research R1).
3. **Forecasting** (3/7/14-day risk; early-warning rather than after-the-fact diagnosis).
4. **Actionable, localized, safe advisory** (IPM-first, source-grounded, multilingual).
5. **Surveillance** (GIS aggregation from many fields → hotspots → officer response).
6. **Improvement loop** (expert-verified cases become training data).

## 3. Stakeholder Pain Points

| Stakeholder | Pain | FasalRakshak relief |
|---|---|---|
| Farmer | "What is this? What do I do? Will it spread?" — with no one to ask | Scan → honest answer → risk → simple action in own language |
| Extension worker | Can't physically cover all fields; duplicate visits | Triage list of at-risk fields; single-phone assisted scanning |
| Expert | Duplicate trivial queries; no context when consulted | Case queue pre-packaged with image + AI hypothesis + answers + weather |
| District officer | No real-time district picture; outbreak surprise | Live map separating predicted/reported/verified; hotspot alerts |
| Agriculture department | Fragmented data; no field-level evidence chain | Structured, auditable observation pipeline (integration-ready **[FUTURE FEATURE]**) |

## 4. Solution Thesis

> **Evidence > Guess.** FasalRakshak treats each scan as an *inquiry*, not a *lookup*: gather visual evidence, measure its sufficiency, ask for what's missing, fuse context, estimate risk, advise with sources, escalate when needed, and learn from verification.

## 5. Scope Boundaries

**In scope (MVP/SIH):** farmer scanning + diagnosis + risk + advisory; adaptive questioning; weather context; basic GIS + officer dashboard; expert validation; multilingual (en/hi/Hinglish); offline-tolerant PWA.

**Out of scope (explicitly):** autonomous pesticide prescription; guaranteed disease identification on any photo; lab diagnostics integration **[FUTURE FEATURE]**; drone/satellite imagery **[FUTURE FEATURE]**; financial/insurance services; hardware (sensors/traps) beyond optional image intake **[FUTURE FEATURE]**.

## 6. Success Definition (problem-level)

- Farmers receive an actionable answer or an honest "insufficient evidence + questions" — never a silent wrong guess.
- The system produces a district-level early-warning signal from field-level events within minutes of a high-risk confirmation.
- Expert-verified data compounds: every corrected case improves the evidence base.
