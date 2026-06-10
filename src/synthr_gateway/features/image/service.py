"""image orchestration: call the provider's image API, shape the response."""

from __future__ import annotations

import httpx

from ...core import errors
from ...providers import Provider
from .models import ImageRequest


async def generate_image(req: ImageRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    try:
        result = await provider.generate_image(req.prompt, model=model, size=req.size, n=req.n)
    except httpx.HTTPError as exc:
        raise errors.provider_error(f"Provider call failed: {exc}") from exc

    if not result.images:
        raise errors.provider_error("Provider returned no images.")
    return {"images": result.images}, {}
