# ADR 0004 — Config-driven, per-feature provider routing

**Status:** accepted

## Context

The platform owner — not each calling app — should decide which provider powers each feature,
and be able to change it without a code deploy. Different features also want different
providers (form-fill on Gemini's free tier, background removal on a local model), and need
per-feature limits, guardrails, and cache policy.

## Decision

`synthr.config.yaml` is the single source of truth. Each feature names its `provider`
(+ optional `fallback`), `model`, `frontend_safe`, `cache`, and `guardrails`. Swapping a
provider is a one-line config change with zero application code. Keys, per-user/per-feature
limits, and origins live in the same file.

## Consequences

- Provider swaps and policy changes are config edits, not deploys.
- The config file **is** the product surface, so it's kept clean, block-style, and documented.
- A bad config fails fast with a field-level `ConfigError`; a security preflight warns on
  dev-secret / plaintext keys / open public keys.
- Secrets stay out of app code: real provider keys live only in the gateway's config/env.
