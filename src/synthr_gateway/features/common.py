"""Shared helper for simple text-out features (summarize, translate, ...)."""

from __future__ import annotations

import httpx

from ..core import errors
from ..optimizer import compress
from ..providers import Message, Provider


async def run_text(provider: Provider, model: str | None, system: str, user: str) -> tuple[str, dict]:
    """Run a plain (non-schema) completion and return (text, usage)."""
    try:
        result = await provider.complete(
            [Message("system", system), Message("user", compress(user))], model=model, temperature=0.2
        )
    except httpx.HTTPError as exc:
        raise errors.provider_error(f"Provider call failed: {exc}") from exc
    return result.text.strip(), result.usage
