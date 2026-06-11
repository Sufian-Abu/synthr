"""Shared helpers for features: plain text out, and schema-constrained JSON out."""

from __future__ import annotations

import json
import re

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


def parse_json_object(text: str) -> dict | None:
    """Pull the first {...} object out of a model response (tolerates fences/prose)."""
    match = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    try:
        obj = json.loads(match.group(0) if match else text)
    except (json.JSONDecodeError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None


async def run_json(
    provider: Provider, model: str | None, system: str, user: str, schema: dict
) -> tuple[dict, dict]:
    """Run a schema-constrained completion and return (parsed_object, usage).

    Raises provider_error if the model didn't return a JSON object.
    """
    result = await provider.complete(
        [Message("system", system), Message("user", compress(user))],
        model=model,
        json_schema=schema,
        temperature=0.2,
    )
    obj = parse_json_object(result.text)
    if obj is None:
        raise errors.provider_error("Model did not return valid JSON.")
    return obj, result.usage
