# Synthr — MVP Spec

> Working spec for the first shippable version. Source of truth for the API contracts,
> config model, and the launch features. Companion to `SYNTHR_PROJECT.md` (vision).

---

## 1. Positioning (one paragraph)

Synthr is a **self-hosted, batteries-included AI-capabilities SDK**. Engineers call
ready-made *features* — `fillForm`, `image`, `removeBackground` — and never touch a prompt
or a provider. The platform owner picks, **per feature in `synthr.config.yaml`**, which
provider powers each one (e.g. `fillForm`→Gemini, `removeBackground`→local Ollama/rembg).
Caching, guardrails, rate-limits, per-user limits, auth, and usage tracking are provided
**free and apply to every feature automatically**. One `docker run`, every project uses it,
zero per-project setup. Reachable from **frontend (npm), backend (pip), and REST/curl**.

It is **not** a gateway/router (LiteLLM, Portkey) — those give you a raw `chat.completions`
pipe and you still build each feature yourself. Synthr is one layer up: the feature *is*
the product.

---

## 2. Access modes (hard requirement)

All three are thin clients over the **same HTTP endpoints**, so all plumbing applies identically.

| Mode | Client | Key type | Notes |
|---|---|---|---|
| Frontend | `synthr-sdk` (npm) | **public** `pk_proj_…` | origin-checked, restricted feature set |
| Backend | `synthr-sdk` (pip) | **secret** `sk_proj_…` | full power |
| Anything | REST / `curl` | secret (or public) | `X-Project-Key` header |

### Dual-key model (this is what makes frontend use safe)

A browser exposes its key in client-side JS. So keys have a **type**:

- **`sk_proj_…` (secret)** — backend/REST only. Full feature access. Never ship to a browser.
- **`pk_proj_…` (public)** — browser-safe. Locked down by:
  - **origin allowlist** — only requests from configured domains are accepted
  - **tighter per-user rate limits**
  - **feature allowlist** — only features marked `frontend_safe: true`

Same pattern as Stripe / Supabase / Clerk.

### 2.1 Per-user limit enforcement (MVP)

`X-User-Id` is **caller-supplied and trusted** — used for per-user counting and cost
attribution. It is best-effort and spoofable, so it is **not** the abuse defense. The real
backstop for public keys is a **hard rate limit per (public-key + origin)** that no
`X-User-Id` games can bypass. Secret keys (backend) are inherently trusted, so their
`X-User-Id` is treated as authoritative.

> Post-MVP (opt-in, Phase 2): a project's backend mints a short-lived signed token
> (`X-User-Token`, JWT signed with a shared secret); Synthr verifies it and enforces
> per-user limits strictly. Off by default — keeps zero-setup for pure-frontend apps.

---

## 3. Config model — `synthr.config.yaml`

```yaml
gateway:
  port: 8000
  secret: ${SYNTHR_SECRET}        # signs/validates keys; from env

# Provider credentials live ONLY here. Engineers never see them.
providers:
  gemini:
    api_key: ${GEMINI_KEY}
  openai:
    api_key: ${OPENAI_KEY}
  ollama:
    url: http://localhost:11434
  rembg:                            # local background-removal model (non-LLM provider)
    type: local

# Each feature is mapped to a provider + model + per-feature policy.
# THIS is the core of Synthr: capability -> provider, chosen here, not in app code.
features:
  fillForm:
    provider: gemini
    model: gemini-1.5-flash
    frontend_safe: true
    cache: { enabled: true, mode: exact, ttl_minutes: 60 }   # exact by default; see §5
    guardrails: { block_pii: true, validate_output: true }

  image:
    provider: gemini
    model: imagen-3
    frontend_safe: false           # cost control: backend-only by default
    cache: { enabled: true, mode: exact, ttl_minutes: 1440 }

  removeBackground:
    provider: rembg                 # NOT an LLM — proves per-feature provider design
    model: u2net
    frontend_safe: true
    cache: { enabled: true, mode: exact, ttl_minutes: 1440 } # keyed by image hash

# Project keys. Each project gets one or more.
projects:
  acme-store:
    keys:
      - id: sk_proj_acme_xxx
        type: secret
      - id: pk_proj_acme_yyy
        type: public
        allowed_origins: ["https://acme.store", "http://localhost:3000"]
    limits:
      per_user: { daily_requests: 50, monthly_requests: 500 }
      per_feature:
        image: { daily_per_user: 5 }

# Defaults applied when a project doesn't override.
defaults:
  limits:
    per_user: { daily_requests: 100 }
  guardrails:
    input:  { block_pii: true, max_prompt_length: 4000 }
    output: { content_filter: true }
```

