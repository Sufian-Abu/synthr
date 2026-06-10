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
- ✅ **Structured provider error mapping** — per-provider error bodies → typed codes across all adapters
- 🟡 **Fallback strategy** — fails over on timeout / rate-limit / invalid response (safety blocks deliberately don't)
- ⬜ **Circuit breaker** + provider health checks

### Auth & security
- ✅ **Hashed project keys** (sha256, constant-time) + scopes + expiry + revoke + audit-on-failure; `synthr keygen` emits the hash
- ⬜ **Online key rotation**, per-key last-used analytics, secret-manager integration
- ✅ **SECURITY.md** threat model + responsible disclosure

### Observability & control
- ⬜ **Request tracing** (OpenTelemetry) + metrics
- ⬜ **Per-project budgets** (hard USD caps, not just logging)
- ⬜ **Admin UI** for projects / keys / config

### Compatibility & features
- ✅ **Drop-in OpenAI-compatible endpoint** (`POST /v1/chat/completions`) — official OpenAI SDK / LangChain / etc. point `base_url` at Synthr and inherit the whole pipeline
- ✅ **Streaming (SSE)** — per-provider `stream_complete`, surfaced via the chat endpoint (`stream: true`)
- ✅ **Tool calling** — OpenAI-format tools in, normalized `tool_calls` out (incl. Gemini's `functionDeclarations`), surfaced via the chat endpoint
- ⬜ **Streamed cache + output redaction** — streaming currently bypasses both
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
