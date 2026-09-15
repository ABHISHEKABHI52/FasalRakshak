# 21 · FAQ For Judges

50 difficult questions with **Strong / Technical / Simple** answers. All answers respect the honesty rules: no fabricated accuracy; IMPLEMENTED/MVP/SIH-DEMO/ADVANCED/FUTURE labels used where relevant. [PROPOSED DESIGN answers]

**Q1. Why is this different from existing crop-disease apps?**
Strong: Existing apps map a photo to a label; FasalRakshak is an early-warning decision system — it separates confidence from risk, refuses to guess when evidence is insufficient, asks targeted follow-up questions, forecasts 3/7/14 days, and routes hard cases to experts with GIS surveillance for officers.
Technical: Calibrated probabilities + OOD gating + information-gain-driven question selection (Chain-of-Inquiry-inspired) + rule-transparent risk engine + RAG-cited advisories + human-in-the-loop feedback into dataset manifests.
Simple: "Other apps guess from a photo. Ours says 'not sure' when it isn't sure, asks the right questions, tells you what may happen next week, and never advises without a source."

**Q2. Why not use image classification alone?**
Strong: A label without confidence, context, risk or action is unsafe — farmers act on advice, not names.
Technical: Classification is one evidence source; field conditions (blur, look-alikes, stage, weather) make single-shot labels brittle; our pipeline gates quality, gates crop identity, models uncertainty, and fuses context before advising.
Simple: "A photo alone can fool any AI — so we don't rely on the photo alone."

**Q3. Where did your data come from?**
Strong: Public research datasets (PlantVillage, PlantDoc, IP102) for pre-training, plus our own consented field captures and expert-verified cases as they accumulate; knowledge text only from public government/university sources.
Technical: Dataset manifests version sources, checksums, split hashes; expert-verified production cases export as training records (consent-gated).
Simple: "Public research datasets to start, real farm photos and expert checks as we grow — all tracked version by version."

**Q4. How do you handle unknown diseases?**
Strong: The system returns "Insufficient Evidence," shows hypotheses as possibilities, asks questions, and recommends expert verification — it never invents a label.
Technical: OOD detection (energy/max-softmax thresholds tuned on out-of-scope images) routes to the insufficient state; unknowns enter the expert-correction pipeline and future datasets.
Simple: "If it hasn't seen something before, it says so and calls an expert — it doesn't make things up."

**Q5. How do you validate predictions?**
Strong: Experts confirm/correct/reject hard and flagged cases; every verdict is stored with the original AI output for auditing and learning.
Technical: `expert_reviews` freezes original prediction + model version + confidence + corrected label; agreement rates monitored per class; expert feedback is a first-class training source.
Simple: "Real agriculture experts double-check the AI's work, and the AI learns from their corrections."

**Q6. How do you prevent hallucination?**
Strong: Recommendations are assembled only from retrieved, cited government/university documents; the system refuses to advise specifics when retrieval is empty.
Technical: Template-first generation (MVP); any LLM rephrasing is restricted to retrieved chunks with citation-preserving validation, temperature 0, refusal on empty retrieval; dosage/brand generation prohibited.
Simple: "The AI can only repeat what official agriculture documents say — with the source shown every time."

**Q7. Why multimodal AI?**
Strong: Real diagnosis needs more than a photo — weather, stage, location and history change both identity likelihood and risk.
Technical: Context fusion combines visual likelihoods, answer-derived evidence, weather suitability rules, stage filters and regional priors into a posterior + evidence trace.
Simple: "The same spot can mean different things in humid vs dry weather — so the system looks at everything together."

**Q8. Why GIS?**
Strong: Diseases spread spatially; a district officer needs a live picture, and farmers benefit when nearby risks are caught early.
Technical: PostGIS storage; hex-grid heatmaps from materialized aggregates; DBSCAN clustering over reported/verified cases only; predicted-risk layers rendered separately.
Simple: "A map shows trouble spreading across villages before it reaches your field."

**Q9. Why XGBoost (and why only later)?**
Strong: Tabular risk prediction with modest data and good explainability — but it needs labeled outcome history, which doesn't exist on day one.
Technical: M5 refines rule-based weights once outcome data accrues; rules remain guardrails; SHAP-style attribution preserves transparency.
Simple: "The smart math model comes when we have real outcomes to learn from — until then, transparent rules."

**Q10. Why YOLO?**
Strong: Pests are localized objects — detection (where + how many) matters, not just classification.
Technical: YOLOv8n/YOLO11n gives real-time boxes on CPU-nano budgets; mAP@50 + per-class P/R tracked; limited Indian-priority class set at demo.
Simple: "It points at the insects it sees and counts them."