Switching a feature's provider = **one line** here. Zero code change in any project.

---

## 4. Unified request/response envelope

Every feature returns the **same shape**, so SDK + error handling is uniform.

**Success**
```json
{
  "data": { /* feature-specific, see §6 */ },
  "meta": {
    "feature": "fillForm",
    "provider": "gemini",
    "cached": false,
    "request_id": "req_abc123",
    "usage": { "tokens": 412, "cost_usd": 0.00007 }
  }
}
```

**Error** (HTTP 4xx/5xx)
```json
{
  "error": {
    "code": "rate_limited",          // see error codes below
    "message": "Daily request limit reached for this user.",
    "retry_after_seconds": 3600
  }
}
```

**Error codes (stable contract):**
`invalid_key` · `origin_not_allowed` · `feature_not_allowed` · `rate_limited`
· `guardrail_blocked` · `provider_error` · `invalid_input` · `internal_error`

**Per-request headers:**
- `X-Project-Key: sk_proj_…` (required)
- `X-User-Id: <stable user id>` (optional but needed for per-user limits)

---

## 5. Caching policy (correctness-first)

A wrong cached answer is worse than a cache miss. So:

- **Default `mode: exact`** — cache key = hash of normalized input. Zero false hits.
- **`mode: similar`** — opt-in only, for text features where near-duplicates are safe
  (e.g. `seo`). Uses embeddings (not bare TF-IDF) with a conservative threshold.
- **Never `similar` for `image` or `removeBackground`** — similarity caching a vision/gen
  task can return the wrong asset. Exact-only, keyed by content hash.
- Every cache entry stores `{input_hash, output, feature, provider, created_at}` in SQLite.

---

## 6. Launch features

### 6.1 `fillForm` — flagship

**Purpose:** given a form's field schema + some context, return the value for each field.
This is the "magic autofill" demo. It is a **structured-output** task (JSON-schema-constrained).

**Endpoint:** `POST /v1/fillForm`

**Request**
```json
{
  "fields": [
    { "name": "fullName",  "type": "string" },
    { "name": "brand",     "type": "string",  "description": "product brand" },
    { "name": "size",      "type": "number" },
    { "name": "color",     "type": "string",  "options": ["red","blue","black"] },
    { "name": "inStock",   "type": "boolean" }
  ],
  "context": "Nike Air Max, red, size 10, available now",
  "locale": "en"
}
```

**Response (`data`)**
```json
{
  "values": {
    "fullName": null,
    "brand": "Nike",
    "size": 10,
    "color": "red",
    "inStock": true
  },
  "unfilled": ["fullName"]
}
```

**Contract rules:**
- Output **must** match the requested field names and types. Enforced via the provider's
  structured-output / JSON-schema mode (Gemini `responseSchema`, OpenAI structured outputs).
- A field that can't be determined from context → `null`, listed in `unfilled`. Never guess.
- `options` fields must return one of the allowed values or `null`.
- Output is validated against the schema **before** returning; on mismatch → one retry,
  then `provider_error`.

**Plumbing applied:** PII scan on `context` (configurable), output schema validation,
exact-mode cache keyed by `hash(fields + context + locale)`, per-user rate limit.

