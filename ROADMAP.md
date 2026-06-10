# Synthr — Roadmap

Where Synthr is, and the path from working MVP to production-grade gateway.
✅ done · 🟡 partial · ⬜ not started

---

## 1. Built — the MVP engine

| Item | Status | Note |
|---|---|---|
| Dual-key auth (secret/public) + origin allowlist | ✅ | keys checked against config |
| Provider abstraction | ✅ | Gemini native + one OpenAI-compatible adapter (OpenAI/Grok/Groq/Ollama) + rembg + mock |
| `synthr.config.yaml` — per-feature provider, limits, cache, guardrails | ✅ | |
| Request pipeline (auth → guardrails → rate limit → cache → optimize → run → log) | ✅ | one shared runner for every feature |
| Rate limiter (per user/feature, sliding window) | ✅ | SQLite-backed |
| Guardrails (input PII/keyword/length, output PII redaction) | ✅ | regex-based |
| Exact + TF-IDF semantic cache | ✅ | persists across restart |
| Provider fallback | 🟡 | fails over on provider error; broader triggers + circuit breaker → §2 |
| Token optimizer | 🟡 | whitespace compression only |
| Usage + USD cost logging + HTMX dashboard | ✅ | |
| Features: `fillForm`, `summarize`, `translate`, `image`, `removeBackground` | ✅ | |
| Python SDK, TypeScript SDK, CLI (`init`/`keygen`/`status`) | ✅ | not yet published |
| Dockerfile + Compose + healthcheck | ✅ | one-command boot |

---

## 2. Production hardening — the real path

The MVP runs on SQLite, single-process, with regex guardrails and config-checked keys. To carry untrusted, multi-team, high-concurrency traffic it needs:

### Storage & scale
- ⬜ **Postgres** backend (SQLAlchemy + Alembic); keep SQLite for dev
- ⬜ **Redis** for cache + rate-limit counters shared across workers
- ⬜ **Background queue** (arq/Celery/RQ) for slow image/background tasks + a job-polling endpoint

### Reliability
- 🟡 **Fallback strategy** — fail over on timeout / rate-limit / invalid response / safety block (not just provider error)
- ⬜ **Circuit breaker** + provider health checks
- ⬜ **Structured provider error mapping** across adapters (typed codes)

### Auth & security
- ✅ **Hashed project keys** (sha256, constant-time) + scopes + expiry + revoke + audit-on-failure; `synthr keygen` emits the hash
- ⬜ **Online key rotation**, per-key last-used analytics, secret-manager integration
- ✅ **SECURITY.md** threat model + responsible disclosure

### Observability & control
- ⬜ **Request tracing** (OpenTelemetry) + metrics
- ⬜ **Per-project budgets** (hard USD caps, not just logging)
- ⬜ **Admin UI** for projects / keys / config

### Compatibility & features
- ⬜ **Drop-in OpenAI-compatible endpoint** (`POST /v1/chat/completions`) — point the official OpenAI SDK / LangChain / etc. at Synthr and inherit the whole pipeline *(deliberately parked: it re-exposes raw chat, which is in tension with the capability-layer positioning — revisit before building)*
- ⬜ **Streaming** (SSE) for text features
- ⬜ **ML PII** guardrail backend (e.g. Presidio) alongside regex
- ⬜ **Embeddings-based** semantic cache (replace TF-IDF) + eval loop

### Delivery
- ⬜ **Published SDKs** (PyPI + npm) via release-on-tag
- ⬜ **Load / concurrency tests**
- ✅/🟡 **CI** (pytest + ruff + mypy on PR)

---

## 3. Feature catalog — breadth (the capability layer)

The product is *features*, not a pipe, so the catalog should keep growing. A text feature = `features/<name>/` + a route; a new kind = a provider method + a `Capability` flag.

**Text:** ⬜ `seo` · ⬜ `rewrite` · ⬜ `classify`/`sentiment` · ⬜ `extract` · ⬜ `generate` · ⬜ `moderate`
**Image:** ⬜ `editImage` · ⬜ `upscale` · ⬜ `variations`
**Vision:** ⬜ `describeImage` · ⬜ `ocr` · ⬜ `detectObjects`
**Audio:** ⬜ `transcribe` · ⬜ `tts`
**Embeddings:** ⬜ `embed` — text → vector (also powers semantic cache + search)
