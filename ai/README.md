# AI / ML (planned — not implemented in Phase 1)

This directory will hold the offline model work defined in `docs/06_AI_ML_Architecture.md`:

```
ai/
├── training/     # per-crop disease classifier, crop-ID, pest detector, quality head
├── evaluation/   # frozen eval sets, metric reports (docs/17)
├── notebooks/    # exploration (never shipped to production)
└── export/       # ONNX export scripts + registry manifests
```

**Status: TODO — FUTURE PHASE.** No models, datasets or training code exist yet.
Phase 1 deliberately contains no AI, as instructed. The serving contract that these
artifacts must satisfy is specified in `docs/06` and `docs/00` §15; the backend
integration point will be `backend/app/ai/` (extraction path documented in docs/05 §2.3).

Rules that will apply when this phase starts (from the architecture):
- no accuracy claims without a recorded held-out evaluation (`docs/17`);
- public-dataset results are never reported as field performance (`docs/18`);
- "Insufficient Evidence" is a first-class model output (`docs/06` §9).