**Q11. How is risk different from confidence?**
Strong: Confidence = certainty about identity; risk = significance and evolution under weather/stage/history. 89% confidence can still be Medium current risk with High 7-day escalation.
Technical: Posterior identity vs factor-weighted context score (docs/10); separate outputs, separate UI elements.
Simple: "How sure we are" vs "how much trouble you're in."

**Q12. What happens with poor internet?**
Strong: The app is an offline-capable PWA — scans save on-device and sync later with idempotency-safe retries; UI stays usable.
Technical: Service worker + IndexedDB outbox + background sync + client compression (≤1024 px); server idempotency keys prevent duplicates.
Simple: "No signal? Take the photo anyway — it sends itself when the network returns."

**Q13. What if weather data is unavailable?**
Strong: Risk is computed without weather and explicitly flagged "weather unknown"; nothing is silently assumed.
Technical: Adapter fallback chain (fresh → stale → climatology → none) with completeness flags; weather factor weight redistributes.
Simple: "It tells you honestly: 'no weather data — risk shown without weather.'"

**Q14. Can farmers trust the recommendation?**
Strong: Trust comes from citations, calibration and expert backup — every advisory shows its government/university source, its confidence, and when to consult a human.
Technical: RAG citation invariants; calibrated outputs; expert validation loop; IPM-first, no auto-pesticide.
Simple: "Every advice shows its source, and an expert backs the hard cases."

**Q15. How do experts validate the system?**
Strong: A dedicated case queue with all context (image, AI output, answers, weather, history) and one-tap confirm/correct/reject + remarks.
Technical: Frozen prediction snapshots in `expert_reviews`; queue ordered by urgency; verdicts update diagnosis state and notify farmers.
Simple: "Experts see everything the AI saw and press confirm or correct."

**Q16. How will this scale to districts/states?**
Strong: Architecture scales in documented steps — single VM for a district pilot, then service extraction, replicas, materialized GIS aggregates, regional models.
Technical: Stateless API + per-crop small models + monthly partitioning + aggregate-first GIS; Redis/queue at higher load; multi-region later (docs/00 §40).
Simple: "Built for one district now, designed so a state is an engineering step, not a rewrite."

**Q17. How will this work with Indian farmers?**
Strong: Hindi/Hinglish-first, icon+text UI, large targets, offline queueing, phone-number login, expert escalation to KVK/officers — designed around field realities.
Technical: next-intl + backend-localized labels; WCAG-targeted accessibility; PWA (no store installs); low-bandwidth flows.
Simple: "Simple screens, their language, works on weak networks, no app-store hassle."

**Q18. How will you handle different crops?**
Strong: Per-crop models behind a crop-ID gate; adding a crop = dataset + model + catalogue entry, not a rebuild.
Technical: Crop catalogue + model registry; per-crop heads; region/crop config.
Simple: "Each crop gets its own specialist — and adding one is routine."

**Q19. What is the revenue/sustainability model?**
Strong: Primary path is public deployment by agriculture departments/KVKs; grants during growth; any future SaaS targets institutions (FPOs/agri-ecosystem), never pay-walling farmer diagnosis.
Technical: Open-source stack, CPU inference, free data tiers → low run cost (docs/00 §41).
Simple: "Farmers' core features stay free forever; institutions pay for the big-picture analytics."

**Q20. How will government departments use it?**
Strong: Officers get a live district picture — verified vs predicted layers, hotspots, trends, intervention tracking — a practical front-end to surveillance workflows.
Technical: Officer dashboard APIs; audited access; aggregate-first views; exportable reports; NPSS-style integration is FUTURE pending partnership.
Simple: "It gives agriculture officers a live map and early warning instead of paperwork after the fact."

**Q21. How do you handle poor-quality images?**
Strong: A dedicated quality engine rejects unusable photos *before* AI runs, with specific retake advice; poor-but-usable photos proceed with reduced confidence.
Technical: Heuristics (Laplacian variance, histogram, EXIF) + leaf-coverage head → score 0–100, bands Good/Acceptable/Poor/Unusable; reasons returned to UI.
Simple: "Bad photo? It tells you exactly what to fix and asks for a retake."

**Q22. What if the farmer photographs the wrong crop?**
Strong: A crop-ID gate catches it; the system asks which crop rather than diagnosing the wrong one.
Technical: M2 crop classifier; mismatch → block disease inference, prompt selection.
Simple: "It checks the leaf matches your chosen crop first."

