# ADR 0002 — SQLite first

**Status:** accepted (revisit for production — Postgres + Redis)

## Context

The gateway needs persistence for the cache, the usage/cost log, and rate-limit counters.
The headline promise is "one Docker command." A production deployment will eventually want
Postgres + Redis, but requiring them on day one kills the zero-setup story.

## Decision

Ship on **SQLite** (single file, in the container or a mounted volume; `:memory:` for tests).
One storage layer, no external services. Postgres + Redis are a documented v0.2 upgrade behind
the same interfaces.

## Consequences

- `docker compose up` works with nothing else running — the demo and single-team case are trivial.
- Tests run fully in-memory, fast, no fixtures.
- **Limitation:** a single connection with a lock — not built for high-concurrency multi-tenant
  writes. This is stated plainly in the README maturity table and SECURITY.md.
- The cache/usage/ratelimit code is written against narrow interfaces so a Postgres/Redis
  backend can slot in without touching features.
