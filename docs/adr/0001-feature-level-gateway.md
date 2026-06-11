# ADR 0001 — A feature-level gateway, not a model router

**Status:** accepted

## Context

Most AI gateways (LiteLLM, Portkey, Helicone) work at the *model* level: they hand you a
unified `chat.completions` pipe, and you still write prompts and build each feature in every
project. That layer is mature and free; competing there adds little.

The recurring pain isn't the model call — it's everything around it, rebuilt per project:
prompt engineering, key custody, caching, rate limits, PII guardrails, cost tracking.

## Decision

Synthr operates one level up, at the **capability** layer. Engineers call ready-made features
(`fillForm`, `summarize`, `seo`, …); Synthr owns the prompt, the provider, and the plumbing.
The OpenAI-compatible `/v1/chat/completions` endpoint exists for drop-in migration, but the
primary surface is named features.

## Consequences

- The caller does nothing per project — that's the core value, and the bar every feature meets.
- Adding a feature is a small server-side package; consumers don't change.
- We own prompt quality and provider quirks (a cost we accept on the platform side).
- It's a different product from model routers — comparisons on "which models" miss the point.
