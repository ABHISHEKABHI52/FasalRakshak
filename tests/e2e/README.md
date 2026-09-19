# Cross-cutting E2E tests (planned — not implemented in Phase 1)

Per `docs/16_Testing_Strategy.md`, end-to-end tests are **P1 (important)** and will cover:

1. Farmer crop-scan flow including the insufficient-evidence question loop.
2. Expert verdict flow (confirm / correct / reject).
3. Officer hotspot map drill-down.
4. Offline capture → queued sync.

**Status: TODO — FUTURE PHASE.** Playwright arrives with the farmer flows (Phase 2+);
Phase 1 covers the foundation with backend pytest (`backend/tests/`) and frontend
vitest (`frontend/src/**/*.test.tsx`).