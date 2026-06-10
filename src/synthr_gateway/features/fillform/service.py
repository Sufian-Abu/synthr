"""fillForm orchestration: build -> call provider -> parse/validate (with one retry)."""

from __future__ import annotations

import httpx

from ...core import errors
from ...providers import Message, Provider
from .models import FillFormRequest, build_field_schema
from .parse import parse_values
from .prompt import RETRY_NUDGE, SYSTEM_PROMPT, build_user_prompt


async def fill_form(req: FillFormRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    schema = build_field_schema(req.fields)
    messages = [Message("system", SYSTEM_PROMPT), Message("user", build_user_prompt(req))]

    try:
        result = await provider.complete(messages, model=model, json_schema=schema, temperature=0.0)
        values = parse_values(result.text, req.fields)
        if values is None:  # one retry with a stricter instruction
            messages.append(Message("system", RETRY_NUDGE))
            result = await provider.complete(messages, model=model, json_schema=schema, temperature=0.0)
            values = parse_values(result.text, req.fields)
    except httpx.HTTPError as exc:
        raise errors.provider_error(f"Provider call failed: {exc}") from exc

    if values is None:
        raise errors.provider_error("Model did not return schema-valid JSON.")

    unfilled = [f.name for f in req.fields if values.get(f.name) is None]
    return {"values": values, "unfilled": unfilled}, result.usage
