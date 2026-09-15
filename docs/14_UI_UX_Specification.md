# 14 · UI/UX Specification

Farmer-first, low-literacy-friendly, rural-connectivity-aware. [PROPOSED DESIGN; SOURCE-DERIVED persona needs]

## 1. Design Principles

1. **One primary action per screen.** 2. **Big targets, big text** (≥44 px, base font 16 px, large-text mode). 3. **Icon + label pairing** (never icon-only). 4. **Show uncertainty honestly** — confidence bars, "insufficient evidence" states. 5. **Explain before you prescribe** — every result has a "why" section. 6. **Works on 2G** — skeletons, compression, queue badges. 7. **Local language default** — hi for many regions, switchable, persisted.

## 2. Screen Inventory (farmer)

| Screen | Purpose | Key elements |
|---|---|---|
| Login/Register | Auth | phone-first, language picker at entry |
| Dashboard | Overview | fields w/ status chips, active alerts, "New Scan" FAB |
| New Scan wizard | Capture flow | field→crop→stage→capture; quality feedback inline; retake tips with illustrations |
| Quality feedback | Gate | score band, reasons ("blurry — hold steady"), retake CTA |
| Analyzing | Progress | staged: "Checking image → Identifying → Assessing risk" |
| Result | Diagnosis | hypothesis card (top-k chips), confidence gauge, "Why we think so", risk panel (current + 3/7/14 bars), advisory steps (numbered, icons), sources link, expert CTA |
| Questions | Adaptive Q&A | 3–5 questions, single-tap options, progress dots |
| Risk detail | Outlook | 3/7/14 bars + factor chips ("rain in last 3 days +2") |
| History | List | scans by field, status pills (diagnosed / insufficient / expert review) |
| Field detail | Timeline | crop cycle, scans, observations, weather summary |
| Alerts | Feed | severity colors, read states |
| Profile/Settings | Prefs | language, notification prefs, offline queue status, consent (ML-use) |

## 3. Screen Inventory (expert / officer / admin)

- **Expert:** case queue (urgency-sorted, filters), case detail (image, AI top-k + confidence, answers, weather, history), verdict sheet (Confirm/Correct/Reject + remarks), my-review stats.
- **Officer:** dashboard cards (7 KPIs), map (layer toggles: reported/verified/predicted/hotspots), hotspot popup + drill-down, inspection/intervention logging, report export.
- **Admin:** users & roles, knowledge ingestion w/ source metadata, model registry (status transitions), config/flags, audit view.

## 4. Key States & Microcopy (localized; en samples)

- **Insufficient evidence:** "We need more information to be sure. Please answer 4 quick questions." (never: "Unknown disease" scary framing)
- **Unusable image:** "Photo isn't clear enough. Hold steady and fill the frame with the leaf." + retake CTA.
- **Weather missing:** "Weather data unavailable — risk shown without weather."
- **Offline saved:** "Saved on your phone. It will send when internet returns."
- **Expert recommended:** "Our confidence is limited. An expert should verify this case."
- **Verified result:** "Confirmed by an agriculture expert ✓".

## 5. Visual System

Tailwind tokens: color semantic (risk: green/amber/orange/red), typography scale, spacing 4-pt; illustrations for capture tips; accessible contrast AA; dark-mode **[P2]**; risk gauge = horizontal bar + percentage + word (never color-only).

## 6. Multilingual UI

next-intl; locale detection on first launch; language switcher persisted; disease/pest names + advisory steps + questions all localized from backend locale columns / i18n files; Hinglish = en copy with transliterated agri terms; RTL not needed (en/hi) but i18n layer direction-ready.

## 7. Low-Connectivity UX

Offline banner; queued-items badge; last-cached timestamps on weather/map; map lazy-loads with low-zoom tiles cached; all destructive actions reversible (soft states); sync status per item.