**Prompt strategy (internal, engineer never sees):** system prompt = "Extract values for the
given fields from the context. Output JSON matching the schema exactly. Use null for any
field not present. For `options` fields, choose only from the allowed list."

---

### 6.2 `image` — generation

**Endpoint:** `POST /v1/image`

**Request**
```json
{ "prompt": "a minimalist running shoe on white background", "size": "1024x1024", "n": 1 }
```

**Response (`data`)**
```json
{ "images": [ { "b64": "...", "mime": "image/png" } ] }
```

- Provider = a diffusion model (Imagen / DALL-E / SD), set in config.
- `frontend_safe: false` by default (cost). Enable for public keys only with tight limits.
- Cache: **exact** on `hash(prompt + size + n + provider)`. Never similarity.

---

### 6.3 `removeBackground` — vision (proves non-LLM provider)

**Endpoint:** `POST /v1/removeBackground`

**Request**
```json
{ "image": "data:image/jpeg;base64,..." }   // or { "image_url": "https://..." }
```

**Response (`data`)**
```json
{ "image": { "b64": "...", "mime": "image/png" } }   // transparent PNG
```

- Provider is **not an LLM** — **`rembg`/U2Net bundled in the Docker image by default**
  (truly $0, offline, no key). Hosted vision APIs (remove.bg / Photoroom) are config-selectable
  alternatives. This feature exists in the MVP specifically to validate that "any provider per
  feature" holds for non-text models — and that a bundled local model works end-to-end.
- Cache: **exact** on `hash(image bytes)`.
- No prompt, no token usage; `meta.usage` omitted or `{tokens: 0}`.

---

## 7. MVP Definition of Done

- [ ] `docker run` starts the gateway < 30s, reads `synthr.config.yaml`.
- [ ] `POST /v1/fillForm` returns schema-valid JSON; unknown fields come back `null`.
- [ ] `POST /v1/image` generates via the configured provider.
- [ ] `POST /v1/removeBackground` returns a transparent PNG via a **non-LLM** provider.
- [ ] Secret key works from backend/REST; public key works from an allowed origin and is
      **rejected** from a disallowed origin.
- [ ] A public key cannot call a feature where `frontend_safe: false`.
- [ ] Exceeding a per-user limit returns `rate_limited` with `retry_after_seconds`.
- [ ] Same input twice → second call returns `meta.cached: true` (exact mode), zero provider cost.
- [ ] Switching `fillForm`'s provider in config (Gemini→Ollama) needs **zero** app code change.
- [ ] Same call works from npm SDK, pip SDK, and `curl`.

---

## 8. Resolved decisions

1. **Streaming** — ❌ Not in MVP. `fillForm` returns small structured JSON; single-response
   only. Streaming waits for a future chat/`generate` feature where it actually helps.
2. **Image return** — ✅ **base64 inline** for MVP (zero infra). Gateway-hosted URLs = Phase 2.
3. **Per-user identity (public keys)** — ✅ **Soft now + signed later.** MVP trusts `X-User-Id`
   for per-user attribution/soft limits, with a **hard limit per (public-key + origin)** as the
   real abuse backstop. A signed-user-token path (app backend mints a JWT, Synthr verifies)
   is a **post-MVP opt-in** for teams needing strict enforcement. See §2.1.
4. **`removeBackground` default** — ✅ **Bundle `rembg`/U2Net in the image.** Truly $0, offline,
   no key — on-brand. Accept the larger image (~300–500 MB) and heavier CPU/RAM. Hosted APIs
   (remove.bg / Photoroom) remain available as a config-selected provider. See §6.3.
5. **Custom features** (`ai.run('x')`) — ❌ Phase 2. Nail the three real features first.

## 9. Phase 2 (explicitly deferred)

Streaming · gateway-hosted image URLs · signed user tokens (strict per-user) · custom feature
registry · similarity (embedding) cache for text features · additional features (`seo`,
`optimizePrompt`, etc.) · MCP server wrapper · A/B provider testing.
```
