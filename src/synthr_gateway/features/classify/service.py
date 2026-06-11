"""classify orchestration — pick one of the caller's labels (schema-constrained)."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_json
from .models import ClassifyRequest

SYSTEM = (
    "You are a precise text classifier. Choose exactly ONE label from the provided list that "
    "best fits the text. Return JSON: {\"label\": <one of the labels>, \"confidence\": 0..1}."
)


async def classify(req: ClassifyRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    schema = {
        "type": "object",
        "properties": {"label": {"type": "string", "enum": req.labels}, "confidence": {"type": "number"}},
    }
    user = f"Labels: {', '.join(req.labels)}\n\nText:\n{req.text}"
    data, usage = await run_json(provider, model, SYSTEM, user, schema)
    label = data.get("label")
    return {"label": label if label in req.labels else None, "confidence": data.get("confidence")}, usage