**Q23. How do you handle diseases that look alike?**
Strong: Top-k differential is always shown; adaptive questions separate look-alikes; experts resolve persistent ambiguity.
Technical: Posterior over differential; per-answer evidence updates; confusion-matrix-aware class review.
Simple: "Instead of one answer, it shows the possibilities and asks what tells them apart."

**Q24. What about pesticide advice — do you prescribe chemicals?**
Strong: No automatic prescriptions; IPM-first steps; chemical content only as stated by verified official sources, with safety notes and officer/KVK referral.
Technical: RAG citation invariants + prohibited-content rules (no dosage/brand generation).
Simple: "We follow official guidance, show the source, and point you to your agriculture officer."

**Q25. How is "insufficient evidence" not a cop-out?**
Strong: It triggers the inquiry loop — targeted questions + context fusion + risk — which frequently resolves the case; when it doesn't, expert routing is the safe path.
Technical: Measured: question-round resolution rate is a tracked metric; the fallback is never silence.
Simple: "Saying 'I need more info' and asking smart questions is better than guessing wrong about someone's crop."

**Q26. What about region-specific disease behavior?**
Strong: Knowledge rules carry region applicability; regional prevalence feeds risk; per-region config/thresholds are supported; region-specific model variants are an ADVANCED path.
Technical: `crop_region_applicability` [P2]; regional aggregate features; registry-selected per-region variants.
Simple: "It learns what matters in your region, and says when it doesn't know."

**Q27. How accurate is the AI?**
Strong: We publish measured numbers only, with protocol (docs/17); no claims before evaluation; dataset and field performance are reported separately.
Technical: macro-F1 headline, per-class P/R, ECE, OOD stats; eval manifests versioned.
Simple: "We only quote numbers we have actually measured and can show."

**Q28. What if the model is confidently wrong?**
Strong: Calibration + differential display + expert loop limit damage; expert corrections drive retraining; safety-critical advice always includes human consultation.
Technical: Temperature scaling; top-k UI; disagreement-rate alerts per class; shadow promotion gates.
Simple: "We show our uncertainty, experts catch errors, and errors make the next version better."

**Q29. Why PWA instead of a native app?**
Strong: No app-store friction, installable on any phone, one codebase, offline-capable — ideal for hackathon velocity and rural distribution.
Technical: Service worker + IndexedDB + Web Push; native-only features (SMS) are adapter stubs marked FUTURE.
Simple: "It installs from the browser — no store, works on any Android."

**Q30. What happens to my photos?**
Strong: Stored for your scan history; used for AI improvement only with your consent (asked at first scan); identifying info stripped.
Technical: EXIF stripped client+server; consent flag gates dataset exports; deletion request anonymizes.
Simple: "Your photos stay yours; we ask before using them to improve the AI."

**Q31. Is farmer location tracked?**
Strong: Only at explicit moments (field registration, scan) — never background tracking; officers see districts by default.
Technical: geography(Point,4326) stored per field; role-gated coordinate access, audited; aggregate views default.
Simple: "Location is set by you for your field — not followed around."

**Q32. How do you protect farmer data?**
Strong: Minimum data, role-based access, row-level scoping, audit logs, encrypted transport, no selling data — officers see aggregates by default.
Technical: docs/12 controls + STRIDE-lite threat model + IDOR/security test suites.
Simple: "Your data is locked to your account; officials see maps, not your name."

**Q33. What if two farmers scan the same field?**
Strong: Field ownership governs access; shared/assisted scanning is supported via extension-worker flows.
Technical: Ownership + assisted-role permissions; idempotency per scan.
Simple: "Access follows who owns (or is helping with) the field."

**Q34. How do you avoid notification spam?**
Strong: Dedupe keys, cooldowns, severity throttling, digests, user preferences.
Technical: `alerts.dedupe_key` unique; 24-h per-field cooldown unless escalation; severity-based routing.
Simple: "You get important alerts once — not five copies."

**Q35. What is the alert severity logic?**
Strong: LOW→CRITICAL mapped from risk category + verification status + spread signals; CRITICAL implies officer visibility.
Technical: Severity rules documented; escalation table in docs/10 §6.
Simple: "Red means act now; officers see the serious ones."

**Q36. How fast is the analysis?**
Strong: Prototype targets: quality check <0.3 s, full analysis <4 s on CPU; measured live in demo.
Technical: Nano models, ONNX CPU, bounded pools; per-stage timeouts.
Simple: "A few seconds on a normal phone network."

