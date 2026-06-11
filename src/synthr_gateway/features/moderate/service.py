"""moderate orchestration — flag unsafe content (schema-constrained)."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_json
from .models import ModerateRequest

SYSTEM = (
    "You are a content-safety classifier. Decide whether the text is unsafe — hate, harassment, "
    "sexual content, violence, self-harm, or illegal activity. Return JSON: "
    "{\"flagged\": bool, \"categories\": [string], \"reason\": string}."
)


async def moderate(req: ModerateRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    schema = {
        "type": "object",
        "properties": {
            "flagged": {"type": "boolean"},
            "categories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
    }
    data, usage = await run_json(provider, model, SYSTEM, req.text, schema)
    categories = data.get("categories")
    return {
        "flagged": bool(data.get("flagged")),
        "categories": categories if isinstance(categories, list) else [],
        "reason": data.get("reason"),
    }, usage
