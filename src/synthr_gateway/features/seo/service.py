"""seo orchestration — content to structured SEO metadata (schema-constrained)."""

from __future__ import annotations

import json
import re

from ...core import errors
from ...optimizer import compress
from ...providers import Message, Provider
from .models import SeoRequest

SYSTEM = (
    "You are an SEO expert. From the given content, produce a page title (<= 60 chars), a meta "
    "description (<= 160 chars), and 5-8 keywords. Return only JSON."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
}


def _parse(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    try:
        obj = json.loads(match.group(0) if match else text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    keywords = obj.get("keywords")
    return {
        "title": obj.get("title"),
        "description": obj.get("description"),
        "keywords": keywords if isinstance(keywords, list) else [],
    }


async def seo(req: SeoRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    messages = [Message("system", SYSTEM), Message("user", compress(req.content))]
    result = await provider.complete(messages, model=model, json_schema=SCHEMA, temperature=0.3)
    data = _parse(result.text)
    if data is None:
        raise errors.provider_error("Model did not return valid SEO JSON.")
    return data, result.usage
