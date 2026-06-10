# Synthr

*Pronounced “sin-ther” — synthesize + route.*

**A self-hosted AI gateway that gives every project ready-made AI features behind one tiny SDK.**
Stand it up once, configure it per project, and your apps just call the feature they need — no prompts to write, no provider keys in your frontend, no per-project plumbing to maintain.

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/storage-SQLite-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![SDKs](https://img.shields.io/badge/SDKs-Python%20%2B%20TypeScript-8A2BE2)
![Tests](https://img.shields.io/badge/tests-41%20passing-3fb950)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## Contents

[The problem](#the-problem) · [What Synthr is](#what-synthr-is) · [Architecture](#architecture) · [Quickstart](#quickstart) · [Calling it](#calling-it) · [Features](#features) · [Providers](#providers) · [Configuration](#configuration) · [Under the hood](#under-the-hood) · [Dashboard](#dashboard) · [Project layout](#project-layout) · [Tests](#tests) · [Status](#status)

---

## The problem

Every project that adds AI re-solves the same problems from scratch — then maintains them, separately, in each repo:

- **Provider wiring** — pick Gemini/OpenAI/…, learn its SDK, redo it in the next project.
- **Key security** — real API keys leak into frontends or get scattered across `.env` files.
- **Runaway cost** — one user (or a runaway loop) burns the whole API budget.
- **Paying twice** — the same prompt is sent and billed again and again.
- **Sensitive data** — credit cards / emails get shipped to the model with nothing stopping them.
- **No visibility** — nobody knows what AI actually costs, per project.
- **Lock-in** — switching providers means rewriting code.

**Synthr solves all of these once, in one place.** Run one Docker container for the team, drop the SDK into any project, and call the feature you need — auth, caching, rate limits, guardrails, fallback, and cost tracking come built in. One config. Every project. No repeated setup.

## What Synthr is

A self-hosted gateway that exposes **ready-made AI features** through one small SDK (or plain REST). You call the capability; Synthr owns the prompt, the provider, and the plumbing:

```python
ai.fill_form(fields=[...], context="Nike Air Max, red, size 10")
# → {"values": {"brand": "Nike", "color": "red", "size": 10}, "unfilled": []}
```

Each feature's provider is chosen in one config file, so pointing form-fill at Gemini and background-removal at a local model — or swapping either later — is a one-line change with zero app code. Engineers never see prompts, keys, or providers. They just use the feature.

## Architecture

<p align="center">
  <img src="docs/architecture.svg" alt="Synthr architecture — engineers → SDK/REST → gateway (auth, cache, rate limit, guardrails, optimizer, router) → providers" width="720">
</p>

Every request walks the same path: **authenticate → guardrails → rate limit → cache → optimize → route (with fallback) → log usage**. Each step is a small, independent module, so adding a feature or a provider doesn't touch the rest.

## Quickstart

**Docker — one command:**

```bash
cp synthr.config.example.yaml synthr.config.yaml   # what runs what
cp .env.example .env                               # your provider keys
docker compose up                                  # gateway on :8000
```

**Or local (Python 3.12+):**

```bash
pip install -e .
cp synthr.config.example.yaml synthr.config.yaml && cp .env.example .env
uvicorn "synthr_gateway.app:create_app" --factory --port 8000
```

The shipped config boots with no keys (it falls back to a mock provider), so the server comes up either way. Add a `GEMINI_KEY` or `GROQ_KEY` to `.env` to get real answers. Then visit:

- **Dashboard** → http://localhost:8000/dashboard
- **API reference (ReDoc)** → http://localhost:8000/redoc

## Calling it

First-party SDKs ship for **Python** and **TypeScript/JS**. **Any other language — Go, Ruby, PHP, Rust, Java, … — uses the plain REST endpoint** (it's just a `POST` with a header). Same endpoints, same response shape everywhere.

### REST (any language)

```bash
curl -X POST http://localhost:8000/v1/fillForm \
  -H "Content-Type: application/json" \
  -H "X-Project-Key: sk_proj_demo_secret" \
  -d '{"fields":[{"name":"brand","type":"string"},{"name":"size","type":"number"}],
       "context":"Nike Air Max size 10"}'
```

### Go (REST, standard library)

No Go SDK needed — it's one `net/http` call:

```go
body, _ := json.Marshal(map[string]any{"text": "Synthr is a self-hosted AI gateway.", "max_words": 8})
req, _ := http.NewRequest("POST", "http://localhost:8000/v1/summarize", bytes.NewReader(body))
req.Header.Set("Content-Type", "application/json")
req.Header.Set("X-Project-Key", "sk_proj_demo_secret")
resp, _ := http.DefaultClient.Do(req)
defer resp.Body.Close()

var out struct {
    Data struct{ Summary string } `json:"data"`
}
json.NewDecoder(resp.Body).Decode(&out)
fmt.Println(out.Data.Summary)
```

### Python ([`sdk/python`](sdk/python/))

```python
from synthr import AI

ai = AI(key="sk_proj_...")                       # url defaults to localhost:8000 / $SYNTHR_URL
ai.fill_form(fields=[{"name": "brand", "type": "string"}], context="Nike Air Max")
ai.summarize(text="…", max_words=20)
ai.translate(text="Good morning", target_lang="Spanish")
```

`AsyncAI` is the same with `await`. Errors raise `SynthrError` (`.code`, `.message`, `.retry_after`).

### TypeScript / JavaScript ([`sdk/typescript`](sdk/typescript/))

```ts
import { AI } from "synthr-sdk";

// Browser: a public key (pk_proj_…). Backend: a secret key (sk_proj_…).
const ai = new AI({ url: "http://localhost:8000", key: "pk_proj_demo_public" });
const { values } = await ai.fillForm([{ name: "brand", type: "string" }], "Nike Air Max");
```

### CLI

```bash
synthr init      # scaffold synthr.config.yaml + .env
synthr keygen    # mint a project key (add --public for a browser key)
synthr status    # ping a running gateway
```

Full reference — auth, every endpoint, error codes — is in **[USAGE.md](USAGE.md)**.

## Features

| Feature | Endpoint | Notes |
|---|---|---|
| Form autofill | `POST /v1/fillForm` | schema-constrained; unknown fields come back `null`, never guessed |
| Summarize | `POST /v1/summarize` | optional `max_words` |
| Translate | `POST /v1/translate` | any `target_lang` |
| Image generation | `POST /v1/image` | backend-only by default |
| Background removal | `POST /v1/removeBackground` | local `rembg` — proves non-LLM providers fit too |

Adding one is a small package under `features/` plus a route. The pattern is the point.

## Providers

Pick per feature in config; swap with a one-line change, zero app code.

| Provider | `kind` | Notes |
|---|---|---|
| Gemini | `gemini` | native API, structured output + Imagen |
| OpenAI | `openai` | text + images |
| Grok (xAI) | `grok` | keys start `xai-` |
| Groq | `groq` | fast inference; keys start `gsk_` |
| Ollama | `ollama` | local, no key, $0 |
| rembg | `rembg` | local background removal (the `vision` extra) |

## Configuration

One file decides everything. A feature names its provider, its guardrails, and its cache mode:

```yaml
features:
  fillForm:
    provider: gemini
    model: gemini-flash-latest
    fallback: { provider: ollama, model: llama3.2 }   # used if the primary errors
    frontend_safe: true
    cache: { enabled: true, mode: exact }
    guardrails:
      block_pii: true            # block a card/SSN/email before it reaches the model
      max_prompt_length: 4000

  summarize:
    provider: groq
    model: llama-3.3-70b-versatile
    cache: { enabled: true, mode: similar, similarity_threshold: 0.9 }   # TF-IDF cache
    guardrails: { redact_output_pii: true }            # scrub PII out of the response
```

## Under the hood

- **Auth** — dual keys: `sk_proj_…` for backends, `pk_proj_…` for browsers (origin-checked, feature-gated). Real provider keys never leave the gateway.
- **Cache** — exact match by default; opt-in **TF-IDF semantic** cache for text features, with a conservative similarity threshold so it never serves a fuzzy answer it can't justify.
- **Rate limits** — sliding window per user, per day/week/month.
- **Guardrails** — regex PII/keyword/length checks on input; PII redaction on output. Blocks are logged.
- **Token optimizer** — strips redundant whitespace from prompts before they go out.
- **Fallback** — if the primary provider errors, the configured fallback serves the request and the caller never knows.
- **Usage & cost** — every request logged to SQLite with tokens and an estimated USD cost; surfaced on the dashboard.

## Dashboard

`/dashboard` is server-rendered (HTMX, no build step) and refreshes itself. It shows total requests, cache-hit rate, tokens, estimated spend, guardrail/redaction events, and per-feature / per-provider breakdowns — all from the SQLite usage log.

## Project layout

```
src/synthr_gateway/       the gateway service
├── app.py                FastAPI factory
├── config/               schema + loader (synthr.config.yaml, .env)
├── core/                 errors + response envelope
├── security/             dual-key auth + origin checks
├── guardrails/           input checks + output redaction
├── cache/                exact + semantic (TF-IDF) + manager
├── ratelimit/            sliding-window limiter + policy
├── optimizer/            prompt compression
├── providers/            base + openai-compat + gemini + rembg + mock + registry
├── features/             one package per capability (fillform, summarize, …)
├── usage/                request logging + pricing
├── dashboard/            HTMX routes + templates
└── api/                  deps, health, v1 routes, shared runner
sdk/python · sdk/typescript    first-party clients
examples/                      REST / Python / JS usage
tests/                         pytest suite
```

## Tests

```bash
pip install -e ".[dev]" && pytest                # gateway (38)
pip install -e sdk/python && pytest sdk/python   # SDK (3)
```

## Status

The core gateway is complete and runs end-to-end. A few things are deliberately not done yet:

- **SDKs aren't published** to PyPI/npm — install from the `sdk/` folders for now. Publishing needs a CI release pipeline, which isn't set up.
- **No GitHub Actions / docs site** yet — intentionally skipped.
- The **token optimizer** is lossless whitespace compression today (honest and conservative — not a magic 30%).
- The **semantic cache** uses TF-IDF (the `semantic` extra). Good and cheap; swapping in real embeddings is a clean future upgrade.

## License

MIT.
