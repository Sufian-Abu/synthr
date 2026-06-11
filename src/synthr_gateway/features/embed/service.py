"""embed orchestration — text(s) to vector(s)."""

from __future__ import annotations

from ...providers import Provider
from .models import EmbedRequest


async def embed(req: EmbedRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    texts = [req.input] if isinstance(req.input, str) else list(req.input)
    result = await provider.embed(texts, model=model)
    dimensions = len(result.vectors[0]) if result.vectors else 0
    return {"model": result.model, "dimensions": dimensions, "vectors": result.vectors}, result.usage
