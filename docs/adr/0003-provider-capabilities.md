# ADR 0003 — Providers declare capabilities

**Status:** accepted

## Context

No single provider does everything: Gemini and OpenAI generate images, Groq and Ollama are
text-only; some support streaming or tool calls, some don't; JSON mode differs (strict
`json_schema` vs `json_object` vs native schema). Features must stay provider-agnostic, but
the gateway has to know what a backend can actually do before routing to it.

## Decision

Every provider implements the `Provider` interface and **declares** what it supports:
`capabilities` (text / image / remove-background) plus `supports_streaming` and
`supports_tools`. The OpenAI-compatible providers share a base class and override only the
parts that genuinely differ (JSON mode, image endpoint, error parsing). The runner checks the
declared capability before dispatching.

## Consequences

- A feature requests a `Capability`; routing to a provider that lacks it fails fast with a
  clear error instead of a confusing upstream 4xx.
- Per-provider divergence (JSON mode, image API, error bodies, streaming, tools) lives in one
  place per provider, not smeared across features.
- The README capability matrix is the human-readable view of these flags.
- Adding a provider = a small adapter + flags; features are untouched.
