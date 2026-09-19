# Development scripts

Phase 1 helpers. These are developer conveniences — they contain no business logic.

| Script | Purpose |
|---|---|
| `init_env.ps1` | Copies `.env.example` to `.env` if it does not exist (never overwrites). |
| `run_all_checks.ps1` | Runs backend tests + frontend typecheck/tests/build. |

Planned helpers (with later phases): `seed_demo_data`, `ingest_knowledge`, `export_dataset`,
`backup_db` (see `docs/00` §46).