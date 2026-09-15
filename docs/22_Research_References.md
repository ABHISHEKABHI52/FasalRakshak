# 22 · Research References

Source discipline: concepts tagged **[SOURCE-DERIVED]** come from the approved concept brief; **[EXTERNAL RESEARCH — verified]** items below were verified against the actual papers (title, venue, pages) available to the team; datasets and canonical methods are cited from their original publications. No fabricated papers, datasets, statistics, or results.

## 1. Core Research Foundation (adaptive questioning) 

**R1 [EXTERNAL RESEARCH — verified] · Chain-of-Inquiry / PlantInquiryVQA**
Sakib, S.N.; Haque, N.; Amin, S.B.; Abdullah, H.M.; Hasan, M.M.; Hossain, M.Z.; Arman, S.E. — *"Thinking Like a Botanist: Challenging Multimodal Language Models with Intent-Driven Chain-of-Inquiry."* Findings of the Association for Computational Linguistics: ACL 2026, pp. 34862–34892 (July 2026).
Introduces **PlantInquiryVQA** — 24,950 expert-curated plant images, 138,068 question–answer pairs with visual grounding, severity labels — and the **Chain of Inquiry** framework: diagnosis modeled as ordered, intent-driven question–answer sequences conditioned on grounded visual cues, mirroring how botanists probe with targeted questions adapting to species, symptoms and severity.
**Use in FasalRakshak [SOURCE-DERIVED usage]:** direct inspiration for the Adaptive Question Engine (docs/00 §17) — evidence-gap-driven question selection rather than fixed questionnaires.

**R2 [EXTERNAL RESEARCH — verified] · Expert-verified reasoning + calibrated confidence**
Mahmood, H.; Yu, Y.; Anwer, R. — *"AgriChain: Visually-Grounded Expert-Verified Reasoning for Interpretable Agricultural Vision–Language Models."* LREC 2026, pp. 2268–2276.
~11,000 expert-curated leaf images with disease labels, calibrated High/Medium/Low confidence, and expert-verified chain-of-thought rationales using standardized descriptors (lesion color, margin, distribution).
**Use:** labeling-guide descriptor standardization (docs/18 §4); calibrated-confidence UX framing; expert-verified rationale pattern for `expert_reviews`.

## 2. Domain Benchmarks & Language Resources

**R3** Nawaz, U.; Awais, M.; Gani, H.; Naseer, M.; Khan, F.S.; Khan, S.; Anwer, R.M. — *"AgriCLIP: Adapting CLIP for Agriculture and Livestock via Domain-Specialized Cross-Model Alignment."* COLING 2025, pp. 9630–9639. (Domain gap between general and agricultural vision — motivates our field-data fine-tuning.)
**R4** Wang, H. et al. — *"Agri-CM3: A Chinese Massive Multi-modal, Multi-level Benchmark for Agricultural Understanding and Reasoning."* ACL 2025, pp. 11729–11754. (3,939 images, 15,901 questions; even top MLLMs reach only ~63.6% — supports our caution against MLLM-only diagnosis.)
**R5** Nedellec, C.; Courtin, M.; Yao, X.; Grosdidier, M.; Pieretti, I.; Duperier, S.; Bossy, R. — *"EPOP: A benchmark corpus for Assessing NLP Models on Structured Information Extraction in Plant Health."* LREC 2026, pp. 1331–1340. (Entity/relation extraction for phytosanitary surveillance — future monitoring-text mining **[FUTURE FEATURE]**.)
**R6** Didwania, K.; Seth, P.; Kasliwal, A.; Agarwal, A. — *"AgriLLM: Harnessing Transformers for Farmer Queries."* NLP4PI @ EMNLP 2024, pp. 179–187. (LLMs for farmer query resolution at scale — informs future multilingual query handling **[FUTURE FEATURE]**.)

## 3. Datasets (public, cited from original publications)

**R7** Hughes, D.P.; Salathé, M. — *"An open access repository of images on plant health to enable the development of mobile disease diagnostics (PlantVillage)."* Frontiers in Plant Science, 2015. — Lab-condition disease images; M3 pre-training (lab≠field discipline enforced).
**R8** Singh, V.; Misra, A.K. et al. — *"PlantDoc: A Dataset for Visual Plant Disease Detection."* CoDS-COMAD 2020. — In-the-wild plant disease images; fine-tuning/eval realism.
**R9** Wu, X. et al. — *"IP102: A Large-Scale Benchmark Dataset for Insect Pest Recognition."* CVPR 2019. — Pest recognition; source for M4 class mapping.

## 4. Methods

**R10** Guo, C.; Pleiss, G.; Sun, Y.; Weinberger, K.Q. — *"On Calibration of Modern Neural Networks."* ICML 2017. (Temperature scaling; ECE — our calibration protocol.)
**R11** Selvaraju, R.R. et al. — *"Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization."* ICCV 2017. (Explainability overlays.)
**R12** Chen, T.; Guestrin, C. — *"XGBoost: A Scalable Tree Boosting System."* KDD 2016. (M5 risk model.)
**R13** Ester, M.; Kriegel, H.-P.; Sander, J.; Xu, X. — *"A Density-Based Algorithm for Discovering Clusters in Large Spatial Databases with Noise (DBSCAN)."* KDD 1996. (GIS hotspot clustering.)
**R14** Tan, M.; Le, Q. — *"EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks."* ICML 2019. **R15** Howard, A. et al. — *"Searching for MobileNetV3."* ICCV 2019. (Backbones.)
**R16** Redmon, J. et al. — *YOLO* family; Ultralytics YOLOv8/11 documentation (implementation reference).

## 5. Government & Domain Anchors [SOURCE-DERIVED framing]

- **Directorate of Plant Protection, Quarantine & Storage (DPPQS), Govt of India** — National Pest Surveillance System (NPSS) framing; surveillance-workflow alignment **[SOURCE-DERIVED concept; any integration = FUTURE FEATURE]**.
- **ICAR / NCIPM / state agricultural universities / KVK networks** — IPM guidance and packages of practices (RAG corpus sources; ingested only from publicly available material with metadata).
- **FAO** — Integrated Pest Management guidance (generic principles referenced qualitatively).
- **IMD / Open-Meteo** — weather data providers (adapter targets, docs/00 §20).

## 6. Reference Integrity Notes

- R1–R6 verified from team-held copies (title/venue/pages extracted directly); R7–R16 are canonical citations to original publications.
- If any reference cannot be produced on demand during Q&A, it must not be cited in the pitch.
- Distinguish always: [SOURCE-DERIVED] concept-brief ideas vs [EXTERNAL RESEARCH] published work vs [PROPOSED DESIGN] FasalRakshak decisions.
