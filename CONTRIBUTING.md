# Contributing to Synthr

Thanks for helping grow Synthr. The whole design goal is that **adding a capability is cheap
and the apps that consume it change nothing** — so most contributions are a small package
plus a route, or a new provider adapter.

## Dev setup

```bash
pip install -e ".[dev]"          # gateway + ruff + mypy + pytest
cp synthr.config.example.yaml synthr.config.yaml
cp .env.example .env
```

Run the gateway locally:

```bash
synthr-gateway                   # or: uvicorn "synthr_gateway.app:create_app" --factory --reload
```

## The three checks (must pass — CI runs them on every PR)

```bash
ruff check src tests             # lint
mypy                             # type-check
pytest -q                        # tests
```

Match the surrounding style: `from __future__ import annotations`, type hints everywhere,
small modules, comments only where intent isn't obvious.

## Add a feature

A feature is the product. The pattern (mirror `features/summarize/`):

1. **`src/synthr_gateway/features/<name>/`**
   - `models.py` — a Pydantic request model with a `json_schema_extra` example.
   - `service.py` — `async def <name>(req, provider, model) -> tuple[dict, dict]` returning
     `(data, usage)`. Use `..common.run_text` for plain text out, or `provider.complete(..., json_schema=...)` for structured output (see `features/seo`).
   - `__init__.py` — export the request model and the function.
2. **`src/synthr_gateway/api/v1/<name>.py`** — a route that calls `execute(...)` with your
   `run=` closure, `capability=Capability.TEXT`, and `guard_text=<the user text>`. Add
   `responses=feature_responses(...)` for the API reference.
3. Register the router in `api/v1/router.py`.
4. Add the feature to `synthr.config.example.yaml` and `tests/conftest.py`.
5. Add a test in `tests/`.

Your feature now **automatically inherits** auth, guardrails, rate limits, cache, provider
fallback, and cost logging — you don't wire any of that.

## Add a provider

Providers implement the `Provider` interface (`providers/base.py`) and declare what they
support via `capabilities` + `supports_streaming` / `supports_tools`.

- **OpenAI-compatible** backend? Add a subclass in `providers/openai_compat.py` (set `kind`,
  override `_apply_json_mode` / image flags / `_classify_error` only where it differs) and
  register it in `KIND_TO_CLASS`.
- **Native API**? Add a new module (mirror `providers/gemini.py`): implement `complete`,
  optionally `stream_complete` / `generate_image`, and map errors with a `classify_error`.
- Wire it into `providers/registry.py` and the `ProviderKind` literal in `config/schema.py`.
- Add adapter tests (mirror `tests/test_provider_adapters.py`) — monkeypatch `post_json` /
  `post_sse`; no live network in tests.

## Pull requests

- One focused change per PR; keep the three checks green.
- Update docs when behavior changes (README, USAGE.md, and the capability matrix if you
  touched a provider).
- Don't commit secrets — `.env` and `synthr.config.yaml` are git-ignored.
