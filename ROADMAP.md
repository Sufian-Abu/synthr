# Synthr — Roadmap

Milestone-based. ✅ done · 🟡 partial · ⬜ not started

---

## v0.1 — OSS MVP  (current)

Runnable end-to-end on one box; honest about its limits.

| Area | Status | Note |
|---|---|---|
| Dual-key auth — **hashed** keys, scopes, expiry, revoke, audit-on-failure | ✅ | `synthr keygen` emits the hash |
| Provider abstraction — per-provider adapters | ✅ | Gemini + OpenAI/Grok/Groq/Ollama + rembg + mock |
| Per-provider JSON mode · image · typed errors · streaming · tools | ✅ | see capability matrix |
| Request pipeline (auth → guardrails → rate limit → cache → optimize → run → log) | ✅ | one shared runner |
| Provider fallback — error / timeout / rate-limit / invalid-response | ✅ | safety blocks don't fail over |
| Guardrails — input PII/keyword/length + output PII redaction | ✅ | regex-based |
| Exact + TF-IDF semantic cache · rate limiter · usage + USD cost · HTMX dashboard | ✅ | |
| Features — fillForm · summarize · translate · rewrite · generate · seo · classify · extract · moderate · embed · image · removeBackground | ✅ | catalog grows; callers change nothing |
| Background jobs · per-project budgets · circuit breaker | ✅ | submit/poll, hard caps, skip dead providers |
| OpenAI-compatible `/v1/chat/completions` (streaming + tools) | ✅ | drop-in for the OpenAI SDK |
| Docker + Compose + healthcheck · CLI · Python & TS SDKs | ✅ | SDKs not yet published → v0.3 |
| CI (ruff + mypy + pytest + docker build) · security preflight | ✅ | |
| Docs — README, USAGE, SECURITY, CONTRIBUTING, ADRs | ✅ | |

---

## v0.2 — Production hardening

Carry untrusted, multi-team, higher-concurrency traffic.

- ⬜ **Postgres** backend (SQLAlchemy + Alembic); keep SQLite for dev
- ⬜ **Redis** for cache + rate-limit counters shared across workers
- 🟡 **Background jobs** — thread-pool worker + `POST /v1/jobs` / `GET /v1/jobs/{id}` shipped; durable queue (arq/Celery) + retries + webhooks still to do
- ✅ **Circuit breaker** + provider health (skip a failing provider, straight to fallback)
- ✅ **Per-project budgets** (hard daily/monthly/per-feature caps → 402)
- ⬜ **Request tracing** (OpenTelemetry) + metrics
- ⬜ **Online key rotation**, per-key last-used analytics, secret-manager integration
- ⬜ **ML PII** guardrail backend (e.g. Presidio) alongside regex
- ⬜ **Embeddings-based** semantic cache (replace TF-IDF) + eval loop
- ⬜ **Streamed cache + output redaction** (streaming currently bypasses both)
- ⬜ **Load / concurrency tests**

---

## v0.3 — SDK publishing & DX

- ⬜ Publish **`synthr-sdk`** to **PyPI** + **npm** via release-on-tag
- ⬜ Versioned changelog + semver
- ⬜ Generated API docs site from the OpenAPI spec
- ⬜ More client examples (Go, mobile, server frameworks)

---

## v0.4 — Dashboard & admin

- ⬜ **Admin UI** for projects / keys / config (create, rotate, revoke, scope)
- ⬜ Dashboard: per-project budgets, alerts, cache-quality view
- ⬜ Audit-log viewer

---

## Feature catalog — breadth (ongoing, any milestone)

A text feature = `features/<name>/` + a route; a new kind = a provider method + a `Capability`.

**Text:** ✅ `fillForm` · ✅ `summarize` · ✅ `translate` · ✅ `rewrite` · ✅ `generate` · ✅ `seo` · ✅ `classify` · ✅ `extract` · ✅ `moderate`
**Image:** ✅ `image` · ⬜ `editImage` · ⬜ `upscale` · ⬜ `variations`
**Vision:** ✅ `removeBackground` · ⬜ `describeImage` · ⬜ `ocr` · ⬜ `detectObjects`
**Audio:** ⬜ `transcribe` · ⬜ `tts`
**Embeddings:** ✅ `embed` — text → vector (Gemini / OpenAI / Ollama); could also power the semantic cache + search
