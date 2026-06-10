# Synthr — Roadmap & Backlog

Status against the architecture + tech-stack diagrams, plus the expanded feature catalog.
✅ done · 🟡 partial · ⬜ not started

---

## A. Gaps from the architecture diagram (the gateway engine)

| Item | Status | Note |
|---|---|---|
| Auth & project keys | ✅ | dual-key (secret/public) + origin allowlist |
| Provider abstraction | ✅ | 6 providers, one interface |
| `synthr.config.yaml` | ✅ | per-feature provider, limits, cache |
| Rate limiter (user/day/week/month) | ✅ | sliding window, SQLite |
| Usage logging | ✅ | one row per request |
| Exact cache | ✅ | SQLite, persists across restart |
| **Semantic cache** (embeddings) | ⬜ | exact-only today; needs embed provider + eval loop |
| **Provider fallback chain** | ⬜ | retry same provider ✅; failover to *other* provider ⬜ |
| **Guardrails engine** (PII / keyword / output) | ⬜ | config fields exist, not enforced |
| **Token optimizer** (~30% savings) | ⬜ | |
| **Usage dashboard** (HTMX UI) | ⬜ | data is logged; no UI yet |
| Monthly USD spend cap | ⬜ | per-provider price table needed |

## B. Gaps from the tech-stack diagram (distribution & DX)

| Item | Status | Note |
|---|---|---|
| FastAPI / SQLite / Pydantic | ✅ | |
| pytest | ✅ | 17 tests |
| LLM provider APIs | ✅ | Gemini, OpenAI, Grok, **Groq**, Ollama |
| **TypeScript SDK** (npm) | ⬜ | thin client over the HTTP API |
| **Python SDK** (pip) | ⬜ | async/sync httpx client |
| **Dockerfile + Compose** | ⬜ | the "one `docker run`" promise |
| **GitHub Actions** (CI + publish) | ⬜ | test on PR, publish SDKs on tag |
| **MkDocs** docs site | ⬜ | README exists |
| **CLI** (`synthr init/keygen/status`) | ⬜ | |
| structlog structured logging | ⬜ | |
| uv (instead of pip) | 🟡 | works with pip/uv both |

---

## C. Expanded feature catalog (the capability layer)

The product is *features*, not a pipe — so the catalog should grow well beyond three.

### Text (LLM — reuse the `complete` path)
- ✅ `fillForm` — schema-constrained autofill
- ✅ `summarize` — concise summary *(added this round)*
- ✅ `translate` — translate to a target language *(added this round)*
- ⬜ `seo` — title/description → SEO meta (title, description, keywords)
- ⬜ `rewrite` — grammar/tone fix, rephrase
- ⬜ `classify` / `sentiment` — label or score text
- ⬜ `extract` — generalized structured extraction (fillForm's bigger sibling)
- ⬜ `generate` — freeform prompt → text (escape hatch)
- ⬜ `moderate` — safety/topic classification

### Image (diffusion)
- ✅ `image` — text → image
- ⬜ `editImage` — image + instruction (inpaint/edit)
- ⬜ `upscale` — enhance resolution
- ⬜ `variations` — variants of an input image

### Vision (non-LLM / multimodal)
- ✅ `removeBackground` — local `rembg`
- ⬜ `describeImage` — caption / alt-text
- ⬜ `ocr` — text from image
- ⬜ `detectObjects` — labels + boxes

### Audio (future)
- ⬜ `transcribe` — speech → text
- ⬜ `tts` — text → speech

### Embeddings (unlocks more)
- ⬜ `embed` — text → vector (also powers the semantic cache + search)

> Pattern proven: a text feature = `features/<name>/{models,service}.py` + a route. A new
> capability kind = a provider method + `Capability` flag. Adding features is now cheap.

---

## D. Proving it works — client integration

Show the same gateway consumed three ways (no code differences on our side):
- ✅ **REST / curl** — `examples/rest.sh`
- ✅ **Backend (Python, httpx)** — `examples/backend.py`
- ✅ **Frontend (JS `fetch`)** — `examples/frontend.mjs` + `examples/frontend.html`
- ⬜ **First-party SDKs** (npm + pip) — sugar over the above

---

## E. Suggested build order

1. **Dockerfile + Compose** — delivers the headline "one command" promise.
2. **HTMX dashboard** — makes the usage data visible (demo gold).
3. **Guardrails enforcement + provider fallback** — complete the engine (small, high value).
4. **A few more text features** (`seo`, `rewrite`, `extract`) — breadth.
5. **SDKs** (Python first, then TS), then **CI + MkDocs** for launch.
6. **Semantic cache + `embed`** — the "smart" tier, with the eval loop.
