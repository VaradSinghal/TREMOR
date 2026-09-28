# TREMOR — Tradeoffs & Design Decisions

This document records deliberate tradeoffs and design decisions made during development.

---

## Phase 0 — Foundation

### SQLite vs Postgres
- **Decision:** Start with SQLite (via `aiosqlite`) for zero-config development; schema is Postgres-compatible.
- **Tradeoff:** Concurrent writes are limited. Acceptable for a single-process deployment; if scaling, swap to Postgres via `DATABASE_URL`.

### Structlog JSON vs Console
- **Decision:** JSON output in production (`LOG_LEVEL != DEBUG`), console renderer for development.
- **Tradeoff:** JSON logs are grep-unfriendly for humans but machine-parseable for production monitoring.

### Coverage threshold (50% → 90%)
- **Decision:** Start at 50% minimum, raise to 90% for `core/` once all phases land.
- **Tradeoff:** Low initial bar lets Phase 0 pass; strict bar on `core/` ensures detection logic is proven.

---

_Each team member should add their decisions here as they implement their components._