**Q37. What happens when the AI service is down?**
Strong: Scans queue and auto-retry; farmers see a clear "temporarily unavailable" message; nothing is lost.
Technical: 503 + retry worker; idempotent analysis; degraded modes keep quality/questions functional.
Simple: "It waits and retries — your photo isn't lost."

**Q38. What if the database fails?**
Strong: Backups (nightly dumps) + restore runbook; read-only degradation where safe; honest 503s.
Technical: pg_dump + volume sync; healthchecks; restart policies.
Simple: "We keep backups so a crash doesn't erase anyone's farm record."

**Q39. How is the knowledge base kept current?**
Strong: Curated ingestion from official sources with reviewer workflow; every advisory shows the document's year/publisher.
Technical: Admin ingestion + checksums + expert review; retrieval eval set.
Simple: "New official advisories get added — with their date shown."

**Q40. Why not use a big multimodal LLM for diagnosis?**
Strong: At MVP: hardware cost, hallucination risk and auditability make nano supervised models + grounded retrieval the safe core; restricted LLM rephrasing is a SIH-demo enhancement.
Technical: Deterministic templates + calibrated CNNs; LLM outputs validated against citations; Agri-CM3-style benchmarks show MLLM reasoning gaps [EXTERNAL RESEARCH R4].
Simple: "Big AI models make confident mistakes; our design makes careful, checkable ones."

**Q41. How do you measure success?**
Strong: Problem-level (docs/02 §6) + model metrics + user metrics: completion rate, comprehension, expert agreement, hotspot lead time (pilot).
Technical: Docs/17 §2–3 metric sets wired into dashboards.
Simple: "Farmers finish scans, understand advice, experts agree — and officers get warnings earlier."

**Q42. What are the system's limits? (honesty question)**
Strong: Field-domain accuracy is unproven until pilots; pests are limited classes; weather depends on providers; insufficiency states will be common early — by design.
Technical: Documented in docs/09 §8, docs/17 §5, docs/18 §8.
Simple: "We say exactly what works and what needs field time — that's the point of Evidence > Guess."

**Q43. How would a malicious user abuse the system?**
Strong: Threat-modeled (STRIDE-lite): upload attacks, IDOR, rate abuse — mitigated via validation, scoping, limits, audits.
Technical: docs/12 §9 table + security test suite.
Simple: "We attack our own system in tests before someone else does."

**Q44. What about low-literacy users?**
Strong: Icon+label UI, single-tap answers, voice-note inputs [FUTURE], assisted mode for extension workers.
Technical: Accessibility targets; assisted-role flows.
Simple: "Pictures, big buttons, and a helper mode."

**Q45. Can this work for organic farmers?**
Strong: IPM-first advice naturally includes non-chemical steps; source filtering can prioritize organic advisories.
Technical: Knowledge-base doc_type/tag filters.
Simple: "Yes — the advice starts with non-chemical steps anyway."

**Q46. What about post-harvest or storage pests?**
Strong: Out of MVP scope; crop-scan design extends to storage imagery later.
Technical: Plant-part/catalogue extension path.
Simple: "Not yet — the design leaves room for it."

**Q47. How do you onboard new crops/languages?**
Strong: Data-driven: catalogue entries, datasets, model slots, i18n files — no architectural change.
Technical: Registry + catalogue + locale files (docs/00 §40).
Simple: "Add data and config — not new engineering."

**Q48. Why should SIH pick this over flashier demos?**
Strong: It solves the stated PS end-to-end with honest AI, works offline, scales to a department use-case, and is safe to deploy with farmers from day one.
Technical: Complete loop (inquiry→fusion→risk→advisory→validation→GIS→feedback) with production-grade engineering (docs/00 §53).
Simple: "It's the one that would actually survive contact with a real farm."

**Q49. What's next after SIH?**
Strong: Field validation pilots, expert network growth, district officer rollout — roadmap phases 3–5.
Technical: Docs/19 with labels per phase.
Simple: "Test on real farms, then a district, then a state."

**Q50. What is the single biggest technical risk?**
Strong: Field-domain model accuracy from limited data — mitigated by honest insufficiency states, expert loops, and narrow crop scope rather than overclaiming.
Technical: Calibration/OOD + dataset strategy + measured evaluation gates.
Simple: "Real-world photos are hard — so we built a system that's safe even when the AI is unsure."

---

*End of FAQ. Cross-references: docs/00 §52 (flagship previews), docs/20 (demo strategy), docs/17 (evaluation honesty).*
