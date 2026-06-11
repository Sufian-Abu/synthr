"""extract orchestration — every matching record as a JSON array (schema-constrained)."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_json
from .models import ExtractRequest

_TYPES = {"string", "number", "integer", "boolean"}

SYSTEM = (
    "Extract EVERY matching record from the text as a JSON array under the key \"items\". "
    "Each record has exactly the requested fields. Use null for a missing value; never invent records."
)


async def extract(req: ExtractRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    item_props = {f.name: {"type": f.type if f.type in _TYPES else "string"} for f in req.fields}
    schema = {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {"type": "object", "properties": item_props}}},
    }
    spec = "; ".join(f"{f.name} ({f.type})" + (f" — {f.description}" if f.description else "") for f in req.fields)
    user = f"Fields per record: {spec}\n\nText:\n{req.text}"
    data, usage = await run_json(provider, model, SYSTEM, user, schema)
    items = data.get("items")
    return {"items": items if isinstance(items, list) else []}, usage
