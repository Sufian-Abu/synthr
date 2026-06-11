"""extract orchestration — one structured record (schema) or a list of them (fields)."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_json
from .models import ExtractRequest

_TYPES = {"string", "number", "integer", "boolean"}


async def extract(req: ExtractRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    # Schema mode → a single structured record, returned directly.
    if req.schema_:
        props = {name: {"type": t if t in _TYPES else "string"} for name, t in req.schema_.items()}
        json_schema = {"type": "object", "properties": props}
        spec = ", ".join(f"{name} ({t})" for name, t in req.schema_.items())
        system = (
            "Extract the requested fields from the text into a single JSON object. "
            "Use null for any value not present; never invent values."
        )
        data, usage = await run_json(provider, model, system, f"Fields: {spec}\n\nText:\n{req.text}", json_schema)
        return {name: data.get(name) for name in req.schema_}, usage

    # Fields mode → a list of records under "items".
    item_props = {f.name: {"type": f.type if f.type in _TYPES else "string"} for f in req.fields or []}
    json_schema = {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {"type": "object", "properties": item_props}}},
    }
    spec = "; ".join(f"{f.name} ({f.type})" + (f" — {f.description}" if f.description else "") for f in req.fields or [])
    system = (
        'Extract EVERY matching record from the text as a JSON array under the key "items". '
        "Each record has exactly the requested fields. Use null for a missing value; never invent records."
    )
    data, usage = await run_json(provider, model, system, f"Fields per record: {spec}\n\nText:\n{req.text}", json_schema)
    items = data.get("items")
    return {"items": items if isinstance(items, list) else []}, usage
